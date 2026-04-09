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
    sidebar_background = "#111827" if options.high_contrast else "#f4f3ef"
    card_background = "#111827" if options.high_contrast else "#ffffff"
    soft_background = "#0f172a" if options.high_contrast else "#f7f7f5"
    muted = "#94a3b8" if options.high_contrast else "#aaaaaa"
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
            padding: 0 1.2rem 0.2rem !important;
            max-width: 980px !important;
        }}
        section[data-testid="stSidebar"] {{
            background: {sidebar_background};
            border-right: 1px solid {border_color} !important;
        }}
        section[data-testid="stSidebar"] .block-container {{
            padding-top: 0.55rem !important;
            padding-bottom: 0.8rem !important;
        }}
        .sidebar-brand {{
            padding: 0.2rem 0.15rem 0.75rem;
            border-bottom: 1px solid {border_color};
            margin-bottom: 0.75rem;
        }}
        .sidebar-title {{
            font-size: 0.92rem;
            font-weight: 600;
            color: {foreground};
            letter-spacing: -0.01em;
        }}
        .sidebar-subtitle {{
            font-size: 0.68rem;
            color: {muted};
            margin-top: 0.12rem;
        }}
        .sidebar-caption {{
            font-size: 0.62rem;
            color: {muted};
            margin-top: 0.22rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}
        .sidebar-section-label {{
            font-size: 0.6rem;
            font-weight: 700;
            letter-spacing: 0.09em;
            text-transform: uppercase;
            color: {muted};
            padding: 0.45rem 0.1rem 0.22rem;
        }}
        .sidebar-advanced-spacer {{
            height: 0.5rem;
        }}
        .copilot-hero {{
            padding: 1.3rem 0 0.95rem;
            border-bottom: 1px solid {border_color};
            margin-bottom: 1.15rem;
            color: {foreground};
        }}
        .hero-title {{
            font-size: 1.4rem;
            font-weight: 600;
            color: {foreground};
            letter-spacing: -0.02em;
        }}
        .brand-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            margin-bottom: 0.6rem;
        }}
        .brand-chip {{
            display: inline-flex;
            align-items: center;
            padding: 0.22rem 0.58rem;
            border-radius: 999px;
            background: {soft_background};
            color: {foreground};
            border: 1px solid {border_color};
            font-size: 0.62rem;
            font-weight: 500;
        }}
        .brand-chip-muted {{
            color: {muted};
        }}
        .copilot-subtitle {{
            color: {muted};
            font-size: 0.8rem;
            line-height: 1.6;
        }}
        .session-panel {{
            border-radius: 14px;
            padding: 0.7rem 0.8rem;
            margin-top: 0.4rem;
            color: {foreground};
            background: {card_background};
            border: 1px solid {border_color};
        }}
        .session-item {{
            display: flex;
            justify-content: space-between;
            gap: 0.75rem;
            align-items: center;
            padding: 0.28rem 0;
            color: {muted};
            font-size: 0.72rem;
        }}
        .session-item strong {{
            color: {foreground};
            font-size: 0.75rem;
        }}
        .stButton button, .stDownloadButton button {{
            border-radius: 999px;
            min-height: 2rem;
            border: 1px solid {border_color};
            box-shadow: none !important;
        }}
        div[data-testid="stSidebar"] .stButton > button {{
            width: 100% !important;
            background: {card_background} !important;
            border: 1px solid {border_color} !important;
            border-radius: 14px !important;
            font-size: 0.82rem !important;
            font-weight: 500 !important;
            color: {foreground} !important;
            padding: 0.58rem 0.9rem !important;
            text-align: center !important;
        }}
        div[data-testid="stSidebar"] .stRadio > div {{
            gap: 0.45rem !important;
        }}
        div[data-testid="stSidebar"] .stRadio [role="radiogroup"] {{
            display: flex !important;
            gap: 0.45rem;
            flex-wrap: nowrap;
        }}
        div[data-testid="stSidebar"] .stRadio label {{
            margin: 0 !important;
            width: auto !important;
        }}
        div[data-testid="stSidebar"] .stRadio label > div:first-child {{
            display: none !important;
        }}
        div[data-testid="stSidebar"] .stRadio label p {{
            margin: 0 !important;
            padding: 0.38rem 0.78rem !important;
            border-radius: 999px;
            border: 1px solid {border_color};
            background: {card_background};
            color: {muted};
            font-size: 0.76rem !important;
            font-weight: 500 !important;
        }}
        div[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] input:checked + div + div p,
        div[data-testid="stSidebar"] .stRadio label:has(input:checked) p {{
            color: {foreground};
            background: {soft_background};
            border-color: {foreground};
        }}
        div[data-testid="stSidebar"] .stCaptionContainer p,
        div[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{
            color: {muted} !important;
            font-size: 0.72rem !important;
            line-height: 1.45 !important;
        }}
        div[data-testid="stSidebar"] details {{
            border: none !important;
            background: transparent !important;
        }}
        div[data-testid="stSidebar"] summary {{
            border: 1px solid {border_color} !important;
            border-radius: 14px !important;
            background: {card_background} !important;
            padding: 0.65rem 0.8rem !important;
        }}
        div[data-testid="stSidebar"] summary p {{
            color: {foreground} !important;
            font-size: 0.8rem !important;
            font-weight: 500 !important;
        }}
        div[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{
            border: 1px dashed {border_color} !important;
            border-radius: 14px !important;
            background: transparent !important;
        }}
        .source-card {{
            border-radius: 14px;
            padding: 0.72rem 0.82rem;
            margin-bottom: 0.6rem;
            color: {foreground};
            background: {soft_background};
            border: 1px solid {border_color};
        }}
        .source-title {{
            font-size: 0.74rem;
            font-weight: 500;
            color: {foreground};
        }}
        .source-meta {{
            font-size: 0.65rem;
            color: {muted};
            margin-top: 0.15rem;
        }}
        .source-preview {{
            font-size: 0.7rem;
            color: {muted};
            margin-top: 0.32rem;
            line-height: 1.45;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        .user-row {{
            display: flex;
            justify-content: flex-end;
            margin: 0.15rem 0 0.5rem;
        }}
        .user-bubble {{
            background: {soft_background};
            border: 1px solid {border_color};
            border-radius: 18px 18px 6px 18px;
            padding: 0.7rem 0.95rem;
            font-size: 0.84rem;
            color: {foreground};
            max-width: 66%;
            line-height: 1.55;
        }}
        .answer-shell {{
            border-radius: 10px 18px 18px 18px;
            padding: 1rem 1.05rem;
            margin-bottom: 0.35rem;
            color: {foreground};
            background: {card_background};
            border: 1px solid {border_color};
        }}
        .meta-line {{
            color: {muted};
            font-size: 0.68rem;
            line-height: 1.55;
            margin-top: 0.25rem;
            padding-left: 0.15rem;
        }}
        div[data-testid="stChatMessage"] {{
            padding-top: 0.25rem;
            padding-bottom: 0.25rem;
        }}
        .empty-label {{
            color: {muted};
            font-size: 0.72rem;
            margin-bottom: 0.6rem;
        }}
        div[data-testid="stChatInput"] {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            width: 100%;
        }}
        div[data-testid="stChatInput"] > div {{
            background: {soft_background} !important;
            border: 1px solid {border_color} !important;
            border-radius: 999px !important;
            padding: 0.35rem 0.45rem 0.35rem 0.75rem !important;
            box-shadow: none !important;
        }}
        div[data-testid="stChatInput"] > div:focus-within {{
            border-color: {foreground} !important;
            background: {card_background} !important;
        }}
        div[data-testid="stChatInput"] textarea {{
            font-size: 0.88rem !important;
            color: {foreground} !important;
            background: transparent !important;
        }}
        div[data-testid="stChatInput"] textarea::placeholder {{
            color: {muted} !important;
        }}
        div[data-testid="stChatInput"] button {{
            background: #1a1a18 !important;
            color: #fafaf8 !important;
            border: none !important;
            border-radius: 999px !important;
            min-height: 2.2rem !important;
            padding: 0 1rem !important;
        }}
        .input-toolbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.5rem;
            padding: 0 0.15rem 0.35rem;
            margin-top: 0.9rem;
        }}
        .input-toolbar-left {{
            display: flex;
            gap: 0.45rem;
            align-items: center;
        }}
        .toolbar-pill {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 2rem;
            height: 2rem;
            border-radius: 999px;
            border: 1px solid {border_color};
            background: {card_background};
            color: {muted};
            font-size: 0.78rem;
            padding: 0 0.7rem;
        }}
        .toolbar-icon {{
            padding: 0;
            width: 2rem;
        }}
        .toolbar-mic-active {{
            color: #b42318;
            border-color: #f4c7c3;
            background: #fef3f2;
        }}
        .model-badge {{
            display: inline-flex;
            align-items: center;
            padding: 0.34rem 0.72rem;
            border-radius: 999px;
            background: {card_background};
            color: {muted};
            font-size: 0.7rem;
            font-weight: 500;
            border: 1px solid {border_color};
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
            border-radius: 999px;
            border: 1px solid {border_color};
            background: {soft_background};
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
            color: {foreground};
            letter-spacing: -0.01em;
        }}
        .copilot-footer a {{
            color: {muted};
            text-decoration: none;
            font-size: 11px;
        }}
        .footer-divider {{
            color: {muted};
        }}
        .stButton button:hover, .stDownloadButton button:hover {{
            border-color: {foreground} !important;
            color: {foreground} !important;
            background: {soft_background} !important;
        }}
        div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stChatMessage"]) .stButton button {{
            background: {soft_background} !important;
            color: {foreground} !important;
            border-radius: 999px !important;
            min-height: 1.9rem !important;
            padding: 0 0.85rem !important;
            font-size: 0.74rem !important;
            text-align: center !important;
        }}
        div[data-testid="stExpander"] details {{
            border: 1px solid {border_color} !important;
            border-radius: 14px !important;
            background: {card_background} !important;
        }}
        div[data-testid="stExpander"] summary {{
            padding: 0.75rem 0.85rem !important;
        }}
        div[data-testid="stExpander"] summary p {{
            color: {foreground} !important;
            font-size: 0.8rem !important;
            font-weight: 500 !important;
        }}
        .stChatMessage p, .stMarkdown p {{
            font-size: {font_size};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
