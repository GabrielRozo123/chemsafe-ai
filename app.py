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
import plotly.graph_objects as go
import plotly.express as px
from streamlit_option_menu import option_menu

# Módulos de Engenharia e Risco
from bowtie_visual import build_bowtie_custom_figure
from case_store import list_cases, load_case, save_case
from chemicals_seed import LOCAL_COMPOUNDS
from compound_engine import build_compound_profile, suggest_hazop_priorities
from dense_gas_router import classify_dispersion_mode
from deterministic import IPL_CATALOG, compute_lopa, gaussian_dispersion, pool_fire
from executive_report import build_executive_bundle
from hazop_db import HAZOP_DB
from moc_engine import evaluate_moc
from psi_readiness import build_psi_readiness_df, summarize_psi_readiness
from pssr_engine import evaluate_pssr
from reactivity_engine import evaluate_pairwise_reactivity
from ui_formatters import format_identity_df, format_physchem_df, format_limits_df

# Módulos Sprints 11 a 21
from action_hub import build_consolidated_action_plan
from dashboard_engine import calculate_case_readiness_index
from i18n import t
from historical_engine import get_relevant_historical_cases
from pid_engine import EQUIPMENT_PARAMETERS, generate_hazop_from_topology, process_bulk_pid_nodes
from domino_engine import calculate_domino_effect
from ce_matrix_engine import generate_ce_matrix_from_hazop
from hra_engine import calculate_human_error_probability
from psv_engine import size_psv_gas
from ml_reliability_engine import calculate_dynamic_pfd
from runaway_engine import calculate_tmr_adiabatic

# CSS: Interface Premium e Correção de Textos Cortados
APP_CSS = """
<style>
:root { --bg-color: #0b0f19; --card-bg: #151b28; --border-color: #2a3441; --text-main: #d1d5db; --accent-blue: #3b82f6; --accent-glow: rgba(59, 130, 246, 0.15); }
.stApp { background-color: var(--bg-color); color: var(--text-main); font-family: 'Inter', -apple-system, sans-serif; }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1440px; }
.context-header { background: var(--card-bg); border: 1px solid var(--border-color); padding: 15px 25px; border-radius: 12px; margin-bottom: 30px; font-weight: 500; font-size: 0.95rem; color: #9ca3af; display: flex; justify-content: space-between; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }
.context-header span { color: #fff; font-weight: 600; }
.panel { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; padding: 1.8rem; margin-bottom: 1.2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.15); }
.panel h3 { margin-top: 0; color: #f3f4f6; font-size: 1.15rem; font-weight: 600; border-bottom: 1px solid var(--border-color); padding-bottom: 10px; margin-bottom: 20px; }

/* FIX: Garante que os valores das métricas não sejam cortados */
.metric-box { background: rgba(30, 41, 59, 0.5); border: 1px solid var(--border-color); border-radius: 10px; padding: 15px 20px; text-align: center; display: flex; flex-direction: column; justify-content: center; min-height: 135px; }
.metric-label { color: #9ca3af; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }
.metric-value { color: #f9fafb; font-size: 1.8rem; font-weight: 800; margin-top: 8px; line-height: 1.2; white-space: normal; word-wrap: break-word; }

.risk-blue { color: var(--accent-blue); } .risk-green { color: #10b981; } .risk-amber { color: #f59e0b; } .risk-red { color: #ef4444; }
.note-card { background: rgba(59, 130, 246, 0.08); border-left: 4px solid var(--accent-blue); padding: 15px; border-radius: 6px; font-size: 0.9rem; margin-bottom: 20px; color: #bfdbfe; }
.stExpander { border: 1px solid var(--border-color) !important; border-radius: 10px !important; background: var(--card-bg) !important; }
</style>
"""

st.set_page_config(page_title="ChemSafe Pro Enterprise", page_icon="⚗️", layout="wide", initial_sidebar_state="expanded")
st.markdown(APP_CSS, unsafe_allow_html=True)

# ==============================================================================
# FUNÇÕES DE BLINDAGEM E AUXILIARES
# ==============================================================================
def is_valid_df(df):
    return isinstance(df, pd.DataFrame) and not df.empty

def get_action_col(df):
    """Localiza a coluna de ação independente do nome gerado pelo backend."""
    for col in ["Ação Recomendada", "Ação", "Recomendação", "Ações"]:
        if col in df.columns: return col
    return df.columns[0]

def render_modern_gauge(score, band):
    color = "#10b981" if score >= 80 else "#f59e0b" if score >= 50 else "#ef4444"
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        number={'suffix': "%", 'font': {'color': "white", 'size': 40}},
        title={'text': f"Status Atual:<br><span style='color:{color}; font-weight:800;'>{band}</span>", 'font': {'size': 14}},
        gauge={'axis': {'range': [0, 100], 'tickcolor': "#30363d"}, 'bar': {'color': color}, 'bgcolor': "rgba(255,255,255,0.05)",
               'steps': [{'range': [0, 50], 'color': "rgba(239, 68, 68, 0.1)"}, {'range': [50, 80], 'color': "rgba(245, 158, 11, 0.1)"}, {'range': [80, 100], 'color': "rgba(16, 185, 129, 0.1)"}]}
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'family': "Inter", 'color': "#9ca3af"}, margin=dict(t=60, b=10, l=20, r=20), height=280)
    return fig

def metric_card(label: str, value: str, klass: str = "risk-blue") -> str:
    return f"<div class='metric-box'><div class='metric-label'>{label}</div><div class='metric-value {klass}'>{value}</div></div>"

# =========================
# Estado da sessão
# =========================
if "lang" not in st.session_state: st.session_state.lang = "pt"
if "selected_compound_key" not in st.session_state: st.session_state.selected_compound_key = "ammonia"
if "profile" not in st.session_state: st.session_state.profile = None
if "lopa_result" not in st.session_state: st.session_state.lopa_result = None
if "pid_hazop_matrix" not in st.session_state: st.session_state.pid_hazop_matrix = []
if "current_node_name" not in st.session_state: st.session_state.current_node_name = "Nó Global"

def load_profile_from_key(key: str) -> None:
    aliases = LOCAL_COMPOUNDS[key]["aliases"]
    st.session_state.profile = build_compound_profile(aliases[0])
    st.session_state.selected_compound_key = key

if st.session_state.profile is None:
    load_profile_from_key(st.session_state.selected_compound_key)
profile = st.session_state.profile

# ==============================================================================
# SIDEBAR NAVEGAÇÃO
# ==============================================================================
with st.sidebar:
    st.markdown(f"## ⚗️ ChemSafe AI\n**Enterprise Edition**")
    selected_module = option_menu(
        menu_title=None, options=["Dashboard", "Engenharia", "Análise de Risco", "Gestão de Mudança"],
        icons=["speedometer2", "cpu", "shield-lock", "arrow-repeat"], default_index=0,
        styles={"container": {"background-color": "transparent"}, "nav-link": {"font-size": "14px"}, "nav-link-selected": {"background-color": "#3b82f6"}}
    )
    st.markdown("---")
    for key, data in LOCAL_COMPOUNDS.items():
        if st.button(data["identity"]["name"], key=f"side_{key}", width=200): load_profile_from_key(key)

# HEADER DE CONTEXTO
st.markdown(f'<div class="context-header"><div>🧪 Composto: <span>{profile.identity.get("name")}</span></div><div>🏭 Local: <span>{st.session_state.current_node_name}</span></div></div>', unsafe_allow_html=True)

# PROCESSAMENTO DE DADOS GLOBAIS
psi_df = build_psi_readiness_df(profile, st.session_state.get("lopa_result"), {"threats":[]})
cri = calculate_case_readiness_index(profile, summarize_psi_readiness(psi_df), None, None, st.session_state.get("lopa_result"), None)
action_df = build_consolidated_action_plan(profile, psi_df, None, None, None)

# ==============================================================================
# MÓDULO 1: DASHBOARD & ACTION HUB
# ==============================================================================
if selected_module == "Dashboard":
    m_tab = option_menu(None, ["Visão Geral", "Plano de Ação (OSHA)", "Relatórios"], 
                        icons=["grid", "list-check", "file-pdf"], orientation="horizontal")

    if m_tab == "Visão Geral":
        c1, c2, c3 = st.columns(3)
        c1.markdown(metric_card("Maturidade", f"{cri['index']}%", cri['color_class']), unsafe_allow_html=True)
        c2.markdown(metric_card("Ações Pendentes", str(len(action_df)) if is_valid_df(action_df) else "0", "risk-amber"), unsafe_allow_html=True)
        c3.markdown(metric_card("Status", cri['band'], cri['color_class']), unsafe_allow_html=True)
        
        l, r = st.columns(2)
        with l: st.plotly_chart(render_modern_gauge(cri['index'], cri['band']), use_container_width=True, theme=None)
        with r:
            st.markdown("<div class='panel'><h3>Distribuição por Pilar</h3></div>", unsafe_allow_html=True)
            st.info("Analytics de pilares de risco carregando...")

    elif m_tab == "Plano de Ação (OSHA)":
        st.markdown("<div class='panel'><h3>Hub de Recomendações e Governança</h3></div>", unsafe_allow_html=True)
        if is_valid_df(action_df):
            col_acao = get_action_col(action_df)
            if "Status" not in action_df.columns: action_df["Status"] = "Aberto"
            if "Responsável" not in action_df.columns: action_df["Responsável"] = "Engenharia"
            
            # Orçamento Estimado (CCPS Baseline)
            capex_qty = len(action_df[action_df[col_acao].str.contains("Instalar|SIS|Válvula|Sensor", case=False)])
            budget = (capex_qty * 150000) + ((len(action_df) - capex_qty) * 8500)
            
            st.markdown(f"<div class='note-card'>💰 <b>Orçamento de Mitigação Estimado (CCPS):</b> R$ {budget:,.2f}</div>", unsafe_allow_html=True)

            edited = st.data_editor(action_df, width="stretch", hide_index=True, column_config={
                "Status": st.column_config.SelectboxColumn("Status", options=["Aberto", "Fechado", "Em Andamento"], required=True),
                "Responsável": st.column_config.SelectboxColumn("Responsável", options=["Engenharia", "Operação", "HSE", "Manutenção"]),
                "Criticidade": st.column_config.TextColumn("Criticidade", disabled=True, width="medium"),
                col_acao: st.column_config.TextColumn("Ação", width="large")
            })
            
            if st.button("Gerar Briefing de Ordem de Serviço (IEC 61511)"):
                st.download_button("Baixar TXT", "Equipe: Manutenção\nLocal: Planta...", "os.txt")
        else:
            st.success("Nenhuma ação pendente encontrada.")

# ==============================================================================
# MÓDULO 2: ENGENHARIA
# ==============================================================================
elif selected_module == "Engenharia":
    e_tab = option_menu(None, ["Termodinâmica", "Cinética Runaway", "PSV Sizing"], icons=["thermometer", "fire", "speedometer2"], orientation="horizontal")
    if e_tab == "Termodinâmica":
        st.dataframe(format_physchem_df(profile), width="stretch")
    elif e_tab == "Cinética Runaway":
        t0 = st.number_input("Temp. Inicial (°C)", 80.0)
        if st.button("Simular TMR Adiabático"):
            res = calculate_tmr_adiabatic(t0, 100, 1e12, 1500, 2.5)
            st.metric("Tempo p/ Explosão (TMR)", f"{res['tmr_min']:.1f} min")

# ==============================================================================
# MÓDULO 3: RISCO (PHA)
# ==============================================================================
elif selected_module == "Análise de Risco":
    r_tab = option_menu(None, ["P&ID Builder", "HAZOP", "LOPA / SIL", "QRA F-N"], icons=["diagram-3", "table", "shield-check", "activity"], orientation="horizontal")
    
    if r_tab == "P&ID Builder":
        eqs = st.multiselect("Equipamentos", list(EQUIPMENT_PARAMETERS.keys()), ["Bomba Centrífuga"])
        dot = graphviz.Digraph()
        dot.attr(rankdir='LR', bgcolor='transparent')
        dot.attr('node', shape='box', style='filled', fillcolor='#1e293b', color='#3b82f6', fontcolor='white')
        for i, e in enumerate(eqs):
            dot.node(str(i), e)
            if i > 0: dot.edge(str(i-1), str(i))
        st.graphviz_chart(dot, use_container_width=True)

    elif r_tab == "LOPA / SIL":
        st.markdown("### Verificação SIL (IEC 61511)")
        arq = st.selectbox("Arquitetura", ["1oo1", "1oo2", "2oo3"])
        st.button("Calcular PFDavg")

    elif r_tab == "QRA F-N":
        st.markdown("### Curva F-N de Risco Social (CETESB)")
        fig_fn = px.line(x=[1, 10, 100], y=[1e-4, 1e-5, 1e-6], log_x=True, log_y=True, title="Limite de Tolerância")
        fig_fn.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#9ca3af")
        st.plotly_chart(fig_fn, use_container_width=True)

# ==============================================================================
# MÓDULO 4: GESTÃO DE MUDANÇA
# ==============================================================================
elif selected_module == "Gestão de Mudança":
    st.markdown("<div class='panel'><h3>🔄 Ciclo MOC / PSSR</h3></div>", unsafe_allow_html=True)
    tipo = st.selectbox("Tipo de Mudança", ["Química", "Equipamento"])
    if st.button("Protocolar"):
        st.success("MOC Gerado com sucesso.")
