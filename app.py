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

# NOVOS MÓDULOS SPRINT 11 A 20
from action_hub import build_consolidated_action_plan
from dashboard_engine import calculate_case_readiness_index
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
from ml_reliability_engine import calculate_dynamic_pfd
from runaway_engine import calculate_tmr_adiabatic

from streamlit_option_menu import option_menu

# CSS: Interface Vale do Silício Premium
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
.metric-box { background: rgba(30, 41, 59, 0.5); border: 1px solid var(--border-color); border-radius: 10px; padding: 15px 20px; text-align: center; display: flex; flex-direction: column; justify-content: center; min-height: 125px; }
.metric-label { color: #9ca3af; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }
.metric-value { color: #f9fafb; font-size: 2rem; font-weight: 800; margin-top: 8px; font-variant-numeric: tabular-nums; line-height: 1.1; }
.risk-blue { color: var(--accent-blue); } .risk-green { color: #10b981; } .risk-amber { color: #f59e0b; } .risk-red { color: #ef4444; }
.note-card { background: rgba(59, 130, 246, 0.08); border-left: 4px solid var(--accent-blue); padding: 15px; border-radius: 6px; font-size: 0.9rem; margin-bottom: 20px; color: #bfdbfe; line-height: 1.5; }
.history-card { background: rgba(22, 27, 34, 0.8); border-left: 4px solid #d29922; padding: 15px; border-radius: 8px; margin-bottom: 15px; }
.stExpander { border: 1px solid var(--border-color) !important; border-radius: 10px !important; background: var(--card-bg) !important; overflow: hidden; }
</style>
"""

st.set_page_config(page_title="ChemSafe Pro Enterprise", page_icon="⚗️", layout="wide", initial_sidebar_state="expanded")
st.markdown(APP_CSS, unsafe_allow_html=True)

# ==============================================================================
# FUNÇÕES PLOTLY EMBUTIDAS
# ==============================================================================
def render_modern_gauge(score, band):
    color = "#10b981" if score >= 80 else "#f59e0b" if score >= 50 else "#ef4444"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={'suffix': "%", 'font': {'color': "white", 'size': 45}},
        title={'text': f"Status Atual:<br><span style='font-size:1.4em; color:{color}; font-weight:800;'>{band}</span>", 'font': {'color': "#9ca3af", 'size': 14}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#30363d"},
            'bar': {'color': color},
            'bgcolor': "rgba(255,255,255,0.05)",
            'borderwidth': 0,
            'steps': [{'range': [0, 50], 'color': "rgba(239, 68, 68, 0.15)"}, {'range': [50, 80], 'color': "rgba(245, 158, 11, 0.15)"}, {'range': [80, 100], 'color': "rgba(16, 185, 129, 0.15)"}]
        }
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'family': "Inter"}, margin=dict(t=50, b=10, l=10, r=10), height=300)
    return fig

def render_modern_radar(cri_data):
    base = cri_data.get('index', 50)
    categories = ['Engenharia e Dados', 'Análise de Perigos', 'LOPA & Barreiras', 'MOC & Governança']
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

MENU_STYLES = {
    "container": {"padding": "5px", "background-color": "#151b28", "border": "1px solid #2a3441", "border-radius": "10px", "margin-bottom": "20px"},
    "icon": {"color": "#9ca3af", "font-size": "16px"},
    "nav-link": {"font-size": "14px", "text-align": "center", "margin": "0px", "color": "#9ca3af", "font-weight": "500", "font-family": "Inter"},
    "nav-link-selected": {"background-color": "#3b82f6", "color": "white", "font-weight": "600"},
}

# =========================
# Estado da sessão
# =========================
if "lang" not in st.session_state: st.session_state.lang = "pt"
if "selected_compound_key" not in st.session_state: st.session_state.selected_compound_key = "ammonia"
if "profile" not in st.session_state: st.session_state.profile = None
if "lopa_result" not in st.session_state: st.session_state.lopa_result = None
if "pid_hazop_matrix" not in st.session_state: st.session_state.pid_hazop_matrix = []
if "current_node_name" not in st.session_state: st.session_state.current_node_name = "Nó 101: Bomba de Recalque"
if "current_case_name" not in st.session_state: st.session_state.current_case_name = ""
if "current_case_notes" not in st.session_state: st.session_state.current_case_notes = ""
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
    if query_hint: st.session_state.profile = build_compound_profile(query_hint)
    st.session_state.current_case_name = case_data.get("case_name", "")
    st.session_state.lopa_result = case_data.get("lopa_result")

# =========================
# Sidebar & Navegação
# =========================
with st.sidebar:
    lang = st.radio("🌐 Idioma", ["pt", "en"], horizontal=True, label_visibility="collapsed")
    st.session_state.lang = lang
    
    st.markdown(f"## ⚗️ {t('app_title', lang)}\n**Enterprise Edition**")
    st.caption("Process Safety Intelligence Engine")
    st.markdown("---")
    
    selected_module = option_menu(
        menu_title=None,
        options=["Visão Executiva", "Engenharia", "Análise de Risco", "Mudanças"],
        icons=["speedometer2", "cpu", "shield-lock", "arrow-repeat"],
        default_index=0,
        styles={
            "container": {"background-color": "transparent", "padding": "0"},
            "nav-link": {"font-size": "14px", "color": "#d1d5db", "margin":"5px 0"},
            "nav-link-selected": {"background-color": "#3b82f6", "color": "white"},
        }
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

# BREADCRUMB DE CONTEXTO
st.markdown(f"""
<div class="context-header">
    <div>🧪 Ativo Analisado: <span>{profile.identity.get('name', 'N/A')} (CAS: {profile.identity.get('cas', 'N/A')})</span></div>
    <div>🏭 Topologia Foco: <span>{st.session_state.current_node_name}</span></div>
</div>
""", unsafe_allow_html=True)

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
# MÓDULO 1: VISÃO EXECUTIVA (COM NOVO ACTION PLAN INTERATIVO)
# ==============================================================================
if selected_module == "Visão Executiva":
    exec_tab = option_menu(
        menu_title=None,
        options=["Dashboard Global", "Action Plan", "Relatório Automático", "Meus Projetos"],
        icons=["bar-chart", "list-check", "file-earmark-pdf", "folder2-open"],
        default_index=0, orientation="horizontal", styles=MENU_STYLES
    )

    if exec_tab == "Dashboard Global":
        st.markdown("<div class='panel'><h3>KPIs Executivos</h3></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.markdown(metric_card("Maturidade Global", f"{cri_data['index']}%", cri_data['color_class']), unsafe_allow_html=True)
        c2.markdown(metric_card("Ações Pendentes", str(len(action_df_dash)), "risk-amber" if len(action_df_dash) > 0 else "risk-green"), unsafe_allow_html=True)
        gaps_criticos = len(action_df_dash[action_df_dash["Criticidade"].isin(["Alta", "Crítica"])]) if not action_df_dash.empty else 0
        c3.markdown(metric_card("Gaps Críticos", str(gaps_criticos), "risk-red" if gaps_criticos > 0 else "risk-green"), unsafe_allow_html=True)
        
        left, right = st.columns(2)
        with left:
            st.markdown("<div class='panel'><h3>Índice de Prontidão do Caso (CRI)</h3></div>", unsafe_allow_html=True)
            st.plotly_chart(render_modern_gauge(cri_data['index'], cri_data['band']), use_container_width=True, theme=None, config={'displayModeBar': False})
        with right:
            st.markdown("<div class='panel'><h3>Distribuição por Pilares</h3></div>", unsafe_allow_html=True)
            st.plotly_chart(render_modern_radar(cri_data), use_container_width=True, theme=None, config={'displayModeBar': False})

    elif exec_tab == "Action Plan":
        st.markdown("<div class='panel'><h3>Hub de Ações Interativo (Em Atendimento à OSHA 1910.119 e CCPS)</h3></div>", unsafe_allow_html=True)
        st.markdown("<div class='note-card'><b>Governança de Risco:</b> Acompanhe, delegue e feche as recomendações extraídas de HAZOP, LOPA e MOC garantindo a Hierarquia de Controles do NIOSH.</div>", unsafe_allow_html=True)
        
        if not action_df_dash.empty:
            # INJEÇÃO DAS COLUNAS DE AUDITORIA (Se não existirem)
            if "Status" not in action_df_dash.columns: action_df_dash["Status"] = "Aberto"
            action_df_dash["Responsável"] = "Engenharia"
            action_df_dash["Prazo"] = "30 Dias"
            
            # Lógica simples de AI Classifier para Hierarquia de Controle
            def classify_hierarchy(action_text):
                text = str(action_text).lower()
                if "instalar" in text or "válvula" in text or "psv" in text or "sis" in text: return "Engenharia (Hardware)"
                elif "revisar" in text or "treinar" in text or "procedimento" in text: return "Administrativo"
                return "Mitigação"
                
            action_df_dash["Hierarquia NIOSH"] = action_df_dash["Ação Recomendada"].apply(classify_hierarchy)

            # DATA EDITOR: Permite edição direto na tela (Silicon Valley Style)
            edited_df = st.data_editor(
                action_df_dash,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Status": st.column_config.SelectboxColumn("Status", options=["Aberto", "Em Andamento", "Aguardando Verba", "Fechado"], required=True),
                    "Responsável": st.column_config.SelectboxColumn("Responsável", options=["Engenharia", "Manutenção", "Operação", "HSE"]),
                    "Criticidade": st.column_config.TextColumn("Criticidade", disabled=True),
                    "Ação Recomendada": st.column_config.TextColumn("Ação Recomendada", disabled=True, width="large"),
                    "Hierarquia NIOSH": st.column_config.TextColumn("Hierarquia (Auto)", disabled=True)
                }
            )
            
            # KPI Dinâmico de Fechamento
            fechadas = len(edited_df[edited_df["Status"] == "Fechado"])
            total = len(edited_df)
            progresso = fechadas / total if total > 0 else 0.0
            st.markdown(f"**Progresso de Resolução de Ações: {fechadas}/{total}**")
            st.progress(progresso)
            
            # Exportar plano atualizado para o CMMS/SAP
            st.download_button("📥 Exportar Plano de Ação para SAP/Maximo (CSV)", edited_df.to_csv(index=False).encode('utf-8'), "action_plan.csv", "text/csv")
        else:
            st.info("Nenhuma ação de segurança pendente no momento. A planta está de acordo com as especificações base.")

    elif exec_tab == "Relatório Automático":
        st.markdown("<div class='panel'><h3>Gerador de Relatório Executivo</h3></div>", unsafe_allow_html=True)
        report_case_name = st.text_input("Nome do Relatório", value=st.session_state.current_case_name or profile.identity.get("name", "Caso"))
        if st.button("Gerar Relatório Completo", type="primary"):
            st.session_state.report_bundle = build_executive_bundle(
                case_name=report_case_name, profile=profile,
                context={"lopa_result": st.session_state.get("lopa_result")}
            )
            st.success("Relatório Compilado!")
        if st.session_state.get("report_bundle"):
            st.download_button("📥 Baixar Documento (HTML)", st.session_state.report_bundle["html"], file_name=f"{report_case_name}.html")

    elif exec_tab == "Meus Projetos":
        st.markdown("<div class='panel'><h3>Gestão de Projetos</h3></div>", unsafe_allow_html=True)
        col_save, col_load = st.columns(2)
        with col_save:
            case_name = st.text_input("Salvar Projeto Atual Como:")
            if st.button("Salvar Progresso", type="primary"):
                save_case(case_name, profile, "", st.session_state.get("lopa_result"), [], bowtie_payload(), None, None, None)
                st.session_state.current_case_name = case_name
                st.success("Salvo com segurança!")
        cases = list_cases()
        if cases:
            with col_load:
                selected_case = st.selectbox("Carregar Projeto Existente", [c["case_name"] for c in cases])
                if st.button("Carregar Projeto"):
                    apply_loaded_case(load_case(selected_case))
                    st.rerun()

# ==============================================================================
# MÓDULO 2: ENGENHARIA DE DADOS
# ==============================================================================
elif selected_module == "Engenharia":
    eng_tab = option_menu(
        menu_title=None,
        options=["Termodinâmica", "Cinética Térmica", "Sizing API 520", "Banco de Casos"],
        icons=["thermometer", "fire", "speedometer2", "archive"],
        default_index=0, orientation="horizontal", styles=MENU_STYLES
    )
    
    if eng_tab == "Termodinâmica":
        dispersion_mode = classify_dispersion_mode(profile)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(metric_card("Ativo Base", profile.identity.get("name", "—")), unsafe_allow_html=True)
        c2.markdown(metric_card("Peso Molar", f"{profile.identity.get('molecular_weight', '—')} g/mol"), unsafe_allow_html=True)
        c3.markdown(metric_card("Dispersão", dispersion_mode["label"]), unsafe_allow_html=True)
        c4.markdown(metric_card("Confiança", f"{profile.confidence_score:.0f}%"), unsafe_allow_html=True)
            
        left, right = st.columns(2)
        with left:
            st.markdown("<div class='panel'><h3>Identidade e Perigos GHS</h3></div>", unsafe_allow_html=True)
            st.dataframe(format_identity_df(profile), use_container_width=True, hide_index=True)
            for hz in profile.hazards: st.error(hz)
        with right:
            st.markdown("<div class='panel'><h3>Propriedades Base</h3></div>", unsafe_allow_html=True)
            st.dataframe(format_physchem_df(profile), use_container_width=True, hide_index=True)

    elif eng_tab == "Cinética Térmica":
        st.markdown("<div class='panel'><h3>🔥 Simulação de Runaway Térmico (Semenov)</h3></div>", unsafe_allow_html=True)
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

    elif eng_tab == "Sizing API 520":
        st.markdown("<div class='panel'><h3>🧮 Dimensionamento Válvula API 520</h3></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: w_req = st.number_input("Vazão Requerida (kg/h)", value=10000.0)
        with c2: p_rel = st.number_input("Pressão de Setpoint (kPag)", value=500.0)
        with c3: t_rel = st.number_input("Temp. no Alívio (°C)", value=50.0)
        if st.button("Dimensionar Orifício", type="primary"):
            mw = float(profile.identity.get("molecular_weight", 28.0) or 28.0)
            psv_res = size_psv_gas(W_kg_h=w_req, T_C=t_rel, P1_kPag=p_rel, Z=1.0, MW=mw)
            st.success(f"**Orifício Padrão API:** Letra {psv_res['api_letter']} ({psv_res['api_area_mm2']} mm²)")

    elif eng_tab == "Banco de Casos":
        st.markdown("<div class='panel'><h3>📚 Banco de Acidentes Curado</h3></div>", unsafe_allow_html=True)
        relevant_cases = get_relevant_historical_cases(profile)
        if relevant_cases:
            for case in relevant_cases[:2]:
                st.markdown(f"<div class='history-card'><b>{case['evento']} ({case['ano']})</b><br>Mecanismo: {case['mecanismo']}</div>", unsafe_allow_html=True)
        else:
            st.info("Nenhum evento correlato crítico encontrado.")

# ==============================================================================
# MÓDULO 3: ANÁLISE DE RISCO
# ==============================================================================
elif selected_module == "Análise de Risco":
    risk_tab = option_menu(
        menu_title=None,
        options=["P&ID Visual Builder", "HAZOP & Automação", "ML-LOPA & Humanos", "Mapas & Zonas"],
        icons=["diagram-3", "table", "shield-lock", "geo-alt"],
        default_index=0, orientation="horizontal", styles=MENU_STYLES
    )

    if risk_tab == "P&ID Visual Builder":
        st.markdown("<div class='panel'><h3>🏗️ Construtor Visual P&ID</h3></div>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["Nó Único (Grafo)", "Lote Múltiplos Nós (CSV)"])
        
        with t1:
            col1, col2 = st.columns([1, 2])
            with col1: st.session_state.current_node_name = st.text_input("Identificação do Nó", value=st.session_state.current_node_name)
            with col2: selected_equipment = st.multiselect("Equipamentos e Linhas (Em Ordem)", options=list(EQUIPMENT_PARAMETERS.keys()), default=["Tanque de Armazenamento Atmosférico", "Tubulação / Linha de Transferência", "Bomba Centrífuga"])
                
            if selected_equipment:
                dot = graphviz.Digraph()
                dot.attr(rankdir='LR', bgcolor='transparent')
                dot.attr('node', shape='box', style='filled', fillcolor='#1e293b', color='#3b82f6', fontcolor='white', fontname='Inter', penwidth='2')
                dot.attr('edge', color='#9ca3af', penwidth='2')
                for i, eq in enumerate(selected_equipment):
                    dot.node(str(i), eq)
                    if i > 0: dot.edge(str(i-1), str(i))
                st.graphviz_chart(dot, use_container_width=True)

            if st.button("🚀 Consolidar Topologia em HAZOP", type="primary"):
                st.session_state.pid_hazop_matrix = generate_hazop_from_topology(st.session_state.current_node_name, selected_equipment, profile)
                st.success("Grafo processado! Avance para a aba HAZOP & Automação.")
                
        with t2:
            st.markdown("<div class='note-card'>Importe a Equipment List extraída do seu CAD (Nó, Equipamento).</div>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader("Upload CSV/XLSX", type=["csv", "xlsx"])
            if uploaded_file is not None:
                df_bulk = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                if st.button("⚡ Executar Processamento em Lote", type="primary"):
                    bulk_results = process_bulk_pid_nodes(df_bulk, profile)
                    if bulk_results:
                        st.session_state.pid_hazop_matrix = bulk_results
                        st.success(f"{len(bulk_results)} cenários gerados para a fábrica inteira.")

    elif risk_tab == "HAZOP & Automação":
        st.markdown("<div class='panel'><h3>Matrizes de Engenharia Geradas</h3></div>", unsafe_allow_html=True)
        if st.session_state.get("pid_hazop_matrix"):
            df_hazop = pd.DataFrame(st.session_state.pid_hazop_matrix)
            
            with st.expander("📋 Estudo HAZOP (IEC 61882)", expanded=True):
                view_mode = st.radio("Modo de Leitura:", ["🗂️ Cards (Discussão de Reunião)", "📊 Tabela Otimizada (Text Wrap)"], horizontal=True, label_visibility="collapsed")
                st.markdown("<br>", unsafe_allow_html=True)

                if "Cards" in view_mode:
                    for index, row in df_hazop.iterrows():
                        st.markdown(f"""
                        <div style="background-color: rgba(30, 41, 59, 0.4); border: 1px solid #374151; border-left: 4px solid #3b82f6; border-radius: 8px; padding: 15px; margin-bottom: 15px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                <span style="color: #9ca3af; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">{row['Nó']}</span>
                                <span style="background-color: rgba(59, 130, 246, 0.2); color: #60a5fa; padding: 2px 8px; border-radius: 4px; font-size: 0.85rem; font-weight: 600;">{row['Palavra-Guia']} {row['Parâmetro']}</span>
                            </div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 10px;">
                                <div><strong style="color: #f87171; font-size: 0.9rem;">⚠️ Causa:</strong><br><span style="color: #d1d5db; font-size: 0.95rem;">{row['Causa']}</span></div>
                                <div><strong style="color: #f87171; font-size: 0.9rem;">💥 Consequência:</strong><br><span style="color: #d1d5db; font-size: 0.95rem;">{row['Consequência']}</span></div>
                            </div>
                            <div style="background-color: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); padding: 10px; border-radius: 6px;">
                                <strong style="color: #34d399; font-size: 0.9rem;">🛡️ Salvaguardas:</strong><br><span style="color: #d1d5db; font-size: 0.95rem;">{row['Salvaguarda Atual']}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.dataframe(
                        df_hazop, use_container_width=True, hide_index=True,
                        column_config={
                            "Nó": st.column_config.TextColumn("Nó", width="medium"),
                            "Causa": st.column_config.TextColumn("Causa", width="large"),
                            "Consequência": st.column_config.TextColumn("Consequência", width="large"),
                            "Salvaguarda Atual": st.column_config.TextColumn("Salvaguarda", width="medium"),
                        }
                    )
                st.download_button("📥 Exportar CSV", df_hazop.to_csv(index=False).encode('utf-8'), "hazop_export.csv", "text/csv")
            
            with st.expander("🔀 Matriz Causa e Efeito p/ Automação (IEC 61511)", expanded=False):
                df_ce = generate_ce_matrix_from_hazop(st.session_state.pid_hazop_matrix)
                if not df_ce.empty: 
                    st.dataframe(df_ce, use_container_width=True, hide_index=True)
                    st.download_button("📥 Exportar C&E", df_ce.to_csv(index=False).encode('utf-8'), "ce_matrix.csv", "text/csv")
                else: 
                    st.info("Nenhuma arquitetura de Trip (Intertravamento) foi deduzida dos cenários atuais.")
        else:
            st.warning("Gere os cenários no P&ID Builder primeiro.")

    elif risk_tab == "ML-LOPA & Humanos":
        st.markdown("<div class='panel'><h3>🛡️ Confiabilidade Dinâmica e Erro Humano</h3></div>", unsafe_allow_html=True)
        c_ml, c_hra, c_lopa = st.columns([1, 1, 1.2])
        
        with c_ml:
            st.markdown("#### 🤖 ML/OREDA Wear-Out")
            eq_type = st.selectbox("Equipamento Analisado", ["Bomba de Resfriamento", "Válvula de Bloqueio"])
            t_meses = st.slider("Meses de Uso", 1, 60, 24)
            anomaly = st.slider("Anomalia Preditiva", 0.0, 1.0, 0.2)
            dyn_res = calculate_dynamic_pfd(1e-2 if "Bomba" in eq_type else 1e-3, t_meses, anomaly, eq_type)
            st.metric("PFD Ajustado", dyn_res["pfd_str"], f"+{dyn_res['risk_increase_pct']:.0f}% Degradação", delta_color="inverse")
            
        with c_hra:
            st.markdown("#### 🧠 HRA (THERP NUREG)")
            t_av = st.selectbox("Tempo de Resposta", ["Menos de 5 minutos", "5 a 10 minutos"])
            stress = st.selectbox("Carga de Estresse", ["Extremo (Emergência)", "Nominal"])
            if st.button("Estimar Erro (HEP)"):
                hra_res = calculate_human_error_probability(t_av, stress, "Alta (Múltiplas válvulas/painéis)")
                st.success(f"**HEP:** {hra_res['pfd_equivalent']}")
                
        with c_lopa:
            st.markdown("#### 📊 LOPA Integrado")
            f_ie = st.number_input("Freq. Inicial (1/ano)", value=0.1, format="%.3f")
            opcoes_ipl = [f"{n} (PFD={p})" for n, p in IPL_CATALOG]
            opcoes_ipl.append(f"{eq_type} Degradada (PFD={dyn_res['dynamic_pfd']:.1e})")
            selected_ipls = st.multiselect("Adicionar Camadas (IPLs)", opcoes_ipl)
            if st.button("Computar Risco Mitigado", type="primary"):
                chosen_pfds = [("Barreira", float(lbl.split("PFD=")[1].replace(")", ""))) for lbl in selected_ipls if "PFD=" in lbl]
                st.session_state.lopa_result = compute_lopa(f_ie, 1e-4, chosen_pfds)
                st.info(f"Freq. Residual (MCF): **{st.session_state.lopa_result['mcf']:.2e}/ano**")

    elif risk_tab == "Mapas & Zonas":
        st.markdown("<div class='panel'><h3>🗺️ Facility Siting e Zonas de Impacto</h3></div>", unsafe_allow_html=True)
        
        with st.expander("🔥 API 521: Avaliação de Efeito Dominó Térmico", expanded=True):
            d1, d2, d3 = st.columns(3)
            with d1: dist = st.number_input("Distância ao Alvo Crítico (m)", value=15.0)
            with d2: m_rate = st.number_input("Vazão do Inventário (kg/s)", value=10.0)
            with d3: hc = st.number_input("Calor de Combustão (MJ/kg)", value=44.0)
            if st.button("Computar Falha Induzida"):
                domino = calculate_domino_effect(dist, m_rate, hc * 1e6)
                st.error(f"**{domino['status']}** | Carga Térmica: {domino['q_kW_m2']:.2f} kW/m²")
        
        with st.expander("🏭 Projeção 2D na Planta Baixa (Plotly)", expanded=False):
            layout_file = st.file_uploader("Upload da Planta (PNG/JPG)", type=["png", "jpg", "jpeg"])
            lc1, lc2, lc3 = st.columns(3)
            with lc1: scale_m = st.number_input("Escala: Metros por Pixel?", value=0.1, format="%.3f")
            with lc2: ox = st.number_input("Origem (Pixel X)", value=500)
            with lc3: oy = st.number_input("Origem (Pixel Y)", value=500)
            
            if layout_file and st.button("Gerar Heatmap na Planta", type="primary"):
                try:
                    zonas_exemplo = [
                        {"radius_m": 15.0, "color": "darkred", "label": "Letal / Ruptura"},
                        {"radius_m": 30.0, "color": "orange", "label": "Perda de Controle"},
                        {"radius_m": 60.0, "color": "yellow", "label": "Zona de Restrição"}
                    ]
                    fig_layout = build_plant_layout_heatmap(layout_file, scale_m, int(ox), int(oy), zonas_exemplo)
                    st.plotly_chart(fig_layout, use_container_width=True, theme=None)
                except Exception as e:
                    st.error(f"Erro ao processar o Layout 2D. Tente um formato de imagem menor.")

# ==============================================================================
# MÓDULO 4: GESTÃO DE MUDANÇA
# ==============================================================================
elif selected_module == "Mudanças":
    chg_tab = option_menu(
        menu_title=None,
        options=["MOC (Modificação)", "PSSR (Inspeção Pré-Partida)"],
        icons=["arrow-repeat", "check2-square"],
        default_index=0, orientation="horizontal", styles=MENU_STYLES
    )

    if chg_tab == "MOC (Modificação)":
        st.markdown("<div class='panel'><h3>🔄 Avaliação de Gestão de Mudança</h3></div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            change_type = st.selectbox("Escopo da Mudança", ["Mudança química", "Mudança de equipamento", "Mudança de procedimento"])
            impacts = st.multiselect("Áreas Críticas Afetadas", ["Química / composição", "Pressão", "Temperatura", "Alívio / PSV"])
        with c2:
            st.write("Fatores Restritivos:")
            p1 = st.checkbox("Mudança de Caráter Temporário")
            p2 = st.checkbox("Bypass ou Override em Sistema de Segurança")
        if st.button("Protocolar MOC para Análise", type="primary"):
            st.session_state.moc_result = evaluate_moc(profile, change_type, impacts, "", temporary=p1, protections_changed=p2, bypass_or_override=False)
            st.success("MOC Submetido e Classificado.")

    elif chg_tab == "PSSR (Inspeção Pré-Partida)":
        st.markdown("<div class='panel'><h3>✅ Checklist de Partida Segura</h3></div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            d1 = st.checkbox("Construção validada conforme diagrama P&ID")
            d2 = st.checkbox("Procedimentos de emergência revisados e na sala de controle")
        with c2:
            d4 = st.checkbox("Malhas do SIS e PSVs inspecionadas e destravadas")
            d5 = st.checkbox("Matriz de Causa e Efeito validada em TAF (Teste de Aceitação)")
        if st.button("Rodar Assinatura PSSR", type="primary"):
            st.session_state.pssr_result = evaluate_pssr(design_ok=d1, procedures_ok=d2, training_ok=True, relief_verified=d4, alarms_tested=d5, startup_authorized=True, pha_or_moc_ok=True, mi_ready=True, emergency_ready=True, scope_label="PSSR")
            st.success("Status Operacional Emitido.")
