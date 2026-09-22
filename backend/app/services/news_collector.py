# backend/app/services/news_collector.py

import os
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

FINNHUB_NEWS_URL = "https://finnhub.io/api/v1/news"


# ============================================================
# DATABASE
# ============================================================

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


# ============================================================
# FETCH NEWS FROM FINNHUB
# ============================================================

def fetch_news():

    print("Fetching financial news...")

    if not FINNHUB_API_KEY:
        print("❌ FINNHUB_API_KEY is missing in .env")
        return []

    try:

        params = {
            "category": "general",
            "token": FINNHUB_API_KEY
        }

        response = requests.get(
            FINNHUB_NEWS_URL,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, list):
            print("❌ Unexpected response from Finnhub")
            print(data)
            return []

        print(f"📰 News received: {len(data)}")

        return data

    except requests.exceptions.RequestException as e:

        print(f"❌ Error fetching news: {e}")

        return []


# ============================================================
# FILTER RELEVANT METALS NEWS
# ============================================================

def filter_relevant_news(articles):

    relevant = []

    keywords = [
        "gold",
        "silver",
        "precious metal",
        "precious metals",
        "bullion",
        "commodity",
        "metals",
        "fed",
        "federal reserve",
        "interest rate",
        "inflation",
        "tariff",
        "trump",
        "dollar",
        "usd"
    ]

    for article in articles:

        headline = article.get("headline", "")
        summary = article.get("summary", "")

        text = f"{headline} {summary}".lower()

        if any(keyword in text for keyword in keywords):
            relevant.append(article)

    print(f"🎯 Relevant news: {len(relevant)}")

    return relevant


# ============================================================
# SAVE NEWS TO POSTGRESQL
# ============================================================

def save_news(articles):

    if not articles:
        print("⚠️ No relevant news found")
        return 0

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        inserted = 0

        for article in articles:

            title = article.get("headline")
            summary = article.get("summary")
            source = article.get("source")
            url = article.get("url")

            # Finnhub timestamp is Unix timestamp
            timestamp = article.get("datetime")

            if timestamp:
                from datetime import datetime, timezone

                published_at = datetime.fromtimestamp(
                    timestamp,
                    tz=timezone.utc
                )
            else:
                published_at = None

            if not title or not url:
                continue

            try:

                cursor.execute(
                    """
                    INSERT INTO news_articles
                    (
                        title,
                        summary,
                        source,
                        url,
                        published_at
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO NOTHING
                    """,
                    (
                        title,
                        summary,
                        source,
                        url,
                        published_at
                    )
                )

                if cursor.rowcount > 0:
                    inserted += 1

            except Exception as e:

                print(f"⚠️ Error inserting article: {e}")

        conn.commit()

        cursor.close()
        conn.close()

        print(f"💾 New articles saved: {inserted}")

        return inserted

    except Exception as e:

        print(f"❌ Database error: {e}")

        return 0


# ============================================================
# MAIN COLLECTION PIPELINE
# ============================================================

def collect_news():

    print()
    print("=" * 60)
    print("📰 AUTOMATIC NEWS COLLECTION")
    print("=" * 60)

    articles = fetch_news()

    if not articles:
        print("⚠️ No news received")
        return

    relevant_articles = filter_relevant_news(articles)

    save_news(relevant_articles)

    print("=" * 60)
    print("✅ NEWS COLLECTION COMPLETED")
    print("=" * 60)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    collect_news()