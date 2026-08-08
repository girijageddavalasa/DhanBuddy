# Day 3 — Personalised DhanBuddy Frontend

## Goal

Day 3 focused on what the user sees and uses during a voice call. The LiveKit starter interface was redesigned into a unique Financial Services experience for DhanBuddy.

## What was built

### 1. Unique DhanBuddy identity

- Created a custom DhanBuddy logo using a speech bubble, rupee symbol, and voice-wave styling.
- Used a distinctive yellow, purple, violet, and magenta colour palette.
- Replaced the generic centred waveform layout with an asymmetric savings-planning workspace.
- Added the tagline: **Your dream, mapped in rupees.**

### 2. Five clear agent states

The frontend clearly communicates the current call state:

1. **Ready** — shows one clear **Start talking** button.
2. **Connecting** — asks the user to wait while DhanBuddy joins the call.
3. **Listening** — displays **Listening to you** and highlights the user indicator.
4. **Speaking** — displays **DhanBuddy is speaking** and highlights the agent indicator.
5. **Call ended** — confirms that the conversation is over and displays **Start again**.

### 3. Savings journey interface

The live-call screen now follows DhanBuddy's actual conversation flow:

`Goal → Target → Timeline → Savings → Estimate`

The journey rail progresses as messages are exchanged. It makes the voice conversation feel like a guided savings-planning session instead of a generic call.

### 4. Flowing live transcript

- The transcript is the main conversation canvas rather than a small optional panel.
- User and DhanBuddy responses appear as readable conversation text.
- A transcript privacy control allows the user to hide or show the conversation.
- Separate speaker indicators make it clear whether the user or DhanBuddy is speaking.

### 5. Voice visualisation

- Added an animated rupee voice orbit instead of the starter's plain centred animation.
- The voice visualiser responds during listening and speaking.
- The interface includes clear text labels so it remains understandable without relying only on animation.

### 6. Call controls

- Moved the prominent **End Session** button to the top header.
- Kept microphone and transcript controls in a compact conversation dock.
- Added automatic call ending when the user says phrases such as **bye**, **goodbye**, or **end call**.
- After the call ends, the user can start a new session.

### 7. Microphone permission handling

Before connecting, the frontend requests microphone access. If permission is blocked, it explains:

- why DhanBuddy cannot hear the user,
- how to use the lock or microphone icon in the browser address bar,
- how to allow microphone access and try again.

### 8. Privacy and safety reminders

The live interface reminds users never to share:

- OTP or PIN,
- passwords,
- account numbers,
- Aadhaar numbers,
- card details.

It also states that DhanBuddy provides an educational estimate, assumes no investment returns, and does not provide personalized financial advice.

### 9. Realtime voice pipeline

The interface explains the voice flow in simple language:

`User speaks → Deepgram STT → Gemini LLM → Murf Falcon streaming TTS → User hears DhanBuddy`

- **Deepgram** converts speech into text.
- **Gemini** understands the request and prepares the response.
- **Murf Falcon** produces the Indian voice using streaming text-to-speech.
- **LiveKit** manages the realtime audio session and agent connection.
- **Next.js** provides the frontend and LiveKit token route.

FastAPI is not currently used. The Python backend runs with LiveKit's `AgentServer`. FastAPI can be added later if DhanBuddy needs custom REST APIs, saved plans, user history, or analytics.

## Extra features

- Responsive desktop and mobile layouts.
- Dark-mode-compatible styling.
- Visible streaming voice-pipeline explanation.
- Four-step savings prompts on the welcome screen.
- Privacy-controlled transcript.
- Educational-estimate disclaimer.
- Camera-ready Day 3 demo guide in `DAY3_DEMO.md`.

## Testing completed

- Prettier formatting passed.
- TypeScript type checking passed.
- Frontend lint passed with only existing starter warnings.
- Next.js production build passed.
- Backend Ruff checks passed.
- All 16 backend tests passed.

## Day 3 demo flow

1. Open DhanBuddy and show the **Ready** state.
2. Select **Start talking** and show **Connecting**.
3. Say: “I want to save for my college fees.”
4. Continue with the target, deadline, current savings, and monthly savings.
5. Show the **Listening** and **Speaking** indicators and flowing transcript.
6. Show the savings journey progressing.
7. Say **bye** and show that the call ends.
8. Show the **Call ended** screen and **Start again** button.

## Outcome

DhanBuddy now has a purpose-built Financial Services frontend rather than the standard LiveKit starter appearance. The interface visually explains the savings-planning journey, clearly communicates every agent state, handles microphone problems, and provides a distinctive realtime voice experience.
