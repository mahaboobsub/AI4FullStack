"""
Assignment Optimizer for BloodBridge AI (M3).
Uses the Hungarian algorithm (scipy) to compute globally optimal donor-to-patient
assignments when multiple active patients/bridges compete for the same nearby donors.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def _build_cost_matrix(patient_candidates: Dict[str, List[Dict[str, Any]]]) -> tuple:
    """
    Build a cost matrix for the Hungarian algorithm.
    patient_candidates: {patient_id: [donor_dicts with match_score]}
    Returns: (cost_matrix, patient_ids_ordered, donor_ids_ordered)
    """
    patient_ids = list(patient_candidates.keys())
    all_donor_ids = set()
    for donors in patient_candidates.values():
        for d in donors:
            all_donor_ids.add(d["donor_id"])
    donor_ids = sorted(all_donor_ids)

    PROHIBITIVE_COST = 1000.0
    n_patients = len(patient_ids)
    n_donors = len(donor_ids)

    # cost[i][j] = cost of assigning donor j to patient i
    cost_matrix = [[PROHIBITIVE_COST] * n_donors for _ in range(n_patients)]

    donor_idx_map = {did: idx for idx, did in enumerate(donor_ids)}

    for p_idx, pid in enumerate(patient_ids):
        for donor in patient_candidates[pid]:
            d_idx = donor_idx_map[donor["donor_id"]]
            score = float(donor.get("match_score", 0.5))
            cost_matrix[p_idx][d_idx] = 1.0 - score  # Lower cost = better match

    return cost_matrix, patient_ids, donor_ids


def optimize_assignments(
    patient_candidates: Dict[str, List[Dict[str, Any]]],
    donors_per_patient: int = 8
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Globally optimal assignment of donors to patients using the Hungarian algorithm.
    Runs in rounds: assign 1 best donor per patient per round, remove assigned,
    repeat until chains are filled or candidates exhausted.

    Args:
        patient_candidates: {patient_id: [ranked donor dicts from matching_engine]}
        donors_per_patient: target chain size per patient

    Returns:
        {patient_id: [assigned donor dicts in priority order]}
    """
    try:
        from scipy.optimize import linear_sum_assignment
    except ImportError:
        logger.warning("scipy not available; falling back to greedy assignment.")
        return _greedy_fallback(patient_candidates, donors_per_patient)

    if len(patient_candidates) <= 1:
        # Single patient — no optimization needed, use greedy
        return _greedy_fallback(patient_candidates, donors_per_patient)

    assignments: Dict[str, List[Dict[str, Any]]] = {pid: [] for pid in patient_candidates}
    assigned_donor_ids: set = set()

    # Build lookup: donor_id -> donor dict per patient
    donor_lookup: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for pid, donors in patient_candidates.items():
        donor_lookup[pid] = {d["donor_id"]: d for d in donors}

    for round_num in range(donors_per_patient):
        # Build remaining candidates (exclude already assigned)
        remaining = {}
        for pid in patient_candidates:
            if len(assignments[pid]) >= donors_per_patient:
                continue
            remaining_donors = [
                d for d in patient_candidates[pid]
                if d["donor_id"] not in assigned_donor_ids
            ]
            if remaining_donors:
                remaining[pid] = remaining_donors

        if not remaining:
            break

        cost_matrix, p_ids, d_ids = _build_cost_matrix(remaining)

        # Solve
        try:
            row_ind, col_ind = linear_sum_assignment(cost_matrix)
        except ValueError:
            logger.warning(f"Round {round_num}: linear_sum_assignment failed; stopping.")
            break

        PROHIBITIVE_COST = 1000.0
        for r, c in zip(row_ind, col_ind):
            if cost_matrix[r][c] >= PROHIBITIVE_COST:
                continue  # No valid assignment
            pid = p_ids[r]
            did = d_ids[c]
            if did in donor_lookup.get(pid, {}):
                assignments[pid].append(donor_lookup[pid][did])
                assigned_donor_ids.add(did)

    logger.info(f"Hungarian optimizer: assigned donors to {len(assignments)} patients "
                f"across {min(round_num + 1, donors_per_patient)} rounds.")
    return assignments


def _greedy_fallback(
    patient_candidates: Dict[str, List[Dict[str, Any]]],
    donors_per_patient: int = 8
) -> Dict[str, List[Dict[str, Any]]]:
    """Simple greedy: each patient gets their top N donors (may overlap)."""
    result = {}
    for pid, donors in patient_candidates.items():
        sorted_donors = sorted(donors, key=lambda d: d.get("match_score", 0), reverse=True)
        result[pid] = sorted_donors[:donors_per_patient]
    return result
