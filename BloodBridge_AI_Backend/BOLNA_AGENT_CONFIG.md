# Bolna Agent Configuration for BloodBridge AI (B3)

## Agent Name
**BloodBridge Donor Coordinator**

## Voice Configuration
- **Provider**: Sarvam AI  
- **Voice**: Hindi Female (natural)
- **Language**: Hindi (primary), English (fallback)

## Call Script (2-sentence NGO intro)
> "Namaste, yeh Blood Warriors Foundation se bol rahe hain. Aapke area mein ek patient ko [blood_type] blood ki zaroorat hai — kya aap donate kar sakte hain?"

## Structured Capture
- **YES**: Fire webhook with `{donor_id, response: "CONFIRMED", call_id}`
- **NO**: Fire webhook with `{donor_id, response: "DECLINED", call_id}`

## Timing Rules
- **TRAI Compliance**: Calls only between 8:00 AM – 9:00 PM IST
- **No-response timeout**: 20 seconds → disconnect → trigger SMS fallback
- **Max call duration**: 120 seconds

## Webhook Configuration
- **URL**: `{APP_BASE_URL}/webhook/bolna`
- **Secret**: `BOLNA_WEBHOOK_SECRET` (HMAC verification)
- **Events**: `call_completed`, `call_failed`, `call_unanswered`

## Fallback Chain
1. Voice call attempt 1
2. Wait 12 minutes
3. Voice call attempt 2 (if attempt 1 PLACED > 12 min)
4. SMS fallback via Twilio (if attempt 2 still unanswered)
