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

## References

- https://github.com/murf-ai/murf-livekit-starter
- https://murf.ai/api/docs/voices-styles/voice-library
- https://murf.ai/api/docs/text-to-speech-models/falcon-2
- https://murf.ai/api/docs/text-to-speech/streaming
- https://docs.livekit.io/agents/start/voice-ai/

## License

MIT
