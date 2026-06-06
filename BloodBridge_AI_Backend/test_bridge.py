from services.matching_engine import rank_donors

# Test with a patient that has bridges (P-10041 confirmed to have bridge members)
r = rank_donors('P-10041')
print(f'Patient P-10041:')
print(f'Primary: {len(r["primary"])} donors\n')

print("Top 5 donors:")
for d in r['primary'][:5]:
    bridge_status = "✅ BRIDGE" if d.get("bridge_bonus", 0) > 0 else "  regular"
    print(f'{bridge_status} {d["donor_id"]} bridge={d.get("bridge_bonus", 0):.1f} antigen={d["antigen_score"]:.2f} score={d["match_score"]:.2f}')

