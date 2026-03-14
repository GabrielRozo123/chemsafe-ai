from __future__ import annotations

import streamlit as st


def init_state() -> None:
    defaults = {
        'selected_compound': None,
        'history': [],
        'hazop_result': None,
        'lopa_result': None,
        'dispersion_result': None,
        'pool_fire_result': None,
        'copilot_messages': [],
        'knowledge_base': None,
        'uploaded_docs': [],
        'report_payload': {},
        'doc_insights': None,
        'risk_register': [],
        'last_case_name': 'untitled_case',
        'report_bundle': None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
