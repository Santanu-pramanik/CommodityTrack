import os
import requests
import psycopg2

from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# FinanceCalendar API
CALENDAR_API = (
    "https://www.financecalendar.com/wp-json/fc/v1/calendar"
)

SOURCE_NAME = "FinanceCalendar"

# Next 30 days
DAYS_AHEAD = 30


IMPORTANT_KEYWORDS = [
    "fed",
    "fomc",
    "interest rate",
    "federal funds",
    "cpi",
    "consumer price index",
    "inflation",
    "ppi",
    "producer price index",
    "nonfarm payroll",
    "non-farm payroll",
    "payrolls",
    "unemployment",
    "jobless claims",
    "gdp",
    "pce",
    "core pce",
    "retail sales",
    "ism manufacturing",
    "ism services",
    "consumer confidence",
    "consumer sentiment",
    "powell",
    "fomc minutes",
    "jolts",
    "employment",
]


def get_connection():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not found in .env")

    return psycopg2.connect(DATABASE_URL)


def clean_numeric(value):

    if value is None:
        return None

    value = str(value).strip()

    if value == "":
        return None

    try:
        value = value.replace(",", "")
        value = value.replace("%", "")

        multiplier = 1

        if value.upper().endswith("K"):
            multiplier = 1000
            value = value[:-1]

        elif value.upper().endswith("M"):
            multiplier = 1000000
            value = value[:-1]

        elif value.upper().endswith("B"):
            multiplier = 1000000000
            value = value[:-1]

        return float(value) * multiplier

    except ValueError:

        print(f"[NUMERIC ERROR] Cannot convert: {value}")

        return None


def parse_event_time(date_string):

    if not date_string:
        return None

    try:

        dt = datetime.fromisoformat(
            str(date_string).replace("Z", "+00:00")
        )

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc)

    except Exception as error:

        print(
            f"[DATE ERROR] "
            f"{date_string} -> {error}"
        )

        return None


def is_relevant_event(event):

    # FinanceCalendar normally provides country/currency
    country = (
        event.get("country")
        or event.get("currency")
        or ""
    ).upper()

    title = (
        event.get("title")
        or event.get("name")
        or event.get("event")
        or ""
    ).lower()

    # We mainly want USD events
    if country not in ["US", "USD"]:
        return False

    return any(
        keyword in title
        for keyword in IMPORTANT_KEYWORDS
    )


def get_metal_impact(event_name):

    # Initial value.
    # Later we will calculate this from
    # historical gold/silver reaction.
    return "NEUTRAL"


def fetch_calendar():

    today = datetime.now(timezone.utc).date()

    end_date = today + timedelta(
        days=DAYS_AHEAD
    )

    url = (
        f"{CALENDAR_API}"
        f"?from={today.isoformat()}"
        f"&to={end_date.isoformat()}"
        f"&limit=500"
    )

    print("=" * 60)
    print("Fetching 30-Day Economic Calendar")
    print("=" * 60)

    print(f"From: {today}")
    print(f"To  : {end_date}")

    headers = {
        "User-Agent":
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/153.0 Safari/537.36"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    result = response.json()

    # API may return either a list
    # or an object containing events
    if isinstance(result, list):

        events = result

    elif isinstance(result, dict):

        events = (
            result.get("events")
            or result.get("data")
            or []
        )

    else:

        events = []

    print(
        f"[OK] Calendar events received: "
        f"{len(events)}"
    )

    return events


def normalize_event(raw_event):

    event_name = (
        raw_event.get("title")
        or raw_event.get("name")
        or raw_event.get("event")
    )

    country = (
        raw_event.get("country")
        or raw_event.get("currency")
    )

    event_time = parse_event_time(
        raw_event.get("time_utc")
        or raw_event.get("date")
        or raw_event.get("datetime")
    )

    if not event_name:
        return None

    if not event_time:
        return None

    previous_value = clean_numeric(
        raw_event.get("previous")
        or raw_event.get("prior")
    )

    forecast_value = clean_numeric(
        raw_event.get("forecast")
        or raw_event.get("consensus")
    )

    actual_value = clean_numeric(
        raw_event.get("actual")
    )

    impact = (
        raw_event.get("impact")
        or "MEDIUM"
    )

    metal_impact = get_metal_impact(
        event_name
    )

    description = (
        f"{event_name} "
        f"({country}) "
        f"from {SOURCE_NAME}."
    )

    return {

        "event_name": event_name,

        "event_type": "ECONOMIC",

        "country": country,

        "event_time": event_time,

        "previous_value": previous_value,

        "forecast_value": forecast_value,

        "actual_value": actual_value,

        "unit": None,

        "impact": str(impact).upper(),

        "gold_impact": metal_impact,

        "silver_impact": metal_impact,

        "description": description
    }


def save_event(event):

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            # Check existing event
            cursor.execute(
                """
                SELECT id
                FROM economic_events
                WHERE event_name = %s
                  AND event_time = %s
                  AND country = %s
                LIMIT 1
                """,
                (
                    event["event_name"],
                    event["event_time"],
                    event["country"],
                )
            )

            existing = cursor.fetchone()

            if existing:

                # UPDATE existing event
                cursor.execute(
                    """
                    UPDATE economic_events
                    SET
                        previous_value = %s,
                        forecast_value = %s,
                        actual_value = %s,
                        unit = %s,
                        impact = %s,
                        gold_impact = %s,
                        silver_impact = %s,
                        description = %s,
                        source = %s
                    WHERE id = %s
                    """,
                    (
                        event["previous_value"],
                        event["forecast_value"],
                        event["actual_value"],
                        event["unit"],
                        event["impact"],
                        event["gold_impact"],
                        event["silver_impact"],
                        event["description"],
                        SOURCE_NAME,
                        existing[0],
                    )
                )

                print(
                    f"[UPDATED] "
                    f"{event['event_name']}"
                )

            else:

                # INSERT new event
                cursor.execute(
                    """
                    INSERT INTO economic_events
                    (
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
                    )
                    VALUES
                    (
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        event["event_name"],
                        event["event_type"],
                        event["country"],
                        event["event_time"],
                        event["previous_value"],
                        event["forecast_value"],
                        event["actual_value"],
                        event["unit"],
                        event["impact"],
                        event["gold_impact"],
                        event["silver_impact"],
                        event["description"],
                        SOURCE_NAME,
                    )
                )

                print(
                    f"[INSERTED] "
                    f"{event['event_name']}"
                )

        conn.commit()

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


def collect_events():

    print()
    print("📅 Starting economic event collection...")
    print()

    raw_events = fetch_calendar()

    saved = 0
    skipped = 0

    today = datetime.now(
        timezone.utc
    ).date()

    end_date = today + timedelta(
        days=DAYS_AHEAD
    )

    for raw_event in raw_events:

        # USD filtering
        if not is_relevant_event(raw_event):

            skipped += 1
            continue

        event = normalize_event(
            raw_event
        )

        if not event:

            skipped += 1
            continue

        event_date = (
            event["event_time"].date()
        )

        if not (
            today
            <= event_date
            <= end_date
        ):

            skipped += 1
            continue

        try:

            save_event(event)

            saved += 1

        except Exception as error:

            print(
                f"[DATABASE ERROR] "
                f"{event['event_name']} "
                f"-> {error}"
            )

    print()
    print("=" * 60)
    print(
        f"Events saved/updated: {saved}"
    )
    print(
        f"Events skipped: {skipped}"
    )
    print("=" * 60)
    print()


if __name__ == "__main__":

    try:

        collect_events()

    except Exception as error:

        print()
        print(
            "[FATAL ERROR]",
            error
        )
        print()