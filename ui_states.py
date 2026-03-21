from __future__ import annotations

import streamlit as st


def render_empty_state(
    title: str,
    message: str,
    icon: str = "ℹ️",
) -> None:
    st.markdown(
        f"""
        <div class="panel" style="text-align:center; padding: 28px 24px;">
            <div style="font-size: 2rem; margin-bottom: 10px;">{icon}</div>
            <div style="font-size: 1.05rem; font-weight: 800; color: #f4f8fd; margin-bottom: 8px;">
                {title}
            </div>
            <div style="color: #9fb0c7; font-size: 0.95rem; line-height: 1.6; max-width: 700px; margin: 0 auto;">
                {message}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_success_state(
    title: str,
    message: str,
    icon: str = "✅",
) -> None:
    st.markdown(
        f"""
        <div class="panel" style="border-color: rgba(52,211,153,0.28); text-align:center; padding: 24px 22px;">
            <div style="font-size: 1.9rem; margin-bottom: 10px;">{icon}</div>
            <div style="font-size: 1.02rem; font-weight: 800; color: #ecfdf5; margin-bottom: 8px;">
                {title}
            </div>
            <div style="color: #b7f7de; font-size: 0.94rem; line-height: 1.6; max-width: 700px; margin: 0 auto;">
                {message}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_error_state(
    title: str,
    message: str,
    icon: str = "⚠️",
) -> None:
    st.markdown(
        f"""
        <div class="panel" style="border-color: rgba(248,113,113,0.28); text-align:center; padding: 24px 22px;">
            <div style="font-size: 1.9rem; margin-bottom: 10px;">{icon}</div>
            <div style="font-size: 1.02rem; font-weight: 800; color: #fef2f2; margin-bottom: 8px;">
                {title}
            </div>
            <div style="color: #fecaca; font-size: 0.94rem; line-height: 1.6; max-width: 700px; margin: 0 auto;">
                {message}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
