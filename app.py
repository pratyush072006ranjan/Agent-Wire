"""
Agent Wire — a newsroom-styled Streamlit front end for the research pipeline
in pipeline.py (search agent -> reader agent -> writer chain -> critic chain).
"""
import warnings
warnings.filterwarnings("ignore",category=DeprecationWarning)
import re
import html
from datetime import datetime

import streamlit as st
from pipeline import run_research_pipeline



# Page setup

st.set_page_config(
    page_title="Agent Wire — Autonomous Research Desk",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

STATIONS = [
    ("search", "01", "Search Wire", "Scanning the open web for leads"),
    ("read", "02", "Field Read", "Pulling the full story off the best lead"),
    ("write", "03", "Drafting Desk", "Composing the dispatch"),
    ("critique", "04", "Copy Desk", "Fact-checking the draft"),
]


# Global styling

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;0,9..144,700;1,9..144,500&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

    :root{
        --ink:#11161d;
        --ink-soft:#181f28;
        --ink-card:#1c2430;
        --line:#2b3542;
        --paper:#efe9d8;
        --paper-dim:#d9d2bd;
        --brass:#c99a3a;
        --brass-dim:#8a6d2c;
        --teal:#4f9091;
        --text:#e7e2d4;
        --text-dim:#9aa3ad;
        --text-ink:#1b1f16;
    }

    html, body, [class*="css"]{
        font-family:'Inter', sans-serif;
    }

    .stApp{
        background:
            radial-gradient(circle at 15% 0%, #1a2129 0%, var(--ink) 45%) fixed;
        color:var(--text);
    }

    section[data-testid="stSidebar"]{
        background:var(--ink-soft);
        border-right:1px solid var(--line);
    }

    /* ---------- masthead ---------- */
    .masthead{
        border-bottom:2px solid var(--brass);
        padding-bottom:18px;
        margin-bottom:28px;
    }
    .masthead .eyebrow{
        font-family:'IBM Plex Mono', monospace;
        letter-spacing:0.28em;
        font-size:0.72rem;
        color:var(--brass);
        text-transform:uppercase;
        margin-bottom:6px;
    }
    .masthead h1{
        font-family:'Fraunces', serif;
        font-weight:700;
        font-size:3.1rem;
        line-height:1;
        color:var(--text);
        margin:0 0 8px 0;
        letter-spacing:-0.01em;
    }
    .masthead .dateline{
        font-family:'IBM Plex Mono', monospace;
        font-size:0.8rem;
        color:var(--text-dim);
    }

    /* ---------- pipeline stepper ---------- */
    .stepper{
        display:flex;
        align-items:flex-start;
        justify-content:space-between;
        margin:6px 0 30px 0;
        position:relative;
    }
    .stepper::before{
        content:"";
        position:absolute;
        top:22px;
        left:6%;
        right:6%;
        height:1px;
        background:var(--line);
        z-index:0;
    }
    .station{
        position:relative;
        z-index:1;
        display:flex;
        flex-direction:column;
        align-items:center;
        width:25%;
        text-align:center;
    }
    .station .dot{
        width:44px;
        height:44px;
        border-radius:50%;
        display:flex;
        align-items:center;
        justify-content:center;
        font-family:'IBM Plex Mono', monospace;
        font-size:0.85rem;
        border:1px solid var(--line);
        background:var(--ink-card);
        color:var(--text-dim);
        transition:all .35s ease;
        margin-bottom:10px;
    }
    .station.done .dot{
        background:var(--brass-dim);
        border-color:var(--brass);
        color:var(--paper);
    }
    .station.active .dot{
        background:var(--brass);
        border-color:var(--brass);
        color:var(--text-ink);
        box-shadow:0 0 0 5px rgba(201,154,58,0.18);
        animation:pulse 1.4s ease-in-out infinite;
    }
    @keyframes pulse{
        0%{box-shadow:0 0 0 4px rgba(201,154,58,0.18);}
        50%{box-shadow:0 0 0 9px rgba(201,154,58,0.05);}
        100%{box-shadow:0 0 0 4px rgba(201,154,58,0.18);}
    }
    .station .label{
        font-weight:600;
        font-size:0.92rem;
        color:var(--text);
    }
    .station.idle .label{ color:var(--text-dim); }
    .station .sub{
        font-size:0.74rem;
        color:var(--text-dim);
        margin-top:2px;
        max-width:150px;
    }

    /* ---------- ticker ---------- */
    .ticker{
        font-family:'IBM Plex Mono', monospace;
        font-size:0.82rem;
        color:var(--teal);
        border-left:2px solid var(--teal);
        padding:4px 0 4px 12px;
        margin:4px 0 22px 0;
        min-height:1.4em;
    }

    /* ---------- cards ---------- */
    .wire-card{
        background:var(--ink-card);
        border:1px solid var(--line);
        border-radius:6px;
        padding:18px 20px;
        margin-bottom:14px;
        font-family:'IBM Plex Mono', monospace;
        font-size:0.83rem;
        color:var(--text-dim);
        white-space:pre-wrap;
        max-height:340px;
        overflow-y:auto;
        line-height:1.55;
    }
    .wire-card .tag{
        display:inline-block;
        font-family:'IBM Plex Mono', monospace;
        font-size:0.68rem;
        letter-spacing:0.14em;
        color:var(--brass);
        border:1px solid var(--brass-dim);
        border-radius:3px;
        padding:2px 7px;
        margin-bottom:10px;
    }

    .paper-card{
        background:var(--paper);
        color:var(--text-ink);
        border-radius:2px;
        padding:36px 44px;
        box-shadow:0 12px 30px rgba(0,0,0,0.35);
        font-family:'Fraunces', serif;
        border-top:6px solid var(--brass);
    }
    .paper-card h2{
        font-family:'Fraunces', serif;
        font-weight:700;
        font-size:1.6rem;
        margin-top:0;
        border-bottom:1px solid var(--paper-dim);
        padding-bottom:10px;
    }
    .paper-card .byline{
        font-family:'IBM Plex Mono', monospace;
        font-size:0.72rem;
        letter-spacing:0.12em;
        color:var(--brass-dim);
        text-transform:uppercase;
        margin-bottom:18px;
    }
    .paper-body{
        font-family:'Inter', sans-serif;
        font-size:0.98rem;
        line-height:1.75;
        white-space:pre-wrap;
    }

    /* ---------- scorecard ---------- */
    .scorecard{
        display:flex;
        gap:26px;
        align-items:center;
        background:var(--ink-card);
        border:1px solid var(--line);
        border-radius:6px;
        padding:22px 26px;
        margin-bottom:18px;
    }
    .gauge{
        --pct: 0;
        width:96px;
        height:96px;
        border-radius:50%;
        flex-shrink:0;
        background:conic-gradient(var(--brass) calc(var(--pct) * 1%), var(--line) 0);
        display:flex;
        align-items:center;
        justify-content:center;
    }
    .gauge-inner{
        width:74px;
        height:74px;
        border-radius:50%;
        background:var(--ink-card);
        display:flex;
        flex-direction:column;
        align-items:center;
        justify-content:center;
        font-family:'IBM Plex Mono', monospace;
    }
    .gauge-inner .num{ font-size:1.35rem; color:var(--text); font-weight:600; }
    .gauge-inner .den{ font-size:0.62rem; color:var(--text-dim); }
    .verdict{
        font-family:'Fraunces', serif;
        font-style:italic;
        font-size:1.05rem;
        color:var(--text);
    }

    .col-title{
        font-family:'IBM Plex Mono', monospace;
        font-size:0.72rem;
        letter-spacing:0.16em;
        text-transform:uppercase;
        color:var(--teal);
        margin-bottom:8px;
    }
    ul.plain{ margin:0; padding-left:18px; color:var(--text-dim); font-size:0.9rem; line-height:1.7;}

    /* ---------- misc ---------- */
    .stButton>button{
        background:var(--brass);
        color:var(--text-ink);
        border:none;
        border-radius:4px;
        font-weight:600;
        letter-spacing:0.03em;
        padding:0.55em 1.4em;
    }
    .stButton>button:hover{
        background:#dcab48;
        color:var(--text-ink);
    }
    .stTextInput input{
        background:var(--ink-card);
        color:var(--text);
        border:1px solid var(--line);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Session state

if "history" not in st.session_state:
    st.session_state.history = []
if "result" not in st.session_state:
    st.session_state.result = None
if "last_topic" not in st.session_state:
    st.session_state.last_topic = ""


# Helpers

def render_stepper(active_key=None, done_keys=frozenset()):
    cells = []
    for key, number, label, sub in STATIONS:
        state = "idle"
        if key in done_keys:
            state = "done"
        if key == active_key:
            state = "active"
        # Built as one unbroken line on purpose: Streamlit's Markdown
        # renderer treats a leading "<div>" as a raw HTML block, and that
        # block ends at the first blank line. Multi-line indented f-strings
        # joined together leave blank lines between cells, which closes the
        # HTML block early and dumps the remaining markup as a code block.
        cell = (
            f'<div class="station {state}">'
            f'<div class="dot">{number}</div>'
            f'<div class="label">{html.escape(label)}</div>'
            f'<div class="sub">{html.escape(sub)}</div>'
            f'</div>'
        )
        cells.append(cell)
    return '<div class="stepper">' + "".join(cells) + "</div>"


def parse_critique(feedback: str):
    score_match = re.search(r"Score:\s*(\d+(?:\.\d+)?)\s*/\s*10", feedback)
    score = float(score_match.group(1)) if score_match else None

    def grab_bullets(section_name, stop_names):
        pattern = rf"{section_name}:(.*?)(?:{'|'.join(stop_names)}:|$)"
        m = re.search(pattern, feedback, re.S)
        if not m:
            return []
        lines = [l.strip("- ").strip() for l in m.group(1).splitlines()]
        return [l for l in lines if l]

    strengths = grab_bullets("Strengths", ["Areas to Improve", "One line verdict"])
    improvements = grab_bullets("Areas to Improve", ["One line verdict"])
    verdict_match = re.search(r"One line verdict:\s*(.*)", feedback)
    verdict = verdict_match.group(1).strip() if verdict_match else None

    return score, strengths, improvements, verdict


def wire_card(tag, text):
    safe = html.escape(text or "(no content)")
    st.markdown(
        f'<div class="wire-card"><span class="tag">{html.escape(tag)}</span>\n{safe}</div>',
        unsafe_allow_html=True,
    )



# Sidebar

with st.sidebar:
    st.markdown(
        "<div style='font-family:IBM Plex Mono, monospace; letter-spacing:0.12em; "
        "font-size:0.72rem; color:var(--brass); text-transform:uppercase;'>Desk Notes</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='color:var(--text-dim); font-size:0.85rem; line-height:1.6; margin-top:6px;'>"
        "Four agents work the story in sequence: one searches, one reads the best "
        "lead in full, one drafts the dispatch, and one checks the draft before it runs."
        "</div>",
        unsafe_allow_html=True,
    )
    st.divider()
    st.markdown(
        "<div style='font-family:IBM Plex Mono, monospace; letter-spacing:0.12em; "
        "font-size:0.72rem; color:var(--teal); text-transform:uppercase;'>Past Assignments</div>",
        unsafe_allow_html=True,
    )
    if st.session_state.history:
        for i, t in enumerate(reversed(st.session_state.history[-12:])):
            st.markdown(
                f"<div style='font-size:0.85rem; color:var(--text-dim); padding:3px 0;'>· {html.escape(t)}</div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            "<div style='font-size:0.85rem; color:var(--text-dim);'>No stories filed yet.</div>",
            unsafe_allow_html=True,
        )


# Masthead

st.markdown(
    f"""
    <div class="masthead">
        <div class="eyebrow">Autonomous Research Desk</div>
        <h1>Agent Wire</h1>
        <div class="dateline">{datetime.now().strftime('%A, %d %B %Y')} &nbsp;·&nbsp; Search — Read — Write — Critique</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# Assignment input

input_col, button_col = st.columns([5, 1])
with input_col:
    topic = st.text_input(
        "Assignment",
        placeholder="e.g. The state of solid-state EV batteries in 2026",
        label_visibility="collapsed",
    )
with button_col:
    run_clicked = st.button("Run desk", use_container_width=True)

stepper_slot = st.empty()
ticker_slot = st.empty()
stepper_slot.markdown(render_stepper(), unsafe_allow_html=True)


# Run pipeline

if run_clicked:
    if not topic.strip():
        st.warning("Give the desk a topic before sending it out on assignment.")
    else:
        done_keys = set()
        ticker_lines = []

        def on_step(step_name, payload):
            done_keys.add(step_name)
            next_active = None
            for key, *_ in STATIONS:
                if key not in done_keys:
                    next_active = key
                    break
            stepper_slot.markdown(
                render_stepper(active_key=next_active, done_keys=done_keys),
                unsafe_allow_html=True,
            )
            label = dict((k, l) for k, _, l, _ in STATIONS)[step_name]
            ticker_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] {label} — filed.")
            ticker_slot.markdown(
                f'<div class="ticker">{html.escape(ticker_lines[-1])}</div>',
                unsafe_allow_html=True,
            )

        stepper_slot.markdown(
            render_stepper(active_key="search"), unsafe_allow_html=True
        )
        ticker_slot.markdown(
            f'<div class="ticker">[{datetime.now().strftime("%H:%M:%S")}] Assignment received — dispatching search agent…</div>',
            unsafe_allow_html=True,
        )

        try:
            with st.spinner("The desk is working the story…"):
                result = run_research_pipeline(topic, on_step=on_step)
            st.session_state.result = result
            st.session_state.last_topic = topic
            if topic not in st.session_state.history:
                st.session_state.history.append(topic)
        except Exception as e:
            st.error(f"The desk hit a snag and couldn't finish the assignment: {e}")


# Results

result = st.session_state.result
if result:
    st.markdown("<br>", unsafe_allow_html=True)
    tab_report, tab_review, tab_notes = st.tabs(
        ["📰 Dispatch", "🖋️ Copy Desk Review", "🗂️ Field Notes"]
    )

    with tab_report:
        st.markdown(
            f"""
            <div class="paper-card">
                <div class="byline">Filed on {html.escape(st.session_state.last_topic)}</div>
                <h2>{html.escape(st.session_state.last_topic.title())}</h2>
                <div class="paper-body">{html.escape(result.get('report',''))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with tab_review:
        score, strengths, improvements, verdict = parse_critique(result.get("feedback", ""))
        pct = int((score / 10) * 100) if score is not None else 0
        st.markdown(
            f"""
            <div class="scorecard">
                <div class="gauge" style="--pct:{pct};">
                    <div class="gauge-inner">
                        <div class="num">{score if score is not None else '—'}</div>
                        <div class="den">/ 10</div>
                    </div>
                </div>
                <div class="verdict">{html.escape(verdict) if verdict else 'No verdict line found — see raw review below.'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<div class="col-title">Strengths</div>', unsafe_allow_html=True)
            if strengths:
                st.markdown(
                    "<ul class='plain'>" + "".join(f"<li>{html.escape(s)}</li>" for s in strengths) + "</ul>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown("<div style='color:var(--text-dim); font-size:0.85rem;'>None parsed.</div>", unsafe_allow_html=True)
        with col_b:
            st.markdown('<div class="col-title">Areas to Improve</div>', unsafe_allow_html=True)
            if improvements:
                st.markdown(
                    "<ul class='plain'>" + "".join(f"<li>{html.escape(s)}</li>" for s in improvements) + "</ul>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown("<div style='color:var(--text-dim); font-size:0.85rem;'>None parsed.</div>", unsafe_allow_html=True)

        with st.expander("Raw review text"):
            wire_card("RAW · COPY DESK", result.get("feedback", ""))

    with tab_notes:
        wire_card("STEP 01 · SEARCH WIRE", result.get("search_results", ""))
        wire_card("STEP 02 · FIELD READ", result.get("scraped_content", ""))
else:
    st.markdown(
        "<div style='color:var(--text-dim); font-size:0.9rem; margin-top:8px;'>"
        "Enter a topic above and hit <b>Run desk</b> — the pipeline will report back here as it works."
        "</div>",
        unsafe_allow_html=True,
    )