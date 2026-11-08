import argparse
import logging
import multiprocessing
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure src directory is in sys.path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Load environment variables
for env_file in [
    Path(".env.local"),
    Path(".env"),
    Path("../.env.local"),
    Path("../.env"),
]:
    if env_file.exists():
        load_dotenv(env_file)

# Ensure Gemini / Google API key compatibility
gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if gemini_key:
    os.environ["GOOGLE_API_KEY"] = gemini_key
    os.environ["GEMINI_API_KEY"] = gemini_key

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("study-companion-backend")

app = FastAPI(
    title="Real-Time Study Companion API",
    description="FastAPI backend for Real-Time AI Study Companion powered by LiveKit, Google Gemini, and Murf Falcon TTS",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Request & Response Schemas
# -----------------------------------------------------------------------------
class TokenRequest(BaseModel):
    room_name: str = Field(
        default="study-room", description="Name of the LiveKit study room"
    )
    participant_identity: str = Field(
        default="student-user", description="Unique student identity"
    )
    participant_name: Optional[str] = Field(
        default="Student", description="Student display name"
    )


class TokenResponse(BaseModel):
    token: str
    url: str
    room_name: str
    participant_identity: str


class StudyNotesRequest(BaseModel):
    notes: str = Field(
        ..., description="Raw study notes, syllabus topics, or technical text"
    )
    topic: Optional[str] = Field(
        default=None,
        description="Optional topic headline (e.g. Artificial Neural Networks)",
    )
    room_name: Optional[str] = Field(
        default=None, description="Optional active LiveKit room to broadcast notes to"
    )


class StudyNotesResponse(BaseModel):
    status: str
    topic: str
    teaching_script: str
    key_takeaways: list[str]
    broadcasted_to_room: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    livekit_configured: bool
    gemini_configured: bool
    murf_configured: bool
    deepgram_configured: bool


# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------
@app.get("/", tags=["General"])
async def root():
    return {
        "service": "Real-Time Study Companion Voice Agent",
        "description": "7th-Semester Computer Science Professor & Study Buddy",
        "pipeline": {
            "stt": "Deepgram Nova-3",
            "llm": "Google Gemini 2.5 Flash",
            "tts": "Murf Falcon (Anisha / Conversation)",
            "transport": "LiveKit WebRTC",
        },
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    lk_url = bool(os.getenv("LIVEKIT_URL"))
    lk_key = bool(os.getenv("LIVEKIT_API_KEY"))
    lk_sec = bool(os.getenv("LIVEKIT_API_SECRET"))
    gemini_ok = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    murf_ok = bool(os.getenv("MURF_API_KEY"))
    deepgram_ok = bool(os.getenv("DEEPGRAM_API_KEY"))

    all_configured = (
        lk_url and lk_key and lk_sec and gemini_ok and murf_ok and deepgram_ok
    )

    return HealthResponse(
        status="healthy" if all_configured else "partially_configured",
        service="real-time-study-companion",
        livekit_configured=lk_url and lk_key and lk_sec,
        gemini_configured=gemini_ok,
        murf_configured=murf_ok,
        deepgram_configured=deepgram_ok,
    )


@app.post("/api/token", response_model=TokenResponse, tags=["LiveKit"])
async def create_token(req: TokenRequest):
    """Generate a WebRTC access token for a student connecting to a study room."""
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    url = os.getenv("LIVEKIT_URL", "wss://localhost:7880")

    if not api_key or not api_secret:
        raise HTTPException(
            status_code=500,
            detail="LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be configured in environment.",
        )

    try:
        from livekit.api import AccessToken, VideoGrants

        token = (
            AccessToken(api_key, api_secret)
            .with_identity(req.participant_identity)
            .with_name(req.participant_name or req.participant_identity)
            .with_grants(
                VideoGrants(
                    room_join=True,
                    room=req.room_name,
                    can_publish=True,
                    can_subscribe=True,
                    can_publish_data=True,
                )
            )
            .to_jwt()
        )

        return TokenResponse(
            token=token,
            url=url,
            room_name=req.room_name,
            participant_identity=req.participant_identity,
        )
    except Exception as e:
        logger.error(f"Error generating LiveKit token: {e}")
        raise HTTPException(
            status_code=500, detail=f"Token creation failed: {e!s}"
        ) from e


@app.post("/api/study-notes", response_model=StudyNotesResponse, tags=["Study Notes"])
async def process_study_notes(req: StudyNotesRequest):
    """Process technical study notes/syllabus into a conversational teaching script using Gemini."""
    gkey = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not gkey:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY or GOOGLE_API_KEY must be set.",
        )

    topic = req.topic or "Technical Exam Topics"

    prompt = (
        "You are an AI study companion acting as an expert 7th-semester Computer Science professor "
        "and exam study buddy. The student provided the following technical study notes or syllabus text:\n\n"
        f"--- NOTES BEGIN ---\n{req.notes}\n--- NOTES END ---\n\n"
        "TASK:\n"
        "1. Convert this technical material into a conversational, easy-to-understand spoken teaching script "
        "suitable for reading aloud right before an exam.\n"
        "2. Do NOT read Markdown tables or bullet points literally; convert them into natural spoken sentences.\n"
        "3. Use vivid intuitive analogies (like volume knobs for neural net weights, or gyroscopes for tilt angle).\n"
        "4. Keep the response punchy, highly engaging, and end by pausing to ask if the student understood.\n"
    )

    teaching_script = ""
    try:
        from google import genai

        client = genai.Client(api_key=gkey)
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=prompt,
        )
        teaching_script = response.text or ""
    except Exception as err:
        logger.warning(
            f"Google GenAI client call encountered: {err}. Attempting fallback formatting."
        )
        teaching_script = (
            f"Alright, let's break down {topic} for your exam! "
            f"Here is the core idea: {req.notes.strip().replace(chr(10), ' ')}. "
            "Remember to focus on the main architecture and how signals propagate through the system. "
            "Does that intuition make sense so far?"
        )

    # Optional: Send notes to active LiveKit room via LiveKit Server API
    broadcasted_room = None
    if req.room_name:
        try:
            from livekit.api import LiveKitAPI

            lk_api = LiveKitAPI()
            await lk_api.room.send_data(
                room=req.room_name,
                data=f"STUDY_NOTES:{req.notes}".encode(),
            )
            await lk_api.aclose()
            broadcasted_room = req.room_name
        except Exception as lk_err:
            logger.warning(
                f"Could not broadcast data to room {req.room_name}: {lk_err}"
            )

    takeaways = [
        "Core Intuition: Master the physical / system architecture before jumping to formulas.",
        "Exam Tip: Explain equations with verbal variable definitions rather than raw math symbols.",
        "Key Differentiator: Understand how error signals or sensor readings are calibrated.",
    ]

    return StudyNotesResponse(
        status="success",
        topic=topic,
        teaching_script=teaching_script,
        key_takeaways=takeaways,
        broadcasted_to_room=broadcasted_room,
    )


# -----------------------------------------------------------------------------
# Worker & Server Runner
# -----------------------------------------------------------------------------
def run_livekit_worker():
    """Run the LiveKit Agent Worker process."""
    from livekit.agents import cli

    from agent import server

    cli.run_app(server)


def run_fastapi_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the FastAPI server via uvicorn."""
    import uvicorn

    uvicorn.run("main:app", host=host, port=port, reload=False)


def main():
    parser = argparse.ArgumentParser(
        description="Real-Time Study Companion Backend & Worker"
    )
    parser.add_argument(
        "--worker",
        action="store_true",
        help="Run LiveKit Agent Worker only",
    )
    parser.add_argument(
        "--server",
        action="store_true",
        help="Run FastAPI server only",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run both FastAPI backend and LiveKit Worker concurrently",
    )
    parser.add_argument(
        "--host", default=os.getenv("HOST", "0.0.0.0"), help="Host for FastAPI server"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8000")),
        help="Port for FastAPI server",
    )

    args, unknown = parser.parse_known_args()

    if args.worker:
        # Pass remaining arguments to LiveKit CLI
        sys.argv = [sys.argv[0], *unknown]
        run_livekit_worker()
    elif args.all:
        logger.info("Starting FastAPI server and LiveKit Worker concurrently...")
        worker_process = multiprocessing.Process(target=run_livekit_worker, daemon=True)
        worker_process.start()
        try:
            run_fastapi_server(host=args.host, port=args.port)
        finally:
            worker_process.terminate()
    else:
        # Default behavior: run FastAPI server
        run_fastapi_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
