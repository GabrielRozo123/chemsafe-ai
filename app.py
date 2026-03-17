from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st

# Módulos Antigos e Ferramentas Visuais
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
from source_governance import build_evidence_ledger_df, build_source_recommendations, summarize_evidence
from source_visuals import build_link_coverage_figure, build_source_summary_figure
from ui_formatters import format_identity_df, format_limits_df, format_physchem_df

# NOVOS MÓDULOS SPRINT 11, 12 e 13
from action_hub import build_consolidated_action_plan
from dashboard_engine import calculate_case_readiness_index
from dashboard_visuals import build_readiness_gauge_figure, build_components_figure
from scenario_compare import build_what_if_comparison
from i18n import t
from area_engine import evaluate_area_risk
from scenario_library import get_typical_scenarios

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
.panel { background: rgba(9,17,31,0.94); border: 1px solid #1d365f; border-radius: 18px; padding: 1rem 1rem 0.95rem 1rem; margin-bottom: 0.9rem; box-shadow: 0 8px 18px rgba(0,0,0,0.10); }
.panel h3 { margin-top: 0; margin-bottom: 0.8rem; color: #f0f6ff; font-size: 1rem; font-weight: 800; }
.note-card { background: rgba(12, 28, 54, 0.95); border-left: 4px solid #4b88ff; border-radius: 12px; padding: 0.9rem 1rem; color: #e9f1ff; }
.kpi-chip { display: inline-block; padding: 0.28rem 0.65rem; border-radius: 999px; border: 1px solid #2b5aa1; margin-right: 0.45rem; margin-bottom: 0.35rem; color: #d9e8ff; background: rgba(31, 74, 139, 0.14); font-size: 0.78rem; }
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
if "compare_profile" not in st.session_state: st.session_state.compare_profile = None
if "compare_query" not in st.session_state: st.session_state.compare_query = ""
if "lopa_result" not in st.session_state: st.session_state.lopa_result = None
if "dispersion_result" not in st.session_state: st.session_state.dispersion_result = None
if "pool_fire_result" not in st.session_state: st.session_state.pool_fire_result = None
if "selected_ipl_names" not in st.session_state: st.session_state.selected_ipl_names =[]
if "current_case_name" not in st.session_state: st.session_state.current_case_name = ""
if "current_case_notes" not in st.session_state: st.session_state.current_case_notes = ""
if "bowtie_initialized_for" not in st.session_state: st.session_state.bowtie_initialized_for = ""
if "moc_result" not in st.session_state: st.session_state.moc_result = None
if "pssr_result" not in st.session_state: st.session_state.pssr_result = None
if "reactivity_partner_profile" not in st.session_state: st.session_state.reactivity_partner_profile = None
if "reactivity_result" not in st.session_state: st.session_state.reactivity_result = None
if "report_bundle" not in st.session_state: st.session_state.report_bundle = None

# Helpers
def metric_card(label: str, value: str, klass: str = "risk-blue") -> str:
    return f"<div class='metric-box'><div class='metric-label'>{label}</div><div class='metric-value {klass}'>{value}</div></div>"

def load_profile_from_key(key: str) -> None:
    aliases = LOCAL_COMPOUNDS[key]["aliases"]
    st.session_state.profile = build_compound_profile(aliases[0])
    st.session_state.selected_compound_key = key

def _default_bowtie_lists(profile):
    threats, barriers_pre, consequences, barriers_mit = [], [], [],[]
    if profile.flags.get("flammable"):
        threats += ["Fonte de ignição", "Vazamento"]
        barriers_pre += ["Controle de ignição", "Detecção"]
        consequences +=["Incêndio", "Flash fire"]
        barriers_mit += ["Combate a incêndio", "Contenção"]
    if profile.flags.get("toxic_inhalation"):
        threats +=["Falha de vedação", "Abertura indevida"]
        barriers_pre += ["Isolamento", "ESD"]
        consequences += ["Exposição ocupacional", "Impacto comunitário"]
        barriers_mit +=["Alarme", "Evacuação"]
    
    return {
        "threats": threats or["Falha de equipamento"],
        "barriers_pre": barriers_pre or ["Procedimento operacional"],
        "top_event": "Perda de contenção / perda de controle",
        "barriers_mit": barriers_mit or ["Plano de emergência"],
        "consequences": consequences or ["Dano ao processo"],
    }

def ensure_bowtie_state(profile):
    compound_marker = profile.identity.get("name", "")
    if st.session_state.bowtie_initialized_for != compound_marker:
        defaults = _default_bowtie_lists(profile)
        st.session_state.bowtie_threats = "\n".join(defaults["threats"])
        st.session_state.bowtie_pre = "\n".join(defaults["barriers_pre"])
        st.session_state.bowtie_top = defaults["top_event"]
        st.session_state.bowtie_mit = "\n".join(defaults["barriers_mit"])
        st.session_state.bowtie_cons = "\n".join(defaults["consequences"])
        st.session_state.bowtie_initialized_for = compound_marker

def bowtie_payload():
    return {
        "threats":[x.strip() for x in st.session_state.get("bowtie_threats", "").splitlines() if x.strip()],
        "barriers_pre":[x.strip() for x in st.session_state.get("bowtie_pre", "").splitlines() if x.strip()],
        "top_event": st.session_state.get("bowtie_top", "Perda de contenção"),
        "barriers_mit":[x.strip() for x in st.session_state.get("bowtie_mit", "").splitlines() if x.strip()],
        "consequences":[x.strip() for x in st.session_state.get("bowtie_cons", "").splitlines() if x.strip()],
    }

def apply_loaded_case(case_data: dict):
    query_hint = case_data.get("query_hint") or case_data.get("compound_name")
    if query_hint:
        st.session_state.profile = build_compound_profile(query_hint)
    st.session_state.current_case_name = case_data.get("case_name", "")
    st.session_state.lopa_result = case_data.get("lopa_result")
    st.session_state.moc_result = case_data.get("moc_result")
    st.session_state.pssr_result = case_data.get("pssr_result")

# =========================
# Sidebar & Navegação
# =========================
with st.sidebar:
    lang = st.radio("🌐 Language / Idioma", ["pt", "en"], horizontal=True, label_visibility="collapsed")
    st.session_state.lang = lang

    st.markdown(f"## ⚗️ {t('app_title', lang)}")
    st.caption("Process Safety Intelligence Engine")
    st.markdown("---")

    st.write(f"**Navegação Principal**")
    selected_module = st.radio(
        "Módulos",
        options=[t("module_exec", lang), t("module_eng", lang), t("module_risk", lang), t("module_change", lang)],
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
ensure_bowtie_state(profile)

# =========================
# Hero & Processamento em Background
# =========================
st.markdown(
    f"""
    <div class="hero">
      <h1>{t('app_title', lang)}</h1>
      <p>Gestão de riscos guiada por propriedades reais, dados rastreáveis e inteligência determinística.</p>
    </div>
    """, unsafe_allow_html=True
)

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
# MÓDULO 1: VISÃO EXECUTIVA
# ==============================================================================
if selected_module == t("module_exec", lang):
    tabs = st.tabs([t("tab_dash", lang), t("tab_action", lang), "Relatório Executivo", "Casos Salvos"])
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
        st.markdown("<div class='panel'><h3>Relatório Executivo com Trilha de Evidências</h3></div>", unsafe_allow_html=True)
        report_case_name = st.text_input("Nome do Relatório", value=st.session_state.current_case_name or profile.identity.get("name", "Caso"))
        if st.button("Gerar Relatório", type="primary"):
            bundle = build_executive_bundle(
                case_name=report_case_name,
                profile=profile,
                context={
                    "evidence_summary": summarize_evidence(profile),
                    "evidence_recommendations": build_source_recommendations(profile),
                    "hazop_priorities": suggest_hazop_priorities(profile, "Equipamento Geral"),
                    "lopa_result": st.session_state.get("lopa_result"),
                    "psi_summary": summarize_psi_readiness(psi_df_dash),
                    "moc_result": st.session_state.get("moc_result"),
                    "pssr_result": st.session_state.get("pssr_result"),
                    "reactivity_result": st.session_state.get("reactivity_result"),
                }
            )
            st.session_state.report_bundle = bundle
            st.success("Relatório Gerado!")
        
        if st.session_state.report_bundle:
            st.download_button("Baixar Markdown", st.session_state.report_bundle["markdown"], file_name=f"{report_case_name}.md")
            st.download_button("Baixar HTML", st.session_state.report_bundle["html"], file_name=f"{report_case_name}.html")

    with cases_tab:
        st.markdown("<div class='panel'><h3>Gestão de Casos</h3></div>", unsafe_allow_html=True)
        c1, c2 = st.columns([2, 3])
        with c1: case_name = st.text_input("Nome do caso", value=st.session_state.current_case_name)
        with c2: case_notes = st.text_area("Notas", value=st.session_state.current_case_notes, height=68)
        
        col_save, col_load = st.columns([1, 1])
        with col_save:
            if st.button("Salvar Caso Atual", type="primary", width="stretch"):
                save_case(case_name, profile, case_notes, st.session_state.get("lopa_result"), st.session_state.get("selected_ipl_names",[]), bowtie_payload(), st.session_state.get("moc_result"), st.session_state.get("pssr_result"), st.session_state.get("reactivity_result"))
                st.session_state.current_case_name = case_name
                st.success("Salvo com sucesso!")
        
        cases = list_cases()
        if cases:
            selected_case = col_load.selectbox("Casos disponíveis", [c["case_name"] for c in cases])
            if col_load.button("Carregar Caso Selecionado", width="stretch"):
                apply_loaded_case(load_case(selected_case))
                st.rerun()

# ==============================================================================
# MÓDULO 2: ENGENHARIA DE DADOS
# ==============================================================================
elif selected_module == t("module_eng", lang):
    tabs = st.tabs(["Overview", t("tab_compound", lang), "Comparador", "Reatividade (Lab)", "Fontes / Evidências"])
    overview_tab, compound_tab, compare_tab, reactivity_tab, sources_tab = tabs

    with overview_tab:
        dispersion_mode = classify_dispersion_mode(profile)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(metric_card("Composto", profile.identity.get("name", "—")), unsafe_allow_html=True)
        c2.markdown(metric_card("CAS", profile.identity.get("cas", "—")), unsafe_allow_html=True)
        c3.markdown(metric_card("Confiança", f"{profile.confidence_score:.0f}/100"), unsafe_allow_html=True)
        c4.markdown(metric_card("Dispersão", dispersion_mode["label"]), unsafe_allow_html=True)
        
        left, right = st.columns(2)
        with left:
            st.markdown("<div class='panel'><h3>Hazard fingerprint</h3></div>", unsafe_allow_html=True)
            st.pyplot(build_hazard_fingerprint_figure(profile), clear_figure=True)
        with right:
            st.markdown("<div class='panel'><h3>Cobertura de fontes</h3></div>", unsafe_allow_html=True)
            st.pyplot(build_source_coverage_figure(profile), clear_figure=True)

        st.markdown("<div class='panel'><h3>Status do pacote de propriedades</h3></div>", unsafe_allow_html=True)
        status_summary = summarize_property_status(profile)
        chips =[f"<span class='kpi-chip'>{k}: {v}</span>" for k, v in status_summary.items()]
        st.markdown("".join(chips), unsafe_allow_html=True)
        st.dataframe(build_property_status_df(profile), width="stretch", hide_index=True)

    with compound_tab:
        left, right = st.columns(2)
        with left:
            st.markdown("<div class='panel'><h3>Identidade e descritores</h3></div>", unsafe_allow_html=True)
            st.dataframe(format_identity_df(profile), width="stretch", hide_index=True)
            st.markdown("<div class='panel'><h3>Perigos / GHS / Incompatibilidades</h3></div>", unsafe_allow_html=True)
            for hz in profile.hazards: st.error(hz)
            for inc in profile.storage.get("incompatibilities",[]): st.warning(f"Incompatível: {inc}")
        with right:
            st.markdown("<div class='panel'><h3>Propriedades físico-químicas</h3></div>", unsafe_allow_html=True)
            st.dataframe(format_physchem_df(profile), width="stretch", hide_index=True)
            st.markdown("<div class='panel'><h3>Limites de exposição</h3></div>", unsafe_allow_html=True)
            st.dataframe(format_limits_df(profile), width="stretch", hide_index=True)

    with compare_tab:
        st.markdown("<div class='panel'><h3>Comparador entre compostos</h3></div>", unsafe_allow_html=True)
        c1, c2 = st.columns([3, 1])
        with c1: st.session_state.compare_query = st.text_input("Segundo composto", value=st.session_state.compare_query)
        with c2:
            if st.button("Comparar", type="primary", width="stretch") and st.session_state.compare_query:
                st.session_state.compare_profile = build_compound_profile(st.session_state.compare_query)

        if st.session_state.compare_profile:
            st.dataframe(build_comparison_df(profile, st.session_state.compare_profile), width="stretch", hide_index=True)
            for line in build_comparison_highlights(profile, st.session_state.compare_profile):
                st.info(line)

    with reactivity_tab:
        st.markdown("<div class='panel'><h3>Reactivity Lab — Matriz de Substâncias</h3></div>", unsafe_allow_html=True)
        c1, c2 = st.columns([3, 1])
        with c1: partner_query = st.text_input("Segundo composto para avaliar mistura", key="react_query")
        with c2:
            if st.button("Carregar para Mistura", type="primary", width="stretch") and partner_query:
                st.session_state.reactivity_partner_profile = build_compound_profile(partner_query)
                st.session_state.reactivity_result = evaluate_pairwise_reactivity(profile, st.session_state.reactivity_partner_profile)

        res = st.session_state.get("reactivity_result")
        if res:
            summary = res["summary"]
            a, b, c = st.columns(3)
            a.markdown(metric_card("Composto A", summary["compound_a"]), unsafe_allow_html=True)
            b.markdown(metric_card("Composto B", summary["compound_b"]), unsafe_allow_html=True)
            c.markdown(metric_card("Severidade da Mistura", summary["severity"], "risk-red" if summary["severity"] != "OK" else "risk-green"), unsafe_allow_html=True)
            
            st.markdown("<div class='panel'><h3>Regras Disparadas</h3></div>", unsafe_allow_html=True)
            st.dataframe(res["hits_df"], width="stretch", hide_index=True)
            for rec in res["recommendations"]: st.warning(rec)

    with sources_tab:
        st.markdown("<div class='panel'><h3>Governança de Fontes (Ledger)</h3></div>", unsafe_allow_html=True)
        st.dataframe(build_evidence_ledger_df(profile), width="stretch", hide_index=True)

# ==============================================================================
# MÓDULO 3: ANÁLISE DE RISCO
# ==============================================================================
elif selected_module == t("module_risk", lang):
    tabs = st.tabs(["Segregação de Área", "HAZOP", "Bow-Tie", "LOPA", t("tab_whatif", lang), "Consequências"])
    area_tab, hazop_tab, bowtie_tab, lopa_tab, whatif_tab, cons_tab = tabs

    with area_tab:
        st.markdown("<div class='panel'><h3>Segregação por Área de Risco</h3></div>", unsafe_allow_html=True)
        st.markdown("<div class='note-card'>O risco muda drasticamente dependendo do ambiente e volume. Selecione a área para obter diretrizes específicas.</div><br>", unsafe_allow_html=True)
        area_selected = st.selectbox("Selecione a Área de Instalação",["Laboratório", "Almoxarifado", "Sala de Cilindros", "Tanque", "Utilidades"])
        
        area_data = evaluate_area_risk(profile, area_selected)
        col_w, col_s = st.columns(2)
        with col_w:
            st.error("🚨 **Avisos de Segurança para esta área:**")
            for w in area_data["warnings"]: st.write(f"- {w}")
        with col_s:
            st.success("🛡️ **Salvaguardas Mínimas Recomendadas:**")
            for s in area_data["safeguards"]: st.write(f"- {s}")

    with hazop_tab:
        st.markdown("<div class='panel'><h3>📚 Biblioteca de Cenários Típicos (Sprint 13)</h3></div>", unsafe_allow_html=True)
        st.markdown("<div class='note-card'>Com base nas propriedades, o sistema pré-carregou os cenários clássicos para acelerar sua análise.</div><br>", unsafe_allow_html=True)
        
        typical_scenarios = get_typical_scenarios(profile)
        if not typical_scenarios:
            st.info("Sem cenários críticos típicos atrelados a este perfil na base de dados.")
        else:
            for cenario in typical_scenarios:
                with st.expander(cenario["titulo"]):
                    st.write(f"**Desvio:** {cenario['desvio']}")
                    st.write(f"**Causa:** {cenario['causa']}")
                    st.error(f"**Consequência:** {cenario['consequencia']}")
                    st.success(f"**Salvaguardas:** {cenario['salvaguardas']}")

        st.markdown("<br><div class='panel'><h3>Worksheet HAZOP Base</h3></div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1: param = st.selectbox("Parâmetro", list(HAZOP_DB.keys()))
        with c2: guideword = st.selectbox("Palavra-guia",["MAIS", "MENOS", "NÃO / NENHUM"])
        
        db = HAZOP_DB.get(param, {}).get(guideword, {})
        if db:
            rows =[]
            for i, cause in enumerate(db.get("causas",[])):
                rows.append({
                    "Desvio": f"{guideword} {param}" if i == 0 else "idem",
                    "Causa": cause,
                    "Consequência": db.get("conseqs")[i] if i < len(db.get("conseqs")) else "—",
                    "Salvaguarda": db.get("salvags")[i] if i < len(db.get("salvags")) else "—",
                    "Recomendação": db.get("rec")[i] if i < len(db.get("rec")) else "—",
                })
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    with bowtie_tab:
        st.markdown("<div class='panel'><h3>Diagrama Bow-Tie Interativo</h3></div>", unsafe_allow_html=True)
        modo_bowtie = st.radio("Modo", ["Executivo", "Técnico"], horizontal=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.text_area("Ameaças", key="bowtie_threats", height=120)
            st.text_area("Barreiras Preventivas", key="bowtie_pre", height=120)
        with c2:
            st.text_input("Top Event", key="bowtie_top")
            st.text_area("Barreiras Mitigadoras", key="bowtie_mit", height=82)
            st.text_area("Consequências", key="bowtie_cons", height=82)

        bt = bowtie_payload()
        st.pyplot(build_bowtie_custom_figure(bt["threats"], bt["barriers_pre"], bt["top_event"], bt["barriers_mit"], bt["consequences"], modo_bowtie.lower()), clear_figure=True)

    with lopa_tab:
        st.markdown("<div class='panel'><h3>Análise de Camadas de Proteção (LOPA)</h3></div>", unsafe_allow_html=True)
        left, right = st.columns(2)
        with left:
            f_ie = st.number_input("Frequência do Evento Iniciador (1/ano)", value=0.1, format="%.4f")
            crit = st.selectbox("Critério de Risco",["Fatalidade — 1e-5", "Lesão Grave — 1e-4", "Lesão Leve — 1e-3"])
            crit_val = {"Fatalidade — 1e-5": 1e-5, "Lesão Grave — 1e-4": 1e-4, "Lesão Leve — 1e-3": 1e-3}[crit]
        with right:
            selected = st.multiselect("Selecione as IPLs",[f"{n} (PFD={p})" for n, p in IPL_CATALOG])
        
        if st.button("Calcular LOPA", type="primary"):
            chosen =[(n, p) for label in selected for n, p in IPL_CATALOG if n in label]
            st.session_state.selected_ipl_names = selected
            st.session_state.lopa_result = compute_lopa(f_ie, crit_val, chosen)

        res = st.session_state.lopa_result
        if res:
            a, b, c, d = st.columns(4)
            a.markdown(metric_card("F_ie", f"{res['f_ie']:.2e}"), unsafe_allow_html=True)
            b.markdown(metric_card("PFD Total", f"{res['pfd_total']:.2e}"), unsafe_allow_html=True)
            c.markdown(metric_card("MCF", f"{res['mcf']:.2e}", "risk-red" if res["ratio"] > 1 else "risk-green"), unsafe_allow_html=True)
            d.markdown(metric_card("SIL", res["sil"], "risk-amber"), unsafe_allow_html=True)

    with whatif_tab:
        st.markdown("<div class='panel'><h3>What-If — Simulador de Proteção (CAPEX)</h3></div>", unsafe_allow_html=True)
        base = st.session_state.get("lopa_result")
        if not base:
            st.info("⚠️ Calcule o caso na aba LOPA primeiro.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Cenário Base (Atual)**")
                st.write(f"MCF Atual: {base['mcf']:.2e}/ano")
            with c2:
                new_ipls = st.multiselect("Modificar IPLs",[f"{n} (PFD={p})" for n, p in IPL_CATALOG], default=st.session_state.get("selected_ipl_names", []))
                if st.button("Simular"):
                    chosen =[(n, p) for label in new_ipls for n, p in IPL_CATALOG if n in label]
                    mod_lopa = compute_lopa(base["f_ie"], base["criterion"], chosen)
                    st.dataframe(build_what_if_comparison(base, mod_lopa), width="stretch", hide_index=True)

    with cons_tab:
        st.markdown("<div class='panel'><h3>Modelagem de Consequências</h3></div>", unsafe_allow_html=True)
        tox_t, fire_t = st.tabs(["Dispersão Tóxica (Gaussiana)", "Fogo em Poça (Pool Fire)"])
        
        with tox_t:
            c1, c2, c3 = st.columns(3)
            q_gs = c1.number_input("Q (g/s)", value=10.0)
            u_ms = c2.number_input("Vento (m/s)", value=3.0)
            stab = c3.selectbox("Classe de Estabilidade", list("ABCDEF"), index=3)
            if st.button("Calcular Dispersão"):
                mw = profile.identity.get("molecular_weight", 20.0) or 20.0
                st.session_state.dispersion_result = gaussian_dispersion(q_gs, u_ms, stab, float(profile.limit("IDLH_ppm", 300)), float(mw), 0)
                st.write(f"**Distância até IDLH:** {st.session_state.dispersion_result.get('x_idlh', '>3000')} metros")

        with fire_t:
            c1, c2 = st.columns(2)
            diam = c1.number_input("Diâmetro (m)", value=5.0)
            dist = c2.number_input("Distância do Alvo (m)", value=20.0)
            if st.button("Calcular Pool Fire"):
                st.session_state.pool_fire_result = pool_fire(diam, 0.05, 44000, dist)
                st.write(f"**Fluxo Térmico no alvo:** {st.session_state.pool_fire_result['q_kW_m2']:.2f} kW/m²")

# ==============================================================================
# MÓDULO 4: GESTÃO DE MUDANÇA
# ==============================================================================
elif selected_module == t("module_change", lang):
    tabs = st.tabs(["PSI / PSM", "MOC (Gestão de Mudanças)", "PSSR (Pré-Startup)"])
    psi_tab, moc_tab, pssr_tab = tabs

    with psi_tab:
        st.markdown("<div class='panel'><h3>Checklist de Prontidão PSI/PSM</h3></div>", unsafe_allow_html=True)
        st.dataframe(build_psi_readiness_df(profile, st.session_state.get("lopa_result"), bowtie_payload()), width="stretch", hide_index=True)

    with moc_tab:
        st.markdown("<div class='panel'><h3>Avaliação de Impacto de Mudança (MOC)</h3></div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            change_type = st.selectbox("Tipo de Mudança",["Mudança química / novo composto", "Mudança de condição operacional", "Mudança de equipamento", "Mudança de procedimento"])
            impacts = st.multiselect("Impactos",["Química / composição", "Pressão", "Temperatura", "Inventário", "Alívio / PSV", "Instrumentação / controle"])
            desc = st.text_area("Descrição")
        with c2:
            st.write("Fatores Agravantes:")
            p1 = st.checkbox("Mudança Temporária")
            p2 = st.checkbox("Afeta Proteções (SIS/PSV)")
            p3 = st.checkbox("Envolve Bypass / Override")
        
        if st.button("Avaliar Criticidade do MOC", type="primary"):
            st.session_state.moc_result = evaluate_moc(profile, change_type, impacts, desc, temporary=p1, protections_changed=p2, bypass_or_override=p3)
            
        res = st.session_state.get("moc_result")
        if res:
            st.markdown(f"<br><b>Classe do MOC:</b> {res['summary']['category']} | <b>Score:</b> {res['summary']['score']}/100", unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(res["checklist_rows"]), width="stretch", hide_index=True)

    with pssr_tab:
        st.markdown("<div class='panel'><h3>Revisão de Segurança Pré-Partida (PSSR)</h3></div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            d1 = st.checkbox("Equipamento conforme especificação")
            d2 = st.checkbox("Procedimentos atualizados")
            d3 = st.checkbox("Treinamento concluído")
        with c2:
            d4 = st.checkbox("PSV e bloqueios inspecionados")
            d5 = st.checkbox("Alarmes testados")
            d6 = st.checkbox("Autorização gerencial assinada")
            
        if st.button("Calcular Prontidão PSSR", type="primary"):
            st.session_state.pssr_result = evaluate_pssr(design_ok=d1, procedures_ok=d2, training_ok=d3, relief_verified=d4, alarms_tested=d5, startup_authorized=d6, pha_or_moc_ok=True, mi_ready=True, emergency_ready=True, scope_label="PSSR")
            
        res = st.session_state.get("pssr_result")
        if res:
            st.markdown(f"<br><b>Status:</b> {res['summary']['readiness']} | <b>Score:</b> {res['summary']['score']}/100", unsafe_allow_html=True)
            for block in res["blockers"]:
                st.error(block)
