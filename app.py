from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from reference_data import NORMS_DB, MODULE_GOVERNANCE
from streamlit_option_menu import option_menu

from app_bootstrap import MENU_STYLES, initialize_session_state
from action_processing import enrich_action_plan_df, get_action_col
from app_runtime import (
    load_profile_with_feedback,
    load_profile_from_key,
    bowtie_payload,
    apply_loaded_case,
)
from case_domain import build_case_header, infer_case_gate, gate_to_status
from chart_utils import (
    is_valid_df,
    safe_float,
    render_modern_gauge,
    render_modern_radar,
    render_action_donut,
    render_action_bar,
    render_flammability_envelope,
)
from chemicals_seed import LOCAL_COMPOUNDS
from dashboard_engine import calculate_case_readiness_index
from i18n import t
from psi_readiness import build_psi_readiness_df, summarize_psi_readiness
from snapshot_engine import build_case_snapshot_payload
from traceability_engine import build_traceability_matrix
from ui_components import render_trust_ribbon
from views_change import render_change_module
from views_engineering import render_engineering_module
from views_executive import render_executive_module
from views_knowledge import render_knowledge_module
from views_risk import render_risk_module
from action_hub import build_consolidated_action_plan

APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');
:root {
  --bg-0: #07111e;
  --bg-1: #0b1422;
  --bg-2: #111c2d;
  --card-bg: rgba(17, 28, 45, 0.78);
  --card-strong: rgba(21, 32, 50, 0.92);
  --border-color: rgba(148, 163, 184, 0.16);
  --border-strong: rgba(96, 165, 250, 0.26);
  --text-main: #e5edf7;
  --text-soft: #9fb0c7;
  --text-faint: #7c8aa0;
  --accent-blue: #60a5fa;
  --accent-cyan: #22d3ee;
  --accent-green: #34d399;
  --accent-amber: #fbbf24;
  --accent-red: #f87171;
  --accent-violet: #a78bfa;
  --glow-blue: rgba(96, 165, 250, 0.16);
  --glow-green: rgba(52, 211, 153, 0.16);
  --glow-red: rgba(248, 113, 113, 0.16);
  --shadow-soft: 0 10px 30px rgba(0, 0, 0, 0.22);
  --shadow-card: 0 18px 45px rgba(0, 0, 0, 0.28);
  --radius-xl: 18px;
  --radius-lg: 14px;
  --radius-md: 10px;
}
html, body, [class*="css"] { font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
.stApp {
  color: var(--text-main);
  background:
    radial-gradient(circle at 12% 10%, rgba(34, 211, 238, 0.08), transparent 20%),
    radial-gradient(circle at 88% 8%, rgba(96, 165, 250, 0.10), transparent 24%),
    radial-gradient(circle at 50% 100%, rgba(52, 211, 153, 0.05), transparent 30%),
    linear-gradient(180deg, var(--bg-0) 0%, var(--bg-1) 52%, #09111c 100%);
}
.block-container { padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1480px; }
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, rgba(9, 15, 28, 0.98) 0%, rgba(11, 20, 34, 0.98) 100%);
  border-right: 1px solid rgba(148, 163, 184, 0.10);
}
.context-header {
  background: linear-gradient(135deg, rgba(17, 28, 45, 0.92) 0%, rgba(18, 31, 50, 0.88) 100%);
  border: 1px solid var(--border-color);
  padding: 18px 24px;
  border-radius: var(--radius-xl);
  margin-bottom: 18px;
  font-weight: 500;
  font-size: 0.96rem;
  color: var(--text-soft);
  display: flex;
  justify-content: space-between;
  gap: 16px;
  box-shadow: var(--shadow-soft);
  backdrop-filter: blur(10px);
}
.context-header span { color: #f8fbff; font-weight: 700; }
.panel {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: 1.35rem 1.35rem 1.2rem 1.35rem;
  margin-bottom: 1rem;
  box-shadow: var(--shadow-soft);
  backdrop-filter: blur(10px);
}
.hero-panel {
  background: linear-gradient(135deg, rgba(20, 33, 52, 0.94) 0%, rgba(13, 23, 38, 0.95) 100%);
  border: 1px solid rgba(96, 165, 250, 0.18);
  border-radius: 20px;
  padding: 20px 22px;
  margin-bottom: 18px;
  box-shadow: var(--shadow-card);
}
.metric-box {
  background: linear-gradient(180deg, rgba(24, 37, 58, 0.82) 0%, rgba(17, 27, 43, 0.90) 100%);
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 14px;
  padding: 16px 18px;
  text-align: center;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 124px;
}
.metric-label {
  color: var(--text-faint);
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-weight: 700;
}
.metric-value {
  color: #f8fbff;
  font-size: 1.78rem;
  font-weight: 800;
  margin-top: 8px;
}
.metric-mono { font-family: 'JetBrains Mono', monospace; }
.risk-blue { color: var(--accent-blue); }
.risk-green { color: var(--accent-green); }
.risk-amber { color: var(--accent-amber); }
.risk-red { color: var(--accent-red); }
.risk-violet { color: var(--accent-violet); }
.note-card {
  background: linear-gradient(90deg, rgba(96, 165, 250, 0.09), rgba(34, 211, 238, 0.06));
  border: 1px solid rgba(96, 165, 250, 0.12);
  border-left: 4px solid var(--accent-blue);
  padding: 14px 15px;
  border-radius: 10px;
  font-size: 0.92rem;
  margin-bottom: 16px;
  color: #d6e8fb;
  line-height: 1.6;
}
.stButton > button, .stDownloadButton > button {
  border-radius: 12px !important;
  border: 1px solid rgba(96, 165, 250, 0.18) !important;
  background: linear-gradient(180deg, rgba(25, 39, 61, 0.92) 0%, rgba(18, 29, 46, 0.96) 100%) !important;
  color: #edf5ff !important;
  font-weight: 700 !important;
}
small, .stCaption { color: var(--text-faint) !important; }
</style>
"""

st.set_page_config(
    page_title="ChemSafe Pro Enterprise",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(APP_CSS, unsafe_allow_html=True)
initialize_session_state()

with st.sidebar:
    lang = st.radio("🌐 Idioma", ["pt", "en"], horizontal=True, label_visibility="collapsed")
    st.session_state.lang = lang

    st.markdown(f"## ⚗️ {t('app_title', lang)}\n**Enterprise Edition v2.6**")
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

if st.session_state.profile is None:
    load_profile_from_key(st.session_state.selected_compound_key)
profile = st.session_state.profile

case_header = build_case_header(
    profile=profile,
    node_name=st.session_state.current_node_name,
    case_name=st.session_state.current_case_name,
    owner=st.session_state.case_owner,
    reviewer=st.session_state.case_reviewer,
)

st.markdown(
    f"""
<div class="context-header">
    <div>🧪 Ativo Analisado: <span>{profile.identity.get('name', 'N/A')} (CAS: {profile.identity.get('cas', 'N/A')})</span></div>
    <div>🏭 Topologia Foco: <span>{st.session_state.current_node_name}</span></div>
    <div>📂 Caso: <span>{case_header.get('case_name', 'Caso')}</span></div>
</div>
""",
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

psi_df_dash = build_psi_readiness_df(profile, st.session_state.get("lopa_result"), bowtie_payload())
psi_summary_dash = summarize_psi_readiness(psi_df_dash)
st.session_state.psi_summary = psi_summary_dash

cri_data = calculate_case_readiness_index(
    profile,
    psi_summary_dash,
    st.session_state.get("moc_result"),
    st.session_state.get("pssr_result"),
    st.session_state.get("lopa_result"),
    st.session_state.get("reactivity_result"),
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

traceability_df = build_traceability_matrix(
    profile=profile,
    psi_df=psi_df_dash,
    psi_summary=psi_summary_dash,
    cri_data=cri_data,
    lopa_result=st.session_state.get("lopa_result"),
    moc_result=st.session_state.get("moc_result"),
    pssr_result=st.session_state.get("pssr_result"),
    reactivity_result=st.session_state.get("reactivity_result"),
)
st.session_state.traceability_rows = traceability_df.to_dict(orient="records") if not traceability_df.empty else []

st.session_state.case_decision_gate = st.session_state.case_decision_gate or infer_case_gate(
    cri_data=cri_data,
    psi_summary=psi_summary_dash,
    gaps_criticos=int(psi_summary_dash.get("critical_gaps", 0)),
    moc_result=st.session_state.get("moc_result"),
    pssr_result=st.session_state.get("pssr_result"),
    lopa_result=st.session_state.get("lopa_result"),
)
if st.session_state.case_status == "rascunho" and st.session_state.case_decision_gate:
    st.session_state.case_status = gate_to_status(st.session_state.case_decision_gate)

has_actions = is_valid_df(action_df_dash)
num_acoes_pendentes = len(action_df_dash) if has_actions else 0
gaps_criticos = int(psi_summary_dash.get("critical_gaps", 0))

if selected_module == "Visão Executiva":
    render_executive_module(
        profile=profile,
        cri_data=cri_data,
        action_df_dash=action_df_dash,
        has_actions=has_actions,
        num_acoes_pendentes=num_acoes_pendentes,
        gaps_criticos=gaps_criticos,
        menu_styles=MENU_STYLES,
        bowtie_payload_fn=bowtie_payload,
        apply_loaded_case_fn=apply_loaded_case,
        render_modern_gauge_fn=render_modern_gauge,
        render_modern_radar_fn=render_modern_radar,
        render_action_donut_fn=render_action_donut,
        render_action_bar_fn=render_action_bar,
        get_action_col_fn=get_action_col,
        psi_df_dash=psi_df_dash,
        psi_summary=psi_summary_dash,
        traceability_df=traceability_df,
    )

elif selected_module == "Engenharia":
    render_engineering_module(
        profile=profile,
        menu_styles=MENU_STYLES,
        safe_float_fn=safe_float,
        render_flammability_envelope_fn=render_flammability_envelope,
    )

elif selected_module == "Análise de Risco":
    render_risk_module(
        profile=profile,
        menu_styles=MENU_STYLES,
        is_valid_df_fn=is_valid_df,
    )

elif selected_module == "Mudanças":
    render_change_module(
        profile=profile,
        menu_styles=MENU_STYLES,
    )

elif selected_module == "Base de Conhecimento":
    render_knowledge_module(
        profile=profile,
        menu_styles=MENU_STYLES,
        norms_db=NORMS_DB,
    )
