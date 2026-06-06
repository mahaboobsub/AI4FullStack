"""Inspect Neo4j graph state."""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from core.neo4j_client import get_driver

async def main():
    d = get_driver()
    async with d.session() as s:
        r = await s.run("MATCH (d:Donor) RETURN d.donor_id AS id, d.lat AS lat, d.lng AS lng, d.location AS loc, d.phone AS phone LIMIT 3")
        async for rec in r:
            print(dict(rec))
        r2 = await s.run("MATCH ()-[c:COMPATIBLE_WITH]->() RETURN count(c) AS edge_count")
        rec2 = await r2.single()
        print(f"COMPATIBLE_WITH edges: {rec2['edge_count']}")
        r3 = await s.run("MATCH ()-[r:IN_CHAIN]->() RETURN count(r) AS chain_count")
        rec3 = await r3.single()
        print(f"IN_CHAIN edges: {rec3['chain_count']}")
        # Check patient lat/lng
        r4 = await s.run("MATCH (p:Patient) RETURN p.patient_id AS id, p.lat AS lat, p.lng AS lng, p.location AS loc LIMIT 3")
        async for rec in r4:
            print(dict(rec))
    await d.close()

asyncio.run(main())
