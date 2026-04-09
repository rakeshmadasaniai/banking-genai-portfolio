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
    font_size = "1.04rem" if options.large_text else "0.96rem"
    background = "#111827" if options.high_contrast else "#F5F7FA"
    card_background = "#0F172A" if options.high_contrast else "#FFFFFF"
    sidebar_background = "#111827" if options.high_contrast else "#FFFFFF"
    foreground = "#F9FAFB" if options.high_contrast else "#111827"
    secondary = "#CBD5E1" if options.high_contrast else "#6B7280"
    accent = "#60A5FA" if options.high_contrast else "#2563EB"
    hover = "rgba(96,165,250,0.18)" if options.high_contrast else "#DBEAFE"
    border = "rgba(148,163,184,0.35)" if options.high_contrast else "#E5E7EB"
    input_border = "rgba(148,163,184,0.45)" if options.high_contrast else "#D1D5DB"
    success_bg = "rgba(34,197,94,0.15)" if options.high_contrast else "#DCFCE7"
    success_fg = "#BBF7D0" if options.high_contrast else "#166534"
    warning_bg = "rgba(245,158,11,0.15)" if options.high_contrast else "#FEF3C7"
    warning_fg = "#FDE68A" if options.high_contrast else "#92400E"

    st.markdown(
        f"""
        <style>
        #MainMenu, header, footer {{ visibility: hidden; }}
        .stDeployButton {{ display: none !important; }}
        .stApp, .stApp > div {{ background: {background} !important; color: {foreground}; }}
        .block-container {{ max-width: 1040px !important; padding: 0.9rem 1.3rem 1rem !important; }}
        section[data-testid="stSidebar"] {{ background: {sidebar_background} !important; border-right: 1px solid {border} !important; min-width: 290px !important; }}
        section[data-testid="stSidebar"] .block-container {{ padding: 0.85rem 0.9rem 0.75rem !important; display: flex; flex-direction: column; min-height: 100vh; }}

        .sidebar-brand {{ padding-bottom: 0.85rem; margin-bottom: 0.85rem; border-bottom: 1px solid {border}; }}
        .sidebar-title {{ font-size: 1rem; font-weight: 700; color: {foreground}; letter-spacing: -0.02em; }}
        .sidebar-subtitle {{ font-size: 0.72rem; color: {secondary}; margin-top: 0.16rem; }}
        .sidebar-caption {{ font-size: 0.68rem; color: {secondary}; margin-top: 0.35rem; }}
        .sidebar-bottom {{ margin-top: auto; padding-top: 0.8rem; border-top: 1px solid {border}; }}
        .sidebar-links {{ display: flex; gap: 0.7rem; flex-wrap: wrap; margin-top: 0.75rem; }}
        .sidebar-links a {{ color: {secondary}; text-decoration: none; font-size: 0.8rem; }}
        .sidebar-links a:hover {{ color: {accent}; }}

        .hero-wrap {{ text-align: center; padding: 1.1rem 0 0.8rem; }}
        .brand-row {{ display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.75rem; }}
        .brand-row-centered {{ justify-content: center; }}
        .brand-chip {{ display: inline-flex; align-items: center; padding: 0.28rem 0.75rem; border-radius: 999px; background: {card_background}; border: 1px solid {border}; color: {secondary}; font-size: 0.74rem; font-weight: 600; }}
        .grounded-chip {{ background: {success_bg}; color: {success_fg}; border-color: transparent; }}
        .hero-title {{ margin: 0; font-size: 38px; line-height: 1.08; font-weight: 800; color: {foreground}; letter-spacing: -0.03em; }}
        .hero-tagline {{ margin-top: 0.8rem; font-size: 18px; font-weight: 500; color: {foreground}; }}
        .hero-oneliner {{ margin-top: 0.65rem; font-size: 15px; color: {secondary}; }}
        .hero-description {{ margin: 0.85rem auto 0; max-width: 760px; font-size: 15px; line-height: 1.7; color: {secondary}; }}
        .hero-divider {{ height: 1px; background: {border}; margin-top: 1.2rem; }}
        .welcome-card {{ margin: 1rem auto 0.25rem; max-width: 760px; }}
        .welcome-title {{ font-size: 1rem; font-weight: 700; color: {foreground}; margin-bottom: 0.55rem; }}
        .welcome-copy {{ font-size: 0.94rem; color: {secondary}; line-height: 1.72; }}

        .starter-label {{ text-align: center; color: {secondary}; font-size: 0.84rem; margin: 1.2rem 0 0.9rem; }}
        .stButton button, .stDownloadButton button {{ border-radius: 14px; border: 1px solid {border}; box-shadow: none !important; min-height: 2.15rem; }}
        .stButton button:hover, .stDownloadButton button:hover {{ background: {hover} !important; border-color: {accent} !important; color: {foreground} !important; }}
        div[data-testid="stSidebar"] .stButton > button {{ width: 100% !important; background: {card_background} !important; color: {foreground} !important; text-align: left !important; padding: 0.7rem 0.9rem !important; border-radius: 14px !important; }}

        div[data-testid="stSidebar"] .stRadio [role="radiogroup"] {{ display: grid !important; gap: 0.35rem !important; }}
        div[data-testid="stSidebar"] .stRadio label > div:first-child {{ display: none !important; }}
        div[data-testid="stSidebar"] .stRadio label p {{ margin: 0 !important; padding: 0.68rem 0.82rem !important; border-radius: 12px; border: 1px solid transparent; color: {secondary}; font-size: 0.82rem !important; }}
        div[data-testid="stSidebar"] .stRadio label:has(input:checked) p {{ background: {hover}; color: {foreground}; border-color: {accent}; }}
        div[data-testid="stSidebar"] .stRadio label:hover p {{ background: {hover}; }}

        .chat-link {{ padding: 0.68rem 0.82rem; border-radius: 12px; color: {secondary}; font-size: 0.82rem; }}
        .chat-link-active {{ background: {hover}; color: {foreground}; border: 1px solid {accent}; }}

        div[data-testid="stExpander"] details {{ border: 1px solid {border} !important; border-radius: 14px !important; background: {card_background} !important; }}
        div[data-testid="stExpander"] summary {{ padding: 0.82rem 0.9rem !important; }}
        div[data-testid="stExpander"] summary p {{ color: {foreground} !important; font-size: 0.86rem !important; font-weight: 600 !important; }}
        .session-panel {{ border: 1px solid {border}; border-radius: 14px; background: {card_background}; padding: 0.75rem 0.9rem; margin-top: 0.75rem; }}
        .session-item {{ display: flex; justify-content: space-between; padding: 0.26rem 0; font-size: 0.74rem; color: {secondary}; }}
        .session-item strong {{ color: {foreground}; }}

        div[data-testid="stChatMessage"] {{ padding: 0.3rem 0 !important; }}
        .user-row {{ display: flex; justify-content: flex-end; margin: 0.2rem 0 0.6rem; }}
        .user-bubble {{ max-width: 66%; background: #F3F4F6; color: {foreground}; border: 1px solid {border}; border-radius: 18px 18px 6px 18px; padding: 0.82rem 1rem; font-size: 15px; line-height: 1.6; }}
        .answer-shell {{ background: {card_background}; color: {foreground}; border: 1px solid {border}; border-radius: 14px; padding: 1rem 1.05rem; font-size: 15px; line-height: 1.72; }}
        .thinking-line {{ display: inline-flex; align-items: center; gap: 0.45rem; padding: 0.42rem 0.72rem; background: {card_background}; border: 1px solid {border}; border-radius: 999px; font-size: 0.8rem; color: {secondary}; }}
        .typing-cursor {{ color: {accent}; animation: blink 1s steps(1) infinite; }}
        @keyframes blink {{ 50% {{ opacity: 0; }} }}
        .meta-line {{ margin-top: 0.45rem; color: {secondary}; font-size: 12px; }}
        .warning-pill {{ margin-bottom: 0.65rem; padding: 0.55rem 0.8rem; background: {warning_bg}; color: {warning_fg}; border-radius: 12px; font-size: 0.8rem; border: 1px solid transparent; }}

        .source-card {{ background: {background}; border: 1px solid {border}; border-radius: 14px; padding: 0.78rem 0.9rem; margin-bottom: 0.65rem; }}
        .source-title {{ font-size: 0.82rem; font-weight: 600; color: {foreground}; }}
        .source-meta {{ font-size: 0.7rem; color: {secondary}; margin-top: 0.18rem; }}
        .source-preview {{ margin-top: 0.4rem; font-size: 0.76rem; line-height: 1.55; color: {secondary}; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}

        .composer-shell {{ position: relative; max-width: 1120px; margin: 1rem auto 0; }}
        .composer-tools {{ position: absolute; left: 0.9rem; right: 0.9rem; top: 0.78rem; display: flex; align-items: center; gap: 0.7rem; z-index: 20; pointer-events: none; }}
        .composer-control {{ display: flex; align-items: center; }}
        .composer-control, .composer-tools div[data-testid="stPopover"], .composer-tools div[data-testid="stSelectbox"] {{ pointer-events: auto; }}
        .composer-shell div[data-testid="stPopover"] button {{ border-radius: 999px !important; min-height: 2.05rem !important; padding: 0 0.75rem !important; background: transparent !important; color: #4B5563 !important; border: 1px solid transparent !important; box-shadow: none !important; }}
        .composer-shell div[data-testid="stPopover"] button:hover {{ background: #F3F4F6 !important; color: #111827 !important; }}
        .mic-live div[data-testid="stPopover"] button, .mic-live div[data-testid="stPopover"] button:hover {{ color: #B91C1C !important; background: #FEE2E2 !important; border-color: #FECACA !important; }}
        .composer-shell div[data-testid="stSelectbox"] > div[data-baseweb="select"] > div {{ min-height: 2.05rem !important; border-radius: 999px !important; background: transparent !important; color: #374151 !important; border: 1px solid transparent !important; padding-left: 0.2rem !important; box-shadow: none !important; }}
        .composer-shell div[data-testid="stSelectbox"] svg {{ fill: #6B7280 !important; }}

        div[data-testid="stChatInput"] {{ background: transparent !important; border: none !important; padding: 0 !important; box-shadow: none !important; }}
        div[data-testid="stChatInput"] > div {{ background: #FFFFFF !important; border: 1px solid {input_border} !important; border-radius: 26px !important; padding: 3.2rem 0.9rem 0.95rem 0.95rem !important; }}
        div[data-testid="stChatInput"] > div:focus-within {{ border-color: {accent} !important; box-shadow: none !important; }}
        div[data-testid="stChatInput"] textarea {{ font-size: 18px !important; line-height: 1.5 !important; color: #111827 !important; background: transparent !important; min-height: 3.2rem !important; padding: 0.1rem 0.1rem 0.35rem !important; }}
        div[data-testid="stChatInput"] textarea::placeholder {{ color: #9CA3AF !important; }}
        div[data-testid="stChatInput"] button {{ background: #111827 !important; color: #FFFFFF !important; border: none !important; border-radius: 999px !important; min-height: 2.5rem !important; min-width: 2.5rem !important; padding: 0 !important; }}
        div[data-testid="stChatInput"] button:hover {{ background: #1F2937 !important; }}

        .safety-note {{ max-width: 720px; text-align: center; color: {secondary}; font-size: 11px; line-height: 1.5; margin: 0.5rem auto 0; opacity: 0.78; }}
        .copilot-footer {{ padding: 0.65rem 0 0.4rem; }}
        .footer-pill {{ display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 0.65rem; margin: 0 auto; width: fit-content; padding: 0.55rem 1rem; border-radius: 999px; border: 1px solid {border}; background: {card_background}; }}
        .rm-avatar {{ width: 24px; height: 24px; border-radius: 999px; background: {foreground}; color: {card_background}; display: flex; align-items: center; justify-content: center; font-size: 0.58rem; font-weight: 700; }}
        .footer-name {{ font-size: 0.82rem; font-weight: 600; color: {foreground}; letter-spacing: -0.01em; }}
        .footer-divider {{ color: {secondary}; }}
        .copilot-footer a {{ color: {secondary}; text-decoration: none; font-size: 0.82rem; }}
        .copilot-footer a:hover {{ color: {accent}; }}

        .stMarkdown p, .stChatMessage p {{ font-size: {font_size}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
