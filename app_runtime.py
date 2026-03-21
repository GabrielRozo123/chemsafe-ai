from __future__ import annotations

import re
import time
import streamlit as st

from chemicals_seed import LOCAL_COMPOUNDS
from compound_engine import build_compound_profile


def load_profile_with_feedback(query: str):
    safe_query = re.sub(
        r"\s+",
        " ",
        str(query).replace("\xa0", " ").replace("Â\xa0", " ").replace("Â ", " "),
    ).strip()

    with st.spinner(f"Buscando dados no PubChem para '{safe_query}'..."):
        time.sleep(0.35)
        return build_compound_profile(safe_query)


def load_profile_from_key(key: str) -> None:
    aliases = LOCAL_COMPOUNDS[key]["aliases"]
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
    st.session_state.current_case_name = case_data.get("case_name", "")
    st.session_state.lopa_result = case_data.get("lopa_result")
