import psycopg2
import requests
from datetime import datetime, timezone
from app.config import DATABASE_URL


def collect_market_data():
    if not DATABASE_URL:
        print("DATABASE_URL not configured")
        return

    try:
        print(f"[{datetime.now()}] Collecting live market data...")

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # 1. Gold Price (PAXG/USDT from Binance)
        try:
            gold_res = requests.get("https://api.binance.com/api/v3/ticker/24hr?symbol=PAXGUSDT", timeout=10).json()
            gold_price = float(gold_res["lastPrice"])
            gold_change = float(gold_res["priceChangePercent"])
            gold_volume = float(gold_res["volume"])
            timestamp = datetime.now(timezone.utc)

            cursor.execute(
                """
                INSERT INTO global_metals (metal_type, symbol, price, timestamp, created_at, change_percent, volume, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                ("GOLD", "PAXG/USDT", gold_price, timestamp, timestamp, gold_change, gold_volume, "Binance API")
            )
            print(f"GOLD: ${gold_price:.2f} ({gold_change:+.2f}%)")
        except Exception as e:
            print(f"Error collecting GOLD: {e}")

        # 2. Silver Price (XAG/USDT from Binance)
        try:
            silver_res = requests.get("https://api.binance.com/api/v3/ticker/24hr?symbol=XAGUSDT", timeout=10).json()
            
            # Check if API returned valid data
            if "lastPrice" in silver_res:
                silver_price = float(silver_res["lastPrice"])
                silver_change = float(silver_res.get("priceChangePercent", 0.0)) # Percentage change
                silver_volume = float(silver_res.get("volume", 0.0))
                timestamp = datetime.now(timezone.utc)

                cursor.execute(
                    """
                    INSERT INTO global_metals (metal_type, symbol, price, timestamp, created_at, change_percent, volume, source)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    ("SILVER", "XAG/USDT", silver_price, timestamp, timestamp, silver_change, silver_volume, "Binance API")
                )
                print(f"SILVER: ${silver_price:.2f} ({silver_change:+.2f}%)")
            else:
                print("Silver data key missing in response")

        except Exception as e:
            print(f"Error collecting SILVER: {e}")

        conn.commit()
        cursor.close()
        conn.close()

        print("Market data saved successfully\n")

    except Exception as e:
        print(f"Market collector error: {e}")