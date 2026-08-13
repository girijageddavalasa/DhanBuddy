import asyncio
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen

RBI_FINANCIAL_EDUCATION_URL = "https://www.rbi.org.in/FinancialEducation/"


def _fetch() -> str:
    request = Request(RBI_FINANCIAL_EDUCATION_URL, headers={"User-Agent": "DhanBuddy/1.0"})
    with urlopen(request, timeout=8) as response:
        return response.read(4000).decode("utf-8", errors="replace")


async def fetch_rbi_financial_education() -> dict[str, object]:
    try:
        content = await asyncio.to_thread(_fetch)
        return {
            "available": True,
            "source": RBI_FINANCIAL_EDUCATION_URL,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "content": content,
        }
    except (OSError, URLError):
        return {
            "available": False,
            "message": "I couldn't reach the official RBI source, so I don't want to guess.",
        }
