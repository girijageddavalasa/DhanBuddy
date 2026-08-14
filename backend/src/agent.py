import asyncio
import json

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    ConversationItemAddedEvent,
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
from telephony.preferences import record_opt_out
from escalation import create_escalation, get_escalation_status
from analytics import (
    CallTracker,
    record_agent_role,
    record_call_language,
    record_call_start,
    record_handoff,
)
from orchestrator import (
    HANDOFF_FAILURE_MESSAGE,
    SPECIALIST_INTRODUCTION,
    build_handoff_context,
    route_request,
)
from scheme_specialist import SPECIALIST_PROMPT, trusted_scheme_search

load_dotenv(".env.local")


EXPLICIT_CONSENT = {"yes", "yes please", "sure", "okay", "हाँ", "हां", "जी हाँ"}


def has_explicit_consent(reply: str) -> bool:
    return reply.casefold().strip(" .,!?") in EXPLICIT_CONSENT


class Assistant(Agent):
    def __init__(self, user_id: str, call_tracker: CallTracker) -> None:
        self.user_id = user_id
        self.call_tracker = call_tracker
        super().__init__(instructions=SYSTEM_PROMPT)

    @function_tool
    async def record_conversation_language(self, language: str) -> dict[str, object]:
        """Record the user's apparent conversation language once when known."""
        updated = await asyncio.to_thread(
            record_call_language, self.call_tracker.call_id, language
        )
        return {"recorded": updated}

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
        self.call_tracker.mark_success("spending_summary", "Database-backed spending answer returned.")
        return {"available": True, **result}

    @function_tool
    async def get_top_spending_categories(self) -> dict[str, object]:
        """Use to rank this user's actual recorded spending categories."""
        result = await asyncio.to_thread(spending_summary, self.user_id)
        if result["categories"]:
            self.call_tracker.mark_success("spending_summary", "Database-backed category ranking returned.")
        return {"available": bool(result["categories"]), **result}

    @function_tool
    async def get_recent_transactions(self, limit: int = 5) -> dict[str, object]:
        """Use when the user asks for recent or latest recorded expenses."""
        rows = await asyncio.to_thread(recent_transactions, self.user_id, limit)
        if rows:
            self.call_tracker.mark_success("spending_summary", "Database-backed recent transactions returned.")
        return {"available": bool(rows), "transactions": rows}

    @function_tool
    async def search_trusted_knowledge(self, question: str) -> dict[str, object]:
        """Use for general financial education, never for personal spending."""
        chunks = await asyncio.to_thread(retrieve, question)
        if not chunks:
            return {"available": False, "message": "I don't have a reliable source for that."}
        self.call_tracker.mark_success("financial_information", "Trusted local knowledge returned.")
        return {"available": True, "sources": [{"text": c.text, "source": c.source, "source_date": c.source_date} for c in chunks]}

    @function_tool
    async def get_official_rbi_information(self) -> dict[str, object]:
        """Use when current official RBI financial-education information is requested."""
        result = await fetch_rbi_financial_education()
        if result.get("available"):
            self.call_tracker.mark_success("financial_information", "Official RBI information returned.")
        return result

    @function_tool
    async def create_escalation(
        self, issue_type: str, short_summary: str, what_happened: str,
        what_dhanbuddy_checked: str, urgency: str, language: str,
        preferred_follow_up_method: str, consent_confirmation: str,
    ) -> dict[str, object]:
        """Create human support only for suspected fraud or a financial dispute.

        Use only after asking permission and receiving a clear yes. Do not use for
        spending summaries, categories, savings education, or ordinary questions.
        Never include credentials, full account numbers, or a full transcript.
        """
        result = await asyncio.to_thread(
            create_escalation, self.user_id, issue_type, short_summary,
            what_happened, what_dhanbuddy_checked, urgency, language,
            preferred_follow_up_method, consent_confirmation,
        )
        if result.get("created") or result.get("duplicate"):
            self.call_tracker.mark_success("human_escalation", "Human support request recorded.")
        return result

    @function_tool
    async def get_escalation_status(self, reference_id: str) -> dict[str, object]:
        """Get the database-backed status of this user's support reference."""
        result = await asyncio.to_thread(get_escalation_status, self.user_id, reference_id)
        return result or {"found": False}

    @function_tool
    async def handoff_to_scheme_specialist(
        self,
        user_language: str,
        user_question: str,
        relevant_context: str = "{}",
    ) -> Agent | str:
        """Hand off only a specific government-scheme question.

        Args:
            user_language: The user's current language or language register.
            user_question: Only the current scheme question, never a transcript.
            relevant_context: JSON with minimal scheme_name, state, age_band, or occupation context.
        """
        if route_request(user_question) != "scheme_specialist":
            return "This is not a government-scheme question, so DhanBuddy will continue helping directly."
        try:
            await asyncio.to_thread(record_handoff, self.call_tracker.call_id, "requested")
            parsed = json.loads(relevant_context) if relevant_context else {}
            if not isinstance(parsed, dict):
                parsed = {}
            context = build_handoff_context(
                self.user_id, user_language, user_question, parsed
            )
            specialist = GovernmentSchemeSpecialist(context, self.call_tracker)
            await asyncio.to_thread(record_handoff, self.call_tracker.call_id, "success")
            return specialist
        except Exception:
            try:
                await asyncio.to_thread(record_handoff, self.call_tracker.call_id, "failure")
            except Exception:
                pass
            return HANDOFF_FAILURE_MESSAGE


class GovernmentSchemeSpecialist(Agent):
    def __init__(self, context, call_tracker: CallTracker) -> None:
        self.context = context
        self.call_tracker = call_tracker
        instructions = (
            SPECIALIST_PROMPT
            + "\n# CURRENT HANDOFF CONTEXT\n"
            + f"Language: {context.user_language}\n"
            + f"Question: {context.user_question}\n"
            + f"Relevant context: {json.dumps(context.relevant_context, ensure_ascii=False)}"
        )
        super().__init__(instructions=instructions)

    async def on_enter(self) -> None:
        await self.session.say(SPECIALIST_INTRODUCTION, allow_interruptions=True)
        await self.session.generate_reply(
            instructions="Answer the handed-off question now. Do not ask the user to repeat it."
        )

    @function_tool
    async def search_government_scheme_sources(self, question: str) -> dict[str, object]:
        """Search only the existing trusted knowledge layer for scheme information."""
        result = await asyncio.to_thread(trusted_scheme_search, question)
        if result.get("available"):
            self.call_tracker.mark_success(
                "financial_information", "Trusted government-scheme information returned."
            )
        return result

    @function_tool
    async def create_scheme_escalation(
        self,
        short_summary: str,
        what_happened: str,
        what_dhanbuddy_checked: str,
        language: str,
        preferred_follow_up_method: str,
        consent_confirmation: str,
    ) -> dict[str, object]:
        """Use existing human support for eligibility judgment, only with consent."""
        result = await asyncio.to_thread(
            create_escalation,
            self.context.user_id,
            "scheme_eligibility_review",
            short_summary,
            what_happened,
            what_dhanbuddy_checked,
            "low",
            language,
            preferred_follow_up_method,
            consent_confirmation,
        )
        if result.get("created") or result.get("duplicate"):
            self.call_tracker.mark_success("human_escalation", "Scheme question sent to existing human support.")
        return result

    @function_tool
    async def hand_back_to_main(self) -> Agent:
        """Return non-scheme questions to the primary DhanBuddy agent."""
        await asyncio.to_thread(record_agent_role, self.call_tracker.call_id, "main")
        return Assistant(self.context.user_id, self.call_tracker)


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


def setup_outbound_opt_out(session: AgentSession, user_id: str) -> None:
    closing = False
    phrases = {"stop calling me", "stop calling", "do not call again", "don't call again", "opt out"}

    async def close_call() -> None:
        await asyncio.to_thread(record_opt_out, user_id)
        await session.interrupt(force=True)
        await session.say("Understood. I won't continue this call.", allow_interruptions=False)
        session.shutdown(drain=True)

    @session.on("conversation_item_added")
    def on_item(event: ConversationItemAddedEvent) -> None:
        nonlocal closing
        item = event.item
        if item.type != "message" or item.role != "user" or closing:
            return
        if (item.text_content or "").casefold().strip(" .,!?\"") in phrases:
            closing = True
            asyncio.create_task(close_call())


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
    outbound_context = None
    try:
        metadata = json.loads(ctx.job.metadata or "{}")
        if metadata.get("call_type") == "outbound_checkin":
            outbound_context = metadata
            setup_outbound_opt_out(session, str(metadata.get("user_id", "")))
    except (json.JSONDecodeError, TypeError):
        outbound_context = None
    channel = "sip" if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP else "browser"
    call_id = await asyncio.to_thread(
        record_call_start, participant.identity, ctx.room.name, channel
    )
    call_tracker = CallTracker(call_id)

    async def finish_analytics() -> None:
        await asyncio.to_thread(call_tracker.finish)

    ctx.add_shutdown_callback(finish_analytics)

    await session.start(
        agent=Assistant(participant.identity, call_tracker),
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

    if outbound_context:
        await session.say(str(outbound_context["opening"]), allow_interruptions=True)
    else:
        await session.generate_reply(
            instructions=(
                "Call lookup_user now. If stored memory exists, greet the returning user "
                "using only that result. Otherwise say exactly: " + FIRST_TURN_GREETING
            )
        )


if __name__ == "__main__":
    cli.run_app(server)
