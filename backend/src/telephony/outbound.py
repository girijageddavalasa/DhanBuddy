import logging
import os
import re

from telephony.linphone import create_linphone_provider
from telephony.preferences import is_opted_out
from telephony.provider import CallRequest, CallResult, TelephonyProvider
from telephony.twilio import create_twilio_provider

logger = logging.getLogger("dhanbuddy.outbound")
E164 = re.compile(r"^\+[1-9]\d{7,14}$")
ALLOWED_PURPOSES = {
    "financial_check_in": "your requested financial check-in",
    "document_follow_up": "your requested document follow-up",
}


def build_call_opening(purpose: str) -> str:
    reason = ALLOWED_PURPOSES.get(purpose)
    if reason is None:
        raise ValueError("Unsupported call purpose.")
    return (
        f"Hi, I'm DhanBuddy, your financial assistant. I'm calling for {reason}. "
        "You can end the call anytime."
    )


def select_provider(name: str | None = None) -> TelephonyProvider:
    selected = (name or os.getenv("TELEPHONY_PROVIDER", "twilio")).strip().casefold()
    if selected == "twilio":
        return create_twilio_provider()
    if selected == "linphone":
        return create_linphone_provider()
    raise ValueError("TELEPHONY_PROVIDER must be twilio or linphone.")


def validate_request(recipient: str, purpose: str, user_id: str) -> CallRequest:
    if not recipient.strip():
        raise ValueError("Recipient is required.")
    if not E164.fullmatch(recipient.strip()):
        raise ValueError("Recipient must use E.164 format.")
    if not user_id.strip() or len(user_id) > 128:
        raise ValueError("A valid anonymous user ID is required.")
    if is_opted_out(user_id):
        raise PermissionError("This user opted out of outbound calls.")
    return CallRequest(recipient.strip(), purpose, user_id, build_call_opening(purpose))


async def make_outbound_call(
    recipient: str, purpose: str, user_id: str,
    provider: TelephonyProvider | None = None, confirmed_opt_in: bool = False,
) -> CallResult:
    if not confirmed_opt_in:
        return CallResult("failed", provider.name if provider else "unselected", "explicit_opt_in_required")
    try:
        request = validate_request(recipient, purpose, user_id)
        selected = provider or select_provider()
        return await selected.place_call(request)
    except PermissionError:
        return CallResult("failed", provider.name if provider else "unselected", "user_opted_out")
    except ValueError as error:
        logger.warning("Outbound call blocked: %s", error)
        return CallResult("failed", provider.name if provider else "unselected", "invalid_or_missing_configuration")
