"""
Donor Eligibility Filter for BloodBridge AI.
Validates donors against WHO and National Blood Transfusion Council (NBTC) India guidelines.
"""
import logging
from datetime import date, datetime
from typing import List, Dict, Optional, Tuple
from ml.antigen_scorer import is_abo_compatible

logger = logging.getLogger(__name__)

def parse_date(date_val) -> Optional[date]:
    """Parse string or date objects safely."""
    if not date_val:
        return None
    if isinstance(date_val, date):
        return date_val
    if isinstance(date_val, str):
        try:
            return datetime.strptime(date_val.split("T")[0], "%Y-%m-%d").date()
        except ValueError:
            logger.warning(f"Could not parse date string: {date_val}")
            return None
    return None

def check_donor_eligibility(donor: Dict, patient: Dict) -> Dict:
    """
    Check if a donor is medically eligible to donate blood for a specific patient.
    Checks in sequence:
    1. Active status
    2. Medical hold flag
    3. ABO blood type compatibility
    4. 56-day donation interval gap
    5. Hemoglobin threshold (>= 12.5 g/dL)
    
    Returns:
        Dict: { 'eligible': bool, 'reason': str|None, 'days_until_eligible': int|None }
    """
    # 1. Active check
    if not donor.get("is_active", True):
        return {
            "eligible": False,
            "reason": "Donor profile is inactive",
            "days_until_eligible": None
        }

    # 2. Medical hold check
    if donor.get("medical_hold", False):
        return {
            "eligible": False,
            "reason": "Donor is on medical hold",
            "days_until_eligible": None
        }

    # 3. Blood type compatibility check
    donor_blood = donor.get("blood_type")
    patient_blood = patient.get("blood_type")
    if not is_abo_compatible(donor_blood, patient_blood):
        return {
            "eligible": False,
            "reason": f"Blood type {donor_blood} is incompatible with patient's {patient_blood}",
            "days_until_eligible": None
        }

    # 4. 56-day donation interval gap check
    last_date = parse_date(donor.get("last_donation_date"))
    if last_date:
        today = date.today()
        days_since = (today - last_date).days
        if days_since < 56:
            days_until = 56 - days_since
            return {
                "eligible": False,
                "reason": f"Minimum 56-day donation interval not met (only {days_since} days since last donation)",
                "days_until_eligible": days_until
            }

    # 5. Hemoglobin threshold check
    hgb = donor.get("hemoglobin")
    if hgb is not None and hgb < 12.5:
        return {
            "eligible": False,
            "reason": f"Hemoglobin level {hgb} g/dL is below the 12.5 g/dL threshold",
            "days_until_eligible": None
        }

    # 6. All checks pass
    return {
        "eligible": True,
        "reason": None,
        "days_until_eligible": 0
    }

def filter_eligible_donors(donors: List[Dict], patient: Dict) -> List[Dict]:
    """
    Filter the list of donors for medical eligibility and sort them.
    Sorting: Donors with the longest gap since their last donation are placed first.
    Never-donated donors (last_donation_date is None) are placed at the absolute top.
    """
    eligible_donors = []
    patient_id = patient.get("patient_id", "Unknown")
    
    for donor in donors:
        res = check_donor_eligibility(donor, patient)
        if res["eligible"]:
            # Inject eligibility details
            d_copy = donor.copy()
            d_copy["eligibility_reason"] = res["reason"]
            d_copy["days_until_eligible"] = res["days_until_eligible"]
            eligible_donors.append(d_copy)

    # Sort: Longest gap first. 
    # Use helper key: never donated -> infinite days ago (represented by huge integer)
    def get_sort_key(d):
        last_date = parse_date(d.get("last_donation_date"))
        if last_date is None:
            return 999999
        return (date.today() - last_date).days

    eligible_donors.sort(key=get_sort_key, reverse=True)
    
    logger.info(f"Eligibility filter: {len(eligible_donors)}/{len(donors)} eligible for {patient_id}")
    return eligible_donors

def get_eligibility_summary(donors: List[Dict], patient: Dict) -> Dict:
    """Returns counts of rejections by reason for admin/trace logging."""
    summary = {
        "eligible": 0,
        "inactive": 0,
        "medical_hold": 0,
        "abo_incompatible": 0,
        "interval_gap": 0,
        "low_hemoglobin": 0
    }
    
    for d in donors:
        res = check_donor_eligibility(d, patient)
        if res["eligible"]:
            summary["eligible"] += 1
        else:
            reason = res["reason"]
            if "inactive" in reason:
                summary["inactive"] += 1
            elif "medical hold" in reason:
                summary["medical_hold"] += 1
            elif "incompatible" in reason:
                summary["abo_incompatible"] += 1
            elif "interval" in reason:
                summary["interval_gap"] += 1
            elif "hemoglobin" in reason:
                summary["low_hemoglobin"] += 1
                
    return summary
