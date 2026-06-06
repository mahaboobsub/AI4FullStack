import asyncio
import logging
import time
logging.basicConfig(level=logging.WARNING)
from agents.graph import run_emergency_pipeline

async def test():
    run_id = int(time.time()) % 100000
    result = await run_emergency_pipeline({
        'request_id': f'REQ-TEST-{run_id}',
        'patient_id': 'P-10000',
        'blood_type': 'O-',
        'city': 'Hyderabad',
        'hospital_name': 'KIMS Secunderabad'
    })
    print('=== PIPELINE RESULT ===')
    print('Outcome:', result.get('outcome'))
    print('Chain length:', len(result.get('chain', [])))
    print('Monitor iterations:', result.get('monitor_iterations', 0))
    errors = result.get('errors', [])
    print('Error count:', len(errors))
    for e in errors:
        print('  ERR:', e[:120])
    print('Node timings (ms):', result.get('node_timings', {}))
    chain = result.get('chain', [])
    if chain:
        print('Top 3 chain donors:')
        for n in chain[:3]:
            pos = n.get('chain_position')
            name = n.get('donor_name')
            antigen = n.get('antigen_score')
            match = n.get('match_score')
            status = n.get('status')
            print(f"  [{pos}] {name} | antigen={antigen} | match={match} | status={status}")

asyncio.run(test())
