from __future__ import annotations

import base64
import html
import io
from datetime import datetime
from statistics import mean

import streamlit as st
import streamlit.components.v1 as components

from features.voice_output import render_voice_output

STARTER_PROMPTS = [
    "English: What are the main KYC requirements for banks?",
    "తెలుగు: బ్యాంకుల్లో KYC కోసం అవసరమైన ప్రధాన పత్రాలు ఏమిటి?",
    "中文: 银行KYC合规最重要的要求是什么？",
    "Español: ¿Cuáles son los requisitos principales de KYC para bancos?",
    "Français: Quelles sont les principales exigences KYC pour les banques ?",
    "Русский: Каковы основные требования KYC для банков?",
]

TECH_ITEMS = [
    ("🤖", "LLM", "OpenAI / Fine-Tuned Model"),
    ("🧠", "Embeddings", "text-embedding-3"),
    ("🗂", "Vector DB", "FAISS / Hybrid"),
    ("🔗", "Framework", "LangChain"),
    ("🖥", "UI", "Streamlit"),
    ("⚙", "Infra", "Python / FastAPI"),
]


def _as_html_text(text: str) -> str:
    return html.escape(str(text)).replace("\n", "<br>")


def _greeting() -> tuple[str, str]:
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning", "🌤"
    if 12 <= hour < 17:
        return "Good afternoon", "☀"
    if 17 <= hour < 21:
        return "Good evening", "🌆"
    return "Good night", "🌙"


def _confidence_value(confidence: str) -> int:
    return {"Low": 35, "Moderate": 68, "High": 92}.get(confidence, 60)


def inject_premium_css() -> None:
    st.markdown(
        """
<style>
:root{
  --bg:#F6F8FC; --bg-soft:#EEF3FA; --panel:#FFFFFF; --text:#0B1220; --muted:#64748B;
  --navy:#123A6F; --blue:#2563EB; --green:#059669; --border:rgba(15,23,42,.08);
  --radius-xl:22px; --radius-lg:18px; --radius-md:14px;
}
html, body, [data-testid="stAppViewContainer"]{background:var(--bg) !important;color:var(--text) !important;color-scheme:light !important;}
.stApp{background:radial-gradient(circle at 18% 0%, rgba(37,99,235,.08), transparent 28%), linear-gradient(180deg, #F8FBFF 0%, #F4F7FC 100%) !important;}
.block-container{max-width:none !important;padding:.12rem .16rem 8rem !important;}
[data-testid="stHeader"]{background:transparent !important;}
#MainMenu, footer{visibility:hidden;}
[data-testid="stSidebar"]{background:var(--bg-soft) !important;border-right:1px solid var(--border) !important;min-width:300px !important;}
[data-testid="stSidebar"] > div{padding-top:4px !important;}
[data-testid="stSidebar"] .stButton > button{width:100% !important;border-radius:12px !important;border:1px solid #1D4ED8 !important;background:linear-gradient(135deg,#2563EB,#0EA5E9) !important;color:#fff !important;font-weight:800 !important;}

.sidebar-brand{display:flex;gap:12px;align-items:center;margin:4px 0 14px;}
.brand-globe{font-size:40px;filter:drop-shadow(0 10px 18px rgba(37,99,235,.18));}
.sidebar-title{font-size:17px;font-weight:900;line-height:1.1;color:#08245A;}
.sidebar-caption{font-size:11px;color:#5E78A8;margin-top:4px;font-weight:600;}
.side-search{height:42px;border:1px solid var(--border);border-radius:14px;background:#fff;color:#94A3B8;display:flex;align-items:center;padding:0 12px;margin:8px 0 18px;font-size:13px;}
.sidebar-section-label{margin:2px 0 10px;font-size:11px;font-weight:900;letter-spacing:.08em;text-transform:uppercase;color:#7A8EAA;}
.side-link-row{display:flex;gap:18px;border-top:1px solid var(--border);padding-top:14px;margin-top:16px;font-weight:700;font-size:12px;}
.side-link-row a{color:#2563EB;text-decoration:none;}
.user-foot{display:flex;align-items:center;gap:10px;border-top:1px solid var(--border);margin-top:16px;padding-top:16px;}
.rm-dot{width:42px;height:42px;border-radius:50%;background:linear-gradient(135deg,#2563EB,#123A6F);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;}
.user-name{font-weight:800;color:#123A6F;font-size:13px;}

.product-shell{background:rgba(255,255,255,.86);border:1px solid var(--border);border-radius:var(--radius-xl);padding:18px;margin:0 0 8px;}
.greeting-row{display:flex;align-items:center;gap:8px;margin:0 0 10px 2px;color:#08245A;font-weight:850;}
.greeting-pill{width:30px;height:30px;border-radius:10px;background:#FFF7ED;border:1px solid #FED7AA;display:flex;align-items:center;justify-content:center;}
.greeting-sub{font-weight:600;color:#29456F;font-size:15px;margin-bottom:18px;}
.hero-card{display:grid;grid-template-columns:112px 1fr 280px;gap:20px;align-items:center;min-height:142px;border:1px solid rgba(37,99,235,.10);border-radius:var(--radius-xl);background:linear-gradient(135deg,rgba(255,255,255,.97),rgba(241,247,255,.90));padding:18px 24px;}
.hero-globe{font-size:78px;}
.hero-title{font-size:30px;font-weight:900;letter-spacing:-.04em;color:#08245A;margin:0 0 8px;}
.hero-copy{font-size:15px;color:#274871;line-height:1.55;}
.bank-art{font-size:82px;opacity:.96;}
.proof-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:16px 0;}
.proof-card,.info-card{background:#fff;border:1px solid var(--border);border-radius:var(--radius-xl);padding:18px;}
.proof-icon{width:42px;height:42px;border-radius:14px;background:#EFF6FF;color:#2563EB;display:flex;align-items:center;justify-content:center;font-size:21px;margin-bottom:10px;}
.proof-title,.info-title{font-weight:900;color:#123A6F;font-size:15px;}
.proof-text,.info-copy{font-size:12.5px;color:var(--muted);line-height:1.55;margin-top:6px;}
.product-info-grid{display:grid;grid-template-columns:1.15fr 1fr;gap:14px;margin:14px 0 22px;}
.tech-row{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:12px;}
.tech-item{text-align:center;font-size:11px;color:#34516F;}
.tech-ico{width:34px;height:34px;border-radius:12px;background:#EFF6FF;margin:0 auto 6px;display:flex;align-items:center;justify-content:center;color:#2563EB;font-size:17px;}

.user-row{display:flex;justify-content:flex-end;margin:0 0 14px;}
.user-bubble{max-width:72%;background:#123A6F;color:#fff;border-radius:16px 16px 4px 16px;padding:12px 18px;font-weight:700;line-height:1.5;font-size:14px;}
.ai-wrap{display:grid;grid-template-columns:54px 1fr;gap:14px;align-items:start;margin:0 0 12px;}
.ai-globe{font-size:44px;line-height:1;}
.answer-shell,.thinking-shell{background:#fff;border:1px solid var(--border);border-radius:var(--radius-lg);padding:18px 20px;font-size:14.5px;line-height:1.72;color:var(--text);}
.thinking-shell{display:flex;align-items:center;gap:10px;min-height:72px;}
.thinking-dot{width:10px;height:10px;border-radius:50%;background:#2563EB;}
.thinking-text{color:#274871;font-weight:700;}
.meta-pills{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;}
.meta-pill{font-size:11px;font-weight:900;border-radius:999px;padding:5px 10px;border:1px solid var(--border);background:#F8FBFF;color:#123A6F;}
.meta-pill.green{background:#ECFDF5;color:#047857;border-color:#BBF7D0;}

.starter-label{margin:6px 0 8px;color:#123A6F;font-size:13px;font-weight:900;}
.stButton > button[id*="starter-"]{width:100% !important;border-radius:12px !important;border:1px solid #1D4ED8 !important;background:linear-gradient(135deg,#2563EB,#0EA5E9) !important;color:#fff !important;font-weight:800 !important;}

div[data-testid="stForm"]:has(.composer-marker){position:fixed !important;left:312px !important;right:8px !important;bottom:8px !important;z-index:90 !important;background:#fff !important;border:1px solid rgba(37,99,235,.14) !important;border-radius:16px !important;padding:8px 10px !important;box-shadow:0 12px 30px rgba(15,23,42,.08) !important;}
@media (max-width:1100px){div[data-testid="stForm"]:has(.composer-marker){left:8px !important;}}
.composer-marker{display:none !important;}
.composer-row [data-testid="stElementContainer"]{margin-bottom:0 !important;}
.composer-row [data-testid="column"]{display:flex;align-items:center;}
.composer-row [data-testid="column"] > div{width:100%;}
div[data-testid="stForm"]:has(.composer-marker) [data-testid="stFormSubmitButton"] button{min-height:44px !important;min-width:56px !important;border-radius:14px !important;background:#123A6F !important;color:#fff !important;border:none !important;}
div[data-testid="stForm"]:has(.composer-marker) div[data-testid="stPopover"] button{min-height:44px !important;min-width:60px !important;border-radius:14px !important;}

@media (max-width:1100px){.hero-card{grid-template-columns:80px 1fr}.bank-art{display:none}.proof-grid,.product-info-grid,.tech-row{grid-template-columns:1fr}}
</style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    greeting, icon = _greeting()
    st.markdown(
        f"""
        <div class="product-shell">
          <div class="greeting-row"><span class="greeting-pill">{icon}</span><span>{html.escape(greeting)}</span></div>
          <div class="greeting-sub">I&#39;m your Banking &amp; Finance Copilot.</div>
          <div class="hero-card">
            <div class="hero-globe">&#127758;</div>
            <div>
              <div class="hero-title">Banking &amp; Finance AI Copilot</div>
              <div class="hero-copy">Your intelligent assistant for banking, compliance, and financial intelligence.<br>
              Ask anything related to AML, KYC, FDIC, Basel III, RBI, regulations, and more. Upload PDF, DOCX, TXT, and image files for grounded answers from your reference material.</div>
            </div>
            <div class="bank-art">&#127974;&#128737;&#65039;</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_homepage_product_intro() -> None:
    proof_cards = [
        ("&#128737;&#65039;", "Source-grounded answers", "Every response is backed by trusted documents with citations."),
        ("&#127760;", "Multilingual workflows", "Use multilingual text, PDF, DOCX, TXT, image, and voice workflows across the app."),
        ("&#9989;", "Evaluation-ready AI system", "Confidence scores, latency, and retrieval insights for transparency."),
    ]
    proof_html = "".join(
        f'<div class="proof-card"><div class="proof-icon">{icon}</div><div class="proof-title">{title}</div><div class="proof-text">{copy}</div></div>'
        for icon, title, copy in proof_cards
    )
    tech_html = "".join(
        f'<div class="tech-item"><div class="tech-ico">{icon}</div><strong>{html.escape(label)}</strong><br>{html.escape(value)}</div>'
        for icon, label, value in TECH_ITEMS
    )
    st.markdown(
        f"""
        <div class="product-shell">
          <div class="proof-grid">{proof_html}</div>
          <div class="product-info-grid">
            <div class="info-card">
              <div class="info-title">About this Copilot</div>
              <div class="info-copy">A product-grade AI assistant for banking and finance professionals. Ask questions, upload documents, and review grounded answers with confidence signals and transparent sources.</div>
            </div>
            <div class="info-card">
              <div class="info-title">Tech Stack</div>
              <div class="tech-row">{tech_html}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_welcome_card() -> None:
    render_homepage_product_intro()


def render_starter_prompts() -> str | None:
    selected = None
    st.markdown('<div class="starter-label">Popular prompts</div>', unsafe_allow_html=True)
    columns = st.columns(3)
    for index, prompt in enumerate(STARTER_PROMPTS):
        with columns[index % 3]:
            if st.button(prompt, key=f"starter-{index}", use_container_width=True):
                selected = prompt
    return selected


def render_about_section() -> None:
    return None


def render_stack_section() -> None:
    return None


def render_sidebar_brand() -> None:
    st.markdown(
        """
        <div class="sidebar-brand">
          <div class="brand-globe">&#127758;</div>
          <div>
            <div class="sidebar-title">Banking &amp; Finance<br>AI Copilot</div>
            <div class="sidebar-caption">Grounded. Trusted. Intelligent.</div>
          </div>
        </div>
        <div class="side-search">&#8989; Search conversations...</div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_summary(base_doc_count: int, upload_doc_count: int, upload_chunk_count: int) -> None:
    st.markdown(
        f"""
        <div style="font-size:12px;color:#48618A;padding:4px 0;display:grid;grid-template-columns:1fr auto;gap:8px;"><span>Base files</span><strong style="color:#123A6F;">{base_doc_count}</strong></div>
        <div style="font-size:12px;color:#48618A;padding:4px 0;display:grid;grid-template-columns:1fr auto;gap:8px;"><span>Uploaded docs</span><strong style="color:#123A6F;">{upload_doc_count}</strong></div>
        <div style="font-size:12px;color:#48618A;padding:4px 0;display:grid;grid-template-columns:1fr auto;gap:8px;"><span>Uploaded chunks</span><strong style="color:#123A6F;">{upload_chunk_count}</strong></div>
        """,
        unsafe_allow_html=True,
    )


def render_session_insights(messages: list[dict]) -> None:
    assistant_messages = [message for message in messages if message.get("role") == "assistant"]
    avg_latency = round(mean(message.get("latency_ms", 0) for message in assistant_messages)) if assistant_messages else 0
    avg_chunks = round(mean(message.get("retrieved_chunks", 0) for message in assistant_messages), 1) if assistant_messages else 0
    st.markdown(
        f"""
        <div style="font-size:12px;color:#48618A;padding:4px 0;display:grid;grid-template-columns:1fr auto;gap:8px;"><span>Answers</span><strong style="color:#123A6F;">{len(assistant_messages)}</strong></div>
        <div style="font-size:12px;color:#48618A;padding:4px 0;display:grid;grid-template-columns:1fr auto;gap:8px;"><span>Avg latency</span><strong style="color:#123A6F;">{avg_latency} ms</strong></div>
        <div style="font-size:12px;color:#48618A;padding:4px 0;display:grid;grid-template-columns:1fr auto;gap:8px;"><span>Avg chunks</span><strong style="color:#123A6F;">{avg_chunks}</strong></div>
        """,
        unsafe_allow_html=True,
    )
    trend = [_confidence_value(str(m.get("confidence", "Moderate"))) for m in assistant_messages[-10:]]
    st.caption("Session trend")
    st.line_chart(trend or [0], height=120)


def render_sidebar_footer() -> None:
    st.markdown(
        """
        <div class="side-link-row">
          <a href="https://github.com/rakeshmadasaniai" target="_blank">GitHub</a>
          <a href="https://www.linkedin.com/in/rakesh-madasani/" target="_blank">LinkedIn</a>
        </div>
        <div class="user-foot">
          <div class="rm-dot">RM</div>
          <div class="user-name">Rakesh Madasani</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_user_message(text: str) -> None:
    st.markdown(f'<div class="user-row"><div class="user-bubble">{_as_html_text(text)}</div></div>', unsafe_allow_html=True)


def _copy_button(answer: str) -> None:
    encoded = base64.b64encode(answer.encode("utf-8")).decode("utf-8")
    components.html(
        f"""
        <button onclick="(function(btn){{
            const raw = atob('{encoded}');
            const bytes = Uint8Array.from(raw, c => c.charCodeAt(0));
            const text = new TextDecoder('utf-8').decode(bytes);
            navigator.clipboard.writeText(text).then(() => {{ btn.innerHTML='Copied'; setTimeout(() => btn.innerHTML='Copy', 1200); }});
        }})(this)"
        style="width:100%;height:38px;border:1px solid rgba(15,23,42,.10);border-radius:12px;background:#fff;color:#123A6F;font-weight:700;cursor:pointer;">
          Copy
        </button>
        """,
        height=42,
    )


def _docx_bytes(answer: str, source_cards: list[dict]) -> bytes:
    try:
        from docx import Document
    except Exception:
        return b""
    document = Document()
    document.add_heading("Banking & Finance Copilot Answer", level=1)
    document.add_paragraph(answer)
    if source_cards:
        document.add_heading("Sources", level=2)
        for card in source_cards[:5]:
            document.add_paragraph(f"{str(card.get('label', 'Source'))}: {str(card.get('preview', ''))[:300]}")
    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()


def render_assistant_message(message: dict, message_key: str, simplified_answers: bool, show_source_cards: bool, show_auto_comparison: bool) -> None:
    answer = str(message.get("answer", "")).strip() if simplified_answers else str(message.get("answer", ""))
    backend_label = str(message.get("backend", "OpenAI")).replace("GPT-4o", "OpenAI")

    st.markdown('<div class="ai-wrap"><div class="ai-globe">&#127758;</div><div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="answer-shell">
          <div class="meta-pills">
            <span class="meta-pill">{html.escape(backend_label)}</span>
            <span class="meta-pill">{html.escape(str(message.get("latency_ms", "--")))} ms</span>
            <span class="meta-pill">{html.escape(str(message.get("retrieved_chunks", "--")))} chunks</span>
            <span class="meta-pill green">{html.escape(str(message.get("confidence", "High")))} confidence</span>
          </div>
          {_as_html_text(answer)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns([1.0, 1.0, 0.9, 0.9, 0.7, 0.7, 4.0])
    with cols[0]:
        render_voice_output(answer, message_key, lang_hint=str(message.get("voice_lang_hint", "") or ""))
    with cols[1]:
        _copy_button(answer)
    with cols[2]:
        st.download_button("TXT", data=answer.encode("utf-8"), file_name=f"copilot-answer-{message_key}.txt", mime="text/plain", key=f"dl-txt-{message_key}", use_container_width=True)
    with cols[3]:
        docx_bytes = _docx_bytes(answer, message.get("source_cards", []))
        if docx_bytes:
            st.download_button("DOCX", data=docx_bytes, file_name=f"copilot-answer-{message_key}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key=f"dl-docx-{message_key}", use_container_width=True)
        else:
            st.button("DOCX", key=f"dl-docx-unavail-{message_key}", disabled=True, use_container_width=True)
    with cols[4]:
        st.button("👍", key=f"up-{message_key}", use_container_width=True)
    with cols[5]:
        st.button("👎", key=f"down-{message_key}", use_container_width=True)

    st.markdown('<div style="font-size:11px;color:#64748B;margin:8px 0 0 2px;">AI can make mistakes. Verify important information with official sources.</div>', unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)


def render_assistant_thinking() -> None:
    st.markdown(
        """
        <div class="ai-wrap">
          <div class="ai-globe">&#127758;</div>
          <div class="thinking-shell"><span class="thinking-dot"></span><span class="thinking-text">Thinking...</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    return None


def enforce_composer_pin() -> None:
    components.html(
        """
<script>
(function () {
  let doc = document;
  try { if (window.parent && window.parent.document) doc = window.parent.document; } catch (_) {}
  function pinComposer() {
    const forms = Array.from(doc.querySelectorAll('div[data-testid="stForm"]')).filter((f) => f.querySelector('.composer-marker'));
    if (!forms.length) return false;
    forms.forEach((form, idx) => { form.style.display = idx === forms.length - 1 ? '' : 'none'; });
    const target = forms[forms.length - 1];
    const mobile = window.innerWidth <= 1100;
    target.style.position = 'fixed';
    target.style.left = mobile ? '8px' : '312px';
    target.style.right = '8px';
    target.style.bottom = '8px';
    target.style.zIndex = '90';
    return true;
  }
  let i = 0;
  const timer = setInterval(() => { i += 1; if (pinComposer() || i > 40) clearInterval(timer); }, 80);
  window.addEventListener('resize', pinComposer);
})();
</script>
        """,
        height=0,
    )
