"""
Demand Forecast LangGraph Agent for BloodBridge AI (A3).
Forecasts per-blood-type donation demand over the next 28 days
using bridge recurrence schedules and historical emergency requests.
"""

import logging
from datetime import date, timedelta, datetime
from typing import Dict, List, Any, TypedDict
from core.database import get_supabase_admin

logger = logging.getLogger(__name__)


class ForecastState(TypedDict, total=False):
    bridges: List[Dict[str, Any]]
    historical_requests: List[Dict[str, Any]]
    forecast_horizon_days: int
    forecast_by_blood_type: Dict[str, int]
    forecast_by_week: List[Dict[str, Any]]
    supply_by_blood_type: Dict[str, int]
    confidence_scores: Dict[str, float]
    shortage_alerts: List[str]
    agent_summary: str
    generated_at: str


# ── NODE 1: DATA COLLECTOR ────────────────────────────────────────────────────

def data_collector(state: ForecastState) -> dict:
    """Fetch bridges, historical requests, and eligible donor supply."""
    supabase = get_supabase_admin()
    horizon = state.get("forecast_horizon_days", 28)
    today = date.today()
    horizon_end = today + timedelta(days=horizon)

    # Bridges with upcoming transfusions
    bridges_res = supabase.table("bridges").select("*").execute()
    bridges = bridges_res.data or []

    # Filter bridges in horizon
    active_bridges = []
    for b in bridges:
        next_dt = b.get("expected_next_transfusion_date")
        if next_dt:
            try:
                nd = date.fromisoformat(str(next_dt)[:10])
                if nd <= horizon_end:
                    active_bridges.append(b)
            except Exception:
                pass

    # Historical emergency requests (last 90 days)
    ninety_ago = (today - timedelta(days=90)).isoformat()
    hist_res = supabase.table("emergency_requests")\
        .select("request_id, blood_type, created_at")\
        .gte("created_at", ninety_ago)\
        .execute()
    historical = hist_res.data or []

    # Eligible donor supply per blood type
    donors_res = supabase.table("donors")\
        .select("blood_type, next_eligible_date, is_active")\
        .eq("is_active", True)\
        .is_("medical_hold", False)\
        .execute()

    supply = {}
    for d in (donors_res.data or []):
        bt = d.get("blood_type", "Unknown")
        ned = d.get("next_eligible_date")
        eligible = True
        if ned:
            try:
                if date.fromisoformat(str(ned)[:10]) > today:
                    eligible = False
            except Exception:
                pass
        if eligible:
            supply[bt] = supply.get(bt, 0) + 1

    return {
        "bridges": active_bridges,
        "historical_requests": historical,
        "supply_by_blood_type": supply
    }


# ── NODE 2: SCHEDULE ANALYZER ─────────────────────────────────────────────────

def schedule_analyzer(state: ForecastState) -> dict:
    """Build week-by-week needed-units per blood type from bridge recurrence."""
    bridges = state.get("bridges", [])
    today = date.today()
    weeks = []

    for w in range(4):
        week_start = today + timedelta(weeks=w)
        week_end = week_start + timedelta(days=6)
        week_label = f"Week {w+1} ({week_start.strftime('%b %d')} - {week_end.strftime('%b %d')})"
        bt_counts: Dict[str, int] = {}

        for b in bridges:
            bt = b.get("bridge_blood_group", "Unknown")
            qty = int(b.get("quantity_required", 1) or 1)
            freq = int(b.get("frequency_in_days", 28) or 28)
            next_dt_str = b.get("expected_next_transfusion_date")
            if not next_dt_str:
                continue

            try:
                next_dt = date.fromisoformat(str(next_dt_str)[:10])
            except Exception:
                continue

            # Expand recurrence within this week
            current = next_dt
            while current <= week_end:
                if current >= week_start:
                    bt_counts[bt] = bt_counts.get(bt, 0) + qty
                current += timedelta(days=freq)

        weeks.append({"week_label": week_label, "blood_type_counts": bt_counts})

    # Aggregate total by blood type
    total_by_bt: Dict[str, int] = {}
    for w in weeks:
        for bt, cnt in w["blood_type_counts"].items():
            total_by_bt[bt] = total_by_bt.get(bt, 0) + cnt

    return {
        "forecast_by_week": weeks,
        "forecast_by_blood_type": total_by_bt
    }


# ── NODE 3: SUPPLY GAP NODE ──────────────────────────────────────────────────

def supply_gap_node(state: ForecastState) -> dict:
    """Compare demand vs supply; compute gaps and confidence scores."""
    demand = state.get("forecast_by_blood_type", {})
    supply = state.get("supply_by_blood_type", {})
    historical = state.get("historical_requests", [])

    # Historical multiplier: count emergencies per blood type
    hist_counts: Dict[str, int] = {}
    for req in historical:
        bt = req.get("blood_type", "Unknown")
        hist_counts[bt] = hist_counts.get(bt, 0) + 1

    total_hist = sum(hist_counts.values()) or 1
    hist_pct = {bt: cnt / total_hist for bt, cnt in hist_counts.items()}

    confidence: Dict[str, float] = {}
    shortage_alerts: List[str] = []
    all_types = set(list(demand.keys()) + list(supply.keys()))

    for bt in all_types:
        d = demand.get(bt, 0)
        s = supply.get(bt, 0)
        # Apply historical multiplier (e.g., O+ sees 20% more emergencies)
        multiplier = 1.0 + hist_pct.get(bt, 0.0)
        adjusted_demand = int(d * multiplier)

        if s > 0 and adjusted_demand > 0:
            ratio = s / adjusted_demand
            confidence[bt] = min(1.0, round(ratio, 2))
        elif adjusted_demand == 0:
            confidence[bt] = 1.0
        else:
            confidence[bt] = 0.0

        if adjusted_demand > s:
            gap = adjusted_demand - s
            shortage_alerts.append(
                f"⚠️ {bt}: Need {adjusted_demand} units, have {s} eligible donors. Gap: {gap}"
            )

    return {
        "confidence_scores": confidence,
        "shortage_alerts": shortage_alerts
    }


# ── NODE 4: BEDROCK INSIGHT NODE ──────────────────────────────────────────────

def bedrock_insight_node(state: ForecastState) -> dict:
    """Send structured forecast to Bedrock Claude for plain-English summary."""
    try:
        from core.llm_provider import get_reasoning_llm
        llm = get_reasoning_llm()

        prompt = (
            "You are a Blood Warriors NGO coordinator AI. Given the following 28-day forecast data, "
            "write a concise 3-paragraph summary: (1) overall demand outlook, (2) specific shortage "
            "risks by blood type, (3) one recommended action per under-supplied blood type.\n\n"
            f"Demand by blood type: {state.get('forecast_by_blood_type', {})}\n"
            f"Supply (eligible donors): {state.get('supply_by_blood_type', {})}\n"
            f"Shortage alerts: {state.get('shortage_alerts', [])}\n"
            f"Confidence scores: {state.get('confidence_scores', {})}\n"
            f"Weekly breakdown: {state.get('forecast_by_week', [])}\n"
        )

        response = llm.invoke(prompt)
        summary = response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        logger.error(f"Bedrock insight call failed: {e}")
        summary = (
            f"Demand forecast for next 28 days generated. "
            f"{len(state.get('shortage_alerts', []))} shortage alerts detected. "
            f"Blood types affected: {', '.join(state.get('forecast_by_blood_type', {}).keys())}."
        )

    return {"agent_summary": summary}


# ── NODE 5: PERSIST NODE ──────────────────────────────────────────────────────

def persist_node(state: ForecastState) -> dict:
    """Write forecast to demand_forecasts table and system_cache."""
    supabase = get_supabase_admin()
    now = datetime.utcnow().isoformat() + "Z"

    forecast_data = {
        "generated_at": now,
        "forecast_horizon_days": state.get("forecast_horizon_days", 28),
        "forecast_json": state.get("forecast_by_week", []),
        "supply_json": state.get("supply_by_blood_type", {}),
        "shortage_alerts": state.get("shortage_alerts", []),
        "ai_summary": state.get("agent_summary", ""),
        "blood_type_breakdown": state.get("forecast_by_blood_type", {})
    }

    try:
        supabase.table("demand_forecasts").insert(forecast_data).execute()
    except Exception as e:
        logger.warning(f"demand_forecasts insert failed (table may not exist): {e}")

    # Upsert system_cache
    try:
        import json
        supabase.table("system_cache").upsert({
            "cache_key": "latest_demand_forecast",
            "cache_value": json.dumps(forecast_data),
            "updated_at": now
        }).execute()
    except Exception as e:
        logger.warning(f"system_cache upsert failed: {e}")

    # Notify via ntfy if shortages
    if state.get("shortage_alerts"):
        try:
            import httpx
            alerts_text = "\n".join(state["shortage_alerts"][:5])
            httpx.post(
                "https://ntfy.sh/bloodbridge-alerts",
                data=f"🩸 Demand Forecast Alert\n{alerts_text}",
                headers={"Title": "BloodBridge Shortage Alert"}
            )
        except Exception:
            pass

    return {"generated_at": now}


# ── PIPELINE RUNNER ───────────────────────────────────────────────────────────

async def run_demand_forecast(horizon_days: int = 28) -> dict:
    """Execute the 5-node demand forecast pipeline sequentially."""
    logger.info("Starting demand forecast pipeline...")

    state: ForecastState = {"forecast_horizon_days": horizon_days}

    # Node 1
    state.update(data_collector(state))
    # Node 2
    state.update(schedule_analyzer(state))
    # Node 3
    state.update(supply_gap_node(state))
    # Node 4
    state.update(bedrock_insight_node(state))
    # Node 5
    state.update(persist_node(state))

    logger.info(f"Demand forecast complete. {len(state.get('shortage_alerts', []))} shortage alerts.")
    return state
