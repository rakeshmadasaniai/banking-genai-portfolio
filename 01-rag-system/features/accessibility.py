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
            background:
                radial-gradient(circle at top, rgba(191,219,254,0.45), transparent 34%),
                linear-gradient(180deg, {background} 0%, #f8fbff 100%);
            color: {foreground};
        }}
        .block-container {{
            max-width: 1080px;
            padding-top: 1.2rem;
            padding-bottom: 1.6rem;
        }}
        section[data-testid="stSidebar"] {{
            background: {sidebar_background};
            border-right: 1px solid {border_color};
        }}
        section[data-testid="stSidebar"] .block-container {{
            padding-top: 1rem;
            padding-bottom: 1rem;
        }}
        .copilot-hero {{
            background: linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(248,250,252,0.94) 100%);
            border-radius: 24px;
            padding: 1.35rem 1.45rem;
            border: 1px solid {border_color};
            box-shadow: 0 18px 38px rgba(15,23,42,0.08);
            margin-bottom: 0.9rem;
            color: #0f172a;
        }}
        .brand-row {{
            display:flex;
            flex-wrap:wrap;
            gap:0.45rem;
            margin-bottom:0.75rem;
        }}
        .brand-chip {{
            display:inline-flex;
            align-items:center;
            padding:0.28rem 0.62rem;
            border-radius:999px;
            background:#dbeafe;
            color:#1d4ed8;
            font-size:0.78rem;
            font-weight:700;
            letter-spacing:0.02em;
            text-transform:uppercase;
        }}
        .brand-chip-muted {{
            background:#e2e8f0;
            color:#334155;
        }}
        .copilot-subtitle {{
            color: #475569;
            font-size: {font_size};
            line-height: 1.6;
        }}
        .welcome-card, .source-card, .answer-shell, .copilot-footer, .session-panel {{
            background: {panel_background};
            border: 1px solid {border_color};
            box-shadow: 0 14px 28px rgba(15,23,42,0.05);
        }}
        .welcome-card {{
            border-radius: 20px;
            padding: 1rem 1.05rem;
            margin-bottom: 0.45rem;
            color: #0f172a;
        }}
        .session-panel {{
            border-radius: 18px;
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
            border-radius: 16px;
            padding: 0.8rem 0.9rem;
            margin-bottom: 0.6rem;
            color: #0f172a;
        }}
        .answer-shell {{
            border-radius: 18px;
            padding: 0.95rem 1rem 0.55rem 1rem;
            margin-bottom: 0.55rem;
            color: #0f172a;
        }}
        .composer-shell {{
            display:flex;
            flex-wrap:wrap;
            gap:0.55rem;
            margin:0.4rem 0 0.75rem 0;
            padding:0.18rem 0;
        }}
        .composer-chip {{
            display:inline-flex;
            align-items:center;
            gap:0.35rem;
            padding:0.45rem 0.8rem;
            border-radius:999px;
            border:1px solid {border_color};
            background: rgba(255,255,255,0.9);
            color:#334155;
            font-size:0.84rem;
            font-weight:600;
        }}
        .meta-line {{
            color:#64748b;
            font-size:0.84rem;
            line-height:1.55;
            margin-top:0.55rem;
        }}
        div[data-testid="stChatMessage"] {{
            padding-top: 0.35rem;
            padding-bottom: 0.35rem;
        }}
        div[data-testid="stChatInput"] {{
            background: rgba(255,255,255,0.95);
            border-radius: 18px;
            border: 1px solid {border_color};
            box-shadow: 0 12px 28px rgba(15,23,42,0.08);
            padding: 0.15rem 0.2rem;
        }}
        div[data-testid="stChatInput"] textarea {{
            font-size: 1rem;
        }}
        div.stButton > button {{
            background: rgba(255,255,255,0.92);
            border: 1px solid {border_color};
        }}
        [data-testid="stVerticalBlock"] > [data-testid="stButton"] button {{
            border-radius: 14px;
        }}
        .copilot-footer {{
            border-radius: 20px;
            padding: 1rem 1.1rem;
            margin-top: 1rem;
            margin-bottom: 0.4rem;
            color: #0f172a;
        }}
        .copilot-footer-note {{
            color: #475569;
            line-height: 1.7;
            margin-bottom: 0.55rem;
        }}
        .copilot-footer-meta {{
            display:flex;
            flex-wrap:wrap;
            gap:0.45rem;
            align-items:center;
            color:#334155;
            font-size:0.92rem;
        }}
        .copilot-footer-meta a {{
            color:#1d4ed8;
            text-decoration:none;
            font-weight:600;
        }}
        .footer-divider {{
            color:#94a3b8;
        }}
        .stChatMessage p, .stMarkdown p {{
            font-size: {font_size};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
