from __future__ import annotations

import hashlib
import os

import streamlit as st
from openai import OpenAI


def _audio_cache_key(message_key: str, answer: str) -> str:
    digest = hashlib.md5(answer.encode("utf-8")).hexdigest()[:10]
    return f"tts::{message_key}::{digest}"


def _generate_audio(answer: str) -> bytes | None:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        st.info("Read Answer Aloud needs OPENAI_API_KEY so the app can generate speech.")
        return None

    client = OpenAI(api_key=api_key)
    model_name = os.environ.get("OPENAI_TTS_MODEL", "gpt-4o-mini-tts").strip()
    voice_name = os.environ.get("OPENAI_TTS_VOICE", "alloy").strip()
    response = client.audio.speech.create(
        model=model_name,
        voice=voice_name,
        input=answer[:4000],
        response_format="mp3",
    )
    if hasattr(response, "read"):
        return response.read()
    if hasattr(response, "content"):
        return response.content
    return None


def render_voice_output(answer: str, message_key: str) -> None:
    if not answer:
        return

    cache_key = _audio_cache_key(message_key, answer)
    if "generated_audio" not in st.session_state:
        st.session_state.generated_audio = {}

    button_key = f"tts-button-{message_key}"
    if st.button("Read Answer Aloud", key=button_key, use_container_width=False):
        with st.spinner("Generating spoken answer..."):
            audio_bytes = _generate_audio(answer)
        if audio_bytes:
            st.session_state.generated_audio[cache_key] = audio_bytes

    if cache_key in st.session_state.generated_audio:
        st.caption("AI-generated voice preview")
        st.audio(st.session_state.generated_audio[cache_key], format="audio/mp3")
