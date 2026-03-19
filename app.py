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
import graphviz # NOVO: Para desenhar os P&IDs visualmente

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

# MÓDULOS SPRINT 11 A 19
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
from hra_engine import calculate_human_error_probability
from psv_engine import size_psv_gas

# MÓDULOS SPRINT 20
from ml_reliability_engine import calculate_dynamic_pfd
from runaway_engine import calculate_tmr_adiabatic

# NOVO CSS: Ultra Moderno / Data-Driven (Inspiração Vale do Silício)
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
if "lopa_result" not in st.session_state: st.session_state.lopa_result = None
if "pid_hazop_matrix" not in st.session_state: st.session_state.pid_hazop_matrix = []
if "current_node_name" not in st.session_state: st.session_state.current_node_name = "Nó 101: Bomba de Recalque"

def metric_card(label: str, value: str, klass: str = "risk-blue") -> str:
    return f"<div class='metric-box'><div class='metric-label'>{label}</div><div class='metric-value {klass}'>{value}</div></div>"

def load_profile_from_key(key: str) -> None:
    aliases = LOCAL_COMPOUNDS[key]["aliases"]
    st.session_state.profile = build_compound_profile(aliases[0])
    st.session_state.selected_compound_key = key

def bowtie_payload():
    return {"threats": [], "barriers_pre": [], "top_event": "Perda de contenção", "barriers_mit": [], "consequences": []}

# Sidebar Modernizada
with st.sidebar:
    st.markdown("## ⚗️ ChemSafe Pro\n**Enterprise Edition**")
    st.markdown("---")
    selected_module = st.radio("Módulos Corporativos", options=["Visão Executiva (CRI)", "Engenharia de Dados", "Análise de Risco (PHA)", "Gestão de Mudança"], label_visibility="collapsed")
    st.markdown("---")
    st.write("**Ativos Rápidos**")
    for key, data in LOCAL_COMPOUNDS.items():
        if st.button(data["identity"]["name"], key=f"quick_{key}", width="stretch"):
            load_profile_from_key(key)
    st.markdown("---")
    manual_query = st.text_input("Buscar CAS na Base Global")
    if st.button("Sincronizar", width="stretch") and manual_query.strip():
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
cri_data = calculate_case_readiness_index(profile, summarize_psi_readiness(psi_df_dash), None, None, st.session_state.get("lopa_result"), None)
action_df_dash = build_consolidated_action_plan(profile, psi_df_dash, None, None, None)

# ==============================================================================
# MÓDULO 1: VISÃO EXECUTIVA
# ==============================================================================
if selected_module == "Visão Executiva (CRI)":
    st.markdown("<div class='panel'><h3>Painel de Prontidão do Caso (CRI)</h3></div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(metric_card("Índice de Prontidão", f"{cri_data['index']}%", cri_data['color_class']), unsafe_allow_html=True)
    c2.markdown(metric_card("Status Atual", cri_data['band'], cri_data['color_class']), unsafe_allow_html=True)
    c3.markdown(metric_card("Ações Pendentes", str(len(action_df_dash)), "risk-amber" if len(action_df_dash) > 0 else "risk-green"), unsafe_allow_html=True)
    c4.markdown(metric_card("Revisões de Risco", "OK", "risk-green"), unsafe_allow_html=True)
    
    left, right = st.columns(2)
    with left:
        st.markdown("<div class='panel'><h3>Matriz de Maturidade</h3></div>", unsafe_allow_html=True)
        st.pyplot(build_readiness_gauge_figure(cri_data), clear_figure=True)
    with right:
        st.markdown("<div class='panel'><h3>Distribuição por Pilares</h3></div>", unsafe_allow_html=True)
        st.pyplot(build_components_figure(cri_data), clear_figure=True)

# ==============================================================================
# MÓDULO 2: ENGENHARIA DE DADOS (Com Runaway e PSV)
# ==============================================================================
elif selected_module == "Engenharia de Dados":
    tabs = st.tabs(["Físico-Química", "🔥 Cinética / Runaway", "🧮 Dimensionamento PSV", "📚 Lições Históricas"])
    prop_tab, run_tab, psv_tab, hist_tab = tabs
    
    with prop_tab:
        dispersion_mode = classify_dispersion_mode(profile)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(metric_card("Composto", profile.identity.get("name", "—")), unsafe_allow_html=True)
        c2.markdown(metric_card("Peso Molar", f"{profile.identity.get('molecular_weight', '—')} g/mol"), unsafe_allow_html=True)
        c3.markdown(metric_card("Dispersão", dispersion_mode["label"]), unsafe_allow_html=True)
        c4.markdown(metric_card("Confiança do Dado", f"{profile.confidence_score:.0f}%"), unsafe_allow_html=True)
        
        left, right = st.columns(2)
        with left:
            st.markdown("<div class='panel'><h3>Propriedades e Descritores</h3></div>", unsafe_allow_html=True)
            st.dataframe(format_identity_df(profile), use_container_width=True, hide_index=True)
        with right:
            st.markdown("<div class='panel'><h3>Termodinâmica Básica</h3></div>", unsafe_allow_html=True)
            st.dataframe(format_physchem_df(profile), use_container_width=True, hide_index=True)

    with run_tab:
        st.markdown("<div class='panel'><h3>🔥 Simulação de Runaway Térmico (Semenov)</h3></div>", unsafe_allow_html=True)
        st.markdown("<div class='note-card'><b>Norma: CCPS Reactive Materials.</b> Estima o TMR (Time to Maximum Rate) em condições adiabáticas. Ideal para preencher o tempo de resposta em cenários de HAZOP de reatores.</div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            t0 = st.number_input("Temp. Inicial do Reator (°C)", value=80.0)
            ea = st.number_input("Energia de Ativação (kJ/mol)", value=100.0)
        with col2:
            dh = st.number_input("Calor de Reação - ΔHr (kJ/kg)", value=1500.0)
            cp = st.number_input("Calor Específico - Cp (kJ/kg.K)", value=2.5)
        with col3:
            a_s = st.number_input("Fator Pré-Exponencial (1/s)", value=1e12, format="%.1e")
            
        if st.button("⚡ Simular TMR Adiabático", type="primary"):
            tmr_res = calculate_tmr_adiabatic(t0, ea, a_s, dh, cp)
            st.markdown(f"### Tempo até Explosão Térmica (TMR): **{tmr_res['tmr_min']:.1f} minutos**")
            st.markdown(metric_card("Status de Intervenção", tmr_res['status'], f"risk-{tmr_res['color']}"), unsafe_allow_html=True)
            st.caption(f"Referência: {tmr_res['references']} | Equação: {tmr_res['formula']}")

    with psv_tab:
        st.markdown("<div class='panel'><h3>🧮 Dimensionamento API 520 (Válvula de Segurança)</h3></div>", unsafe_allow_html=True)
        st.markdown("<div class='note-card'>A massa molar é extraída automaticamente da base de dados do composto atual.</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: w_req = st.number_input("Vazão de Alívio (kg/h)", value=10000.0)
        with c2: p_rel = st.number_input("Pressão de Alívio (kPag)", value=500.0)
        with c3: t_rel = st.number_input("Temperatura de Alívio (°C)", value=50.0)
        if st.button("Dimensionar Orifício API", type="primary"):
            mw = float(profile.identity.get("molecular_weight", 28.0) or 28.0)
            psv_res = size_psv_gas(W_kg_h=w_req, T_C=t_rel, P1_kPag=p_rel, Z=1.0, MW=mw)
            st.success(f"**Orifício Recomendado (API STD 520):** Letra {psv_res['api_letter']} ({psv_res['api_area_mm2']} mm²)")
            st.write(f"Área Mínima Calculada Exata: {psv_res['calculated_area_mm2']:.2f} mm²")

    with hist_tab:
        st.markdown("<div class='panel'><h3>📚 Lições Históricas de Engenharia</h3></div>", unsafe_allow_html=True)
        for case in get_relevant_historical_cases(profile)[:2]:
            st.markdown(f"<div class='history-card'><b>{case['evento']}</b><br>Mecanismo: {case['mecanismo']}</div>", unsafe_allow_html=True)

# ==============================================================================
# MÓDULO 3: ANÁLISE DE RISCO (Com Visual de Grafos e ML OREDA)
# ==============================================================================
elif selected_module == "Análise de Risco (PHA)":
    tabs = st.tabs(["🏗️ P&ID Visual Builder", "📋 HAZOP & C&E", "🛡️ ML-LOPA", "🌪️ F&G e Siting"])
    pid_tab, hazop_tab, lopa_tab, cons_tab = tabs

    # ABA 1: CONSTRUTOR P&ID VISUAL (ESTILO REACT FLOW)
    with pid_tab:
        st.markdown("<div class='panel'><h3>🏗️ Construtor Visual de Topologia</h3></div>", unsafe_allow_html=True)
        st.markdown("<div class='note-card'>Selecione os equipamentos. O sistema desenhará o grafo de fluxo automaticamente e gerará os cenários termodinâmicos do HAZOP.</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.session_state.current_node_name = st.text_input("Identificação do Nó", value=st.session_state.current_node_name)
        with col2:
            selected_equipment = st.multiselect("Selecione na ordem do fluxo", options=list(EQUIPMENT_PARAMETERS.keys()), default=["Tanque de Armazenamento Atmosférico", "Tubulação / Linha de Transferência", "Bomba Centrífuga"])
            
        if selected_equipment:
            # DESENHANDO O GRAFO (P&ID Flow)
            dot = graphviz.Digraph()
            dot.attr(rankdir='LR', bgcolor='transparent')
            dot.attr('node', shape='box', style='filled', fillcolor='#1e293b', color='#3b82f6', fontcolor='white', fontname='Helvetica', penwidth='2')
            dot.attr('edge', color='#9ca3af', penwidth='2')
            
            for i, eq in enumerate(selected_equipment):
                dot.node(str(i), eq)
                if i > 0:
                    dot.edge(str(i-1), str(i))
                    
            st.graphviz_chart(dot, use_container_width=True)

        if st.button("🚀 Consolidar Topologia e Gerar HAZOP", type="primary"):
            st.session_state.pid_hazop_matrix = generate_hazop_from_topology(st.session_state.current_node_name, selected_equipment, profile)
            st.success("Matrizes geradas via Inteligência Determinística! Avance de aba.")

    # ABA 2: HAZOP E MATRIZ C&E
    with hazop_tab:
        if st.session_state.get("pid_hazop_matrix"):
            st.markdown("<div class='panel'><h3>📋 Tabela HAZOP (IEC 61882)</h3></div>", unsafe_allow_html=True)
            df_hazop = pd.DataFrame(st.session_state.pid_hazop_matrix)
            st.dataframe(df_hazop, use_container_width=True, hide_index=True)
            
            with st.expander("🔀 Ver Matriz Causa e Efeito (IEC 61511)", expanded=False):
                df_ce = generate_ce_matrix_from_hazop(st.session_state.pid_hazop_matrix)
                if not df_ce.empty:
                    st.dataframe(df_ce, use_container_width=True, hide_index=True)
                else:
                    st.info("Nenhum intertravamento detectado para gerar matriz.")
        else:
            st.warning("Construa a topologia no P&ID Builder primeiro.")

    # ABA 3: LOPA DINÂMICO E PREDITIVO (ML / OREDA)
    with lopa_tab:
        st.markdown("<div class='panel'><h3>🛡️ LOPA Preditivo e Dinâmico</h3></div>", unsafe_allow_html=True)
        st.markdown("<div class='note-card'>Em vez de taxas de falha estáticas, este módulo ajusta o PFD em tempo real utilizando desgaste de Weibull (Tempo em serviço) e sinais de Machine Learning (Score de Vibração/Anomalia) baseado nos Handbooks OREDA.</div>", unsafe_allow_html=True)
        
        c_ml, c_lopa = st.columns([1, 1.5])
        
        with c_ml:
            st.markdown("#### 🤖 ML: Degradação de Barreira")
            eq_type = st.selectbox("Equipamento Analisado", ["Bomba de Resfriamento", "Válvula de Bloqueio (SDV)", "Transmissor de Nível (LIT)"])
            t_meses = st.slider("Tempo em Operação (Meses)", 1, 60, 24)
            anomaly = st.slider("Score de Anomalia Preditiva (Vibração/Ruído)", 0.0, 1.0, 0.2, help="0 = Saudável, 1.0 = Falha Iminente")
            
            base_pfd = 1e-2 if "Bomba" in eq_type else 1e-3
            dyn_res = calculate_dynamic_pfd(base_pfd, t_meses, anomaly, eq_type)
            
            st.metric(label="PFD Dinâmico Ajustado", value=dyn_res["pfd_str"], delta=f"+{dyn_res['risk_increase_pct']:.0f}% de Risco", delta_color="inverse")
            st.caption(f"Ref: {dyn_res['references']}")
            
        with c_lopa:
            st.markdown("#### 📊 Calculadora LOPA Global")
            f_ie = st.number_input("Freq. Evento Iniciador (1/ano)", value=0.1, format="%.3f")
            
            # Aqui permitimos selecionar as barreiras normais + a barreira degradada pelo ML
            opcoes_ipl = [f"{n} (PFD={p})" for n, p in IPL_CATALOG]
            opcoes_ipl.append(f"{eq_type} Degradada (PFD={dyn_res['dynamic_pfd']:.1e})")
            
            selected_ipls = st.multiselect("Selecione IPLs na Arquitetura", opcoes_ipl)
            
            if st.button("Calcular Risco Residual", type="primary"):
                # Lógica para puxar o valor numérico do multiselect string
                chosen_pfds = []
                for lbl in selected_ipls:
                    try:
                        val = float(lbl.split("PFD=")[1].replace(")", ""))
                        chosen_pfds.append(("Barreira", val))
                    except: pass
                    
                st.session_state.lopa_result = compute_lopa(f_ie, 1e-4, chosen_pfds)
                res = st.session_state.lopa_result
                st.success(f"**MCF (Frequência Mitigada):** {res['mcf']:.2e} /ano")
                st.markdown(metric_card("Requisito SIL do Gap", res["sil"], "risk-amber"), unsafe_allow_html=True)

    # ABA 4: DOMINÓ E FACILITY SITING
    with cons_tab:
        st.markdown("<div class='panel'><h3>🌪️ Engenharia Geográfica e Consequências</h3></div>", unsafe_allow_html=True)
        with st.expander("🔥 Modelo Efeito Dominó (Point Source API 521)", expanded=True):
            d1, d2, d3 = st.columns(3)
            with d1: dist = st.number_input("Distância ao Alvo (m)", value=15.0)
            with d2: m_rate = st.number_input("Taxa de Queima (kg/s)", value=10.0)
            with d3: hc = st.number_input("Calor Combustão (MJ/kg)", value=44.0)
            if st.button("Calcular Radiação"):
                domino = calculate_domino_effect(dist, m_rate, hc * 1e6)
                st.error(f"**{domino['status']}** | Radiação: {domino['q_kW_m2']:.2f} kW/m²")
                st.caption(f"Ref: {domino['references']}")

# ==============================================================================
# MÓDULO 4: GESTÃO DE MUDANÇA
# ==============================================================================
elif selected_module == "Gestão de Mudança":
    st.info("Módulos MOC e PSSR operacionais no backend.")
