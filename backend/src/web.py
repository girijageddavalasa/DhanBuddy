import os
import re
import secrets
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from livekit import api
from document_parser import parse_document
from finance_data import correct_category, export_transactions, save_document
from ocr import OCRUnavailableError, extract_text
from upload_validation import MAX_UPLOAD_BYTES, validate_image
from escalation import list_escalations, update_escalation_status
from analytics import analytics_summary, health_snapshot

load_dotenv(Path(__file__).resolve().parents[1] / ".env.local")

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
ORIGINAL_DIR = DATA_DIR / "uploads" / "original"
EXPORT_DIR = DATA_DIR / "exports"
app = FastAPI(title="DhanBuddy")


def required_setting(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise HTTPException(status_code=503, detail=f"Missing server setting: {name}")
    return value


def current_user(request: Request) -> str:
    identity = request.cookies.get("dhanbuddy_user_id", "")
    if not re.fullmatch(r"caller-[a-f0-9]{32}", identity):
        raise HTTPException(status_code=401, detail="Start a DhanBuddy session first.")
    return identity


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/static/style.css", include_in_schema=False)
async def stylesheet() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "style.css", media_type="text/css")


@app.get("/static/app.js", include_in_schema=False)
async def javascript() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "app.js", media_type="text/javascript")


@app.get("/static/dashboard.js", include_in_schema=False)
async def dashboard_javascript() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "dashboard.js", media_type="text/javascript")


@app.get("/internal/support", include_in_schema=False)
async def support_page() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "support.html")


@app.get("/dashboard", include_in_schema=False)
async def dashboard_page() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "dashboard.html")


@app.get("/api/analytics")
async def call_analytics(
    date_from: str | None = None, date_to: str | None = None,
    language: str | None = None, channel: str | None = None,
    outcome: str | None = None,
) -> dict:
    return analytics_summary(
        date_from=date_from, date_to=date_to, language=language,
        channel=channel, outcome=outcome,
    )


@app.get("/api/health")
async def health() -> dict[str, object]:
    configured = all(os.getenv(name) for name in ("LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"))
    return health_snapshot(livekit_configured=configured)


def require_support_token(request: Request) -> None:
    expected = os.getenv("SUPPORT_VIEW_TOKEN", "")
    supplied = request.headers.get("x-support-token", "")
    if not expected or not secrets.compare_digest(expected, supplied):
        raise HTTPException(status_code=401, detail="Support authorization required.")


@app.get("/internal/api/escalations")
async def support_escalations(request: Request) -> list[dict]:
    require_support_token(request)
    return list_escalations()


@app.patch("/internal/api/escalations/{reference_id}")
async def support_update(reference_id: str, status: str, request: Request) -> dict:
    require_support_token(request)
    if not update_escalation_status(reference_id, status):
        raise HTTPException(status_code=404, detail="Escalation not found.")
    return {"updated": True}


@app.post("/api/token")
async def create_token(request: Request) -> JSONResponse:
    livekit_url = required_setting("LIVEKIT_URL")
    api_key = required_setting("LIVEKIT_API_KEY")
    api_secret = required_setting("LIVEKIT_API_SECRET")
    agent_name = os.getenv("AGENT_NAME", "dhanbuddy")
    room_name = f"dhanbuddy-{uuid.uuid4().hex[:12]}"
    saved_identity = request.cookies.get("dhanbuddy_user_id", "")
    identity = (
        saved_identity
        if re.fullmatch(r"caller-[a-f0-9]{32}", saved_identity)
        else f"caller-{uuid.uuid4().hex}"
    )

    room_config = api.RoomConfiguration(
        agents=[api.RoomAgentDispatch(agent_name=agent_name)]
    )
    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity(identity)
        .with_name("DhanBuddy caller")
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            )
        )
        .with_room_config(room_config)
        .to_jwt()
    )
    response = JSONResponse(
        {"serverUrl": livekit_url, "participantToken": token}
    )
    response.set_cookie(
        "dhanbuddy_user_id",
        identity,
        max_age=60 * 60 * 24 * 365,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
    )
    return response


@app.post("/api/documents")
async def upload_document(request: Request, file: UploadFile = File(...)) -> dict:
    user_id = current_user(request)
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 8 MB or smaller.")
    try:
        extension = validate_image(content)
    except ValueError as error:
        raise HTTPException(status_code=415, detail=str(error)) from error
    ORIGINAL_DIR.mkdir(parents=True, exist_ok=True)
    destination = ORIGINAL_DIR / f"{uuid.uuid4().hex}{extension}"
    destination.write_bytes(content)
    try:
        parsed = parse_document(extract_text(destination))
    except OCRUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    document_id = save_document(user_id, str(destination), parsed)
    safe_result = {key: value for key, value in parsed.items() if key != "raw_text"}
    return {"document_id": document_id, "document": safe_result}


@app.patch("/api/transactions/{transaction_id}/category")
async def update_category(transaction_id: int, category: str, request: Request) -> dict:
    updated = correct_category(current_user(request), transaction_id, category)
    if not updated:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    return {"updated": True}


@app.get("/api/exports/transactions.csv")
async def transactions_csv(request: Request) -> FileResponse:
    user_id = current_user(request)
    output = export_transactions(user_id, EXPORT_DIR / f"transactions-{user_id}.csv")
    return FileResponse(output, filename="transactions.csv", media_type="text/csv")
