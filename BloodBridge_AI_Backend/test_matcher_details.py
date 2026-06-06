from services.matching_engine import rank_donors

# Test matching for patient P-10000 with detailed breakdown
r = rank_donors('P-10000')
print(f'✅ Matcher returned {len(r["primary"])} primary donors\n')

print("Detailed scoring breakdown for top 3:\n")
for i, d in enumerate(r['primary'][:3], 1):
    print(f"#{i} {d['donor_id']} ({d['blood_type']})")
    print(f"   Distance: {d['distance_km']:.1f}km")
    print(f"   Antigen safety: {d['antigen_score']:.2f}")
    print(f"   Churn risk: {d.get('churn_score', 0):.2f}")
    print(f"   Bridge bonus: {d.get('bridge_bonus', 0):.2f}")
    print(f"   Engagement: {d.get('engagement_score', 0):.2f}")
    print(f"   FINAL MATCH SCORE: {d['match_score']:.2f}\n")
