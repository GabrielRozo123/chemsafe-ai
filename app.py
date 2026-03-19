from __future__ import annotations

import sys
from pathlib import Path
import io
import math

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st
import graphviz

# Módulos Antigos e Ferramentas Visuais
from bowtie_visual import build_bowtie_custom_figure
from case_store import list_cases, load_case, save_case
from chemicals_seed import LOCAL_COMPOUNDS
from comparator import build_comparison_df, build_comparison_highlights
from compound_engine import build_compound_profile, suggest_hazop_priorities, suggest_lopa_ipls
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
from risk_visuals import build_confidence_figure, build_hazard_fingerprint_figure, build_incompatibility_matrix_figure, build_ipl_layers_figure, build_risk_matrix_figure, build_source_coverage_figure
from source_governance import build_evidence_ledger_df, build_source_recommendations, summarize_evidence
from source_visuals import build_link_coverage_figure, build_source_summary_figure
from ui_formatters import format_identity_df, format_limits_df, format_physchem_df

# NOVOS MÓDULOS SPRINT 11 A 18
from action_hub import build_consolidated_action_plan
from dashboard_engine import calculate_case_readiness_index
from dashboard_visuals import build_readiness_gauge_figure, build_components_figure
from scenario_compare import build_what_if_comparison
from i18n import t
from area_engine import evaluate_area_risk
from scenario_library import get_typical_scenarios
from regulatory_engine import check_regulatory_framework, generate_facilitator_questions
from map_visuals import render_map_in_streamlit
from historical_engine import get_relevant_historical_cases
from pid_engine import EQUIPMENT_PARAMETERS, generate_hazop_from_topology, process_bulk_pid_nodes
from domino_engine import calculate_domino_effect
from ce_matrix_engine import generate_ce_matrix_from_hazop

# MÓDULOS SPRINT 19 E 20
from hra_engine import calculate_human_error_probability
from psv_engine import size_psv_gas
from ml_reliability_engine import calculate_dynamic_pfd
from runaway_engine import calculate_tmr_adiabatic

# CSS: Interface Vale do Silício (Progressive Disclosure, Clean Dark Theme)
APP_CSS = """
<style>
:root { --bg-color: #0b0f19; --card-bg: #151b28; --border-color: #2a3441; --text-main: #d1d5db; --accent-blue: #3b82f6; --accent-glow: rgba(59, 130, 246, 0.15); }
.stApp { background-color: var(--bg-color); color: var(--text-main); font-family: 'Inter', -apple-system, sans-serif; }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1440px; }
.context-header { background: var(--card-bg); border: 1px solid var(--border-color); padding: 15px 25px; border-radius: 12px; margin-bottom: 30px; font-weight: 500; font-size: 0.95rem; color: #9ca3af; display: flex; justify-content: space-between; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }
.context-header span { color: #fff; font-weight: 600; }
.panel { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; padding: 1.8rem; margin-bottom: 1.2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.15); transition: border-color 0.3s ease; }
.panel:hover { border-color: var(--accent-blue); box-shadow: 0 4px 20px var(--accent-glow); }
.panel h3 { margin-top: 0; color: #f3f4f6; font-size: 1.15rem; font-weight: 600; border-bottom: 1px solid var(--border-color); padding-bottom: 10px; margin-bottom: 20px; }
.metric-box { background: rgba(30, 41, 59, 0.5); border: 1px solid var(--border-color); border-radius: 10px; padding: 20px; text-align: center; }
.metric-label { color: #9ca3af; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }
.metric-value { color: #f9fafb; font-size: 2rem; font-weight: 800; margin-top: 8px; font-variant-numeric: tabular-nums; }
.risk-blue { color: var(--accent-blue); } .risk-green { color: #10b981; } .risk-amber { color: #f59e0b; } .risk-red { color: #ef4444; }
.note-card { background: rgba(59, 130, 246, 0.08); border-left: 4px solid var(--accent-blue); padding: 15px; border-radius: 6px; font-size: 0.9rem; margin-bottom: 20px; color: #bfdbfe; line-height: 1.5; }
.history-card { background: rgba(22, 27, 34, 0.8); border-left: 4px solid #d29922; padding: 15px; border-radius: 8px; margin-bottom: 15px; }
.stExpander { border: 1px solid var(--border-color) !important; border-radius: 10px !important; background: var(--card-bg) !important; overflow: hidden; }
</style>
"""

st.set_page_config(page_title="ChemSafe Pro Enterprise", page_icon="⚗️", layout="wide", initial_sidebar_state="expanded")
st.markdown(APP_CSS, unsafe_allow_html=True)

# =========================
# Estado da sessão
# =========================
if "lang" not in st.session_state: st.session_state.lang = "pt"
if "selected_compound_key" not in st.session_state: st.session_state.selected_compound_key = "ammonia"
if "profile" not in st.session_state: st.session_state.profile = None
if "compare_query" not in st.session_state: st.session_state.compare_query = ""
if "lopa_result" not in st.session_state: st.session_state.lopa_result = None
if "pid_hazop_matrix" not in st.session_state: st.session_state.pid_hazop_matrix = []
if "current_node_name" not in st.session_state: st.session_state.current_node_name = "Nó 101: Bomba de Recalque"
if "current_case_name" not in st.session_state: st.session_state.current_case_name = ""
if "current_case_notes" not in st.session_state: st.session_state.current_case_notes = ""
if "moc_result" not in st.session_state: st.session_state.moc_result = None
if "pssr_result" not in st.session_state: st.session_state.pssr_result = None
if "reactivity_result" not in st.session_state: st.session_state.reactivity_result = None
if "dispersion_result" not in st.session_state: st.session_state.dispersion_result = None
if "pool_fire_result" not in st.session_state: st.session_state.pool_fire_result = None

def metric_card(label: str, value: str, klass: str = "risk-blue") -> str:
    return f"<div class='metric-box'><div class='metric-label'>{label}</div><div class='metric-value {klass}'>{value}</div></div>"

def load_profile_from_key(key: str) -> None:
    aliases = LOCAL_COMPOUNDS[key]["aliases"]
    st.session_state.profile = build_compound_profile(aliases[0])
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
    
    st.markdown(f"## ⚗️ {t('app_title', lang)}\n**Enterprise Edition**")
    st.caption("Process Safety Intelligence Engine")
    st.markdown("---")
    
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
    manual_query = st.text_input(t("search_compound", lang), placeholder="CAS ou Nome")
    if st.button(t("load_compound", lang), width="stretch") and manual_query.strip():
        st.session_state.profile = build_compound_profile(manual_query.strip())

if st.session_state.profile is None:
    load_profile_from_key(st.session_state.selected_compound_key)
profile = st.session_state.profile

# BREADCRUMB DE CONTEXTO
st.markdown(f"""
<div class="context-header">
    <div>🧪 Ativo Analisado: <span>{profile.identity.get('name', 'N/A')} (CAS: {profile.identity.get('cas', 'N/A')})</span></div>
    <div>🏭 Topologia Foco: <span>{st.session_state.current_node_name}</span></div>
</div>
""", unsafe_allow_html=True)

# Dashboards Globais
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
        c1.markdown(metric_card("Índice Global", f"{cri_data['index']}%", cri_data['color_class']), unsafe_allow_html=True)
        c2.markdown(metric_card("Status Atual", cri_data['band'], cri_data['color_class']), unsafe_allow_html=True)
        c3.markdown(metric_card("Ações Abertas", str(len(action_df_dash)), "risk-amber" if len(action_df_dash) > 0 else "risk-green"), unsafe_allow_html=True)
        gaps_crit = len(action_df_dash[action_df_dash["Criticidade"].isin(["Alta", "Crítica"])]) if len(action_df_dash) > 0 else 0
        c4.markdown(metric_card("Gaps Críticos", str(gaps_crit), "risk-red" if gaps_crit > 0 else "risk-green"), unsafe_allow_html=True)
        
        left, right = st.columns(2)
        with left:
            st.markdown("<div class='panel'><h3>Matriz de Maturidade</h3></div>", unsafe_allow_html=True)
            st.pyplot(build_readiness_gauge_figure(cri_data), clear_figure=True)
        with right:
            st.markdown("<div class='panel'><h3>Distribuição por Pilares</h3></div>", unsafe_allow_html=True)
            st.pyplot(build_components_figure(cri_data), clear_figure=True)

    with action_plan_tab:
        st.markdown("<div class='panel'><h3>Hub de Ações Consolidadas (Action Plan)</h3></div>", unsafe_allow_html=True)
        st.dataframe(action_df_dash, use_container_width=True, hide_index=True)

    with report_tab:
        st.markdown("<div class='panel'><h3>Relatório Executivo Automático</h3></div>", unsafe_allow_html=True)
        report_case_name = st.text_input("Nome do Relatório", value=st.session_state.current_case_name or profile.identity.get("name", "Caso"))
        if st.button("Gerar Relatório Completo", type="primary"):
            bundle = build_executive_bundle(
                case_name=report_case_name, profile=profile,
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
            st.success("Relatório Compilado com Sucesso!")
        if st.session_state.get("report_bundle"):
            st.download_button("📥 Baixar Documento (Markdown)", st.session_state.report_bundle["markdown"], file_name=f"{report_case_name}.md")
            st.download_button("📥 Baixar Documento (HTML)", st.session_state.report_bundle["html"], file_name=f"{report_case_name}.html")

    with cases_tab:
        st.markdown("<div class='panel'><h3>Gestão e Histórico de Casos</h3></div>", unsafe_allow_html=True)
        c1, c2 = st.columns([2, 3])
        with c1: case_name = st.text_input("Nome do caso", value=st.session_state.current_case_name)
        with c2: case_notes = st.text_area("Notas Técnicas", value=st.session_state.current_case_notes, height=68)
        col_save, col_load = st.columns([1, 1])
        with col_save:
            if st.button("Salvar Progresso Atual", type="primary", width="stretch"):
                save_case(case_name, profile, case_notes, st.session_state.get("lopa_result"), st.session_state.get("selected_ipl_names", []), bowtie_payload(), st.session_state.get("moc_result"), st.session_state.get("pssr_result"), st.session_state.get("reactivity_result"))
                st.session_state.current_case_name = case_name
                st.success("Dados salvos de forma segura.")
        cases = list_cases()
        if cases:
            selected_case = col_load.selectbox("Projetos Disponíveis", [c["case_name"] for c in cases])
            if col_load.button("Carregar Projeto", width="stretch"):
                apply_loaded_case(load_case(selected_case))
                st.rerun()

# ==============================================================================
# MÓDULO 2: ENGENHARIA DE DADOS
# ==============================================================================
elif selected_module == t("module_eng", lang):
    tabs = st.tabs(["Físico-Química", "🔥 Cinética / Runaway", "🧮 Dimensionamento PSV", "📚 Histórico & Misturas"])
    prop_tab, run_tab, psv_tab, hist_tab = tabs
    
    with prop_tab:
        dispersion_mode = classify_dispersion_mode(profile)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(metric_card("Ativo Base", profile.identity.get("name", "—")), unsafe_allow_html=True)
        c2.markdown(metric_card("Peso Molar", f"{profile.identity.get('molecular_weight', '—')} g/mol"), unsafe_allow_html=True)
        c3.markdown(metric_card("Dispersão", dispersion_mode["label"]), unsafe_allow_html=True)
        c4.markdown(metric_card("Confiança do Dado", f"{profile.confidence_score:.0f}%"), unsafe_allow_html=True)
        
        st.markdown("<div class='panel'><h3>⚖️ Enquadramento Regulatório (OSHA PSM / NR-20)</h3></div>", unsafe_allow_html=True)
        inv_kg = st.number_input("Inventário Estimado na Planta (kg)", min_value=0.0, value=5000.0, step=500.0)
        for alert in check_regulatory_framework(profile, inv_kg):
            if "Isento" in alert: st.success(alert)
            else: st.warning(alert)
            
        left, right = st.columns(2)
        with left:
            st.markdown("<div class='panel'><h3>Identidade e Perigos GHS</h3></div>", unsafe_allow_html=True)
            st.dataframe(format_identity_df(profile), use_container_width=True, hide_index=True)
            for hz in profile.hazards: st.error(hz)
        with right:
            st.markdown("<div class='panel'><h3>Termodinâmica e Limites</h3></div>", unsafe_allow_html=True)
            st.dataframe(format_physchem_df(profile), use_container_width=True, hide_index=True)
            st.dataframe(format_limits_df(profile), use_container_width=True, hide_index=True)

    with run_tab:
        st.markdown("<div class='panel'><h3>🔥 Simulação de Runaway Térmico (Semenov)</h3></div>", unsafe_allow_html=True)
        st.markdown("<div class='note-card'><b>Referência: CCPS Reactive Materials.</b> Estima o TMR (Time to Maximum Rate) em condições adiabáticas (falha de resfriamento).</div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            t0 = st.number_input("Temp. Operação (°C)", value=80.0)
            ea = st.number_input("Energia de Ativação (kJ/mol)", value=100.0)
        with col2:
            dh = st.number_input("Calor de Reação - ΔHr (kJ/kg)", value=1500.0)
            cp = st.number_input("Calor Específico - Cp (kJ/kg.K)", value=2.5)
        with col3:
            a_s = st.number_input("Fator Pré-Exponencial (1/s)", value=1e12, format="%.1e")
            
        if st.button("⚡ Calcular TMR Adiabático", type="primary"):
            tmr_res = calculate_tmr_adiabatic(t0, ea, a_s, dh, cp)
            st.markdown(f"### Tempo de Resposta Restante (TMR): **{tmr_res['tmr_min']:.1f} minutos**")
            st.markdown(metric_card("Ação Exigida", tmr_res['status'], f"risk-{tmr_res['color']}"), unsafe_allow_html=True)
            st.caption(f"Ref: {tmr_res['references']} | {tmr_res['formula']}")

    with psv_tab:
        st.markdown("<div class='panel'><h3>🧮 Dimensionamento API 520 (Válvula de Alívio)</h3></div>", unsafe_allow_html=True)
        st.markdown("<div class='note-card'>A massa molar é injetada automaticamente com base no ativo em estudo.</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: w_req = st.number_input("Vazão Requerida (kg/h)", value=10000.0)
        with c2: p_rel = st.number_input("Pressão de Setpoint (kPag)", value=500.0)
        with c3: t_rel = st.number_input("Temp. no Alívio (°C)", value=50.0)
        if st.button("Dimensionar Orifício", type="primary"):
            mw = float(profile.identity.get("molecular_weight", 28.0) or 28.0)
            psv_res = size_psv_gas(W_kg_h=w_req, T_C=t_rel, P1_kPag=p_rel, Z=1.0, MW=mw)
            st.success(f"**Orifício Padrão API Selecionado:** Letra {psv_res['api_letter']} ({psv_res['api_area_mm2']} mm²)")
            st.write(f"Área Estrita Calculada: {psv_res['calculated_area_mm2']:.2f} mm²")

    with hist_tab:
        st.markdown("<div class='panel'><h3>🧪 Laboratório de Reatividade e Lições Aprendidas</h3></div>", unsafe_allow_html=True)
        partner_query = st.text_input("Composto para avaliar mistura com o atual")
        if st.button("Analisar Incompatibilidade", type="primary") and partner_query:
            partner_profile = build_compound_profile(partner_query)
            st.session_state.reactivity_result = evaluate_pairwise_reactivity(profile, partner_profile)
            res = st.session_state.reactivity_result
            if res:
                a, b, c = st.columns(3)
                a.markdown(metric_card("Ativo A", res["summary"]["compound_a"]), unsafe_allow_html=True)
                b.markdown(metric_card("Ativo B", res["summary"]["compound_b"]), unsafe_allow_html=True)
                c.markdown(metric_card("Consequência", res["summary"]["severity"], "risk-red" if res["summary"]["severity"] != "OK" else "risk-green"), unsafe_allow_html=True)
        
        st.markdown("<hr><h4>📚 Banco de Acidentes Curado</h4>", unsafe_allow_html=True)
        relevant_cases = get_relevant_historical_cases(profile)
        if relevant_cases:
            for case in relevant_cases[:2]:
                st.markdown(f"<div class='history-card'><b>{case['evento']} ({case['ano']})</b><br>Mecanismo: {case['mecanismo']}<br><i>Fonte: {case['fonte']}</i></div>", unsafe_allow_html=True)
        else:
            st.info("Nenhum evento correlato crítico encontrado na base.")

# ==============================================================================
# MÓDULO 3: ANÁLISE DE RISCO (HAZOP, LOPA, P&ID)
# ==============================================================================
elif selected_module == t("module_risk", lang):
    tabs = st.tabs(["🏗️ P&ID Visual Builder", "📋 HAZOP & C&E", "🛡️ ML-LOPA & HRA", "🌪️ Dominó & F&G Maps"])
    pid_tab, hazop_tab, lopa_tab, cons_tab = tabs

    # ABA 1: P&ID VISUAL (Graphviz)
    with pid_tab:
        st.markdown("<div class='panel'><h3>🏗️ Topologia da Planta e Geração de Cenários</h3></div>", unsafe_allow_html=True)
        
        t1, t2 = st.tabs(["Visual Builder (Nó Único)", "Processamento em Lote (Excel/CSV)"])
        
        with t1:
            st.markdown("<div class='note-card'>Selecione os equipamentos em série. O grafo é atualizado dinamicamente.</div>", unsafe_allow_html=True)
            col1, col2 = st.columns([1, 2])
            with col1:
                st.session_state.current_node_name = st.text_input("Identificação do Nó", value=st.session_state.current_node_name)
            with col2:
                selected_equipment = st.multiselect("Fluxo de Equipamentos", options=list(EQUIPMENT_PARAMETERS.keys()), default=["Tanque de Armazenamento Atmosférico", "Bomba Centrífuga"])
                
            if selected_equipment:
                dot = graphviz.Digraph()
                dot.attr(rankdir='LR', bgcolor='transparent')
                dot.attr('node', shape='box', style='filled', fillcolor='#1e293b', color='#3b82f6', fontcolor='white', fontname='Inter', penwidth='2')
                dot.attr('edge', color='#9ca3af', penwidth='2')
                for i, eq in enumerate(selected_equipment):
                    dot.node(str(i), eq)
                    if i > 0: dot.edge(str(i-1), str(i))
                st.graphviz_chart(dot, use_container_width=True)

            if st.button("🚀 Processar Grafo e Criar HAZOP", type="primary"):
                st.session_state.pid_hazop_matrix = generate_hazop_from_topology(st.session_state.current_node_name, selected_equipment, profile)
                st.success("Análise de Perigos concluída! Verifique a próxima aba.")
                
        with t2:
            st.markdown("<div class='note-card'>Importe a <b>Equipment List</b> do seu software CAD 3D para processar a fábrica inteira.</div>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader("Upload CSV/XLSX (Colunas: Nó, Equipamento)", type=["csv", "xlsx"])
            if uploaded_file is not None:
                df_bulk = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                if st.button("⚡ Executar Bulk Process", type="primary"):
                    bulk_results = process_bulk_pid_nodes(df_bulk, profile)
                    if bulk_results:
                        st.session_state.pid_hazop_matrix = bulk_results
                        st.success(f"Excelente. Foram mapeados {len(bulk_results)} desvios termodinâmicos.")

    # ABA 2: HAZOP E C&E
    with hazop_tab:
        st.markdown("<div class='panel'><h3>Matrizes de Risco e Automação</h3></div>", unsafe_allow_html=True)
        if st.session_state.get("pid_hazop_matrix"):
            with st.expander("📋 Estudo HAZOP Completo (IEC 61882)", expanded=True):
                df_hazop = pd.DataFrame(st.session_state.pid_hazop_matrix)
                st.dataframe(df_hazop, use_container_width=True, hide_index=True)
                st.download_button("📥 Download HAZOP", df_hazop.to_csv(index=False).encode('utf-8'), "hazop.csv", "text/csv")
            
            with st.expander("🔀 Matriz Causa e Efeito para PLC (IEC 61511)", expanded=False):
                df_ce = generate_ce_matrix_from_hazop(st.session_state.pid_hazop_matrix)
                if not df_ce.empty:
                    st.dataframe(df_ce, use_container_width=True, hide_index=True)
                    st.download_button("📥 Download C&E Matrix", df_ce.to_csv(index=False).encode('utf-8'), "ce_matrix.csv", "text/csv")
                else:
                    st.info("Nenhuma arquitetura de Trip/Alarme detectada no HAZOP para formar matriz.")
        else:
            st.warning("O sistema requer uma topologia definida na aba anterior.")

    # ABA 3: LOPA, ML, E HRA
    with lopa_tab:
        st.markdown("<div class='panel'><h3>🛡️ LOPA com PFD Dinâmico (OREDA) e HRA (THERP)</h3></div>", unsafe_allow_html=True)
        st.markdown("<div class='note-card'>Substitua as taxas de falha estáticas por análises de fadiga (Weibull) e confiabilidade humana rigorosas.</div>", unsafe_allow_html=True)
        
        c_ml, c_hra, c_lopa = st.columns([1, 1, 1.2])
        
        with c_ml:
            st.markdown("#### 🤖 ML/OREDA Wear-Out")
            eq_type = st.selectbox("Equipamento Analisado", ["Bomba de Resfriamento", "Válvula de Bloqueio (SDV)"])
            t_meses = st.slider("Meses em Serviço", 1, 60, 24)
            anomaly = st.slider("Alarme de Vibração (ML)", 0.0, 1.0, 0.2)
            base_pfd = 1e-2 if "Bomba" in eq_type else 1e-3
            dyn_res = calculate_dynamic_pfd(base_pfd, t_meses, anomaly, eq_type)
            st.metric("PFD Ajustado", dyn_res["pfd_str"], f"+{dyn_res['risk_increase_pct']:.0f}% Degradação", delta_color="inverse")
            
        with c_hra:
            st.markdown("#### 🧠 HRA Operador")
            t_av = st.selectbox("Tempo P/ Agir", ["Menos de 5 minutos", "5 a 10 minutos", "10 a 30 minutos"])
            stress = st.selectbox("Estresse", ["Extremo (Emergência Crítica)", "Alto (Alarme de Alta Prioridade)", "Nominal"])
            comp = st.selectbox("Complexidade", ["Alta (Múltiplas válvulas/painéis)", "Baixa (Pressionar botão de emergência)"])
            if st.button("Obter Erro Humano (HEP)"):
                hra_res = calculate_human_error_probability(t_av, stress, comp)
                st.success(f"**HEP:** {hra_res['pfd_equivalent']}")
                st.caption(f"Norma: {hra_res['references']}")
                
        with c_lopa:
            st.markdown("#### 📊 Calculadora LOPA")
            f_ie = st.number_input("Freq. Evento Iniciador (1/ano)", value=0.1, format="%.3f")
            opcoes_ipl = [f"{n} (PFD={p})" for n, p in IPL_CATALOG]
            opcoes_ipl.append(f"{eq_type} Degradada (PFD={dyn_res['dynamic_pfd']:.1e})")
            selected_ipls = st.multiselect("IPLs Instaladas", opcoes_ipl)
            
            if st.button("Simular SIL Global", type="primary"):
                chosen_pfds = []
                for lbl in selected_ipls:
                    try:
                        val = float(lbl.split("PFD=")[1].replace(")", ""))
                        chosen_pfds.append(("Barreira", val))
                    except: pass
                st.session_state.lopa_result = compute_lopa(f_ie, 1e-4, chosen_pfds)
                res = st.session_state.lopa_result
                st.info(f"Freq. Mitigada (MCF): **{res['mcf']:.2e}/ano**")
                st.markdown(metric_card("SIL Target", res["sil"], "risk-amber"), unsafe_allow_html=True)

    # ABA 4: DOMINÓ, FIRE & GAS, E MAPAS
    with cons_tab:
        st.markdown("<div class='panel'><h3>🌪️ Avaliação de Efeito Dominó e Mapas</h3></div>", unsafe_allow_html=True)
        
        with st.expander("🔥 API 521: Radiação Térmica em Estruturas Vizinhas", expanded=True):
            d1, d2, d3 = st.columns(3)
            with d1: dist = st.number_input("Distância ao Alvo Crítico (m)", value=15.0)
            with d2: m_rate = st.number_input("Vazão de Liberação (kg/s)", value=10.0)
            with d3: hc = st.number_input("Calor de Combustão (MJ/kg)", value=44.0)
            if st.button("Verificar Falha de Equipamentos"):
                domino = calculate_domino_effect(dist, m_rate, hc * 1e6)
                st.error(f"**{domino['status']}** | Radiação Estimada: {domino['q_kW_m2']:.2f} kW/m²")
                st.caption(f"Impacto Normativo: {domino['impact']}")
                
        with st.expander("📡 ISA TR84: F&G Mapping Sugerido", expanded=False):
            if st.button("Posicionar Detectores de Gás (LFL)"):
                lfl = float(profile.limit("LEL_vol", 5.0))
                st.success(f"**Perfil Inflamável Ativo.** O limite de explosividade (LEL) é {lfl}% vol.")
                st.write("- **Anel Primário (Alarme 10% LEL):** Aconselha-se proximidade à fonte de liberação.")
                st.write("- **Anel Secundário (Intertravamento 25% LEL):** Disparo de válvula SDV e espuma de combate.")

        with st.expander("🌍 Integração GIS de Dispersão", expanded=False):
            c1, c2 = st.columns(2)
            with c1: lat = st.number_input("Latitude", value=-22.8188, format="%.6f")
            with c2: lon = st.number_input("Longitude", value=-47.0635, format="%.6f")
            st.caption("Pressione o ícone de camadas no mapa para exportação em PDF.")
            render_map_in_streamlit(lat=lat, lon=lon, dispersion_data=st.session_state.get("dispersion_result"), thermal_data=st.session_state.get("pool_fire_result"))

# ==============================================================================
# MÓDULO 4: GESTÃO DE MUDANÇA E PRÉ-STARTUP (MOC / PSSR)
# ==============================================================================
elif selected_module == t("module_change", lang):
    tabs = st.tabs(["Auditoria PSI", "🔄 MOC (Gestão de Mudanças)", "✅ PSSR (Pré-Startup)"])
    psi_tab, moc_tab, pssr_tab = tabs

    with psi_tab:
        st.markdown("<div class='panel'><h3>Auditoria Global do Perfil (PSI)</h3></div>", unsafe_allow_html=True)
        st.markdown("<div class='note-card'>Avalia a consistência das informações de segurança de processo disponíveis no momento para este composto.</div>", unsafe_allow_html=True)
        st.dataframe(build_psi_readiness_df(profile, st.session_state.get("lopa_result"), bowtie_payload()), use_container_width=True, hide_index=True)

    with moc_tab:
        st.markdown("<div class='panel'><h3>🔄 Avaliação e Roteamento de MOC</h3></div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            change_type = st.selectbox("Tipo da Proposta de Mudança", ["Mudança química / novo composto", "Mudança de condição operacional", "Mudança de equipamento", "Mudança de procedimento"])
            impacts = st.multiselect("Áreas de Impacto", ["Química / composição", "Pressão", "Temperatura", "Inventário", "Alívio / PSV", "Instrumentação / controle"])
            desc = st.text_area("Justificativa Técnica")
        with c2:
            st.write("Fatores de Agravamento de Risco:")
            p1 = st.checkbox("Mudança em caráter temporário")
            p2 = st.checkbox("Afeta Sistemas Instrumentados (SIS/Trips) ou PSV")
            p3 = st.checkbox("Requer Bypass / Override de alarmes")
        
        if st.button("Submeter para Análise de Criticidade MOC", type="primary"):
            st.session_state.moc_result = evaluate_moc(profile, change_type, impacts, desc, temporary=p1, protections_changed=p2, bypass_or_override=p3)
            
        res = st.session_state.get("moc_result")
        if res:
            st.markdown(f"<br><b>Classificação MOC:</b> {res['summary']['category']} | <b>Score:</b> {res['summary']['score']}/100", unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(res["checklist_rows"]), use_container_width=True, hide_index=True)

    with pssr_tab:
        st.markdown("<div class='panel'><h3>✅ Check de Partida Segura (PSSR)</h3></div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            d1 = st.checkbox("Inspeção de campo aprovou montagem vs. P&ID")
            d2 = st.checkbox("Procedimentos Operacionais atualizados e emitidos")
            d3 = st.checkbox("Equipe de turno totalmente treinada")
        with c2:
            d4 = st.checkbox("Rotas de alívio e PSVs verificadas")
            d5 = st.checkbox("Testes de Causa e Efeito (Intertravamentos) concluídos com sucesso")
            d6 = st.checkbox("Aprovação final do Engenheiro Chefe/Gerente")
            
        if st.button("Verificar Go/No-Go", type="primary"):
            st.session_state.pssr_result = evaluate_pssr(design_ok=d1, procedures_ok=d2, training_ok=d3, relief_verified=d4, alarms_tested=d5, startup_authorized=d6, pha_or_moc_ok=True, mi_ready=True, emergency_ready=True, scope_label="PSSR")
            
        res = st.session_state.get("pssr_result")
        if res:
            st.markdown(f"<br><b>Status do Startup:</b> {res['summary']['readiness']} | <b>Confiabilidade:</b> {res['summary']['score']}%", unsafe_allow_html=True)
            for block in res["blockers"]:
                st.error(block)
