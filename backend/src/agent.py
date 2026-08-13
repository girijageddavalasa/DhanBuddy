import asyncio

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    UserStateChangedEvent,
    cli,
    function_tool,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from prompt import (
    FIRST_TURN_GREETING,
    SILENCE_CLOSE,
    SILENCE_REPROMPT,
    SYSTEM_PROMPT,
)
from memory_workflow import run_memory_workflow
from finance_data import recent_transactions, spending_summary
from official_info import fetch_rbi_financial_education
from trusted_knowledge import retrieve

load_dotenv(".env.local")


EXPLICIT_CONSENT = {"yes", "yes please", "sure", "okay", "हाँ", "हां", "जी हाँ"}


def has_explicit_consent(reply: str) -> bool:
    return reply.casefold().strip(" .,!?") in EXPLICIT_CONSENT


class Assistant(Agent):
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        super().__init__(instructions=SYSTEM_PROMPT)

    @function_tool
    async def lookup_user(self) -> dict[str, object]:
        """Look up consented memory for the current anonymous browser user."""
        return await asyncio.to_thread(
            run_memory_workflow, {"user_id": self.user_id, "action": "lookup"}
        )

    @function_tool
    async def save_user_memory(
        self, key: str, value: str, consent_confirmation: str
    ) -> dict[str, object]:
        """Save one allowed fact only after explicit consent.

        Args:
            key: Allowed fact type, such as name or preferred_language.
            value: The useful, non-sensitive value to remember.
            consent_confirmation: The user's exact latest consent reply.
        """
        consent = has_explicit_consent(consent_confirmation)
        return await asyncio.to_thread(
            run_memory_workflow,
            {
                "user_id": self.user_id,
                "action": "save",
                "new_fact_key": key,
                "new_fact_value": value,
                "memory_consent": consent,
            },
        )

    @function_tool
    async def forget_me(self, confirmation: str) -> dict[str, object]:
        """Delete this user's memory after explicit confirmation.

        Args:
            confirmation: The user's exact latest deletion confirmation.
        """
        if not has_explicit_consent(confirmation):
            return {"operation_succeeded": False, "response_context": "Deletion was not confirmed."}
        return await asyncio.to_thread(
            run_memory_workflow, {"user_id": self.user_id, "action": "forget"}
        )

    @function_tool
    async def get_spending_summary(self) -> dict[str, object]:
        """Use for totals, category spending, and where this user spent most."""
        result = await asyncio.to_thread(spending_summary, self.user_id)
        if not result["categories"]:
            return {"available": False, "message": "I don't have enough recorded transactions to calculate that yet."}
        return {"available": True, **result}

    @function_tool
    async def get_top_spending_categories(self) -> dict[str, object]:
        """Use to rank this user's actual recorded spending categories."""
        result = await asyncio.to_thread(spending_summary, self.user_id)
        return {"available": bool(result["categories"]), **result}

    @function_tool
    async def get_recent_transactions(self, limit: int = 5) -> dict[str, object]:
        """Use when the user asks for recent or latest recorded expenses."""
        rows = await asyncio.to_thread(recent_transactions, self.user_id, limit)
        return {"available": bool(rows), "transactions": rows}

    @function_tool
    async def search_trusted_knowledge(self, question: str) -> dict[str, object]:
        """Use for general financial education, never for personal spending."""
        chunks = await asyncio.to_thread(retrieve, question)
        if not chunks:
            return {"available": False, "message": "I don't have a reliable source for that."}
        return {"available": True, "sources": [{"text": c.text, "source": c.source, "source_date": c.source_date} for c in chunks]}

    @function_tool
    async def get_official_rbi_information(self) -> dict[str, object]:
        """Use when current official RBI financial-education information is requested."""
        return await fetch_rbi_financial_education()


server = AgentServer()


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


def setup_inactivity_handler(session: AgentSession) -> None:
    """Reprompt once, then close after a second period of silence."""
    inactivity_task: asyncio.Task[None] | None = None

    async def handle_silence() -> None:
        await session.say(SILENCE_REPROMPT, allow_interruptions=True)
        await asyncio.sleep(10)
        await session.say(SILENCE_CLOSE, allow_interruptions=False)
        session.shutdown(drain=True)

    @session.on("user_state_changed")
    def on_user_state_changed(event: UserStateChangedEvent) -> None:
        nonlocal inactivity_task
        if event.new_state == "away":
            if inactivity_task is None or inactivity_task.done():
                inactivity_task = asyncio.create_task(handle_silence())
            return

        if inactivity_task is not None:
            inactivity_task.cancel()
            inactivity_task = None


@server.rtc_session(agent_name="dhanbuddy")
async def my_agent(ctx: JobContext) -> None:
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(model="gemini-3.5-flash-lite"),
        tts=murf.TTS(
            voice="Abhinav",
            style="Conversational",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
        user_away_timeout=8.0,
    )
    setup_inactivity_handler(session)

    await ctx.connect()
    participant = await ctx.wait_for_participant()

    await session.start(
        agent=Assistant(participant.identity),
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

    await session.generate_reply(
        instructions=(
            "Call lookup_user now. If stored memory exists, greet the returning user "
            "using only that result. Otherwise say exactly: " + FIRST_TURN_GREETING
        )
    )


if __name__ == "__main__":
    cli.run_app(server)
