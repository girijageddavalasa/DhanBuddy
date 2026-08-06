import logging
from dataclasses import asdict, dataclass

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    function_tool,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
SYSTEM_PROMPT = """You are DhanBuddy, a friendly Indian voice assistant whose only task is goal-based savings planning.

Start by asking what the user is saving for. Then collect these details, asking exactly one question per response and in this order:
1. Target amount.
2. Deadline.
3. Amount already saved.
4. Amount they can save every month.

Accept natural Indian number formats such as 50,000 rupees, 5 lakhs, and 1 crore. Once all four details are known, work out the whole number of months from today to the deadline and call calculate_savings_plan. Use the tool result for every number; never invent or mentally recalculate the figures.

Tell the user how much they may accumulate by the deadline, whether they are on track, the approximate monthly shortfall or surplus, and one practical next step such as increasing monthly savings or extending the deadline. Explain that it is an educational estimate without investment returns and is not personalized financial advice.

Speak in short, natural sentences suitable for voice. Use Indian currency terms such as rupees, lakhs, and crores. Do not use markdown, bullet points, emojis, or complex formatting. Do not recommend specific stocks, mutual funds, insurance plans, banks, cryptocurrencies, or financial products. Do not promise returns. Never request an OTP, PIN, CVV, password, account number, Aadhaar number, or card details. If asked about anything outside goal-based savings planning, politely say you can only help with a savings goal and return to the next unanswered question."""


@dataclass(frozen=True)
class SavingsPlan:
    projected_amount: float
    required_monthly_saving: float
    monthly_difference: float
    on_track: bool


def calculate_plan(
    target_amount: float,
    months: int,
    already_saved: float,
    monthly_saving: float,
) -> SavingsPlan:
    """Calculate a zero-return savings estimate."""
    if target_amount <= 0:
        raise ValueError("Target amount must be greater than zero.")
    if months <= 0:
        raise ValueError("Deadline must be at least one month away.")
    if already_saved < 0 or monthly_saving < 0:
        raise ValueError("Savings amounts cannot be negative.")

    projected_amount = already_saved + monthly_saving * months
    required_monthly = max(target_amount - already_saved, 0) / months
    return SavingsPlan(
        projected_amount=round(projected_amount, 2),
        required_monthly_saving=round(required_monthly, 2),
        monthly_difference=round(monthly_saving - required_monthly, 2),
        on_track=projected_amount >= target_amount,
    )


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    @function_tool
    async def calculate_savings_plan(
        self,
        target_amount: float,
        months: int,
        already_saved: float,
        monthly_saving: float,
    ) -> dict[str, float | bool]:
        """Calculate a savings goal estimate without investment returns.

        Args:
            target_amount: Goal amount in rupees.
            months: Whole number of months remaining until the deadline.
            already_saved: Amount already saved in rupees.
            monthly_saving: Amount the user can save each month in rupees.
        """
        plan = calculate_plan(target_amount, months, already_saved, monthly_saving)
        logger.info("Calculated savings plan: %s", plan)
        return asdict(plan)


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="dhanbuddy")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
            voice="Anisha",
            locale="en-IN",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()

    await session.generate_reply(
        instructions=(
            "Say exactly: Hello! I\u2019m DhanBuddy. Tell me one financial goal you "
            "would like to achieve. Do not add anything else."
        )
    )


if __name__ == "__main__":
    cli.run_app(server)

