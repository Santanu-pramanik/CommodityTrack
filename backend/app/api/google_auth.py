from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
import psycopg2

from app.config import (
    DATABASE_URL,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    FRONTEND_URL,
)

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

oauth = OAuth()

oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url=(
        "https://accounts.google.com/.well-known/openid-configuration"
    ),
    client_kwargs={
        "scope": "openid email profile"
    },
)


@router.get("/google")
async def google_login(request: Request):

    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth credentials are not configured"
        )

    return await oauth.google.authorize_redirect(
        request,
        GOOGLE_REDIRECT_URI
    )


@router.get("/google/callback")
async def google_callback(request: Request):

    try:
        token = await oauth.google.authorize_access_token(request)

        user_info = token.get("userinfo")

        if not user_info:
            raise HTTPException(
                status_code=400,
                detail="Google user information not received"
            )

        google_user_id = user_info.get("sub")
        email = user_info.get("email")
        name = user_info.get("name")
        picture = user_info.get("picture")

        if not google_user_id:
            raise HTTPException(
                status_code=400,
                detail="Google user ID not received"
            )

        conn = psycopg2.connect(DATABASE_URL)

        try:
            with conn.cursor(
                cursor_factory=RealDictCursor
            ) as cursor:

                cursor.execute(
                    """
                    INSERT INTO users (
                        provider,
                        provider_user_id,
                        name,
                        email,
                        profile_image
                    )
                    VALUES (
                        'GOOGLE',
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    ON CONFLICT (
                        provider,
                        provider_user_id
                    )
                    DO UPDATE SET
                        name = EXCLUDED.name,
                        email = EXCLUDED.email,
                        profile_image = EXCLUDED.profile_image,
                        updated_at = NOW()
                    RETURNING
                        id,
                        provider,
                        provider_user_id,
                        name,
                        email,
                        profile_image,
                        notification_channel;
                    """,
                    (
                        google_user_id,
                        name,
                        email,
                        picture,
                    )
                )

                user = cursor.fetchone()

            conn.commit()

        finally:
            conn.close()

        return RedirectResponse(
            url=(
                f"{FRONTEND_URL}/"
                f"?login=success"
                f"&user_id={user['id']}"
            )
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Google login failed: {str(e)}"
        )

class NotificationPreferenceRequest(BaseModel):
    user_id: int

    email_enabled: bool = False
    sms_enabled: bool = False
    whatsapp_enabled: bool = False
    telegram_enabled: bool = False

    phone_number: str | None = None
    telegram_username: str | None = None

    email_consent: bool = False
    sms_consent: bool = False
    whatsapp_consent: bool = False
    telegram_consent: bool = False

@router.post("/notification-preferences")
def save_notification_preferences(
    data: NotificationPreferenceRequest
):
    conn = None

    try:
        # Validate consent matches selected channels

        if data.email_enabled and not data.email_consent:
            raise HTTPException(
                status_code=400,
                detail="Email permission is required."
            )

        if data.sms_enabled and not data.sms_consent:
            raise HTTPException(
                status_code=400,
                detail="SMS permission is required."
            )

        if data.whatsapp_enabled and not data.whatsapp_consent:
            raise HTTPException(
                status_code=400,
                detail="WhatsApp permission is required."
            )

        if data.telegram_enabled and not data.telegram_consent:
            raise HTTPException(
                status_code=400,
                detail="Telegram permission is required."
            )

        # Phone required for SMS / WhatsApp
        if (data.sms_enabled or data.whatsapp_enabled) and not data.phone_number:
            raise HTTPException(
                status_code=400,
                detail="Phone number is required for SMS or WhatsApp."
            )

        # Telegram username required for Telegram
        if data.telegram_enabled and not data.telegram_username:
            raise HTTPException(
                status_code=400,
                detail="Telegram username is required."
            )

        # Build notification channel
        channels = []

        if data.email_enabled:
            channels.append("EMAIL")

        if data.sms_enabled:
            channels.append("SMS")

        if data.whatsapp_enabled:
            channels.append("WHATSAPP")

        if data.telegram_enabled:
            channels.append("TELEGRAM")

        notification_channel = ",".join(channels) if channels else "NONE"

        conn = psycopg2.connect(DATABASE_URL)

        with conn.cursor() as cursor:

            # Check user exists
            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE id = %s
                """,
                (data.user_id,)
            )

            user = cursor.fetchone()

            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="User not found"
                )

            # Save notification preferences
            cursor.execute(
                """
                UPDATE users
                SET
                    email_enabled = %s,
                    sms_enabled = %s,
                    whatsapp_enabled = %s,
                    telegram_enabled = %s,

                    phone_number = %s,
                    telegram_username = %s,

                    notification_channel = %s,

                    email_consent = %s,
                    sms_consent = %s,
                    whatsapp_consent = %s,
                    telegram_consent = %s,

                    consent_updated_at = NOW(),
                    updated_at = NOW()

                WHERE id = %s
                """,
                (
                    data.email_enabled,
                    data.sms_enabled,
                    data.whatsapp_enabled,
                    data.telegram_enabled,

                    data.phone_number,
                    data.telegram_username,

                    notification_channel,

                    data.email_consent,
                    data.sms_consent,
                    data.whatsapp_consent,
                    data.telegram_consent,

                    data.user_id,
                )
            )

        conn.commit()

        return {
            "success": True,
            "message": "Notification preferences saved",
            "notification_channel": notification_channel
        }

    except HTTPException:
        raise

    except Exception as e:
        if conn:
            conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Unable to save notification preferences: {str(e)}"
        )

    finally:
        if conn:
            conn.close()

@router.get("/user/{user_id}")
def get_user(user_id: int):
    conn = None

    try:
        conn = psycopg2.connect(DATABASE_URL)

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    email,
                    profile_image
                FROM users
                WHERE id = %s
                """,
                (user_id,)
            )

            user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        return dict(user)

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to fetch user: {str(e)}"
        )

    finally:
        if conn:
            conn.close()