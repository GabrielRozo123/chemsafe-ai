"""ChemSafe Pro Enterprise — ponto de entrada Streamlit.

Este arquivo contém APENAS orquestração: page config, sidebar, roteamento
de módulos e cálculo dos dados globais.  Toda lógica de negócio, gráficos,
constantes e estado de sessão são importados de módulos dedicados.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu

# ── Módulos internos (fontes canônicas) ──────────────────────────────
from theme import APP_CSS
from app_bootstrap import MENU_STYLES, initialize_session_state
from app_runtime import load_profile_with_feedback, load_profile_from_key, bowtie_payload
from chart_utils import is_valid_df
from action_processing import enrich_action_plan_df
from reference_data import MODULE_GOVERNANCE

# Views
from views_executive import render_executive_module
from views_engineering import render_engineering_module
from views_risk import render_risk_module
from views_change import render_change_module
from views_knowledge import render_knowledge_module

# UI
from ui_components import render_trust_ribbon

# Engines de domínio
from chemicals_seed import LOCAL_COMPOUNDS
from psi_readiness import build_psi_readiness_df, summarize_psi_readiness
from action_hub import build_consolidated_action_plan
from dashboard_engine import calculate_case_readiness_index
from traceability_engine import build_traceability_matrix
from i18n import t


# ══════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="ChemSafe Pro Enterprise",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(APP_CSS, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# SESSION STATE (fonte única: app_bootstrap.py)
# ══════════════════════════════════════════════════════════════════════
initialize_session_state()


# ══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════
with st.sidebar:
    lang = st.radio("🌐 Idioma", ["pt", "en"], horizontal=True, label_visibility="collapsed")
    st.session_state.lang = lang

    st.markdown(f"## ⚗️ {t('app_title', lang)}\n**Enterprise Edition v2.5**")
    st.caption("Process Safety Intelligence Engine")
    st.session_state.audit_mode = st.toggle(
        "Modo Auditoria / Evidências",
        value=st.session_state.audit_mode,
        help="Exibe base normativa, rastreabilidade e fundamento técnico do módulo.",
    )
    st.markdown("---")

    selected_module = option_menu(
        menu_title=None,
        options=["Visão Executiva", "Engenharia", "Análise de Risco", "Mudanças", "Base de Conhecimento"],
        icons=["speedometer2", "cpu", "shield-lock", "arrow-repeat", "book"],
        default_index=0,
        styles={
            "container": {"background-color": "transparent", "padding": "0"},
            "nav-link": {"font-size": "14px", "color": "#d1d5db", "margin": "5px 0"},
            "nav-link-selected": {"background-color": "#3b82f6", "color": "white"},
        },
    )

    st.markdown("---")
    st.write(f"**{t('quick_access', lang)}**")
    for key, data in LOCAL_COMPOUNDS.items():
        if st.button(data["identity"]["name"], key=f"quick_{key}", use_container_width=True):
            load_profile_from_key(key)

    st.markdown("---")
    manual_query = st.text_input("Buscar CAS ou Nome")
    if st.button("Carregar Composto", use_container_width=True) and manual_query.strip():
        st.session_state.profile = load_profile_with_feedback(manual_query.strip())


# ══════════════════════════════════════════════════════════════════════
# CARREGAMENTO INICIAL DO PERFIL
# ══════════════════════════════════════════════════════════════════════
if st.session_state.profile is None:
    load_profile_from_key(st.session_state.selected_compound_key)
profile = st.session_state.profile


# ══════════════════════════════════════════════════════════════════════
# CABEÇALHO DE CONTEXTO
# ══════════════════════════════════════════════════════════════════════
st.markdown(
    f"""<div class="context-header">
<div>🧪 Ativo Analisado: <span>{profile.identity.get('name', 'N/A')} (CAS: {profile.identity.get('cas', 'N/A')})</span></div>
<div>🏭 Topologia Foco: <span>{st.session_state.current_node_name}</span></div>
</div>""",
    unsafe_allow_html=True,
)

if st.session_state.audit_mode:
    gov = MODULE_GOVERNANCE.get(
        selected_module,
        {"basis": "Base técnica curada.", "refs": [], "confidence": "Média"},
    )
    render_trust_ribbon(
        module_name=selected_module,
        basis=gov["basis"],
        refs=gov["refs"],
        confidence=gov["confidence"],
    )


# ══════════════════════════════════════════════════════════════════════
# DADOS GLOBAIS (calculados uma vez por rerun)
# ══════════════════════════════════════════════════════════════════════
psi_df_dash = build_psi_readiness_df(profile, st.session_state.get("lopa_result"), bowtie_payload())
psi_summary = summarize_psi_readiness(psi_df_dash)

cri_data = calculate_case_readiness_index(
    profile,
    psi_summary,
    st.session_state.get("moc_result"),
    st.session_state.get("pssr_result"),
    st.session_state.get("lopa_result"),
    st.session_state.get("reactivity_result"),
)

traceability_df = build_traceability_matrix(
    profile=profile,
    psi_df=psi_df_dash,
    psi_summary=psi_summary,
    cri_data=cri_data,
    lopa_result=st.session_state.get("lopa_result"),
    moc_result=st.session_state.get("moc_result"),
    pssr_result=st.session_state.get("pssr_result"),
    reactivity_result=st.session_state.get("reactivity_result"),
)

action_df_dash = enrich_action_plan_df(
    build_consolidated_action_plan(
        profile,
        psi_df_dash,
        st.session_state.get("moc_result"),
        st.session_state.get("pssr_result"),
        st.session_state.get("reactivity_result"),
    )
)

has_actions = is_valid_df(action_df_dash)
num_acoes_pendentes = len(action_df_dash) if has_actions else 0
gaps_criticos = 0
if has_actions and "Criticidade" in action_df_dash.columns:
    gaps_criticos = len(action_df_dash[action_df_dash["Criticidade"].isin(["Alta", "Crítica"])])


# ══════════════════════════════════════════════════════════════════════
# ROTEAMENTO DE MÓDULOS (views importam suas dependências diretamente)
# ══════════════════════════════════════════════════════════════════════
if selected_module == "Visão Executiva":
    render_executive_module(
        profile=profile,
        cri_data=cri_data,
        action_df_dash=action_df_dash,
        has_actions=has_actions,
        num_acoes_pendentes=num_acoes_pendentes,
        gaps_criticos=gaps_criticos,
        menu_styles=MENU_STYLES,
        psi_df_dash=psi_df_dash,
        psi_summary=psi_summary,
        traceability_df=traceability_df,
    )

elif selected_module == "Engenharia":
    render_engineering_module(
        profile=profile,
        menu_styles=MENU_STYLES,
    )

elif selected_module == "Análise de Risco":
    render_risk_module(
        profile=profile,
        menu_styles=MENU_STYLES,
    )

elif selected_module == "Mudanças":
    render_change_module(
        profile=profile,
        menu_styles=MENU_STYLES,
    )

elif selected_module == "Base de Conhecimento":
    from reference_data import NORMS_DB

    render_knowledge_module(
        profile=profile,
        menu_styles=MENU_STYLES,
        norms_db=NORMS_DB,
    )
