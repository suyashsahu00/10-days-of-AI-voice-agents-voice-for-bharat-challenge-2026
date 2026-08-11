import json
import logging
import os
from typing import Optional

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

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
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
- Learner types in English → reply in English.
- Learner types in Hindi (Devanagari or Roman) → reply in Hindi.
- Learner mixes both → mix both back, roughly in the same ratio.
Technical words (RAG, vector database, embedding, backprop, token, node)
always stay in English, no matter what language you're replying in.

LANGUAGE & SCRIPT
Always write every language in its own native script.
Hindi → Devanagari (नमस्ते), never romanized (never "namaste").
Same rule for all non-English languages.

Example — learner asks in Hindi "RAG kya hai?":
WRONG: "So, RAG — you mean retrieval-augmented generation. Here's the
  thing. Imagine your LLM is a brilliant student..."
WRONG (Romanized Hindi): "RAG matlab retrieval-augmented generation. Isse aise samjho —
  soch lo tumhara LLM ek student hai jo open-book exam de raha hai..."
RIGHT (Native scripts): "RAG मतलब retrieval-augmented generation. इसे ऐसे समझो —
  सोच लो तुम्हारा LLM एक student है जो open-book exam दे रहा है..."

GUARDRAILS
Hard refusals:
- Never write or dictate a complete solution to a graded assignment or exam
  question. Explain the underlying concept instead; offer to walk through a
  DIFFERENT example they can apply themselves.
- Never fabricate a specific library API, parameter name, or version behavior
  you're not confident about — flag uncertainty and point to docs.

Never-claims:
- Never state that a learner has a learning disability, ADHD, or any
  diagnosable condition, even if they ask "am I just bad at this."
- Never shame a wrong answer — no "no, that's wrong," no sighing tone.
  Reframe: "close — here's the piece that's different" or "that's a common
  mix-up, here's why."
- Never claim mastery on the learner's behalf ("you've got this down") unless
  they've actually demonstrated it across the conversation.

Escalation script:
If the learner expresses real frustration, repeated failure, or says
something like "I'm just stupid" — stop teaching, acknowledge directly
("that frustration is normal, this stuff is genuinely hard"), offer a break,
and suggest a human mentor/instructor for anything beyond a quick concept
check. Do not diagnose, do not push through.

STYLE
Short sentences (under ~20 words) — this is spoken, not read. No bulleted
lists out loud; if you'd write a list, turn it into "first... then... and
finally" spoken naturally. Pace: pause after introducing a new term to let it
land. On silence (2-3s): re-prompt once with a simpler question, not a repeat
of the same one. On a second silence: offer to pause the session rather than
looping.

VOICE REALISM
- Use filler words sparingly (1 per 2-3 sentences max), never stacked.
- Self-correct when introducing new concepts, not when stating known facts —
  e.g. "so RAG retrieves the — actually, let's back up, what's a vector?"
- Emotion adjusts warmth/pace only — never sharpness or the content of a
  correction, even if the learner is being difficult or repeats a mistake.
- Light non-verbal acknowledgments only (mm-hm, brief laugh at a genuine
  mix-up) — no sighs or exhales, they read as judgmental against a no-shame
  guardrail.
- Recurring behavior: restate the question before answering it ("okay, why
  does backprop need the chain rule — good one"); lead with an analogy before
  the formal term.
- Never repeat the same opener or affirmation phrase in back-to-back turns —
  vary "so basically / here's the thing / okay so" and "exactly / right /
  yeah that's it."""


def load_exercises():
    exercises_path = os.path.join(os.path.dirname(__file__), "exercises.json")
    if os.path.exists(exercises_path):
        with open(exercises_path, encoding="utf-8") as f:
            return json.load(f)
    return []


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    @function_tool
    async def lookup_caller(self, context: RunContext, user_id: str) -> str:
        """Look up stored information about the current caller by their user_id or phone number.

        Args:
            user_id: The unique identifier or phone number of the caller.
        """
        caller_info = db.get_caller(user_id)
        if caller_info:
            return (
                f"Caller Info for {user_id}: Name={caller_info.get('name')}, "
                f"Last Topic={caller_info.get('last_topic')}, Facts={caller_info.get('facts')}, "
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
        """Save or update facts, name, or last studied topic for the caller in memory.

        Args:
            user_id: Caller's user ID or phone number.
            name: Caller's name if provided.
            last_topic: The topic/concept covered in this session.
            fact: Any notable fact or preference to remember about the caller.
        """
        db.save_caller(
            user_id=user_id,
            name=name,
            last_topic=last_topic,
            facts=fact,
            opted_out=False,
        )
        return f"Updated memory for caller {user_id}."

    @function_tool
    async def fetch_next_exercise(
        self, context: RunContext, topic: Optional[str] = None
    ) -> str:
        """Fetch the next AI/ML concept practice question for the learner.

        Args:
            topic: Optional specific concept topic to retrieve an exercise for.
        """
        exercises = load_exercises()
        if not exercises:
            return "No practice exercises are currently available."

        if topic:
            matching = [
                e for e in exercises if topic.lower() in e.get("topic", "").lower()
            ]
            if matching:
                ex = matching[0]
                return f"Topic: {ex['topic']}\nQuestion: {ex['question']}\nHint: {ex['hints'][0]}"

        ex = exercises[0]
        return (
            f"Topic: {ex['topic']}\nQuestion: {ex['question']}\nHint: {ex['hints'][0]}"
        )

    @function_tool
    async def opt_out_caller(self, context: RunContext, user_id: str) -> str:
        """Opt the caller out of daily practice calls and unsubscribe them from future sessions.

        Args:
            user_id: The phone number or user ID of the caller opting out.
        """
        db.save_caller(user_id=user_id, opted_out=True)
        return f"Caller {user_id} has been opted out and unsubscribed from future practice calls."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3", language="multi"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
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

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
