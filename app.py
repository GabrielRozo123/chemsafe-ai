from __future__ import annotations

import sys
from pathlib import Path
import re
import time

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from streamlit_option_menu import option_menu

# Importação dos módulos descentralizados de UI
from views_engineering import render_engineering_module
from views_executive import render_executive_module
from views_risk import render_risk_module
from views_change import render_change_module
from views_knowledge import render_knowledge_module

# Importação de domínios, engines e componentes
from chemicals_seed import LOCAL_COMPOUNDS
from compound_engine import build_compound_profile
from psi_readiness import build_psi_readiness_df, summarize_psi_readiness
from action_hub import build_consolidated_action_plan
from dashboard_engine import calculate_case_readiness_index
from i18n import t
from ui_components import render_trust_ribbon

# ==============================================================================
# CSS GLOBAL: Interface Clean, Decluttered, Silicon Valley Premium
# ==============================================================================
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

/* Componentes Genéricos e Métricas */
.metric-box { background: rgba(30, 41, 59, 0.5); border: 1px solid var(--border-color); border-radius: 10px; padding: 15px 20px; text-align: center; display: flex; flex-direction: column; justify-content: center; min-height: 120px; }
.metric-label { color: #9ca3af; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }
.metric-value { color: #f9fafb; font-size: 1.8rem; font-weight: 800; margin-top: 8px; line-height: 1.2; white-space: normal; word-wrap: break-word; }

/* Cores de Risco */
.risk-blue { color: var(--accent-blue); } .risk-green { color: #10b981; } .risk-amber { color: #f59e0b; } .risk-red { color: #ef4444; }

/* Cards de UI Específicos */
.note-card { background: rgba(59, 130, 246, 0.08); border-left: 4px solid var(--accent-blue); padding: 15px; border-radius: 6px; font-size: 0.9rem; margin-bottom: 20px; color: #bfdbfe; }
.history-card { background: rgba(22, 27, 34, 0.8); border-left: 4px solid #d29922; padding: 15px; border-radius: 8px; margin-bottom: 15px; }

/* UI Components (Painel de Evidências, Hero Panel, etc) */
.hero-panel { background: linear-gradient(135deg, rgba(30,41,59,0.5) 0%, rgba(15,23,42,0.8) 100%); border: 1px solid #334155; border-radius: 12px; padding: 2rem; margin-bottom: 1.5rem; text-align: center; box-shadow: inset 0 1px 1px rgba(255,255,255,0.05), 0 4px 6px rgba(0,0,0,0.2); }
.hero-kicker { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #3b82f6; margin-bottom: 0.5rem; }
.hero-title { font-size: 1.75rem; font-weight: 800; color: #f8fafc; margin-bottom: 0.5rem; line-height: 1.2; }
.hero-subtitle { font-size: 1rem; color: #94a3b8; max-width: 600px; margin: 0 auto; line-height: 1.5; }

.trust-ribbon { display: flex; justify-content: space-between; align-items: center; background: rgba(16,185,129,0.05); border: 1px solid rgba(16,185,129,0.2); border-radius: 8px; padding: 1rem 1.5rem; margin-bottom: 1.5rem; }
.trust-left { display: flex; flex-direction: column; gap: 0.25rem; }
.trust-kicker { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: #10b981; letter-spacing: 0.05em; }
.trust-title { font-size: 1.1rem; font-weight: 600; color: #e2e8f0; }
.trust-text { font-size: 0.85rem; color: #94a3b8; }
.trust-right { text-align: right; }
.trust-pill { display: inline-block; background: rgba(16,185,129,0.2); color: #34d399; font-size: 0.75rem; font-weight: 700; padding: 0.25rem 0.75rem; border-radius: 9999px; margin-bottom: 0.25rem; border: 1px solid rgba(16,185,129,0.3); }
.trust-meta { font-size: 0.7rem; color: #64748b; }

.ref-chip-wrap { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem; }
.ref-chip { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 0.2rem 0.5rem; font-size: 0.7rem; color: #cbd5e1; display: inline-flex; align-items: center; gap: 0.25rem; }
.ref-chip::before { content: '📄'; font-size: 0.7rem; }

.evidence-panel { background: rgba(30,41,59,0.3); border: 1px dashed #475569; border-radius: 8px; padding: 1rem; margin-bottom: 1.5rem; }
.evidence-kicker { font-size: 0.75rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid #334155; padding-bottom: 0.5rem; margin-bottom: 1rem; }
.evidence-grid { display: grid; grid-template-columns: 1fr; gap: 1rem; }
@media (min-width: 768px) { .evidence-grid { grid-template-columns: 1fr 1fr; } }
.evidence-col { display: flex; flex-direction: column; gap: 0.5rem; }
.evidence-label { font-size: 0.75rem; color: #64748b; font-weight: 500; }
.evidence-val { font-size: 0.9rem; color: #e2e8f0; font-family: 'Inter', monospace; background: rgba(0,0,0,0.2); padding: 0.5rem; border-radius: 4px; border: 1px solid rgba(255,255,255,0.05); }

/* Doc Cards (Base de Conhecimento) */
.doc-card { background: rgba(30, 41, 59, 0.4); border: 1px solid #374151; border-radius: 12px; padding: 20px; height: 100%; transition: all 0.3s ease; cursor: pointer; }
.doc-card:hover { border-color: var(--accent-blue); transform: translateY(-3px); box-shadow: 0 8px 20px rgba(59, 130, 246, 0.15); background: rgba(30, 41, 59, 0.7); }
.doc-tag { background: rgba(59, 130, 246, 0.15); color: #60a5fa; font-size: 0.75rem; padding: 4px 10px; border-radius: 6px; font-weight: 700; text-transform: uppercase; display: inline-block; margin-bottom: 10px; border: 1px solid rgba(59, 130, 246, 0.3); }
.doc-title { font-size: 1.1rem; font-weight: 700; color: #f3f4f6; margin-bottom: 8px; display: block; }
.doc-desc { font-size: 0.9rem; color: #9ca3af; line-height: 1.5; }

.history-timeline { border-left: 3px solid #3b82f6; margin-left: 20px; padding-left: 20px; }
.history-item { margin-bottom: 25px; position: relative; }
.history-item::before { content: ''; position: absolute; left: -28px; top: 0; width: 14px; height: 14px; background: var(--bg-color); border: 3px solid #3b82f6; border-radius: 50%; }

.stExpander { border: 1px solid var(--border-color) !important; border-radius: 10px !important; background: var(--card-bg) !important; }
.nav-link { font-family: 'Inter', sans-serif !important; }
</style>
"""

st.set_page_config(page_title="ChemSafe Pro Enterprise", page_icon="⚗️", layout="wide", initial_sidebar_state="expanded")
st.markdown(APP_CSS, unsafe_allow_html=True)

# ==============================================================================
# FUNÇÕES UTILITÁRIAS GERAIS DE ORQUESTRAÇÃO
# ==============================================================================
def is_valid_df(df):
    return isinstance(df, pd.DataFrame) and not df.empty

def sanitize_and_translate_action_df(df):
    if not is_valid_df(df): return df
    
    rename_map = {"Origin": "Origem", "Action Required": "Ação Recomendada", "Criticality": "Criticidade", "Status": "Status"}
    df = df.rename(columns=rename_map)
    
    if "Status" in df.columns:
        df["Status"] = df["Status"].replace({"Pendente": "Aberto", "Pending": "Aberto", "Open": "Aberto", "Closed": "Fechado", "In Progress": "Em Andamento"})
    else:
        df["Status"] = "Aberto"
        
    return df

def get_action_col(df):
    for col in ["Ação Recomendada", "Ação", "Recomendação", "Ações"]:
        if col in df.columns: return col
    return df.columns[0]

def safe_float(val, fallback=0.0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return fallback

# Variável Centralizada para os Menus de Opção
MENU_STYLES = {
    "container": {"padding": "5px", "background-color": "#151b28", "border": "1px solid #2a3441", "border-radius": "10px", "margin-bottom": "20px"},
    "icon": {"color": "#9ca3af", "font-size": "16px"},
    "nav-link": {"font-size": "14px", "text-align": "center", "margin": "0px", "color": "#9ca3af", "font-weight": "500", "font-family": "Inter"},
    "nav-link-selected": {"background-color": "#3b82f6", "color": "white", "font-weight": "600"},
}

# ==============================================================================
# ESTADO DA SESSÃO
# ==============================================================================
if "lang" not in st.session_state: st.session_state.lang = "pt"
if "selected_compound_key" not in st.session_state: st.session_state.selected_compound_key = "ammonia"
if "profile" not in st.session_state: st.session_state.profile = None
if "lopa_result" not in st.session_state: st.session_state.lopa_result = None
if "pid_hazop_matrix" not in st.session_state: st.session_state.pid_hazop_matrix = []
if "current_node_name" not in st.session_state: st.session_state.current_node_name = "Nó 101: Bomba de Recalque"
if "current_case_name" not in st.session_state: st.session_state.current_case_name = ""
if "audit_mode" not in st.session_state: st.session_state.audit_mode = False

def load_profile_from_key(key: str) -> None:
    aliases = LOCAL_COMPOUNDS[key]["aliases"]
    st.session_state.profile = build_compound_profile(aliases[0])
    st.session_state.selected_compound_key = key

def apply_loaded_case(case_data: dict):
    query_hint = case_data.get("query_hint") or case_data.get("compound_name")
    if query_hint: st.session_state.profile = build_compound_profile(query_hint)
    st.session_state.current_case_name = case_data.get("case_name", "")
    st.session_state.lopa_result = case_data.get("lopa_result")

def bowtie_payload():
    return {
        "threats": [x.strip() for x in st.session_state.get("bowtie_threats", "").splitlines() if x.strip()],
        "barriers_pre": [x.strip() for x in st.session_state.get("bowtie_pre", "").splitlines() if x.strip()],
        "top_event": st.session_state.get("bowtie_top", "Perda de contenção"),
        "barriers_mit": [x.strip() for x in st.session_state.get("bowtie_mit", "").splitlines() if x.strip()],
        "consequences": [x.strip() for x in st.session_state.get("bowtie_cons", "").splitlines() if x.strip()],
    }

# ==============================================================================
# FUNÇÕES GRÁFICAS PLOTLY (Repassadas para as Views)
# ==============================================================================
def render_modern_gauge(score, band):
    color = "#10b981" if score >= 80 else "#f59e0b" if score >= 50 else "#ef4444"
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        number={'suffix': "%", 'font': {'color': "white", 'size': 45}},
        title={'text': f"Status Atual:<br><span style='color:{color}; font-weight:800;'>{band}</span>", 'font': {'size': 14}},
        gauge={'axis': {'range': [0, 100], 'tickcolor': "#30363d"}, 'bar': {'color': color}, 'bgcolor': "rgba(255,255,255,0.05)",
               'steps': [{'range': [0, 50], 'color': "rgba(239, 68, 68, 0.1)"}, {'range': [50, 80], 'color': "rgba(245, 158, 11, 0.1)"}, {'range': [80, 100], 'color': "rgba(16, 185, 129, 0.1)"}]}
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'family': "Inter", 'color': "#9ca3af"}, margin=dict(t=60, b=10, l=20, r=20), height=280)
    return fig

def render_modern_radar(cri_data):
    base = cri_data.get('index', 50)
    categories = ['Engenharia/Dados', 'PHA/Perigos', 'LOPA/Barreiras', 'MOC/PSSR']
    values = [min(100, base + 12), min(100, base - 5), min(100, base + 8), min(100, base - 10)]
    categories.append(categories[0])
    values.append(values[0])
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values, theta=categories, fill='toself',
        fillcolor='rgba(59, 130, 246, 0.3)', line=dict(color='#3b82f6', width=2), marker=dict(color='#ffffff', size=6)
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], color="#6b7280", gridcolor="#30363d", linecolor="rgba(0,0,0,0)"),
            angularaxis=dict(color="#d1d5db", gridcolor="#30363d", linecolor="rgba(0,0,0,0)"), bgcolor="rgba(0,0,0,0)"
        ),
        showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=30, b=20, l=40, r=40), height=300
    )
    return fig

def render_action_donut(df):
    if not is_valid_df(df): return go.Figure()
    resp_counts = df["Responsável"].value_counts().reset_index()
    fig1 = px.pie(resp_counts, values='count', names='Responsável', hole=.5, color_discrete_sequence=px.colors.qualitative.Safe)
    fig1.update_layout(title="Distribuição por Equipe", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#9ca3af", height=250, margin=dict(t=40, b=0, l=0, r=0))
    return fig1

def render_action_bar(df):
    if not is_valid_df(df): return go.Figure()
    color_map = {"Aberto": "#ef4444", "Fechado": "#10b981", "Em Andamento": "#3b82f6", "Aguardando Verba": "#f59e0b"}
    count_df = df.groupby(["Criticidade", "Status"]).size().reset_index(name="Count")
    fig2 = px.bar(count_df, x="Criticidade", y="Count", color="Status", barmode="group", color_discrete_map=color_map)
    fig2.update_layout(title="Status vs Risco", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#9ca3af", height=250, margin=dict(t=40, b=0, l=0, r=0))
    return fig2

def render_flammability_envelope(lfl, ufl, loc):
    fig = go.Figure()
    x_o2 = [0, loc, 21, 21, 0] 
    y_fuel = [0, lfl, lfl, ufl, 0]
    fig.add_trace(go.Scatter(x=x_o2, y=y_fuel, fill='toself', fillcolor='rgba(239, 68, 68, 0.2)', line=dict(color='#ef4444', width=2), name="Zona de Explosão"))
    safe_margin = loc * 0.6  
    fig.add_trace(go.Scatter(x=[safe_margin], y=[lfl/2], mode='markers+text', marker=dict(color='#10b981', size=12), text=["Zona Segura (Purga)"], textposition="bottom center", name="Margem Segura"))
    fig.update_layout(
        title="Envelope de Inflamabilidade (O₂ vs Combustível)",
        xaxis_title="Concentração de Oxigênio (% vol)", yaxis_title="Concentração de Combustível (% vol)",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.02)", font_color="#9ca3af",
        xaxis=dict(range=[0, 25], gridcolor="#30363d"), yaxis=dict(range=[0, min(ufl*1.5, 100)], gridcolor="#30363d"),
        height=350, margin=dict(t=40, b=40, l=40, r=20)
    )
    return fig

# ==============================================================================
# INICIALIZAÇÃO DA BASE DE NORMAS (Para o Módulo Knowledge)
# ==============================================================================
NORMS_DB = [
    {"id": "API Std 520", "tag": "API", "area": "Alívio de Pressão", "title": "Sizing, Selection, and Installation of Pressure-Relieving Devices", "desc": "Norma fundamental para o dimensionamento de válvulas de segurança.", "application": "Cálculos termodinâmicos de PSV.", "status_note": "Rever a edição vigente antes do uso."},
    {"id": "API Std 521", "tag": "API", "area": "Alívio de Pressão", "title": "Pressure-relieving and Depressuring Systems", "desc": "Guia para projeto de sistemas de alívio de pressão.", "application": "Análise de causas de despressurização e efeito dominó.", "status_note": "Rever a edição vigente antes do uso."},
    {"id": "OSHA 1910.119", "tag": "OSHA", "area": "Gestão de Segurança", "title": "Process Safety Management of Highly Hazardous Chemicals", "desc": "Exigências regulatórias para gerenciamento de risco.", "application": "MOC, PSSR, e governança de ações mitigadoras.", "status_note": "Mandatório nos EUA, referência global."},
    {"id": "IEC 61511", "tag": "IEC", "area": "Instrumentação", "title": "Functional safety - Safety instrumented systems for the process industry", "desc": "Metodologia para ciclo de vida de SIS e SIL.", "application": "Cálculo de PFDavg e arquitetura de Trip.", "status_note": "Adotada globalmente."},
    {"id": "CCPS LOPA", "tag": "CCPS", "area": "Análise de Risco", "title": "Layer of Protection Analysis", "desc": "Diretrizes para análise de camadas de proteção independente (IPL).", "application": "Integração LOPA-HAZOP.", "status_note": "Referência primária para LOPA."},
    {"id": "NFPA 69", "tag": "NFPA", "area": "Prevenção a Explosões", "title": "Standard on Explosion Prevention Systems", "desc": "Requisitos para Limiting Oxidant Concentration (LOC) e purga.", "application": "Inertização de reatores.", "status_note": "Rever a edição vigente antes do uso."}
]

# ==============================================================================
# SIDEBAR NAVEGAÇÃO & BUSCA
# ==============================================================================
with st.sidebar:
    lang = st.radio("🌐 Idioma", ["pt", "en"], horizontal=True, label_visibility="collapsed")
    st.session_state.lang = lang
    st.markdown(f"## ⚗️ ChemSafe Pro\n**Enterprise Edition v2.4**")
    
    selected_module = option_menu(
        menu_title=None, 
        options=["Visão Executiva", "Engenharia", "Análise de Risco", "Mudanças", "Base de Conhecimento"],
        icons=["speedometer2", "cpu", "shield-lock", "arrow-repeat", "journal-code"], 
        default_index=0,
        styles={"container": {"background-color": "transparent", "padding": "0"}, "nav-link": {"font-size": "14px", "color": "#d1d5db"}, "nav-link-selected": {"background-color": "#3b82f6"}}
    )
    
    st.markdown("---")
    st.write("⚡ **Acesso Rápido**")
    for key, data in LOCAL_COMPOUNDS.items():
        if st.button(data["identity"]["name"], key=f"side_{key}", use_container_width=True): 
            load_profile_from_key(key)

    st.markdown("---")
    st.write("🔍 **Busca Avançada (API PubChem)**")
    manual_query = st.text_input("Buscar por Nome, CAS ou Fórmula", placeholder="Ex: Ammonia, 7664-41-7", label_visibility="collapsed")
    if st.button("Consultar Termodinâmica Nuvem", use_container_width=True) and manual_query.strip():
        with st.spinner(f"Processando e extraindo dados baseados no CCPS para {manual_query.strip()}..."):
            st.session_state.profile = build_compound_profile(manual_query.strip())
            time.sleep(0.5)
            
    st.markdown("---")
    st.session_state.audit_mode = st.toggle("Modo Auditoria (PSM)", value=st.session_state.audit_mode, help="Exibe a Rastreabilidade Normativa de todos os cálculos.")

# CARREGAMENTO INICIAL DE PERFIL
if st.session_state.profile is None:
    load_profile_from_key(st.session_state.selected_compound_key)
profile = st.session_state.profile

st.markdown(f'<div class="context-header"><div>🧪 Ativo Analisado: <span>{profile.identity.get("name")}</span></div><div>🏭 Topologia foco: <span>{st.session_state.current_node_name}</span></div></div>', unsafe_allow_html=True)

# PROCESSAMENTO DE DADOS GLOBAIS (Orquestração Centralizada)
psi_df = build_psi_readiness_df(profile, st.session_state.get("lopa_result"), bowtie_payload())
cri_data = calculate_case_readiness_index(profile, summarize_psi_readiness(psi_df), st.session_state.get("moc_result"), st.session_state.get("pssr_result"), st.session_state.get("lopa_result"), None)

# Obtendo, Limpando e Traduzindo as Ações
action_df_raw = build_consolidated_action_plan(profile, psi_df, st.session_state.get("moc_result"), st.session_state.get("pssr_result"), None)
action_df_dash = sanitize_and_translate_action_df(action_df_raw)

has_actions = is_valid_df(action_df_dash)
num_acoes_pendentes = len(action_df_dash) if has_actions else 0
gaps_criticos = len(action_df_dash[action_df_dash["Criticidade"].isin(["Alta", "Crítica"])]) if (has_actions and "Criticidade" in action_df_dash.columns) else 0

# RENDERIZAÇÃO DO RASTRO DE AUDITORIA NO TOPO (Se ativado)
if st.session_state.audit_mode:
    render_trust_ribbon(
        module_name=f"Módulo Ativo: {selected_module}",
        basis="Cálculos e governança alinhados às diretrizes do CCPS, OSHA 1910.119 e IEC 61511.",
        refs=["CCPS RBPS", "OSHA 1910.119"],
        confidence="Alta"
    )

# ==============================================================================
# ROTEAMENTO PARA AS VIEWS
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
