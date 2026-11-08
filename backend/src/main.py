import argparse
import logging
import multiprocessing
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
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
async def root(request: Request):
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header:
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Real-Time Study Companion — Voice for Bharat</title>
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: #151e32;
      --text: #f1f5f9;
      --accent: #6366f1;
      --accent-hover: #4f46e5;
      --muted: #94a3b8;
      --border: #23314e;
      --success: #10b981;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      margin: 0;
      padding: 2rem 1rem;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    .container {
      max-width: 840px;
      width: 100%;
    }
    .header {
      text-align: center;
      margin-bottom: 2rem;
    }
    h1 { margin: 0.5rem 0; font-size: 2.2rem; }
    p.subtitle { color: var(--muted); margin: 0; font-size: 1.1rem; }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.5rem;
      margin-bottom: 1.5rem;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .badge {
      display: inline-block;
      padding: 0.35rem 0.75rem;
      border-radius: 9999px;
      background: var(--success);
      color: white;
      font-weight: 600;
      font-size: 0.85rem;
    }
    .pipeline {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 1rem;
      margin-top: 1rem;
    }
    .pipeline-item {
      background: #0b0f19;
      border: 1px solid var(--border);
      padding: 0.85rem;
      border-radius: 8px;
    }
    .pipeline-item strong { display: block; color: #818cf8; font-size: 0.85rem; margin-bottom: 0.25rem; }
    .pipeline-item span { font-size: 0.95rem; }
    .quick-topics {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin: 0.75rem 0;
    }
    .chip {
      background: #1e293b;
      border: 1px solid var(--border);
      color: #c7d2fe;
      padding: 0.3rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.85rem;
      cursor: pointer;
      transition: all 0.2s;
    }
    .chip:hover {
      background: var(--accent);
      color: white;
      border-color: var(--accent);
    }
    textarea {
      width: 100%;
      box-sizing: border-box;
      height: 140px;
      background: #0b0f19;
      border: 1px solid var(--border);
      border-radius: 8px;
      color: var(--text);
      padding: 0.85rem;
      font-family: inherit;
      font-size: 0.95rem;
      line-height: 1.5;
      resize: vertical;
    }
    textarea:focus {
      outline: none;
      border-color: var(--accent);
    }
    .actions {
      display: flex;
      align-items: center;
      gap: 1rem;
      margin-top: 1rem;
    }
    button.btn-primary {
      background: var(--accent);
      color: white;
      border: none;
      padding: 0.85rem 1.75rem;
      border-radius: 8px;
      font-weight: 600;
      font-size: 1rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      transition: background 0.2s;
    }
    button.btn-primary:hover:not(:disabled) { background: var(--accent-hover); }
    button.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
    button.btn-secondary {
      background: #1e293b;
      color: #f1f5f9;
      border: 1px solid var(--border);
      padding: 0.6rem 1.2rem;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      font-size: 0.9rem;
    }
    button.btn-secondary:hover { background: #334155; }
    #statusIndicator {
      display: none;
      margin-top: 1rem;
      padding: 0.75rem 1rem;
      border-radius: 8px;
      background: rgba(99, 102, 241, 0.15);
      border: 1px solid var(--accent);
      color: #c7d2fe;
      font-size: 0.95rem;
    }
    #resultCard {
      display: none;
      margin-top: 1.5rem;
      padding: 1.25rem;
      border-radius: 8px;
      background: #0b0f19;
      border: 1px solid var(--border);
    }
    #teachingText {
      line-height: 1.65;
      font-size: 1.05rem;
      white-space: pre-wrap;
      margin-bottom: 1.5rem;
    }
    .takeaways {
      background: #151e32;
      border-left: 4px solid var(--success);
      padding: 1rem;
      border-radius: 4px;
      margin-bottom: 1.25rem;
    }
    .takeaways h4 { margin: 0 0 0.5rem 0; color: var(--success); }
    .takeaways ul { margin: 0; padding-left: 1.2rem; }
    .takeaways li { margin-bottom: 0.35rem; font-size: 0.95rem; }
    a.link { color: #818cf8; text-decoration: none; font-weight: 500; }
    a.link:hover { text-decoration: underline; }
    .spinner {
      width: 16px;
      height: 16px;
      border: 2px solid #ffffff;
      border-top-color: transparent;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      display: inline-block;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <span class="badge">LiveKit WebRTC + Murf Falcon TTS + Google Gemini</span>
      <h1>Real-Time Study Companion</h1>
      <p class="subtitle">7th-Semester Computer Science Professor & Exam Study Buddy</p>
    </div>

    <div class="card">
      <h3 style="margin-top: 0;">Active Architecture Pipeline</h3>
      <div class="pipeline">
        <div class="pipeline-item">
          <strong>STT (Ears)</strong>
          <span>Deepgram Nova-3</span>
        </div>
        <div class="pipeline-item">
          <strong>LLM (Brain)</strong>
          <span>Google Gemini 2.5 Flash</span>
        </div>
        <div class="pipeline-item">
          <strong>TTS (Voice)</strong>
          <span>Murf Falcon (Anisha / Marcus)</span>
        </div>
        <div class="pipeline-item">
          <strong>Real-Time Stream</strong>
          <span>LiveKit WebRTC</span>
        </div>
      </div>
    </div>

    <div class="card">
      <h3 style="margin-top: 0;">Try Study Notes Conversion</h3>
      <p style="color: var(--muted); margin: 0 0 0.5rem 0;">Paste raw syllabus notes, formulas, or pick a sample exam topic:</p>

      <div class="quick-topics">
        <span class="chip" onclick="loadSample('rnn')">RNNs & Feedback Loops</span>
        <span class="chip" onclick="loadSample('mpu6050')">MPU6050 Accelerometer / I2C</span>
        <span class="chip" onclick="loadSample('backprop')">ANN & Backpropagation</span>
        <span class="chip" onclick="loadSample('apriori')">Data Mining & Apriori</span>
      </div>

      <textarea id="notesInput" placeholder="Paste bullet points, tables, or syllabus text here...">A **Recurrent Neural Network (RNN)** is a class of artificial neural networks designed specifically for processing **sequential or time-series data**. Unlike standard feedforward neural networks where inputs are processed independently, an RNN contains **feedback loops** that allow information to persist across consecutive time steps.</textarea>

      <div class="actions">
        <button id="convertBtn" class="btn-primary" onclick="convertNotes()">
          <span>Convert to Spoken Exam Teaching Script</span>
        </button>
        <span style="color: var(--muted); font-size: 0.85rem;">(or press Ctrl+Enter)</span>
      </div>

      <div id="statusIndicator">
        <span class="spinner" style="margin-right: 0.5rem; vertical-align: middle;"></span>
        <span id="statusText">Consulting Google Gemini Professor... please wait (~5-10s)</span>
      </div>

      <div id="resultCard">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; border-bottom: 1px solid var(--border); padding-bottom: 0.75rem;">
          <h3 style="margin: 0; color: #818cf8;">Spoken Teaching Script</h3>
          <div style="display: flex; gap: 0.5rem;">
            <button id="readAloudBtn" class="btn-secondary" onclick="toggleReadAloud()">🔊 Read Aloud</button>
            <button class="btn-secondary" onclick="copyScript()">📋 Copy</button>
          </div>
        </div>

        <div id="teachingText"></div>

        <div class="takeaways">
          <h4>Key High-Yield Exam Takeaways:</h4>
          <ul id="takeawaysList"></ul>
        </div>

        <div style="margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center;">
          <span style="color: var(--muted); font-size: 0.85rem;">Ready to practice live over voice?</span>
          <a class="link" href="http://localhost:3000" target="_blank" style="font-weight: 600;">Launch LiveKit Voice Session &rarr;</a>
        </div>
      </div>
    </div>

    <div class="card" style="display: flex; justify-content: space-between; align-items: center;">
      <div>
        <strong>Interactive OpenAPI Docs:</strong>
        <span style="color: var(--muted);">Explore all backend endpoints (/api/token, /api/study-notes) via Swagger</span>
      </div>
      <a class="link" href="/docs" target="_blank">Open /docs &rarr;</a>
    </div>
  </div>

  <script>
    const samples = {
      rnn: "A **Recurrent Neural Network (RNN)** is a class of artificial neural networks designed specifically for processing **sequential or time-series data**. Unlike standard feedforward neural networks where inputs are processed independently, an RNN contains **feedback loops** that allow information to persist across consecutive time steps.",
      mpu6050: "MPU6050 is a 6-axis motion tracking sensor. It integrates a 3-axis MEMS accelerometer and a 3-axis MEMS gyroscope on the same silicon die. It communicates with microcontrollers using the I2C bus protocol (default address 0x68 or 0x69 when AD0 is HIGH). Accelerometer measures linear acceleration and gravity, while Gyroscope measures angular velocity in degrees per second.",
      backprop: "Backpropagation is the primary algorithm used to train Artificial Neural Networks. It computes the gradient of the loss function with respect to each weight using the Chain Rule of calculus. The error is propagated backward from the output layer to the input layer, adjusting weights via gradient descent with learning rate alpha.",
      apriori: "Apriori algorithm is used for Frequent Itemset Mining and Association Rule Learning in data mining. It operates on the downward-closure property: all non-empty subsets of a frequent itemset must also be frequent. Key metrics: Support (frequency of itemset), Confidence (conditional probability), and Lift (strength of rule over random coincidence)."
    };

    function loadSample(key) {
      document.getElementById('notesInput').value = samples[key] || '';
    }

    document.getElementById('notesInput').addEventListener('keydown', function(e) {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        convertNotes();
      }
    });

    let synthUtterance = null;

    async function convertNotes() {
      const text = document.getElementById('notesInput').value.trim();
      if (!text) {
        alert('Please paste some syllabus notes or select a sample topic first!');
        return;
      }

      const btn = document.getElementById('convertBtn');
      const statusIndicator = document.getElementById('statusIndicator');
      const statusText = document.getElementById('statusText');
      const resultCard = document.getElementById('resultCard');
      const teachingText = document.getElementById('teachingText');
      const takeawaysList = document.getElementById('takeawaysList');

      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span> <span>Consulting Gemini Professor...</span>';
      statusIndicator.style.display = 'block';
      statusText.innerText = 'Connecting to Google Gemini 2.5 Flash... transforming dense notes into spoken script (~5-10s)';
      resultCard.style.display = 'none';

      try {
        const res = await fetch('/api/study-notes', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({notes: text, topic: 'CS Exam Revision'})
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || `Server returned status ${res.status}`);
        }

        const data = await res.json();
        teachingText.innerText = data.teaching_script || 'No script returned.';

        takeawaysList.innerHTML = '';
        if (data.key_takeaways && data.key_takeaways.length) {
          data.key_takeaways.forEach(item => {
            const li = document.createElement('li');
            li.innerText = item;
            takeawaysList.appendChild(li);
          });
        }

        statusIndicator.style.display = 'none';
        resultCard.style.display = 'block';
        resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });

      } catch (err) {
        statusIndicator.style.display = 'block';
        statusIndicator.style.background = 'rgba(239, 68, 68, 0.2)';
        statusIndicator.style.borderColor = '#ef4444';
        statusIndicator.style.color = '#fca5a5';
        statusText.innerHTML = '<strong>Error:</strong> ' + err.message + '<br><small>Ensure backend is running (uv run python src/main.py) and GEMINI_API_KEY/GOOGLE_API_KEY is configured in .env.local.</small>';
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>Convert to Spoken Exam Teaching Script</span>';
      }
    }

    function toggleReadAloud() {
      const readBtn = document.getElementById('readAloudBtn');
      const text = document.getElementById('teachingText').innerText;
      if (!window.speechSynthesis) {
        alert('Your browser does not support speech synthesis.');
        return;
      }

      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
        readBtn.innerText = '🔊 Read Aloud';
        return;
      }

      synthUtterance = new SpeechSynthesisUtterance(text);
      synthUtterance.rate = 1.05;
      synthUtterance.pitch = 1.0;
      synthUtterance.onend = () => { readBtn.innerText = '🔊 Read Aloud'; };
      synthUtterance.onerror = () => { readBtn.innerText = '🔊 Read Aloud'; };

      window.speechSynthesis.speak(synthUtterance);
      readBtn.innerText = '⏹️ Stop Audio';
    }

    function copyScript() {
      const text = document.getElementById('teachingText').innerText;
      navigator.clipboard.writeText(text).then(() => {
        alert('Spoken script copied to clipboard!');
      });
    }
  </script>
</body>
</html>"""
        return HTMLResponse(content=html_content)

    return JSONResponse(
        content={
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
    )


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

    display_host = "localhost" if host in ("0.0.0.0", "127.0.0.1") else host
    print(
        f"\n============================================================\n"
        f"  Real-Time Study Companion Backend is Running!\n"
        f"  -> Open in your browser:  http://{display_host}:{port}\n"
        f"  -> Interactive Swagger:   http://{display_host}:{port}/docs\n"
        f"  (Note: Windows browsers cannot open 0.0.0.0, use localhost)\n"
        f"============================================================\n",
        flush=True,
    )
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
