#!/bin/bash
BOT_TOKEN=$(grep TELEGRAM_BOT_TOKEN /home/ubuntu/app/AI4FullStack/BloodBridge_AI_Backend/.env.production | cut -d= -f2)
SECRET=$(grep TELEGRAM_WEBHOOK_SECRET /home/ubuntu/app/AI4FullStack/BloodBridge_AI_Backend/.env.production | cut -d= -f2)
echo "Bot token starts with: ${BOT_TOKEN:0:8}..."
echo "Setting webhook to: https://inquilab-ai.duckdns.org/webhook/telegram"
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" -d "url=https://inquilab-ai.duckdns.org/webhook/telegram" -d "secret_token=${SECRET}"
echo ""
echo "--- Webhook Info ---"
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"
echo ""
