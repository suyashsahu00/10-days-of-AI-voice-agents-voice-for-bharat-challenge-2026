# Day 8 – Build a Call Analytics Dashboard

Your agent can now handle conversations, remember users, use tools, make calls, and ask humans for help. Today, you will build a simple dashboard to see how it is performing.

You can connect the dashboard to your browser-based agent, your SIP agent, or both.

For Day 8, your objective is to:

- **Step 1: Decide what a successful call means for your agent.** Use the objectives you defined on Day 2. Keep the definition simple and specific.

  Examples:	

  | Track               | A successful call could mean                                                |
  | ------------------- | --------------------------------------------------------------------------- |
  | Farm & Field        | The farmer receives the requested price or weather information              |
  | Health Access       | The caller receives safe guidance or an appropriate escalation              |
  | Learning & Literacy | The learner completes an exercise                                           |
  | Local Commerce      | The caller finds a product or completes an enquiry                          |
  | Financial Services  | The caller completes an eligibility check or receives a document list       |
  | Disaster Response   | The caller receives verified information or a human-help request is created |
- **Step 2: Record the outcome of every call.** When a call ends, save whether it was successful or failed. A failed call does not necessarily mean that something broke. It means the call did not reach the success condition you defined. For example, a learner may refuse to complete a lesson, or a caller may end the conversation before finishing their enquiry. You may use the database you added on Day 4 or any other database.
- **Step 3: Build a simple web dashboard.** It must show these three numbers:

  - **Total calls**
  - **Successful calls**
  - **Failed calls**
- **Step 4: Use real data from your agent.** The numbers must come from actual browser or SIP calls. Do not hardcode the values shown on the dashboard.
- **Step 5: Test the success path.** Make at least one successful call. Check that the total calls and successful calls increase on the dashboard.
- **Step 6: Protect caller information.** Do not display passwords, OTPs, PINs, account numbers, medical details, or full conversation transcripts on a public dashboard.
- **Step 7: Record a short video** showing a successful call and the total calls and successful calls increasing on the dashboard.
- **Step 8: Post the video on LinkedIn** with a description of what you built on Day 8. Mention that you're building a voice agent using the fastest TTS API — **Murf Falcon**. Mention that you're part of **10 Days of Voice Agents** and don't forget to tag the official **Murf AI** handle. Also use the hashtag **#VoiceForBharat**.
- **Step 9: Submit your post link** using the submission form shared on Discord.

## Advanced (Optional)

You only need the three required metrics to complete Day 8. Try these if you want to build more:

- **Test the failure path.** Make a call that does not reach its success condition and show the failed calls count increasing.
- **Failure types.** Group failures into categories such as the user declining to continue, an incomplete task, a tool failure, an API error, no response, or a user hang-up.
- **Success rate.** Show the percentage of calls that completed successfully.
- **Call history.** Show recent calls with their time, duration, channel, and outcome.
- **Track-specific outcomes.** Track leads, completed exercises, eligibility checks, escalations, orders, or another result that matters for your agent.
- **Filters and charts.** Filter by date, language, browser or SIP, and show how results change over time.
- **Live updates.** Refresh the dashboard automatically when a call ends.
- **Latency.** Track how long the agent takes to begin speaking after the user finishes.

### You've finished Day 8 if:

- Your dashboard is connected to real call data
- It shows total, successful, and failed calls
- You have defined what success means for your agent
- At least one successful test call increases the total and successful call counts
- The dashboard does not expose sensitive caller information

Once your dashboard is working, your LinkedIn post is live, and your form submission is complete, you've finished Day 8.

## Resources

- [LiveKit Webhooks](https://docs.livekit.io/home/server/webhooks/)
- [Python SQLite](https://docs.python.org/3/library/sqlite3.html)
- [Chart.js](https://www.chartjs.org/docs/latest/)
