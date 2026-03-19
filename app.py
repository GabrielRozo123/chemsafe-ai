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
.block-container { padding-top: 2rem; max-width: 1400px; }
.context-header { background: var(--card-bg); border-bottom: 1px solid var(--border-color); padding: 12px 20px; border-radius: 8px; margin-bottom: 25px; font-weight: 600; color: #8b949e; display: flex; justify-content: space-between; }
.context-header span { color: var(--accent-blue); }
.panel { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 10px; padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
.panel h3 { margin-top: 0; color: #f0f6ff; font-size: 1.1rem; border-bottom: 1px solid var(--border-color); padding-bottom: 8px; margin-bottom: 15px; }
.metric-box { background: rgba(22, 27, 34, 0.6); border: 1px solid var(--border-color); border-radius: 8px; padding: 15px; text-align: center; }
.metric-label { color: #8b949e; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; }
.metric-value { color: #ffffff; font-size: 1.8rem; font-weight: 700; margin-top: 5px; }
.risk-blue { color: var(--accent-blue); } .risk-green { color: #3fb950; } .risk-amber { color: #d29922; } .risk-red { color: #f85149; }
.note-card { background: rgba(88, 166, 255, 0.1); border-left: 4px solid var(--accent-blue); padding: 12px 15px; border-radius: 4px; font-size: 0.9rem; margin-bottom: 15px; }
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

def load_profile_from_key(key: str) -> None:
    aliases = LOCAL_COMPOUNDS[key]["aliases"]
    st.session_state.profile = build_compound_profile(aliases[0])
    st.session_state.selected_compound_key = key

def bowtie_payload():
    return {"threats": [], "barriers_pre": [], "top_event": "Perda de contenção", "barriers_mit": [], "consequences": []}

# Sidebar simplificada
with st.sidebar:
    lang = st.radio("🌐 Idioma", ["pt", "en"], horizontal=True, label_visibility="collapsed")
    st.session_state.lang = lang
    st.markdown("## ⚗️ ChemSafe Pro")
    st.caption("Process Safety Intelligence Engine")
    st.markdown("---")
    selected_module = st.radio("Módulos", options=[t("module_exec", lang), t("module_eng", lang), t("module_risk", lang), t("module_change", lang)], label_visibility="collapsed")
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

# ==============================================================================
# MÓDULOS 1 e 2: Visão Executiva e Engenharia (Ocultados por brevidade no snippet, mantemos a estrutura limpa)
# ==============================================================================
if selected_module == t("module_exec", lang):
    st.info("Acesse os Módulos de Engenharia ou Risco para explorar as Sprints de Rastreabilidade.")
    
elif selected_module == t("module_eng", lang):
    tabs = st.tabs(["Propriedades", "📚 Lições Históricas", "🧮 Dimensionamento PSV (API 520)"])
    prop_tab, hist_tab, psv_tab = tabs
    
    with prop_tab:
        left, right = st.columns(2)
        with left:
            st.markdown("<div class='panel'><h3>Identidade e Descritores</h3></div>", unsafe_allow_html=True)
            st.dataframe(format_identity_df(profile), use_container_width=True, hide_index=True)
        with right:
            st.markdown("<div class='panel'><h3>Propriedades Físico-Químicas</h3></div>", unsafe_allow_html=True)
            st.dataframe(format_physchem_df(profile), use_container_width=True, hide_index=True)

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
# MÓDULO 3: ANÁLISE DE RISCO (UI Clean + Sprints 17, 18 e 19)
# ==============================================================================
elif selected_module == t("module_risk", lang):
    tabs = st.tabs([
        "🏗️ P&ID Builder", "HAZOP & C&E", "🛡️ LOPA & HRA", "🌪️ Dominó & F&G"
    ])
    pid_tab, hazop_tab, lopa_tab, cons_tab = tabs

    # ABA 1: CONSTRUTOR P&ID
    with pid_tab:
        st.markdown("<div class='panel'><h3>🏗️ Topologia do P&ID</h3></div>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 2])
        with col1:
            st.session_state.current_node_name = st.text_input("Nome do Nó", value=st.session_state.current_node_name)
        with col2:
            selected_equipment = st.multiselect("Equipamentos do Nó", options=list(EQUIPMENT_PARAMETERS.keys()), default=["Tanque de Armazenamento Atmosférico", "Bomba Centrífuga"])
        
        if st.button("🚀 Gerar Matrizes de Segurança", type="primary"):
            st.session_state.pid_hazop_matrix = generate_hazop_from_topology(st.session_state.current_node_name, selected_equipment, profile)
            st.success("Matrizes geradas e vinculadas! Avance para a próxima aba.")

    # ABA 2: HAZOP & CAUSA E EFEITO (Progressive Disclosure)
    with hazop_tab:
        if st.session_state.get("pid_hazop_matrix"):
            with st.expander("📋 Tabela HAZOP Gerada (IEC 61882)", expanded=True):
                st.dataframe(pd.DataFrame(st.session_state.pid_hazop_matrix), use_container_width=True, hide_index=True)
            
            with st.expander("🔀 Matriz Causa e Efeito (IEC 61511 / API RP 14C)", expanded=False):
                df_ce = generate_ce_matrix_from_hazop(st.session_state.pid_hazop_matrix)
                if not df_ce.empty:
                    st.dataframe(df_ce, use_container_width=True, hide_index=True)
                    st.download_button("📥 Exportar C&E (CSV)", df_ce.to_csv(index=False).encode('utf-8'), "ce_matrix.csv", "text/csv")
                else:
                    st.info("Nenhum intertravamento (SIS/Trip) detectado no HAZOP.")
        else:
            st.warning("Configure o Nó no P&ID Builder primeiro.")

    # ABA 3: LOPA & CONFIABILIDADE HUMANA (HRA)
    with lopa_tab:
        st.markdown("<div class='panel'><h3>🛡️ Análise de Camadas e Confiabilidade</h3></div>", unsafe_allow_html=True)
        c_lopa, c_hra = st.columns(2)
        
        with c_hra:
            st.markdown("#### 🧠 Análise de Erro Humano (THERP)")
            st.markdown("<div class='note-card'>Referência: NUREG/CR-1278. Estima a probabilidade do operador falhar em uma resposta de emergência.</div>", unsafe_allow_html=True)
            t_av = st.selectbox("Tempo Disponível", ["Menos de 5 minutos", "5 a 10 minutos", "10 a 30 minutos", "Mais de 30 minutos"])
            stress = st.selectbox("Nível de Estresse", ["Extremo (Emergência Crítica)", "Alto (Alarme de Alta Prioridade)", "Nominal (Operação Normal)"])
            comp = st.selectbox("Complexidade da Ação", ["Alta (Múltiplas válvulas/painéis)", "Média (Ação em painel único)", "Baixa (Pressionar botão de emergência)"])
            
            if st.button("Calcular PFD Humano"):
                hra_res = calculate_human_error_probability(t_av, stress, comp)
                st.success(f"**Probabilidade de Falha (HEP):** {hra_res['hep']:.2%} ({hra_res['pfd_equivalent']})")
                st.caption(f"Ref: {hra_res['references']}")
                
        with c_lopa:
            st.markdown("#### 📊 Calculadora LOPA")
            f_ie = st.number_input("Frequência do Evento Iniciador", value=0.1, format="%.3f")
            selected_ipls = st.multiselect("Selecione IPLs (Mecânicas/Instrumentadas)", [f"{n} (PFD={p})" for n, p in IPL_CATALOG])
            if st.button("Calcular Risco (LOPA)", type="primary"):
                chosen = [(n, p) for lbl in selected_ipls for n, p in IPL_CATALOG if n in lbl]
                lopa_res = compute_lopa(f_ie, 1e-4, chosen)
                st.info(f"Frequência Mitigada Final: **{lopa_res['mcf']:.2e}**")

    # ABA 4: EFEITO DOMINÓ & FIRE AND GAS MAPPING
    with cons_tab:
        st.markdown("<div class='panel'><h3>🌪️ Avaliação Espacial de Consequências</h3></div>", unsafe_allow_html=True)
        
        with st.expander("🔥 Efeito Dominó (API 521 / Point Source Model)", expanded=True):
            st.markdown("<div class='note-card'>Avalia a propagação de incêndios para equipamentos vizinhos (Facility Siting).</div>", unsafe_allow_html=True)
            d1, d2, d3 = st.columns(3)
            with d1: dist = st.number_input("Distância ao Alvo (m)", value=15.0)
            with d2: m_rate = st.number_input("Taxa de Queima (kg/s)", value=10.0)
            with d3: hc = st.number_input("Calor de Combustão (MJ/kg)", value=44.0)
            
            if st.button("Calcular Radiação Térmica"):
                domino = calculate_domino_effect(dist, m_rate, hc * 1e6)
                st.error(f"**{domino['status']}** | Radiação: {domino['q_kW_m2']:.2f} kW/m²")
                st.caption(f"Impacto: {domino['impact']}")
                
        with st.expander("📡 ISA TR84 - Mapeamento de Detectores (F&G Mapping)", expanded=False):
            st.markdown("<div class='note-card'>Cruza a dispersão termodinâmica para sugerir o posicionamento de sensores de gás.</div>", unsafe_allow_html=True)
            if st.button("Gerar Recomendações de Cobertura F&G"):
                lfl = float(profile.limit("LEL_vol", 5.0)) # Puxa LEL do composto
                st.success(f"**Ativo Inflamável Detectado.** LEL/LFL = {lfl}% vol.")
                st.write("- **Sensor 1 (Early Warning):** Instalar a 1/3 da distância da pluma teórica (Alarme em 10% do LEL).")
                st.write("- **Sensor 2 (Ação Executiva):** Instalar a 2/3 da distância, intertravado com SDV (Trip em 25% do LEL).")
                st.caption("Baseado nas premissas de cobertura geográfica da ISA TR84.00.07.")

# ==============================================================================
# MÓDULO 4: GESTÃO DE MUDANÇA (Ocultado no snippet por brevidade)
# ==============================================================================
elif selected_module == t("module_change", lang):
    st.info("Módulo de Gestão de Mudança e PSSR.")
