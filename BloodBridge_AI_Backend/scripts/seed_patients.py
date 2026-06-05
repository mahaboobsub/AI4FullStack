"""Seed only patients into Supabase + Neo4j."""
import asyncio, random, logging
from datetime import datetime
from core.database import get_supabase_admin
from core.neo4j_client import get_driver

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BLOOD_TYPES = ["A+","A-","B+","B-","AB+","AB-","O+","O-"]
CITIES = ["Hyderabad","Warangal","Mumbai","Delhi","Bangalore"]
FIRST = ["Rahul","Priya","Amit","Sneha","Vikram","Anjali","Ramesh","Kiran","Sanjay","Deepa","Meena","Arjun"]
LAST = ["Sharma","Reddy","Patel","Kumar","Singh","Nair","Rao","Verma","Das","Gupta","Krishnan","Iyer"]
HOSPITALS = {
    "Hyderabad": ["KIMS Secunderabad","Apollo Banjara Hills","Gandhi Hospital","Nizam Institute","Yashoda Somajiguda"],
    "Warangal": ["MGM Hospital Warangal","Kakatiya Medical College"],
    "Mumbai": ["KEM Hospital","Lilavati Hospital","Tata Memorial"],
    "Delhi": ["AIIMS New Delhi","Safdarjung Hospital","Max Saket"],
    "Bangalore": ["Narayana Health","Manipal Hospital Whitefield","St Johns Medical"]
}
WARDS = ["ICU","General Ward","Pediatric","Hematology","Oncology"]

patients = []
for i in range(10):
    city = random.choice(CITIES)
    patients.append({
        "patient_id": f"P-{random.randint(10000,99999)}",
        "name": f"patient{i+1}",
        "phone": f"+919{random.randint(100000000, 999999999)}",
        "password": "patient123",
        "age": random.randint(3,45),
        "blood_type": random.choice(BLOOD_TYPES),
        "hospital": random.choice(HOSPITALS[city]),
        "ward": random.choice(WARDS),
        "city": city,
        "hemoglobin": round(random.uniform(6.0,11.0),1),
        "transfusion_count": random.randint(0,30),
        "status": random.choice(["CRITICAL","STABLE","OVERDUE"]),
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()+"Z"
    })

async def seed_patients():
    supabase = get_supabase_admin()
    driver = get_driver()

    logger.info("Inserting 10 patients into Supabase...")
    try:
        res = supabase.table("patients").insert(patients).execute()
        logger.info(f"Patients inserted: {len(res.data)} rows")
    except Exception as e:
        logger.error(f"Supabase error: {e}")

    logger.info("Syncing patients to Neo4j...")
    async with driver.session() as session:
        for p in patients:
            await session.run(
                "MERGE (n:Patient {patient_id: $id}) "
                "SET n.blood_type=$bt, n.city=$city, n.hospital=$hospital, n.status=$status",
                id=p["patient_id"], bt=p["blood_type"], city=p["city"],
                hospital=p["hospital"], status=p["status"]
            )
        await session.run(
            "MATCH (d:Donor),(p:Patient) "
            "WHERE d.blood_type=p.blood_type AND d.city=p.city AND d.is_active=true "
            "MERGE (d)-[r:COMPATIBLE_WITH]->(p) "
            "SET r.score=0.9, r.created_at=datetime()"
        )

    logger.info("Patient seeding complete! Here are the 10 patients:")
    for p in patients:
        logger.info(f"  {p['patient_id']} | {p['name']} | {p['blood_type']} | {p['hospital']} ({p['city']})")

asyncio.run(seed_patients())
