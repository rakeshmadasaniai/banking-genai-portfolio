from __future__ import annotations

import streamlit as st


def render_voice_input_toggle() -> bool:
    enabled = st.toggle("Voice mode", value=False, help="Prepares the UI for voice-first workflows.")
    if enabled:
        st.caption("Voice input hook enabled. Add speech-to-text integration later without changing the rest of the app flow.")
    return enabled


def render_voice_input_helper(enabled: bool) -> str:
    if not enabled:
        return ""
    transcript = st.text_input(
        "Voice transcript placeholder",
        value="",
        placeholder="A microphone transcript can flow here in a future upgrade.",
    )
    return transcript.strip()
