# Day 4 – Give Your Agent a Memory That Lasts

Your voice agent can now talk, follow a role and show all of this through a proper frontend. But it forgets everyone the moment a call ends. Today, you will make it remember people.


For Day 4, your objective is to:

* **Step 1: Add a database to save your data.** SQLite is simple and good enough. You can use Postgres or Mongo instead if you already know them, but you do not have to.
* **Step 2: Save who the caller is and a few facts about them.** At the least, store their name and an ID so you can find them again later. Then add 2 to 4 facts that matter for your track. A saved record can look like this:

```json
{
  "user_id": "string",
  "name": "string",
  "language_preference": "string",
  "facts": { "key": "value" },
  "last_interaction": "timestamp"
}
```

  Examples of facts worth saving for each track:

  | Track | Facts to save |
  | --- | --- |
  | Farm & Field | Crops grown, land size, district, irrigation type |
  | Health Access | Age band, ongoing conditions, last triage outcome. Do not store written-out medical notes |
  | Learning & Literacy | Current level, topics covered, mistakes they keep making |
  | Local Commerce | Past orders, usual quantities, preferred delivery slot |
  | Financial Services | Schemes already checked, eligibility answers. Do not store account or ID numbers |
  | Disaster Response | Location, household size, mobility needs, last check-in |

* **Step 3: Let the agent read and write this data through functions, not the prompt.** Give it one function to look a caller up and one to save what it just learned. The agent should call these itself when it needs them.
* **Step 4: Greet returning callers by name.** When the agent already knows someone, it should welcome them back and continue from last time. For example: "Namaste Ramesh, last time we spoke about your cotton. Did the spraying help?"
* **Step 5: Ask before you save anything.** Tell the caller you are going to remember this, and if they say no, do not save it. For Financial Services and Health Access this is a hard rule. Saving something you should not means you are out.
* **Step 6: Test the full flow.** Call your agent, tell it something about yourself, and hang up. Then call again and check that it remembers you.
* **Step 7: Record a short video of both calls one after the other, so the difference is clear.** In the first call the agent does not know you, and in the second call it does.
* **Step 8: Post the video on LinkedIn with a description of what you built on Day 4.** Mention that you're building a voice agent using the fastest TTS API — **Murf Falcon**. Mention that you're part of **10 Days of Voice Agents** and don't forget to tag the official Murf AI handle. Also use the hashtag **#VoiceForBharat**.
* **Step 9: Submit your post link using the submission form shared on Discord.**

## Advanced (Optional)
You only need the steps above to complete Day 4. Try these if you want to do more:

* Async retrieval. Look the caller up while the agent is still talking, so there is no silence during the lookup.
* A "forget me" tool. Let the caller ask to be forgotten, wipe their record, and show it working.
* RAG over a knowledge base. Ground the agent's answers in real documents such as scheme PDFs, crop advisories, or syllabus material.

## Handling Multilocale Messages

If your agent understands Hindi but speaks it in an English accent, it's because the wrong language settings are used. 

Here is how to fix it.

If you are using the LiveKit starter, set up your session in `agent.py` like this:

```python
session = AgentSession(
    stt=deepgram.STT(model="nova-3", language="multi"),  # set "multi" to detect non-English speech
    llm=google.LLM(
        model="gemini-3.5-flash-lite",
    ),
    tts=murf.TTS(
        voice="Anisha",  # do not hardcode the locale key
        style="Conversation",
        tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
        text_pacing=True,
    ),
    turn_detection=MultilingualModel(),
    vad=ctx.proc.userdata["vad"],
    preemptive_generation=True,
)
```

Also tell your LLM to always reply in the correct script for each language. Add something like this to your prompt:

```
LANGUAGE & SCRIPT
Always write every language in its own native script.
- Hindi → Devanagari (नमस्ते), never romanized (never "namaste").
- Same rule for all non-English languages.
```


You've finished Day 4 if:

* The data is still there after you fully restart the agent
* The agent gets a caller's info through a function, not the prompt
* A second call from the same person clearly goes better than the first
* The agent asks before it saves, and drops it when the caller says no

Once your agent is working, your LinkedIn post is live, and your form submission is complete, you've finished Day 4.
Resources

* [Tool Definition and Use](https://docs.livekit.io/agents/build/tools/)
* [External Data and RAG](https://docs.livekit.io/agents/build/external-data/)
* [Python SQLite](https://docs.python.org/3/library/sqlite3.html)
* [MongoDB with Python](https://www.mongodb.com/languages/python)
