#!/usr/bin/env python3
"""
BloodBridge AI -- Telegram Webhook Setup via ngrok
===================================================
Run this AFTER starting ngrok to automatically:
  1. Get your current ngrok public URL
  2. Register it as the Telegram webhook
  3. Update TELEGRAM_WEBHOOK_URL in your .env file

Usage:
  Step 1:  ngrok http 8000
  Step 2:  python setup_webhook.py
  Step 3:  python -m uvicorn main:app --reload --port 8000

Requirements:
  pip install httpx python-dotenv
"""
import sys
import re
import asyncio
from pathlib import Path

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(1)

try:
    from dotenv import load_dotenv, set_key
    import os
    load_dotenv()
except ImportError:
    print("ERROR: python-dotenv not installed. Run: pip install python-dotenv")
    sys.exit(1)

ENV_FILE = Path(__file__).parent / ".env"
NGROK_API = "http://127.0.0.1:4040/api/tunnels"


async def get_ngrok_url() -> str:
    """Query ngrok's local API to get the current public HTTPS tunnel URL."""
    print("Looking for running ngrok tunnel...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(NGROK_API)
            resp.raise_for_status()
            tunnels = resp.json().get("tunnels", [])

        https_tunnels = [t for t in tunnels if t.get("proto") == "https"]
        if not https_tunnels:
            print("ERROR: No HTTPS ngrok tunnel found.")
            print("Make sure ngrok is running: ngrok http 8000")
            sys.exit(1)

        url = https_tunnels[0]["public_url"]
        print(f"  Found ngrok URL: {url}")
        return url
    except httpx.ConnectError:
        print("ERROR: Cannot reach ngrok API at http://127.0.0.1:4040")
        print("Make sure ngrok is running: ngrok http 8000")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR querying ngrok: {e}")
        sys.exit(1)


async def set_telegram_webhook(bot_token: str, webhook_url: str, secret: str) -> bool:
    """Register the webhook URL with Telegram Bot API."""
    full_url = f"{webhook_url}/webhook/telegram"
    api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"

    print(f"\nRegistering Telegram webhook...")
    print(f"  URL: {full_url}")

    params = {
        "url": full_url,
        "allowed_updates": ["message", "callback_query"],
        "drop_pending_updates": True,
    }
    if secret:
        params["secret_token"] = secret

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(api_url, json=params)
        data = resp.json()

    if data.get("ok"):
        print(f"  Telegram webhook set successfully!")
        print(f"  Description: {data.get('description', 'OK')}")
        return True
    else:
        print(f"  ERROR setting webhook: {data.get('description', data)}")
        return False


async def get_webhook_info(bot_token: str):
    """Print current webhook info for verification."""
    api_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(api_url)
        data = resp.json()
    if data.get("ok"):
        info = data.get("result", {})
        print(f"\nCurrent webhook info:")
        print(f"  URL            : {info.get('url', 'not set')}")
        print(f"  Pending updates: {info.get('pending_update_count', 0)}")
        print(f"  Last error     : {info.get('last_error_message', 'none')}")


def update_env_file(webhook_url: str):
    """Update TELEGRAM_WEBHOOK_URL in the .env file."""
    if not ENV_FILE.exists():
        print(f"\nWARNING: .env file not found at {ENV_FILE}")
        return

    content = ENV_FILE.read_text(encoding="utf-8")
    full_url = f"{webhook_url}/webhook/telegram"

    # Replace TELEGRAM_WEBHOOK_URL= line
    new_content = re.sub(
        r"^TELEGRAM_WEBHOOK_URL=.*$",
        f"TELEGRAM_WEBHOOK_URL={full_url}",
        content,
        flags=re.MULTILINE
    )

    if new_content != content:
        ENV_FILE.write_text(new_content, encoding="utf-8")
        print(f"\n  .env updated: TELEGRAM_WEBHOOK_URL={full_url}")
    else:
        print(f"\n  NOTE: Could not find TELEGRAM_WEBHOOK_URL= in .env — please add it manually:")
        print(f"  TELEGRAM_WEBHOOK_URL={full_url}")


async def main():
    print("=" * 60)
    print("  BloodBridge AI -- Telegram Webhook Setup (ngrok)")
    print("=" * 60)

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    webhook_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()

    if not bot_token:
        print("\nERROR: TELEGRAM_BOT_TOKEN not found in .env")
        sys.exit(1)

    bot_display = f"{bot_token[:10]}...{bot_token[-6:]}"
    print(f"\nBot token: {bot_display}")
    print(f"Secret   : {'set' if webhook_secret else 'NOT SET (webhook will be less secure)'}")

    # 1. Get ngrok URL
    ngrok_url = await get_ngrok_url()

    # 2. Register webhook with Telegram
    ok = await set_telegram_webhook(bot_token, ngrok_url, webhook_secret)

    if ok:
        # 3. Update .env
        update_env_file(ngrok_url)

        # 4. Print verification info
        await get_webhook_info(bot_token)

        print("\n" + "=" * 60)
        print("  DONE! Webhook is live.")
        print("=" * 60)
        print(f"\nNext steps:")
        print(f"  1. Keep ngrok running in its terminal")
        print(f"  2. Start the API:")
        print(f"     uvicorn main:app --reload --port 8000")
        print(f"  3. Open Telegram and send /start to your bot")
        print(f"     Bot: https://t.me/{bot_token.split(':')[0]}")
        print(f"\nNOTE: ngrok URLs change every restart (free plan).")
        print(f"      Re-run this script each time you restart ngrok.")
    else:
        print("\nSetup failed. Check your TELEGRAM_BOT_TOKEN and ngrok status.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
