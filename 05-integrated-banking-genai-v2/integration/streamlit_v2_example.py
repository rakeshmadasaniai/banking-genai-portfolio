import os

import requests
import streamlit as st


BACKEND_URL = os.environ.get("BANKING_V2_API_URL", "http://127.0.0.1:8000")


def chat_with_v2(message: str, session_id: str, compare: bool = False):
    endpoint = "/chat/compare" if compare else "/chat"
    response = requests.post(
        f"{BACKEND_URL}{endpoint}",
        json={"message": message, "session_id": session_id, "use_memory": True},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


st.title("Banking GenAI Assistant - Version B client example")
session_id = st.text_input("Session ID", value="demo-session")
compare_mode = st.checkbox("Compare OpenAI vs local HF", value=False)
message = st.text_input("Question", value="What is the difference between AML and KYC?")

if st.button("Send"):
    result = chat_with_v2(message, session_id, compare=compare_mode)
    st.json(result)
