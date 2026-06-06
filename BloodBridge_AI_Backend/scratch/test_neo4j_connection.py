"""Quick standalone Neo4j connectivity test (Windows-safe)."""
import asyncio
import os
import sys

# Force utf-8 stdout
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Load .env manually
from pathlib import Path
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

NEO4J_URI = os.getenv("NEO4J_URI", "")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

async def test():
    print("=" * 60)
    print("NEO4J CONNECTION TEST")
    print("=" * 60)
    print(f"  URI      : {NEO4J_URI}")
    print(f"  Username : {NEO4J_USERNAME}")
    print(f"  Password : {'*' * len(NEO4J_PASSWORD) if NEO4J_PASSWORD else '(empty)'}")
    print()

    if not NEO4J_URI:
        print("[FAIL] NEO4J_URI is empty. Set it in .env")
        return

    try:
        from neo4j import AsyncGraphDatabase
    except ImportError:
        print("[FAIL] neo4j package not installed. Run: pip install neo4j")
        return

    print("1. Creating async driver...")
    driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

    try:
        print("2. Verifying connectivity...")
        await driver.verify_connectivity()
        print("   [OK] Connectivity verified")

        print("3. Running test query: RETURN 1 AS ok ...")
        async with driver.session() as session:
            result = await session.run("RETURN 1 AS ok")
            record = await result.single()
            if record and record["ok"] == 1:
                print("   [OK] Query returned 1 -- correct")
            else:
                print(f"   [FAIL] Unexpected result: {record}")

        print("4. Counting nodes in database...")
        async with driver.session() as session:
            result = await session.run(
                "MATCH (n) RETURN labels(n) AS labels, count(n) AS cnt ORDER BY cnt DESC LIMIT 10"
            )
            records = [r async for r in result]
            if records:
                print("   Node counts by label:")
                for r in records:
                    print(f"     {r['labels']}: {r['cnt']}")
            else:
                print("   (no nodes in database -- empty graph)")

        print()
        print("=" * 60)
        print("[SUCCESS] NEO4J IS WORKING!")
        print("=" * 60)

    except Exception as e:
        print()
        print("=" * 60)
        print(f"[FAIL] NEO4J ERROR: {type(e).__name__}: {e}")
        print("=" * 60)

    finally:
        await driver.close()

if __name__ == "__main__":
    asyncio.run(test())
