from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

CallStatus = Literal["answered", "busy", "no_answer", "failed", "user_hangup"]


@dataclass(frozen=True)
class CallRequest:
    recipient: str
    purpose: str
    user_id: str
    opening: str


@dataclass(frozen=True)
class CallResult:
    status: CallStatus
    provider: str
    reason: str | None = None
    room_name: str | None = None


class TelephonyProvider(ABC):
    name: str

    @abstractmethod
    async def place_call(self, request: CallRequest) -> CallResult:
        raise NotImplementedError
