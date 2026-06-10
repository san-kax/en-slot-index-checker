import streamlit as st
import pandas as pd
import requests
import json
import time
import os
from datetime import datetime

st.set_page_config(
    page_title="Google Index Checker",
    page_icon="🔍",
    layout="wide",
)


def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.title("🔍 Google Index Checker")
    st.subheader("Sign in")
    pwd = st.text_input("Password", type="password")
    if st.button("Enter", type="primary"):
        correct = st.secrets.get("APP_PASSWORD", "")
        if pwd == correct and correct != "":
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False

if not check_password():
    st.stop()

CSV_FILE = "en_gx_slot_game_urls.csv"
RESULTS_FILE = "index_results.json"
IS_CLOUD = not os.path.exists(RESULTS_FILE) and not os.access(".", os.W_OK)


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_urls():
    df = pd.read_csv(CSV_FILE)
    df.columns = df.columns.str.strip()
    return df


def load_results():
    # Session state takes priority (cloud); fall back to local file
    if "results" in st.session_state:
        return st.session_state["results"]
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as f:
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
    except OSError:
        pass  # read-only filesystem (Streamlit Cloud) — session state is the store


def check_url_indexed(url: str, api_key: str) -> dict:
    try:
        params = {
            "engine": "google",
            "q": f"site:{url}",
            "api_key": api_key,
            "num": 1,
        }
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


def build_summary_df(df: pd.DataFrame, results: dict) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        url = row["url"]
        r = results.get(url, {})
        rows.append({
            "url": url,
            "title": row.get("title", ""),
            "market": row.get("market", ""),
            "http_status": row.get("status", ""),
            "index_status": r.get("status", "pending"),
            "checked_at": r.get("checked_at", ""),
            "error": r.get("error", "") or "",
        })
    return pd.DataFrame(rows)


STATUS_COLOURS = {
    "indexed":     ("🟢", "#d4edda", "#155724"),
    "not_indexed": ("🔴", "#f8d7da", "#721c24"),
    "error":       ("🟡", "#fff3cd", "#856404"),
    "pending":     ("⚪", "#e9ecef", "#383d41"),
}

def colour_status(val):
    _, bg, fg = STATUS_COLOURS.get(val, ("", "", ""))
    if bg:
        return f"background-color:{bg}; color:{fg}; font-weight:500"
    return ""


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("⚙️ Settings")

    # Pre-fill from Streamlit secrets if available
    default_key = ""
    try:
        default_key = st.secrets.get("SERP_API_KEY", "")
    except Exception:
        pass

    api_key = st.text_input(
        "SERP API Key",
        value=default_key,
        type="password",
        help="Add to Streamlit Cloud secrets as SERP_API_KEY to pre-fill for all users.",
    )

    st.divider()
    batch_size = st.slider("Batch size per run", 10, 500, 200, 10)
    delay_ms   = st.slider("Delay between requests (ms)", 200, 3000, 600, 100)

    st.divider()
    uploaded = st.file_uploader(
        "Import previous results (JSON)",
        type="json",
        help="Upload a previously exported results file to resume progress.",
    )
    if uploaded:
        imported = json.load(uploaded)
        save_results(imported)
        st.success(f"Imported {len(imported):,} results.")
        st.rerun()

    st.divider()
    if st.button("🗑️ Clear all results", use_container_width=True):
        st.session_state["results"] = {}
        if os.path.exists(RESULTS_FILE):
            os.remove(RESULTS_FILE)
        st.rerun()


# ── Load data ─────────────────────────────────────────────────────────────────

try:
    df = load_urls()
except FileNotFoundError:
    st.error(f"`{CSV_FILE}` not found. Make sure it's committed to the repo.")
    st.stop()

results     = load_results()
summary_df  = build_summary_df(df, results)

total       = len(summary_df)
indexed     = (summary_df["index_status"] == "indexed").sum()
not_indexed = (summary_df["index_status"] == "not_indexed").sum()
errors      = (summary_df["index_status"] == "error").sum()
pending     = (summary_df["index_status"] == "pending").sum()
checked     = total - pending
pct_done    = round(checked / total * 100, 1) if total else 0


# ── Header ────────────────────────────────────────────────────────────────────

st.title("🔍 Google Index Checker")
st.caption("gambling.com — EN Slot Games Pages  •  Data: en_gx_slot_game_urls.csv")

# ── Summary cards ─────────────────────────────────────────────────────────────

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total URLs",      f"{total:,}")
c2.metric("Checked",         f"{checked:,}",     delta=f"{pct_done}%")
c3.metric("🟢 Indexed",      f"{indexed:,}",     delta=f"{round(indexed/checked*100,1)}% of checked" if checked else None)
c4.metric("🔴 Not indexed",  f"{not_indexed:,}", delta=f"{round(not_indexed/checked*100,1)}% of checked" if checked else None)
c5.metric("🟡 Errors",       f"{errors:,}")
c6.metric("⚪ Pending",      f"{pending:,}")

st.progress(checked / total if total else 0, text=f"Progress: {checked:,} / {total:,} URLs checked ({pct_done}%)")

st.divider()

# ── Run controls ──────────────────────────────────────────────────────────────

col_run, col_err, col_save = st.columns([2, 1, 1])

with col_run:
    run_btn = st.button(
        f"▶ Check next {batch_size} pending URLs",
        type="primary",
        disabled=not api_key or pending == 0,
        use_container_width=True,
    )
with col_err:
    recheck_btn = st.button(
        f"🔄 Recheck {errors:,} errors",
        disabled=not api_key or errors == 0,
        use_container_width=True,
    )
with col_save:
    results_json = json.dumps(results, indent=2).encode("utf-8")
    st.download_button(
        "💾 Save progress (JSON)",
        data=results_json,
        file_name=f"index_results_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
        mime="application/json",
        use_container_width=True,
        disabled=len(results) == 0,
    )

if run_btn or recheck_btn:
    if not api_key:
        st.error("Enter your SERP API key in the sidebar.")
        st.stop()

    queue = (
        summary_df[summary_df["index_status"] == "error"]["url"].tolist()[:batch_size]
        if recheck_btn
        else summary_df[summary_df["index_status"] == "pending"]["url"].tolist()[:batch_size]
    )

    prog      = st.progress(0, text="Starting…")
    status_ph = st.empty()
    rate_hit  = False

    for i, url in enumerate(queue):
        status_ph.text(f"({i+1}/{len(queue)}) {url}")
        result = check_url_indexed(url, api_key)
        results[url] = result

        if result.get("error") == "rate_limited":
            st.warning("⚠️ Rate limited by SERP API. Progress saved — try again shortly.")
            rate_hit = True
            break

        prog.progress((i + 1) / len(queue), text=f"{i+1}/{len(queue)} checked")
        time.sleep(delay_ms / 1000)

    save_results(results)
    if not rate_hit:
        status_ph.success(f"✅ Done! {len(queue)} URLs checked.")
    st.rerun()

st.divider()

# ── Results table ─────────────────────────────────────────────────────────────

st.subheader("Results")

f1, f2, f3 = st.columns([2, 1, 1])
with f1:
    search = st.text_input("Search URL or title", placeholder="e.g. starburst")
with f2:
    status_filter = st.multiselect(
        "Index status",
        ["indexed", "not_indexed", "error", "pending"],
        default=[],
    )
with f3:
    market_filter = st.multiselect(
        "Market", sorted(summary_df["market"].dropna().unique().tolist()), default=[]
    )

filtered = summary_df.copy()
if search:
    m = (
        filtered["url"].str.contains(search, case=False, na=False)
        | filtered["title"].str.contains(search, case=False, na=False)
    )
    filtered = filtered[m]
if status_filter:
    filtered = filtered[filtered["index_status"].isin(status_filter)]
if market_filter:
    filtered = filtered[filtered["market"].isin(market_filter)]

st.dataframe(
    filtered[["url", "title", "market", "http_status", "index_status", "checked_at", "error"]]
    .style.map(colour_status, subset=["index_status"]),
    use_container_width=True,
    height=520,
    column_config={
        "url": st.column_config.LinkColumn("URL"),
        "index_status": "Index Status",
        "checked_at": "Checked At",
        "http_status": "HTTP",
    },
)
st.caption(f"Showing {len(filtered):,} of {total:,} URLs")

# ── Export ────────────────────────────────────────────────────────────────────

st.divider()
e1, e2 = st.columns(2)

with e1:
    st.download_button(
        "⬇️ Download all results (CSV)",
        data=summary_df.to_csv(index=False).encode("utf-8"),
        file_name=f"index_results_all_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True,
    )
with e2:
    not_idx = summary_df[summary_df["index_status"] == "not_indexed"]
    st.download_button(
        f"⬇️ Download not-indexed ({len(not_idx):,}) (CSV)",
        data=not_idx.to_csv(index=False).encode("utf-8"),
        file_name=f"not_indexed_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        disabled=len(not_idx) == 0,
        use_container_width=True,
    )
