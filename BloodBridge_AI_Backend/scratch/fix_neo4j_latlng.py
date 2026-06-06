"""
One-time migration: Extract lat/lng from POINT properties and store as scalar properties.
Also syncs phone from Supabase donors into Neo4j Donor nodes.
"""
import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from core.config import get_settings
from core.database import get_supabase_admin
from core.neo4j_client import get_driver

async def migrate():
    print("=" * 60)
    print("NEO4J MIGRATION: Add lat/lng/phone scalar properties")
    print("=" * 60)

    driver = get_driver()
    supabase = get_supabase_admin()

    # Step 1: Extract lat/lng from POINT on Donor nodes
    print("\n[1/4] Extracting lat/lng from Donor.location POINT...")
    async with driver.session() as session:
        result = await session.run("""
            MATCH (d:Donor)
            WHERE d.location IS NOT NULL
            SET d.lat = d.location.latitude,
                d.lng = d.location.longitude
            RETURN count(d) AS updated
        """)
        rec = await result.single()
        print(f"       Updated {rec['updated']} Donor nodes with lat/lng")

    # Step 2: Extract lat/lng from POINT on Patient nodes
    print("[2/4] Extracting lat/lng from Patient.location POINT...")
    async with driver.session() as session:
        result = await session.run("""
            MATCH (p:Patient)
            WHERE p.location IS NOT NULL
            SET p.lat = p.location.latitude,
                p.lng = p.location.longitude
            RETURN count(p) AS updated
        """)
        rec = await result.single()
        print(f"       Updated {rec['updated']} Patient nodes with lat/lng")

    # Step 3: Sync phone numbers from Supabase to Neo4j
    print("[3/4] Syncing phone numbers from Supabase to Neo4j Donor nodes...")
    donors_res = supabase.table("donors").select("donor_id, phone").execute()
    donors = donors_res.data or []
    phone_count = 0
    async with driver.session() as session:
        for d in donors:
            if d.get("phone"):
                await session.run(
                    "MATCH (d:Donor {donor_id: $donor_id}) SET d.phone = $phone",
                    {"donor_id": d["donor_id"], "phone": d["phone"]}
                )
                phone_count += 1
    print(f"       Synced phone for {phone_count} Donor nodes")

    # Step 4: Verify
    print("[4/4] Verifying migration...")
    async with driver.session() as session:
        r = await session.run("""
            MATCH (d:Donor)
            WHERE d.lat IS NOT NULL AND d.lng IS NOT NULL
            RETURN count(d) AS donors_with_latlng
        """)
        rec = await r.single()
        print(f"       Donors with lat/lng: {rec['donors_with_latlng']}")

        r2 = await session.run("""
            MATCH (p:Patient)
            WHERE p.lat IS NOT NULL AND p.lng IS NOT NULL
            RETURN count(p) AS patients_with_latlng
        """)
        rec2 = await r2.single()
        print(f"       Patients with lat/lng: {rec2['patients_with_latlng']}")

        r3 = await session.run("""
            MATCH (d:Donor)
            WHERE d.phone IS NOT NULL
            RETURN count(d) AS donors_with_phone
        """)
        rec3 = await r3.single()
        print(f"       Donors with phone: {rec3['donors_with_phone']}")

        # Quick match test
        r4 = await session.run("""
            MATCH (p:Patient)
            WITH p LIMIT 1
            MATCH (d:Donor)-[c:COMPATIBLE_WITH]->(p)
            WHERE d.lat IS NOT NULL AND p.lat IS NOT NULL
            WITH d, c, p,
                 point.distance(
                     point({latitude: d.lat, longitude: d.lng}),
                     point({latitude: p.lat, longitude: p.lng})
                 ) AS distance_m
            RETURN d.donor_id AS donor_id, d.name AS name, d.blood_type AS blood_type,
                   c.antigen_score AS score, distance_m / 1000.0 AS distance_km
            ORDER BY c.antigen_score DESC, distance_m ASC
            LIMIT 3
        """)
        print("\n       Sample match test (first patient, top 3 donors):")
        count = 0
        async for rec in r4:
            print(f"         {rec['donor_id']} | {rec['name']} | {rec['blood_type']} | score={rec['score']:.2f} | {rec['distance_km']:.1f}km")
            count += 1
        if count == 0:
            print("         (no matches found - check COMPATIBLE_WITH edges)")
        else:
            print(f"\n       [SUCCESS] Distance-based matching is now working!")

    await driver.close()
    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(migrate())
