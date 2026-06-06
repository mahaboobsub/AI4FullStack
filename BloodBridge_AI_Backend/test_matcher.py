from services.matching_engine import rank_donors

# Test matching for patient P-10000
r = rank_donors('P-10000')
print(f'primary: {len(r["primary"])}')
print(f'wide_net: {len(r["wide_net"])}\n')

print("Top 5 donors:")
for d in r['primary'][:5]:
    print(f'{d["donor_id"]} {d["blood_type"]} {d["distance_km"]:.1f}km antigen={d["antigen_score"]:.2f} score={d["match_score"]:.2f}')
