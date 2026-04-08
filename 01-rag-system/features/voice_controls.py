from __future__ import annotations

import io
import os

import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder


def _transcribe_audio(audio_payload: dict) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    model_name = os.environ.get("OPENAI_STT_MODEL", "gpt-4o-mini-transcribe").strip()
    if not api_key:
        st.warning("Voice Input (Preview) needs OPENAI_API_KEY to transcribe microphone audio.")
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


def render_voice_input_preview() -> tuple[str, bool]:
    st.markdown("### Voice Input (Preview)")
    st.caption("Browser microphone capture with cloud transcription. Best effort on supported browsers.")

    audio_payload = mic_recorder(
        start_prompt="\U0001F399 Start recording",
        stop_prompt="\u23F9 Stop recording",
        just_once=True,
        use_container_width=False,
        format="webm",
        key="copilot_mic_preview",
    )
    if not audio_payload:
        return "", False

    current_voice_id = audio_payload.get("id")
    if st.session_state.get("last_voice_id") == current_voice_id:
        return "", True

    with st.spinner("Transcribing your voice input..."):
        transcript = _transcribe_audio(audio_payload)

    st.session_state.last_voice_id = current_voice_id
    st.session_state.last_voice_transcript = transcript

    if transcript:
        st.success(f"Transcript ready: {transcript}")
        return transcript, True

    st.warning("The recording was captured, but transcription did not return usable text.")
    return "", True
