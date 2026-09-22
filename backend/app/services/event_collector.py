import os
import requests
import psycopg2

from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


CALENDAR_API = (
    "https://www.financecalendar.com/wp-json/fc/v1/calendar"
)

SOURCE_NAME = "FinanceCalendar"

DAYS_AHEAD = 30


IMPORTANT_KEYWORDS = [

    "fed",
    "fomc",
    "interest rate",
    "interest rates",
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

    "average hourly earnings",

    "adp employment",

    "durable goods",

    "industrial production",

    "housing starts",

    "building permits",
]


US_COUNTRY_VALUES = {
    "US",
    "USA",
    "USD",
    "UNITED STATES",
    "UNITED STATES OF AMERICA",
    "AMERICA",
}


def get_connection():

    if not DATABASE_URL:
        raise ValueError(
            "DATABASE_URL not found in .env"
        )

    return psycopg2.connect(
        DATABASE_URL
    )


def clean_numeric(value):

    if value is None:
        return None

    if isinstance(value, bool):
        return None

    value = str(value).strip()

    if not value:
        return None

    value = value.replace(",", "")
    value = value.replace("%", "")

    multiplier = 1

    suffix = value[-1:].upper()

    if suffix == "K":

        multiplier = 1000
        value = value[:-1]

    elif suffix == "M":

        multiplier = 1000000
        value = value[:-1]

    elif suffix == "B":

        multiplier = 1000000000
        value = value[:-1]

    try:

        return float(value) * multiplier

    except ValueError:

        return None


def parse_event_time(value):

    if not value:
        return None

    try:

        value = str(value).strip()

        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        dt = datetime.fromisoformat(value)

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
            f"{value} -> {error}"
        )

        return None


def get_country(event):

    country = (
        event.get("country")
        or event.get("currency")
        or event.get("country_code")
        or ""
    )

    return str(country).strip()


def get_event_name(event):

    return str(
        event.get("title")
        or event.get("name")
        or event.get("event")
        or ""
    ).strip()


def is_us_event(event):

    country = get_country(event)

    country_upper = country.upper()

    return (
        country_upper in US_COUNTRY_VALUES
        or country_upper.startswith("US ")
        or "UNITED STATES" in country_upper
    )


def is_relevant_event(event):

    event_name = get_event_name(
        event
    ).lower()

    if not event_name:
        return False

    if not is_us_event(event):

        return False

    return any(
        keyword in event_name
        for keyword in IMPORTANT_KEYWORDS
    )


def get_metal_impact(event_name):

    name = event_name.lower()

    # These are descriptive initial labels.
    # Later this can be replaced by historical
    # event-reaction calculations.

    if any(
        keyword in name
        for keyword in [
            "fed",
            "fomc",
            "interest rate",
            "federal funds",
            "powell",
        ]
    ):

        return "HIGH"

    if any(
        keyword in name
        for keyword in [
            "cpi",
            "inflation",
            "ppi",
            "pce",
            "nonfarm",
            "non-farm payroll",
            "payrolls",
            "unemployment",
            "jobless claims",
            "gdp",
        ]
    ):

        return "MEDIUM"

    return "NEUTRAL"


def fetch_calendar():

    today = datetime.now(
        timezone.utc
    ).date()

    end_date = (
        today
        + timedelta(
            days=DAYS_AHEAD
        )
    )

    params = {

        "from": today.isoformat(),

        "to": end_date.isoformat(),

        "limit": 500,
    }

    headers = {

        "User-Agent":
            "CommodityTrack/1.0 "
            "(Economic Calendar Application)"
    }

    print()
    print(
        "Fetching economic calendar..."
    )

    print(
        f"From: {today}"
    )

    print(
        f"To  : {end_date}"
    )

    try:

        response = requests.get(
            CALENDAR_API,
            params=params,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        result = response.json()

    except Exception as error:

        print(
            f"[CALENDAR API ERROR] "
            f"{error}"
        )

        return []

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

    event_name = get_event_name(
        raw_event
    )

    if not event_name:

        return None

    country = get_country(
        raw_event
    )

    event_time = parse_event_time(
        raw_event.get("time_utc")
        or raw_event.get("datetime")
        or raw_event.get("date")
        or raw_event.get("time")
    )

    if not event_time:

        return None

    previous_value = clean_numeric(
        raw_event.get("previous")
        if raw_event.get("previous") is not None
        else raw_event.get("prior")
    )

    forecast_value = clean_numeric(
        raw_event.get("forecast")
        if raw_event.get("forecast") is not None
        else raw_event.get("consensus")
    )

    actual_value = clean_numeric(
        raw_event.get("actual")
    )

    impact = str(
        raw_event.get("impact")
        or "MEDIUM"
    ).upper()

    if impact not in {
        "HIGH",
        "MEDIUM",
        "LOW"
    }:

        impact = "MEDIUM"

    metal_impact = get_metal_impact(
        event_name
    )

    category = raw_event.get(
        "category"
    )

    source_url = raw_event.get(
        "url"
    )

    description_parts = [
        event_name,
        f"({country})",
        f"Source: {SOURCE_NAME}"
    ]

    if category:

        description_parts.append(
            f"Category: {category}"
        )

    if source_url:

        description_parts.append(
            f"URL: {source_url}"
        )

    description = " | ".join(
        description_parts
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
            impact,

        "gold_impact":
            metal_impact,

        "silver_impact":
            metal_impact,

        "description":
            description,
    }


def save_event(event):

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT id
                FROM economic_events
                WHERE event_name = %s
                  AND event_time = %s
                  AND COALESCE(country, '') =
                      COALESCE(%s, '')
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
    print(
        "Starting economic event collection..."
    )
    print()

    raw_events = fetch_calendar()

    saved = 0
    skipped = 0

    today = datetime.now(
        timezone.utc
    ).date()

    end_date = (
        today
        + timedelta(
            days=DAYS_AHEAD
        )
    )

    for raw_event in raw_events:

        if not is_relevant_event(
            raw_event
        ):

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

            save_event(
                event
            )

            saved += 1

        except Exception as error:

            print(
                f"[DATABASE ERROR] "
                f"{event['event_name']} "
                f"-> {error}"
            )

    print()
    print(
        "=" * 60
    )

    print(
        f"Events saved/updated: {saved}"
    )

    print(
        f"Events skipped: {skipped}"
    )

    print(
        "=" * 60
    )

    print()


if __name__ == "__main__":

    try:

        collect_events()

    except Exception as error:

        print(
            f"[FATAL ERROR] {error}"
        )