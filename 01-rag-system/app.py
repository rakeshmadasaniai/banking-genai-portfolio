import streamlit as st

from core.product_runtime import run_product_runtime

if "risk_profile" not in st.session_state:
    st.session_state.risk_profile = None

if "investment_goal" not in st.session_state:
    st.session_state.investment_goal = None

if "liquidity_need" not in st.session_state:
    st.session_state.liquidity_need = None

if "investment_horizon" not in st.session_state:
    st.session_state.investment_horizon = None


def update_investment_memory(user_query: str) -> None:
    q = user_query.lower()

    if "conservative" in q:
        st.session_state.risk_profile = "conservative"
    elif "moderate" in q:
        st.session_state.risk_profile = "moderate"
    elif "aggressive" in q:
        st.session_state.risk_profile = "aggressive"

    if "growth" in q:
        st.session_state.investment_goal = "growth"
    elif "income" in q:
        st.session_state.investment_goal = "income"
    elif "preservation" in q or "protect" in q:
        st.session_state.investment_goal = "capital preservation"
    elif "retirement" in q:
        st.session_state.investment_goal = "retirement"

    if "1 year" in q or "2 years" in q or "3 years" in q or "short term" in q:
        st.session_state.liquidity_need = "high"
    elif "long term" in q or "10 years" in q or "ten years" in q:
        st.session_state.liquidity_need = "low"

    if "10 years" in q or "ten years" in q:
        st.session_state.investment_horizon = "10 years"
    elif "5 years" in q or "five years" in q:
        st.session_state.investment_horizon = "5 years"


pending_query = st.session_state.get("pending_question", "")
if pending_query:
    update_investment_memory(pending_query)

run_product_runtime()
st.stop()
