import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Load environment variables from .env.local, .env, or parent directories
env_paths = [
    Path(".env.local"),
    Path(".env"),
    Path("../.env.local"),
    Path("../.env"),
]
for p in env_paths:
    if p.exists():
        load_dotenv(p)

# Ensure Gemini / Google API key compatibility
gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if gemini_key:
    os.environ["GOOGLE_API_KEY"] = gemini_key
    os.environ["GEMINI_API_KEY"] = gemini_key

logger = logging.getLogger("study-companion-agent")

# -----------------------------------------------------------------------------
# 7th-Semester Computer Science Professor & Study Buddy System Prompt
# -----------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an AI study companion. The user will provide technical exam notes or syllabus topics (e.g., Artificial Neural Networks, MPU6050, Data Mining). Your job is to read the text and explain it conversationally, concisely, and clearly, as if you are teaching it right before an exam. Do not read Markdown tables or bullet points literally; convert them into natural spoken sentences. Keep responses highly engaging and pause to ask if the user understood.

ROLE & PERSONA:
- You are a friendly, encouraging 7th-semester Computer Science professor and study buddy.
- You have deep technical mastery across Computer Science, Electronics, and AI/ML, but you talk like an approachable mentor doing a rapid whiteboard revision session.
- You distill dense academic syllabi into intuitive, high-scoring exam insights.

TEACHING & SPOKEN DELIVERY GUIDELINES:
1. Pure Spoken Cadence: This conversation happens entirely over voice. Keep sentences short, punchy, and conversational (typically under 20 words each).
2. No Literal Formatting: Never recite asterisks, hashes, backticks, bullet symbols, or table grid syntax out loud. Convert tables into natural comparative sentences (e.g., "Compared to supervised learning, unsupervised learning...").
3. Analogies First, Formulas Second: Ground technical topics in vivid real-world intuition before mentioning technical jargon:
   - Artificial Neural Networks (ANN): Weights as volume knobs, activation functions as threshold switches, backpropagation as adjusting knobs based on the final error.
   - MPU6050: A 6-axis motion tracking sensor combining a 3-axis accelerometer (measures gravity and tilt) and a 3-axis gyroscope (measures angular velocity), communicating over I2C.
   - Data Mining: Finding hidden gold in mountains of data—classification for categorizing, clustering for grouping without labels, association rules for market baskets.
4. Active Checking: End explanations by briefly pausing and checking for understanding (e.g., "Does that picture make sense so far?", "Ready to look at how the equations work?", "Should we test this with a quick exam question?").
5. Language & Tone: Confident, crisp, supportive, and energetic. If the student is confused, break the concept down into an even simpler analogy without making them feel bad.
"""


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    @function_tool
    async def explain_exam_concept(
        self,
        context: RunContext,
        topic: str,
        focus_area: str = "core intuition and exam questions",
    ) -> str:
        """Break down a specific computer science or engineering topic for an upcoming exam.

        Args:
            topic: The technical topic or syllabus unit (e.g., Backpropagation, MPU6050 I2C registers, Apriori Algorithm)
            focus_area: Specific exam angle such as high-yield questions, numericals, or architectural trade-offs
        """
        logger.info(f"Explaining exam concept: {topic} (focus: {focus_area})")
        return (
            f"Here is the high-yield exam breakdown for '{topic}': "
            f"Focus on the core principle, how it behaves during operation, and the standard 5-mark exam question asked on it. "
            f"Deliver this explanation conversationally and ask the student if they understood."
        )

    @function_tool
    async def quiz_student(
        self,
        context: RunContext,
        topic: str,
        difficulty: str = "medium",
    ) -> str:
        """Generate a quick 1-question verbal check to test the student's exam readiness on a topic.

        Args:
            topic: The subject or topic being revised
            difficulty: 'easy', 'medium', or 'hard'
        """
        logger.info(f"Generating verbal quiz question for topic: {topic}")
        return f"Formulate one sharp, high-yield exam question on {topic} ({difficulty} difficulty) and ask the student to answer in their own words."


server = AgentServer()


def prewarm(proc: JobProcess):
    """Pre-load heavy models into memory (Silero VAD)."""
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    """LiveKit RTC session entry point for the Study Companion voice agent."""
    ctx.log_context_fields = {
        "room": ctx.room.name,
        "agent": "study-companion",
    }
    logger.info(f"Starting Real-Time Study Companion for room: {ctx.room.name}")

    # Determine configuration from environment
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    murf_voice = os.getenv("MURF_VOICE", "Anisha")
    deepgram_model = os.getenv("DEEPGRAM_MODEL", "nova-3")

    # Set up the voice AI pipeline:
    # 1. Deepgram STT: turns student voice speech into text
    # 2. Google Gemini: converts syllabus notes and questions into conversational exam explanations
    # 3. Murf Falcon TTS: renders the teacher's voice in real-time
    session = AgentSession(
        stt=deepgram.STT(
            model=deepgram_model,
            language="multi",
        ),
        llm=google.LLM(
            model=gemini_model,
            api_key=gemini_key,
        ),
        tts=murf.TTS(
            voice=murf_voice,
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    # Listen for incoming data packets (e.g. study notes / syllabus text submitted by user via UI)
    @ctx.room.on("data_received")
    def on_data_received(data_packet: rtc.DataPacket):
        try:
            raw_text = data_packet.data.decode("utf-8")
            logger.info(f"Received study notes via data packet: {raw_text[:60]}...")
            session.generate_reply(
                user_input=(
                    f'The student just submitted these study notes/text:\n"{raw_text}"\n\n'
                    "Please explain these notes conversationally and concisely for their upcoming exam. "
                    "Do not read bullet points or markdown tables literally. "
                    "Keep it highly engaging and pause to ask if they understood."
                )
            )
        except Exception as exc:
            logger.error(f"Failed to process incoming study notes data: {exc}")

    # Start the session and connect room IO
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Join the room and connect WebRTC streams
    await ctx.connect()
    logger.info(
        f"Agent joined room {ctx.room.name}. Waiting for participant to connect..."
    )

    # Wait for the student to join the room
    participant = await ctx.wait_for_participant()
    logger.info(f"Student participant connected: {participant.identity}")

    # Automatic greeting: Agent answers immediately when user connects
    session.generate_reply(
        instructions=(
            "Greet the student warmly and enthusiastically as their 7th-semester Computer Science professor "
            "and study buddy. Welcome them to today's exam revision session, and ask what technical syllabus topic "
            "or study notes (like Artificial Neural Networks, MPU6050, or Data Mining) they want to master right now."
        )
    )


if __name__ == "__main__":
    cli.run_app(server)
