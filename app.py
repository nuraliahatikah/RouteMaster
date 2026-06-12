import html
import json
import os

import streamlit as st

from routemaster.integration_hub import build_issue_payload, push_issue_to_produck
from routemaster.reply_engine import EvaluationResult, evaluate_review

KB_PATH = os.path.join("property_data", "local_knowledge.txt")

SAMPLE_REVIEWS = {
    "Parking — only one spot inside": (
        "The place was fine but we brought three cars and had no idea where to put "
        "the last one. Terrible experience."
    ),
    "Trash bag leaked": (
        "The kitchen trash bag leaked all over the floor when we lifted it up, "
        "creating a massive dirty mess."
    ),
    "Late checkout": (
        "We wanted to leave at 1 PM but were told checkout is strictly 11 AM. "
        "Felt rushed and disappointed."
    ),
    "Positive stay": (
        "Everything was super clean and beautiful! The kids loved the place."
    ),
}

SAMPLE_OPTIONS = ["Custom paste", *SAMPLE_REVIEWS.keys()]


def configure_page() -> None:
    st.set_page_config(
        page_title="RouteMaster — Track 2",
        page_icon="🦆",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def init_session_state() -> None:
    defaults = {
        "evaluation_result": None,
        "review_processed": "",
        "push_completed": False,
        "push_message": "",
        "push_success": False,
        "custom_review": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_app_styles() -> str:
    return """
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
    .stApp {
        background: radial-gradient(ellipse 80% 60% at 10% 0%, #1a1040 0%, transparent 55%),
                    radial-gradient(ellipse 70% 50% at 90% 10%, #0c3547 0%, transparent 50%),
                    linear-gradient(160deg, #0b0f1a 0%, #111827 45%, #0f172a 100%);
    }
    #MainMenu, footer, header { visibility: hidden; }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .block-container { padding-top: 1.2rem; max-width: 1180px; }
    .hero {
        background: linear-gradient(135deg, rgba(99,102,241,0.18), rgba(16,185,129,0.12), rgba(124,58,237,0.15));
        border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 1.1rem 1.4rem;
        margin-bottom: 1rem;
    }
    .hero h1 {
        margin: 0; font-size: 1.75rem; font-weight: 700;
        background: linear-gradient(90deg, #e2e8f0, #a5b4fc, #6ee7b7);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .hero .tagline { color: #94a3b8; font-size: 0.88rem; margin-top: 0.25rem; }
    .hero .track-pill {
        display: inline-block; margin-top: 0.5rem; padding: 0.25rem 0.7rem; border-radius: 999px;
        font-size: 0.68rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;
        background: rgba(124,58,237,0.25); color: #c4b5fd; border: 1px solid rgba(167,139,250,0.35);
    }
    .workflow { display: flex; gap: 0.4rem; margin-bottom: 0.75rem; flex-wrap: wrap; }
    .workflow-step {
        flex: 1; min-width: 100px; text-align: center; padding: 0.45rem 0.35rem; border-radius: 8px;
        font-size: 0.68rem; font-weight: 600; color: #64748b;
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
    }
    .workflow-step.active { color: #a5b4fc; background: rgba(99,102,241,0.15); border-color: rgba(99,102,241,0.35); }
    .workflow-step.done { color: #6ee7b7; background: rgba(16,185,129,0.12); border-color: rgba(16,185,129,0.3); }
    .panel-label { font-size: 0.65rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #6366f1; }
    .panel-title { font-size: 1rem; font-weight: 700; color: #f1f5f9; margin: 0.15rem 0 0.75rem; }
    .property-card {
        background: linear-gradient(145deg, rgba(30,58,95,0.9), rgba(45,106,79,0.85));
        border-radius: 12px; padding: 0.9rem; color: #f8fafc; margin-bottom: 0.75rem;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .property-card h4 { margin: 0 0 0.25rem; font-size: 0.95rem; }
    .property-card .meta { font-size: 0.75rem; opacity: 0.85; margin-bottom: 0.5rem; }
    .property-card .chip-row { display: flex; gap: 0.3rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
    .property-card .chip { font-size: 0.62rem; padding: 0.15rem 0.45rem; border-radius: 5px; background: rgba(255,255,255,0.12); }
    .property-card .wifi {
        background: rgba(0,0,0,0.2); border-radius: 8px; padding: 0.5rem 0.6rem; font-size: 0.72rem;
        font-family: 'JetBrains Mono', monospace;
    }
    .compliance-box {
        background: rgba(124,58,237,0.12); border: 1px solid rgba(167,139,250,0.3);
        border-radius: 10px; padding: 0.65rem 0.75rem; font-size: 0.72rem; color: #c4b5fd; line-height: 1.45;
    }
    .incidents-panel { background: rgba(15,23,42,0.8); border-radius: 12px; padding: 0.75rem; border: 1px solid #334155; }
    .incidents-header { display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.5rem; }
    .live-dot { width: 7px; height: 7px; background: #22c55e; border-radius: 50%; animation: blink 1.4s infinite; }
    @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }
    .incidents-panel h4 { color: #e2e8f0; font-size: 0.8rem; margin: 0; }
    .incident-log { font-size: 0.7rem; color: #cbd5e1; padding: 0.4rem 0.5rem; margin-bottom: 0.3rem; border-radius: 6px; background: rgba(255,255,255,0.03); border-left: 3px solid transparent; }
    .incident-log.warn { border-left-color: #f59e0b; }
    .incident-log.ok { border-left-color: #22c55e; }
    .incident-log.info { border-left-color: #3b82f6; }
    .badge-negative {
        background: linear-gradient(135deg, #991b1b, #ef4444); color: #fff; padding: 0.55rem 0.75rem;
        border-radius: 10px; font-weight: 700; font-size: 0.82rem; text-align: center;
        border: 1px solid #fca5a5; animation: pulse-red 2s ease-in-out infinite;
    }
    .badge-positive {
        background: linear-gradient(135deg, #065f46, #10b981); color: #fff; padding: 0.55rem 0.75rem;
        border-radius: 10px; font-weight: 700; font-size: 0.82rem; text-align: center;
    }
    .badge-neutral {
        background: linear-gradient(135deg, #1e40af, #3b82f6); color: #fff; padding: 0.55rem 0.75rem;
        border-radius: 10px; font-weight: 700; font-size: 0.82rem; text-align: center;
    }
    @keyframes pulse-red { 0%, 100% { box-shadow: 0 0 10px rgba(239,68,68,0.3); } 50% { box-shadow: 0 0 20px rgba(239,68,68,0.6); } }
    .stat-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.07); border-radius: 10px; padding: 0.55rem 0.65rem; text-align: center; }
    .stat-card .label { font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.07em; color: #64748b; font-weight: 600; }
    .stat-card .value { font-size: 0.9rem; font-weight: 700; color: #e2e8f0; margin-top: 0.15rem; }
    .stat-card .delta { font-size: 0.65rem; color: #6ee7b7; font-weight: 600; }
    .reply-bubble {
        background: linear-gradient(160deg, rgba(99,102,241,0.1), rgba(16,185,129,0.08));
        border: 1px solid rgba(99,102,241,0.2); border-radius: 12px; padding: 0.75rem 0.9rem; margin: 0.5rem 0;
    }
    .reply-bubble .reply-label { font-size: 0.62rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #818cf8; margin-bottom: 0.35rem; }
    .reply-bubble pre { white-space: pre-wrap; font-family: 'DM Sans', sans-serif; font-size: 0.82rem; color: #cbd5e1; margin: 0; line-height: 1.5; max-height: 200px; overflow-y: auto; }
    .facts-panel { margin: 0.35rem 0 0.5rem; max-height: 90px; overflow-y: auto; }
    .fact-chip {
        display: inline-block; font-size: 0.65rem; padding: 0.2rem 0.45rem; margin: 0.1rem 0.15rem 0.1rem 0;
        border-radius: 5px; background: rgba(99,102,241,0.15); color: #a5b4fc; border: 1px solid rgba(99,102,241,0.25);
    }
    .track2-divider { border: none; border-top: 1px solid rgba(124,58,237,0.35); margin: 0.75rem 0; }
    .track2-header { color: #c4b5fd; font-size: 0.95rem; font-weight: 700; margin-bottom: 0.1rem; }
    .track2-sub { font-size: 0.72rem; color: #64748b; margin-bottom: 0.5rem; }
    .empty-state { text-align: center; padding: 2rem 1rem; color: #64748b; }
    .empty-state .icon { font-size: 2rem; margin-bottom: 0.5rem; }
    .empty-state h3 { color: #94a3b8; font-size: 0.9rem; margin: 0 0 0.3rem; }
    div[data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a, #111827); border-right: 1px solid rgba(255,255,255,0.06); }
    div[data-testid="stSidebar"] > div:first-child { width: 280px !important; }
    """


def inject_styles() -> None:
    st.markdown(f"<style>{get_app_styles()}</style>", unsafe_allow_html=True)


def render_track2_compliance() -> None:
    st.markdown(
        """
        <div class="compliance-box">
            <strong>Track 2 — Required Stack</strong><br>
            Produck issue filing via <code>POST /v1/issues</code><br>
            Grounded replies from <code>local_knowledge.txt</code> only.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_property_profile() -> None:
    st.markdown("#### 🏡 Property Profile")
    st.markdown(
        """
        <div class="property-card">
            <h4>Mini Homestay Bak</h4>
            <div class="meta">📍 Pontian, Johor, Malaysia</div>
            <div class="chip-row">
                <span class="chip">🅿️ Max 2 cars</span>
                <span class="chip">🕚 Checkout 11 AM</span>
                <span class="chip">🗑️ Double-bag trash</span>
            </div>
            <div class="wifi">
                <strong>Wi-Fi</strong><br>
                Network: <code>HomestayBak_Guest</code>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_incidents_monitor() -> None:
    st.markdown("#### 📡 Live Incidents")
    st.markdown(
        """
        <div class="incidents-panel">
            <div class="incidents-header">
                <div class="live-dot"></div>
                <h4>Recent activity</h4>
            </div>
            <div class="incident-log warn">⚠️ 10:14 PM — Minor parking dispute flagged</div>
            <div class="incident-log ok">✅ 09:30 AM — Maid turnover cleared</div>
            <div class="incident-log info">ℹ️ 08:05 AM — Checkout reminder sent</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Simulated feed · Pontian ops channel")


def render_sidebar() -> None:
    with st.sidebar:
        render_property_profile()
        render_incidents_monitor()
        st.markdown("---")
        render_track2_compliance()


def workflow_step_class(step: int, has_result: bool, push_completed: bool) -> str:
    if step == 1:
        return "done" if has_result else "active"
    if step == 2:
        if not has_result:
            return ""
        return "done"
    if step == 3:
        if push_completed:
            return "done"
        return "active" if has_result else ""
    return ""


def render_hero(has_result: bool, push_completed: bool) -> None:
    st.markdown(
        f"""
        <div class="hero">
            <h1>🦆 RouteMaster</h1>
            <div class="tagline">Grounded guest-review ops desk · Quackathon Track 2</div>
            <span class="track-pill">Track 2 · Produck · Mini Homestay Bak</span>
        </div>
        <div class="workflow">
            <div class="workflow-step {workflow_step_class(1, has_result, push_completed)}">① Ingest Review</div>
            <div class="workflow-step {workflow_step_class(2, has_result, push_completed)}">② Ground &amp; Draft</div>
            <div class="workflow-step {workflow_step_class(3, has_result, push_completed)}">③ Produck Push</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_review_text(sample_choice: str) -> str:
    if sample_choice == "Custom paste":
        return st.text_area(
            "Review text",
            value=st.session_state.custom_review,
            height=140,
            placeholder="Paste a guest review here…",
            label_visibility="collapsed",
            key="custom_review_area",
        )
    return st.text_area(
        "Review text",
        value=SAMPLE_REVIEWS[sample_choice],
        height=140,
        disabled=True,
        label_visibility="collapsed",
        key=f"sample_{sample_choice}",
    )


def run_evaluation(review_text: str) -> None:
    cleaned = review_text.strip()
    if not cleaned:
        st.warning("Please enter or select a review first.")
        return
    st.session_state.evaluation_result = evaluate_review(cleaned, KB_PATH)
    st.session_state.review_processed = cleaned
    st.session_state.push_completed = False
    st.session_state.push_message = ""
    st.session_state.push_success = False


def render_review_panel() -> None:
    st.markdown('<div class="panel-label">Input</div><div class="panel-title">Customer Review</div>', unsafe_allow_html=True)

    with st.container(border=True):
        sample_choice = st.selectbox(
            "Scenario",
            SAMPLE_OPTIONS,
            label_visibility="visible",
        )
        review_input = get_review_text(sample_choice)

        if st.button("⚡ Run evaluation", type="primary", use_container_width=True):
            run_evaluation(review_input)


def render_sentiment_badge(sentiment: str) -> None:
    normalized = sentiment.lower()
    if normalized == "negative":
        st.markdown('<div class="badge-negative">🚨 NEGATIVE</div>', unsafe_allow_html=True)
    elif normalized == "positive":
        st.markdown('<div class="badge-positive">✨ POSITIVE</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="badge-neutral">🔎 {sentiment.upper()}</div>', unsafe_allow_html=True)


def render_analysis_metrics(result: EvaluationResult) -> None:
    badge_col, cat_col, sponsor_col = st.columns(3)
    with badge_col:
        render_sentiment_badge(result.sentiment)
    with cat_col:
        category = result.topics[0].replace("_", " ").title()
        st.markdown(
            f'<div class="stat-card"><div class="label">Category</div>'
            f'<div class="value">{html.escape(category)}</div></div>',
            unsafe_allow_html=True,
        )
    with sponsor_col:
        status = "Filed" if st.session_state.push_completed else "Ready"
        delta = "▲ Produck OK" if st.session_state.push_completed else "▲ Stack OK"
        st.markdown(
            f'<div class="stat-card"><div class="label">Produck</div>'
            f'<div class="value">{status}</div><div class="delta">{delta}</div></div>',
            unsafe_allow_html=True,
        )


def render_cited_facts(facts: list[str]) -> None:
    if not facts:
        st.caption("No matching facts in local_knowledge.txt")
        return
    chips = "".join(f'<span class="fact-chip">{html.escape(f)}</span>' for f in facts)
    st.markdown(f'<div class="facts-panel">{chips}</div>', unsafe_allow_html=True)


def render_reply_bubble(draft_reply: str) -> None:
    st.markdown(
        f"""
        <div class="reply-bubble">
            <div class="reply-label">✉️ Grounded Reply Draft</div>
            <pre>{html.escape(draft_reply)}</pre>
        </div>
        """,
        unsafe_allow_html=True,
    )


def handle_produck_push(payload, api_key: str) -> None:
    with st.spinner("POST https://api.produck.dev/v1/issues …"):
        success, msg, _body = push_issue_to_produck(payload, api_key=api_key or None)
    st.session_state.push_success = success
    st.session_state.push_message = msg
    if success:
        st.session_state.push_completed = True


def render_push_feedback() -> None:
    if st.session_state.push_message:
        if st.session_state.push_success:
            st.success(st.session_state.push_message)
        else:
            st.error(st.session_state.push_message)


def render_track2_hub(result: EvaluationResult) -> None:
    st.markdown('<hr class="track2-divider">', unsafe_allow_html=True)
    st.markdown(
        '<div class="track2-header">🔧 Track 2 — Produck Issue Filing</div>'
        '<div class="track2-sub">Required sponsor stack · structured JSON → api.produck.dev/v1/issues</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        payload = build_issue_payload(result)

        with st.expander("🔍 Inspect Produck JSON payload", expanded=result.is_negative):
            st.json(payload.to_dict())

        api_key_input = st.text_input("Produck API key (optional)", type="password")

        if st.button("🚀 Push issue to Produck API", type="secondary", use_container_width=True):
            handle_produck_push(payload, api_key_input)

        render_push_feedback()

        st.download_button(
            label="⬇️ Download issue payload (JSON)",
            data=json.dumps(payload.to_dict(), indent=2),
            file_name=f"produck_issue_{result.topics[0]}.json",
            mime="application/json",
            use_container_width=True,
        )


def render_evaluation_results(result: EvaluationResult) -> None:
    render_analysis_metrics(result)
    st.caption(f"Grounded from {len(result.cited_facts)} fact(s) in local_knowledge.txt")
    render_cited_facts(result.cited_facts)
    render_reply_bubble(result.draft_reply)
    render_track2_hub(result)


def render_empty_state() -> None:
    st.markdown(
        """
        <div class="empty-state">
            <div class="icon">📋</div>
            <h3>Awaiting evaluation</h3>
            <p>Select a scenario, then click <strong>Run evaluation</strong>.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_output_panel() -> None:
    st.markdown('<div class="panel-label">Output</div><div class="panel-title">Analysis &amp; Produck Hub</div>', unsafe_allow_html=True)

    with st.container(border=True):
        if st.session_state.evaluation_result:
            render_evaluation_results(st.session_state.evaluation_result)
        else:
            render_empty_state()


def render_main_layout() -> None:
    col_left, col_right = st.columns([1, 1.15], gap="medium")
    with col_left:
        render_review_panel()
    with col_right:
        render_output_panel()


def main() -> None:
    configure_page()
    init_session_state()
    inject_styles()
    render_sidebar()

    has_result = st.session_state.evaluation_result is not None
    render_hero(has_result, st.session_state.push_completed)
    render_main_layout()


if __name__ == "__main__":
    main()
