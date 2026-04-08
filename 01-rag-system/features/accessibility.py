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
        .hero-note {{
            margin-top: 0.65rem;
            color: #64748b;
            line-height: 1.65;
            font-size: 0.94rem;
        }}
        .welcome-card, .source-card, .stat-card, .answer-shell, .copilot-footer {{
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
        .stat-card {{
            border-radius: 18px;
            padding: 0.85rem 0.95rem;
            min-height: 88px;
            margin: 0.15rem 0 0.45rem 0;
            color: #0f172a;
        }}
        .stat-label {{
            font-size: 0.78rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }}
        .stat-value {{
            font-size: 1.75rem;
            font-weight: 800;
            line-height: 1.1;
            color: #0f172a;
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
            margin:0.25rem 0 0.8rem 0;
            padding:0.2rem 0;
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
            font-size:0.88rem;
            font-weight:600;
        }}
        .meta-pill {{
            display: inline-block;
            margin: 0.1rem 0.35rem 0.35rem 0;
            padding: 0.28rem 0.58rem;
            border-radius: 999px;
            background: rgba(29,78,216,0.12);
            color: {accent};
            font-size: 0.82rem;
            font-weight: 700;
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
