from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import events
from app.api import market
from app.api import news
from app.api import speeches
from app.api import predictions
from app.api import historical
from app.api.market import fetch_market_data_from_db
from contextlib import asynccontextmanager

from app.config import scheduler, settings
from app.services.news_collector import collect_news



@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    print("🚀 Starting CommodityTrack API...")
    
    if not scheduler.running:
        # Add market data update job
        scheduler.add_job(
        collect_news,
        "interval",
        seconds=settings.NEWS_UPDATE_INTERVAL,
        id="news_data_update",
        name="News Data Update",
        replace_existing=True
    )
        scheduler.start()
        print("✅ Scheduler started - Market updates every 60 seconds")
    
    yield
    
    # SHUTDOWN
    if scheduler.running:
        scheduler.shutdown()
        print("✅ Scheduler stopped")
app = FastAPI(
    title="Gold & Silver Market Intelligence"
)

# Frontend to Backend API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router)
app.include_router(market.router)
app.include_router(news.router)
app.include_router(speeches.router)
app.include_router(predictions.router)
app.include_router(historical.router)

@app.get("/")
def root():
    return {
        "app": "Gold & Silver Market Intelligence",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }