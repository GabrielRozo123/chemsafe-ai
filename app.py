from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st

# Módulos de Visualização e Armazenamento Antigos
from bowtie_visual import build_bowtie_custom_figure
from case_store import list_cases, load_case, save_case
from chemicals_seed import LOCAL_COMPOUNDS
from comparator import build_comparison_df, build_comparison_highlights
from compound_engine import (
    build_compound_profile,
    suggest_hazop_priorities,
    suggest_lopa_ipls,
)
from dense_gas_router import classify_dispersion_mode
from deterministic import IPL_CATALOG, compute_lopa, gaussian_dispersion, pool_fire
from executive_report import build_executive_bundle
from hazop_db import HAZOP_DB
from moc_engine import evaluate_moc
from moc_visuals import build_moc_impacts_figure, build_moc_score_figure
from property_status import build_property_status_df, summarize_property_status
from psi_readiness import build_psi_readiness_df, summarize_psi_readiness
from psi_visuals import build_psi_pillars_figure, build_psi_score_figure
from pssr_engine import evaluate_pssr
from pssr_visuals import build_pssr_score_figure
from reactivity_engine import evaluate_pairwise_reactivity
from reactivity_visuals import build_pairwise_matrix_figure
from risk_register import build_risk_register
from risk_visuals import (
    build_confidence_figure,
    build_hazard_fingerprint_figure,
    build_incompatibility_matrix_figure,
    build_ipl_layers_figure,
    build_risk_matrix_figure,
    build_source_coverage_figure,
)
from source_governance import (
    build_evidence_ledger_df,
    build_source_recommendations,
    summarize_evidence,
)
from source_visuals import build_link_coverage_figure, build_source_summary_figure
from ui_formatters import format_identity_df, format_limits_df, format_physchem_df

# Módulos SPRINT 11 e 12 (Ação, Executivo, What-if, Área, Tradução)
from action_hub import build_consolidated_action_plan
from dashboard_engine import calculate_case_readiness_index
from dashboard_visuals import build_readiness_gauge_figure, build_components_figure
from scenario_compare import build_what_if_comparison
from i18n import t
from area_engine import evaluate_area_risk

APP_CSS = """
<style>
.stApp { background: linear-gradient(180deg, #07111f, #081a31); color: #e9f1ff; }
.block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 1450px; }
.hero { background: linear-gradient(135deg, #0d2345, #0b1830); border: 1px solid #1c3f78; border-radius: 20px; padding: 1.3rem 1.5rem; margin-bottom: 1rem; box-shadow: 0 12px 30px rgba(0,0,0,0.18); }
.hero h1 { margin: 0 0 0.35rem 0; color: #f4f8ff; font-size: 2rem; font-weight: 800; }
.hero p { margin: 0; color: #9fc1ff; font-size: 1rem; }
.badge { display: inline-block; margin: 0.40rem 0.35rem 0 0; padding: 0.28rem 0.65rem; border-radius: 999px; border: 1px solid #2b5aa1; color: #cfe1ff; background: rgba(31, 74, 139, 0.18); font-size: 0.78rem; }
.metric-box { background: rgba(10,22,42,0.95); border: 1px solid #1d365f; border-radius: 18px; padding: 1rem; min-height: 118px; box-shadow: 0 8px 18px rgba(0,0,0,0.12); }
.metric-label { color: #7ea8ea; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; }
.metric-value { color: white; font-size: 1.55rem; font-weight: 800; margin-top: 0.45rem; line-height: 1.1; }
.risk-blue { color: #62a8ff; } .risk-green { color: #34d399; } .risk-amber { color: #fbbf24; } .risk-red { color: #fb7185; }
.panel { background: rgba(9,17,31,0.94); border: 1px solid #1d365f; border-radius: 18px; padding: 1rem; margin-bottom: 0.9rem; box-shadow: 0 8px 18px rgba(0,0,0,0.10); }
.panel h3 { margin-top: 0; margin-bottom: 0.8rem; color: #f0f6ff; font-size: 1rem; font-weight: 800; }
.note-card { background: rgba(12, 28, 54, 0.95); border-left: 4px solid #4b88ff; border-radius: 12px; padding: 0.9rem 1rem; color: #e9f1ff; }
</style>
"""

st.set_page_config(page_title="ChemSafe Pro AI", page_icon="⚗️", layout="wide", initial_sidebar_state="expanded")
st.markdown(APP_CSS, unsafe_allow_html=True)

# =========================
# Estado da sessão
# =========================
if "lang" not in st.session_state: st.session_state.lang = "pt"
if "selected_compound_key" not in st.session_state: st.session_state.selected_compound_key = "ammonia"
if "profile" not in st.session_state: st.session_state.profile = None
if "lopa_result" not in st.session_state: st.session_state.lopa_result = None
if "bowtie_initialized_for" not in st.session_state: st.session_state.bowtie_initialized_for = ""
if "moc_result" not in st.session_state: st.session_state.moc_result = None
if "pssr_result" not in st.session_state: st.session_state.pssr_result = None
if "reactivity_result" not in st.session_state: st.session_state.reactivity_result = None

# Helpers
def metric_card(label: str, value: str, klass: str = "risk-blue") -> str:
    return f"<div class='metric-box'><div class='metric-label'>{label}</div><div class='metric-value {klass}'>{value}</div></div>"

def load_profile_from_key(key: str) -> None:
    aliases = LOCAL_COMPOUNDS[key]["aliases"]
    st.session_state.profile = build_compound_profile(aliases[0])
    st.session_state.selected_compound_key = key

def bowtie_payload():
    return {
        "threats":[x.strip() for x in st.session_state.get("bowtie_threats", "").splitlines() if x.strip()],
        "barriers_pre":[x.strip() for x in st.session_state.get("bowtie_pre", "").splitlines() if x.strip()],
        "top_event": st.session_state.get("bowtie_top", "Perda de contenção"),
        "barriers_mit":[x.strip() for x in st.session_state.get("bowtie_mit", "").splitlines() if x.strip()],
        "consequences":[x.strip() for x in st.session_state.get("bowtie_cons", "").splitlines() if x.strip()],
    }

# =========================
# Sidebar & Navegação
# =========================
with st.sidebar:
    # Toggle de Idioma
    lang = st.radio("🌐 Language / Idioma", ["pt", "en"], horizontal=True, label_visibility="collapsed")
    st.session_state.lang = lang

    st.markdown(f"## ⚗️ {t('app_title', lang)}")
    st.caption("Process Safety Intelligence Engine")
    st.markdown("---")

    # Módulos de Navegação (A grande sacada de UX)
    st.write(f"**Navegação Principal**")
    selected_module = st.radio(
        "Módulos",
        options=[
            t("module_exec", lang), 
            t("module_eng", lang), 
            t("module_risk", lang), 
            t("module_change", lang)
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.write(f"**{t('quick_access', lang)}**")
    for key, data in LOCAL_COMPOUNDS.items():
        if st.button(data["identity"]["name"], key=f"quick_{key}", width="stretch"):
            load_profile_from_key(key)

    st.markdown("---")
    manual_query = st.text_input(t("search_compound", lang), placeholder="Nome ou CAS")
    if st.button(t("load_compound", lang), width="stretch"):
        if manual_query.strip():
            st.session_state.profile = build_compound_profile(manual_query.strip())


# Inicialização Básica
if st.session_state.profile is None:
    load_profile_from_key(st.session_state.selected_compound_key)
profile = st.session_state.profile

# =========================
# Hero
# =========================
st.markdown(
    f"""
    <div class="hero">
      <h1>{t('app_title', lang)}</h1>
      <p>Gestão de riscos guiada por propriedades reais, dados rastreáveis e inteligência determinística.</p>
    </div>
    """, unsafe_allow_html=True
)

# Processamentos em Background para o Dashboard não quebrar
psi_df_dash = build_psi_readiness_df(profile, st.session_state.get("lopa_result"), bowtie_payload())
cri_data = calculate_case_readiness_index(
    profile, summarize_psi_readiness(psi_df_dash),
    st.session_state.get("moc_result"), st.session_state.get("pssr_result"),
    st.session_state.get("lopa_result"), st.session_state.get("reactivity_result")
)
action_df_dash = build_consolidated_action_plan(
    profile, psi_df_dash, st.session_state.get("moc_result"), st.session_state.get("pssr_result"), st.session_state.get("reactivity_result")
)

# ==============================================================================
# ROTEAMENTO DOS MÓDULOS (Aqui resolvemos a sobrecarga de abas!)
# ==============================================================================

if selected_module == t("module_exec", lang):
    tabs = st.tabs([t("tab_dash", lang), t("tab_action", lang), "Relatório", "Casos Salvos"])
    dash_tab, action_plan_tab, report_tab, cases_tab = tabs

    with dash_tab:
        st.markdown("<div class='panel'><h3>Case Readiness Index (CRI)</h3></div>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(metric_card("Readiness Global", f"{cri_data['index']}%", cri_data['color_class']), unsafe_allow_html=True)
        c2.markdown(metric_card("Status do Caso", cri_data['band'], cri_data['color_class']), unsafe_allow_html=True)
        c3.markdown(metric_card("Ações Abertas", str(len(action_df_dash)), "risk-amber" if len(action_df_dash) > 0 else "risk-green"), unsafe_allow_html=True)
        gaps_crit = len(action_df_dash[action_df_dash["Criticidade"].isin(["Alta", "Crítica"])]) if len(action_df_dash) > 0 else 0
        c4.markdown(metric_card("Gaps Críticos", str(gaps_crit), "risk-red" if gaps_crit > 0 else "risk-green"), unsafe_allow_html=True)
        
        left, right = st.columns(2)
        with left:
            st.markdown("<div class='panel'><h3>Maturidade Global</h3></div>", unsafe_allow_html=True)
            st.pyplot(build_readiness_gauge_figure(cri_data), clear_figure=True)
        with right:
            st.markdown("<div class='panel'><h3>Desempenho por Pilar</h3></div>", unsafe_allow_html=True)
            st.pyplot(build_components_figure(cri_data), clear_figure=True)

    with action_plan_tab:
        st.markdown("<div class='panel'><h3>Hub de Ações Consolidadas (Action Plan)</h3></div>", unsafe_allow_html=True)
        st.dataframe(action_df_dash, width="stretch", hide_index=True)

    with report_tab:
        st.info("Aba de Geração de Relatório em PDF/Markdown (Simplificada para foco).")
    
    with cases_tab:
        st.info("Aba de Salvar/Carregar Cenários da Base de Dados.")

# ==============================================================================

elif selected_module == t("module_eng", lang):
    tabs = st.tabs(["Overview", t("tab_compound", lang), "Reatividade Química", "Fontes / Evidências"])
    overview_tab, compound_tab, reactivity_tab, sources_tab = tabs

    with overview_tab:
        dispersion_mode = classify_dispersion_mode(profile)
        c1, c2, c3 = st.columns(3)
        c1.markdown(metric_card("Composto", profile.identity.get("name", "—")), unsafe_allow_html=True)
        c2.markdown(metric_card("CAS", profile.identity.get("cas", "—")), unsafe_allow_html=True)
        c3.markdown(metric_card("Confiança do Pacote", f"{profile.confidence_score:.0f}/100"), unsafe_allow_html=True)
        
        st.markdown("<div class='panel'><h3>Hazard Fingerprint</h3></div>", unsafe_allow_html=True)
        st.pyplot(build_hazard_fingerprint_figure(profile), clear_figure=True)

    with compound_tab:
        st.markdown("<div class='panel'><h3>Propriedades Físico-Químicas</h3></div>", unsafe_allow_html=True)
        st.dataframe(format_physchem_df(profile), width="stretch", hide_index=True)

    with reactivity_tab:
        st.markdown("<div class='panel'><h3>Matriz de Reatividade</h3></div>", unsafe_allow_html=True)
        st.pyplot(build_incompatibility_matrix_figure(profile), clear_figure=True)

    with sources_tab:
        st.markdown("<div class='panel'><h3>Ledger de Evidências (Governança)</h3></div>", unsafe_allow_html=True)
        st.dataframe(build_evidence_ledger_df(profile), width="stretch", hide_index=True)

# ==============================================================================

elif selected_module == t("module_risk", lang):
    tabs = st.tabs(["Segregação de Área", t("tab_hazop", lang), "LOPA", t("tab_whatif", lang), "Consequências"])
    area_tab, hazop_tab, lopa_tab, whatif_tab, cons_tab = tabs

    # SPRINT 12: ABA NOVA
    with area_tab:
        st.markdown("<div class='panel'><h3>Segregação por Área de Risco</h3></div>", unsafe_allow_html=True)
        st.markdown("<div class='note-card'>O risco muda drasticamente dependendo do ambiente e volume. Selecione a área para obter diretrizes específicas.</div><br>", unsafe_allow_html=True)
        
        area_selected = st.selectbox("Selecione a Área de Instalação",["Laboratório", "Almoxarifado", "Sala de Cilindros", "Tanque", "Utilidades"])
        
        area_data = evaluate_area_risk(profile, area_selected)
        
        col_w, col_s = st.columns(2)
        with col_w:
            st.error("🚨 **Avisos de Segurança para esta área:**")
            for w in area_data["warnings"]:
                st.write(f"- {w}")
        with col_s:
            st.success("🛡️ **Salvaguardas Mínimas Recomendadas:**")
            for s in area_data["safeguards"]:
                st.write(f"- {s}")

    with hazop_tab:
        st.markdown("<div class='panel'><h3>HAZOP Worksheet Base</h3></div>", unsafe_allow_html=True)
        st.info("Tabela de Desvios (Nó, Parâmetro, Palavra-Guia) - Visualização simplificada.")

    with lopa_tab:
        st.markdown("<div class='panel'><h3>Cálculo de LOPA e SIL</h3></div>", unsafe_allow_html=True)
        st.info("Definição de F_ie, Seleção de IPLs e cálculo de MCF.")

    with whatif_tab:
        st.markdown("<div class='panel'><h3>What-If — Comparador de Proteção</h3></div>", unsafe_allow_html=True)
        st.info("Simulação de adição/remoção de IPLs (Ferramenta de CAPEX).")

    with cons_tab:
        st.markdown("<div class='panel'><h3>Modelagem de Consequências</h3></div>", unsafe_allow_html=True)
        st.info("Cálculos de Dispersão Gaussiana e Pool Fire.")

# ==============================================================================

elif selected_module == t("module_change", lang):
    tabs = st.tabs(["PSI / PSM", "MOC (Gestão de Mudanças)", "PSSR (Pré-Startup)"])
    psi_tab, moc_tab, pssr_tab = tabs

    with psi_tab:
        st.markdown("<div class='panel'><h3>Checklist de PSI / PSM</h3></div>", unsafe_allow_html=True)
        st.dataframe(build_psi_readiness_df(profile, None, None), width="stretch", hide_index=True)

    with moc_tab:
        st.markdown("<div class='panel'><h3>Avaliação de MOC</h3></div>", unsafe_allow_html=True)
        st.info("Formulário de impactos e cálculo de criticidade da mudança.")

    with pssr_tab:
        st.markdown("<div class='panel'><h3>PSSR Readiness</h3></div>", unsafe_allow_html=True)
        st.info("Checklist de prontidão para introdução de produto químico.")
