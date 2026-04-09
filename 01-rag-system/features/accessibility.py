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
    background = "#0b1120" if options.high_contrast else "#fafaf8"
    foreground = "#f8fafc" if options.high_contrast else "#0f172a"
    border_color = "rgba(148,163,184,0.45)" if options.high_contrast else "#e8e7e2"
    st.markdown(
        f"""
        <style>
        #MainMenu, footer, header {{
            visibility: hidden;
        }}
        .stDeployButton {{
            display: none !important;
        }}
        .stApp {{
            background: {background} !important;
            color: {foreground};
        }}
        .stApp > div {{
            background: {background} !important;
        }}
        .block-container {{
            padding: 0 !important;
            max-width: 100% !important;
        }}
        section[data-testid="stSidebar"] {{
            background: #f4f3ef;
            border-right: 1px solid #e8e7e2 !important;
        }}
        section[data-testid="stSidebar"] .block-container {{
            padding-top: 0.35rem !important;
            padding-bottom: 0.8rem !important;
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
            padding: 1.1rem 0 0.85rem;
            border-bottom: 1px solid #f0efeb;
            margin-bottom: 1rem;
            color: #1a1a18;
        }}
        .hero-title {{
            font-size: 18px;
            font-weight: 600;
            color: #1a1a18;
            letter-spacing: -0.02em;
        }}
        .brand-row {{
            display:flex;
            flex-wrap:wrap;
            gap:6px;
            margin-bottom:9px;
        }}
        .brand-chip {{
            display:inline-flex;
            align-items:center;
            padding:3px 9px;
            border-radius:999px;
            background:#e6f1fb;
            color:#0C447C;
            font-size:10px;
            font-weight:500;
        }}
        .brand-chip-muted {{
            background:#f0efe9;
            color:#777;
            border: 1px solid #e8e7e2;
        }}
        .copilot-subtitle {{
            color: #aaa;
            font-size: 12px;
            line-height: 1.6;
        }}
        .session-panel {{
            border-radius: 8px;
            padding: 0.7rem 0.8rem;
            margin-top: 0.4rem;
            color: #0f172a;
            background:#fff;
            border:1px solid #eeede9;
        }}
        .session-item {{
            display:flex;
            justify-content:space-between;
            gap:0.75rem;
            align-items:center;
            padding:0.28rem 0;
            color:#777;
            font-size:0.72rem;
        }}
        .session-item strong {{
            color:#1a1a18;
            font-size:0.75rem;
        }}
        .stButton button, .stDownloadButton button {{
            border-radius: 10px;
            min-height: 2.3rem;
        }}
        div[data-testid="stSidebar"] .stButton > button {{
            width: 100% !important;
            background: #ffffff !important;
            border: 1px solid #d8d7d2 !important;
            border-radius: 10px !important;
            font-size: 12px !important;
            font-weight: 500 !important;
            color: #1a1a18 !important;
            padding: 8px 10px !important;
            text-align: left !important;
        }}
        .source-card {{
            border-radius: 8px;
            padding: 0.55rem 0.7rem;
            margin-bottom: 0.6rem;
            color: #0f172a;
            background: #fafaf8;
            border: 1px solid #eeede9;
        }}
        .source-title {{
            font-size: 11px;
            font-weight: 500;
            color: #1a1a18;
        }}
        .source-meta {{
            font-size: 10px;
            color: #aaa;
            margin-top: 2px;
        }}
        .source-preview {{
            font-size: 10px;
            color: #7d7a74;
            margin-top: 4px;
            line-height: 1.45;
        }}
        .user-row {{
            display: flex;
            justify-content: flex-end;
            margin: 4px 0;
        }}
        .user-bubble {{
            background: #f4f3ef;
            border: 1px solid #e8e7e2;
            border-radius: 16px 16px 4px 16px;
            padding: 10px 14px;
            font-size: 13px;
            color: #1a1a18;
            max-width: 66%;
            line-height: 1.55;
        }}
        .answer-shell {{
            border-radius: 4px 16px 16px 16px;
            padding: 14px 16px;
            margin-bottom: 0.28rem;
            color: #1a1a18;
            background: #fff;
            border: 1px solid #eeede9;
        }}
        .meta-line {{
            color:#c0bdb6;
            font-size:10px;
            line-height:1.55;
            margin-top:5px;
            padding-left:0.15rem;
        }}
        div[data-testid="stChatMessage"] {{
            padding-top: 0.15rem;
            padding-bottom: 0.15rem;
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
            font-size: 13px;
            color: #1a1a18;
        }}
        .input-toolbar {{
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:8px;
            padding:0 2px 4px;
            margin-top:0.2rem;
        }}
        .input-toolbar-left {{
            display:flex;
            gap:8px;
            align-items:center;
        }}
        .toolbar-pill {{
            display:inline-flex;
            align-items:center;
            justify-content:center;
            min-width:32px;
            height:32px;
            border-radius:999px;
            border:1px solid #e8e7e2;
            background:#fff;
            color:#888;
            font-size:11px;
            padding: 0 8px;
        }}
        .model-badge {{
            display:inline-flex;
            align-items:center;
            padding:3px 11px;
            border-radius:999px;
            background:#eeecea;
            color:#666;
            font-size:10px;
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
            gap:10px;
            align-items:center;
            justify-content:center;
            margin: 0 auto;
            width: fit-content;
            padding: 6px 18px;
            border-radius: 30px;
            border: 1px solid #eeede9;
            background: #fafaf8;
        }}
        .rm-avatar {{
            width: 22px;
            height: 22px;
            border-radius: 999px;
            background: #1a1a18;
            color: #fff;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size: 8px;
            font-weight: 700;
        }}
        .footer-name {{
            font-size: 11px;
            font-weight: 500;
            color: #444;
            letter-spacing: -0.01em;
        }}
        .copilot-footer a {{
            color:#888;
            text-decoration:none;
            font-size:11px;
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
