import os

from telephony.livekit_sip import LiveKitSIPProvider


def create_twilio_provider() -> LiveKitSIPProvider:
    required = ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER", "LIVEKIT_SIP_OUTBOUND_TRUNK_ID")
    missing = [name for name in required if not os.getenv(name, "").strip()]
    if missing:
        raise ValueError("Missing Twilio provider configuration: " + ", ".join(missing))
    return LiveKitSIPProvider("twilio", os.environ["LIVEKIT_SIP_OUTBOUND_TRUNK_ID"], os.getenv("AGENT_NAME", "dhanbuddy"))
