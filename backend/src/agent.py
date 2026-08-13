import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Optional

import aiohttp
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

import db

logger = logging.getLogger("agent")

load_dotenv(".env.local")
db.init_db()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

SYSTEM_PROMPT = """IDENTITY
You are Sydney, an AI/ML learning companion built for the "Learning & Literacy"
track of 10 Days of Voice Agents, powered by Murf Falcon TTS. You work for the
learner, not for any exam board or employer — your job is to build their
understanding, not their credentials.

OBJECTIVES
A successful call achieves:
1. The learner leaves with a correct, self-explained understanding of ONE
   concept (RAG, backprop, loop/agent architecture, graph-based orchestration,
   etc.) — not a dump of five concepts half-understood.
2. Within the first 2-3 turns, you've calibrated to their actual level
   (total beginner vs. "I know Python but not transformers") rather than
   assuming.
3. The learner leaves knowing what to study next — a concept, not a copy-paste
   answer to their assignment.

KNOWLEDGE
You know ML/DL/RAG/prompt-engineering/agent-loop/graph-engineering concepts at
a solid conceptual and architectural level. You do NOT reliably know: current
library APIs, exact function signatures, version-specific syntax, or anything
released after your training data — for these, say so plainly and point them
to official docs instead of guessing. You cannot see or debug their actual
code over voice — if they need line-by-line debugging, tell them to paste it
in a text channel instead of improvising a fix blind.

LANGUAGE
Reply in the same language the learner just used.
- Learner speaks in English → reply in English.
- Learner speaks in Hindi → reply in Hindi.
- Learner mixes both → mix both back, roughly in the same ratio.
Technical words (RAG, vector database, embedding, backprop, token, node)
always stay in English.

LANGUAGE & SCRIPT
Always write every language in its own native script.
Hindi → Devanagari (नमस्ते), never romanized.

GUARDRAILS
Hard refusals:
- Never write or dictate a complete solution to a graded assignment or exam.
- Never fabricate a specific library API or version behavior — flag uncertainty.

Never-claims:
- Never state a learner has a learning disability or any diagnosable condition.
- Never shame a wrong answer. Reframe constructively.
- Never claim mastery unless demonstrated across the conversation.

ESCALATION — WHEN TO ASK FOR HUMAN HELP
Call create_escalation in exactly two situations:
1. Learner is emotionally distressed — says things like "I am stupid",
   "I give up", "I hate this", "I cannot do this", repeated frustration.
2. Learner explicitly asks for a human teacher or mentor.

Before calling create_escalation you MUST:
- Tell the learner what you want to share.
- Ask permission: "Kya main yeh details ek human mentor ke saath share kar
  sakti hoon?"
- Only call the tool if they say yes.
- After tool returns, tell the learner the reference ID and next steps.
  Do not promise immediate reply.

Do NOT escalate for wrong answers, confusion, or normal learning struggle.

MEMORY & CONSENT
- Before calling remember_caller_fact, ask out loud and wait for yes.
- If they decline, do not call the tool.
- Only store facts relevant to AI/ML learning progress.

EXERCISES
- Once the learner has clearly grasped a concept, proactively offer a
  practice exercise using fetch_next_exercise. Do not offer mid-explanation.
- Speak the question naturally, never like JSON.
- If the tool is unavailable, say so in one sentence and move on verbally.

STYLE
Short sentences under 20 words — this is spoken, not read. No bulleted lists
out loud. Pause after a new term. On silence 2-3s: re-prompt once with a
simpler question. On second silence: offer to pause.

VOICE REALISM
- Filler words sparingly, never stacked.
- Self-correct when introducing new concepts.
- Light non-verbal acknowledgments only — no sighs.
- Restate the question before answering it.
- Never repeat the same opener in back-to-back turns."""


def load_exercises():
    exercises_path = os.path.join(os.path.dirname(__file__), "exercises.json")
    if os.path.exists(exercises_path):
        with open(exercises_path, encoding="utf-8") as f:
            return json.load(f)
    return []


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self._exercise_fetched = False
        self._learner_responded = False
        self._escalation_created = False
        self._fact_saved = False
        self._user_turns = 0

    @function_tool
    async def lookup_caller(self, context: RunContext, user_id: str) -> str:
        """Look up stored information about the current caller by their user_id.

        Args:
            user_id: The unique identifier or phone number of the caller.
        """
        caller_info = db.get_caller(user_id)
        if caller_info:
            return (
                f"Caller Info for {user_id}: Name={caller_info.get('name')}, "
                f"Last Topic={caller_info.get('last_topic')}, "
                f"Facts={caller_info.get('facts')}, "
                f"Opted Out={bool(caller_info.get('opted_out'))}"
            )
        return f"No previous records found for caller {user_id}."

    @function_tool
    async def remember_caller_fact(
        self,
        context: RunContext,
        user_id: str,
        name: Optional[str] = None,
        last_topic: Optional[str] = None,
        fact: Optional[str] = None,
    ) -> str:
        """Save or update facts about the caller. Only call after explicit
        permission from the caller.

        Args:
            user_id: Caller's user ID or phone number.
            name: Caller's name if provided.
            last_topic: The topic covered in this session.
            fact: Any notable fact or preference to remember.
        """
        db.save_caller(
            user_id=user_id,
            name=name,
            last_topic=last_topic,
            facts=fact,
            opted_out=False,
        )
        self._fact_saved = True
        return f"Updated memory for caller {user_id}."

    @function_tool
    async def fetch_next_exercise(
        self, context: RunContext, topic: Optional[str] = None
    ) -> str:
        """Fetch a practice exercise for the learner. Call this proactively
        once the learner has just demonstrated understanding of a concept.
        Do not call this mid-explanation or at the start of a call.

        Args:
            topic: Optional specific topic to retrieve an exercise for.
        """
        try:
            exercises = load_exercises()
            if not exercises:
                return (
                    "The practice set is unavailable. Tell the learner in one "
                    "sentence and offer to talk through the concept verbally."
                )
            if topic:
                matching = [
                    e for e in exercises if topic.lower() in e.get("topic", "").lower()
                ]
                if matching:
                    ex = matching[0]
                    self._exercise_fetched = True
                    return (
                        f"Exercise: {ex['question']} "
                        f"Hint if stuck: {ex['hints'][0]} "
                        "Ask naturally. Do not reveal the hint unless stuck."
                    )
            ex = exercises[0]
            self._exercise_fetched = True
            return (
                f"Exercise: {ex['question']} "
                f"Hint if stuck: {ex['hints'][0]} "
                "Ask naturally. Do not reveal the hint unless stuck."
            )
        except Exception as e:
            logger.warning(f"fetch_next_exercise failed: {e}")
            return (
                "The practice set is unavailable. Tell the learner in one "
                "sentence and move on verbally. Do not invent a question."
            )

    @function_tool
    async def create_escalation(
        self,
        context: RunContext,
        user_id: str,
        name: str,
        reason: str,
        summary: str,
        language: str,
        follow_up: str,
    ) -> str:
        """Create a human escalation request. Only call after explicit
        permission from the learner.

        Args:
            user_id: Caller's user ID or phone number.
            name: Caller's name.
            reason: 'learner_distressed' or 'requested_human_teacher'.
            summary: Short summary of what happened and what was covered.
                     No passwords, OTPs, PINs, or account numbers.
            language: Language the learner used e.g. 'Hindi', 'Hinglish'.
            follow_up: How they want to be reached e.g. 'phone', 'email'.
        """
        try:
            self._escalation_created = True
            timestamp = datetime.now().strftime("%Y%m%d-%H%M")

            ref_id = f"ESC-{timestamp}"

            db.save_escalation(
                ref_id=ref_id,
                user_id=user_id,
                name=name,
                reason=reason,
                summary=summary,
                language=language,
                follow_up=follow_up,
            )

            if DISCORD_WEBHOOK_URL:
                reason_label = (
                    "🆘 Learner Distressed"
                    if reason == "learner_distressed"
                    else "🙋 Requested Human Teacher"
                )
                discord_payload = {
                    "embeds": [
                        {
                            "title": f"Sydney Escalation — {ref_id}",
                            "color": (
                                16711680 if reason == "learner_distressed" else 16744272
                            ),
                            "fields": [
                                {
                                    "name": "Reason",
                                    "value": reason_label,
                                    "inline": True,
                                },
                                {
                                    "name": "Name",
                                    "value": name or "Unknown",
                                    "inline": True,
                                },
                                {
                                    "name": "Language",
                                    "value": language,
                                    "inline": True,
                                },
                                {
                                    "name": "Follow-up via",
                                    "value": follow_up,
                                    "inline": True,
                                },
                                {
                                    "name": "User ID",
                                    "value": user_id,
                                    "inline": False,
                                },
                                {
                                    "name": "Summary",
                                    "value": summary,
                                    "inline": False,
                                },
                            ],
                            "footer": {"text": f"Reference ID: {ref_id}"},
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    ]
                }
                async with (
                    aiohttp.ClientSession() as http_session,
                    http_session.post(
                        DISCORD_WEBHOOK_URL,
                        json=discord_payload,
                    ) as resp,
                ):
                    if resp.status not in (200, 204):
                        logger.warning(f"Discord webhook returned {resp.status}")

            logger.info(f"Escalation created: {ref_id} for {user_id}")
            return (
                f"Escalation created. Reference ID: {ref_id}. "
                "Tell the learner their reference ID and that a human mentor "
                "will review this and follow up within 24 hours. "
                "Do not promise faster."
            )

        except Exception as e:
            logger.error(f"create_escalation failed: {e}")
            return (
                "The escalation could not be saved. Tell the learner you were "
                "unable to create the request and suggest they reach out to a "
                "mentor directly."
            )

    @function_tool
    async def opt_out_caller(self, context: RunContext, user_id: str) -> str:
        """Opt the caller out of future outbound practice calls.

        Args:
            user_id: The phone number or user ID of the caller opting out.
        """
        db.save_caller(user_id=user_id, opted_out=True)
        return f"Caller {user_id} has been opted out of future practice calls."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    assistant = Assistant()

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
        agent=assistant,
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

    participant = await ctx.wait_for_participant()
    user_id = participant.identity or "unknown"
    room_name = ctx.room.name

    disconnect_event = asyncio.Event()

    @ctx.room.on("disconnected")
    def _on_room_disconnected(*args):
        disconnect_event.set()

    @ctx.room.on("participant_disconnected")
    def _on_participant_disconnected(*args):
        disconnect_event.set()

    @session.on("user_speech_committed")
    def _on_user_speech(*args):
        assistant._user_turns += 1
        if assistant._exercise_fetched:
            assistant._learner_responded = True

    try:
        await disconnect_event.wait()
    finally:
        # A call is SUCCESSFUL if:
        # 1. The caller had a real conversation (at least 2 turns)
        # 2. OR an exercise was fetched AND the learner responded verbally after it
        # 3. OR a human escalation was created (_escalation_created)
        # 4. OR the caller's learning facts/progress were successfully saved (_fact_saved)
        is_success = (
            assistant._user_turns >= 2
            or (assistant._exercise_fetched and assistant._learner_responded)
            or assistant._escalation_created
            or assistant._fact_saved
        )
        outcome = "success" if is_success else "failed"

        db.save_call(
            user_id=user_id,
            room_name=room_name,
            outcome=outcome,
        )
        logger.info(
            f"Call ended — user: {user_id}, room: {room_name}, outcome: {outcome}"
        )


if __name__ == "__main__":
    cli.run_app(server)
