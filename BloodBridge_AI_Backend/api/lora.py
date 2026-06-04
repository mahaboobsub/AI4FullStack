"""
LoRa offline communication bridge REST API routes for BloodBridge AI.

Endpoints:
  POST /api/lora/receive  — Accept decoded LoRa packet from gateway, trigger emergency pipeline
  GET  /api/lora/status   — Return gateway connectivity status + queue depth
  POST /api/lora/flush    — Manually trigger offline queue flush
"""
import time
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional

from services.lora_bridge import (
    LoRaPacket,
    store_offline_packet,
    flush_offline_queue,
    get_queue_depth,
    encode_lora_packet,
    decode_lora_packet,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/lora", tags=["lora-offline"])


# ── Pydantic Schemas ──────────────────────────────────────────────────────────
class LoRaReceiveRequest(BaseModel):
    """Decoded LoRa packet payload posted by the gateway bridge."""
    request_id: str = Field(..., description="8-char emergency request identifier")
    patient_id: str = Field(..., description="8-char patient identifier")
    blood_type: str = Field(..., description="Blood type needed e.g. O-")
    urgency_level: str = Field(..., description="LOW / MEDIUM / HIGH / CRITICAL")
    city: str = Field(..., description="Patient's city (max 20 chars)")
    hospital_name: str = Field("", description="Hospital name (max 30 chars, optional)")
    units_needed: int = Field(1, ge=1, le=10, description="Units of blood required")
    source: str = Field("lora", description="Packet source identifier")
    original_timestamp: Optional[int] = Field(None, description="Original transmission Unix timestamp")


class LoRaReceiveResponse(BaseModel):
    success: bool
    emergency_id: Optional[str]
    queued_offline: bool
    message: str


class LoRaStatusResponse(BaseModel):
    gateway_online: bool
    queue_depth: int
    last_packet_received_at: Optional[int]
    api_version: str


class LoRaFlushResponse(BaseModel):
    success: bool
    flushed_count: int
    failed_count: int
    errors: list[str]


class LoRaEncodeRequest(BaseModel):
    """Utility endpoint: encode a dict to binary LoRa packet (hex)."""
    emergency: dict


# ── State ─────────────────────────────────────────────────────────────────────
_last_packet_ts: Optional[int] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/receive", response_model=LoRaReceiveResponse, summary="Receive decoded LoRa packet")
async def receive_lora_packet(
    payload: LoRaReceiveRequest,
    background_tasks: BackgroundTasks
):
    """
    POST /api/lora/receive
    ---
    Receives a decoded emergency LoRa packet from the gateway bridge.
    Validates the packet, then triggers the BloodBridge emergency pipeline
    as a background task (non-blocking — gateway must return quickly to receive next packet).

    If the API cannot reach Supabase, stores the packet offline and returns 202.
    """
    global _last_packet_ts
    _last_packet_ts = int(time.time())

    logger.info(
        f"LoRa packet received: request_id={payload.request_id} "
        f"blood={payload.blood_type} urgency={payload.urgency_level} "
        f"city={payload.city} source={payload.source}"
    )

    # Validate blood type
    valid_blood_types = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
    if payload.blood_type.upper() not in valid_blood_types:
        raise HTTPException(status_code=400, detail=f"Invalid blood_type: {payload.blood_type}")

    # Validate urgency
    valid_urgency = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    if payload.urgency_level.upper() not in valid_urgency:
        raise HTTPException(status_code=400, detail=f"Invalid urgency_level: {payload.urgency_level}")

    # Build emergency record
    emergency_data = {
        "blood_type": payload.blood_type.upper(),
        "urgency_level": payload.urgency_level.upper(),
        "city": payload.city,
        "hospital_name": payload.hospital_name,
        "units_needed": payload.units_needed,
        "source": payload.source,
        "lora_request_id": payload.request_id,
        "lora_patient_id": payload.patient_id,
        "lora_timestamp": payload.original_timestamp or _last_packet_ts,
    }

    # Attempt to create emergency record in Supabase + trigger pipeline
    emergency_id = None
    pipeline_queued = False
    stored_offline = False

    try:
        from core.database import get_supabase_admin
        supabase = get_supabase_admin()

        # Create emergency record
        res = supabase.table("blood_requests").insert({
            "blood_type": emergency_data["blood_type"],
            "urgency_level": emergency_data["urgency_level"],
            "city": emergency_data["city"],
            "hospital_name": emergency_data["hospital_name"],
            "units_needed": emergency_data["units_needed"],
            "status": "PENDING",
            "source": "lora_offline",
            "notes": f"LoRa packet from gateway. Original request_id: {payload.request_id}"
        }).execute()

        if res.data:
            emergency_id = res.data[0].get("request_id")

        # Trigger emergency pipeline as background task
        async def run_pipeline(eid: str):
            try:
                from agents.graph import run_emergency_pipeline
                await run_emergency_pipeline(eid)
            except Exception as e:
                logger.error(f"LoRa pipeline failed for emergency {eid}: {e}", exc_info=True)

        if emergency_id:
            background_tasks.add_task(run_pipeline, emergency_id)
            pipeline_queued = True
            logger.info(f"LoRa emergency {emergency_id} queued for pipeline processing.")

    except Exception as e:
        logger.warning(f"BloodBridge API unavailable, storing LoRa packet offline: {e}")
        # Store offline for later flush
        lora_packet = LoRaPacket(
            request_id=payload.request_id,
            patient_id=payload.patient_id,
            blood_type=payload.blood_type.upper(),
            city=payload.city,
            urgency=payload.urgency_level.upper(),
            timestamp=payload.original_timestamp or int(time.time()),
            hospital_name=payload.hospital_name,
            units_needed=payload.units_needed,
        )
        stored_offline = store_offline_packet(lora_packet)

    return LoRaReceiveResponse(
        success=pipeline_queued or stored_offline,
        emergency_id=emergency_id,
        queued_offline=stored_offline,
        message=(
            f"Emergency pipeline triggered for {payload.blood_type} in {payload.city}."
            if pipeline_queued
            else f"Stored offline (queue depth: {get_queue_depth()}). Will retry when connectivity restores."
            if stored_offline
            else "Failed to process packet."
        )
    )


@router.get("/status", response_model=LoRaStatusResponse, summary="LoRa gateway status")
async def get_lora_status():
    """
    GET /api/lora/status
    ---
    Returns LoRa gateway connectivity status and offline queue depth.
    Used by the dashboard to show rural connectivity state.
    """
    queue_depth = get_queue_depth()
    return LoRaStatusResponse(
        gateway_online=True,   # Server is up; field gateway connectivity is separate concern
        queue_depth=max(0, queue_depth),
        last_packet_received_at=_last_packet_ts,
        api_version="1.0.0"
    )


@router.post("/flush", response_model=LoRaFlushResponse, summary="Flush offline LoRa queue")
async def flush_lora_queue(background_tasks: BackgroundTasks):
    """
    POST /api/lora/flush
    ---
    Manually triggers a flush of all offline-stored LoRa packets to the
    BloodBridge emergency pipeline. Call this when connectivity is restored.

    The flush runs as a background task — response is returned immediately.
    Check GET /api/lora/status to monitor queue_depth going to 0.
    """
    queue_depth = get_queue_depth()
    if queue_depth == 0:
        return LoRaFlushResponse(
            success=True,
            flushed_count=0,
            failed_count=0,
            errors=[]
        )

    logger.info(f"Manual LoRa queue flush triggered. Queue depth: {queue_depth}")

    # Run flush and return result
    result = await flush_offline_queue()

    return LoRaFlushResponse(
        success=result["flushed"] > 0,
        flushed_count=result["flushed"],
        failed_count=result["failed"],
        errors=result["errors"]
    )


@router.post("/encode-test", summary="Encode emergency to binary LoRa packet (debug)")
async def encode_lora_test(payload: LoRaEncodeRequest):
    """
    POST /api/lora/encode-test
    ---
    Debug utility: encode an emergency dict to a LoRa binary packet and return
    the hex representation. Useful for testing the gateway firmware.
    """
    try:
        encoded = encode_lora_packet(payload.emergency)
        decoded = decode_lora_packet(encoded)
        return {
            "hex": encoded.hex(),
            "size_bytes": len(encoded),
            "decoded": decoded,
            "lora_sf12_airtime_ms": round(len(encoded) * 8 / 250 * 1000, 1)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Encoding failed: {e}")
