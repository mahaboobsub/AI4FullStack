import asyncio
import traceback
from api.webhooks import telegram_webhook

class MockRequest:
    def __init__(self):
        self.headers = {"X-Telegram-Bot-Api-Secret-Token": "8f7c2d4a9e1b6c3d5f8a0b2e7c9d1f4a"}
    
    async def json(self):
        return {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "date": 1,
                "chat": {"id": 123, "type": "private"},
                "text": "/start"
            }
        }

async def run():
    req = MockRequest()
    try:
        res = await telegram_webhook(req)
        print("Success:", res)
    except Exception as e:
        print("Exception caught:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run())
