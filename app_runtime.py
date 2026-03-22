from __future__ import annotations

import re
import time
import streamlit as st

from chemicals_seed import LOCAL_COMPOUNDS
from compound_engine import build_compound_profile

DEFAULT_COMPOUND_KEY = "ammonia"


def _clean_query(query: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        str(query).replace("\xa0", " ").replace("Â\xa0", " ").replace("Â ", " "),
    ).strip()


def _build_default_profile():
    aliases = LOCAL_COMPOUNDS.get(DEFAULT_COMPOUND_KEY, {}).get("aliases", ["ammonia"])
    return build_compound_profile(aliases[0])


def load_profile_with_feedback(query: str):
    safe_query = _clean_query(query)

    if not safe_query:
        st.warning("Digite um nome de composto ou um número CAS válido.")
        return st.session_state.get("profile") or _build_default_profile()

    with st.spinner(f"Buscando dados no PubChem para '{safe_query}'..."):
        try:
            time.sleep(0.35)
            profile = build_compound_profile(safe_query)
            if profile is None:
                raise ValueError("O motor não retornou um perfil válido.")
            return profile

        except Exception:
            st.error(
                f"Não foi possível carregar '{safe_query}'. "
                "O app continuará usando um composto padrão para evitar interrupção."
            )
            return st.session_state.get("profile") or _build_default_profile()


def load_profile_from_key(key: str) -> None:
    aliases = LOCAL_COMPOUNDS.get(key, {}).get("aliases", [key])
    st.session_state.profile = load_profile_with_feedback(aliases[0])
    st.session_state.selected_compound_key = key


def bowtie_payload():
    return {
        "threats": [x.strip() for x in st.session_state.get("bowtie_threats", "").splitlines() if x.strip()],
        "barriers_pre": [x.strip() for x in st.session_state.get("bowtie_pre", "").splitlines() if x.strip()],
        "top_event": st.session_state.get("bowtie_top", "Perda de contenção"),
        "barriers_mit": [x.strip() for x in st.session_state.get("bowtie_mit", "").splitlines() if x.strip()],
        "consequences": [x.strip() for x in st.session_state.get("bowtie_cons", "").splitlines() if x.strip()],
    }


def apply_loaded_case(case_data: dict):
    query_hint = case_data.get("query_hint") or case_data.get("compound_name")

    if query_hint:
        st.session_state.profile = load_profile_with_feedback(query_hint)
    elif st.session_state.get("profile") is None:
        st.session_state.profile = _build_default_profile()

    st.session_state.current_case_name = case_data.get("case_name", "")
    st.session_state.current_node_name = case_data.get("current_node_name", st.session_state.get("current_node_name", ""))
    st.session_state.lopa_result = case_data.get("lopa_result")
    st.session_state.moc_result = case_data.get("moc_result")
    st.session_state.pssr_result = case_data.get("pssr_result")
    st.session_state.reactivity_result = case_data.get("reactivity_result")
    st.session_state.case_status = case_data.get("case_status", "rascunho")
    st.session_state.case_status_note = case_data.get("case_status_note", "")
    st.session_state.case_owner = case_data.get("case_owner", "")
    st.session_state.case_reviewer = case_data.get("case_reviewer", "")
    st.session_state.case_decision_gate = case_data.get("case_decision_gate", "")
    st.session_state.review_history = case_data.get("review_history", [])
    st.session_state.traceability_rows = case_data.get("traceability_rows", [])
    st.session_state.psi_summary = case_data.get("psi_summary")
