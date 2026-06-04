"""
8-Antigen ISBT Blood Compatibility Scorer for BloodBridge AI.
Scores donor compatibility against patient antibody profiles.
"""

ABO_COMPATIBILITY = {
    'O-': ['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+'],
    'O+': ['O+', 'A+', 'B+', 'AB+'],
    'A-': ['A-', 'A+', 'AB-', 'AB+'],
    'A+': ['A+', 'AB+'],
    'B-': ['B-', 'B+', 'AB-', 'AB+'],
    'B+': ['B+', 'AB+'],
    'AB-': ['AB-', 'AB+'],
    'AB+': ['AB+']
}

ANTIGEN_PENALTIES = {
    'kell': 0.35,   # Kell mismatch
    'duffy': 0.25,  # Duffy mismatch
    'kidd': 0.20,   # Kidd mismatch
    'rh_e': 0.10,   # Rh-E mismatch
    'rh_c': 0.05,   # Rh-C mismatch
    'mns': 0.03,    # MNS mismatch
    'abo': 0.02     # Non-identical ABO type mismatch
}

def is_abo_compatible(donor_blood: str, patient_blood: str) -> bool:
    """Check if donor's blood type is ABO compatible with the patient."""
    compat = ABO_COMPATIBILITY.get(donor_blood, [])
    return patient_blood in compat

def compute_antigen_score(donor: dict, patient: dict) -> float:
    """
    Compute compatibility score from 0.0 to 1.0.
    1.0 represents a perfect identical antigen match.
    0.0 represents a dangerous mismatch.
    """
    donor_blood = donor.get("blood_type")
    patient_blood = patient.get("blood_type")
    
    # 1. Base ABO check
    if not is_abo_compatible(donor_blood, patient_blood):
        return 0.0
        
    score = 1.0
    
    # 2. Kell antigen check
    if (patient.get("kell_negative") or patient.get("antibody_kell")) and not donor.get("kell_negative"):
        score -= ANTIGEN_PENALTIES['kell']
        
    # 3. Duffy antigen check
    if (patient.get("needs_duffy_negative") or patient.get("antibody_duffy")) and not donor.get("duffy_negative"):
        score -= ANTIGEN_PENALTIES['duffy']
        
    # 4. Kidd antigen check
    if (patient.get("needs_kidd_negative") or patient.get("antibody_kidd")) and not donor.get("kidd_negative"):
        score -= ANTIGEN_PENALTIES['kidd']
        
    # 5. Rh-E antigen check
    if (patient.get("antibody_rh_e") or "anti-E" in str(patient.get("antibody_flags", []))) and not donor.get("rh_e_negative"):
        score -= ANTIGEN_PENALTIES['rh_e']
        
    # 6. Rh-C antigen check
    if (patient.get("antibody_rh_c") or "anti-C" in str(patient.get("antibody_flags", []))) and not donor.get("rh_c_negative"):
        score -= ANTIGEN_PENALTIES['rh_c']
        
    # 7. MNS antigen check
    if (patient.get("antibody_mns") or "anti-M" in str(patient.get("antibody_flags", []))) and not donor.get("mns_negative"):
        score -= ANTIGEN_PENALTIES['mns']
        
    # 8. Residual ABO penalty (identical match preference)
    if donor_blood != patient_blood:
        score -= ANTIGEN_PENALTIES['abo']
        
    return max(0.0, round(score, 2))

def get_eligibility_flags(donor: dict) -> dict:
    """Return which antigens this donor can safely provide (True = Antigen-negative/safe)."""
    return {
        'kell_safe': donor.get('kell_negative', False),
        'duffy_safe': donor.get('duffy_negative', False),
        'kidd_safe': donor.get('kidd_negative', False),
        'rh_e_safe': donor.get('rh_e_negative', False),
        'rh_c_safe': donor.get('rh_c_negative', False),
        'mns_safe': donor.get('mns_negative', False)
    }

def explain_score(donor: dict, patient: dict, score: float) -> str:
    """Generate a human-readable explanation of the score for dashboard traces."""
    if score == 0.0:
        return f"Dangerous mismatch: ABO incompatible ({donor.get('blood_type')} for {patient.get('blood_type')})"
        
    explanations = []
    
    # Check mismatches
    if (patient.get("kell_negative") or patient.get("antibody_kell")) and not donor.get("kell_negative"):
        explanations.append(f"Kell mismatch (-{ANTIGEN_PENALTIES['kell']})")
    if (patient.get("needs_duffy_negative") or patient.get("antibody_duffy")) and not donor.get("duffy_negative"):
        explanations.append(f"Duffy mismatch (-{ANTIGEN_PENALTIES['duffy']})")
    if (patient.get("needs_kidd_negative") or patient.get("antibody_kidd")) and not donor.get("kidd_negative"):
        explanations.append(f"Kidd mismatch (-{ANTIGEN_PENALTIES['kidd']})")
    if (patient.get("antibody_rh_e") or "anti-E" in str(patient.get("antibody_flags", []))) and not donor.get("rh_e_negative"):
        explanations.append(f"Rh-E mismatch (-{ANTIGEN_PENALTIES['rh_e']})")
    if (patient.get("antibody_rh_c") or "anti-C" in str(patient.get("antibody_flags", []))) and not donor.get("rh_c_negative"):
        explanations.append(f"Rh-C mismatch (-{ANTIGEN_PENALTIES['rh_c']})")
    if (patient.get("antibody_mns") or "anti-M" in str(patient.get("antibody_flags", []))) and not donor.get("mns_negative"):
        explanations.append(f"MNS mismatch (-{ANTIGEN_PENALTIES['mns']})")
    if donor.get("blood_type") != patient.get("blood_type"):
        explanations.append(f"Non-identical ABO type mismatch (-{ANTIGEN_PENALTIES['abo']})")
        
    if not explanations:
        return f"Perfect identical match ({score*100}%)"
        
    return f"Score {score}: " + ", ".join(explanations)

if __name__ == "__main__":
    # Test cases validation
    print("Running Antigen Scorer Test Cases:")
    
    # Test case 1: Perfect match
    p1 = {"blood_type": "B+", "kell_negative": False}
    d1 = {"blood_type": "B+", "kell_negative": False}
    s1 = compute_antigen_score(d1, p1)
    print(f"Case 1 (B+ to B+): {explain_score(d1, p1, s1)}")
    
    # Test case 2: ABO incompatible
    p2 = {"blood_type": "B+", "kell_negative": False}
    d2 = {"blood_type": "A+", "kell_negative": False}
    s2 = compute_antigen_score(d2, p2)
    print(f"Case 2 (A+ to B+): {explain_score(d2, p2, s2)}")
    
    # Test case 3: Kell mismatch
    p3 = {"blood_type": "O+", "antibody_kell": True, "kell_negative": True}
    d3 = {"blood_type": "O+", "kell_negative": False} # donor is Kell-pos
    s3 = compute_antigen_score(d3, p3)
    print(f"Case 3 (O+ Kell-pos donor for Kell-neg patient): {explain_score(d3, p3, s3)}")
    
    # Test case 4: Compatible non-identical ABO + minor mismatch
    p4 = {"blood_type": "AB+", "antibody_duffy": True}
    d4 = {"blood_type": "B+", "duffy_negative": False}
    s4 = compute_antigen_score(d4, p4)
    print(f"Case 4 (B+ Duffy-pos donor for AB+ Duffy-neg patient): {explain_score(d4, p4, s4)}")
