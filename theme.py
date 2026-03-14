from __future__ import annotations

APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
:root {
  --bg: #07111f;
  --panel: #0d1b2a;
  --panel-2: #10233b;
  --stroke: #1d3557;
  --text: #e5eef9;
  --muted: #7d93b2;
  --blue: #4ea3ff;
  --green: #34d399;
  --amber: #f59e0b;
  --red: #ef4444;
}
.stApp {background: radial-gradient(circle at top left, #0f1f36, #07111f 50%); color: var(--text); font-family: 'Inter', sans-serif;}
[data-testid='stSidebar'] {background: linear-gradient(180deg,#081525,#0c1729); border-right: 1px solid var(--stroke);}
.block-container {padding-top: 1.25rem; padding-bottom: 2rem;}
.hero {
  background: linear-gradient(135deg, rgba(17,38,66,0.95), rgba(8,21,37,0.98));
  border: 1px solid rgba(78,163,255,0.25);
  border-radius: 18px;
  padding: 1.35rem 1.5rem;
  margin-bottom: 1rem;
  box-shadow: 0 20px 60px rgba(0,0,0,0.18);
}
.hero h1 {margin: 0; font-size: 1.8rem; color: var(--text);}
.hero p {margin: 0.35rem 0 0 0; color: var(--muted);}
.badge {display:inline-block; margin: 0.35rem 0.35rem 0 0; padding: 0.22rem 0.55rem; border-radius: 999px; border:1px solid rgba(78,163,255,.25); color: #b5d7ff; font-size: .72rem;}
.panel {background: rgba(12,23,41,0.88); border:1px solid rgba(125,147,178,.15); border-radius: 16px; padding: 1rem; margin-bottom: 1rem;}
.metric-box {background: rgba(7,17,31,0.88); border:1px solid rgba(125,147,178,.15); border-radius: 14px; padding: .8rem .95rem; min-height: 96px;}
.metric-label {color: var(--muted); font-size: .75rem; text-transform: uppercase; letter-spacing: .08em;}
.metric-value {color: var(--text); font-weight: 700; font-size: 1.3rem; margin-top: .4rem;}
.note-card {background: rgba(16,35,59,.7); border-left: 4px solid var(--blue); padding: .8rem .95rem; border-radius: 12px; color: #d9e8fb;}
.risk-red {color: var(--red);} .risk-amber {color: var(--amber);} .risk-green {color: var(--green);} .risk-blue {color: var(--blue);}
.stButton>button, .stDownloadButton>button {border-radius: 12px; border: 1px solid rgba(78,163,255,.35); background: linear-gradient(180deg,#163356,#10233b); color:#e8f2ff; font-weight:600;}
.stButton>button:hover, .stDownloadButton>button:hover {border-color: rgba(78,163,255,.6); color:#fff;}
[data-baseweb='tab-list'] {gap: .25rem;}
[data-baseweb='tab'] {background: rgba(7,17,31,.45); border-radius: 10px 10px 0 0; padding: .7rem .9rem;}
[data-baseweb='tab'][aria-selected='true'] {background: rgba(16,35,59,.95);}
.small-muted {color: var(--muted); font-size: .82rem;}
</style>
"""
