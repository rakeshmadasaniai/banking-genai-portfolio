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
    large_text = st.checkbox("Large text", value=False)
    high_contrast = st.checkbox("High contrast", value=False)
    simplified_answers = st.checkbox("Simplified response display", value=False)
    return AccessibilityOptions(True, large_text, high_contrast, simplified_answers)


def apply_accessibility_styles(options: AccessibilityOptions) -> None:
    if not options.enabled:
        return

    font_size = "1.04rem" if options.large_text else "0.95rem"
    contrast = "#0B1220" if options.high_contrast else "#123A6F"
    st.markdown(
        f"""
        <style>
        .answer-shell, .thinking-shell, .user-bubble, .hero-copy, .proof-text, .info-copy {{
          font-size: {font_size} !important;
        }}
        .answer-shell, .thinking-shell {{
          border-width: 1.5px !important;
          border-color: rgba(37,99,235,.24) !important;
        }}
        .meta-pill, .starter-label, .proof-title, .info-title {{
          color: {contrast} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
