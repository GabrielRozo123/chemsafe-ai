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


# ---------------------------------------------------------------------------
# Defaults centralizados — ÚNICA fonte de verdade para session_state
# ---------------------------------------------------------------------------
_SESSION_DEFAULTS: dict = {
    # Idioma e navegação
    "lang": "pt",
    "selected_compound_key": "ammonia",
    "audit_mode": True,
    # Perfil e dados do composto
    "profile": None,
    "compound_cache": {},
    # SDS / FISPQ reader
    "sds_extracted_data": None,
    "sds_extraction_mode": None,
    "sds_merge_changes": None,
    # Caso / projeto
    "current_case_name": "",
    "current_node_name": "Nó 101: Bomba de Recalque",
    "case_owner": "",
    "case_reviewer": "",
    "case_date": "",
    "case_status": "Em Análise",
    "case_status_note": "",
    "case_priority": "Normal",
    "case_notes": "",
    "case_decision_gate": None,
    "case_gate_history": [],
    # HAZOP / risco
    "pid_hazop_matrix": [],
    "hazop_scenarios": [],
    "selected_equipment": [],
    "risk_matrix": None,
    # LOPA
    "lopa_result": None,
    "lopa_scenarios": [],
    # Bow-Tie
    "bowtie_threats": "",
    "bowtie_pre": "",
    "bowtie_top": "Perda de contenção",
    "bowtie_mit": "",
    "bowtie_cons": "",
    "bowtie_data": {},
    # PSV / Runaway
    "psv_result": None,
    "psv_inputs": None,
    "tmr_result": None,
    "tmr_inputs": None,
    # MOC / PSSR / Reatividade
    "moc_result": None,
    "pssr_result": None,
    "reactivity_result": None,
    # Relatórios e exports
    "report_bundle": None,
    # Executivo
    "executive_summary": "",
    "recommendations": [],
    "risk_assessment": {},
    "mitigation_plan": [],
    "compliance_status": {},
    "audit_findings": [],
    "action_plan": [],
    # Histórico e rastreabilidade
    "document_history": [],
    "review_history": [],
}


def initialize_session_state() -> None:
    """Inicializa todas as variáveis de session_state com valores padrão.

    Chamar uma única vez no topo do ``app.py``.  Variáveis que já existem
    (por exemplo após um rerun) não são sobrescritas.
    """
    for key, value in _SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value
