import os

from telephony.livekit_sip import LiveKitSIPProvider


def create_linphone_provider() -> LiveKitSIPProvider:
    trunk_id = os.getenv("LIVEKIT_SIP_OUTBOUND_TRUNK_ID", "").strip()
    if not trunk_id:
        raise ValueError("Missing Linphone provider configuration: LIVEKIT_SIP_OUTBOUND_TRUNK_ID")
    return LiveKitSIPProvider("linphone", trunk_id, os.getenv("AGENT_NAME", "dhanbuddy"))
