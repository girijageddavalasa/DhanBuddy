# DhanBuddy

DhanBuddy is a friendly Indian voice assistant for goal-based savings planning, built for the Financial Services track of 10 Days of Voice Agents - #VoiceForBharat Edition.

It asks one question at a time, calculates a zero-return savings estimate, and tells the user whether they are on track. It never recommends financial products or requests sensitive banking or identity details.

![DhanBuddy Banner](images/banner.png)

## Voice pipeline

User speech -> Deepgram Nova-3 STT -> Gemini -> deterministic savings calculator -> Murf Falcon TTS -> LiveKit

Deepgram runs in multilingual mode for English, Hindi, and code-mixed speech. A small approved local knowledge retriever explains savings terms. It never performs financial calculations or product recommendations.

DhanBuddy uses Murf's Anisha voice with the en-IN locale and Conversation style. This warm Indian English voice was chosen to make a personal money conversation feel familiar and approachable.

## What it calculates

After collecting the goal, target amount, deadline, current savings, and monthly saving capacity, DhanBuddy reports:

- projected savings by the deadline,
- whether the goal is on track,
- approximate monthly shortfall or surplus,
- one practical adjustment.

The estimate assumes no investment returns and is educational, not personalized financial advice.

## Prerequisites

- Python 3.10+
- uv
- Node.js 18+
- pnpm
- A LiveKit Cloud project
- Murf, Deepgram, and Google API keys

## Configure

Copy backend/.env.example to backend/.env.local and frontend/.env.example to frontend/.env.local.

Set LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET, MURF_API_KEY, DEEPGRAM_API_KEY, and GOOGLE_API_KEY in the backend file. Set the matching LiveKit values and AGENT_NAME=dhanbuddy in the frontend file.

Never commit either .env.local file.

## Install and run

Backend:

    cd backend
    uv sync
    uv run python src/agent.py download-files
    uv run python src/agent.py dev

Frontend, in another terminal:

    cd frontend
    pnpm install
    pnpm dev

Open http://localhost:3000, select Talk to DhanBuddy, allow microphone access, and speak. On Windows, start_app.ps1 can start both services after setup.

## Test and lint

    cd backend
    uv run pytest
    uv run ruff check .

    cd frontend
    pnpm lint
    pnpm format:check

## Day 1 demo checklist

1. Start the backend and frontend with valid API keys.
2. Record a short conversation and say Financial Services track aloud.
3. Note the latency from end-of-user-speech to first audio out.
4. Post the video on LinkedIn. Mention DhanBuddy, the problem it solves, Murf Falcon as the fastest TTS API, and 10 Days of Voice Agents - VoiceForBharat Edition.
5. Tag Murf AI and include #VoiceForBharat.
6. Submit the LinkedIn post link using the Discord form.

## Day 2: safe multilingual conversations

DhanBuddy now includes:

- a structured identity, objectives, knowledge boundary, language policy, guardrails, and voice style,
- English, Hindi, and natural Hinglish mirroring,
- explicit refusals and a safe escalation script,
- deterministic local retrieval for approved savings explanations,
- one silence re-prompt and a graceful close after continued inactivity,
- short spoken replies with one question at a time,
- red-team cases documented in [RED_TEAM.md](RED_TEAM.md),
- a camera-ready script in [DAY2_DEMO.md](DAY2_DEMO.md).

The knowledge retriever is intentionally small and auditable. Add only reviewed educational entries to `backend/src/knowledge.py`. Do not use retrieval for arithmetic, eligibility decisions, approvals, or financial-product advice.

## Day 3: personalised voice interface

The frontend is now designed specifically for DhanBuddy's Financial Services track. It includes:

- a custom yellow, purple, and magenta DhanBuddy identity and rupee voice logo,
- clear Ready, Connecting, Listening, Speaking, and Call ended states,
- an animated audio visualiser and speaker indicators for the user and DhanBuddy,
- a microphone-permission error with simple browser recovery instructions,
- a visible four-step savings conversation guide and privacy reminders,
- transcript privacy controls and a Start again action after a call ends,
- automatic call closure when the user says "bye" or "goodbye".

See [DAY3_DEMO.md](DAY3_DEMO.md) for the camera-ready flow and test checklist.

## Day 4: persistent, consent-based memory

DhanBuddy now recognises a returning browser using a random anonymous caller ID
and stores approved profile facts in SQLite. The agent reads and writes memory only
through `lookup_caller`, `save_caller_memory`, and `forget_caller` tools. Saving and
permanent deletion both require explicit caller confirmation.

The database is created at `backend/data/dhanbuddy.db` and is intentionally ignored
by Git. The approved official-source knowledge library lives in `backend/rag/`.
See [notes/day4.md](notes/day4.md) for implementation details and
[DAY4_DEMO.md](DAY4_DEMO.md) for the restart, refusal, and forget-me demonstrations.

## Day 5: chained domain tools

DhanBuddy can now reuse a consented savings goal and compare three practical ways
to address a gap. `lookup_previous_goal` retrieves the saved inputs from SQLite,
then `compare_goal_scenarios` performs a deterministic zero-return calculation.
The result is spoken naturally and sent to the frontend as a timestamped visual
card over a reliable LiveKit data packet.

The source is **local deterministic calculation**, not a live external API or
market feed. This is stated in every tool result. Missing memory, incomplete data,
invalid values, and UI-delivery failures all have explicit fallback responses.
See [notes/day5.md](notes/day5.md) and [DAY5_DEMO.md](DAY5_DEMO.md).

## Day 6: consented outbound calls

DhanBuddy can place a requested savings-goal check-in call through a stored
LiveKit outbound SIP trunk backed by a provider such as Twilio. The launcher
requires explicit opt-in, dispatches the agent before dialing, waits for the
carrier answer, and prints a safe outcome and retry rule.

The opening identifies DhanBuddy, explains the reason for the call, and tells the
recipient how to stop future calls. Goal details are withheld until the recipient
confirms their preferred name. A spoken opt-out is persisted locally by anonymous
caller ID and immediately ends the call.

This integration uses real telephony status from LiveKit/SIP, but requires your
own provider account, number, credentials, and `LIVEKIT_SIP_OUTBOUND_TRUNK_ID`.
No phone number or SIP secret is committed. Voicemail detection is not enabled.
See [notes/day6.md](notes/day6.md) and [DAY6_DEMO.md](DAY6_DEMO.md).

## References

- https://github.com/murf-ai/murf-livekit-starter
- https://murf.ai/api/docs/voices-styles/voice-library
- https://murf.ai/api/docs/text-to-speech-models/falcon-2
- https://murf.ai/api/docs/text-to-speech/streaming
- https://docs.livekit.io/agents/start/voice-ai/

## License

MIT
