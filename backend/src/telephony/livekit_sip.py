import json
import logging
import os
import uuid

from telephony.provider import CallRequest, CallResult, TelephonyProvider

logger = logging.getLogger("dhanbuddy.telephony")


class LiveKitSIPProvider(TelephonyProvider):
    def __init__(self, name: str, trunk_id: str, agent_name: str = "dhanbuddy") -> None:
        self.name = name
        self.trunk_id = trunk_id
        self.agent_name = agent_name

    async def place_call(self, request: CallRequest) -> CallResult:
        from livekit import api
        from livekit.protocol.agent_dispatch import CreateAgentDispatchRequest
        from livekit.protocol.room import CreateRoomRequest
        from livekit.protocol.sip import CreateSIPParticipantRequest

        room_name = f"dhanbuddy-outbound-{uuid.uuid4().hex[:10]}"
        sip_identity = f"outbound-{uuid.uuid4().hex[:10]}"
        metadata = json.dumps({
            "call_type": "outbound_checkin", "user_id": request.user_id,
            "purpose": request.purpose, "opening": request.opening,
            "sip_identity": sip_identity,
        })
        client = api.LiveKitAPI()
        try:
            await client.room.create_room(CreateRoomRequest(name=room_name, empty_timeout=120))
            await client.agent_dispatch.create_dispatch(CreateAgentDispatchRequest(
                agent_name=self.agent_name, room=room_name, metadata=metadata
            ))
            await client.sip.create_sip_participant(CreateSIPParticipantRequest(
                sip_trunk_id=self.trunk_id, sip_call_to=request.recipient,
                room_name=room_name, participant_identity=sip_identity,
                participant_name="DhanBuddy recipient", participant_metadata=metadata,
                display_name="DhanBuddy", wait_until_answered=True,
            ))
            return CallResult("answered", self.name, room_name=room_name)
        except api.TwirpError as error:
            detail = f"{error.code} {error.message}".casefold()
            status = "busy" if "busy" in detail or "486" in detail else "no_answer" if "timeout" in detail or "408" in detail else "failed"
            logger.warning("Outbound %s call failed: status=%s", self.name, status)
            return CallResult(status, self.name, "telephony_provider_unavailable", room_name)
        finally:
            await client.aclose()
