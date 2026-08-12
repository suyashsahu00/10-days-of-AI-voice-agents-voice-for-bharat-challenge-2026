# Day 7 – Know When to Ask for Human Help

Your agent can now remember users, use real data, and make outbound calls. But it should not try to solve every problem on its own. Today, you will teach it when and how to ask a human for help.

You do not need SIP calls for this task. You can complete it using your browser-based agent.

For Day 7, your objective is to:

- **Step 1: Choose two reasons for human help.** Pick situations where your agent should stop and create a request for a human.

  Examples for each track:

  | Track               | When to ask for human help                                                   |
  | ------------------- | ---------------------------------------------------------------------------- |
  | Farm & Field        | The market data is missing or old; the farmer reports a serious crop problem |
  | Health Access       | The caller has a red-flag symptom or asks for a diagnosis                    |
  | Learning & Literacy | The learner is upset or needs help from a teacher                            |
  | Local Commerce      | The caller has a payment, refund, or order dispute                           |
  | Financial Services  | The caller reports possible fraud or needs a decision the agent cannot make  |
  | Disaster Response   | The caller is trapped, injured, or needs urgent local help                   |

- **Step 2: Build a human-help tool.** Add a function such as `create_escalation`. The agent should call it when one of your chosen situations happens.

- **Step 3: Create a short summary for the human.** Save only the useful details:
  - Who needs help
  - What happened
  - What the agent already checked
  - How urgent it is
  - The caller's language and preferred follow-up method

  Do not send the full conversation unless it is needed. Do not include passwords, OTPs, PINs, account numbers, or other private information.

- **Step 4: Ask before sharing.** Tell the caller what information you want to send and ask for permission. If they say no, do not create the request.

- **Step 5: Send the request somewhere real.** You can use email, Slack, Discord, a webhook, a help-desk tool, or a simple dashboard. A local database with a page that shows open requests is also acceptable.

- **Step 6: Give the caller a clear next step.** After the request is created, give them a reference ID. Explain what will happen next. Do not promise that a human will reply immediately unless that is true.

- **Step 7: Test both paths.** Have one conversation that needs human help and one normal conversation that does not. The agent should create a request only when it is needed.

- **Step 8: Record a short video** showing the agent finding the problem, asking for permission, creating the request, and showing the request to the human.

- **Step 9: Post the video on LinkedIn** with a description of what you built on Day 7. Mention that you're building a voice agent using the fastest TTS API — **Murf Falcon**. Mention that you're part of **10 Days of Voice Agents** and don't forget to tag the official **Murf AI** handle. Also use the hashtag **#VoiceForBharat**.

- **Step 10: Submit your post link** using the submission form shared on Discord.

## Advanced (Optional)

You only need the steps above to complete Day 7. Try these if you want to do more:

- **Add urgency levels.** Mark requests as low, medium, high, or emergency.
- **Remove private information.** Check the summary and remove sensitive details before sending it.
- **Stop duplicate requests.** If the same problem is already open, update it instead of creating another one.
- **Show the request status.** Let the user see if the request is open, in progress, or resolved.
- **Call back after resolution.** Use the outbound calling work from Day 6 to tell the user when the problem is resolved.

### You've finished Day 7 if:

- The agent knows when it needs human help
- It asks for permission before sharing the caller's information
- It creates a real request with a short and useful summary
- It gives the caller a reference ID and an honest next step
- A normal conversation does not create an unnecessary request

Once your agent is working, your LinkedIn post is live, and your form submission is complete, you've finished Day 7.

## Resources

- [LiveKit Tool Definition and Use](https://docs.livekit.io/agents/logic/tools/)
- [LiveKit External Data and RAG](https://docs.livekit.io/agents/build/external-data/)
- [Discord Webhooks](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks)
