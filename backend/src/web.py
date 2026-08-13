import os
import re
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
