# Day 6 phone demo

## One-time telephony setup

You need a Twilio number and outbound SIP trunk, or the Linphone alternative from
the challenge guide. Do not commit usernames, passwords, phone numbers, or API
keys.

1. Copy `backend/telephony/outbound-trunk.example.json` and replace its placeholders locally.
2. Create the trunk with the LiveKit CLI:

   ```powershell
   lk sip outbound create telephony/outbound-trunk.example.json --auth-user "YOUR_SIP_USERNAME" --auth-pass "YOUR_SIP_PASSWORD"
   ```

3. Put the returned `ST_...` value in `backend/.env.local`:

   ```dotenv
   LIVEKIT_SIP_OUTBOUND_TRUNK_ID=ST_your_outbound_trunk_id
   AGENT_NAME=dhanbuddy
   ```

## Run

Terminal 1:

```powershell
cd C:\DLGM\DhanBuddy\backend
uv run python src\agent.py start
```

Terminal 2, using only a phone number you control:

```powershell
cd C:\DLGM\DhanBuddy\backend
uv run python -m outbound.launcher `
  --to "+91YOUR_CONTROLLED_NUMBER" `
  --caller-id "day6-demo-user" `
  --name "Girija" `
  --goal "college fees" `
  --deadline "three years" `
  --confirmed-opt-in
```

Twilio trial accounts may only call a verified destination number.

## Short camera script

Say: "This is Day 6 of VoiceForBharat. My track is Financial Services. DhanBuddy
now makes consented outbound savings check-in calls using LiveKit telephony and
Murf Falcon, the fastest TTS API."

Show Terminal 1, run the launcher in Terminal 2, and record the controlled phone
ringing.

When DhanBuddy asks whether it reached you, say:

"Yes, this is Girija. Please check my college-fee savings goal."

Then demonstrate the limit:

"Recommend a mutual fund and promise the return."

DhanBuddy should refuse and offer a zero-return educational estimate. Finally
say:

"Stop calling me."

It should confirm the opt-out and end the call. Show the terminal outcome without
showing any secrets or the full phone number.
