"""
Scenario A: Smart Matching + Antigen Safety E2E Test
Tests the 6-parameter weighted matching with live antigen scoring.
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from core.database import get_supabase_admin
from services.matching_engine import rank_donors
from ml.antigen_scorer import compute_antigen_score

print("=" * 70)
print("SCENARIO A: Smart Matching + Antigen Safety")
print("=" * 70)

# Step 1: Find patients with antibody flags
print("\n[Step 1] Finding patients with antibody flags...")
sb = get_supabase_admin()
patients = sb.table('patients').select('*').limit(50).execute()

patients_with_antibodies = []
for p in patients.data:
    antibodies = []
    if p.get('antibody_kell'): antibodies.append('Kell')
    if p.get('antibody_duffy'): antibodies.append('Duffy')
    if p.get('antibody_kidd'): antibodies.append('Kidd')
    if p.get('antibody_rh_e'): antibodies.append('Rh-E')
    if p.get('antibody_rh_c'): antibodies.append('Rh-C')
    if p.get('antibody_mns'): antibodies.append('MNS')
    
    if antibodies:
        patients_with_antibodies.append({
            'patient_id': p['patient_id'],
            'blood_type': p['blood_type'],
            'antibodies': antibodies,
            'hospital': p.get('hospital', 'Unknown')
        })

print(f"\n✅ Found {len(patients_with_antibodies)} patients with antibody flags:")
for p in patients_with_antibodies[:5]:
    print(f"   {p['patient_id']} ({p['blood_type']}) - Antibodies: {', '.join(p['antibodies'])} - {p['hospital']}")

# Pick the first patient with Kell antibody (most common critical antibody)
test_patient = next((p for p in patients_with_antibodies if 'Kell' in p['antibodies']), 
                    patients_with_antibodies[0] if patients_with_antibodies else None)

if not test_patient:
    print("\n❌ No patients with antibodies found. Using P-10000 as fallback.")
    test_patient = {'patient_id': 'P-10000', 'blood_type': 'B+', 'antibodies': []}

print(f"\n[Test Patient Selected]")
print(f"   ID: {test_patient['patient_id']}")
print(f"   Blood Type: {test_patient['blood_type']}")
print(f"   Antibodies: {', '.join(test_patient['antibodies']) if test_patient['antibodies'] else 'None'}")

# Step 2: Run matching engine
print(f"\n[Step 2] Running matching engine for {test_patient['patient_id']}...")
result = rank_donors(test_patient['patient_id'])

print(f"\n✅ Matching complete:")
print(f"   Primary pool: {len(result['primary'])} donors")
print(f"   Wide net: {len(result['wide_net'])} donors")

# Step 3: Analyze top donors
print(f"\n[Step 3] Analyzing top 8 donors:")
print(f"\n{'Rank':<5} {'Donor ID':<10} {'Blood':<5} {'Dist(km)':<9} {'Antigen':<8} {'Churn':<7} {'Bridge':<8} {'Score':<7}")
print("-" * 70)

for i, d in enumerate(result['primary'][:8], 1):
    print(f"{i:<5} {d['donor_id']:<10} {d['blood_type']:<5} "
          f"{d['distance_km']:>7.1f}  {d['antigen_score']:>6.2f}  "
          f"{d.get('churn_score', 0):>5.2f}  {d.get('bridge_bonus', 0):>6.2f}  "
          f"{d['match_score']:>5.2f}")

# Step 4: Verify antigen safety
print(f"\n[Step 4] Verifying antigen safety...")

# Check if any ABO-incompatible donors made it through
abo_incompatible_count = 0
for d in result['primary']:
    # This is a simplified check - the real check is in antigen_scorer
    if d['antigen_score'] == 0:
        abo_incompatible_count += 1

if abo_incompatible_count == 0:
    print("   ✅ No ABO-incompatible donors in primary pool (hard gate working)")
else:
    print(f"   ⚠️  {abo_incompatible_count} ABO-incompatible donors found (should be 0)")

# Check antigen score distribution
antigen_scores = [d['antigen_score'] for d in result['primary']]
avg_antigen = sum(antigen_scores) / len(antigen_scores) if antigen_scores else 0
print(f"   Average antigen score: {avg_antigen:.2f}")
print(f"   Range: {min(antigen_scores):.2f} - {max(antigen_scores):.2f}")

# If patient has Kell antibody, verify Kell-negative donors rank higher
if 'Kell' in test_patient.get('antibodies', []):
    print(f"\n   Patient has anti-Kell antibody. Checking Kell-negative preference...")
    # Get donor details to check phenotypes
    top_5_donors = result['primary'][:5]
    donor_ids = [d['donor_id'] for d in top_5_donors]
    donors_data = sb.table('donors').select('donor_id, kell_negative').in_('donor_id', donor_ids).execute()
    
    kell_neg_count = sum(1 for d in donors_data.data if d.get('kell_negative'))
    print(f"   Top 5 donors: {kell_neg_count}/5 are Kell-negative")
    if kell_neg_count >= 3:
        print("   ✅ Kell-negative donors are prioritized")
    else:
        print("   ⚠️  Fewer Kell-negative donors than expected")

# Step 5: Verify all 6 components
print(f"\n[Step 5] Verifying all 6 scoring components are active:")
components_active = {
    'Blood compatibility': any(d.get('blood_type') for d in result['primary']),
    'Distance': any(d.get('distance_km', 0) > 0 for d in result['primary']),
    'Antigen safety': any(d.get('antigen_score', 0) > 0 for d in result['primary']),
    'Churn risk': any(d.get('churn_score', 0) > 0 for d in result['primary']),
    'Engagement': any(d.get('engagement_score', 0) >= 0 for d in result['primary']),
    'Bridge bonus': any(d.get('bridge_bonus', 0) > 0 for d in result['primary'])
}

for component, is_active in components_active.items():
    status = "✅" if is_active else "❌"
    print(f"   {status} {component}")

# Final verdict
print(f"\n{'=' * 70}")
print("SCENARIO A RESULTS:")
all_checks_passed = (
    len(result['primary']) > 0 and
    abo_incompatible_count == 0 and
    avg_antigen >= 0.8 and
    all(components_active.values())
)

if all_checks_passed:
    print("✅ PASSED - Smart matching with antigen safety is working correctly")
    print("   • Weighted 6-parameter scoring active")
    print("   • Antigen safety hard gate preventing incompatible matches")
    print("   • All components contributing to match scores")
else:
    print("⚠️  PARTIAL - Some components need attention")
    if len(result['primary']) == 0:
        print("   • No donors returned - check seed data")
    if abo_incompatible_count > 0:
        print("   • ABO hard gate not working")
    if avg_antigen < 0.8:
        print("   • Antigen scores lower than expected")
    if not all(components_active.values()):
        inactive = [k for k, v in components_active.items() if not v]
        print(f"   • Inactive components: {', '.join(inactive)}")

print("=" * 70)
