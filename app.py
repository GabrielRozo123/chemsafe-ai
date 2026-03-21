from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from reference_data import NORMS_DB, MODULE_GOVERNANCE
from streamlit_option_menu import option_menu
from action_processing import enrich_action_plan_df, sanitize_and_translate_action_df, get_action_col

from views_engineering import render_engineering_module
from views_executive import render_executive_module
from views_risk import render_risk_module
from views_change import render_change_module
from views_knowledge import render_knowledge_module
from chemicals_seed import LOCAL_COMPOUNDS


from psi_readiness import build_psi_readiness_df, summarize_psi_readiness
from action_hub import build_consolidated_action_plan
from dashboard_engine import calculate_case_readiness_index
from i18n import t
from ui_components import render_trust_ribbon
from chart_utils import (
    is_valid_df,
    safe_float,
    render_modern_gauge,
    render_modern_radar,
    render_action_donut,
    render_action_bar,
    render_flammability_envelope,
)
from app_runtime import (
    load_profile_with_feedback,
    load_profile_from_key,
    bowtie_payload,
    apply_loaded_case,
)

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

html, body, [class*="css"]  {
  font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.stApp {
  color: var(--text-main);
  background:
    radial-gradient(circle at 12% 10%, rgba(34, 211, 238, 0.08), transparent 20%),
    radial-gradient(circle at 88% 8%, rgba(96, 165, 250, 0.10), transparent 24%),
    radial-gradient(circle at 50% 100%, rgba(52, 211, 153, 0.05), transparent 30%),
    linear-gradient(180deg, var(--bg-0) 0%, var(--bg-1) 52%, #09111c 100%);
}

.block-container {
  padding-top: 1.2rem;
  padding-bottom: 3rem;
  max-width: 1480px;
}

section[data-testid="stSidebar"] {
  background:
    linear-gradient(180deg, rgba(9, 15, 28, 0.98) 0%, rgba(11, 20, 34, 0.98) 100%);
  border-right: 1px solid rgba(148, 163, 184, 0.10);
}

.context-header {
  background:
    linear-gradient(135deg, rgba(17, 28, 45, 0.92) 0%, rgba(18, 31, 50, 0.88) 100%);
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

.context-header span {
  color: #f8fbff;
  font-weight: 700;
}

.panel {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: 1.35rem 1.35rem 1.2rem 1.35rem;
  margin-bottom: 1rem;
  box-shadow: var(--shadow-soft);
  backdrop-filter: blur(10px);
  transition: transform 0.18s ease, border-color 0.22s ease, box-shadow 0.22s ease;
}

.panel:hover {
  transform: translateY(-1px);
  border-color: var(--border-strong);
  box-shadow: 0 16px 38px rgba(0,0,0,0.24), 0 0 0 1px rgba(96,165,250,0.05);
}

.panel h3 {
  margin-top: 0;
  color: #f4f8fd;
  font-size: 1.02rem;
  font-weight: 700;
  letter-spacing: 0.01em;
  border-bottom: 1px solid rgba(148,163,184,0.10);
  padding-bottom: 10px;
  margin-bottom: 16px;
}

.hero-panel {
  background:
    linear-gradient(135deg, rgba(20, 33, 52, 0.94) 0%, rgba(13, 23, 38, 0.95) 100%);
  border: 1px solid rgba(96, 165, 250, 0.18);
  border-radius: 20px;
  padding: 20px 22px;
  margin-bottom: 18px;
  box-shadow: var(--shadow-card);
}

.hero-kicker {
  color: var(--accent-cyan);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 0.72rem;
  font-weight: 800;
  margin-bottom: 8px;
}

.hero-title {
  color: #f8fbff;
  font-size: 1.35rem;
  font-weight: 800;
  margin-bottom: 6px;
}

.hero-subtitle {
  color: var(--text-soft);
  font-size: 0.96rem;
  line-height: 1.55;
}

.metric-box {
  background:
    linear-gradient(180deg, rgba(24, 37, 58, 0.82) 0%, rgba(17, 27, 43, 0.90) 100%);
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 14px;
  padding: 16px 18px;
  text-align: center;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 124px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
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
  line-height: 1.18;
  white-space: normal;
  word-wrap: break-word;
}

.metric-mono {
  font-family: 'JetBrains Mono', monospace;
}

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

.trust-ribbon {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: flex-start;
  background:
    linear-gradient(135deg, rgba(12, 22, 36, 0.96) 0%, rgba(18, 31, 50, 0.92) 100%);
  border: 1px solid rgba(52, 211, 153, 0.20);
  border-radius: 18px;
  padding: 16px 18px;
  margin-bottom: 18px;
  box-shadow: var(--shadow-soft);
}

.trust-left { flex: 1; }
.trust-kicker {
  color: var(--accent-green);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 0.70rem;
  font-weight: 800;
  margin-bottom: 6px;
}
.trust-title {
  color: #f7fbff;
  font-size: 1.05rem;
  font-weight: 800;
  margin-bottom: 4px;
}
.trust-text {
  color: var(--text-soft);
  font-size: 0.91rem;
  line-height: 1.5;
}
.trust-right {
  min-width: 180px;
  text-align: right;
}
.trust-pill {
  display: inline-block;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(52, 211, 153, 0.14);
  border: 1px solid rgba(52, 211, 153, 0.24);
  color: #b7f7de;
  font-size: 0.78rem;
  font-weight: 800;
  margin-bottom: 8px;
}
.trust-meta {
  color: var(--text-faint);
  font-size: 0.80rem;
}

.ref-chip-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}
.ref-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 0.76rem;
  color: #d9e7f8;
  background: rgba(148, 163, 184, 0.08);
  border: 1px solid rgba(148, 163, 184, 0.12);
}
.ref-chip::before {
  content: "▣";
  color: var(--accent-cyan);
  font-size: 0.72rem;
}

.doc-card {
  background: linear-gradient(180deg, rgba(23, 36, 57, 0.78) 0%, rgba(16, 26, 42, 0.88) 100%);
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 16px;
  padding: 20px;
  height: 100%;
  transition: all 0.22s ease;
  box-shadow: var(--shadow-soft);
}

.doc-card:hover {
  border-color: rgba(96, 165, 250, 0.28);
  transform: translateY(-2px);
  box-shadow: 0 16px 36px rgba(0,0,0,0.26);
}

.doc-tag {
  background: rgba(96, 165, 250, 0.12);
  color: #9fcbff;
  font-size: 0.74rem;
  padding: 4px 10px;
  border-radius: 999px;
  font-weight: 800;
  text-transform: uppercase;
  display: inline-block;
  margin-bottom: 10px;
  border: 1px solid rgba(96, 165, 250, 0.18);
}

.doc-title {
  font-size: 1.06rem;
  font-weight: 800;
  color: #f4f8fd;
  margin-bottom: 8px;
  display: block;
}

.doc-desc {
  font-size: 0.91rem;
  color: var(--text-soft);
  line-height: 1.58;
}

.history-timeline {
  border-left: 3px solid rgba(96, 165, 250, 0.55);
  margin-left: 20px;
  padding-left: 22px;
}
.history-item {
  margin-bottom: 24px;
  position: relative;
}
.history-item::before {
  content: '';
  position: absolute;
  left: -30px;
  top: 2px;
  width: 14px;
  height: 14px;
  background: #08111f;
  border: 3px solid var(--accent-blue);
  border-radius: 50%;
}

.evidence-panel {
  background: linear-gradient(180deg, rgba(12, 21, 34, 0.92) 0%, rgba(15, 25, 40, 0.96) 100%);
  border: 1px solid rgba(167, 139, 250, 0.16);
  border-radius: 16px;
  padding: 18px;
  margin-bottom: 16px;
  box-shadow: var(--shadow-soft);
}
.evidence-kicker {
  color: var(--accent-violet);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 0.70rem;
  font-weight: 800;
  margin-bottom: 6px;
}
.evidence-title {
  color: #f7fbff;
  font-size: 1.02rem;
  font-weight: 800;
  margin-bottom: 8px;
}
.evidence-sub {
  color: var(--text-soft);
  font-size: 0.91rem;
  line-height: 1.56;
  margin-bottom: 14px;
}
.evidence-grid {
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  gap: 14px;
}
.evidence-card {
  background: rgba(148, 163, 184, 0.05);
  border: 1px solid rgba(148, 163, 184, 0.10);
  border-radius: 12px;
  padding: 12px 13px;
}
.evidence-card h4 {
  margin: 0 0 8px 0;
  color: #f0f6ff;
  font-size: 0.86rem;
  font-weight: 800;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}
.evidence-card ul {
  margin: 0;
  padding-left: 18px;
}
.evidence-card li {
  color: var(--text-soft);
  font-size: 0.88rem;
  line-height: 1.55;
  margin-bottom: 4px;
}
.evidence-code {
  font-family: 'JetBrains Mono', monospace;
  background: rgba(96, 165, 250, 0.08);
  color: #d5e7ff;
  border: 1px solid rgba(96, 165, 250, 0.12);
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 0.82rem;
  line-height: 1.5;
  white-space: pre-wrap;
}
.evidence-inputs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0,1fr));
  gap: 8px;
}
.evidence-input-item {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(148,163,184,0.08);
  border-radius: 10px;
  padding: 9px 10px;
}
.evidence-input-label {
  color: var(--text-faint);
  font-size: 0.73rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 4px;
}
.evidence-input-value {
  color: #f4f9ff;
  font-size: 0.89rem;
  font-weight: 700;
}

.stExpander {
  border: 1px solid rgba(148, 163, 184, 0.12) !important;
  border-radius: 14px !important;
  background: rgba(17, 28, 45, 0.62) !important;
  overflow: hidden;
}

.stButton > button,
.stDownloadButton > button {
  border-radius: 12px !important;
  border: 1px solid rgba(96, 165, 250, 0.18) !important;
  background: linear-gradient(180deg, rgba(25, 39, 61, 0.92) 0%, rgba(18, 29, 46, 0.96) 100%) !important;
  color: #edf5ff !important;
  font-weight: 700 !important;
  transition: all 0.18s ease !important;
  box-shadow: 0 6px 16px rgba(0,0,0,0.18);
}

.stButton > button:hover,
.stDownloadButton > button:hover {
  transform: translateY(-1px);
  border-color: rgba(96, 165, 250, 0.30) !important;
  box-shadow: 0 10px 22px rgba(0,0,0,0.24), 0 0 0 3px rgba(96,165,250,0.08);
}

.nav-link {
  font-family: 'Inter', sans-serif !important;
}

[data-testid="stMetric"] {
  background: rgba(17, 28, 45, 0.68);
  border: 1px solid rgba(148, 163, 184, 0.10);
  padding: 12px 14px;
  border-radius: 12px;
}

small, .stCaption {
  color: var(--text-faint) !important;
}
</style>
"""

st.set_page_config(
    page_title="ChemSafe Pro Enterprise",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(APP_CSS, unsafe_allow_html=True)

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
    "nav-link-selected": {"background-color": "#3b82f6", "color": "white", "font-weight": "600"},
}


# ==============================================================================
# ESTADO DA SESSÃO
# ==============================================================================
if "lang" not in st.session_state:
    st.session_state.lang = "pt"
if "selected_compound_key" not in st.session_state:
    st.session_state.selected_compound_key = "ammonia"
if "profile" not in st.session_state:
    st.session_state.profile = None
if "lopa_result" not in st.session_state:
    st.session_state.lopa_result = None
if "pid_hazop_matrix" not in st.session_state:
    st.session_state.pid_hazop_matrix = []
if "current_node_name" not in st.session_state:
    st.session_state.current_node_name = "Nó 101: Bomba de Recalque"
if "current_case_name" not in st.session_state:
    st.session_state.current_case_name = ""
if "audit_mode" not in st.session_state:
    st.session_state.audit_mode = True
if "psv_result" not in st.session_state:
    st.session_state.psv_result = None
if "psv_inputs" not in st.session_state:
    st.session_state.psv_inputs = None
if "tmr_result" not in st.session_state:
    st.session_state.tmr_result = None
if "tmr_inputs" not in st.session_state:
    st.session_state.tmr_inputs = None
if "moc_result" not in st.session_state:
    st.session_state.moc_result = None
if "pssr_result" not in st.session_state:
    st.session_state.pssr_result = None
if "reactivity_result" not in st.session_state:
    st.session_state.reactivity_result = None




# ==============================================================================
# SIDEBAR
# ==============================================================================
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
        if st.button(data["identity"]["name"], key=f"quick_{key}", width="stretch"):
            load_profile_from_key(key)

    st.markdown("---")
    manual_query = st.text_input("Buscar CAS ou Nome")
    if st.button("Carregar Composto", width="stretch") and manual_query.strip():
        st.session_state.profile = load_profile_with_feedback(manual_query.strip())


if st.session_state.profile is None:
    load_profile_from_key(st.session_state.selected_compound_key)
profile = st.session_state.profile

st.markdown(
    f"""
<div class="context-header">
    <div>🧪 Ativo Analisado: <span>{profile.identity.get('name', 'N/A')} (CAS: {profile.identity.get('cas', 'N/A')})</span></div>
    <div>🏭 Topologia Foco: <span>{st.session_state.current_node_name}</span></div>
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

# ==============================================================================
# DADOS GLOBAIS
# ==============================================================================
psi_df_dash = build_psi_readiness_df(profile, st.session_state.get("lopa_result"), bowtie_payload())
cri_data = calculate_case_readiness_index(
    profile,
    summarize_psi_readiness(psi_df_dash),
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

has_actions = is_valid_df(action_df_dash)
num_acoes_pendentes = len(action_df_dash) if has_actions else 0
gaps_criticos = 0
if has_actions and "Criticidade" in action_df_dash.columns:
    gaps_criticos = len(action_df_dash[action_df_dash["Criticidade"].isin(["Alta", "Crítica"])])


# ==============================================================================
# MÓDULO 1: VISÃO EXECUTIVA
# ==============================================================================
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
    )

# ==============================================================================
# MÓDULO 2: ENGENHARIA
# ==============================================================================
elif selected_module == "Engenharia":
    render_engineering_module(
        profile=profile,
        menu_styles=MENU_STYLES,
        safe_float_fn=safe_float,
        render_flammability_envelope_fn=render_flammability_envelope,
    )

# ==============================================================================
# MÓDULO 3: ANÁLISE DE RISCO
# ==============================================================================
elif selected_module == "Análise de Risco":
    render_risk_module(
        profile=profile,
        menu_styles=MENU_STYLES,
        is_valid_df_fn=is_valid_df,
    )

# ==============================================================================
# MÓDULO 4: MUDANÇAS
# ==============================================================================
elif selected_module == "Mudanças":
    render_change_module(
        profile=profile,
        menu_styles=MENU_STYLES,
    )

# ==============================================================================
# MÓDULO 5: BASE DE CONHECIMENTO
# ==============================================================================
elif selected_module == "Base de Conhecimento":
    render_knowledge_module(
        profile=profile,
        menu_styles=MENU_STYLES,
        norms_db=NORMS_DB,
    )
