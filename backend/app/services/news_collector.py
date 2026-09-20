import os
import json
import requests
import psycopg2

from datetime import datetime, timezone
from dotenv import load_dotenv


# =========================================================
# LOAD ENVIRONMENT
# =========================================================

load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

API_URL = "https://www.alphavantage.co/query"


# =========================================================
# FETCH NEWS FROM ALPHA VANTAGE
# =========================================================

def fetch_news():

    if not API_KEY:
        print("❌ ALPHA_VANTAGE_API_KEY not configured")
        return []

    print("📰 Fetching financial news...")

    params = {
        "function": "NEWS_SENTIMENT",
        "topics": "financial_markets,economy_monetary,economy_macro,economy_fiscal",
        "sort": "LATEST",
        "limit": 50,
        "apikey": API_KEY
    }

    try:

        response = requests.get(
            API_URL,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        if "feed" not in data:

            print("❌ No news feed returned")

            print(
                json.dumps(
                    data,
                    indent=2
                )
            )

            return []

        return data["feed"]

    except Exception as e:

        print(
            f"❌ Error fetching news: {e}"
        )

        return []


# =========================================================
# FILTER RELEVANT NEWS
# =========================================================

def is_relevant_news(item):

    text = (
        (item.get("title") or "")
        + " "
        + (item.get("summary") or "")
    ).lower()

    keywords = [

        # Metals
        "gold",
        "silver",
        "xau",
        "xag",

        # Federal Reserve
        "fed",
        "federal reserve",
        "powell",

        # Interest rate
        "interest rate",
        "rate cut",
        "rate hike",
        "monetary policy",

        # Inflation
        "inflation",
        "cpi",
        "ppi",

        # Jobs
        "nonfarm",
        "payroll",
        "jobs report",
        "unemployment",

        # Dollar / Bonds
        "dollar",
        "usd",
        "treasury yield",
        "bond yield",

        # Trump / Policy
        "trump",
        "tariff"
    ]

    return any(
        keyword in text
        for keyword in keywords
    )


# =========================================================
# NORMALIZE SENTIMENT
# =========================================================

def normalize_sentiment(label):

    if not label:
        return "NEUTRAL"

    label = label.upper()

    if "BULLISH" in label:
        return "BULLISH"

    if "BEARISH" in label:
        return "BEARISH"

    return "NEUTRAL"


# =========================================================
# DETECT METAL TYPE
# =========================================================

def detect_metal_type(item):

    text = (
        (item.get("title") or "")
        + " "
        + (item.get("summary") or "")
    ).lower()

    has_gold = any(
        x in text
        for x in ["gold", "xau"]
    )

    has_silver = any(
        x in text
        for x in ["silver", "xag"]
    )

    if has_gold and has_silver:
        return "BOTH"

    if has_gold:
        return "GOLD"

    if has_silver:
        return "SILVER"

    return "MACRO"


# =========================================================
# DETECT SYMBOL
# =========================================================

def detect_symbol(metal_type):

    if metal_type == "GOLD":
        return "GC=F"

    if metal_type == "SILVER":
        return "SI=F"

    if metal_type == "BOTH":
        return "GC=F,SI=F"

    return None


# =========================================================
# DETECT IMPACT
# =========================================================

def detect_impact(sentiment):

    if sentiment == "BULLISH":
        return "POSITIVE"

    if sentiment == "BEARISH":
        return "NEGATIVE"

    return "NEUTRAL"


# =========================================================
# SAVE NEWS TO DATABASE
# =========================================================

def save_news(news_list):

    if not DATABASE_URL:

        print(
            "❌ DATABASE_URL not configured"
        )

        return 0

    conn = None
    cursor = None

    inserted = 0

    try:

        conn = psycopg2.connect(
            DATABASE_URL
        )

        cursor = conn.cursor()

        for item in news_list:

            title = item.get("title")
            summary = item.get("summary")
            source = item.get("source")
            url = item.get("url")

            if not url:
                continue

            # -------------------------------------------------
            # Published time
            # -------------------------------------------------

            published_at = None

            published_raw = item.get(
                "time_published"
            )

            if published_raw:

                try:

                    published_at = datetime.strptime(
                        published_raw,
                        "%Y%m%dT%H%M%S"
                    ).replace(
                        tzinfo=timezone.utc
                    )

                except ValueError:

                    published_at = None

            # -------------------------------------------------
            # Sentiment
            # -------------------------------------------------

            sentiment = normalize_sentiment(
                item.get(
                    "overall_sentiment_label"
                )
            )

            sentiment_score = item.get(
                "overall_sentiment_score"
            )

            # -------------------------------------------------
            # Metal
            # -------------------------------------------------

            metal_type = detect_metal_type(
                item
            )

            symbol = detect_symbol(
                metal_type
            )

            impact = detect_impact(
                sentiment
            )

            # -------------------------------------------------
            # Trump
            # -------------------------------------------------

            combined_text = (
                (title or "")
                + " "
                + (summary or "")
            ).lower()

            is_trump_related = (
                "trump" in combined_text
            )

            # -------------------------------------------------
            # Keywords
            # -------------------------------------------------

            keywords = {

                "topics": item.get(
                    "topics",
                    []
                ),

                "ticker_sentiment": item.get(
                    "ticker_sentiment",
                    []
                )
            }

            # -------------------------------------------------
            # Insert
            # -------------------------------------------------

            query = """

                INSERT INTO news_articles (

                    title,
                    summary,
                    source,
                    url,
                    published_at,
                    symbol,
                    metal_type,
                    sentiment,
                    sentiment_score,
                    impact,
                    keywords,
                    is_trump_related,
                    created_at

                )

                SELECT

                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s::jsonb,
                    %s,
                    NOW()

                WHERE NOT EXISTS (

                    SELECT 1

                    FROM news_articles

                    WHERE url = %s

                );

            """

            cursor.execute(
                query,
                (
                    title,
                    summary,
                    source,
                    url,
                    published_at,
                    symbol,
                    metal_type,
                    sentiment,
                    sentiment_score,
                    impact,
                    json.dumps(keywords),
                    is_trump_related,
                    url
                )
            )

            if cursor.rowcount > 0:

                inserted += 1

        conn.commit()

        return inserted

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            f"❌ Database error: {e}"
        )

        return 0

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# MAIN COLLECTOR FUNCTION
# =========================================================

def collect_news():

    print("\n" + "=" * 60)
    print("📰 AUTOMATIC NEWS COLLECTION")
    print("=" * 60)

    news = fetch_news()

    print(
        f"📥 News received: {len(news)}"
    )

    relevant_news = [

        item

        for item in news

        if is_relevant_news(item)

    ]

    print(
        f"🎯 Relevant news: {len(relevant_news)}"
    )

    if not relevant_news:

        print(
            "⚠️ No relevant news found"
        )

        return

    inserted = save_news(
        relevant_news
    )

    print(
        f"✅ New articles inserted: {inserted}"
    )

    print("=" * 60 + "\n")


# =========================================================
# MANUAL TEST
# =========================================================

if __name__ == "__main__":

    collect_news()