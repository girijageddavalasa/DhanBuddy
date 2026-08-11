"""CLI that dispatches DhanBuddy and places one consented outbound SIP call."""

import argparse
import asyncio
import contextlib
import json
import os
import sys
import uuid
from dataclasses import dataclass

from dotenv import load_dotenv
from livekit import api
from livekit.protocol.agent_dispatch import CreateAgentDispatchRequest
from livekit.protocol.room import CreateRoomRequest, DeleteRoomRequest
from livekit.protocol.sip import CreateSIPParticipantRequest

from outbound.call_logic import classify_call_failure, retry_rule, validate_e164
from outbound.preferences import is_opted_out


@dataclass(frozen=True)
class OutboundConfig:
    phone_number: str
    caller_id: str
    caller_name: str
    goal: str
    deadline: str
    trunk_id: str
    agent_name: str


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} is required in backend/.env.local")
    return value


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Place one DhanBuddy savings check-in call."
    )
    parser.add_argument(
        "--to", required=True, help="Your controlled number in E.164 format."
    )
    parser.add_argument(
        "--caller-id",
        required=True,
        help="Anonymous caller ID; never a phone or Aadhaar number.",
    )
    parser.add_argument(
        "--name", required=True, help="Preferred name used only for verification."
    )
    parser.add_argument("--goal", required=True, help="Consented savings-goal label.")
    parser.add_argument(
        "--deadline", required=True, help="Consented goal deadline description."
    )
    parser.add_argument(
        "--confirmed-opt-in",
        action="store_true",
        help="Required confirmation that this person requested the check-in call.",
    )
    return parser.parse_args(argv)


def build_config(args: argparse.Namespace) -> OutboundConfig:
    if not args.confirmed_opt_in:
        raise ValueError("Outbound calls require --confirmed-opt-in.")
    caller_id = args.caller_id.strip()
    if not caller_id or len(caller_id) > 100:
        raise ValueError("Provide a short anonymous caller ID.")
    if is_opted_out(caller_id):
        raise ValueError("This caller opted out. No call was placed.")
    return OutboundConfig(
        phone_number=validate_e164(args.to),
        caller_id=caller_id,
        caller_name=args.name.strip(),
        goal=args.goal.strip(),
        deadline=args.deadline.strip(),
        trunk_id=_required_env("LIVEKIT_SIP_OUTBOUND_TRUNK_ID"),
        agent_name=os.getenv("AGENT_NAME", "dhanbuddy").strip() or "dhanbuddy",
    )


async def place_call(config: OutboundConfig) -> int:
    room_name = f"dhanbuddy-outbound-{uuid.uuid4().hex[:10]}"
    sip_identity = f"outbound-{uuid.uuid4().hex[:10]}"
    metadata = {
        "call_type": "outbound_goal_checkin",
        "caller_id": config.caller_id,
        "caller_name": config.caller_name,
        "goal": config.goal,
        "deadline": config.deadline,
        "sip_identity": sip_identity,
    }
    client = api.LiveKitAPI()
    answered = False
    try:
        await client.room.create_room(
            CreateRoomRequest(name=room_name, empty_timeout=120)
        )
        await client.agent_dispatch.create_dispatch(
            CreateAgentDispatchRequest(
                agent_name=config.agent_name,
                room=room_name,
                metadata=json.dumps(metadata),
            )
        )
        print("OUTBOUND | dispatch created; dialing the consented number")
        request = CreateSIPParticipantRequest(
            sip_trunk_id=config.trunk_id,
            sip_call_to=config.phone_number,
            room_name=room_name,
            participant_identity=sip_identity,
            participant_name="DhanBuddy caller",
            participant_metadata=json.dumps(metadata),
            display_name="DhanBuddy",
            wait_until_answered=True,
        )
        await client.sip.create_sip_participant(request)
        answered = True
        print("OUTBOUND RESULT | answered")
        print(f"RETRY RULE | {retry_rule('answered')}")
        return 0
    except api.TwirpError as error:
        detail = f"{error.code} {error.message} {error.status} {error.metadata}"
        outcome = classify_call_failure(detail)
        print(f"OUTBOUND RESULT | {outcome}", file=sys.stderr)
        print(f"RETRY RULE | {retry_rule(outcome)}", file=sys.stderr)
        return 2
    finally:
        if not answered:
            with contextlib.suppress(Exception):
                await client.room.delete_room(DeleteRoomRequest(room=room_name))
        await client.aclose()


async def main(argv: list[str] | None = None) -> int:
    load_dotenv(".env.local")
    try:
        config = build_config(parse_args(argv))
    except ValueError as error:
        print(f"OUTBOUND BLOCKED | {error}", file=sys.stderr)
        return 2
    return await place_call(config)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
