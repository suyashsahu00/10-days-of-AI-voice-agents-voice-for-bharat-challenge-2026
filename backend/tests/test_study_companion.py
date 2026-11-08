import os
import sys
from pathlib import Path

from starlette.testclient import TestClient

# Ensure backend/src is in sys.path
backend_src = Path(__file__).resolve().parent.parent / "src"
if str(backend_src) not in sys.path:
    sys.path.insert(0, str(backend_src))

from agent import SYSTEM_PROMPT, Assistant  # noqa: E402
from main import app  # noqa: E402


def test_system_prompt_configuration():
    """Verify system prompt contains the exact required prompt instructions."""
    required_prompt = (
        "You are an AI study companion. The user will provide technical exam notes or syllabus topics "
        "(e.g., Artificial Neural Networks, MPU6050, Data Mining). Your job is to read the text and explain "
        "it conversationally, concisely, and clearly, as if you are teaching it right before an exam. "
        "Do not read Markdown tables or bullet points literally; convert them into natural spoken sentences. "
        "Keep responses highly engaging and pause to ask if the user understood."
    )
    assert required_prompt in SYSTEM_PROMPT
    assert "7th-semester Computer Science professor" in SYSTEM_PROMPT


def test_assistant_initialization():
    """Verify Assistant instantiates with system prompt instructions."""
    assistant = Assistant()
    assert assistant.instructions == SYSTEM_PROMPT


def test_fastapi_root_endpoint():
    """Verify FastAPI root endpoint provides service overview."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Real-Time Study Companion Voice Agent"
    assert "Deepgram" in data["pipeline"]["stt"]
    assert "Gemini" in data["pipeline"]["llm"]
    assert "Murf" in data["pipeline"]["tts"]


def test_fastapi_health_endpoint():
    """Verify FastAPI health endpoint reports status."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["service"] == "real-time-study-companion"


def test_fastapi_token_endpoint():
    """Verify token generation endpoint works when credentials are provided."""
    client = TestClient(app)
    os.environ["LIVEKIT_API_KEY"] = "devkey"
    os.environ["LIVEKIT_API_SECRET"] = (
        "secret_key_minimum_length_must_be_thirty_two_chars_long"
    )
    os.environ["LIVEKIT_URL"] = "wss://test.livekit.cloud"

    response = client.post(
        "/api/token",
        json={"room_name": "exam-revision", "participant_identity": "student-test"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["room_name"] == "exam-revision"
    assert data["participant_identity"] == "student-test"
