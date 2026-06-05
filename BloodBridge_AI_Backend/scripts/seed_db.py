import asyncio
import random
import uuid
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import existing clients from BloodBridge
from core.database import get_supabase_admin
from core.neo4j_client import get_driver

BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
CITIES = ["Hyderabad", "Warangal", "Mumbai", "Delhi", "Bangalore"]
FIRST_NAMES = ["Rahul", "Priya", "Amit", "Sneha", "Vikram", "Anjali", "Ramesh", "Kiran", "Sanjay", "Deepa"]
LAST_NAMES = ["Sharma", "Reddy", "Patel", "Kumar", "Singh", "Nair", "Rao", "Verma", "Das", "Gupta"]

def generate_donors(count=100):
    donors = []
    for i in range(count):
        donor_id = f"D-{random.randint(10000, 99999)}"
        name = f"donor{i+1}"
        blood_type = random.choice(BLOOD_TYPES)
        city = random.choice(CITIES)
        phone = f"+91{random.randint(9000000000, 9999999999)}"
        
        donors.append({
            "donor_id": donor_id,
            "name": name,
            "password": "donor123",
            "blood_type": blood_type,
            "city": city,
            "phone": phone,
            "is_active": True,
            "donation_count": random.randint(0, 10),
            "lives_saved": random.randint(0, 15),
            "preferred_language": random.choice(["Hindi", "English", "Telugu"]),
            "kell_negative": random.choice([True, False]),
            "created_at": datetime.utcnow().isoformat() + "Z"
        })
    return donors

HOSPITALS = {
    "Hyderabad": ["KIMS Secunderabad", "Apollo Banjara Hills", "Nizam's Institute", "Gandhi Hospital", "Yashoda Somajiguda"],
    "Warangal": ["MGM Hospital Warangal", "Kakatiya Medical College"],
    "Mumbai": ["KEM Hospital", "Lilavati Hospital", "Tata Memorial"],
    "Delhi": ["AIIMS New Delhi", "Safdarjung Hospital", "Max Saket"],
    "Bangalore": ["Narayana Health", "Manipal Hospital Whitefield", "St. John's Medical"]
}
WARDS = ["ICU", "General Ward", "Pediatric", "Hematology", "Oncology"]
STATUSES = ["CRITICAL", "STABLE", "OVERDUE"]

def generate_patients(count=10):
    patients = []
    for i in range(count):
        patient_id = f"P-{random.randint(10000, 99999)}"
        name = f"patient{i+1}"
        blood_type = random.choice(BLOOD_TYPES)
        city = random.choice(CITIES)
        hospital = random.choice(HOSPITALS[city])
        age = random.randint(3, 45)
        
        patients.append({
            "patient_id": patient_id,
            "name": name,
            "phone": f"+919{random.randint(100000000, 999999999)}",
            "password": "patient123",
            "age": age,
            "blood_type": blood_type,
            "hospital": hospital,
            "ward": random.choice(WARDS),
            "city": city,
            "hemoglobin": round(random.uniform(6.0, 11.0), 1),
            "transfusion_count": random.randint(0, 30),
            "status": random.choice(STATUSES),
            "antibody_kell": random.random() < 0.15,
            "antibody_duffy": random.random() < 0.1,
            "kell_negative": random.random() < 0.2,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat() + "Z"
        })
    return patients

async def seed():
    logger.info("Starting database seeding...")
    supabase = get_supabase_admin()
    driver = get_driver()
    
    donors = generate_donors(100)
    patients = generate_patients(10)
    
    # 1. Insert into Supabase
    logger.info("Inserting 100 Donors into Supabase...")
    try:
        supabase.table("donors").insert(donors).execute()
        logger.info("Donors inserted successfully.")
    except Exception as e:
        logger.error(f"Error inserting donors: {e}")
        
    logger.info("Inserting 10 Patients into Supabase...")
    try:
        supabase.table("patients").insert(patients).execute()
        logger.info("Patients inserted successfully.")
    except Exception as e:
        logger.error(f"Error inserting patients: {e}")

    # 2. Insert into Neo4j
    logger.info("Syncing nodes to Neo4j...")
    async with driver.session() as session:
        # Create Donors
        for d in donors:
            await session.run("""
                MERGE (n:Donor {donor_id: $id})
                SET n.blood_type = $bt, n.city = $city, n.is_active = $active
            """, id=d["donor_id"], bt=d["blood_type"], city=d["city"], active=d["is_active"])
            
        # Create Patients
        for p in patients:
            await session.run("""
                MERGE (n:Patient {patient_id: $id})
                SET n.blood_type = $bt, n.city = $city, n.hospital = $hospital, n.status = $status
            """, id=p["patient_id"], bt=p["blood_type"], city=p["city"], hospital=p["hospital"], status=p["status"])
            
        # Create COMPATIBLE_WITH edges for same blood type in same city
        logger.info("Generating COMPATIBLE_WITH edges in Neo4j...")
        await session.run("""
            MATCH (d:Donor), (p:Patient)
            WHERE d.blood_type = p.blood_type AND d.city = p.city AND d.is_active = true
            MERGE (d)-[r:COMPATIBLE_WITH]->(p)
            SET r.score = 0.9, r.created_at = datetime()
        """)
        
    logger.info("Seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed())
