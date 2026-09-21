import yfinance as yf
import psycopg2
from datetime import datetime, timezone
from app.config import DATABASE_URL


def collect_market_data():

    if not DATABASE_URL:
        print("DATABASE_URL not configured")
        return

    try:
        print(f"[{datetime.now()}] Collecting market data...")

        symbols = {
            "GOLD": "GC=F",
            "SILVER": "SI=F"
        }

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        for metal_type, symbol in symbols.items():

            try:
                ticker = yf.Ticker(symbol)

                history = ticker.history(
                    period="1d",
                    interval="1m"
                )

                if history.empty:
                    print(f"No data for {symbol}")
                    continue

                latest = history.iloc[-1]

                price = float(latest["Close"])

                # Previous close
                previous_close = None

                try:
                    previous_close = ticker.fast_info.get("previous_close")
                except Exception:
                    pass

                change_percent = None

                if previous_close:
                    change_percent = (
                        (price - float(previous_close))
                        / float(previous_close)
                    ) * 100

                # Volume
                volume = None

                try:
                    if latest["Volume"]:
                        volume = float(latest["Volume"])
                except Exception:
                    pass

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
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        metal_type,
                        symbol,
                        price,
                        timestamp,
                        timestamp,
                        change_percent,
                        volume,
                        "Yahoo Finance"
                    )
                )

                if change_percent is not None:
                    print(
                        f"{metal_type}: "
                        f"${price:.2f} "
                        f"({change_percent:+.2f}%)"
                    )
                else:
                    print(
                        f"{metal_type}: "
                        f"${price:.2f}"
                    )

            except Exception as metal_error:
                print(
                    f"Error collecting {metal_type}: "
                    f"{metal_error}"
                )

        conn.commit()

        cursor.close()
        conn.close()

        print("Market data saved successfully\n")

    except Exception as e:
        print(f"Market collector error: {e}")