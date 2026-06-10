import streamlit as st
import pandas as pd
import requests
import json
import time
import os
from datetime import datetime

st.set_page_config(
    page_title="Index Checker — gambling.com",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* Page background */
.stApp { background: #f4f6f9; }

/* Hide default streamlit header padding */
.block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; }

/* ── Stat cards ── */
.stat-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 12px;
    margin-bottom: 1.5rem;
}
.stat-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 18px 16px 14px;
    border: 1px solid #e8eaed;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.stat-card .label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #8a94a6;
    margin-bottom: 8px;
}
.stat-card .value {
    font-size: 26px;
    font-weight: 700;
    color: #1a1f36;
    line-height: 1;
    margin-bottom: 6px;
}
.stat-card .sub {
    font-size: 12px;
    color: #8a94a6;
}
.stat-card.green  { border-top: 3px solid #22c55e; }
.stat-card.red    { border-top: 3px solid #ef4444; }
.stat-card.amber  { border-top: 3px solid #f59e0b; }
.stat-card.blue   { border-top: 3px solid #3b82f6; }
.stat-card.purple { border-top: 3px solid #8b5cf6; }
.stat-card.gray   { border-top: 3px solid #94a3b8; }

/* ── Progress bar container ── */
.progress-wrap {
    background: #ffffff;
    border-radius: 12px;
    padding: 16px 20px;
    border: 1px solid #e8eaed;
    margin-bottom: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.progress-label {
    display: flex;
    justify-content: space-between;
    font-size: 13px;
    color: #4b5563;
    margin-bottom: 10px;
    font-weight: 500;
}
.progress-track {
    background: #e9ecef;
    border-radius: 99px;
    height: 10px;
    overflow: hidden;
}
.progress-fill {
    height: 100%;
    border-radius: 99px;
    background: linear-gradient(90deg, #3b82f6, #6366f1);
    transition: width 0.4s ease;
}

/* ── Section card ── */
.section-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 20px 24px;
    border: 1px solid #e8eaed;
    margin-bottom: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.section-title {
    font-size: 14px;
    font-weight: 700;
    color: #1a1f36;
    margin-bottom: 16px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ── Status badge ── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 99px;
    font-size: 12px;
    font-weight: 600;
}
.badge-indexed     { background:#dcfce7; color:#15803d; }
.badge-not_indexed { background:#fee2e2; color:#b91c1c; }
.badge-error       { background:#fef3c7; color:#92400e; }
.badge-pending     { background:#f1f5f9; color:#475569; }

/* ── Running status banner ── */
.running-banner {
    background: linear-gradient(135deg, #eff6ff, #eef2ff);
    border: 1px solid #bfdbfe;
    border-radius: 12px;
    padding: 14px 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 1rem;
    font-size: 14px;
    color: #1e40af;
    font-weight: 500;
}
.pulse-dot {
    width: 10px; height: 10px;
    background: #3b82f6;
    border-radius: 50%;
    animation: pulse 1.2s infinite;
    flex-shrink: 0;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.8); }
}

/* ── Page header ── */
.page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e8eaed;
}
.page-title { font-size: 22px; font-weight: 700; color: #1a1f36; margin: 0; }
.page-sub   { font-size: 13px; color: #8a94a6; margin: 4px 0 0; }

/* Override default streamlit button styles */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    height: 40px !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #1a1f36 !important;
}
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #f1f5f9 !important; }
[data-testid="stSidebar"] .stSlider label,
[data-testid="stSidebar"] .stTextInput label { color: #94a3b8 !important; font-size: 12px !important; }
[data-testid="stSidebar"] hr { border-color: #2d3748 !important; }

/* Dataframe */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

/* Hide default metric delta arrow clutter */
[data-testid="stMetricDelta"] { display: none; }
</style>
""", unsafe_allow_html=True)


# ── Password gate ─────────────────────────────────────────────────────────────

def check_password():
    if st.session_state.get("authenticated"):
        return True

    col = st.columns([1, 1.2, 1])[1]
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='text-align:center; margin-bottom:2rem;'>
            <div style='font-size:40px;'>🔍</div>
            <h2 style='color:#1a1f36; margin:8px 0 4px;'>Index Checker</h2>
            <p style='color:#8a94a6; font-size:14px;'>gambling.com — EN Slot Games</p>
        </div>
        """, unsafe_allow_html=True)
        pwd = st.text_input("Password", type="password", placeholder="Enter password…", label_visibility="collapsed")
        if st.button("Sign in", type="primary", use_container_width=True):
            correct = st.secrets.get("APP_PASSWORD", "")
            if pwd == correct and correct != "":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    return False

if not check_password():
    st.stop()


CSV_FILE    = "en_gx_slot_game_urls.csv"
RESULTS_FILE = "index_results.json"
CHUNK       = 25


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_urls():
    df = pd.read_csv(CSV_FILE)
    df.columns = df.columns.str.strip()
    return df


def load_results():
    if "results" in st.session_state:
        return st.session_state["results"]
    for fname in (RESULTS_FILE, "index_results_backup.json"):
        if os.path.exists(fname):
            with open(fname, "r") as f:
                data = json.load(f)
            st.session_state["results"] = data
            return data
    st.session_state["results"] = {}
    return {}


def save_results(results: dict):
    st.session_state["results"] = results
    try:
        with open(RESULTS_FILE, "w") as f:
            json.dump(results, f, indent=2)
        # Keep a rolling backup so a redeployment doesn't wipe progress
        with open("index_results_backup.json", "w") as f:
            json.dump(results, f, indent=2)
    except OSError:
        pass


def check_url_indexed(url: str, api_key: str) -> dict:
    try:
        params = {"engine": "google", "q": f"site:{url}", "api_key": api_key, "num": 1}
        resp = requests.get("https://serpapi.com/search", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        organic = data.get("organic_results", [])
        return {
            "status": "indexed" if organic else "not_indexed",
            "checked_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "result_count": len(organic),
            "error": None,
        }
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response is not None else 0
        if code == 429:
            return {"status": "error", "error": "rate_limited", "checked_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}
        return {"status": "error", "error": f"HTTP {code}", "checked_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}
    except Exception as e:
        return {"status": "error", "error": str(e)[:80], "checked_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}


def build_summary_df(df, results):
    rows = []
    for _, row in df.iterrows():
        url = row["url"]
        r = results.get(url, {})
        rows.append({
            "url":          url,
            "title":        row.get("title", ""),
            "market":       row.get("market", ""),
            "http_status":  row.get("status", ""),
            "index_status": r.get("status", "pending"),
            "checked_at":   r.get("checked_at", ""),
            "error":        r.get("error", "") or "",
        })
    return pd.DataFrame(rows)


def colour_status(val):
    m = {
        "indexed":     "background-color:#dcfce7;color:#15803d;font-weight:600",
        "not_indexed": "background-color:#fee2e2;color:#b91c1c;font-weight:600",
        "error":       "background-color:#fef3c7;color:#92400e;font-weight:600",
        "pending":     "background-color:#f1f5f9;color:#475569;font-weight:600",
    }
    return m.get(val, "")


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Settings")

    api_key = ""
    try:
        api_key = st.secrets.get("SERP_API_KEY", "")
    except Exception:
        pass

    if api_key:
        st.markdown("""
        <div style='background:#1e3a5f;border-radius:8px;padding:10px 14px;margin-bottom:4px;'>
          <span style='color:#60a5fa;font-size:12px;font-weight:600;'>✓ SERP API KEY</span><br>
          <span style='color:#94a3b8;font-size:11px;'>Loaded from secrets</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        api_key = st.text_input("SERP API Key", type="password",
                                help="Set SERP_API_KEY in Streamlit Cloud secrets to avoid entering it here.")

    st.markdown("---")
    delay_ms = st.slider("Delay between requests (ms)", 200, 3000, 600, 100)
    st.caption(f"~{round(3600000 / delay_ms):,} requests/hour at this setting")

    st.markdown("---")
    st.markdown("**Import saved progress**")
    uploaded = st.file_uploader("Upload JSON", type="json", label_visibility="collapsed")
    if uploaded:
        imported = json.load(uploaded)
        save_results(imported)
        st.success(f"Imported {len(imported):,} results.")
        st.rerun()

    st.markdown("---")
    if st.button("🗑️ Clear all results", use_container_width=True):
        st.session_state["results"] = {}
        st.session_state["running"] = False
        st.session_state["recheck_errors"] = False
        if os.path.exists(RESULTS_FILE):
            os.remove(RESULTS_FILE)
        st.rerun()

    st.markdown("---")
    st.markdown(f"<p style='font-size:11px;color:#64748b;'>Last updated: {datetime.utcnow().strftime('%H:%M UTC')}</p>",
                unsafe_allow_html=True)


# ── Load data ─────────────────────────────────────────────────────────────────

try:
    df = load_urls()
except FileNotFoundError:
    st.error(f"`{CSV_FILE}` not found. Make sure it's committed to the repo.")
    st.stop()

results    = load_results()
summary_df = build_summary_df(df, results)

total       = len(summary_df)
indexed     = int((summary_df["index_status"] == "indexed").sum())
not_indexed = int((summary_df["index_status"] == "not_indexed").sum())
errors      = int((summary_df["index_status"] == "error").sum())
pending     = int((summary_df["index_status"] == "pending").sum())
checked     = total - pending
pct_done    = round(checked / total * 100, 1) if total else 0
idx_rate    = round(indexed / checked * 100, 1) if checked else 0

running        = st.session_state.get("running", False)
recheck_errors = st.session_state.get("recheck_errors", False)


# ── Page header ───────────────────────────────────────────────────────────────

st.markdown(f"""
<div class="page-header">
  <div>
    <p class="page-title">🔍 Google Index Checker</p>
    <p class="page-sub">gambling.com · EN Slot Games · {total:,} URLs</p>
  </div>
  <div style="font-size:13px;color:#8a94a6;">
    {'<span style="color:#22c55e;font-weight:600;">● Running</span>' if running else '<span style="color:#94a3b8;">● Idle</span>'}
  </div>
</div>
""", unsafe_allow_html=True)


# ── Stat cards ────────────────────────────────────────────────────────────────

st.markdown(f"""
<div class="stat-grid">
  <div class="stat-card blue">
    <div class="label">Total URLs</div>
    <div class="value">{total:,}</div>
    <div class="sub">in dataset</div>
  </div>
  <div class="stat-card purple">
    <div class="label">Checked</div>
    <div class="value">{checked:,}</div>
    <div class="sub">{pct_done}% complete</div>
  </div>
  <div class="stat-card green">
    <div class="label">Indexed</div>
    <div class="value">{indexed:,}</div>
    <div class="sub">{idx_rate}% of checked</div>
  </div>
  <div class="stat-card red">
    <div class="label">Not Indexed</div>
    <div class="value">{not_indexed:,}</div>
    <div class="sub">{round(not_indexed/checked*100,1) if checked else 0}% of checked</div>
  </div>
  <div class="stat-card amber">
    <div class="label">Errors</div>
    <div class="value">{errors:,}</div>
    <div class="sub">need recheck</div>
  </div>
  <div class="stat-card gray">
    <div class="label">Pending</div>
    <div class="value">{pending:,}</div>
    <div class="sub">not yet checked</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Progress bar ──────────────────────────────────────────────────────────────

fill_pct = round(checked / total * 100, 2) if total else 0
st.markdown(f"""
<div class="progress-wrap">
  <div class="progress-label">
    <span>Overall progress</span>
    <span><strong>{checked:,}</strong> / {total:,} URLs checked</span>
  </div>
  <div class="progress-track">
    <div class="progress-fill" style="width:{fill_pct}%"></div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Controls ──────────────────────────────────────────────────────────────────

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Controls</div>', unsafe_allow_html=True)

col_start, col_recheck, col_stop, col_save = st.columns([2, 2, 1, 1])

with col_start:
    if st.button(
        "▶  Start index check" if not running else "▶  Running…",
        type="primary",
        disabled=running or not api_key or pending == 0,
        use_container_width=True,
    ):
        st.session_state["running"] = True
        st.session_state["recheck_errors"] = False
        st.rerun()

with col_recheck:
    if st.button(
        f"🔄  Recheck {errors:,} errors",
        disabled=running or not api_key or errors == 0,
        use_container_width=True,
    ):
        st.session_state["running"] = True
        st.session_state["recheck_errors"] = True
        st.rerun()

with col_stop:
    if st.button("⏹  Stop", disabled=not running, use_container_width=True):
        st.session_state["running"] = False
        st.session_state["recheck_errors"] = False
        st.rerun()

with col_save:
    st.download_button(
        "💾  Save JSON",
        data=json.dumps(results, indent=2).encode("utf-8"),
        file_name=f"index_results_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
        mime="application/json",
        use_container_width=True,
        disabled=len(results) == 0,
    )

st.markdown("</div>", unsafe_allow_html=True)


# ── Auto-run loop ─────────────────────────────────────────────────────────────

if running:
    queue = (
        summary_df[summary_df["index_status"] == "error"]["url"].tolist()
        if recheck_errors
        else summary_df[summary_df["index_status"] == "pending"]["url"].tolist()
    )

    if not queue:
        st.session_state["running"] = False
        st.session_state["recheck_errors"] = False
        st.success("✅ All URLs checked! Download your results below.")
        st.rerun()

    chunk = queue[:CHUNK]
    remaining = len(queue)

    st.markdown(f"""
    <div class="running-banner">
      <div class="pulse-dot"></div>
      <span>Checking URLs — <strong>{remaining:,} remaining</strong> · Processing next {len(chunk)} · {delay_ms}ms delay</span>
    </div>
    """, unsafe_allow_html=True)

    prog      = st.progress(0)
    status_ph = st.empty()
    rate_hit  = False

    for i, url in enumerate(chunk):
        slug = url.split("/")[-1]
        status_ph.markdown(
            f"<p style='font-size:12px;color:#64748b;margin:0;'>⚡ {i+1}/{len(chunk)} — <code>{slug}</code></p>",
            unsafe_allow_html=True,
        )
        result = check_url_indexed(url, api_key)
        results[url] = result

        if result.get("error") == "rate_limited":
            st.session_state["running"] = False
            st.session_state["recheck_errors"] = False
            save_results(results)
            st.warning("⚠️ Rate limited by SERP API. Progress saved — wait a moment then click Start again.")
            rate_hit = True
            break

        prog.progress((i + 1) / len(chunk))
        time.sleep(delay_ms / 1000)

    if not rate_hit:
        save_results(results)
        st.rerun()


# ── Results table ─────────────────────────────────────────────────────────────

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Results</div>', unsafe_allow_html=True)

f1, f2, f3 = st.columns([2.5, 1.5, 1.5])
with f1:
    search = st.text_input("Search", placeholder="Search URL or title…", label_visibility="collapsed")
with f2:
    status_filter = st.multiselect("Status", ["indexed", "not_indexed", "error", "pending"],
                                   default=[], placeholder="Filter by status…")
with f3:
    market_filter = st.multiselect("Market", sorted(summary_df["market"].dropna().unique().tolist()),
                                   default=[], placeholder="Filter by market…")

filtered = summary_df.copy()
if search:
    mask = (
        filtered["url"].str.contains(search, case=False, na=False)
        | filtered["title"].str.contains(search, case=False, na=False)
    )
    filtered = filtered[mask]
if status_filter:
    filtered = filtered[filtered["index_status"].isin(status_filter)]
if market_filter:
    filtered = filtered[filtered["market"].isin(market_filter)]

st.dataframe(
    filtered[["url", "title", "market", "http_status", "index_status", "checked_at", "error"]]
    .style.map(colour_status, subset=["index_status"]),
    use_container_width=True,
    height=480,
    column_config={
        "url":          st.column_config.LinkColumn("URL", width="large"),
        "title":        st.column_config.TextColumn("Title", width="large"),
        "market":       st.column_config.TextColumn("Market", width="small"),
        "http_status":  st.column_config.TextColumn("HTTP", width="small"),
        "index_status": st.column_config.TextColumn("Index Status", width="medium"),
        "checked_at":   st.column_config.TextColumn("Checked At", width="medium"),
        "error":        st.column_config.TextColumn("Error", width="medium"),
    },
)
st.caption(f"Showing {len(filtered):,} of {total:,} URLs")
st.markdown("</div>", unsafe_allow_html=True)


# ── Export ────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Export</div>', unsafe_allow_html=True)

e1, e2, e3 = st.columns(3)
with e1:
    st.download_button(
        "⬇️  All results (CSV)",
        data=summary_df.to_csv(index=False).encode("utf-8"),
        file_name=f"index_results_all_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True,
    )
with e2:
    not_idx = summary_df[summary_df["index_status"] == "not_indexed"]
    st.download_button(
        f"⬇️  Not indexed ({len(not_idx):,}) (CSV)",
        data=not_idx.to_csv(index=False).encode("utf-8"),
        file_name=f"not_indexed_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        disabled=len(not_idx) == 0,
        use_container_width=True,
    )
with e3:
    st.download_button(
        "⬇️  Save progress (JSON)",
        data=json.dumps(results, indent=2).encode("utf-8"),
        file_name=f"index_results_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
        mime="application/json",
        use_container_width=True,
        disabled=len(results) == 0,
    )

st.markdown("</div>", unsafe_allow_html=True)
