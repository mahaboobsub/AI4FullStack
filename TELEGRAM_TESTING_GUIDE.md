# BloodBridge AI — Telegram Bot Testing Guide

> This guide walks you through every Telegram bot feature with exact messages to send and expected replies, presented as chat conversations.

---

## Prerequisites

Before testing, make sure all 3 services are running:

1. **Backend**: `.\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000`
2. **Ngrok**: `ngrok http 8000`
3. **Webhook**: `.\venv\Scripts\python.exe setup_webhook.py`

Then open your Telegram bot. You can find it by searching for the bot username you created with @BotFather.

---

## Test 1: First-Time User Onboarding (Consent Flow)

When a brand-new user opens the bot for the first time, they go through a DPDP-compliant consent flow.

### Chat:

```
👤 You:    /start

🤖 Bot:    🩸 Welcome to BloodBridge AI!

           We coordinate rare matched blood donations for Thalassemia patients.

           🛡️ DPDP Act Compliance & Data Consent:
           Under Section 6 of India's Digital Personal Data Protection Act 2023,
           we need your explicit consent to store your data and contact you for
           emergency blood requests.

           Reply HAAN or YES to accept and start. Reply NO to reject.
```

### Accept Consent:

```
👤 You:    YES

🤖 Bot:    🎉 Consent Granted & Onboarding Started!

           Thank you! We have registered your consent. To complete your
           registration and set your blood group, type: /register [blood_type]
           (e.g. /register B+).
```

### Reject Consent:

```
👤 You:    NO

🤖 Bot:    Understood. We will not store your data or contact you.
           Feel free to reach out to us if you change your mind.
```

---

## Test 2: Register as a Donor

After accepting consent, register your blood type.

### Chat:

```
👤 You:    /register B+

🤖 Bot:    🎉 Registration complete! Registered as B+ in Hyderabad. Thank you!
```

### Invalid Blood Type:

```
👤 You:    /register X

🤖 Bot:    Invalid blood type. Supported: A+, A-, B+, B-, AB+, AB-, O+, O-
```

### Missing Blood Type:

```
👤 You:    /register

🤖 Bot:    Please provide your blood type. Example: /register B+
```

### Update Existing Registration:

```
👤 You:    /register O-

🤖 Bot:    Updated your registered blood type to O-.
```

---

## Test 3: Check Your Impact & Badges

View your donation stats, badges earned, and streak.

### Chat:

```
👤 You:    /impact

🤖 Bot:    🏆 Your BloodBridge Impact Profile:

           - Donor Name: Telegram Donor 1234
           - Lives Saved: 0 🩸
           - Total Donations: 0
           - Current Streak: 0 days
           - Badges Earned: None yet! Keep donating to earn badges.

           Thank you for being a vital part of the Blood Warriors community!
```

### Alternative Command:

```
👤 You:    /badges

🤖 Bot:    (Same response as /impact — shows your badges and stats)
```

---

## Test 4: Check Emergency Chain Status

Check the real-time status of a blood donation chain for a patient.

### Chat:

```
👤 You:    /status P-12345

🤖 Bot:    📊 Chain Status for Patient P-12345 (Request: REQ-54321)
           - Overall Request Status: IN_PROGRESS
           - Confirmed: 2 ✅
           - Alerted/Outreached: 4 ⏳
           - Declined: 1 ❌
           - Pending: 1 💤
```

### No Active Request:

```
👤 You:    /status P-99999

🤖 Bot:    No active emergency requests found for patient P-99999.
```

### Missing Patient ID:

```
👤 You:    /status

🤖 Bot:    Please provide a Patient ID. Example: /status P-1002
```

---

## Test 5: View City Leaderboard

See the top-ranked blood donors in your city.

### Chat:

```
👤 You:    /leaderboard

🤖 Bot:    🏆 Leaderboard for Hyderabad this month:

           1. Ravi Kumar - 12 lives saved 🩸
           2. Priya Sharma - 9 lives saved 🩸
           3. Anand Reddy - 7 lives saved 🩸
           4. Sunita Verma - 5 lives saved 🩸
           5. Mohammed Ali - 4 lives saved 🩸
```

### Empty Leaderboard:

```
👤 You:    /leaderboard

🤖 Bot:    🏆 Leaderboard for Hyderabad this month:

           No leaderboard entries found for this month.
```

---

## Test 6: View Your Consent Status (DPDP)

Check which data consent categories you have granted or revoked.

### Chat:

```
👤 You:    /consent

🤖 Bot:    🛡️ Your Data Consent Status:
           - data_storage: ✅ Granted
           - outreach_telegram: ✅ Granted
           - outreach_sms: ✅ Granted
```

---

## Test 7: Revoke Consent

Revoke a specific consent type (DPDP compliance).

### Chat:

```
👤 You:    /revoke outreach_sms

🤖 Bot:    Successfully revoked consent for outreach_sms.
           We will no longer contact you via this channel.
```

### Revoke All:

```
👤 You:    /revoke all

🤖 Bot:    Successfully revoked consent for all.
           We will no longer contact you via this channel.
```

### Missing Type:

```
👤 You:    /revoke

🤖 Bot:    Please provide consent type
           (e.g. outreach_telegram, outreach_sms, or all).
```

---

## Test 8: Export Your Personal Data (Right to Access)

Download all data the system holds about you (DPDP Section 11).

### Chat:

```
👤 You:    /mydata

🤖 Bot:    🛡️ DPDP Right to Access - Your Personal Data Export:

           Name: Telegram Donor 1234
           Phone: +919876543210
           Blood Type: B+
           City: Hyderabad
           Consent Outreach: True
           Registered At: 2026-06-05T10:30:00Z
```

---

## Test 9: Delete All Your Data (Right to Erasure)

Permanently erase your profile and donation history (DPDP Section 12).

### Chat (Step 1 — Warning):

```
👤 You:    /deletedata

🤖 Bot:    ⚠️ WARNING: This will permanently erase your profile and
           donation history. To proceed, type /deletedata CONFIRM.
```

### Chat (Step 2 — Confirm Deletion):

```
👤 You:    /deletedata CONFIRM

🤖 Bot:    🚮 Right to Erasure Executed. Your profile and all history
           have been permanently deleted from our servers.
```

---

## Test 10: Respond to an Emergency Alert

When an emergency is triggered and you are matched as a compatible donor, the bot will send you an alert message. Here is how the conversation flows:

### Incoming Alert (Bot initiates):

```
🤖 Bot:    🚨 URGENT: O- blood needed at Government General Hospital,
           Hyderabad. A Thalassemia patient needs your help urgently.
           Reply YES to confirm your donation or NO to decline.
```

### Accept:

```
👤 You:    YES

🤖 Bot:    🩸 Thank you! Your donation is confirmed. The hospital staff
           has been notified. We will contact you with scheduling details.
```

### Decline:

```
👤 You:    NO

🤖 Bot:    Understood. Thank you for letting us know.
           We will reach out to you next time.
```

### Accept in Hindi:

```
👤 You:    HAAN

🤖 Bot:    🩸 Thank you! Your donation is confirmed. The hospital staff
           has been notified. We will contact you with scheduling details.
```

---

## Test 11: AI Freeform Chat (Groq Llama-3.3)

The bot also supports natural language conversations powered by Groq's Llama-3.3-70B model. You can ask anything related to blood donation.

### Chat:

```
👤 You:    I want to donate blood, how can I help?

🤖 Bot:    🩸 Thank you for your willingness to help! As a registered donor,
           you'll be automatically matched when a compatible patient needs
           blood in your city. You can check your current stats with /impact
           and view your city's leaderboard with /leaderboard. Stay active
           and we'll reach out when someone needs you! ✅
```

### Chat:

```
👤 You:    What blood types are compatible with O negative?

🤖 Bot:    O- is the universal donor for red blood cells! O- blood can be
           given to patients of any blood type (A+, A-, B+, B-, AB+, AB-,
           O+, O-). However, O- patients can only receive O- blood.
           This makes O- donors extremely valuable — thank you for
           being part of the community! 🩸
```

### Chat:

```
👤 You:    How often can I donate blood?

🤖 Bot:    According to WHO and NBTC guidelines, you must wait a minimum
           of 56 days (8 weeks) between whole blood donations. Your
           hemoglobin level must also be above 12.5 g/dL. Our system
           automatically tracks your eligibility! ✅
```

---

## Test 12: Photo OCR Onboarding

You can send a photo of your blood group card and the bot will automatically extract your blood type using AI-powered OCR.

### Chat:

```
👤 You:    📸 (Send a photo of your blood group card)

🤖 Bot:    📸 OCR Scan Success!

           Extracted Blood Type: B+
           Confidence: 94%

           Your donor profile has been updated automatically.
```

### Failed Scan:

```
👤 You:    📸 (Send an unclear or unrelated photo)

🤖 Bot:    📸 OCR Scan failed to detect a valid blood group card.
           Please try again with a clearer image.
```

---

## Quick Command Reference

| Command | Description | Who Can Use |
|---------|-------------|-------------|
| `/start` | Welcome message + consent prompt | Everyone |
| `/register B+` | Register or update your blood type | Everyone |
| `/impact` | View your donation stats and badges | Donors |
| `/badges` | Same as /impact | Donors |
| `/status P-1002` | Check emergency chain status | Everyone |
| `/leaderboard` | View city leaderboard | Everyone |
| `/consent` | View your consent status | Donors |
| `/revoke sms` | Revoke a consent type | Donors |
| `/mydata` | Export all your personal data | Donors |
| `/deletedata` | Request data deletion (requires CONFIRM) | Donors |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Bot not responding at all | Make sure ngrok is running and `setup_webhook.py` was executed |
| Bot replies in Hindi | Fixed! Default is now English. If still Hindi, re-run the backend server |
| `500 Internal Server Error` in backend logs | Check that the Groq API key is valid in `.env` |
| "StructuredTool does not support sync invocation" | This bug has been fixed. Restart the backend if you still see it |
| Bot says "type /help for commands" | The Groq API key might be missing or invalid — bot falls back to command mode |

---

*Last updated: June 2026*
