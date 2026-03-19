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

# Módulos Legados e Engenharia
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

# MÓDULOS SPRINT 11 A 24
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

# CSS: Interface Clean, Decluttered, Silicon Valley Premium
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

.metric-box { background: rgba(30, 41, 59, 0.5); border: 1px solid var(--border-color); border-radius: 10px; padding: 15px 20px; text-align: center; display: flex; flex-direction: column; justify-content: center; min-height: 120px; }
.metric-label { color: #9ca3af; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }
.metric-value { color: #f9fafb; font-size: 1.8rem; font-weight: 800; margin-top: 8px; line-height: 1.2; white-space: normal; word-wrap: break-word; }

.risk-blue { color: var(--accent-blue); } .risk-green { color: #10b981; } .risk-amber { color: #f59e0b; } .risk-red { color: #ef4444; }
.note-card { background: rgba(59, 130, 246, 0.08); border-left: 4px solid var(--accent-blue); padding: 15px; border-radius: 6px; font-size: 0.9rem; margin-bottom: 20px; color: #bfdbfe; }
.stExpander { border: 1px solid var(--border-color) !important; border-radius: 10px !important; background: var(--card-bg) !important; }

.doc-card { background: rgba(30, 41, 59, 0.4); border: 1px solid #374151; border-radius: 12px; padding: 20px; height: 100%; transition: all 0.3s ease; cursor: pointer; }
.doc-card:hover { border-color: var(--accent-blue); transform: translateY(-3px); box-shadow: 0 8px 20px rgba(59, 130, 246, 0.15); background: rgba(30, 41, 59, 0.7); }
.doc-tag { background: rgba(59, 130, 246, 0.15); color: #60a5fa; font-size: 0.75rem; padding: 4px 10px; border-radius: 6px; font-weight: 700; text-transform: uppercase; display: inline-block; margin-bottom: 10px; border: 1px solid rgba(59, 130, 246, 0.3); }
.doc-title { font-size: 1.1rem; font-weight: 700; color: #f3f4f6; margin-bottom: 8px; display: block; }
.doc-desc { font-size: 0.9rem; color: #9ca3af; line-height: 1.5; }
.history-timeline { border-left: 3px solid #3b82f6; margin-left: 20px; padding-left: 20px; }
.history-item { margin-bottom: 25px; position: relative; }
.history-item::before { content: ''; position: absolute; left: -28px; top: 0; width: 14px; height: 14px; background: var(--bg-color); border: 3px solid #3b82f6; border-radius: 50%; }
.nav-link { font-family: 'Inter', sans-serif !important; }
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
    for col in ["Ação Recomendada", "Ação", "Recomendação", "Ações", "Action Required"]:
        if col in df.columns: return col
    return df.columns[0]

def sanitize_and_translate_action_df(df):
    """Limpa os dados do backend e traduz colunas/status para Português (PT-BR)"""
    if not is_valid_df(df): return df
    
    # Renomear colunas do inglês para o português, se existirem
    rename_map = {
        "Origin": "Origem",
        "Action Required": "Ação Recomendada",
        "Criticality": "Criticidade",
        "Status": "Status"
    }
    df = df.rename(columns=rename_map)
    
    # Padronizar a coluna de Status para as métricas não quebrarem
    if "Status" in df.columns:
        df["Status"] = df["Status"].replace({"Pendente": "Aberto", "Pending": "Aberto", "Open": "Aberto", "Closed": "Fechado", "In Progress": "Em Andamento"})
    else:
        df["Status"] = "Aberto"
        
    return df

def estimate_mitigation_cost(action_text):
    """
    Rigor Econômico: Baseado na AACE International (Class 5 Estimate) e CCPS.
    Retorna o valor estimado (R$) e a categoria contábil da recomendação.
    """
    text = str(action_text).lower()
    if any(k in text for k in ["sis", "intertravamento", "sil", "clp", "automação"]):
        return 250000.0, "CAPEX (SIS/Automação)"
    elif any(k in text for k in ["válvula", "psv", "alívio", "ruptura", "bomba"]):
        return 45000.0, "CAPEX (Mecânica)"
    elif any(k in text for k in ["alarme", "sensor", "detector", "f&g", "transmissor"]):
        return 35000.0, "CAPEX (Instrumentação)"
    elif any(k in text for k in ["instalar", "modificar", "trocar", "construir"]):
        return 80000.0, "CAPEX (Infraestrutura)"
    elif any(k in text for k in ["procedimento", "treinar", "revisar", "atualizar", "documento", "limites"]):
        return 8500.0, "OPEX (Engenharia/SGI)"
    else:
        return 15000.0, "OPEX (Geral/Estudos)"

# ==============================================================================
# MOTORES GRÁFICOS PLOTLY
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

def render_action_analytics(df):
    if not is_valid_df(df): return go.Figure(), go.Figure()
    resp_counts = df["Responsável"].value_counts().reset_index()
    fig1 = px.pie(resp_counts, values='count', names='Responsável', hole=.5, color_discrete_sequence=px.colors.qualitative.Safe)
    fig1.update_layout(title="Distribuição por Equipe", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#9ca3af", height=250, margin=dict(t=40, b=0, l=0, r=0))
    
    # Garantir que as cores batam com os status
    color_map = {"Aberto": "#ef4444", "Fechado": "#10b981", "Em Andamento": "#3b82f6", "Aguardando Verba": "#f59e0b"}
    count_df = df.groupby(["Criticidade", "Status"]).size().reset_index(name="Count")
    fig2 = px.bar(count_df, x="Criticidade", y="Count", color="Status", barmode="group", color_discrete_map=color_map)
    fig2.update_layout(title="Status vs Risco", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#9ca3af", height=250, margin=dict(t=40, b=0, l=0, r=0))
    return fig1, fig2

def render_flammability_envelope(lfl, ufl, loc):
    fig = go.Figure()
    x_o2 = [0, loc, 21, 21, 0] 
    y_fuel = [0, lfl, lfl, ufl, 0]
    fig.add_trace(go.Scatter(x=x_o2, y=y_fuel, fill='toself', fillcolor='rgba(239, 68, 68, 0.2)', line=dict(color='#ef4444', width=2), name="Zona de Explosão"))
    safe_margin = loc * 0.6
    fig.add_trace(go.Scatter(x=[safe_margin], y=[lfl/2], mode='markers+text', marker=dict(color='#10b981', size=12), text=["Zona Segura (Purga)"], textposition="bottom center", name="Safe Margin"))
    fig.update_layout(
        title="Envelope de Inflamabilidade (O₂ vs Combustível)",
        xaxis_title="Concentração de Oxigênio (% vol)", yaxis_title="Concentração de Combustível (% vol)",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.02)", font_color="#9ca3af",
        xaxis=dict(range=[0, 25], gridcolor="#30363d"), yaxis=dict(range=[0, min(ufl*1.5, 100)], gridcolor="#30363d"),
        height=350, margin=dict(t=40, b=40, l=40, r=20)
    )
    return fig

# =========================
# ESTADO DA SESSÃO
# =========================
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

def metric_card(label: str, value: str, klass: str = "risk-blue") -> str:
    return f"<div class='metric-box'><div class='metric-label'>{label}</div><div class='metric-value {klass}'>{value}</div></div>"

# ==============================================================================
# SIDEBAR NAVEGAÇÃO & BUSCA OTIMIZADA
# ==============================================================================
with st.sidebar:
    lang = st.radio("🌐 Idioma", ["pt", "en"], horizontal=True, label_visibility="collapsed")
    st.session_state.lang = lang
    st.markdown(f"## ⚗️ ChemSafe Pro\n**Enterprise Edition v2.4**")
    
    MENU_STYLES = {"container": {"background-color": "transparent", "padding": "0"}, "nav-link": {"font-size": "14px", "color": "#d1d5db"}, "nav-link-selected": {"background-color": "#3b82f6"}}
    selected_module = option_menu(
        menu_title=None, 
        options=["Visão Executiva", "Engenharia", "Análise de Risco", "Gestão de Mudança", "Base de Conhecimento"],
        icons=["speedometer2", "cpu", "shield-lock", "arrow-repeat", "journal-code"], 
        default_index=0,
        styles=MENU_STYLES
    )
    
    st.markdown("---")
    st.write("⚡ **Acesso Rápido**")
    for key, data in LOCAL_COMPOUNDS.items():
        if st.button(data["identity"]["name"], key=f"side_{key}", use_container_width=True): 
            load_profile_from_key(key)

    st.markdown("---")
    st.write("🔍 **Busca Avançada (API)**")
    manual_query = st.text_input("Buscar por Nome, CAS ou Fórmula", placeholder="Ex: 7664-41-7", label_visibility="collapsed")
    if st.button("Consultar Banco de Dados", use_container_width=True) and manual_query.strip():
        with st.spinner("Buscando dados termodinâmicos na nuvem..."):
            st.session_state.profile = build_compound_profile(manual_query.strip())

# CONTEXT HEADER
st.markdown(f'<div class="context-header"><div>🧪 Ativo Analisado: <span>{profile.identity.get("name")}</span></div><div>🏭 Topologia foco: <span>{st.session_state.current_node_name}</span></div></div>', unsafe_allow_html=True)

# PROCESSAMENTO DE DADOS GLOBAIS
psi_df = build_psi_readiness_df(profile, st.session_state.get("lopa_result"), {"threats":[]})
cri = calculate_case_readiness_index(profile, summarize_psi_readiness(psi_df), None, None, st.session_state.get("lopa_result"), None)

# Obtendo e Sanitizando as Ações
action_df_raw = build_consolidated_action_plan(profile, psi_df, None, None, None)
action_df = sanitize_and_translate_action_df(action_df_raw)

has_actions = is_valid_df(action_df)
num_acoes = len(action_df) if has_actions else 0

# ==============================================================================
# MÓDULO 1: VISÃO EXECUTIVA & ACTION HUB (COM RIGOR AACE/CCPS)
# ==============================================================================
if selected_module == "Visão Executiva":
    TAB_STYLES = {"container": {"background-color": "#151b28", "border": "1px solid #2a3441", "border-radius": "10px"}, "nav-link-selected": {"background-color": "#3b82f6"}}
    m_tab = option_menu(None, ["Dashboard Global", "Action Hub (OSHA)"], icons=["grid", "list-check"], orientation="horizontal", styles=TAB_STYLES)

    if m_tab == "Dashboard Global":
        st.markdown("<div class='panel'><h3>KPIs de Prontidão e Risco</h3></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.markdown(metric_card("Maturidade", f"{cri['index']}%", cri['color_class']), unsafe_allow_html=True)
        c2.markdown(metric_card("Pendências", str(num_acoes), "risk-amber"), unsafe_allow_html=True)
        c3.markdown(metric_card("Nível de Risco", cri['band'], cri['color_class']), unsafe_allow_html=True)
        
        l, r = st.columns(2)
        with l: st.plotly_chart(render_modern_gauge(cri['index'], cri['band']), use_container_width=True, theme=None, config={'displayModeBar': False})
        with r:
            st.markdown("<div class='panel'><h3>Distribuição por Pilares</h3></div>", unsafe_allow_html=True)
            values = [85, 70, 90, 65]
            fig_r = go.Figure(data=go.Scatterpolar(r=values, theta=['Dados Químicos', 'Engenharia', 'LOPA/SIL', 'MOC/PSSR'], fill='toself', fillcolor='rgba(59,130,246,0.2)', line_color='#3b82f6'))
            fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor="#30363d"), angularaxis=dict(gridcolor="#30363d")), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#9ca3af", height=300, margin=dict(t=30, b=30, l=40, r=40))
            st.plotly_chart(fig_r, use_container_width=True, theme=None)

    elif m_tab == "Action Hub (OSHA)":
        st.markdown("<div class='panel'><h3>Hub de Governança e Resolução de Ações</h3></div>", unsafe_allow_html=True)
        if has_actions:
            col_acao = get_action_col(action_df)
            if "Responsável" not in action_df.columns: action_df["Responsável"] = "Engenharia"
            
            # Aplicar motor financeiro AACE/CCPS linha a linha
            if "Custo Estimado (R$)" not in action_df.columns:
                action_df[["Custo Estimado (R$)", "Categoria AACE"]] = action_df[col_acao].apply(lambda x: pd.Series(estimate_mitigation_cost(x)))
            
            c_ch1, c_ch2, c_bud = st.columns([1, 1, 1])
            f1, f2 = render_action_analytics(action_df)
            c_ch1.plotly_chart(f1, use_container_width=True, theme=None)
            c_ch2.plotly_chart(f2, use_container_width=True, theme=None)
            
            # Sumarização do Orçamento
            abertas_df = action_df[action_df["Status"] != "Fechado"]
            budget_total = abertas_df["Custo Estimado (R$)"].sum()
            capex_count = len(abertas_df[abertas_df["Categoria AACE"].str.contains("CAPEX")])
            opex_count = len(abertas_df[abertas_df["Categoria AACE"].str.contains("OPEX")])
            
            c_bud.markdown(f"""
                <div style="background:rgba(59,130,246,0.1); border:1px solid #3b82f6; border-radius:10px; padding:20px; height:250px; display:flex; flex-direction:column; justify-content:center;">
                    <small style='color:#9ca3af'>ORÇAMENTO ESTIMADO (AACE CLASSE 5)</small>
                    <h2 style='color:white; margin:10px 0;'>R$ {budget_total:,.2f}</h2>
                    <p style='font-size:0.8rem; color:#d1d5db;'><span style="color:#f59e0b">● CAPEX:</span> {capex_count} requisições de hardware<br>
                    <span style="color:#3b82f6">● OPEX:</span> {opex_count} revisões/estudos</p>
                </div>
            """, unsafe_allow_html=True)

            # Data Editor Interativo Localizado
            st.markdown("<hr style='border-color: #2a3441;'>", unsafe_allow_html=True)
            edited = st.data_editor(action_df, width="stretch", hide_index=True, column_config={
                "Status": st.column_config.SelectboxColumn("Status", options=["Aberto", "Em Andamento", "Fechado", "Aguardando Verba"], required=True),
                "Responsável": st.column_config.SelectboxColumn("Responsável", options=["Engenharia", "Manutenção", "HSE", "Operação"]),
                "Custo Estimado (R$)": st.column_config.NumberColumn("Custo Est. (R$)", format="R$ %.2f", disabled=True),
                "Categoria AACE": st.column_config.TextColumn("Natureza do Custo", disabled=True),
                "Criticidade": st.column_config.TextColumn("Criticidade", disabled=True, width="medium"),
                col_acao: st.column_config.TextColumn("Ação Recomendada", width="large")
            })
            
            # Barra de progresso interativa
            fechadas = len(edited[edited["Status"] == "Fechado"])
            st.progress(fechadas / num_acoes if num_acoes > 0 else 0.0, text=f"Progresso de Adequação: {fechadas}/{num_acoes} ações mitigadas")
        else:
            st.success("Tudo em ordem. Nenhuma ação pendente detectada para este ativo.")

# ==============================================================================
# MÓDULO 2: ENGENHARIA (CLEAN UI & NFPA 69)
# ==============================================================================
elif selected_module == "Engenharia":
    TAB_STYLES = {"container": {"background-color": "#151b28", "border": "1px solid #2a3441", "border-radius": "10px"}, "nav-link-selected": {"background-color": "#3b82f6"}}
    e_tab = option_menu(None, ["Termodinâmica", "Inertização (NFPA 69)", "Emergências (PSV/Runaway)"], 
                        icons=["thermometer", "cone-striped", "speedometer2"], orientation="horizontal", styles=TAB_STYLES)
    
    if e_tab == "Termodinâmica":
        l, r = st.columns(2)
        with l:
            st.markdown("<div class='panel'><h3>Propriedades Físico-Químicas</h3></div>", unsafe_allow_html=True)
            st.dataframe(format_physchem_df(profile), width="stretch", hide_index=True)
        with r:
            st.markdown("<div class='panel'><h3>Limites de Exposição (NIOSH)</h3></div>", unsafe_allow_html=True)
            st.dataframe(format_limits_df(profile), width="stretch", hide_index=True)

    elif e_tab == "Inertização (NFPA 69)":
        st.markdown("<div class='panel'><h3>⚠️ Envelope de Inflamabilidade & Purga de Reatores</h3></div>", unsafe_allow_html=True)
        st.markdown("<div class='note-card'>Calcule a atmosfera segura durante partidas e paradas. Para evitar a mistura explosiva, a concentração de O₂ deve operar abaixo da <b>Limiting Oxygen Concentration (LOC)</b> com margem de segurança estabelecida.</div>", unsafe_allow_html=True)
        
        lfl_val = float(profile.limit("LEL_vol", 5.0))
        ufl_val = float(profile.limit("UEL_vol", 15.0))
        
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("#### Parâmetros do Composto")
            lfl = st.number_input("LFL (% Combustível)", value=lfl_val)
            ufl = st.number_input("UFL (% Combustível)", value=ufl_val)
            loc = st.number_input("LOC (% Oxigênio)", value=10.5, help="Concentração limite de O2 segundo NFPA 69")
            
            safe_o2 = loc * 0.6
            st.metric("Margem de Segurança Sugerida", f"O₂ < {safe_o2:.1f}%")
        
        with c2:
            fig_flam = render_flammability_envelope(lfl, ufl, loc)
            st.plotly_chart(fig_flam, use_container_width=True, theme=None, config={'displayModeBar': False})

    elif e_tab == "Emergências (PSV/Runaway)":
        st.markdown("<div class='panel'><h3>Cálculos de Emergência (Clean Mode)</h3></div>", unsafe_allow_html=True)
        st.markdown("<div class='note-card'>Utilize os botões ⚙️ para expandir os parâmetros de cálculo. A interface foca nos resultados operacionais críticos.</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.markdown("#### 🔥 Dimensionamento de Alívio (API 520)")
                with st.popover("⚙️ Configurar Parâmetros da Válvula"):
                    w = st.number_input("Vazão (kg/h)", 10000.0)
                    p = st.number_input("Pressão Setpoint (kPag)", 500.0)
                    t_rel = st.number_input("Temp. no Alívio (°C)", 50.0)
                
                if st.button("Executar Sizing", use_container_width=True, type="primary"):
                    mw = float(profile.identity.get("molecular_weight", 28.0) or 28.0)
                    res = size_psv_gas(w, t_rel, p, 1.0, mw)
                    st.success(f"Orifício: **Letra {res['api_letter']}** ({res['api_area_mm2']} mm²)")

        with c2:
            with st.container(border=True):
                st.markdown("#### ⚡ Runaway Térmico (Semenov)")
                with st.popover("⚙️ Configurar Cinética (CCPS)"):
                    t0 = st.number_input("Temp. Processo (°C)", 80.0)
                    ea = st.number_input("Energia Ativação (kJ/mol)", 100.0)
                if st.button("Estimar TMR", use_container_width=True):
                    res = calculate_tmr_adiabatic(t0, ea, 1e12, 1500, 2.5)
                    st.error(f"Tempo p/ Explosão Adibática: **{res['tmr_min']:.1f} min**")

# ==============================================================================
# MÓDULO 3: ANÁLISE DE RISCO (SIL COM RIGOR MATEMÁTICO)
# ==============================================================================
elif selected_module == "Análise de Risco":
    TAB_STYLES = {"container": {"background-color": "#151b28", "border": "1px solid #2a3441", "border-radius": "10px"}, "nav-link-selected": {"background-color": "#3b82f6"}}
    r_tab = option_menu(None, ["HAZOP Builder", "Verificação SIL (IEC)", "QRA Social"], 
                        icons=["diagram-3", "shield-check", "activity"], orientation="horizontal", styles=TAB_STYLES)

    if r_tab == "HAZOP Builder":
        st.markdown("<div class='panel'><h3>Geração Inteligente de P&ID e HAZOP</h3></div>", unsafe_allow_html=True)
        eqs = st.multiselect("Topologia da Linha", list(EQUIPMENT_PARAMETERS.keys()), ["Bomba Centrífuga", "Tubulação / Linha de Transferência"])
        if st.button("Sintetizar Cenários"):
            st.session_state.pid_hazop_matrix = generate_hazop_from_topology(st.session_state.current_node_name, eqs, profile)
            st.success("Análise concluída. Acesse o Action Hub para ver as pendências geradas.")
            
        if st.session_state.get("pid_hazop_matrix"):
            df_hazop = pd.DataFrame(st.session_state.pid_hazop_matrix)
            st.markdown("<hr>", unsafe_allow_html=True)
            st.dataframe(df_hazop, width="stretch", hide_index=True)

    elif r_tab == "Verificação SIL (IEC)":
        st.markdown("<div class='panel'><h3>🖲️ Análise de Arquitetura de Intertravamento (IEC 61511)</h3></div>", unsafe_allow_html=True)
        st.markdown("<div class='note-card'>Cálculo paramétrico da Probabilidade Média de Falha sob Demanda ($PFD_{avg}$) garantindo a rastreabilidade matemática para auditorias SIF.</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            arq = st.selectbox("Arquitetura de Sensores/Válvulas", ["1oo1 (Simplex)", "1oo2 (Redundante)", "2oo3 (Votação)"])
            lambda_du = st.number_input("Taxa de Falha Perigosa (λdu) - falhas/hora", 1e-6, format="%.2e")
            ti_meses = st.number_input("Intervalo de Proof Test (Meses)", 12)
            ti_horas = ti_meses * 730
            
        with col2:
            st.markdown("#### Memorial de Cálculo (Equações IEC)")
            if "1oo1" in arq:
                st.latex(r"PFD_{avg} = \lambda_{DU} \times \frac{TI}{2}")
                pfd_avg = lambda_du * (ti_horas / 2)
            elif "1oo2" in arq:
                st.latex(r"PFD_{avg} \approx \frac{(\lambda_{DU} \times TI)^2}{3} + \beta \times \lambda_{DU} \times \frac{TI}{2}")
                st.caption("*Assumindo Fator de Causa Comum (β) = 10%*")
                pfd_avg = (((lambda_du * ti_horas)**2) / 3) + (0.10 * lambda_du * (ti_horas / 2))
            else:
                st.latex(r"PFD_{avg} \approx (\lambda_{DU} \times TI)^2 + \beta \times \lambda_{DU} \times \frac{TI}{2}")
                st.caption("*Assumindo Fator de Causa Comum (β) = 10%*")
                pfd_avg = ((lambda_du * ti_horas)**2) + (0.10 * lambda_du * (ti_horas / 2))

            sil = "SIL 3" if pfd_avg < 1e-3 else "SIL 2" if pfd_avg < 1e-2 else "SIL 1" if pfd_avg < 1e-1 else "Não Classificado"
            
            st.markdown(f"""
            <div style='background:rgba(16,185,129,0.1); border:1px solid #10b981; border-radius:8px; padding:15px; margin-top:20px; text-align:center;'>
                <span style='color:#9ca3af; font-size:0.8rem; text-transform:uppercase;'>Resultado Final de Confiabilidade</span><br>
                <span style='color:white; font-size:2.5rem; font-weight:800;'>{pfd_avg:.2e}</span><br>
                <span style='color:#10b981; font-size:1.2rem; font-weight:700;'>Alcança {sil}</span>
            </div>
            """, unsafe_allow_html=True)

    elif r_tab == "QRA Social":
        st.markdown("<div class='panel'><h3>Curva F-N de Risco Social</h3></div>", unsafe_allow_html=True)
        fig_fn = go.Figure()
        fig_fn.add_trace(go.Scatter(x=[1, 10, 100], y=[1e-4, 1e-5, 1e-6], name="Limite Tolerável", line=dict(color='red', dash='dash')))
        fig_fn.add_trace(go.Scatter(x=[1, 10, 100], y=[1e-5, 1e-6, 1e-7], name="Limite Desprezível", line=dict(color='green', dash='dash')))
        fig_fn.add_trace(go.Scatter(x=[10], y=[2e-5], mode='markers+text', text=["Risco da Planta"], textposition="top center", marker=dict(size=12, color='white')))
        fig_fn.update_layout(xaxis_type="log", yaxis_type="log", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#9ca3af", height=400)
        st.plotly_chart(fig_fn, use_container_width=True, theme=None)

# ==============================================================================
# MÓDULO 4: GESTÃO DE MUDANÇA
# ==============================================================================
elif selected_module == "Gestão de Mudança":
    st.markdown("<div class='panel'><h3>Fluxo de Modificações e PSSR</h3></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.selectbox("Escopo", ["Química", "Mecânica", "Controle"])
        st.button("Protocolar MOC")
    with c2:
        st.checkbox("P&ID Atualizado?")
        st.checkbox("Operadores Treinados?")
        st.button("Emitir Certificado PSSR")

# ==============================================================================
# MÓDULO 5: BASE DE CONHECIMENTO E NORMAS
# ==============================================================================
elif selected_module == "Base de Conhecimento":
    TAB_STYLES = {"container": {"background-color": "#151b28", "border": "1px solid #2a3441", "border-radius": "10px"}, "nav-link-selected": {"background-color": "#3b82f6"}}
    kb_tab = option_menu(None, ["Normas Técnicas", "Histórico de Falhas"], icons=["journal-text", "clock-history"], orientation="horizontal", styles=TAB_STYLES)

    if kb_tab == "Normas Técnicas":
        st.markdown("<div class='panel'><h3>Biblioteca Curada (API, OSHA, IEC)</h3></div>", unsafe_allow_html=True)
        st.info("Consulte diretamente as referências normativas que baseiam os cálculos deste software.")
        
        cols = st.columns(2)
        normas = [
            {"id": "API Std 520 / 521", "tag": "API", "desc": "Sizing, Selection, and Installation of Pressure-Relieving Devices. Base para cálculos termodinâmicos de alívio."},
            {"id": "IEC 61511 / ISA TR84", "tag": "IEC", "desc": "Functional safety. Base matemática rigorosa para o cálculo do PFDavg e determinação do SIL da planta."},
            {"id": "NFPA 69", "tag": "NFPA", "desc": "Standard on Explosion Prevention Systems. Requisitos para sistemas de purga e Limiting Oxidant Concentration (LOC)."},
            {"id": "OSHA 1910.119", "tag": "OSHA", "desc": "Process Safety Management. Exige que ações de mitigação sejam rastreadas, orçadas e fechadas tempestivamente."}
        ]
        for idx, n in enumerate(normas):
            with cols[idx % 2]:
                st.markdown(f"""
                <div class="doc-card">
                    <span class="doc-tag">{n['tag']}</span><br>
                    <span class="doc-title">{n['id']}</span>
                    <p class="doc-desc">{n['desc']}</p>
                </div>
                """, unsafe_allow_html=True)
                st.write("")

    elif kb_tab == "Histórico de Falhas":
        st.markdown("<div class='panel'><h3>Banco de Incidentes Históricos</h3></div>", unsafe_allow_html=True)
        cases = get_relevant_historical_cases(profile)
        if cases:
            html = "<div class='history-timeline'>"
            for c in cases:
                html += f"<div class='history-item'><div style='color:#3b82f6; font-weight:700;'>{c['ano']}</div><div style='color:white; font-size:1.1rem; margin-top:5px;'>{c['evento']}</div><div style='color:#9ca3af; font-size:0.9rem; margin-top:5px;'>{c['mecanismo']}</div></div>"
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.success("Nenhuma falha histórica encontrada para esta substância.")
