import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, jsonify

import db

app = Flask(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Sydney — Call Analytics</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #050507;
    color: #f2f3f7;
    font-family: 'Helvetica Neue', Arial, sans-serif;
    min-height: 100vh;
    padding: 40px 24px;
  }
  .header {
    text-align: center;
    margin-bottom: 48px;
  }
  .header h1 {
    font-size: 2rem;
    font-weight: 400;
    letter-spacing: -0.3px;
  }
  .header p {
    margin-top: 8px;
    color: rgba(242,243,247,0.5);
    font-size: 0.9rem;
  }
  .cards {
    display: flex;
    justify-content: center;
    gap: 24px;
    flex-wrap: wrap;
    margin-bottom: 48px;
  }
  .card {
    background: rgba(18,18,26,0.6);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 32px 40px;
    text-align: center;
    min-width: 180px;
    backdrop-filter: blur(10px);
  }
  .card .label {
    font-size: 0.78rem;
    letter-spacing: 1.4px;
    color: rgba(242,243,247,0.5);
    font-weight: 600;
    text-transform: uppercase;
    margin-bottom: 12px;
  }
  .card .number {
    font-size: 3rem;
    font-weight: 700;
    line-height: 1;
  }
  .card.total .number  { color: #8fa4ff; }
  .card.success .number { color: #7ee8c8; }
  .card.failed .number  { color: #ff8fb3; }
  .section-title {
    text-align: center;
    font-size: 0.78rem;
    letter-spacing: 1.4px;
    color: rgba(242,243,247,0.5);
    font-weight: 600;
    text-transform: uppercase;
    margin-bottom: 16px;
  }
  .history {
    max-width: 700px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .row {
    background: rgba(18,18,26,0.5);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 14px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0.88rem;
  }
  .row .user { color: rgba(242,243,247,0.6); font-size: 0.78rem; }
  .row .time { color: rgba(242,243,247,0.4); font-size: 0.75rem; }
  .badge {
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
  }
  .badge.success { background: rgba(126,232,200,0.15); color: #7ee8c8; }
  .badge.failed  { background: rgba(255,143,179,0.15); color: #ff8fb3; }
  .refresh {
    display: block;
    margin: 32px auto 0;
    background: rgba(18,18,26,0.6);
    border: 1px solid rgba(255,255,255,0.1);
    color: rgba(242,243,247,0.7);
    padding: 10px 28px;
    border-radius: 999px;
    font-size: 0.88rem;
    cursor: pointer;
  }
  .refresh:hover { border-color: #8fa4ff; color: #f2f3f7; }
</style>
</head>
<body>
<div class="header">
  <h1>Sydney — Call Analytics</h1>
  <p>Learning &amp; Literacy · Voice for Bharat</p>
</div>

<div class="cards" id="cards">
  <div class="card total">
    <div class="label">Total Calls</div>
    <div class="number" id="total">—</div>
  </div>
  <div class="card success">
    <div class="label">Successful</div>
    <div class="number" id="successful">—</div>
  </div>
  <div class="card failed">
    <div class="label">Failed</div>
    <div class="number" id="failed">—</div>
  </div>
</div>

<div class="section-title">Recent Calls</div>
<div class="history" id="history"></div>

<div style="display: flex; justify-content: center; gap: 16px; margin-top: 32px;">
  <button class="refresh" style="margin: 0;" onclick="load()">Refresh</button>
  <button class="refresh" style="margin: 0; border-color: rgba(255,143,179,0.3); color: #ff8fb3;" onclick="resetData()">Reset Data</button>
</div>

<script>
async function load() {
  const res = await fetch('/api/stats');
  const data = await res.json();
  document.getElementById('total').textContent = data.total;
  document.getElementById('successful').textContent = data.successful;
  document.getElementById('failed').textContent = data.failed;

  const history = document.getElementById('history');
  history.innerHTML = '';
  if (!data.recent.length) {
    history.innerHTML = '<div style="text-align:center;color:rgba(242,243,247,0.3);font-size:0.85rem;">No calls yet.</div>';
    return;
  }
  data.recent.forEach(c => {
    const uid = c.user_id
      ? c.user_id.substring(0, 8) + '...'
      : 'unknown';
    const time = c.ended_at || '';
    const badge = c.outcome === 'success'
      ? '<span class="badge success">Success</span>'
      : '<span class="badge failed">Failed</span>';
    history.innerHTML += `
      <div class="row">
        <div>
          <div>${c.room_name || 'Unknown room'}</div>
          <div class="user">User: ${uid}</div>
          <div class="time">${time}</div>
        </div>
        ${badge}
      </div>`;
  });
}
async function resetData() {
  if (!confirm('Are you sure you want to reset all call analytics data?')) return;
  await fetch('/api/reset', { method: 'POST' });
  load();
}
load();
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return DASHBOARD_HTML


@app.route("/api/stats")
def stats():
    data = db.get_call_stats()
    return jsonify(data)


@app.route("/api/reset", methods=["POST"])
def reset():
    db.reset_calls()
    return jsonify({"status": "success"})


if __name__ == "__main__":
    print("Dashboard running at http://localhost:8080")
    app.run(host="0.0.0.0", port=8080, debug=False)
