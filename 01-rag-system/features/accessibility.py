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
    enabled = st.toggle("Accessibility mode", value=False)
    if not enabled:
        return AccessibilityOptions(False, False, False, False)
    large_text = st.checkbox("Large text", value=True)
    high_contrast = st.checkbox("High contrast", value=False)
    simplified_answers = st.checkbox("Simplified response display", value=False)
    return AccessibilityOptions(True, large_text, high_contrast, simplified_answers)


def apply_accessibility_styles(options: AccessibilityOptions) -> None:
    font_size = "1.08rem" if options.large_text else "0.98rem"
    background = "#0f172a" if options.high_contrast else "#f7fafc"
    foreground = "#f8fafc" if options.high_contrast else "#0f172a"
    accent = "#38bdf8" if options.high_contrast else "#1d4ed8"
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: {background};
            color: {foreground};
        }}
        .block-container {{
            max-width: 1220px;
            padding-top: 1.4rem;
            padding-bottom: 2rem;
        }}
        .copilot-hero {{
            background: rgba(255,255,255,0.92);
            border-radius: 22px;
            padding: 1.25rem 1.3rem;
            border: 1px solid rgba(15,23,42,0.08);
            box-shadow: 0 14px 34px rgba(15,23,42,0.08);
            margin-bottom: 1rem;
            color: #0f172a;
        }}
        .copilot-subtitle {{
            color: #475569;
            font-size: {font_size};
            line-height: 1.6;
        }}
        .source-card {{
            border: 1px solid rgba(29,78,216,0.12);
            border-radius: 16px;
            padding: 0.8rem 0.9rem;
            background: rgba(255,255,255,0.95);
            margin-bottom: 0.6rem;
            color: #0f172a;
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
        .stChatMessage p, .stMarkdown p {{
            font-size: {font_size};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
