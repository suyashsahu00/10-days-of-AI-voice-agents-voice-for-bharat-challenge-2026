# Day 9 – Hand Off to a Specialist Agent

Your main agent can do many things. But one agent should not try to be an expert at everything. Today, you will create a specialist agent and let your main agent hand the conversation to it when needed.

You can complete this task with your browser-based agent.

> **Using the Murf LiveKit Starter?** You can refer to our [agent handoff example project](https://github.com/murf-ai/murf-livekit-starter/tree/agent-handoff). It shows how to add a specialist agent and hand the conversation to it. You can use this example as a guide and change the agents for your own track.

For Day 9, your objective is to:

- **Step 1: Choose one specialist for your track.** Give the specialist one clear job.

  Examples:

  | Track               | Specialist agent                  |
  | ------------------- | --------------------------------- |
  | Farm & Field        | Crop problem specialist           |
  | Health Access       | Clinic and appointment specialist |
  | Learning & Literacy | Maths practice specialist         |
  | Local Commerce      | Returns and refunds specialist    |
  | Financial Services  | Government scheme specialist      |
  | Disaster Response   | Shelter information specialist    |

- **Step 2: Create the specialist as a separate agent.** Give it its own instructions, role, and limits. Keep its job smaller and more focused than the main agent's job.

- **Step 3: Add a handoff tool to the main agent.** The main agent should use this tool when the user's request needs the specialist. Write a clear tool description so the main agent knows when to use it.

- **Step 4: Pass the conversation to the specialist.** The specialist should know what the user asked and continue the same conversation. The user should not have to explain the full problem again.

- **Step 5: Make the handoff clear to the user.** Before switching, the main agent should say something simple, such as: "I will connect you to our crop specialist." The specialist should introduce itself after taking over.

- **Step 6: Test both paths.** Ask one normal question that the main agent can answer. Then ask one question that needs the specialist. The main agent should hand off only the second question.

- **Step 7: Record a short video** showing the user asking for specialist help, the main agent announcing the handoff, and the specialist continuing the conversation.

- **Step 8: Post the video on LinkedIn** with a description of what you built on Day 9. Mention that you're building a voice agent using the fastest TTS API — **Murf Falcon**. Mention that you're part of **10 Days of Voice Agents** and don't forget to tag the official **Murf AI** handle. Also use the hashtag **#VoiceForBharat**.

- **Step 9: Submit your post link** using the submission form shared on Discord.

## Advanced (Optional)

You only need one working specialist and one handoff to complete Day 9. Try these if you want to do more:

- **Hand back to the main agent.** Let the specialist return the conversation when its work is complete or the user changes the topic.
- **Add more specialists.** Create two or three specialists and route each request to the correct one.
- **Share useful data.** Pass saved user details and tool results to the specialist without asking for them again.
- **Handle a failed handoff.** If the specialist cannot start, let the main agent explain the problem and continue helping.
- **Test your routing.** Write ten sample user requests and check that each one stays with the main agent or goes to the correct specialist.

### You've finished Day 9 if:

- Your main agent and specialist agent have different, clear jobs
- The main agent hands off only when the user's request needs the specialist
- The user is told when the handoff happens
- The specialist understands the request and continues the conversation
- A normal question stays with the main agent

Once your agent handoff is working, your LinkedIn post is live, and your form submission is complete, you've finished Day 9.

## Resources

- [Agent Handoff Example Project](https://github.com/murf-ai/murf-livekit-starter/tree/agent-handoff)
- [Agent Handoff Example Project Instructions](https://github.com/murf-ai/murf-livekit-starter/tree/agent-handoff/backend#agent-handoff)
- [LiveKit Agents and Handoffs](https://docs.livekit.io/agents/logic/agents-handoffs/)
- [LiveKit Multi-Agent Python Example](https://github.com/livekit-examples/multi-agent-python)
- [LiveKit Tools](https://docs.livekit.io/agents/logic/tools/)
