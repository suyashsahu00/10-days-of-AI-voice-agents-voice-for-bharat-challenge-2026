import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

import db
from agent import Assistant

logger = logging.getLogger("outbound-agent")

load_dotenv(".env.local")
db.init_db()

server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="outbound-agent")
async def outbound_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(model="gemini-3.5-flash-lite"),
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

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

    await ctx.connect()

    # Wait for the callee to join the session
    participant = await ctx.wait_for_participant()
    logger.info(f"Participant joined: {participant.identity}, kind: {participant.kind}")

    is_sip = participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
    user_id = (
        participant.identity
        or participant.attributes.get("sip.phoneNumber")
        or "unknown_caller"
    )

    caller_info = (
        db.get_caller(user_id) if is_sip or user_id != "unknown_caller" else None
    )

    if caller_info and (caller_info.get("name") or caller_info.get("last_topic")):
        name = caller_info.get("name", "there")
        topic = caller_info.get("last_topic", "our previous topic")
        greeting = f"Hi {name}, it's Sydney again. Last time we covered {topic}. Ready for a new one?"
    else:
        greeting = (
            "Hi, this is Sydney, your AI ML learning companion. "
            "I'm calling because you signed up for a daily practice session. "
            "I have a quick concept question for you today. "
            "If you don't want these calls, just say 'stop' and I'll make a note of it. "
            "Ready to begin?"
        )

    logger.info(f"Greeting participant ({user_id}): {greeting}")
    await session.say(greeting)


if __name__ == "__main__":
    cli.run_app(server)
