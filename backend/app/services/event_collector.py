import os
import requests
import psycopg2

from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv


# =========================================================
# CONFIG
# =========================================================

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

FOREX_FACTORY_JSON = (
    "https://nfs.faireconomy.media/"
    "ff_calendar_thisweek.json"
)

SOURCE_NAME = "Forex Factory"

DAYS_AHEAD = 7


# =========================================================
# IMPORTANT EVENTS
# =========================================================

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
]


# =========================================================
# DATE RANGE
# =========================================================

def get_date_range(days=7):

    today = datetime.now(timezone.utc).date()

    end_date = today + timedelta(days=days)

    return today, end_date


# =========================================================
# DATABASE
# =========================================================

def get_connection():

    if not DATABASE_URL:
        raise ValueError(
            "DATABASE_URL not found in .env"
        )

    return psycopg2.connect(DATABASE_URL)


# =========================================================
# FETCH FOREX FACTORY
# =========================================================

def fetch_forex_factory():

    print("=" * 60)
    print("Fetching Forex Factory Economic Calendar")
    print("=" * 60)

    headers = {
        "User-Agent":
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/153.0 Safari/537.36"
    }

    response = requests.get(
        FOREX_FACTORY_JSON,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    print(
        f"[OK] JSON events received: {len(data)}"
    )

    return data


# =========================================================
# DATE PARSER
# =========================================================

def parse_event_time(date_string):

    if not date_string:
        return None

    try:

        dt = datetime.fromisoformat(
            str(date_string)
        )

        if dt.tzinfo is None:

            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt.astimezone(
            timezone.utc
        )

    except Exception as error:

        print(
            f"[DATE ERROR] "
            f"{date_string} -> {error}"
        )

        return None


# =========================================================
# EVENT FILTER
# =========================================================

def is_relevant_event(event):
    country = (event.get("country") or "").upper()
    title = (event.get("title") or "").lower()

    if country != "USD":
        return False

    keywords = [
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
        "adp",
        "employment",
        "gdp",
        "pce",
        "core pce",
        "retail sales",
        "ism manufacturing",
        "ism services",
        "consumer confidence",
        "consumer sentiment",
        "powell",
        "goolsbee",
        "williams",
        "jefferson",
        "fomc minutes",
        "manufacturing index",
    ]

    return any(keyword in title for keyword in keywords)

# =========================================================
# METAL IMPACT
# =========================================================

def get_metal_impact(event_name):

    # Directional impact will be calculated later
    # using historical market reaction.

    return "NEUTRAL"

# =========================================================
# NORMALIZE EVENT
# =========================================================

def normalize_event(raw_event):

    event_name = raw_event.get("title")

    country = raw_event.get("country")

    impact = raw_event.get("impact")

    event_time = parse_event_time(
        raw_event.get("date")
    )

    if not event_name:
        return None

    if not event_time:
        return None

    # Forex Factory currently provides
    # previous and forecast as strings.
    previous_value = clean_numeric(
    raw_event.get("previous")
)

    forecast_value = clean_numeric(
        raw_event.get("forecast")
    )

    actual_value = clean_numeric(
        raw_event.get("actual")
    )

    metal_impact = get_metal_impact(
        event_name
    )

    description = (
        f"{event_name} "
        f"({country}) "
        f"from Forex Factory."
    )

    return {

        "event_name":
            event_name,

        "event_type":
            "ECONOMIC",

        "country":
            country,

        "event_time":
            event_time,

        "previous_value":
            previous_value,

        "forecast_value":
            forecast_value,

        "actual_value":
            actual_value,

        "unit":
            None,

        "impact":
            str(impact).upper(),

        "gold_impact":
            metal_impact,

        "silver_impact":
            metal_impact,

        "description":
            description
    }


# =========================================================
# SAVE EVENT
# =========================================================

def save_event(event):

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            # Check duplicate
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

            # ---------------------------------------------
            # UPDATE
            # ---------------------------------------------

            if existing:

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

            # ---------------------------------------------
            # INSERT
            # ---------------------------------------------

            else:

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

def clean_numeric(value):

    if value is None:
        return None

    value = str(value).strip()

    if value == "":
        return None

    try:

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

        print(
            f"[NUMERIC ERROR] "
            f"Cannot convert: {value}"
        )

        return None
# =========================================================
# MAIN COLLECTOR
# =========================================================

def collect_events():

    today, end_date = get_date_range(
        DAYS_AHEAD
    )

    print()
    print(
        f"Collecting events: "
        f"{today} -> {end_date}"
    )
    print()

    raw_events = fetch_forex_factory()

    saved = 0
    skipped = 0

    for raw_event in raw_events:

        # ---------------------------------------------
        # Filter
        # ---------------------------------------------

        if not is_relevant_event(
            raw_event
        ):

            skipped += 1
            continue

        # ---------------------------------------------
        # Normalize
        # ---------------------------------------------

        event = normalize_event(
            raw_event
        )

        if not event:

            skipped += 1
            continue

        # ---------------------------------------------
        # Date filter
        # ---------------------------------------------

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

        # ---------------------------------------------
        # Save
        # ---------------------------------------------

        try:

            save_event(event)

            saved += 1

        except Exception as error:

            print(
                f"[DATABASE ERROR] "
                f"{event['event_name']} -> "
                f"{error}"
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


# =========================================================
# RUN
# =========================================================

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