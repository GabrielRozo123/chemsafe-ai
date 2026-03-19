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

# Módulos Antigos e Ferramentas Visuais
from bowtie_visual import build_bowtie_custom_figure
from case_store import list_cases, load_case, save_case
from chemicals_seed import LOCAL_COMPOUNDS
from comparator import build_comparison_df
from compound_engine import build_compound_profile, suggest_hazop_priorities
from dense_gas_router import classify_dispersion_mode
from deterministic import IPL_CATALOG, compute_lopa, gaussian_dispersion, pool_fire
from executive_report import build_executive_bundle
from hazop_db import HAZOP_DB
from moc_engine import evaluate_moc
from psi_readiness import build_psi_readiness_df, summarize_psi_readiness
from pssr_engine import evaluate_pssr
from reactivity_engine import evaluate_pairwise_reactivity
from risk_visuals import build_hazard_fingerprint_figure, build_source_coverage_figure
from source_governance import build_evidence_ledger_df, build_source_recommendations, summarize_evidence
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

# MÓDULOS SPRINT 19
from hra_engine import calculate_human_error_probability
from psv_engine import size_psv_gas

# NOVO CSS: Filosofia "Vale do Silício" (Progressive Disclosure, Cores Neutras com Acentos Semânticos)
APP_CSS = """
<style>
:root { --bg-color: #0d1117; --card-bg: #161b22; --border-color: #30363d; --text-main: #c9d1d9; --accent-blue: #58a6ff; }
.stApp { background-color: var(--bg-color); color: var(--text-main); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1400px; }
.context-header { background: var(--card-bg); border-bottom: 1px solid var(--border-color); padding: 12px 20px; border-radius: 8px; margin-bottom: 25px; font-weight: 600; color: #8b949e; display: flex; justify-content: space-between; }
.context-header span { color: var(--accent-blue); }
.panel { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 10px; padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
.panel h3 { margin-top: 0; color: #f0f6ff; font-size: 1.1rem; border-bottom: 1px solid var(--border-color); padding-bottom: 8px; margin-bottom: 15px; }
.metric-box { background: rgba(22, 27, 34, 0.6); border: 1px solid var(--border-color); border-radius: 8px; padding: 15px; text-align: center; }
.metric-label { color: #8b949e; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; }
.metric-value { color: #ffffff; font-size: 1.8rem; font-weight: 700; margin-top: 5px; }
.risk-blue { color: var(--accent-blue); } .risk-green { color: #3fb950; } .risk-amber { color: #d29922; } .risk-red { color: #f85149; }
.note-card { background: rgba(88, 166, 255, 0.1); border-left: 4px solid var(--accent-blue); padding: 12px 15px; border-radius: 4px; font-size: 0.9rem; margin-bottom: 15px; }
.history-card { background: rgba(22, 27, 34, 0.8); border-left: 4px solid #d29922; padding: 15px; border-radius: 8px; margin-bottom: 15px; }
.stExpander { border: 1px solid var(--border-color) !important; border-radius: 8px !important; background: var(--card-bg) !important; }
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
if "compare_query" not in st.session_state: st.session_state.compare_query = ""
if "lopa_result" not in st.session_state: st.session_state.lopa_result = None
if "pid_hazop_matrix" not in st.session_state: st.session_state.pid_hazop_matrix = []
if "current_node_name" not in st.session_state: st.session_state.current_node_name = "Nó Global"
if "current_case_name" not in st.session_state: st.session_state.current_case_name = ""
if "current_case_notes" not in st.session_state: st.session_state.current_case_notes = ""
if "moc_result" not in st.session_state: st.session_state.moc_result = None
if "pssr_result" not in st.session_state: st.session_state.pssr_result = None
if "reactivity_result" not in st.session_state: st.session_state.reactivity_result = None

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
    lang = st.radio("🌐 Idioma", ["pt", "en"], horizontal=True, label_visibility="collapsed")
    st.session_state.lang = lang
    
    st.markdown("## ⚗️ ChemSafe Pro")
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
    manual_query = st.text_input("Buscar CAS ou Nome")
    if st.button("Carregar Composto", width="stretch") and manual_query.strip():
        st.session_state.profile = build_compound_profile(manual_query.strip())

if st.session_state.profile is None:
    load_profile_from_key(st.session_state.selected_compound_key)
profile = st.session_state.profile

# BREADCRUMB DE CONTEXTO (UI Vale do Silício)
st.markdown(f"""
<div class="context-header">
    <div>🧪 Ativo: <span>{profile.identity.get('name', 'N/A')} (CAS: {profile.identity.get('cas', 'N/A')})</span></div>
    <div>🏭 Topologia: <span>{st.session_state.current_node_name}</span></div>
</div>
""", unsafe_allow_html=True)

# Geração de Dashboards Globais
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
            st.success("Relatório Gerado!")
        if st.session_state.get("report_bundle"):
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
                save_case(case_name, profile, case_notes, st.session_state.get("lopa_result"), st.session_state.get("selected_ipl_names", []), bowtie_payload(), st.session_state.get("moc_result"), st.session_state.get("pssr_result"), st.session_state.get("reactivity_result"))
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
    tabs = st.tabs(["Propriedades Físico-Químicas", "Reatividade e Misturas", "📚 Lições Históricas", "🧮 Dimensionamento PSV (API 520)"])
    prop_tab, react_tab, hist_tab, psv_tab = tabs
    
    with prop_tab:
        dispersion_mode = classify_dispersion_mode(profile)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(metric_card("Composto", profile.identity.get("name", "—")), unsafe_allow_html=True)
        c2.markdown(metric_card("CAS", profile.identity.get("cas", "—")), unsafe_allow_html=True)
        c3.markdown(metric_card("Confiança do Pacote", f"{profile.confidence_score:.0f}/100"), unsafe_allow_html=True)
        c4.markdown(metric_card("Dispersão", dispersion_mode["label"]), unsafe_allow_html=True)
        
        st.markdown("<div class='panel'><h3>⚖️ Enquadramento Regulatório (OSHA PSM / NR-20)</h3></div>", unsafe_allow_html=True)
        inv_kg = st.number_input("Massa Armazenada na Planta (kg)", min_value=0.0, value=5000.0, step=500.0)
        for alert in check_regulatory_framework(profile, inv_kg):
            if "Isento" in alert: st.success(alert)
            else: st.warning(alert)
            
        left, right = st.columns(2)
        with left:
            st.markdown("<div class='panel'><h3>Identidade e Descritores</h3></div>", unsafe_allow_html=True)
            st.dataframe(format_identity_df(profile), use_container_width=True, hide_index=True)
            st.markdown("<div class='panel'><h3>Perigos / GHS</h3></div>", unsafe_allow_html=True)
            for hz in profile.hazards: st.error(hz)
        with right:
            st.markdown("<div class='panel'><h3>Físico-Química e Termodinâmica</h3></div>", unsafe_allow_html=True)
            st.dataframe(format_physchem_df(profile), use_container_width=True, hide_index=True)
            st.markdown("<div class='panel'><h3>Limites de Exposição Toleráveis</h3></div>", unsafe_allow_html=True)
            st.dataframe(format_limits_df(profile), use_container_width=True, hide_index=True)

    with react_tab:
        st.markdown("<div class='panel'><h3>Reactivity Lab — Matriz de Substâncias</h3></div>", unsafe_allow_html=True)
        c1, c2 = st.columns([3, 1])
        with c1: partner_query = st.text_input("Composto para avaliar mistura com o atual", key="react_query")
        with c2:
            if st.button("Avaliar Mistura", type="primary", width="stretch") and partner_query:
                partner_profile = build_compound_profile(partner_query)
                st.session_state.reactivity_result = evaluate_pairwise_reactivity(profile, partner_profile)
        res = st.session_state.get("reactivity_result")
        if res:
            summary = res["summary"]
            a, b, c = st.columns(3)
            a.markdown(metric_card("Composto A", summary["compound_a"]), unsafe_allow_html=True)
            b.markdown(metric_card("Composto B", summary["compound_b"]), unsafe_allow_html=True)
            c.markdown(metric_card("Severidade", summary["severity"], "risk-red" if summary["severity"] != "OK" else "risk-green"), unsafe_allow_html=True)
            st.dataframe(res["hits_df"], use_container_width=True, hide_index=True)

    with hist_tab:
        st.markdown("<div class='panel'><h3>📚 Banco de Lições Históricas</h3></div>", unsafe_allow_html=True)
        st.markdown("<div class='note-card'>Base curada de acidentes da indústria selecionados pelos perigos do composto atual.</div>", unsafe_allow_html=True)
        relevant_cases = get_relevant_historical_cases(profile)
        if not relevant_cases:
            st.info("Nenhum evento histórico correlato encontrado.")
        else:
            for case in relevant_cases:
                st.markdown(f"<div class='history-card'>", unsafe_allow_html=True)
                st.subheader(f"{case['evento']} ({case['ano']}) - {case['local']}")
                st.caption(f"**Match:** {case['relevancia']} | **Fonte:** {case['fonte']}")
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Substância:** {case['substancia_principal']}")
                    st.write(f"**Mecanismo:** {case['mecanismo']}")
                with c2:
                    st.error(f"**Consequências:** {case['consequencias']}")
                st.success("**Lições Aprendidas:**")
                for l in case["licoes_aprendidas"]: st.markdown(f"- {l}")
                st.markdown("</div>", unsafe_allow_html=True)

    with psv_tab:
        st.markdown("<div class='panel'><h3>🧮 Dimensionamento de Válvula de Segurança (PSV)</h3></div>", unsafe_allow_html=True)
        st.markdown("<div class='note-card'><b>Norma: API STD 520 Parte I.</b> O motor puxa automaticamente o peso molecular do composto ativo.</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: w_req = st.number_input("Vazão de Alívio (kg/h)", value=15000.0)
        with c2: p_rel = st.number_input("Pressão de Alívio (kPag)", value=1000.0)
        with c3: t_rel = st.number_input("Temperatura de Alívio (°C)", value=80.0)
        if st.button("Dimensionar Orifício API", type="primary"):
            mw = float(profile.identity.get("molecular_weight", 28.0) or 28.0)
            psv_res = size_psv_gas(W_kg_h=w_req, T_C=t_rel, P1_kPag=p_rel, Z=1.0, MW=mw)
            st.success(f"**Orifício Recomendado (API):** Letra {psv_res['api_letter']} ({psv_res['api_area_mm2']} mm²)")
            st.write(f"Área Mínima Calculada: {psv_res['calculated_area_mm2']:.2f} mm²")
            st.caption(f"Ref: {psv_res['references']} | {psv_res['formula']}")

# ==============================================================================
# MÓDULO 3: ANÁLISE DE RISCO
# ==============================================================================
elif selected_module == t("module_risk", lang):
    tabs = st.tabs(["🏗️ P&ID Builder", "HAZOP & C&E", "🛡️ LOPA & HRA", "🌪️ Dominó & F&G"])
    pid_tab, hazop_tab, lopa_tab, cons_tab = tabs

    # ABA 1: CONSTRUTOR P&ID
    with pid_tab:
        st.markdown("<div class='panel'><h3>🏗️ Topologia do P&ID</h3></div>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["📝 Construtor Manual", "📊 Importação em Lote (CSV)"])
        
        with t1:
            st.markdown("<div class='note-card'>Selecione os equipamentos presentes no Nó do P&ID. O motor termodinâmico fará o resto.</div>", unsafe_allow_html=True)
            col1, col2 = st.columns([1, 2])
            with col1:
                st.session_state.current_node_name = st.text_input("Nome do Nó", value=st.session_state.current_node_name)
            with col2:
                selected_equipment = st.multiselect("Equipamentos do Nó", options=list(EQUIPMENT_PARAMETERS.keys()), default=["Tanque de Armazenamento Atmosférico", "Bomba Centrífuga"])
            if st.button("🚀 Gerar Matrizes de Segurança", type="primary"):
                st.session_state.pid_hazop_matrix = generate_hazop_from_topology(st.session_state.current_node_name, selected_equipment, profile)
                st.success("Matrizes geradas e vinculadas! Avance para a aba HAZOP & C&E.")
                
        with t2:
            st.markdown("<div class='note-card'>Exporte a <b>Equipment List</b> do seu CAD (2 colunas: Nó, Equipamento) para processar a planta inteira de uma vez.</div>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader("Carregue o CSV/Excel", type=["csv", "xlsx"])
            if uploaded_file is not None:
                try:
                    df_bulk = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                    if st.button("⚡ Processar Lote", type="primary"):
                        bulk_results = process_bulk_pid_nodes(df_bulk, profile)
                        if bulk_results:
                            st.session_state.pid_hazop_matrix = bulk_results
                            st.success(f"Sucesso! {len(bulk_results)} cenários gerados.")
                except Exception as e:
                    st.error(f"Erro: {e}")

    # ABA 2: HAZOP E CAUSA E EFEITO
    with hazop_tab:
        st.markdown("<div class='panel'><h3>Análise de Perigos e Matriz de Automação</h3></div>", unsafe_allow_html=True)
        if st.session_state.get("pid_hazop_matrix"):
            with st.expander("📋 Tabela HAZOP Gerada Automática (IEC 61882)", expanded=True):
                df_hazop = pd.DataFrame(st.session_state.pid_hazop_matrix)
                st.dataframe(df_hazop, use_container_width=True, hide_index=True)
                st.download_button("📥 Baixar HAZOP (CSV)", df_hazop.to_csv(index=False).encode('utf-8'), "hazop_export.csv", "text/csv")
            
            with st.expander("🔀 Matriz Causa e Efeito (IEC 61511 / API RP 14C)", expanded=False):
                df_ce = generate_ce_matrix_from_hazop(st.session_state.pid_hazop_matrix)
                if not df_ce.empty:
                    st.dataframe(df_ce, use_container_width=True, hide_index=True)
                    st.download_button("📥 Baixar C&E (CSV)", df_ce.to_csv(index=False).encode('utf-8'), "ce_matrix.csv", "text/csv")
                else:
                    st.info("Nenhum intertravamento (SIS/Trip) detectado no HAZOP.")
        else:
            st.warning("Configure o Nó no P&ID Builder primeiro para liberar as matrizes.")

    # ABA 3: LOPA & HRA
    with lopa_tab:
        st.markdown("<div class='panel'><h3>🛡️ Análise de Camadas de Proteção e Confiabilidade</h3></div>", unsafe_allow_html=True)
        c_hra, c_lopa = st.columns(2)
        
        with c_hra:
            st.markdown("#### 🧠 Avaliação de Erro Humano (HRA)")
            st.markdown("<div class='note-card'>Calcula a Probabilidade de Erro Humano (HEP) com base no método THERP (NUREG/CR-1278).</div>", unsafe_allow_html=True)
            t_av = st.selectbox("Tempo Disponível", ["Menos de 5 minutos", "5 a 10 minutos", "10 a 30 minutos", "Mais de 30 minutos"])
            stress = st.selectbox("Nível de Estresse", ["Extremo (Emergência Crítica)", "Alto (Alarme de Alta Prioridade)", "Nominal (Operação Normal)"])
            comp = st.selectbox("Complexidade da Ação", ["Alta (Múltiplas válvulas/painéis)", "Média (Ação em painel único)", "Baixa (Pressionar botão de emergência)"])
            
            if st.button("Calcular PFD do Operador"):
                hra_res = calculate_human_error_probability(t_av, stress, comp)
                st.success(f"**Probabilidade de Falha (HEP):** {hra_res['hep']:.2%} ({hra_res['pfd_equivalent']})")
                st.caption(f"Ref: {hra_res['references']}")
                
        with c_lopa:
            st.markdown("#### 📊 LOPA (Layer of Protection Analysis)")
            f_ie = st.number_input("Frequência do Evento Iniciador (1/ano)", value=0.1, format="%.3f")
            selected_ipls = st.multiselect("Selecione IPLs na Arquitetura", [f"{n} (PFD={p})" for n, p in IPL_CATALOG])
            if st.button("Calcular Gap de Risco", type="primary"):
                chosen = [(n, p) for lbl in selected_ipls for n, p in IPL_CATALOG if n in lbl]
                st.session_state.lopa_result = compute_lopa(f_ie, 1e-4, chosen)
                res = st.session_state.lopa_result
                st.info(f"Frequência Mitigada Final (MCF): **{res['mcf']:.2e} /ano**")
                st.markdown(metric_card("Requisito de Malha (SIL)", res["sil"], "risk-amber"), unsafe_allow_html=True)

    # ABA 4: DOMINÓ & DISPERSÃO
    with cons_tab:
        st.markdown("<div class='panel'><h3>🌪️ Consequências Espaciais (Facility Siting)</h3></div>", unsafe_allow_html=True)
        
        with st.expander("🔥 Efeito Dominó (API 521 / Point Source Model)", expanded=True):
            st.markdown("<div class='note-card'>Avalia a propagação de radiação para equipamentos adjacentes.</div>", unsafe_allow_html=True)
            d1, d2, d3 = st.columns(3)
            with d1: dist = st.number_input("Distância ao Alvo (m)", value=15.0)
            with d2: m_rate = st.number_input("Taxa de Queima (kg/s)", value=10.0)
            with d3: hc = st.number_input("Calor de Combustão (MJ/kg)", value=44.0)
            
            if st.button("Calcular Radiação Térmica"):
                domino = calculate_domino_effect(dist, m_rate, hc * 1e6)
                st.error(f"**{domino['status']}** | Radiação: {domino['q_kW_m2']:.2f} kW/m²")
                st.caption(f"Impacto: {domino['impact']} | Ref: {domino['references']}")
                
        with st.expander("📡 Mapeamento ISA TR84 (Fire & Gas Mapping)", expanded=False):
            st.markdown("<div class='note-card'>Posicionamento estratégico de sensores baseado na dispersão LFL.</div>", unsafe_allow_html=True)
            if st.button("Gerar Recomendações F&G"):
                lfl = float(profile.limit("LEL_vol", 5.0))
                st.success(f"**Ativo Inflamável Detectado.** Limite Inferior (LEL/LFL) = {lfl}% vol.")
                st.write("- **Sensor 1 (Early Warning):** Instalar a 1/3 da distância teórica da pluma (Alarme setado para 10% do LEL).")
                st.write("- **Sensor 2 (Ação Executiva):** Instalar a 2/3 da distância (Trip setado para 25% do LEL, intertravado com SDV).")

        with st.expander("🌍 Mapa de Impacto Georreferenciado", expanded=False):
            c1, c2 = st.columns(2)
            with c1: lat = st.number_input("Latitude", value=-22.8188, format="%.6f")
            with c2: lon = st.number_input("Longitude", value=-47.0635, format="%.6f")
            render_map_in_streamlit(lat=lat, lon=lon, dispersion_data=st.session_state.get("dispersion_result"), thermal_data=st.session_state.get("pool_fire_result"))

# ==============================================================================
# MÓDULO 4: GESTÃO DE MUDANÇA
# ==============================================================================
elif selected_module == t("module_change", lang):
    tabs = st.tabs(["PSI / PSM", "MOC (Gestão de Mudanças)", "PSSR (Pré-Startup)"])
    psi_tab, moc_tab, pssr_tab = tabs

    with psi_tab:
        st.markdown("<div class='panel'><h3>Checklist de Prontidão PSI/PSM</h3></div>", unsafe_allow_html=True)
        st.dataframe(build_psi_readiness_df(profile, st.session_state.get("lopa_result"), bowtie_payload()), use_container_width=True, hide_index=True)

    with moc_tab:
        st.markdown("<div class='panel'><h3>Avaliação de Impacto de Mudança (MOC)</h3></div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            change_type = st.selectbox("Tipo de Mudança", ["Mudança química / novo composto", "Mudança de condição operacional", "Mudança de equipamento", "Mudança de procedimento"])
            impacts = st.multiselect("Impactos", ["Química / composição", "Pressão", "Temperatura", "Inventário", "Alívio / PSV", "Instrumentação / controle"])
            desc = st.text_area("Descrição da Mudança")
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
            st.dataframe(pd.DataFrame(res["checklist_rows"]), use_container_width=True, hide_index=True)

    with pssr_tab:
        st.markdown("<div class='panel'><h3>Revisão de Segurança Pré-Partida (PSSR)</h3></div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            d1 = st.checkbox("Equipamento inspecionado e conforme P&ID")
            d2 = st.checkbox("Procedimentos operacionais atualizados")
            d3 = st.checkbox("Treinamento de operadores concluído")
        with c2:
            d4 = st.checkbox("PSV e sistemas de alívio verificados")
            d5 = st.checkbox("Malhas de intertravamento e alarmes testados")
            d6 = st.checkbox("Autorização gerencial assinada")
            
        if st.button("Calcular Prontidão PSSR", type="primary"):
            st.session_state.pssr_result = evaluate_pssr(design_ok=d1, procedures_ok=d2, training_ok=d3, relief_verified=d4, alarms_tested=d5, startup_authorized=d6, pha_or_moc_ok=True, mi_ready=True, emergency_ready=True, scope_label="PSSR")
        res = st.session_state.get("pssr_result")
        if res:
            st.markdown(f"<br><b>Status Final:</b> {res['summary']['readiness']} | <b>Score:</b> {res['summary']['score']}/100", unsafe_allow_html=True)
            for block in res["blockers"]:
                st.error(block)
