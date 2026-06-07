"""Persist OCR/VLM scan results to Supabase, Neo4j, and admin WebSocket."""
import json
import logging
from typing import Any, Dict, Optional

from core.database import get_supabase_admin
from core.time_utils import utc_now_iso
from core.neo4j_client import get_driver

logger = logging.getLogger(__name__)


def format_antigen_summary(panel: dict) -> str:
    """Human-readable antigen line for Telegram/admin, e.g. 'D+, K−, Fya+'."""
    if not panel:
        return "not detected"
    parts = []
    for key in sorted(panel.keys()):
        val = panel[key]
        if isinstance(val, str) and val.lower().startswith("pos"):
            parts.append(f"{key}+")
        elif isinstance(val, str) and val.lower().startswith("neg"):
            parts.append(f"{key}−")
        else:
            parts.append(f"{key}:{val}")
    return ", ".join(parts) if parts else "not detected"


async def sync_ocr_to_neo4j_and_graph(donor_id: str, result: dict) -> None:
    """Rebuild COMPATIBLE_WITH edges and push realtime update to admin graph."""
    flags = result.get("antigen_flags") or {}
    panel = result.get("antigen_panel") or {}

    try:
        from agents.neo4j_match import Neo4jMatcher
        await Neo4jMatcher.rebuild_edges_for_donor(donor_id)
    except Exception as e:
        logger.warning(f"Neo4j edge rebuild after OCR failed for {donor_id}: {e}")

    try:
        driver = get_driver()
        if driver:
            async with driver.session() as session:
                await session.run(
                    """
                    MATCH (d:Donor {donor_id: $donor_id})
                    SET d.kell_negative = coalesce($kell_negative, d.kell_negative),
                        d.duffy_negative = coalesce($duffy_negative, d.duffy_negative),
                        d.kidd_negative = coalesce($kidd_negative, d.kidd_negative),
                        d.rh_e_negative = coalesce($rh_e_negative, d.rh_e_negative),
                        d.rh_c_negative = coalesce($rh_c_negative, d.rh_c_negative),
                        d.mns_negative = coalesce($mns_negative, d.mns_negative),
                        d.antigen_panel_json = $panel_json,
                        d.ocr_updated_at = datetime()
                    """,
                    donor_id=donor_id,
                    kell_negative=flags.get("kell_negative"),
                    duffy_negative=flags.get("duffy_negative"),
                    kidd_negative=flags.get("kidd_negative"),
                    rh_e_negative=flags.get("rh_e_negative"),
                    rh_c_negative=flags.get("rh_c_negative"),
                    mns_negative=flags.get("mns_negative"),
                    panel_json=json.dumps(panel),
                )
    except Exception as e:
        logger.warning(f"Neo4j donor antigen property update failed for {donor_id}: {e}")

    try:
        from api.websocket import ws_manager
        await ws_manager.broadcast({
            "type": "ocr_scan_complete",
            "donor_id": donor_id,
            "blood_group": result.get("blood_group"),
            "name": result.get("name"),
            "antigen_panel": panel,
            "antigen_flags": flags,
            "antigen_summary": format_antigen_summary(panel),
        })
    except Exception as e:
        logger.debug(f"WebSocket broadcast after OCR skipped: {e}")


async def persist_ocr_results(donor_id: Optional[str], result: dict) -> None:
    """Write OCR extraction to Supabase donor row + verifications audit."""
    if not donor_id:
        return

    supabase = get_supabase_admin()
    blood_group = result.get("blood_group")
    donor_name = result.get("name")
    flags = result.get("antigen_flags") or {}
    panel = result.get("antigen_panel") or {}

    update_payload: Dict[str, Any] = {"updated_at": utc_now_iso()}
    if blood_group:
        update_payload["blood_type"] = blood_group
    if donor_name:
        update_payload["name"] = donor_name
    if flags:
        update_payload.update(flags)
    if panel:
        update_payload["antigen_data"] = panel

    try:
        supabase.table("donors").update(update_payload).eq("donor_id", donor_id).execute()
    except Exception as e:
        # antigen_data column may not exist on older schemas — retry without it
        if "antigen_data" in update_payload:
            update_payload.pop("antigen_data", None)
            try:
                supabase.table("donors").update(update_payload).eq("donor_id", donor_id).execute()
            except Exception as e2:
                logger.error(f"Failed to update donor {donor_id} after OCR: {e2}")
        else:
            logger.error(f"Failed to update donor {donor_id} after OCR: {e}")

    try:
        supabase.table("donor_verifications").insert({
            "donor_id": donor_id,
            "antigen_flag": "ocr_card",
            "flag_value": True,
            "verification_type": "ocr_card",
            "confidence": 0.95 if blood_group else 0.5,
            "notes": json.dumps({
                "antigen_panel": panel,
                "antigen_flags": flags,
                "ocr_source": result.get("ocr_source", []),
                "vision_confidence": result.get("vision_confidence", 0.0),
                "raw_sample": (result.get("raw_text") or "")[:200],
            })[:500],
        }).execute()
    except Exception as e:
        logger.debug(f"donor_verifications insert skipped: {e}")

    await sync_ocr_to_neo4j_and_graph(donor_id, result)
