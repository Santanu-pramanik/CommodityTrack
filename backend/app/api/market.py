# backend/app/api/v1/market.py
"""
Market data endpoints with background scheduler and WebSocket
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import asyncio
import json

from app.config import DATABASE_URL, scheduler, settings

router = APIRouter(
    prefix="/api/market",
    tags=["Market"]
)

# Store WebSocket clients
connected_clients = set()

# ============================================================================
# HELPER FUNCTION - Fetch from Database
# ============================================================================

def fetch_market_data_from_db():
    """
    Fetch latest gold/silver prices from database
    Used by both REST endpoint and scheduler
    Returns: dict or None
    """
    if not DATABASE_URL:
        print("❌ DATABASE_URL not configured")
        return None

    try:
        print(f"[{datetime.now()}] 🔄 Fetching market data from DB...")
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT DISTINCT ON (metal_type)
                metal_type,
                symbol,
                price,
                change_percent,
                timestamp,
                source
            FROM latest_metal_prices
            ORDER BY metal_type, timestamp DESC;
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()

        if not rows:
            print("⚠️ No data found in database")
            return None

        print(f"✅ Rows fetched: {len(rows)}")

        # Parse data
        result = {
            "gold": None,
            "silver": None,
            "last_updated": datetime.now().isoformat()
        }

        for row in rows:
            # Handle NULL values safely
            change_pct = None
            if row['change_percent'] is not None:
                try:
                    change_pct = float(row['change_percent'])
                except:
                    change_pct = None

            price = None
            if row['price'] is not None:
                try:
                    price = float(row['price'])
                except:
                    price = None

            data = {
                "symbol": row['symbol'] or "N/A",
                "price": price,
                "change_percent": change_pct,
                "timestamp": row['timestamp'].isoformat() if row['timestamp'] else None,
                "source": row['source'] or "unknown"
            }

            if row['metal_type'].upper() == "GOLD":
                result["gold"] = data
                print(f"   💛 Gold: ${data['price']}")

            elif row['metal_type'].upper() == "SILVER":
                result["silver"] = data
                print(f"   ⚪ Silver: ${data['price']}")

        print(f"✅ Market data ready\n")
        
        # Broadcast to WebSocket clients (async in background)
        try:
            asyncio.create_task(broadcast_to_websockets(result))
        except RuntimeError:
            # No event loop running, skip broadcast
            pass
        
        return result

    except Exception as e:
        print(f"❌ Error fetching market data: {str(e)}")
        return None

# ============================================================================
# WEBSOCKET - Real-time Updates
# ============================================================================

async def broadcast_to_websockets(data: dict):
    """
    Send market data to all connected WebSocket clients
    """
    if not connected_clients:
        return  # No clients connected
    
    print(f"📡 Broadcasting to {len(connected_clients)} WebSocket clients...")
    
    disconnected = set()
    
    for client in connected_clients:
        try:
            await client.send_json({
                "type": "market_update",
                "data": data,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"⚠️ Error sending to WebSocket: {e}")
            disconnected.add(client)
    
    # Remove dead connections
    for client in disconnected:
        connected_clients.discard(client)
    
    if disconnected:
        print(f"🗑️ Removed {len(disconnected)} disconnected clients")

@router.websocket("/ws/market")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time market updates
    Clients connect here and receive updates every 60 seconds
    """
    await websocket.accept()
    connected_clients.add(websocket)
    
    print(f"✅ WebSocket client connected. Total: {len(connected_clients)}")
    
    try:
        # Send initial data
        data = fetch_market_data_from_db()
        if data:
            await websocket.send_json({
                "type": "initial_data",
                "data": data
            })
        
        # Keep connection alive with heartbeat
        while True:
            try:
                # Wait for message with timeout (prevents hanging)
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # 30 second timeout
                )
                # If we receive something, echo it back (ping/pong)
                await websocket.send_json({
                    "type": "pong",
                    "message": message
                })
            except asyncio.TimeoutError:
                # Timeout is OK, just keep connection alive
                continue
            except WebSocketDisconnect:
                break
            
    except Exception as e:
        print(f"⚠️ WebSocket error: {e}")
    finally:
        connected_clients.discard(websocket)
        print(f"❌ WebSocket client disconnected. Total: {len(connected_clients)}")

# ============================================================================
# REST ENDPOINTS
# ============================================================================

@router.get("/")
async def get_market_data():
    """
    Get latest market data (Gold & Silver)
    Endpoint: GET /api/market/
    """
    try:
        result = fetch_market_data_from_db()
        
        if result is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch market data from database"
            )
        
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

@router.get("/gold")
async def get_gold_price():
    """
    Get only GOLD price
    Endpoint: GET /api/market/gold
    """
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT * FROM latest_metal_prices 
            WHERE UPPER(metal_type) = 'GOLD'
            ORDER BY timestamp DESC
            LIMIT 1;
        """
        
        cursor.execute(query)
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="No gold price data found")
        
        return {
            "symbol": row['symbol'] or "GC=F",
            "price": float(row['price']) if row['price'] else None,
            "change_percent": float(row['change_percent']) if row['change_percent'] else None,
            "timestamp": row['timestamp'].isoformat() if row['timestamp'] else None,
            "source": row['source'] or "unknown"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/silver")
async def get_silver_price():
    """
    Get only SILVER price
    Endpoint: GET /api/market/silver
    """
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT * FROM latest_metal_prices 
            WHERE UPPER(metal_type) = 'SILVER'
            ORDER BY timestamp DESC
            LIMIT 1;
        """
        
        cursor.execute(query)
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="No silver price data found")
        
        return {
            "symbol": row['symbol'] or "SI=F",
            "price": float(row['price']) if row['price'] else None,
            "change_percent": float(row['change_percent']) if row['change_percent'] else None,
            "timestamp": row['timestamp'].isoformat() if row['timestamp'] else None,
            "source": row['source'] or "unknown"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{metal_type}")
async def get_price_history(metal_type: str, limit: int = 30):
    """
    Get price history for a metal (GOLD or SILVER)
    Endpoint: GET /api/market/history/gold?limit=30
    """
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")

    if limit > 365:
        limit = 365  # Max 1 year

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                metal_type,
                symbol,
                price,
                change_percent,
                timestamp,
                source
            FROM latest_metal_prices 
            WHERE UPPER(metal_type) = %s
            ORDER BY timestamp DESC
            LIMIT %s;
        """
        
        cursor.execute(query, (metal_type.upper(), limit))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not rows:
            raise HTTPException(status_code=404, detail=f"No price history found for {metal_type}")
        
        return {
            "metal_type": metal_type.upper(),
            "limit": limit,
            "total": len(rows),
            "data": [
                {
                    "price": float(row['price']) if row['price'] else None,
                    "change_percent": float(row['change_percent']) if row['change_percent'] else None,
                    "timestamp": row['timestamp'].isoformat() if row['timestamp'] else None,
                    "source": row['source'] or "unknown"
                }
                for row in rows
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_market_stats():
    """
    Get market statistics
    Endpoint: GET /api/market/stats
    """
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                metal_type,
                COUNT(*) as total_records,
                MIN(price) as min_price,
                MAX(price) as max_price,
                AVG(price) as avg_price,
                MAX(timestamp) as last_update
            FROM latest_metal_prices
            GROUP BY metal_type;
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        stats = {}
        for row in rows:
            stats[row['metal_type'].lower()] = {
                "total_records": row['total_records'],
                "min_price": float(row['min_price']) if row['min_price'] else None,
                "max_price": float(row['max_price']) if row['max_price'] else None,
                "avg_price": float(row['avg_price']) if row['avg_price'] else None,
                "last_update": row['last_update'].isoformat() if row['last_update'] else None
            }
        
        return stats
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))