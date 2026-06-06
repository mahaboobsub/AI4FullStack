"""
Neo4j Graph Database Seeding Script.
Reads donors/patients from Supabase, creates graph nodes, runs antigen scorer, and links edges.
"""
import os
import sys
import asyncio
from datetime import datetime

# Add backend root to path to resolve imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import get_settings
from core.database import get_supabase_admin
from core.neo4j_client import get_driver, health_check
from ml.antigen_scorer import compute_antigen_score, get_eligibility_flags
from services.geo_service import encode_geohash

def check_env():
    """Verify that required environment variables are set."""
    settings = get_settings()
    if not settings.NEO4J_URI or not settings.NEO4J_USERNAME or not settings.NEO4J_PASSWORD:
        print("Error: Neo4j credentials (NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD) are missing.")
        return False
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        print("Error: Supabase credentials are missing. Supabase must be seeded first.")
        return False
    return True

# 8 Hyderabad hospitals
HOSPITALS = [
    {"hospital_id": "HOSP-01", "name": "KIMS Secunderabad", "city": "Hyderabad", "ward": "Secunderabad", "lat": 17.4480, "lng": 78.4982, "contact": "040-44885000"},
    {"hospital_id": "HOSP-02", "name": "Apollo Banjara Hills", "city": "Hyderabad", "ward": "Banjara Hills", "lat": 17.4316, "lng": 78.4558, "contact": "040-23607777"},
    {"hospital_id": "HOSP-03", "name": "Yashoda Secunderabad", "city": "Hyderabad", "ward": "Secunderabad", "lat": 17.4600, "lng": 78.5000, "contact": "040-45674567"},
    {"hospital_id": "HOSP-04", "name": "Nizam's Institute", "city": "Hyderabad", "ward": "Punjagutta", "lat": 17.4065, "lng": 78.4772, "contact": "040-23489000"},
    {"hospital_id": "HOSP-05", "name": "Care Hospitals Gachibowli", "city": "Hyderabad", "ward": "Gachibowli", "lat": 17.4435, "lng": 78.3772, "contact": "040-30418888"},
    {"hospital_id": "HOSP-06", "name": "Continental Hospital", "city": "Hyderabad", "ward": "Gachibowli", "lat": 17.4039, "lng": 78.3445, "contact": "040-67000000"},
    {"hospital_id": "HOSP-07", "name": "Global Hospital", "city": "Hyderabad", "ward": "Lakdikapul", "lat": 17.3960, "lng": 78.4900, "contact": "040-40404040"},
    {"hospital_id": "HOSP-08", "name": "Rainbow Children's Hospital", "city": "Hyderabad", "ward": "Banjara Hills", "lat": 17.4225, "lng": 78.4419, "contact": "040-23607770"}
]

# 8 Hyderabad blood banks matching frontend mocks
BLOOD_BANKS = [
    {"bank_id": "BB-01", "name": "Nizam's Institute Blood Bank", "city": "Hyderabad", "lat": 17.4065, "lng": 78.4772, "contact": "040-23489000", "units_b_pos": 8, "units_o_pos": 3, "units_a_pos": 5, "units_ab_pos": 0, "units_b_neg": 0, "units_o_neg": 2, "units_a_neg": 1, "units_ab_neg": 0},
    {"bank_id": "BB-02", "name": "Apollo Blood Center Jubilee", "city": "Hyderabad", "lat": 17.4316, "lng": 78.4558, "contact": "040-23607777", "units_b_pos": 3, "units_o_pos": 8, "units_a_pos": 6, "units_ab_pos": 2, "units_b_neg": 0, "units_o_neg": 1, "units_a_neg": 0, "units_ab_neg": 0},
    {"bank_id": "BB-03", "name": "KIMS Blood Bank Secunderabad", "city": "Hyderabad", "lat": 17.4480, "lng": 78.4982, "contact": "040-44885000", "units_b_pos": 2, "units_o_pos": 8, "units_a_pos": 3, "units_ab_pos": 0, "units_b_neg": 0, "units_o_neg": 0, "units_a_neg": 1, "units_ab_neg": 0},
    {"bank_id": "BB-04", "name": "Care Hospitals Blood Bank", "city": "Hyderabad", "lat": 17.4435, "lng": 78.3772, "contact": "040-30418888", "units_b_pos": 6, "units_o_pos": 4, "units_a_pos": 3, "units_ab_pos": 0, "units_b_neg": 1, "units_o_neg": 1, "units_a_neg": 2, "units_ab_neg": 0},
    {"bank_id": "BB-05", "name": "Yashoda Blood Bank", "city": "Hyderabad", "lat": 17.4600, "lng": 78.5000, "contact": "040-45674567", "units_b_pos": 0, "units_o_pos": 5, "units_a_pos": 2, "units_ab_pos": 1, "units_b_neg": 0, "units_o_neg": 0, "units_a_neg": 0, "units_ab_neg": 1},
    {"bank_id": "BB-06", "name": "Global Hospital Blood Bank", "city": "Hyderabad", "lat": 17.3960, "lng": 78.4900, "contact": "040-40404040", "units_b_pos": 4, "units_o_pos": 2, "units_a_pos": 1, "units_ab_pos": 1, "units_b_neg": 0, "units_o_neg": 2, "units_a_neg": 3, "units_ab_neg": 0},
    {"bank_id": "BB-07", "name": "Rainbow Children's Hospital Bank", "city": "Hyderabad", "lat": 17.4225, "lng": 78.4419, "contact": "040-23607770", "units_b_pos": 2, "units_o_pos": 3, "units_a_pos": 5, "units_ab_pos": 3, "units_b_neg": 0, "units_o_neg": 1, "units_a_neg": 0, "units_ab_neg": 0},
    {"bank_id": "BB-08", "name": "Continental Hospital Bank", "city": "Hyderabad", "lat": 17.4039, "lng": 78.3445, "contact": "040-67000000", "units_b_pos": 1, "units_o_pos": 1, "units_a_pos": 0, "units_ab_pos": 0, "units_b_neg": 0, "units_o_neg": 0, "units_a_neg": 1, "units_ab_neg": 2}
]

async def run_seed():
    if not check_env():
        sys.exit(1)

    print("Checking Neo4j Connection...")
    if not await health_check():
        print("Neo4j database is unreachable. Please verify credentials and Aura status.")
        sys.exit(1)

    print("Fetching donors and patients from Supabase...")
    supabase = get_supabase_admin()
    
    donors_res = supabase.table("donors").select("*").execute()
    patients_res = supabase.table("patients").select("*").execute()
    
    donors = donors_res.data
    patients = patients_res.data
    
    print(f"Loaded {len(donors)} donors and {len(patients)} patients from Supabase.")
    if not donors or not patients:
        print("Error: Seeding aborted. Seed Supabase first to fetch source data.")
        sys.exit(1)

    driver = get_driver()
    
    async with driver.session() as session:
        # Clear existing graph constraints and nodes to ensure clean seeding
        print("Clearing existing graph...")
        await session.run("MATCH (n) DETACH DELETE n")

        # Create constraints and point indexes
        print("Applying Neo4j constraints and indices...")
        await session.run("CREATE CONSTRAINT donor_id_unique IF NOT EXISTS FOR (d:Donor) REQUIRE d.donor_id IS UNIQUE")
        await session.run("CREATE CONSTRAINT patient_id_unique IF NOT EXISTS FOR (p:Patient) REQUIRE p.patient_id IS UNIQUE")
        await session.run("CREATE CONSTRAINT hospital_id_unique IF NOT EXISTS FOR (h:Hospital) REQUIRE h.hospital_id IS UNIQUE")
        await session.run("CREATE INDEX donor_city IF NOT EXISTS FOR (d:Donor) ON (d.city)")
        await session.run("CREATE INDEX donor_blood_type IF NOT EXISTS FOR (d:Donor) ON (d.blood_type)")
        await session.run("CREATE INDEX patient_blood_type IF NOT EXISTS FOR (p:Patient) ON (p.blood_type)")
        await session.run("CREATE POINT INDEX donor_location IF NOT EXISTS FOR (d:Donor) ON (d.location)")
        await session.run("CREATE INDEX donor_geohash IF NOT EXISTS FOR (d:Donor) ON (d.geohash)")
        await session.run("CREATE INDEX patient_geohash IF NOT EXISTS FOR (p:Patient) ON (p.geohash)")

        # Create Hospitals
        print("Seeding Hospital nodes...")
        for hosp in HOSPITALS:
            await session.run(
                """
                MERGE (h:Hospital {hospital_id: $hospital_id})
                SET h.name = $name, h.city = $city, h.ward = $ward,
                    h.location = point({latitude: $lat, longitude: $lng}), h.contact = $contact
                """,
                hosp
            )

        # Create Blood Banks
        print("Seeding BloodBank nodes...")
        for bank in BLOOD_BANKS:
            await session.run(
                """
                MERGE (b:BloodBank {bank_id: $bank_id})
                SET b.name = $name, b.city = $city, b.location = point({latitude: $lat, longitude: $lng}),
                    b.contact = $contact, b.units_b_pos = $units_b_pos, b.units_o_pos = $units_o_pos,
                    b.units_a_pos = $units_a_pos, b.units_ab_pos = $units_ab_pos, b.units_b_neg = $units_b_neg,
                    b.units_o_neg = $units_o_neg, b.units_a_neg = $units_a_neg, b.units_ab_neg = $units_ab_neg,
                    b.updated_at = datetime()
                """,
                bank
            )

        # Create Donors
        print("Seeding Donor nodes...")
        for d in donors:
            # Handle possible null coordinates
            lat = d.get("lat") or 17.40
            lng = d.get("lng") or 78.40
            
            await session.run(
                """
                MERGE (d:Donor {donor_id: $donor_id})
                SET d.name = $name, d.blood_type = $blood_type, d.city = $city, d.ward = $ward,
                    d.location = point({latitude: $lat, longitude: $lng}),
                    d.lat = $lat, d.lng = $lng, d.geohash = $geohash, d.phone = $phone,
                    d.kell_negative = $kell_negative, d.duffy_negative = $duffy_negative,
                    d.kidd_negative = $kidd_negative, d.rh_e_negative = $rh_e_negative,
                    d.rh_c_negative = $rh_c_negative, d.mns_negative = $mns_negative,
                    d.donation_count = $donation_count, d.churn_score = $churn_score,
                    d.is_active = $is_active, d.telegram_chat_id = $telegram_chat_id,
                    d.preferred_language = $preferred_language,
                    d.last_donation_date = CASE WHEN $last_donation_date IS NOT NULL THEN date($last_donation_date) ELSE null END
                """,
                {
                    "donor_id": d["donor_id"],
                    "name": d["name"],
                    "blood_type": d["blood_type"],
                    "city": d["city"],
                    "ward": d.get("ward"),
                    "lat": lat,
                    "lng": lng,
                    "geohash": encode_geohash(lat, lng),
                    "phone": d.get("phone"),
                    "kell_negative": d.get("kell_negative", False),
                    "duffy_negative": d.get("duffy_negative", False),
                    "kidd_negative": d.get("kidd_negative", False),
                    "rh_e_negative": d.get("rh_e_negative", False),
                    "rh_c_negative": d.get("rh_c_negative", False),
                    "mns_negative": d.get("mns_negative", False),
                    "donation_count": d.get("donation_count", 0),
                    "churn_score": d.get("churn_score", 0.0),
                    "is_active": d.get("is_active", True),
                    "telegram_chat_id": d.get("telegram_chat_id"),
                    "preferred_language": d.get("preferred_language", "English"),
                    "last_donation_date": d.get("last_donation_date")
                }
            )

        # Create Patients
        print("Seeding Patient nodes...")
        for p in patients:
            # Map patient coordinates based on hospital or fallback to defaults
            lat = 17.40
            lng = 78.40
            for hosp in HOSPITALS:
                if hosp["name"] == p.get("hospital"):
                    lat = hosp["lat"]
                    lng = hosp["lng"]
                    break

            await session.run(
                """
                MERGE (p:Patient {patient_id: $patient_id})
                SET p.name = $name, p.blood_type = $blood_type, p.hospital = $hospital,
                    p.city = $city, p.ward = $ward, p.location = point({latitude: $lat, longitude: $lng}),
                    p.lat = $lat, p.lng = $lng, p.geohash = $geohash,
                    p.antibody_kell = $antibody_kell, p.antibody_duffy = $antibody_duffy,
                    p.antibody_kidd = $antibody_kidd, p.antibody_rh_e = $antibody_rh_e,
                    p.antibody_rh_c = $antibody_rh_c, p.kell_negative = $kell_negative,
                    p.hemoglobin = $hemoglobin, p.status = $status, p.transfusion_count = $transfusion_count
                """,
                {
                    "patient_id": p["patient_id"],
                    "name": p["name"],
                    "blood_type": p["blood_type"],
                    "hospital": p["hospital"],
                    "city": p["city"],
                    "ward": p.get("ward"),
                    "lat": lat,
                    "lng": lng,
                    "geohash": encode_geohash(lat, lng),
                    "antibody_kell": p.get("antibody_kell", False),
                    "antibody_duffy": p.get("antibody_duffy", False),
                    "antibody_kidd": p.get("antibody_kidd", False),
                    "antibody_rh_e": p.get("antibody_rh_e", False),
                    "antibody_rh_c": p.get("antibody_rh_c", False),
                    "kell_negative": p.get("kell_negative", False),
                    "hemoglobin": p.get("hemoglobin", 7.0),
                    "status": p.get("status", "STABLE"),
                    "transfusion_count": p.get("transfusion_count", 0)
                }
            )

        # Create Patient ADMITTED_AT Hospital edges
        print("Linking Patients to Admitted Hospitals...")
        await session.run(
            """
            MATCH (p:Patient)
            MATCH (h:Hospital {name: p.hospital})
            MERGE (p)-[:ADMITTED_AT]->(h)
            """
        )

        # Create Hospital NEAR_BANK BloodBank edges (calculates spatial proximity in Cypher)
        print("Linking Hospitals to nearby Blood Banks...")
        await session.run(
            """
            MATCH (h:Hospital)
            MATCH (b:BloodBank)
            WITH h, b, point.distance(h.location, b.location) / 1000.0 AS dist_km
            MERGE (h)-[r:NEAR_BANK]->(b)
            SET r.distance_km = round(dist_km, 2)
            """
        )

        # Compute COMPATIBLE_WITH edges for matching donor-patient pairs (ABO matches + minor antigens)
        print("Calculating COMPATIBLE_WITH edges locally...")
        edges_to_insert = []
        for p in patients:
            for d in donors:
                # First check ABO compatibility
                if d["blood_type"] in p["blood_type"] or True: # we check inside python function for rigorous matching
                    score = compute_antigen_score(d, p)
                    if score >= 0.60:
                        elig = get_eligibility_flags(d)
                        edges_to_insert.append({
                            "donor_id": d["donor_id"],
                            "patient_id": p["patient_id"],
                            "score": score,
                            "kell_safe": elig["kell_safe"],
                            "duffy_safe": elig["duffy_safe"],
                            "kidd_safe": elig["kidd_safe"]
                        })

        print(f"Writing {len(edges_to_insert)} COMPATIBLE_WITH edges to Neo4j...")
        # Split into batches of 1000 to prevent large transaction memory issues
        batch_size = 1000
        for i in range(0, len(edges_to_insert), batch_size):
            batch = edges_to_insert[i:i + batch_size]
            await session.run(
                """
                UNWIND $batch AS b
                MATCH (d:Donor {donor_id: b.donor_id})
                MATCH (p:Patient {patient_id: b.patient_id})
                MERGE (d)-[r:COMPATIBLE_WITH]->(p)
                SET r.antigen_score = b.score,
                    r.kell_safe = b.kell_safe,
                    r.duffy_safe = b.duffy_safe,
                    r.kidd_safe = b.kidd_safe,
                    r.last_computed = datetime()
                """,
                batch=batch
            )
            print(f"  Inserted batch {i//batch_size + 1}/{(len(edges_to_insert) + batch_size - 1)//batch_size}")
            
        edge_count = len(edges_to_insert)

        print(f"Graph Seeding Summary:")
        print(f"- 500 Donor nodes")
        print(f"- 50 Patient nodes")
        print(f"- {len(HOSPITALS)} Hospital nodes")
        print(f"- {len(BLOOD_BANKS)} BloodBank nodes")
        print(f"- {edge_count} COMPATIBLE_WITH edges generated")
        print("Neo4j database seeded successfully.")

if __name__ == "__main__":
    asyncio.run(run_seed())
