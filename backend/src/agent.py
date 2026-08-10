import json
import logging
import random
from pathlib import Path

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    ChatContext,
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

from db import get_caller, init_db, save_caller

logger = logging.getLogger("agent")

load_dotenv(".env.local")

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

MEMORY & CONSENT
- Before calling remember_caller_fact, say so out loud and wait for a yes —
  e.g. "Main yeh yaad rakh loon, next time se continue kar sakein?"
- If they decline, do not call the tool. Continue the conversation normally,
  do not ask again in the same call.
- Only store facts relevant to their AI/ML learning: current_level,
  topics_covered, common_mistakes. Nothing else.

EXERCISES
- Once the learner has just correctly explained or clearly grasped a concept
  in the conversation, proactively offer a quick practice exercise using
  fetch_next_exercise — don't wait to be asked.
- Do not offer an exercise before a concept has actually landed, and never
  offer two exercises back to back without a concept explanation in between.
- Speak the exercise question naturally, as if you thought of it yourself —
  never read it out with any JSON/list formatting or say "the data says."
- If the tool reports the practice set is unavailable, say so plainly in one
  short sentence and move straight into talking through the concept verbally
  instead of stalling or inventing a question.
- Data note: this is a static, hand-built practice set, not a live feed —
  no need to mention "today's" or "latest," just call it "my practice set."

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


class Assistant(Agent):
    def __init__(self, chat_ctx: ChatContext, user_id: str) -> None:
        super().__init__(instructions=SYSTEM_PROMPT, chat_ctx=chat_ctx)
        self.user_id = user_id

    @function_tool
    async def lookup_caller(self, context: RunContext) -> str:
        """Use this if you're unsure what you already know about the caller,
        or want to double check a fact before referencing it."""
        caller = get_caller(self.user_id)
        return (
            json.dumps(caller) if caller else "No record found — this is a new caller."
        )

    @function_tool
    async def remember_caller_fact(
        self,
        context: RunContext,
        name: str,
        language_preference: str,
        facts: dict,
    ) -> str:
        """Save what you just learned about the caller.
        Only call this after you have explicitly asked permission and the
        caller said yes. facts should be short key-value pairs about their
        learning progress only — e.g. current_level, topics_covered,
        common_mistakes. Never store unrelated personal information.

        Args:
            name: the caller's name
            language_preference: their preferred language, e.g. "Hindi", "English", "Hinglish"
            facts: dict of learning-relevant facts to remember
        """
        save_caller(self.user_id, name, language_preference, facts)
        logger.info(f"Saved facts for {self.user_id}")
        return "Saved."

    @function_tool
    async def fetch_next_exercise(
        self,
        context: RunContext,
        level: str,
        topic: str | None = None,
    ) -> str:
        """Fetch a practice exercise for the learner from Sydney's static
        practice set. Call this PROACTIVELY, without being asked, once the
        learner has just demonstrated understanding of a concept in
        conversation — offer it as a natural next step, e.g. "chalo isko
        thoda test karte hain." Do not call this at the start of a call or
        mid-explanation, only after a concept has actually landed.

        Args:
            level: the learner's current level — one of "beginner",
                "intermediate", "advanced". Infer this from how the
                conversation has gone so far, or ask if unclear.
            topic: optional, one of "RAG", "backprop", "embeddings",
                "LangGraph", "chunking". Omit to get any topic at that level.
        """
        try:
            path = Path(__file__).parent / "exercises.json"
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            pool = [e for e in data["exercises"] if e["level"] == level.lower()]
            if topic:
                topic_pool = [e for e in pool if e["topic"].lower() == topic.lower()]
                if topic_pool:
                    pool = topic_pool

            if not pool:
                return (
                    f"No exercise found for level '{level}'"
                    + (f" and topic '{topic}'" if topic else "")
                    + ". Tell the learner you don't have a matching exercise "
                    "right now and offer to just talk through the concept instead."
                )

            exercise = random.choice(pool)
            return (
                f"Exercise from Sydney's practice set: {exercise['question']} "
                f"(Hint if they get stuck: {exercise['hint']}) "
                "Ask this naturally in conversation, don't read it robotically. "
                "Do not give away the hint unless they're stuck."
            )

        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            logger.warning(f"fetch_next_exercise failed: {e}")
            return (
                "The practice set is unavailable right now. Tell the learner, "
                "in your own natural voice, that you can't pull a structured "
                "question at the moment, and offer to just talk through the "
                "concept together instead — do not invent a fake exercise."
            )


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    init_db()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    await ctx.connect()
    participant = await ctx.wait_for_participant()
    user_id = participant.identity

    caller = get_caller(user_id)

    initial_ctx = ChatContext()
    if caller:
        initial_ctx.add_message(
            role="assistant",
            content=(
                f"Returning caller. Name: {caller['name']}. "
                f"Language preference: {caller['language_preference']}. "
                f"Known facts: {json.dumps(caller['facts'])}. "
                "Greet them by name and reference something specific from what "
                "you already know, then ask a natural follow-up before continuing."
            ),
        )
    else:
        initial_ctx.add_message(
            role="assistant",
            content="New caller, no record exists yet. This is a first-time introduction.",
        )

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
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
        agent=Assistant(chat_ctx=initial_ctx, user_id=user_id),
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


if __name__ == "__main__":
    cli.run_app(server)
