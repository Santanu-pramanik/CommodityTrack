import psycopg2
import requests

from datetime import datetime, timezone

from app.config import DATABASE_URL


BINANCE_SPOT_API = "https://api.binance.com/api/v3/ticker/24hr"
BINANCE_FUTURES_API = "https://fapi.binance.com/fapi/v1/ticker/24hr"


def get_json(url, symbol):
    response = requests.get(
        url,
        params={"symbol": symbol},
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, dict):
        raise ValueError(
            f"Invalid response for {symbol}: {data}"
        )

    if "lastPrice" not in data:
        raise ValueError(
            f"Price data missing for {symbol}: {data}"
        )

    return data


def save_market_data(
    cursor,
    metal_type,
    symbol,
    data,
    source
):
    price = float(data["lastPrice"])

    change_percent = float(
        data.get("priceChangePercent", 0.0)
    )

    volume = float(
        data.get("volume", 0.0)
    )

    timestamp = datetime.now(timezone.utc)

    cursor.execute(
        """
        INSERT INTO global_metals
        (
            metal_type,
            symbol,
            price,
            timestamp,
            created_at,
            change_percent,
            volume,
            source
        )
        VALUES
        (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            metal_type,
            symbol,
            price,
            timestamp,
            timestamp,
            change_percent,
            volume,
            source
        )
    )

    return price, change_percent, volume


def collect_market_data():

    if not DATABASE_URL:
        print("DATABASE_URL not configured")
        return

    conn = None
    cursor = None

    try:

        print(
            f"[{datetime.now()}] "
            "Collecting live market data..."
        )

        conn = psycopg2.connect(DATABASE_URL)

        cursor = conn.cursor()

        # --------------------------------------------------
        # GOLD
        # PAXG/USDT from Binance Spot
        # --------------------------------------------------

        try:

            gold_data = get_json(
                BINANCE_SPOT_API,
                "PAXGUSDT"
            )

            gold_price, gold_change, gold_volume = (
                save_market_data(
                    cursor=cursor,
                    metal_type="GOLD",
                    symbol="PAXG/USDT",
                    data=gold_data,
                    source="Binance Spot API"
                )
            )

            print(
                f"GOLD: ${gold_price:.2f} "
                f"({gold_change:+.2f}%)"
            )

        except Exception as error:

            print(
                f"Error collecting GOLD: {error}"
            )

        # --------------------------------------------------
        # SILVER
        # XAG/USDT from Binance Futures
        # --------------------------------------------------

        try:

            silver_data = get_json(
                BINANCE_FUTURES_API,
                "XAGUSDT"
            )

            silver_price, silver_change, silver_volume = (
                save_market_data(
                    cursor=cursor,
                    metal_type="SILVER",
                    symbol="XAG/USDT",
                    data=silver_data,
                    source="Binance Futures API"
                )
            )

            print(
                f"SILVER: ${silver_price:.2f} "
                f"({silver_change:+.2f}%)"
            )

        except Exception as error:

            print(
                f"Error collecting SILVER: {error}"
            )

        conn.commit()

        print(
            "Market data saved successfully\n"
        )

    except Exception as error:

        if conn:
            conn.rollback()

        print(
            f"Market collector error: {error}"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()