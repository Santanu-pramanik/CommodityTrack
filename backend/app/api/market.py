"""
Market API
- Latest Gold/Silver price
- Price history
- Real OHLC candles generated from global_metals
- WebSocket live updates
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from psycopg2.extras import RealDictCursor
import psycopg2
from datetime import datetime
import asyncio

from app.config import DATABASE_URL


router = APIRouter(
    prefix="/api/market",
    tags=["Market"]
)


# ============================================================
# WEBSOCKET CLIENTS
# ============================================================

connected_clients = set()


# ============================================================
# DATABASE HELPER
# ============================================================

def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not configured")

    return psycopg2.connect(
        DATABASE_URL,
        connect_timeout=5
    )

# ============================================================
# LATEST MARKET DATA
# ============================================================

def fetch_latest_market_data():

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT DISTINCT ON (UPPER(metal_type))
                metal_type,
                symbol,
                price,
                change_percent,
                timestamp,
                volume,
                source
            FROM global_metals
            WHERE UPPER(metal_type) IN ('GOLD', 'SILVER')
            ORDER BY UPPER(metal_type), timestamp DESC, id DESC;
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        result = {
            "gold": None,
            "silver": None,
            "last_updated": datetime.utcnow().isoformat()
        }

        for row in rows:

            data = {
                "symbol": row["symbol"],
                "price": float(row["price"]) if row["price"] is not None else None,
                "change_percent": (
                    float(row["change_percent"])
                    if row["change_percent"] is not None
                    else 0.0
                ),
                "volume": (
                    int(row["volume"])
                    if row["volume"] is not None
                    else 0
                ),
                "timestamp": (
                    row["timestamp"].isoformat()
                    if row["timestamp"]
                    else None
                ),
                "source": row["source"]
            }

            metal = row["metal_type"].upper()

            if metal == "GOLD":
                result["gold"] = data

            elif metal == "SILVER":
                result["silver"] = data

        return result

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ============================================================
# BROADCAST
# ============================================================

async def broadcast_to_websockets(data):

    if not connected_clients:
        return

    disconnected = set()

    for client in connected_clients:

        try:

            await client.send_json({
                "type": "market_update",
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })

        except Exception:
            disconnected.add(client)

    for client in disconnected:
        connected_clients.discard(client)


# ============================================================
# ALL MARKET DATA
# ============================================================

@router.get("/")
def get_market_data():

    try:

        data = fetch_latest_market_data()

        if not data["gold"] and not data["silver"]:
            raise HTTPException(
                status_code=404,
                detail="No market data available"
            )

        return data

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Market database error: {str(e)}"
        )


# ============================================================
# GOLD
# ============================================================

@router.get("/gold")
async def get_gold_price():

    conn = None
    cursor = None

    try:

        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT
                metal_type,
                symbol,
                price,
                change_percent,
                timestamp,
                volume,
                source
            FROM global_metals
            WHERE metal_type = 'GOLD'
            ORDER BY timestamp DESC, id DESC
            LIMIT 1;
        """)

        row = cursor.fetchone()

        if not row:

            raise HTTPException(
                status_code=404,
                detail="No gold price data found"
            )

        return {
            "metal_type": "GOLD",
            "symbol": row["symbol"],
            "price": float(row["price"]),
            "change_percent": (
                float(row["change_percent"])
                if row["change_percent"] is not None
                else 0.0
            ),
            "volume": (
                int(row["volume"])
                if row["volume"] is not None
                else 0
            ),
            "timestamp": (
                row["timestamp"].isoformat()
                if row["timestamp"]
                else None
            ),
            "source": row["source"]
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Gold API error: {str(e)}"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ============================================================
# SILVER
# ============================================================

@router.get("/silver")
def get_silver_price():

    conn = None
    cursor = None

    try:

        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT
                metal_type,
                symbol,
                price,
                change_percent,
                timestamp,
                volume,
                source
            FROM global_metals
            WHERE metal_type = 'SILVER'
            ORDER BY timestamp DESC, id DESC
            LIMIT 1;
        """)

        row = cursor.fetchone()

        if not row:

            raise HTTPException(
                status_code=404,
                detail="No silver price data found"
            )

        return {
            "metal_type": "SILVER",
            "symbol": row["symbol"],
            "price": float(row["price"]),
            "change_percent": (
                float(row["change_percent"])
                if row["change_percent"] is not None
                else 0.0
            ),
            "volume": (
                int(row["volume"])
                if row["volume"] is not None
                else 0
            ),
            "timestamp": (
                row["timestamp"].isoformat()
                if row["timestamp"]
                else None
            ),
            "source": row["source"]
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Silver API error: {str(e)}"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ============================================================
# PRICE HISTORY
# ============================================================

@router.get("/history/{metal_type}")
def get_price_history(
    metal_type: str,
    limit: int = 100
):

    metal = metal_type.upper()

    if metal not in ["GOLD", "SILVER"]:

        raise HTTPException(
            status_code=400,
            detail="metal_type must be GOLD or SILVER"
        )

    limit = max(1, min(limit, 5000))

    conn = None
    cursor = None

    try:

        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT
                id,
                metal_type,
                symbol,
                price,
                change_percent,
                timestamp,
                volume,
                source
            FROM global_metals
            WHERE UPPER(metal_type) = %s
            ORDER BY timestamp DESC, id DESC
            LIMIT %s;
        """, (metal, limit))

        rows = cursor.fetchall()

        # Oldest -> newest
        rows.reverse()

        data = []

        for row in rows:

            data.append({
                "id": row["id"],
                "price": float(row["price"]),
                "change_percent": (
                    float(row["change_percent"])
                    if row["change_percent"] is not None
                    else 0.0
                ),
                "timestamp": (
                    row["timestamp"].isoformat()
                    if row["timestamp"]
                    else None
                ),
                "volume": (
                    int(row["volume"])
                    if row["volume"] is not None
                    else 0
                ),
                "source": row["source"]
            })

        return {
            "metal_type": metal,
            "limit": limit,
            "total": len(data),
            "data": data
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"History API error: {str(e)}"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ============================================================
# REAL OHLC CANDLES
# ============================================================

@router.get("/candles/{metal_type}")
def get_market_candles(
    metal_type: str,
    interval: str = "5m",
    days: int = 1
):

    metal = metal_type.upper()

    if metal not in ["GOLD", "SILVER"]:

        raise HTTPException(
            status_code=400,
            detail="metal_type must be GOLD or SILVER"
        )

    allowed_intervals = {
        "1m": "1 minute",
        "5m": "5 minutes",
        "15m": "15 minutes",
        "30m": "30 minutes",
        "1h": "1 hour",
        "4h": "4 hours",
        "1d": "1 day"
    }

    if interval not in allowed_intervals:

        raise HTTPException(
            status_code=400,
            detail="Invalid interval"
        )

    days = max(1, min(days, 30))

    bucket = allowed_intervals[interval]

    conn = None
    cursor = None

    try:

        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = f"""
            SELECT
                date_trunc(
                    'minute',
                    timestamp
                )
                -
                (
                    EXTRACT(
                        minute FROM timestamp
                    )::int % %s
                ) * INTERVAL '1 minute'
                AS candle_time,

                (
                    array_agg(
                        price
                        ORDER BY timestamp ASC, id ASC
                    )
                )[1] AS open,

                MAX(price) AS high,

                MIN(price) AS low,

                (
                    array_agg(
                        price
                        ORDER BY timestamp DESC, id DESC
                    )
                )[1] AS close,

                SUM(volume) AS volume

            FROM global_metals

            WHERE UPPER(metal_type) = %s
              AND timestamp >= NOW() - INTERVAL '{days} days'

            GROUP BY candle_time

            ORDER BY candle_time ASC;
        """

        # Convert interval to minutes
        interval_minutes = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "4h": 240,
            "1d": 1440
        }[interval]

        cursor.execute(
            query,
            (interval_minutes, metal)
        )

        rows = cursor.fetchall()

        candles = []

        for row in rows:

            candles.append({
                "time": row["candle_time"].isoformat(),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": (
                    float(row["volume"])
                    if row["volume"] is not None
                    else 0
                )
            })

        return {
            "metal_type": metal,
            "interval": interval,
            "days": days,
            "total": len(candles),
            "data": candles
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Candle API error: {str(e)}"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ============================================================
# STATS
# ============================================================

@router.get("/stats")
def get_market_stats():

    conn = None
    cursor = None

    try:

        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT
                metal_type,
                COUNT(*) AS total_records,
                MIN(price) AS min_price,
                MAX(price) AS max_price,
                AVG(price) AS avg_price,
                MAX(timestamp) AS last_update
            FROM global_metals
            GROUP BY metal_type;
        """)

        rows = cursor.fetchall()

        stats = {}

        for row in rows:

            stats[row["metal_type"].lower()] = {
                "total_records": row["total_records"],
                "min_price": (
                    float(row["min_price"])
                    if row["min_price"] is not None
                    else None
                ),
                "max_price": (
                    float(row["max_price"])
                    if row["max_price"] is not None
                    else None
                ),
                "avg_price": (
                    float(row["avg_price"])
                    if row["avg_price"] is not None
                    else None
                ),
                "last_update": (
                    row["last_update"].isoformat()
                    if row["last_update"]
                    else None
                )
            }

        return stats

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Stats API error: {str(e)}"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ============================================================
# WEBSOCKET
# ============================================================

@router.websocket("/ws/market")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()

    connected_clients.add(websocket)

    try:

        # Initial data
        data = fetch_latest_market_data()

        if data:

            await websocket.send_json({
                "type": "initial_data",
                "data": data
            })

        while True:

            try:

                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30
                )

                await websocket.send_json({
                    "type": "pong",
                    "message": message
                })

            except asyncio.TimeoutError:

                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                })

    except WebSocketDisconnect:
        pass

    except Exception as e:
        print(f"WebSocket error: {e}")

    finally:

        connected_clients.discard(websocket)