from __future__ import annotations

import io
import os

import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder


def _get_transcript(audio_payload: dict) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    model_name = os.environ.get("OPENAI_STT_MODEL", "gpt-4o-mini-transcribe").strip()
    if not api_key:
        st.warning("Voice input needs OPENAI_API_KEY to transcribe microphone audio.")
        return ""

    audio_bytes = audio_payload.get("bytes")
    audio_format = audio_payload.get("format", "webm")
    if not audio_bytes:
        return ""

    client = OpenAI(api_key=api_key)
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = f"copilot_voice.{audio_format}"
    transcript = client.audio.transcriptions.create(model=model_name, file=audio_file)
    return (getattr(transcript, "text", "") or "").strip()


def render_voice_input() -> tuple[str, bool]:
    st.markdown("### Voice Input")
    st.caption("Use the microphone button to speak your banking question.")

    audio_payload = mic_recorder(
        start_prompt="🎙️",
        stop_prompt="⏹️",
        just_once=True,
        use_container_width=False,
        format="webm",
        key="copilot_mic",
    )
    if not audio_payload:
        return "", False

    last_voice_id = st.session_state.get("last_voice_id")
    current_voice_id = audio_payload.get("id")
    if last_voice_id == current_voice_id:
        return "", True

    with st.spinner("Transcribing your voice input..."):
        transcript = _get_transcript(audio_payload)

    st.session_state.last_voice_id = current_voice_id
    st.session_state.last_voice_transcript = transcript

    if transcript:
        st.success(f"Voice transcript ready: {transcript}")
        return transcript, True

    st.warning("Voice input was recorded, but transcription did not return usable text.")
    return "", True
