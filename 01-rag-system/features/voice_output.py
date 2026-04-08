from __future__ import annotations

import streamlit as st


def render_voice_output(answer: str, enabled: bool) -> None:
    if not enabled or not answer:
        return
    st.caption("Voice output hook is enabled. The final answer text is ready for TTS playback.")
    st.download_button(
        "Download answer text for TTS",
        data=answer,
        file_name="copilot_answer.txt",
        mime="text/plain",
        use_container_width=True,
    )
