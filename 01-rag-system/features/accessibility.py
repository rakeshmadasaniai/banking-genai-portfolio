from __future__ import annotations

from dataclasses import dataclass

import streamlit as st


@dataclass
class AccessibilityOptions:
    enabled: bool
    large_text: bool
    high_contrast: bool
    simplified_answers: bool


def render_accessibility_controls() -> AccessibilityOptions:
    enabled = st.toggle("Accessibility mode", value=False, help="Enable readability-focused response and display options.")
    if not enabled:
        return AccessibilityOptions(False, False, False, False)
    large_text = st.checkbox("Large text", value=True, help="Increase the base reading size across chat and source cards.")
    high_contrast = st.checkbox("High contrast", value=False, help="Increase separation between foreground content and the page background.")
    simplified_answers = st.checkbox(
        "Simplified response display",
        value=False,
        help="Shorten paragraph blocks and keep answer text easier to scan before the source cards.",
    )
    return AccessibilityOptions(True, large_text, high_contrast, simplified_answers)


def apply_accessibility_styles(options: AccessibilityOptions) -> None:
    font_size = "1.08rem" if options.large_text else "0.98rem"
    background = "#0b1120" if options.high_contrast else "#eef4fb"
    foreground = "#f8fafc" if options.high_contrast else "#0f172a"
    accent = "#38bdf8" if options.high_contrast else "#1d4ed8"
    sidebar_background = "#111827" if options.high_contrast else "#f8fbff"
    panel_background = "#111827" if options.high_contrast else "rgba(255,255,255,0.82)"
    border_color = "rgba(148,163,184,0.45)" if options.high_contrast else "rgba(148,163,184,0.18)"
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: #fafaf8;
            color: {foreground};
        }}
        .block-container {{
            max-width: 1000px;
            padding-top: 0.4rem;
            padding-bottom: 1rem;
        }}
        section[data-testid="stSidebar"] {{
            background: #f4f3ef;
            border-right: 1px solid #e8e7e2;
        }}
        section[data-testid="stSidebar"] .block-container {{
            padding-top: 0.35rem;
            padding-bottom: 0.8rem;
        }}
        .sidebar-brand {{
            padding: 0.2rem 0.35rem 0.8rem;
            border-bottom: 1px solid #e8e7e2;
            margin-bottom: 0.8rem;
        }}
        .sidebar-title {{
            font-size: 0.92rem;
            font-weight: 600;
            color: #1a1a18;
            letter-spacing: -0.01em;
        }}
        .sidebar-subtitle {{
            font-size: 0.68rem;
            color: #9a9893;
            margin-top: 0.12rem;
        }}
        .sidebar-section-label {{
            font-size: 0.6rem;
            font-weight: 700;
            letter-spacing: 0.09em;
            text-transform: uppercase;
            color: #b0aea8;
            padding: 0.4rem 0.35rem 0.2rem;
        }}
        .copilot-hero {{
            padding: 1rem 0 0.8rem;
            border-bottom: 1px solid #f0efeb;
            margin-bottom: 1rem;
            color: #1a1a18;
        }}
        .brand-row {{
            display:flex;
            flex-wrap:wrap;
            gap:0.35rem;
            margin-bottom:0.55rem;
        }}
        .brand-chip {{
            display:inline-flex;
            align-items:center;
            padding:0.22rem 0.55rem;
            border-radius:999px;
            background:#e6f1fb;
            color:#1d4ed8;
            font-size:0.62rem;
            font-weight:600;
        }}
        .brand-chip-muted {{
            background:#f0efe9;
            color:#777;
            border: 1px solid #e8e7e2;
        }}
        .copilot-subtitle {{
            color: #aaa;
            font-size: 0.78rem;
            line-height: 1.6;
        }}
        .source-card, .answer-shell, .copilot-footer, .session-panel {{
            background: #fff;
            border: 1px solid #eeede9;
            box-shadow: none;
        }}
        .session-panel {{
            border-radius: 10px;
            padding: 0.8rem 0.9rem;
            margin-top: 0.55rem;
            color: #0f172a;
        }}
        .session-item {{
            display:flex;
            justify-content:space-between;
            gap:0.75rem;
            align-items:center;
            padding:0.28rem 0;
            color:#475569;
            font-size:0.9rem;
        }}
        .session-item strong {{
            color:#0f172a;
            font-size:0.92rem;
        }}
        .stButton button, .stDownloadButton button {{
            border-radius: 12px;
            min-height: 2.6rem;
        }}
        .source-card {{
            border-radius: 8px;
            padding: 0.55rem 0.7rem;
            margin-bottom: 0.6rem;
            color: #0f172a;
            background: #fafaf8;
        }}
        .answer-shell {{
            border-radius: 4px 16px 16px 16px;
            padding: 0.95rem 1rem 0.65rem 1rem;
            margin-bottom: 0.55rem;
            color: #1a1a18;
        }}
        .meta-line {{
            color:#c0bdb6;
            font-size:0.68rem;
            line-height:1.55;
            margin-top:0.45rem;
            padding-left:0.15rem;
        }}
        div[data-testid="stChatMessage"] {{
            padding-top: 0.35rem;
            padding-bottom: 0.35rem;
        }}
        div[data-testid="stChatInput"] {{
            background: #f7f7f5;
            border-radius: 28px;
            border: 1.5px solid #e0deda;
            box-shadow: none;
            padding: 0.2rem 0.28rem;
            width: 100%;
        }}
        div[data-testid="stChatInput"] textarea {{
            font-size: 0.82rem;
            color: #1a1a18;
        }}
        div.stButton > button {{
            background: #ffffff;
            border: 1px solid #d8d7d2;
        }}
        [data-testid="stVerticalBlock"] > [data-testid="stButton"] button {{
            border-radius: 10px;
        }}
        .input-toolbar {{
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:0.5rem;
            padding:0 0.15rem 0.35rem;
            margin-top:0.2rem;
        }}
        .input-toolbar-left {{
            display:flex;
            gap:0.4rem;
            align-items:center;
        }}
        .toolbar-pill {{
            display:inline-flex;
            align-items:center;
            justify-content:center;
            width:1.9rem;
            height:1.9rem;
            border-radius:999px;
            border:1px solid #e8e7e2;
            background:#fff;
            color:#888;
            font-size:0.8rem;
        }}
        .model-badge {{
            display:inline-flex;
            align-items:center;
            padding:0.24rem 0.6rem;
            border-radius:999px;
            background:#eeecea;
            color:#666;
            font-size:0.65rem;
            font-weight:500;
        }}
        .copilot-footer {{
            background: transparent;
            border: none;
            padding: 0.5rem 0 0.9rem;
            margin-top: 0.4rem;
            margin-bottom: 0.2rem;
        }}
        .footer-pill {{
            display:flex;
            flex-wrap:wrap;
            gap:0.55rem;
            align-items:center;
            justify-content:center;
            margin: 0 auto;
            width: fit-content;
            padding: 0.42rem 0.95rem;
            border-radius: 999px;
            border: 1px solid #eeede9;
            background: #fafaf8;
        }}
        .rm-avatar {{
            width: 1.4rem;
            height: 1.4rem;
            border-radius: 999px;
            background: #1a1a18;
            color: #fff;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size: 0.48rem;
            font-weight: 700;
        }}
        .footer-name {{
            font-size: 0.7rem;
            font-weight: 500;
            color: #444;
            letter-spacing: -0.01em;
        }}
        .copilot-footer a {{
            color:#888;
            text-decoration:none;
            font-size:0.68rem;
        }}
        .footer-divider {{
            color:#d0cdc7;
        }}
        .stChatMessage p, .stMarkdown p {{
            font-size: {font_size};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
