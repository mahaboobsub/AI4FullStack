"""
Blood bank inventory scraper for BloodBridge AI.
3-tier fallback: Neo4j graph → e-RaktKosh national portal API → local seed data.
Used by InventoryAgent when the entire donor chain fails.

e-RaktKosh (eraktkosh.in) is India's Ministry of Health national blood bank portal.
"""
import logging
import asyncio
import httpx
from typing import Optional
from core.neo4j_client import get_driver

logger = logging.getLogger(__name__)

# ── e-RaktKosh API config ─────────────────────────────────────────────────────
ERAKTKOSH_BASE_URL = "https://eraktkosh.in"
ERAKTKOSH_SEARCH_URL = f"{ERAKTKOSH_BASE_URL}/BLDAHIMS/bloodbank/nearbyBB.cnt"
ERAKTKOSH_TIMEOUT = 8.0          # seconds
ERAKTKOSH_MAX_RETRIES = 2

# Mapping from our blood type strings → e-RaktKosh blood component codes
BLOOD_TYPE_CODES = {
    "A+":  {"group": "1", "rh": "P"},  # A Positive
    "A-":  {"group": "1", "rh": "N"},  # A Negative
    "B+":  {"group": "2", "rh": "P"},  # B Positive
    "B-":  {"group": "2", "rh": "N"},  # B Negative
    "AB+": {"group": "3", "rh": "P"},  # AB Positive
    "AB-": {"group": "3", "rh": "N"},  # AB Negative
    "O+":  {"group": "4", "rh": "P"},  # O Positive
    "O-":  {"group": "4", "rh": "N"},  # O Negative
}

# State code mapping for major Indian cities (used in e-RaktKosh state filter)
CITY_STATE_MAP = {
    "hyderabad": "TG", "warangal": "TG", "vijayawada": "AP",
    "mumbai": "MH", "pune": "MH", "nagpur": "MH",
    "delhi": "DL", "new delhi": "DL",
    "bangalore": "KA", "bengaluru": "KA", "mysore": "KA",
    "chennai": "TN", "coimbatore": "TN",
    "kolkata": "WB",
    "ahmedabad": "GJ", "surat": "GJ",
    "jaipur": "RJ",
    "lucknow": "UP", "kanpur": "UP", "varanasi": "UP",
    "bhopal": "MP", "indore": "MP",
    "chandigarh": "CH",
    "bhubaneswar": "OD",
    "guwahati": "AS",
    "kochi": "KL", "thiruvananthapuram": "KL",
}


async def scrape_eraktkosh(city: str, blood_type: str) -> list[dict]:
    """
    Query the e-RaktKosh national blood bank portal for blood availability.

    Returns: list of dicts — [{name, contact, address, units, source}]
    Falls back to empty list on timeout or parse error (caller should try next tier).
    """
    code = BLOOD_TYPE_CODES.get(blood_type.upper())
    if not code:
        logger.warning(f"Unknown blood type '{blood_type}' for e-RaktKosh query.")
        return []

    state = CITY_STATE_MAP.get(city.lower(), "")

    # e-RaktKosh uses a form POST with specific parameters
    payload = {
        "bloodGroup": code["group"],
        "rhFactor": code["rh"],
        "state": state,
        "district": city,
        "facility_type": "BB",   # Blood Bank
    }

    headers = {
        "User-Agent": "BloodBridge-AI/1.0 (Emergency Blood Matching System)",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": ERAKTKOSH_BASE_URL,
    }

    for attempt in range(1, ERAKTKOSH_MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=ERAKTKOSH_TIMEOUT, verify=False) as client:
                resp = await client.post(
                    ERAKTKOSH_SEARCH_URL,
                    data=payload,
                    headers=headers
                )
                resp.raise_for_status()

            data = resp.json()

            # e-RaktKosh returns {"data": [{...}, ...]} or similar structure
            results = []
            raw_list = data if isinstance(data, list) else data.get("data", data.get("results", []))

            for bank in raw_list:
                # Normalize field names from e-RaktKosh response schema
                name    = bank.get("facilityName") or bank.get("name") or bank.get("bbName", "Unknown Blood Bank")
                contact = bank.get("contactNo") or bank.get("phone") or bank.get("mobile", "N/A")
                address = bank.get("address") or bank.get("facilityAddress", "")
                units   = int(bank.get("totalUnits") or bank.get("units") or bank.get("available", 0))

                if units > 0:
                    results.append({
                        "name": name,
                        "contact": contact,
                        "address": address,
                        "units": units,
                        "city": city,
                        "source": "eraktkosh",
                        "blood_type": blood_type,
                    })

            logger.info(f"e-RaktKosh: found {len(results)} banks with {blood_type} stock in {city}")
            return results

        except httpx.TimeoutException:
            logger.warning(f"e-RaktKosh timeout (attempt {attempt}/{ERAKTKOSH_MAX_RETRIES}) for {city}/{blood_type}")
            if attempt < ERAKTKOSH_MAX_RETRIES:
                await asyncio.sleep(1.5 * attempt)
        except httpx.HTTPStatusError as e:
            logger.warning(f"e-RaktKosh HTTP {e.response.status_code} for {city}/{blood_type}")
            return []
        except (ValueError, KeyError) as e:
            logger.warning(f"e-RaktKosh response parse error: {e}")
            return []
        except Exception as e:
            logger.error(f"e-RaktKosh unexpected error: {e}", exc_info=True)
            return []

    return []


async def _query_neo4j(city: str, blood_type: str) -> list[dict]:
    """
    Tier 1: Query Neo4j graph for blood banks with live stock.
    The Neo4j BloodBank nodes are periodically updated by the sync job.
    """
    driver = get_driver()
    results = []

    # Map blood type to Neo4j property name: 'B+' → 'units_b_pos'
    type_key = blood_type.lower().replace("+", "_pos").replace("-", "_neg")
    prop_name = f"units_{type_key}"

    query = f"""
    MATCH (b:BloodBank)
    WHERE b.city = $city AND b.{prop_name} > 0
    RETURN b.name AS name, b.contact AS contact, b.{prop_name} AS units,
           b.address AS address,
           b.location.latitude AS lat, b.location.longitude AS lng
    ORDER BY b.{prop_name} DESC
    LIMIT 10
    """

    try:
        async with driver.session() as session:
            res = await session.run(query, {"city": city})
            async for record in res:
                r = dict(record)
                r["source"] = "neo4j"
                r["blood_type"] = blood_type
                results.append(r)
    except Exception as e:
        logger.error(f"Neo4j blood bank query failed: {e}", exc_info=True)

    return results


def _query_local_seed(city: str, blood_type: str) -> list[dict]:
    """
    Tier 3 (last resort): Query the local seed data file for blood bank listings.
    Returns empty list if seed data is not available.
    """
    try:
        from data.seed_neo4j import BLOOD_BANKS
        type_key = blood_type.lower().replace("+", "_pos").replace("-", "_neg")
        prop_name = f"units_{type_key}"
        results = []
        for bank in BLOOD_BANKS:
            if bank.get("city", "").lower() == city.lower():
                units = bank.get(prop_name, 0)
                if units > 0:
                    results.append({
                        "name": bank["name"],
                        "contact": bank.get("contact", "N/A"),
                        "address": bank.get("address", city),
                        "units": units,
                        "city": city,
                        "lat": bank.get("lat"),
                        "lng": bank.get("lng"),
                        "source": "local_seed",
                        "blood_type": blood_type,
                    })
        return results
    except Exception as e:
        logger.error(f"Local seed blood bank query failed: {e}")
        return []


async def get_nearest_banks_with_stock(city: str, blood_type: str) -> list[dict]:
    """
    Main public function — 3-tier fallback chain:
      Tier 1: Neo4j graph (fastest, O(1))
      Tier 2: e-RaktKosh national portal (real-time web data)
      Tier 3: Local seed data (last resort)

    Returns list of blood bank dicts with keys:
      {name, contact, address, units, city, source, blood_type}
    """
    # Tier 1: Neo4j
    results = await _query_neo4j(city, blood_type)
    if results:
        logger.info(f"Blood bank search: {len(results)} results from Neo4j for {city}/{blood_type}")
        return results

    logger.warning(f"Neo4j returned 0 blood banks for {city}/{blood_type}. Trying e-RaktKosh...")

    # Tier 2: e-RaktKosh scraper
    results = await scrape_eraktkosh(city, blood_type)
    if results:
        logger.info(f"Blood bank search: {len(results)} results from e-RaktKosh for {city}/{blood_type}")
        return results

    logger.warning(f"e-RaktKosh returned 0 results for {city}/{blood_type}. Using local seed fallback...")

    # Tier 3: Local seed
    results = _query_local_seed(city, blood_type)
    if results:
        logger.info(f"Blood bank search: {len(results)} results from local seed for {city}/{blood_type}")
    else:
        logger.error(f"All tiers exhausted — no blood banks found for {city}/{blood_type}")

    return results


async def find_emergency_supply(patient: dict) -> dict:
    """
    Orchestration function called by InventoryAgent when the entire donor chain fails.
    Searches all tiers for the patient's blood type in their city.

    Args:
        patient: dict with keys {patient_id, blood_type, city, hospital_name, urgency_level}

    Returns:
        {
            found: bool,
            banks: list[dict],   # matched blood banks
            source: str,         # 'neo4j' | 'eraktkosh' | 'local_seed' | 'none'
            message: str         # human-readable summary for Telegram alert
        }
    """
    city = patient.get("city", "")
    blood_type = patient.get("blood_type", "")
    patient_id = patient.get("patient_id", "?")
    urgency = patient.get("urgency_level", "HIGH")

    if not city or not blood_type:
        return {
            "found": False,
            "banks": [],
            "source": "none",
            "message": "Cannot search: patient city or blood type is missing."
        }

    logger.info(f"InventoryAgent: searching for {blood_type} supply in {city} for patient {patient_id}")

    banks = await get_nearest_banks_with_stock(city, blood_type)

    if not banks:
        return {
            "found": False,
            "banks": [],
            "source": "none",
            "message": (
                f"⚠️ CRITICAL: No {blood_type} blood found in any blood bank in {city}. "
                f"Manual escalation required for patient {patient_id}."
            )
        }

    # Build summary message
    top_bank = banks[0]
    source_label = {"neo4j": "BloodBridge network", "eraktkosh": "e-RaktKosh portal", "local_seed": "registry"}.get(
        top_bank["source"], "database"
    )
    message = (
        f"🏥 Blood bank found via {source_label}!\n"
        f"• {top_bank['name']}\n"
        f"• Contact: {top_bank['contact']}\n"
        f"• {blood_type} units available: {top_bank['units']}\n"
        f"• Location: {top_bank.get('address', city)}\n"
        f"({len(banks)} bank(s) total with stock)"
    )

    return {
        "found": True,
        "banks": banks,
        "source": top_bank["source"],
        "message": message
    }
