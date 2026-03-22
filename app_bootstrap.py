from __future__ import annotations

import streamlit as st

MENU_STYLES = {
    "container": {
        "padding": "5px",
        "background-color": "#151b28",
        "border": "1px solid #2a3441",
        "border-radius": "10px",
        "margin-bottom": "20px",
    },
    "icon": {"color": "#9ca3af", "font-size": "16px"},
    "nav-link": {
        "font-size": "14px",
        "text-align": "center",
        "margin": "0px",
        "color": "#9ca3af",
        "font-weight": "500",
        "font-family": "Inter",
    },
    "nav-link-selected": {
        "background-color": "#3b82f6",
        "color": "white",
        "font-weight": "600",
    },
}


def initialize_session_state() -> None:
    defaults = {
        "lang": "pt",
        "selected_compound_key": "ammonia",
        "profile": None,
        "lopa_result": None,
        "pid_hazop_matrix": [],
        "current_node_name": "Nó 101: Bomba de Recalque",
        "current_case_name": "",
        "audit_mode": True,
        "psv_result": None,
        "psv_inputs": None,
        "tmr_result": None,
        "tmr_inputs": None,
        "moc_result": None,
        "pssr_result": None,
        "reactivity_result": None,
        "psi_summary": None,
        "case_status": "rascunho",
        "case_status_note": "",
        "case_owner": "",
        "case_reviewer": "",
        "case_decision_gate": "",
        "review_history": [],
        "traceability_rows": [],
        "report_bundle": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
