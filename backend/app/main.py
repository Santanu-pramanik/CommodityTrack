from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import events
from app.api import market
from app.api import news
from app.api import speeches
from app.api import predictions
from app.api import historical

from app.config import scheduler, settings
from app.services.news_collector import collect_news
from app.services.market_collector import collect_market_data
from app.services.event_collector import collect_events
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):

    print("Starting CommodityTrack API...")

    try:
        
        # Run initial data collection
        print("Running initial market data collection...")
        await asyncio.to_thread(collect_market_data)


        print("Running initial economic event collection...")
        await asyncio.to_thread(collect_events)

        # Schedule news updates
        scheduler.add_job(
            collect_news,
            "interval",
            seconds=settings.NEWS_UPDATE_INTERVAL,
            id="news_data_update",
            name="News Data Update",
            replace_existing=True
        )

        # Schedule economic event updates
        scheduler.add_job(
            collect_events,
            "interval",
            hours=1,
            id="economic_events_update",
            name="Economic Events Update",
            replace_existing=True
        )

        # Schedule market updates
        scheduler.add_job(
            collect_market_data,
            "interval",
            seconds=settings.MARKET_UPDATE_INTERVAL,
            id="market_data_update",
            name="Market Data Update",
            replace_existing=True
        )

        # Start scheduler
        if not scheduler.running:
            scheduler.start()

        print(
            f"Scheduler started. "
            f"Market updates every {settings.MARKET_UPDATE_INTERVAL} seconds."
        )

    except Exception as e:
        print(f"Scheduler startup error: {e}")

    yield

    # Shutdown scheduler
    if scheduler.running:
        scheduler.shutdown()
        print("Scheduler stopped.")


app = FastAPI(
    title="Gold & Silver Market Intelligence",
    lifespan=lifespan
)


# CORS configuration

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://commoditytrack-production-2084.up.railway.app",
        "https://commoditytrack-production-5160.up.railway.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex=r"https://.*\.railway\.app",
    expose_headers=["*"]
)


# Register API routers

app.include_router(events.router)
app.include_router(market.router)
app.include_router(news.router)
app.include_router(speeches.router)
app.include_router(predictions.router)
app.include_router(historical.router)


# Root endpoint

@app.get("/")
def root():
    return {
        "app": "Gold & Silver Market Intelligence",
        "status": "running"
    }


# Health endpoint

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }