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

# NOVOS MÓDULOS SPRINT 11 A 21
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

# CSS: Interface Premium com Correção de Texto Cortado
APP_CSS = """
<style>
:root { --bg-color: #0b0f19; --card-bg: #151b28; --border-color: #2a3441; --text-main: #d1d5db; --accent-blue: #3b82f6; --accent-glow: rgba(59, 130, 246, 0.15); }
.stApp { background-color: var(--bg-color); color: var(--text-main); font-family: 'Inter', -apple-system, sans-serif; }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1440px; }
.context-header { background: var(--card-bg); border: 1px solid var(--border-color); padding: 15px 25px; border-radius: 12px; margin-bottom: 30px; font-weight: 500; font-size: 0.95rem; color: #9ca3af; display: flex; justify-content: space-between; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }
.context-header span { color: #fff; font-weight: 600; }
.panel { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; padding: 1.8rem; margin-bottom: 1.2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.15); }
.panel h3 { margin-top: 0; color: #f3f4f6; font-size: 1.15rem; font-weight: 600; border-bottom: 1px solid var(--border-color); padding-bottom: 10px; margin-bottom: 20px; }

/* CORREÇÃO PARA TEXTO CORTADO EM CARDS */
.metric-box { background: rgba(30, 41, 59, 0.5); border: 1px solid var(--border-color); border-radius: 10px; padding: 15px 20px; text-align: center; display: flex; flex-direction: column; justify-content: center; min-height: 130px; }
.metric-label { color: #9ca3af; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }
.metric-value { color: #f9fafb; font-size: 1.7rem; font-weight: 800; margin-top: 8px; line-height: 1.2; white-space: normal; word-wrap: break-word; }

.risk-blue { color: var(--accent-blue); } .risk-green { color: #10b981; } .risk-amber { color: #f59e0b; } .risk-red { color: #ef4444; }
.note-card { background: rgba(59, 130, 246, 0.08); border-left: 4px solid var(--accent-blue); padding: 15px; border-radius: 6px; font-size: 0.9rem; margin-bottom: 20px; color: #bfdbfe; }
.stExpander { border: 1px solid var(--border-color) !important; border-radius: 10px !important; background: var(--card-bg) !important; }
</style>
"""

st.set_page_config(page_title="ChemSafe Pro Enterprise", page_icon="⚗️", layout="wide", initial_sidebar_state="expanded")
st.markdown(APP_CSS, unsafe_allow_html=True)

# ==============================================================================
# FUNÇÕES DE UTILIDADE E BLINDAGEM
# ==============================================================================
def is_valid_df(df):
    return isinstance(df, pd.DataFrame) and not df.empty

def get_action_col(df):
    possible = ["Ação Recomendada", "Ação", "Recomendação", "Ações"]
    for p in possible:
        if p in df.columns: return p
    return df.columns[-1]

# ==============================================================================
# MOTORES GRÁFICOS PLOTLY
# ==============================================================================
def render_modern_gauge(score, band):
    color = "#10b981" if score >= 80 else "#f59e0b" if score >= 50 else "#ef4444"
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        number={'suffix': "%", 'font': {'color': "white", 'size': 40}},
        title={'text': f"Status: <span style='color:{color}'>{band}</span>", 'font': {'size': 16}},
        gauge={'axis': {'range': [0, 100], 'tickcolor': "#30363d"}, 'bar': {'color': color}, 'bgcolor': "rgba(255,255,255,0.05)",
               'steps': [{'range': [0, 50], 'color': "rgba(239, 68, 68, 0.1)"}, {'range': [50, 80], 'color': "rgba(245, 158, 11, 0.1)"}, {'range': [80, 100], 'color': "rgba(16, 185, 129, 0.1)"}]}
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'family': "Inter", 'color': "#9ca3af"}, margin=dict(t=60, b=10, l=20, r=20), height=280)
    return fig

def render_action_analytics(df):
    if not is_valid_df(df): return go.Figure(), go.Figure()
    # Donut de Responsáveis
    resp_counts = df["Responsável"].value_counts().reset_index()
    fig1 = px.pie(resp_counts, values='count', names='Responsável', hole=.5, color_discrete_sequence=px.colors.qualitative.Pastel)
    fig1.update_layout(title="Ações por Equipe", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#9ca3af", height=250, margin=dict(t=40, b=0, l=0, r=0))
    # Bar Status vs Criticidade
    fig2 = px.bar(df, x="Criticidade", color="Status", barmode="group", color_discrete_map={"Aberto": "#ef4444", "Fechado": "#10b981"})
    fig2.update_layout(title="Status por Criticidade", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#9ca3af", height=250, margin=dict(t=40, b=0, l=0, r=0))
    return fig1, fig2

# ==============================================================================
# ESTADO DA SESSÃO
# ==============================================================================
if "lang" not in st.session_state: st.session_state.lang = "pt"
if "selected_compound_key" not in st.session_state: st.session_state.selected_compound_key = "ammonia"
if "profile" not in st.session_state: st.session_state.profile = None
if "lopa_result" not in st.session_state: st.session_state.lopa_result = None
if "pid_hazop_matrix" not in st.session_state: st.session_state.pid_hazop_matrix = []
if "current_node_name" not in st.session_state: st.session_state.current_node_name = "Nó 101: Bomba de Recalque"

def load_profile_from_key(key: str) -> None:
    aliases = LOCAL_COMPOUNDS[key]["aliases"]
    st.session_state.profile = build_compound_profile(aliases[0])
    st.session_state.selected_compound_key = key

if st.session_state.profile is None:
    load_profile_from_key(st.session_state.selected_compound_key)
profile = st.session_state.profile

# ==============================================================================
# SIDEBAR NAVEGAÇÃO (Silicon Valley Style)
# ==============================================================================
with st.sidebar:
    st.markdown(f"## ⚗️ {t('app_title', 'pt')}\n**Enterprise v2.2**")
    selected_module = option_menu(
        menu_title=None, options=["Executivo", "Engenharia", "Análise de Risco", "Mudanças"],
        icons=["speedometer2", "cpu", "shield-lock", "arrow-repeat"], default_index=0,
        styles={"container": {"background-color": "transparent"}, "nav-link": {"font-size": "14px", "color": "#d1d5db"}, "nav-link-selected": {"background-color": "#3b82f6"}}
    )
    st.markdown("---")
    for key, data in LOCAL_COMPOUNDS.items():
        if st.button(data["identity"]["name"], key=f"q_{key}", use_container_width=True): load_profile_from_key(key)

# HEADER DE CONTEXTO
st.markdown(f'<div class="context-header"><div>🧪 Ativo: <span>{profile.identity.get("name")}</span></div><div>🏭 Nó: <span>{st.session_state.current_node_name}</span></div></div>', unsafe_allow_html=True)

# PROCESSAMENTO DE DADOS GLOBAIS
psi_df = build_psi_readiness_df(profile, st.session_state.get("lopa_result"), {"threats":[]})
cri = calculate_case_readiness_index(profile, summarize_psi_readiness(psi_df), None, None, st.session_state.get("lopa_result"), None)
action_df = build_consolidated_action_plan(profile, psi_df, None, None, None)

# ==============================================================================
# MÓDULO 1: EXECUTIVO & ACTION HUB
# ==============================================================================
if selected_module == "Executivo":
    m_tab = option_menu(None, ["Dashboard", "Action Plan (OSHA)", "Relatórios"], icons=["grid", "list-check", "file-pdf"], orientation="horizontal",
                        styles={"container": {"background-color": "#151b28", "border": "1px solid #2a3441", "border-radius": "10px"}})

    if m_tab == "Dashboard":
        c1, c2, c3 = st.columns(3)
        c1.markdown(metric_card("Maturidade Global", f"{cri['index']}%", cri['color_class']), unsafe_allow_html=True)
        c2.markdown(metric_card("Ações em Aberto", str(len(action_df)) if is_valid_df(action_df) else "0", "risk-amber"), unsafe_allow_html=True)
        c3.markdown(metric_card("Status de Risco", cri['band'], cri['color_class']), unsafe_allow_html=True)
        
        l, r = st.columns(2)
        with l: st.plotly_chart(render_modern_gauge(cri['index'], cri['band']), use_container_width=True, theme=None)
        with r:
            st.markdown("<div class='panel'><h3>Distribuição por Pilares</h3></div>", unsafe_allow_html=True)
            # Radar placeholder ou gráfico de barras de pilares
            st.info("Gráfico de radar de maturidade carregando...")

    elif m_tab == "Action Plan (OSHA)":
        st.markdown("<div class='panel'><h3>Hub de Governança de Recomendações</h3></div>", unsafe_allow_html=True)
        if is_valid_df(action_df):
            col_a = get_action_col(action_df)
            if "Status" not in action_df.columns: action_df["Status"] = "Aberto"
            if "Responsável" not in action_df.columns: action_df["Responsável"] = "Engenharia"
            
            # Analytics e Orçamento (CCPS Baseline)
            c_ch1, c_ch2, c_bud = st.columns([1, 1, 1])
            f1, f2 = render_action_analytics(action_df)
            c_ch1.plotly_chart(f1, use_container_width=True)
            c_ch2.plotly_chart(f2, use_container_width=True)
            
            capex_n = len(action_df[action_df[col_a].str.contains("Instalar|SIS|Válvula|Sensor", case=False)])
            budget = (capex_n * 150000) + ((len(action_df)-capex_n) * 8500)
            c_bud.markdown(f"<div style='background:rgba(59,130,246,0.1); border:1px solid #3b82f6; border-radius:10px; padding:20px; height:250px; display:flex; flex-direction:column; justify-content:center;'>"
                           f"<small>ORÇAMENTO ESTIMADO (CCPS)</small><h2 style='color:white'>R$ {budget:,.2f}</h2><p style='font-size:0.8rem'>CAPEX: {capex_n} itens | OPEX: {len(action_df)-capex_n} itens</p></div>", unsafe_allow_html=True)

            edited = st.data_editor(action_df, width="stretch", hide_index=True, column_config={
                "Status": st.column_config.SelectboxColumn("Status", options=["Aberto", "Fechado", "Em Andamento"]),
                "Responsável": st.column_config.SelectboxColumn("Responsável", options=["Engenharia", "Manutenção", "HSE"]),
                "Criticidade": st.column_config.TextColumn("Criticidade", disabled=True, width="medium"),
                col_a: st.column_config.TextColumn("Ação Recomendada", width="large")
            })
            
            if st.button("Gerar Ordem de Serviço (Workflow IEC 61511)"):
                st.download_button("Baixar Briefing de Campo", "ORDEM DE SERVIÇO\nEquipe: Manutenção\nAção: Verificar Válvula...", file_name="os.txt")

# ==============================================================================
# MÓDULO 2: ENGENHARIA (PSV & RUNAWAY)
# ==============================================================================
elif selected_module == "Engenharia":
    e_tab = option_menu(None, ["Termodinâmica", "Cinética Runaway", "Dimensionamento PSV"], icons=["thermometer", "fire", "speedometer2"], orientation="horizontal")
    
    if e_tab == "Termodinâmica":
        l, r = st.columns(2)
        l.markdown("<div class='panel'><h3>Dados Físico-Químicos</h3></div>", unsafe_allow_html=True)
        l.dataframe(format_physchem_df(profile), width="stretch")
        r.markdown("<div class='panel'><h3>Limites de Exposição</h3></div>", unsafe_allow_html=True)
        r.dataframe(format_limits_df(profile), width="stretch")

    elif e_tab == "Cinética Runaway":
        st.markdown("<div class='panel'><h3>🔥 Simulação de Estabilidade Térmica (Semenov/CCPS)</h3></div>", unsafe_allow_html=True)
        t0 = st.number_input("Temp. Operação (°C)", 80.0)
        if st.button("Calcular TMR Adiabático"):
            res = calculate_tmr_adiabatic(t0, 100, 1e12, 1500, 2.5)
            st.metric("TMR (Tempo até Explosão)", f"{res['tmr_min']:.1f} min", delta_color="inverse")
            st.warning(f"Status: {res['status']}")

# ==============================================================================
# MÓDULO 3: RISCO (SPRINT 22 - NOVAS FUNÇÕES)
# ==============================================================================
elif selected_module == "Análise de Risco":
    r_tab = option_menu(None, ["P&ID Visual", "HAZOP", "LOPA / SIL Verif.", "QRA Social (F-N)"], icons=["diagram-3", "table", "shield-check", "activity"], orientation="horizontal")

    if r_tab == "P&ID Visual":
        eqs = st.multiselect("Fluxo de Equipamentos", list(EQUIPMENT_PARAMETERS.keys()), ["Bomba Centrífuga"])
        dot = graphviz.Digraph(format='png')
        dot.attr(rankdir='LR', bgcolor='transparent')
        dot.attr('node', shape='box', style='filled', fillcolor='#1e293b', color='#3b82f6', fontcolor='white')
        for i, e in enumerate(eqs):
            dot.node(str(i), e)
            if i > 0: dot.edge(str(i-1), str(i))
        st.graphviz_chart(dot, use_container_width=True)

    elif r_tab == "LOPA / SIL Verif.":
        st.markdown("<div class='panel'><h3>🖲️ Verificação de Arquitetura SIL (IEC 61511)</h3></div>", unsafe_allow_html=True)
        st.info("Módulo da Sprint 22: Cálculo de PFDavg por arquitetura (1oo1, 1oo2, 2oo3).")
        arq = st.selectbox("Arquitetura do Intertravamento", ["1oo1 (Single)", "1oo2 (Redundante)", "2oo3 (Votação)"])
        st.button("Validar Probabilidade de Falha")

    elif r_tab == "QRA Social (F-N)":
        st.markdown("<div class='panel'><h3>📈 Gráfico de Risco Social (Curva F-N)</h3></div>", unsafe_allow_html=True)
        st.info("Módulo da Sprint 22: Cruzamento de Frequência vs Fatalidades (Critério CETESB/TNO).")
        # Placeholder de gráfico ALARP
        fig_fn = go.Figure()
        fig_fn.add_trace(go.Scatter(x=[1, 10, 100], y=[1e-4, 1e-5, 1e-6], name="Linha de Tolerância (CETESB)", line_color="red"))
        fig_fn.update_layout(xaxis_type="log", yaxis_type="log", title="Curva F-N Interativa", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#9ca3af")
        st.plotly_chart(fig_fn, use_container_width=True)

# ==============================================================================
# MÓDULO 4: MUDANÇAS (MOC/PSSR)
# ==============================================================================
elif selected_module == "Mudanças":
    m_tab = option_menu(None, ["MOC", "PSSR"], icons=["arrow-repeat", "check2-square"], orientation="horizontal")
    if m_tab == "MOC":
        st.markdown("<div class='panel'><h3>🔄 Gestão de Mudanças</h3></div>", unsafe_allow_html=True)
        tipo = st.selectbox("Tipo", ["Química", "Equipamento", "Procedimento"])
        if st.button("Protocolar MOC"):
            res = evaluate_moc(profile, tipo, [], "")
            st.success(f"MOC Classificado: {res['summary']['category']}")
