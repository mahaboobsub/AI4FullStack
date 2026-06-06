# DEMO_MOCK_MODE — Decision Guide

## Decision (locked for this repo)

| Environment | `DEMO_MOCK_MODE` | Why |
|-------------|------------------|-----|
| **Local demo / hackathon / offline** | `true` | Voice calls simulate success; Neo4j matcher returns synthetic donors if graph is down. No Bolna/ngrok required. |
| **Staging with real APIs** | `false` | Live Bolna voice + real Telegram; requires `BOLNA_API_KEY`, `TELEGRAM_BOT_TOKEN`, ngrok webhook. |
| **Production** | `false` (required) | `main.py` **aborts startup** if `DEMO_MOCK_MODE=true` when `APP_ENV=production`. |

## What it affects

| Service | `true` | `false` |
|---------|--------|---------|
| `voice_service.make_bolna_call` | Returns simulated `INITIATED` | Calls Bolna API |
| `neo4j_match.find_top_donors` | Synthetic donor pool fallback | Live graph / matching engine |
| Admin config `GET /api/admin/config` | Exposes `demo_mock_mode: true` | Exposes `demo_mock_mode: false` |

## Recommended `.env` for local demos

```env
APP_ENV=development
DEMO_MOCK_MODE=true
```

## Recommended `.env` for live integration testing

```env
APP_ENV=development
DEMO_MOCK_MODE=false
BOLNA_API_KEY=...
BOLNA_AGENT_ID=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_WEBHOOK_URL=https://<ngrok>/webhook/telegram
```

## Verify current mode

```powershell
cd BloodBridge_AI_Backend
python -c "from core.config import get_settings; s=get_settings(); print(f'DEMO_MOCK_MODE={s.DEMO_MOCK_MODE} APP_ENV={s.APP_ENV}')"
```

Or open **Admin → System Config** banner (reads `demo_mock_mode` from `/api/admin/config`).
