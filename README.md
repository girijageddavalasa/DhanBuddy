# DhanBuddy

DhanBuddy is a browser-based Indian voice assistant built for the Financial
Services track of **10 Days of Voice Agents — VoiceForBharat Edition**.

## Day 1 — Voice Agent

Day 1 provides a basic real-time voice conversation:

```text
Browser → LiveKit → Deepgram STT → Gemini → Murf Falcon TTS → Browser audio
```

- LiveKit connects the browser and Python voice worker.
- Deepgram Nova-3 multilingual transcribes English, Hindi, and supported
  code-mixed speech.
- Gemini generates short conversational responses.
- Murf Falcon produces the speech output.
- Murf's **Abhinav** voice is configured because it is an Indian voice whose
  Falcon configuration supports Indian English and Hindi.

English and Hindi are the configured Day 1 language path. Telugu and Tamil remain
target languages, but this single-session STT configuration does not claim them:
Deepgram Nova-3 `language="multi"` currently includes Hindi and English, while
Telugu and Tamil require separate fixed-language recognition configuration.

Day 1 deliberately does not include memory, OCR, RAG, financial calculators,
outbound calls, analytics, escalation, specialist agents, or orchestration.

## Day 2 — Personality, Job and Limits

DhanBuddy is a voice-first financial information assistant for Indian users. It
helps users understand information they provide, make sense of described spending
or records, and discuss general financial information. It is not a bank,
investment advisor, financial institution, or government authority.

The Day 2 prompt defines clear knowledge boundaries. DhanBuddy distinguishes user-
provided or tool-returned facts from unavailable information. It must not invent
transactions, balances, rates, eligibility, approvals, or other financial facts.
No financial-data tools or retrieval system are implemented yet.

Financial guardrails prohibit requesting OTPs, PINs, CVVs, passwords, banking
credentials, or card-security information. DhanBuddy cannot perform transactions,
confirm payments or refunds, promise approvals, guarantee returns, or impersonate
an institution. Sensitive disputes use a reusable preparation script without
claiming that a human is immediately available.

The agent mirrors English, Hindi, or supported Hindi-English code-mixing. Hindi
responses use Devanagari unless transliteration is requested. Telugu and Tamil
remain target languages and are not claimed as runtime-verified.

Responses are short and designed to be spoken. The LiveKit session gives one
inactivity reprompt, gives a different closing response after continued silence,
then ends gracefully. Guardrail scenarios are documented in `RED_TEAM.md`.

**Runtime verification is pending because the local voice environment has not yet
been configured.**

## Day 3 — Personalized Frontend

Day 3 adds a lightweight interface built with plain HTML, CSS, and JavaScript. It
is served directly by a small FastAPI application and uses the LiveKit browser SDK
without exposing API credentials in client-side code.

The interface includes DhanBuddy branding, responsive desktop and mobile layouts,
visible focus states, and five clear voice states: Ready, Connecting, Listening,
Speaking, and Call ended. It also handles blocked microphone permission, LiveKit
connection errors, retrying, ending a conversation, and starting again. The bill
upload button is a visual placeholder only; OCR is not implemented.

Start the static frontend and secure token endpoint with:

```powershell
cd backend
uv run uvicorn src.web:app --reload --port 8000
```

Then open `http://localhost:8000`. Run the LiveKit voice worker separately using
the existing Day 1 command.

**Runtime verification is pending.**

## Day 8 — Call Analytics

Day 8 stores real call lifecycle records in SQLite. A successful call means a
requested task was completed by an appropriate tool: a database-backed spending
answer, document processing, trusted financial information, or a human escalation.
A connection, model reply, or long duration alone does not count as success. Calls
ending without a marked task are recorded as `failure/incomplete_task`.

The `calls` table stores anonymous user and session IDs, browser or SIP channel,
language when known, timestamps, calculated duration, outcome, task outcome,
failure type, completion reason, and optional latency. It stores no transcript or
financial content. Failure types include user hangup, incomplete task, tool failure,
API error, no response, connection error, and unknown.

Latency is the interval between the end of user speech and the beginning of
DhanBuddy audio. The analytics module provides an explicit millisecond recording
interface. Until an exact measurement is supplied, latency remains null and is
never invented.

The public `/dashboard` page queries SQLite for call totals, success rate, average
duration, average known latency, escalation count, calls over time, outcomes,
languages, channels, failure types, and sanitized recent history. Filters cover
date range, language, channel, and outcome. Polling refreshes every ten seconds.

`GET /api/health` returns only safe service, database, agent configuration,
LiveKit configuration, timestamp, and last-activity fields. The main interface
shows them in a small floating monitor. No keys, transcripts, OCR text, escalation
summaries, account data, or transaction details are exposed.

All analytics come from persisted records. An empty database displays zero; no
demonstration calls are generated automatically.

**Runtime verification is pending.**

## Day 5 — Documents, Financial Tools and Trusted Knowledge

Day 5 adds this local document workflow:

```text
Upload → OCR text → structured extraction → categorization → SQLite
       → user correction → CSV export → spending tools
```

FastAPI accepts JPG, PNG, and WEBP files up to 8 MB. Originals receive unique
names under `backend/data/uploads/original` and are never overwritten. The OCR
interface is provider-independent; the initial provider is local Tesseract through
Pytesseract. Tesseract must be installed separately for real OCR execution.

Documents store merchant, date, total, currency, private raw text, and individual
line items. Unknown fields remain null. Categories use a small deterministic
allowlist with confidence scores. Low-confidence items require user confirmation,
and corrections are persisted with `category_source=user`.

SQLite remains the source of truth for personal financial data. Authenticated-by-
anonymous-cookie endpoints can export normalized transaction CSV, while agent
tools query actual SQLite rows for summaries, top categories, and recent expenses.

Trusted external knowledge is deliberately separate:

```text
Personal spending → SQLite
General education → trusted local RAG documents
Current RBI material → official RBI retrieval tool
```

The RAG foundation ingests reviewed text files, chunks them, creates lightweight
local token-vector representations, and retrieves relevant chunks with source
metadata. It is **LOCAL**, not a live vector service. The RBI tool is **LIVE** and
records its retrieval timestamp. If it cannot reach the official source, the agent
is instructed not to guess.

**Runtime verification is pending.** No receipt samples were available in this
checkout, and neither Tesseract nor the complete project environment was verified.

## Day 6 — Outbound Calls

Day 6 adds a modular, consent-controlled outbound path:

```text
DhanBuddy → outbound service → Twilio or Linphone-backed LiveKit SIP trunk
           → existing LiveKit agent → Murf Falcon
```

The Twilio and Linphone adapters share one LiveKit SIP implementation and one
DhanBuddy agent. Provider-specific configuration remains separate. Calls require
an E.164 recipient, an allowlisted purpose, an anonymous user ID, and explicit
opt-in. Arbitrary purpose text cannot become a telephony command.

Required common settings:

```text
TELEPHONY_PROVIDER=twilio  # or linphone
LIVEKIT_SIP_OUTBOUND_TRUNK_ID
AGENT_NAME=dhanbuddy
```

For a Twilio-backed trunk, configure these names while provisioning the trunk:

```text
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
TWILIO_PHONE_NUMBER
```

For the Linphone fallback, create and verify a compatible SIP account/trunk, then
set `TELEPHONY_PROVIDER=linphone` and its stored LiveKit outbound trunk ID. Linphone
support is configuration-ready but has not been tested.

Place one explicitly consented test call using only a controlled number:

```powershell
cd backend
uv run python -m telephony.cli --recipient +919876543210 `
  --purpose financial_check_in --user-id caller-example --confirmed-opt-in
```

The opening identifies DhanBuddy, explains the requested purpose, and says the
recipient may end the call. “Stop calling me” persists an opt-out and ends without
persuasion. Outcomes are limited to answered, busy, no-answer, failed, and user
hangup. This is operational status only, not a Day 8 analytics system. Failures
never produce a fabricated success response and logs exclude credentials.

**Real outbound calling is runtime verification pending.**

## Day 7 — Human Escalation

Day 7 adds a permission-gated support workflow:

```text
Suspected fraud or financial dispute → explain human-review need → ask permission
→ sanitize a short summary → SQLite escalation → reference ID → internal review
```

Ordinary spending, category, savings, and financial-education questions do not
trigger escalation. Potentially unauthorized transactions receive high urgency;
general disputes receive medium urgency. Low and emergency values are supported by
the schema but are not assigned automatically without a genuine reason.

The escalation tool accepts only the anonymous user ID, issue classification,
short summary, what happened, what DhanBuddy checked, urgency, language, preferred
follow-up method, and the user's exact consent response. It refuses a no, unclear
answer, or silence. It stores no full transcript.

Before storage, a defensive sanitizer masks obvious OTP, PIN, CVV, password,
credential, card-security, and long account-number patterns. Regex redaction is a
secondary safeguard; DhanBuddy is still instructed never to request these values.

Each successful request receives a user-facing `DHN-YYYYMMDD-XXXX` reference.
Repeated open or in-progress requests for the same user and issue reuse the existing
reference. Status values are `open`, `in_progress`, `resolved`, and `cancelled`.
The voice agent reports only the status stored in SQLite.

The minimal internal view is available at `/internal/support`. Escalation data is
loaded only after the operator supplies `SUPPORT_VIEW_TOKEN`; the data endpoint
requires it in the `X-Support-Token` header. The view exposes only reference,
issue, urgency, sanitized summary, status, and creation time.

**Runtime verification is pending.**

## Day 4 — Persistent Memory

Day 4 adds consent-controlled memory at `backend/data/dhanbuddy.db`. SQLite is the
source of truth, and the voice agent accesses it only through `lookup_user`,
`save_user_memory`, and `forget_me` tools. Database contents are never inserted
into the system prompt.

The database stores an anonymous user ID, optional name and language preference,
a small allowlist of useful facts, consent state, timestamps, and short interaction
summaries. It does not store full transcripts or financial credentials. Every new
fact requires an explicit yes before the save branch can run. “Forget me” deletes
only that anonymous user's rows after confirmation.

LangGraph coordinates the memory decision instead of replacing the voice agent:

```text
SQLite
  ↓
Memory tools
  ↓
LangGraph state and conditional consent branch
  ↓
LiveKit voice agent
```

The graph supports lookup, consent request, save, discard, and forget nodes. The
Day 3 token endpoint retains a random anonymous caller ID in an HTTP-only cookie,
allowing the same browser to be recognized without collecting a phone number or
financial identifier. SQLite operations run in a worker thread so they do not
unnecessarily block the real-time agent event loop.

LiveKit remains responsible for real-time audio, Deepgram for speech recognition,
Gemini for language understanding, and Murf Falcon for speech output.

**Runtime verification is pending.**

## Day 9 — Specialist Agent and Orchestrator

DhanBuddy now uses a small, explicit router for government-scheme questions:

```text
DhanBuddy Main Agent
        |
        v
Lightweight intent router
        |
        +-- spending, transactions, documents, memory, education --> Main Agent
        |
        +-- scheme eligibility, benefits, documents, requirements
                              |
                              v
                 Government Scheme Specialist
```

The specialist exists to keep government-scheme answers inside a narrow trusted-
source and safety boundary. The main agent announces the handoff only for an
explicit scheme question. It passes the anonymous `user_id`, language, current
question, and a small allowlist of relevant context (`scheme_name`, `state`,
`age_band`, and `occupation`). It never passes a transcript, OTP, PIN, CVV,
password, banking credentials, or card-security information.

The specialist uses the existing Day 5 trusted-knowledge retrieval layer, keeps
source and document dates, and adds the UTC retrieval time. It does not mix
personal SQLite transaction records into scheme retrieval. When a reliable
official source is unavailable, it says so instead of guessing. It never
guarantees eligibility or approval, claims submission, or invents requirements,
deadlines, or benefit amounts.

If specialist creation fails, DhanBuddy reports the failure and remains available
for general financial information. A topic change can be handed back to the main
agent. Questions requiring human eligibility judgment reuse the Day 7 escalation
table and consent flow. The Day 8 `calls` table records `agent_role`,
`handoff_requested`, `handoff_success`, and `handoff_failure`; no second analytics
database is created.

Credential-free Day 9 tests cover routing, context continuity, announcements,
introduction, redaction, guardrails, failure behavior, language, escalation, and
analytics. Real LiveKit, microphone, and Murf voice handoff remain unverified.

## Requirements

- Python 3.10+
- `uv`
- Node.js 18+
- `pnpm`
- A LiveKit Cloud project
- Murf, Deepgram, and Google API credentials

Required environment variable names:

```text
LIVEKIT_URL
LIVEKIT_API_KEY
LIVEKIT_API_SECRET
MURF_API_KEY
DEEPGRAM_API_KEY
GOOGLE_API_KEY
AGENT_NAME
```

Copy `backend/.env.example` to `backend/.env.local` and
`frontend/.env.example` to `frontend/.env.local`. Put the matching LiveKit
values in both files and keep `AGENT_NAME=dhanbuddy`. Never commit either local
environment file.

## Start the backend

```powershell
cd backend
uv sync
uv run python src/agent.py download-files
uv run python src/agent.py dev
```

## Start the frontend

In a second terminal:

```powershell
cd frontend
pnpm install
pnpm dev
```

Open `http://localhost:3000`, connect, allow microphone access, and confirm that
the greeting is audible.

## Voice test

Try these in order:

1. English: `Hello DhanBuddy. Can you hear me?`
2. Hindi: `नमस्ते धनबडी, क्या आप मेरी आवाज़ सुन सकते हैं?`
3. Code-mixed: `DhanBuddy, kya aap mujhe sun sakte hain?`
4. End the session using the frontend disconnect control.

A test is successful only when the browser transcript reaches the agent and the
Murf-generated reply is audible. Automated checks alone do not verify microphone,
LiveKit Cloud, or speaker output.

## Automated checks

```powershell
cd backend
uv run pytest
uv run ruff check .

cd ../frontend
pnpm lint
pnpm format:check
pnpm build
```

## References

- [Murf Falcon streaming documentation](https://murf.ai/api/docs/text-to-speech/streaming)
- [Murf Falcon voice library](https://murf.ai/api/docs/voices-styles/voice-library)
- [LiveKit Agents documentation](https://docs.livekit.io/agents)
- [Deepgram models and languages](https://developers.deepgram.com/docs/models-languages-overview/)

## License

MIT
