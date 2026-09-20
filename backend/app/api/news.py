from fastapi import APIRouter, HTTPException
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/api/news",
    tags=["News"]
)

DATABASE_URL = os.getenv("DATABASE_URL")


@router.get("/")
def get_news(limit: int = 20):

    if not DATABASE_URL:
        raise HTTPException(
            status_code=500,
            detail="DATABASE_URL is not configured"
        )

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        query = """
            SELECT
                id,
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
                is_trump_related
            FROM news_articles
            ORDER BY published_at DESC
            LIMIT %s;
        """

        cursor.execute(query, (limit,))
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        news = []

        for row in rows:
            news.append({
                "id": row[0],
                "title": row[1],
                "summary": row[2],
                "source": row[3],
                "url": row[4],
                "published_at": (
                    row[5].isoformat()
                    if row[5]
                    else None
                ),
                "symbol": row[6],
                "metal_type": row[7],
                "sentiment": row[8],
                "sentiment_score": (
                    float(row[9])
                    if row[9] is not None
                    else None
                ),
                "impact": row[10],
                "keywords": row[11],
                "is_trump_related": row[12]
            })

        return {
            "count": len(news),
            "news": news
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )