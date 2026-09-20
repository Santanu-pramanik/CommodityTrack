# backend/app/config.py
"""
Configuration for scheduled tasks and settings
"""

from apscheduler.schedulers.background import BackgroundScheduler
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Initialize scheduler (globally)
scheduler = BackgroundScheduler()

class Settings:
    """App settings"""
    DATABASE_URL = DATABASE_URL
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    DEBUG = os.getenv("DEBUG", False)
    NEWS_UPDATE_INTERVAL = 10 * 60
    
    # Scheduler settings
    MARKET_UPDATE_INTERVAL = 60  # seconds
    LOG_UPDATES = True

settings = Settings()