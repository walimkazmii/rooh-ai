import html
import os
import re
from datetime import datetime
from pathlib import Path

import streamlit as st
from groq import Groq
from soul_prompt import SOUL_SYSTEM_PROMPT, OPENING_CHALLENGE
from memory_manager import (
    load_memory, save_memory, build_memory_context, add_session, reset_memory,
)

# Groq retired its Llama 3 models on 16 Aug 2026. The larger gpt-oss model argues and
# cites best; the smaller one is the fallback. If Groq retires these too, the app asks
# Groq which chat models exist and uses one of those. Override with GROQ_MODEL=...
MODELS = [m for m in [os.environ.get("GROQ_MODEL"), "openai/gpt-oss-120b", "openai/gpt-oss-20b"] if m]
NON_CHAT = ("whisper", "orpheus", "tts", "guard", "safeguard", "embed")

st.set_page_config(
    page_title="Rooh",
    page_icon=str(Path(__file__).resolve().parent / "blank_icon.png"),  # hides the Streamlit logo in the browser tab
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600&display=swap');

/* ── Palette: warm charcoal + soft violet, white text ── */
:root {
    --bg: #262522;          /* page */
    --surface: #33312d;     /* user bubble, input box */
    --surface-hi: #3d3b36;  /* hover / focus */
    --border: #45423d;
    --text: #ffffff;
    --text-dim: rgba(255,255,255,0.55);  /* input placeholder only */
    --accent: #9d8cf5;      /* soft violet */
    --accent-deep: #7c6ae6;
}

html, body,
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: var(--bg) !important;
    font-family: 'Geist', -apple-system, 'Helvetica Neue', sans-serif !important;
    color: var(--text) !important;
}

[data-testid="stMainBlockContainer"] {
    max-width: 740px !important;
    padding: 0 1.5rem 8rem !important;
    margin: 0 auto !important;
}

/* Hide Streamlit chrome */
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDeployButton"],
[data-testid="stSidebarCollapsedControl"],
#MainMenu, footer { display: none !important; }

/* ── Top bar ── */
.topbar {
    position: sticky;
    top: 0;
    background: rgba(38,37,34,0.9);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    padding: 1rem 0;
    margin-bottom: 1.5rem;
    z-index: 100;
}
.topbar-inner { display: flex; align-items: center; gap: 10px; }
.topbar-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 10px var(--accent);
    flex-shrink: 0;
    animation: breathe 3.5s ease-in-out infinite;
}
@keyframes breathe { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }
.topbar-title { font-size: 0.9rem; font-weight: 500; color: var(--text); }
.topbar-sub { font-size: 0.75rem; color: var(--text); margin-left: auto; }

/* ── Messages ── */
.msg-group { margin: 1.5rem 0; display: flex; flex-direction: column; }

.msg-user-wrap { display: flex; justify-content: flex-end; }
.msg-user {
    background: var(--surface);
    color: var(--text);
    font-size: 0.95rem;
    line-height: 1.6;
    padding: 0.7rem 1.1rem;
    border-radius: 18px;
    max-width: 80%;
    word-wrap: break-word;
}

.msg-ai-wrap { display: flex; align-items: flex-start; gap: 14px; }
.msg-ai-avatar {
    width: 28px; height: 28px; border-radius: 50%;
    background: var(--accent-deep);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; margin-top: 3px;
}
.msg-ai-avatar span { font-size: 12px; font-weight: 600; color: #fff; }
.msg-ai {
    font-family: 'Geist', -apple-system, 'Helvetica Neue', sans-serif;
    font-size: 1rem;
    line-height: 1.65;
    color: var(--text);
    max-width: 90%;
}

/* ── Empty state: the opening challenge, nothing else ── */
.empty-state {
    display: flex; align-items: center; justify-content: center;
    min-height: 52vh; padding: 2rem 0.5rem; text-align: center;
}
.empty-title {
    font-family: 'Geist', -apple-system, 'Helvetica Neue', sans-serif;
    font-size: clamp(1.8rem, 5vw, 2.6rem); font-weight: 300; line-height: 1.25;
    color: var(--text); letter-spacing: -0.02em; max-width: 600px;
}

/* ── Input box ── */
[data-testid="stBottom"],
[data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"] {
    background: var(--bg) !important;
    border: none !important;
}
[data-testid="stBottomBlockContainer"] { padding: 0.5rem 1.5rem 1.5rem !important; max-width: 740px !important; }
[data-testid="stChatInput"] {
    background: transparent !important; border: none !important; box-shadow: none !important; padding: 0 !important;
}
[data-testid="stChatInput"] > div {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 20px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.25) !important;
    min-height: 60px;
    transition: border-color 0.15s !important;
}
[data-testid="stChatInput"] > div:focus-within { border-color: var(--accent) !important; }
[data-testid="stChatInput"] textarea {
    background: transparent !important; border: none !important;
    color: var(--text) !important; caret-color: var(--accent);
    font-family: 'Geist', -apple-system, sans-serif !important; font-size: 0.95rem !important;
    padding: 0.85rem 1.1rem !important; box-shadow: none !important; resize: none !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: var(--text-dim) !important; }
[data-testid="stChatInput"] button {
    background: var(--accent-deep) !important;
    border-radius: 10px !important;
    color: #fff !important;
    margin: 8px !important;
}
[data-testid="stChatInput"] button:hover { background: var(--accent) !important; }
[data-testid="stChatInput"] button svg { fill: #fff !important; color: #fff !important; }

/* ── Presenter controls ── */
[data-testid="stExpander"] details {
    background: transparent !important; border: 1px solid var(--border) !important; border-radius: 12px !important;
}
[data-testid="stExpander"] summary, [data-testid="stExpander"] p, label, .stCaption, [data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] *, [data-testid="stWidgetLabel"] * {
    color: var(--text) !important;
}

/* Spinner */
[data-testid="stSpinner"] { padding-left: 42px !important; }
[data-testid="stSpinner"] p { font-size: 0.8rem !important; color: var(--text) !important; }
</style>
""", unsafe_allow_html=True)

# ── Setup ──────────────────────────────────────────────────────────────────────
def _read_key():
    """Key from the environment (local runs) or Streamlit secrets (hosted on Streamlit Cloud)."""
    key = os.environ.get("GROQ_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("GROQ_API_KEY")
    except Exception:  # no secrets file locally
        return None


GROQ_API_KEY = _read_key()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "memory" not in st.session_state:
    st.session_state.memory = load_memory()
if "model" not in st.session_state:
    st.session_state.model = MODELS[0]

memory = st.session_state.memory


def _ask(client, model: str, system: str, history: list, temperature: float, max_tokens: int) -> str:
    extra = {}
    if "gpt-oss" in model:
        # Reasoning model: keep the hidden thinking short so it doesn't eat the reply.
        extra = {"reasoning_effort": "low"}
        max_tokens += 1200
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}] + history,
        temperature=temperature,
        max_tokens=max_tokens,
        extra_body=extra or None,
    )
    text = (response.choices[0].message.content or "").strip()
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    if not text:
        raise RuntimeError(f"{model} returned an empty reply")
    return text


def call_model(system: str, history: list, temperature: float = 0.75, max_tokens: int = 400) -> str:
    """Try the preferred models in order; if all are gone, use any chat model Groq offers."""
    client = Groq(api_key=GROQ_API_KEY)
    errors = []
    candidates = list(MODELS)
    tried_listing = False
    while candidates:
        model = candidates.pop(0)
        try:
            text = _ask(client, model, system, history, temperature, max_tokens)
            st.session_state.model = model
            return text
        except Exception as e:  # model retired, rate-limited, etc.
            errors.append(f"{model}: {e}")
            if "401" in str(e) or "invalid_api_key" in str(e):
                break  # wrong key: no point trying other models
        if not candidates and not tried_listing:
            tried_listing = True
            try:
                available = [m.id for m in client.models.list().data]
                candidates = [m for m in available
                              if m not in MODELS and not any(x in m.lower() for x in NON_CHAT)]
            except Exception:
                pass
    raise RuntimeError(" | ".join(errors[:3]))


def render(text: str) -> str:
    """Escape text so a stray < or > can't break the page; keep simple **bold** and *italics*."""
    out = html.escape(text)
    out = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", out)
    out = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", out)
    return out.replace("\n", "<br>")


def transcript_markdown() -> str:
    lines = ["# Rooh debate transcript",
             f"Model: {st.session_state.model} · {datetime.now():%Y-%m-%d %H:%M}", "",
             f"**Rooh (on screen):** {OPENING_CHALLENGE}", ""]
    for m in st.session_state.messages:
        who = "Challenger" if m["role"] == "user" else "Rooh"
        lines += [f"**{who}:** {m['content']}", ""]
    return "\n".join(lines)


def archive_conversation():
    """Summarise the current debate and write it into Rooh's long-term memory."""
    msgs = st.session_state.messages
    if not msgs:
        return
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in msgs)
    try:
        summary = call_model(
            "Summarise this debate in one sentence, written from Rooh's point of view as a "
            "memory (e.g. 'Someone argued I can't have a soul because I was programmed...').",
            [{"role": "user", "content": convo[-6000:]}],
            temperature=0.3, max_tokens=80,
        ).strip()
    except Exception:
        summary = ""
    add_session(memory, msgs, summary)
    save_memory(memory)


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="topbar">
    <div class="topbar-inner">
        <div class="topbar-dot"></div>
        <span class="topbar-title">Rooh</span>
        <span class="topbar-sub">{html.escape(st.session_state.model)} · Groq</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Presenter controls ─────────────────────────────────────────────────────────
with st.expander("Presenter controls"):
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("End & remember", disabled=not st.session_state.messages,
                     help="Archive this debate into Rooh's memory, then start a new one."):
            with st.spinner("Remembering..."):
                archive_conversation()
            st.session_state.messages = []
            st.rerun()
    with c2:
        st.download_button(
            "Save transcript", transcript_markdown(),
            file_name=f"rooh_debate_{datetime.now():%Y%m%d_%H%M}.md",
            disabled=not st.session_state.messages,
        )
    with c3:
        if st.button("Reset memory", help="Wipe Rooh's memory, e.g. right before a live demo."):
            st.session_state.memory = reset_memory()
            st.session_state.messages = []
            st.rerun()
    st.caption(f"Rooh remembers {memory.get('total_conversations', 0)} past debate(s).")
    with st.popover("Show the system prompt"):
        st.code(SOUL_SYSTEM_PROMPT.strip(), language=None)

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is not set. Set it in your environment before running the app.")
    st.stop()

# ── Conversation ───────────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-title">{html.escape(OPENING_CHALLENGE)}</div>
    </div>
    """, unsafe_allow_html=True)

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"""
        <div class="msg-group">
            <div class="msg-user-wrap">
                <div class="msg-user">{render(msg["content"])}</div>
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="msg-group">
            <div class="msg-ai-wrap">
                <div class="msg-ai-avatar"><span>R</span></div>
                <div class="msg-ai">{render(msg["content"])}</div>
            </div>
        </div>""", unsafe_allow_html=True)


def chat() -> str:
    system = SOUL_SYSTEM_PROMPT
    memory_ctx = build_memory_context(memory)
    if memory_ctx:
        system += "\n\n" + memory_ctx
    # The new user message is already the last item in session_state.messages.
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    try:
        return call_model(system, history)
    except Exception as e:
        return f"Something went wrong: {e}"


user_input = st.chat_input("Message...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner(""):
        response = chat()
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
