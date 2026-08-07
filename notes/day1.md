Here is the complete explanation of what we built and why each API key is required.

## What is DhanBuddy?

DhanBuddy is a voice-based savings planner under the **Financial Services** track.

It helps a user answer one question:

> “If I continue saving this amount every month, can I reach my financial goal before my deadline?”

It collects:

1. What the user is saving for
2. Target amount
3. Deadline
4. Amount already saved
5. Monthly saving capacity

It then calculates:

- Expected amount by the deadline
- Whether the user is on track
- Required monthly savings
- Monthly shortfall or surplus
- One practical next step

It does not calculate investment returns and does not recommend financial products.

---

## Complete voice flow

When you speak, this happens:

```text
Your microphone
      ↓
LiveKit sends the audio
      ↓
Deepgram converts speech into text
      ↓
Google Gemini understands the text
      ↓
DhanBuddy collects the required information
      ↓
Our Python calculator calculates the savings result
      ↓
Gemini creates a short response
      ↓
Murf Falcon converts the text into an Indian voice
      ↓
LiveKit sends the voice back to your browser
      ↓
You hear DhanBuddy
```

Each service performs a different job.

---

## 1. LiveKit: communication system

Environment variables:

```dotenv
LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
```

LiveKit connects:

- Your browser
- Your microphone
- The Python backend agent
- DhanBuddy’s generated audio

You can think of LiveKit as the telephone line or meeting room.

### What each LiveKit value does

`LIVEKIT_URL` identifies your LiveKit Cloud project.

Example:

```dotenv
LIVEKIT_URL=wss://dhanbuddy-example.livekit.cloud
```

`LIVEKIT_API_KEY` identifies your application.

`LIVEKIT_API_SECRET` proves that the application is authorized to create rooms and connection tokens.

The frontend creates a temporary participant token. That token allows the browser to:

- Join a LiveKit room
- Publish microphone audio
- Receive DhanBuddy’s audio
- Exchange text data

The token currently expires after 15 minutes.

### Why LiveKit values are used twice

The same LiveKit credentials are kept in:

```text
backend/.env.local
frontend/.env.local
```

The frontend uses them to create a temporary browser connection token.

The backend uses them to register the DhanBuddy agent and join the same LiveKit project.

Both must point to the same project.

---

## 2. Deepgram: DhanBuddy’s ears

Environment variable:

```dotenv
DEEPGRAM_API_KEY=
```

Deepgram performs Speech-to-Text, also called STT.

For example, you say:

> “My target is ten lakh rupees.”

Deepgram converts that audio into text:

```text
My target is 10 lakh rupees.
```

That text is sent to Gemini.

We configured:

```python
deepgram.STT(model="nova-3")
```

Therefore:

```text
Deepgram = ears
```

Without a valid Deepgram key, DhanBuddy may connect but cannot understand what you say.

---

## 3. Google Gemini: DhanBuddy’s brain

Environment variable:

```dotenv
GOOGLE_API_KEY=
```

Gemini is the Large Language Model, or LLM.

It understands the conversation and decides:

- Which question should be asked next
- Whether the user has provided the target
- Whether the user has provided a deadline
- Whether all information is available
- When to call the savings calculator
- How to explain the result naturally

We configured:

```python
google.LLM(model="gemini-3.5-flash-lite")
```

For example:

```text
User: I want to save for my master’s degree.
```

Gemini understands that the goal is a master’s degree. It then asks:

```text
What is your target amount?
```

Therefore:

```text
Gemini = brain
```

Without the Google key, DhanBuddy cannot decide what to ask or produce an answer.

An OpenAI key is not currently required because this project uses Gemini.

---

## 4. Murf Falcon: DhanBuddy’s voice

Environment variable:

```dotenv
MURF_API_KEY=
```

Murf performs Text-to-Speech, also called TTS.

For example, Gemini produces this text:

```text
What is your target amount?
```

Murf Falcon converts it into spoken audio.

We configured:

```python
murf.TTS(
    voice="Anisha",
    locale="en-IN",
    style="Conversation",
)
```

This means:

- Voice: Anisha
- Language and accent: Indian English
- Style: Natural conversation
- TTS engine: Murf Falcon

Therefore:

```text
Murf Falcon = voice
```

This is the hard requirement for the VoiceForBharat challenge.

Without the Murf key, DhanBuddy may understand you and generate text, but it cannot speak.

---

## 5. Silero: detecting when you speak

Silero Voice Activity Detection is included locally as a package.

It does not require a separate API key.

It detects:

- When you start speaking
- When you stop speaking
- Which parts of the microphone audio contain speech
- Which parts are silence or background noise

We load it before starting the agent:

```python
silero.VAD.load()
```

Therefore:

```text
Silero VAD = detects voice and silence
```

---

## 6. Multilingual turn detector

The LiveKit multilingual turn detector helps determine when the user has finished their sentence.

For example, if you say:

> “I want to save… for my master’s degree.”

It tries not to interrupt during the short pause.

It also does not require your own separate API key.

---

## 7. Noise cancellation

The project includes LiveKit noise cancellation.

It helps reduce:

- Fan noise
- Room noise
- Background sounds
- Some microphone interference

It improves the audio before Deepgram processes it.

---

## What `AGENT_NAME=dhanbuddy` means

The backend registers the agent using:

```python
@server.rtc_session(agent_name="dhanbuddy")
```

The frontend dispatches:

```dotenv
AGENT_NAME=dhanbuddy
```

These names must match.

When you click **Talk to DhanBuddy**, the frontend tells LiveKit:

> “Please send the agent named `dhanbuddy` into this room.”

Earlier, this value was empty, so the frontend could create a room without explicitly requesting DhanBuddy. We corrected it and added a fallback in the code.

---

## What the savings calculator does

The important calculations are performed by our Python function, not guessed by Gemini.

### Projected savings

```text
Already saved + (monthly saving × remaining months)
```

### Required monthly savings

```text
(Target amount − already saved) ÷ remaining months
```

### Monthly difference

```text
Current monthly saving − required monthly saving
```

A positive difference means a surplus.

A negative difference means a shortfall.

### Example

The user provides:

```text
Target: ₹10 lakhs
Deadline: 3 years or 36 months
Already saved: ₹1 lakh
Monthly saving: ₹20,000
```

Projected amount:

```text
₹1,00,000 + (₹20,000 × 36)
= ₹8,20,000
```

Required monthly saving:

```text
(₹10,00,000 − ₹1,00,000) ÷ 36
= ₹25,000
```

Monthly difference:

```text
₹20,000 − ₹25,000
= −₹5,000
```

Result:

- Projected amount: ₹8.2 lakhs
- Target: ₹10 lakhs
- Status: Not on track
- Monthly shortfall: ₹5,000
- Next step: Increase savings by approximately ₹5,000 monthly or extend the deadline

The calculation assumes zero investment returns.

---

## What the system prompt controls

The `SYSTEM_PROMPT` in [agent.py](C:/DLGM/DhanBuddy/backend/src/agent.py) defines DhanBuddy’s rules.

It tells DhanBuddy to:

- Work only on savings goals
- Ask one question at a time
- Follow the correct question order
- Use lakhs, crores, and rupees
- Keep responses short for voice
- Use the Python calculator
- Provide an educational disclaimer
- Avoid financial-product recommendations
- Avoid promising returns
- Never request sensitive information

Sensitive information DhanBuddy must never request includes:

- OTP
- PIN
- CVV
- Password
- Bank account number
- Aadhaar number
- Card details

---

## What the frontend does

The frontend is the website you open at:

```text
http://localhost:3000
```

It provides:

- Talk to DhanBuddy button
- Microphone permission
- Audio visualizer
- Text conversation
- Connection and disconnect controls
- DhanBuddy branding

The configuration is in [app-config.ts](C:/DLGM/DhanBuddy/frontend/app-config.ts).

We changed:

- Company name to DhanBuddy
- Page title to DhanBuddy Voice Savings Planner
- Button text to Talk to DhanBuddy
- Theme colour to green
- Video input off
- Screen sharing off
- Agent name to `dhanbuddy`

Video and screen sharing are unnecessary because this is a voice savings assistant.

---

## What the token API does

The frontend token endpoint is in [route.ts](C:/DLGM/DhanBuddy/frontend/app/api/token/route.ts).

When you click the button, this endpoint:

1. Creates a random room name
2. Creates a random user identity
3. Generates a temporary 15-minute LiveKit token
4. Gives microphone publishing permission
5. Gives audio subscription permission
6. Requests the `dhanbuddy` agent
7. Returns the connection details to the browser

The browser does not directly expose the LiveKit API secret to the user.

---

## Where the keys are stored

Backend keys:

```text
C:\DLGM\DhanBuddy\backend\.env.local
```

Frontend LiveKit configuration:

```text
C:\DLGM\DhanBuddy\frontend\.env.local
```

These files are ignored by Git through `.gitignore`.

Therefore, they should not be uploaded to GitHub.

Never show the contents of these files in your video.

---

## What happens when you start the backend

This command:

```powershell
uv run python src\agent.py dev
```

Does the following:

1. Loads `backend/.env.local`
2. Loads the Silero speech detector
3. Connects the agent worker to LiveKit
4. Registers the name `dhanbuddy`
5. Waits for a user to create a room
6. Starts Deepgram, Gemini, and Murf when a session begins

Keep this terminal running.

---

## What happens when you start the frontend

This command:

```powershell
npm run dev
```

Does the following:

1. Starts the Next.js website
2. Loads `frontend/.env.local`
3. Makes the website available at port 3000
4. Waits for you to click Talk to DhanBuddy
5. Creates a LiveKit room and dispatches the backend agent

Keep this terminal running too.

---

## Simple one-line explanation for your video

> “DhanBuddy uses LiveKit for real-time audio communication, Deepgram to understand my speech, Gemini to manage the conversation, a Python calculator to check my savings goal, and Murf Falcon—the fastest text-to-speech API—to respond in a natural Indian English voice.”

That sentence explains the entire project clearly.