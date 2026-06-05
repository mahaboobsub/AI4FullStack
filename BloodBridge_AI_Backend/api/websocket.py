"""
WebSocket connection handlers for BloodBridge AI real-time dashboard.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime
import logging
from core.ws_manager import ws_manager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/emergencies")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Push initial state with active emergencies to the client on connection
        from core.database import get_supabase_admin
        supabase = get_supabase_admin()
        
        res = supabase.table("emergency_requests").select("*").eq("status", "IN_PROGRESS").execute()
        active_emergencies = res.data or []
        
        for idx, emp in enumerate(active_emergencies):
            req_id = emp["request_id"]
            res_nodes = supabase.table("blood_chains")\
                .select("*")\
                .eq("request_id", req_id)\
                .order("chain_position")\
                .execute()
            active_emergencies[idx]["chain"] = res_nodes.data or []
            
        await websocket.send_json({
            "type": "initial_state",
            "data": active_emergencies,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
        import asyncio
        async def keep_alive():
            try:
                while True:
                    await asyncio.sleep(30)
                    await websocket.send_json({
                        "type": "ping",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    })
            except Exception:
                pass

        keep_alive_task = asyncio.create_task(keep_alive())
        try:
            while True:
                await websocket.receive_text()
        finally:
            keep_alive_task.cancel()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)

