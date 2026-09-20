from fastapi import APIRouter, Query
import os
import psycopg2
from dotenv import load_dotenv


load_dotenv()

router = APIRouter(prefix="/api")


# =========================================================
# DATABASE CONNECTION
# =========================================================

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not found in .env")

    return psycopg2.connect(DATABASE_URL)


# =========================================================
# GET ECONOMIC EVENTS
# =========================================================

@router.get("/events")
def get_events(days: int = Query(7, ge=1, le=30)):

    conn = get_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    id,
                    event_name,
                    event_type,
                    country,
                    event_time,
                    previous_value,
                    forecast_value,
                    actual_value,
                    unit,
                    impact,
                    gold_impact,
                    silver_impact,
                    description,
                    source
                FROM economic_events

                WHERE country = 'USD'

                AND event_time >= NOW()

                AND event_time < NOW() + (%s * INTERVAL '1 day')

                ORDER BY event_time ASC
                """,
                (days,)
            )

            rows = cursor.fetchall()

            events = []

            for row in rows:

                events.append({
                    "id": row[0],
                    "event": row[1],
                    "event_type": row[2],
                    "country": row[3],

                    "date": row[4].date().isoformat()
                    if row[4] else None,

                    "time": row[4].strftime("%H:%M")
                    if row[4] else None,

                    "event_time": row[4].isoformat()
                    if row[4] else None,

                    "previous": row[5],
                    "forecast": row[6],
                    "actual": row[7],

                    "unit": row[8],
                    "impact": row[9],

                    "gold_effect": row[10],
                    "silver_effect": row[11],

                    "description": row[12],
                    "source": row[13]
                })

            return {
                "count": len(events),
                "days": days,
                "events": events
            }

    finally:
        conn.close()


# =========================================================
# UPCOMING EVENTS
# =========================================================

@router.get("/events/upcoming")
def get_upcoming_events():

    return get_events(days=7)