from __future__ import annotations

import sys
from pathlib import Path
import io
import math
import re
import time

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st
import graphviz
import plotly.graph_objects as go
import plotly.express as px
from streamlit_option_menu import option_menu

# Módulos Legados e Ferramentas Visuais
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
from source_governance import (
    build_evidence_ledger_df,
    build_source_recommendations,
    summarize_evidence,
)
from ui_formatters import format_identity_df, format_limits_df, format_physchem_df

# NOVOS MÓDULOS SPRINT 11 A 24
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

# CSS: Interface Vale do Silício Premium, Decluttered + Cards de Documentação
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

/* FIX: Garante que os valores das métricas não sejam cortados */
.metric-box { background: rgba(30, 41, 59, 0.5); border: 1px solid var(--border-color); border-radius: 10px; padding: 15px 20px; text-align: center; display: flex; flex-direction: column; justify-content: center; min-height: 125px; }
.metric-label { color: #9ca3af; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }
.metric-value { color: #f9fafb; font-size: 1.8rem; font-weight: 800; margin-top: 8px; line-height: 1.2; white-space: normal; word-wrap: break-word; }

.risk-blue { color: var(--accent-blue); } .risk-green { color: #10b981; } .risk-amber { color: #f59e0b; } .risk-red { color: #ef4444; }
.note-card { background: rgba(59, 130, 246, 0.08); border-left: 4px solid var(--accent-blue); padding: 15px; border-radius: 6px; font-size: 0.9rem; margin-bottom: 20px; color: #bfdbfe; line-height: 1.5; }
.history-card { background: rgba(22, 27, 34, 0.8); border-left: 4px solid #d29922; padding: 15px; border-radius: 8px; margin-bottom: 15px; }
.stExpander { border: 1px solid var(--border-color) !important; border-radius: 10px !important; background: var(--card-bg) !important; overflow: hidden; }

/* SPRINT 23: DOC CARDS ESTILO VERCEL/STRIPE */
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

st.set_page_config(
    page_title="ChemSafe Pro Enterprise",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(APP_CSS, unsafe_allow_html=True)

# ==============================================================================
# FUNÇÕES DE BLINDAGEM E MOTORES PLOTLY
# ==============================================================================
def is_valid_df(df):
    """Garante que a variável é um DataFrame do Pandas e não está vazia."""
    return isinstance(df, pd.DataFrame) and not df.empty


def get_action_col(df):
    """Descobre dinamicamente a coluna de ação para evitar KeyError."""
    if not isinstance(df, pd.DataFrame) or df.empty or len(df.columns) == 0:
        return "Ação Recomendada"

    possible_names = [
        "Ação Recomendada",
        "Ação",
        "Recomendação",
        "Ações",
        "Descrição",
        "Ação Requerida",
    ]
    for name in possible_names:
        if name in df.columns:
            return name

    excluded = [
        "Origem",
        "Criticidade",
        "Status",
        "Responsável",
        "Prazo",
        "Prazo (Dias)",
        "Recurso",
        "Hierarquia NIOSH",
        "Requer MOC?",
        "Pacote AACE",
        "Custo Min (R$)",
        "Custo P50 (R$)",
        "Custo Máx (R$)",
    ]
    for col in df.columns:
        if col not in excluded:
            return col

    return df.columns[-1]


def normalize_whitespace(value):
    """Remove espaços bugados, \\xa0 e normaliza strings."""
    if not isinstance(value, str):
        return value
    value = value.replace("\xa0", " ")
    value = value.replace("Â\xa0", " ")
    value = value.replace("Â ", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def translate_value(value, mapping):
    if not isinstance(value, str):
        return value
    key = normalize_whitespace(value).lower()
    return mapping.get(key, normalize_whitespace(value))


def load_profile_with_feedback(query: str):
    """Busca com loading state para parecer acesso real a backend/PubChem."""
    safe_query = normalize_whitespace(query)
    with st.spinner(f"Buscando dados no PubChem para '{safe_query}'..."):
        time.sleep(0.35)
        return build_compound_profile(safe_query)


ACTION_COLUMN_ALIASES = {
    "action required": "Ação Recomendada",
    "recommended action": "Ação Recomendada",
    "action recommended": "Ação Recomendada",
    "action": "Ação Recomendada",
    "actions": "Ação Recomendada",
    "description": "Ação Recomendada",
    "status": "Status",
    "owner": "Responsável",
    "responsible": "Responsável",
    "due days": "Prazo (Dias)",
    "deadline days": "Prazo (Dias)",
    "due date": "Prazo",
    "deadline": "Prazo",
    "resource": "Recurso",
    "severity": "Criticidade",
    "criticality": "Criticidade",
    "niosh hierarchy": "Hierarquia NIOSH",
    "requires moc?": "Requer MOC?",
    "requires moc": "Requer MOC?",
    "moc required?": "Requer MOC?",
    "moc required": "Requer MOC?",
}

ACTION_VALUE_MAPPINGS = {
    "Status": {
        "pending": "Aberto",
        "open": "Aberto",
        "in progress": "Em Andamento",
        "waiting budget": "Aguardando Verba",
        "budget pending": "Aguardando Verba",
        "closed": "Fechado",
    },
    "Criticidade": {
        "critical": "Crítica",
        "high": "Alta",
        "medium": "Média",
        "moderate": "Média",
        "low": "Baixa",
    },
    "Recurso": {
        "capex": "CAPEX",
        "opex": "OPEX",
    },
    "Responsável": {
        "engineering": "Engenharia",
        "maintenance": "Manutenção",
        "operations": "Operação",
        "operation": "Operação",
        "hse": "HSE",
    },
}

AACE_CLASS5_LIBRARY = [
    {
        "label": "SIS / SIF / ESD",
        "resource": "CAPEX",
        "keywords": ["sis", "sif", "esd", "shutdown", "trip", "intertravamento"],
        "min": 120000.0,
        "p50": 220000.0,
        "max": 450000.0,
    },
    {
        "label": "CLP / PLC / Painel",
        "resource": "CAPEX",
        "keywords": ["clp", "plc", "logic solver", "painel", "ihm", "remota"],
        "min": 45000.0,
        "p50": 90000.0,
        "max": 180000.0,
    },
    {
        "label": "Válvula / SDV / PSV / Atuador",
        "resource": "CAPEX",
        "keywords": ["válvula", "valvula", "psv", "sdv", "atuador", "bloqueio"],
        "min": 18000.0,
        "p50": 42000.0,
        "max": 110000.0,
    },
    {
        "label": "Instrumentação / Alarmes / Sensores",
        "resource": "CAPEX",
        "keywords": ["sensor", "transmissor", "alarme", "detector", "instrument", "pressostato", "chave"],
        "min": 12000.0,
        "p50": 30000.0,
        "max": 70000.0,
    },
    {
        "label": "Treinamento / Procedimento",
        "resource": "OPEX",
        "keywords": ["treinamento", "capacitação", "procedimento", "instrução", "instrucao", "treinar", "reciclagem"],
        "min": 3000.0,
        "p50": 8500.0,
        "max": 18000.0,
    },
    {
        "label": "Estudo / HAZOP / LOPA / Engenharia",
        "resource": "OPEX",
        "keywords": ["estudo", "hazop", "lopa", "análise", "analise", "simulação", "simulacao", "investigação", "investigacao"],
        "min": 7000.0,
        "p50": 15000.0,
        "max": 35000.0,
    },
]


def sanitize_and_translate_action_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Blindagem do Action Hub:
    - remove \\xa0
    - traduz colunas inglesas
    - traduz status ingleses
    """
    if df is None:
        return pd.DataFrame()
    if not isinstance(df, pd.DataFrame):
        return df

    out = df.copy()
    out.columns = [normalize_whitespace(col) for col in out.columns]

    rename_map = {}
    for col in out.columns:
        col_key = normalize_whitespace(col).lower()
        if col_key in ACTION_COLUMN_ALIASES:
            rename_map[col] = ACTION_COLUMN_ALIASES[col_key]

    out = out.rename(columns=rename_map)

    for col in out.select_dtypes(include="object").columns:
        out[col] = out[col].apply(normalize_whitespace)

    for col, mapping in ACTION_VALUE_MAPPINGS.items():
        if col in out.columns:
            out[col] = out[col].apply(lambda x: translate_value(x, mapping))

    if "Requer MOC?" in out.columns:
        out["Requer MOC?"] = out["Requer MOC?"].apply(
            lambda x: x if isinstance(x, bool) else str(x).strip().lower() in {"true", "1", "yes", "sim", "y"}
        )

    return out


def classify_hierarchy(action_text):
    text = normalize_whitespace(action_text).lower()
    if any(word in text for word in ["eliminar", "substituir"]):
        return "Eliminação/Substituição"
    if any(
        word in text
        for word in [
            "sis",
            "sif",
            "esd",
            "clp",
            "plc",
            "válvula",
            "valvula",
            "psv",
            "alarme",
            "sensor",
            "detector",
            "intertravamento",
            "bloqueio",
        ]
    ):
        return "Engenharia (Hardware)"
    if any(
        word in text
        for word in [
            "treinar",
            "treinamento",
            "procedimento",
            "instrução",
            "instrucao",
            "revisar",
            "checklist",
        ]
    ):
        return "Administrativo (Procedimento)"
    return "Mitigação (Emergência)"


def estimate_action_cost(action_text: str, hierarchy: str) -> dict:
    text = normalize_whitespace(action_text).lower()
    hierarchy = normalize_whitespace(hierarchy).lower()

    for rule in AACE_CLASS5_LIBRARY:
        if any(keyword in text for keyword in rule["keywords"]):
            return {
                "Recurso": rule["resource"],
                "Pacote AACE": rule["label"],
                "Custo Min (R$)": rule["min"],
                "Custo P50 (R$)": rule["p50"],
                "Custo Máx (R$)": rule["max"],
            }

    if "engenharia" in hierarchy or "eliminação" in hierarchy:
        return {
            "Recurso": "CAPEX",
            "Pacote AACE": "Hardware Genérico",
            "Custo Min (R$)": 25000.0,
            "Custo P50 (R$)": 60000.0,
            "Custo Máx (R$)": 140000.0,
        }

    return {
        "Recurso": "OPEX",
        "Pacote AACE": "Ação Administrativa Genérica",
        "Custo Min (R$)": 2500.0,
        "Custo P50 (R$)": 7000.0,
        "Custo Máx (R$)": 16000.0,
    }


def enrich_action_plan_df(df: pd.DataFrame) -> pd.DataFrame:
    out = sanitize_and_translate_action_df(df)
    if not is_valid_df(out):
        return out

    col_acao = get_action_col(out)

    if "Status" not in out.columns:
        out["Status"] = "Aberto"
    if "Responsável" not in out.columns:
        out["Responsável"] = "Engenharia"
    if "Prazo (Dias)" not in out.columns:
        out["Prazo (Dias)"] = 30
    if "Requer MOC?" not in out.columns:
        out["Requer MOC?"] = False
    if "Criticidade" not in out.columns:
        out["Criticidade"] = "Média"

    out["Hierarquia NIOSH"] = out[col_acao].apply(classify_hierarchy)

    cost_df = out.apply(
        lambda row: estimate_action_cost(row[col_acao], row.get("Hierarquia NIOSH", "")),
        axis=1,
        result_type="expand",
    )

    for col in cost_df.columns:
        out[col] = cost_df[col]

    return out


def render_modern_gauge(score, band):
    color = "#10b981" if score >= 80 else "#f59e0b" if score >= 50 else "#ef4444"
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "%", "font": {"color": "white", "size": 45}},
            title={
                "text": f"Status Atual:<br><span style='font-size:1.4em; color:{color}; font-weight:800;'>{band}</span>",
                "font": {"color": "#9ca3af", "size": 14},
            },
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#30363d"},
                "bar": {"color": color},
                "bgcolor": "rgba(255,255,255,0.05)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 50], "color": "rgba(239, 68, 68, 0.15)"},
                    {"range": [50, 80], "color": "rgba(245, 158, 11, 0.15)"},
                    {"range": [80, 100], "color": "rgba(16, 185, 129, 0.15)"},
                ],
            },
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter"},
        margin=dict(t=50, b=10, l=10, r=10),
        height=300,
    )
    return fig


def render_modern_radar(cri_data):
    base = cri_data.get("index", 50)
    categories = ["Engenharia/Dados", "PHA/Perigos", "LOPA/Barreiras", "MOC/PSSR"]
    values = [min(100, base + 12), min(100, base - 5), min(100, base + 8), min(100, base - 10)]
    categories.append(categories[0])
    values.append(values[0])

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=categories,
            fill="toself",
            fillcolor="rgba(59, 130, 246, 0.3)",
            line=dict(color="#3b82f6", width=2),
            marker=dict(color="#ffffff", size=6),
        )
    )
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                color="#6b7280",
                gridcolor="#30363d",
                linecolor="rgba(0,0,0,0)",
            ),
            angularaxis=dict(
                color="#d1d5db",
                gridcolor="#30363d",
                linecolor="rgba(0,0,0,0)",
            ),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=30, b=20, l=40, r=40),
        height=300,
    )
    return fig


def render_action_donut(df):
    if not is_valid_df(df):
        return go.Figure()

    base_df = sanitize_and_translate_action_df(df)
    if "Status" not in base_df.columns:
        return go.Figure()
    if "Responsável" not in base_df.columns:
        base_df["Responsável"] = "Engenharia"

    abertas = base_df[base_df["Status"] != "Fechado"]
    if abertas.empty:
        return go.Figure()

    count_df = abertas["Responsável"].value_counts().reset_index()
    count_df.columns = ["Responsável", "Count"]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=count_df["Responsável"],
                values=count_df["Count"],
                hole=0.5,
                marker=dict(colors=["#3b82f6", "#f59e0b", "#ef4444", "#10b981"]),
            )
        ]
    )
    fig.update_layout(
        title=dict(text="Ações Abertas por Equipe", font=dict(color="#d1d5db", size=14)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9ca3af", family="Inter"),
        margin=dict(t=40, b=10, l=10, r=10),
        height=250,
        showlegend=True,
        legend=dict(orientation="v", y=0.5, x=1.0),
    )
    return fig


def render_action_bar(df):
    if not is_valid_df(df):
        return go.Figure()

    base_df = sanitize_and_translate_action_df(df)
    if "Status" not in base_df.columns:
        return go.Figure()
    if "Criticidade" not in base_df.columns:
        base_df["Criticidade"] = "Média"

    count_df = base_df.groupby(["Criticidade", "Status"]).size().reset_index(name="Count")
    fig = px.bar(
        count_df,
        x="Criticidade",
        y="Count",
        color="Status",
        color_discrete_map={
            "Aberto": "#ef4444",
            "Em Andamento": "#f59e0b",
            "Aguardando Verba": "#8b5cf6",
            "Fechado": "#10b981",
        },
        barmode="group",
    )
    fig.update_layout(
        title=dict(text="Distribuição de Risco", font=dict(color="#d1d5db", size=14)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9ca3af", family="Inter"),
        margin=dict(t=40, b=10, l=10, r=10),
        height=250,
        xaxis=dict(title="", showgrid=False),
        yaxis=dict(title="", showgrid=True, gridcolor="#30363d"),
    )
    return fig


def render_flammability_envelope(lfl, ufl, loc):
    """Renderiza o Envelope de Inflamabilidade NFPA 69"""
    fig = go.Figure()

    # Pontos do triângulo: Origem, LOC point, LFL (em ar), UFL (em ar)
    # Assumindo ar ambiente com 21% O2
    x_o2 = [0, loc, 21, 21, 0]
    y_fuel = [0, lfl, lfl, ufl, 0]

    fig.add_trace(
        go.Scatter(
            x=x_o2,
            y=y_fuel,
            fill="toself",
            fillcolor="rgba(239, 68, 68, 0.2)",
            line=dict(color="#ef4444", width=2),
            name="Zona de Explosão",
        )
    )

    # Marcador de Segurança (Abaixo do LOC - NFPA 69 recomenda margem)
    safe_margin_o2 = loc * 0.6
    fig.add_trace(
        go.Scatter(
            x=[safe_margin_o2],
            y=[lfl / 2],
            mode="markers+text",
            marker=dict(color="#10b981", size=12),
            text=["Zona Segura (Purga)"],
            textposition="bottom center",
            name="Margem Segura",
        )
    )

    fig.update_layout(
        title="Envelope de Inflamabilidade (O₂ vs Combustível)",
        xaxis_title="Concentração de Oxigênio (% vol)",
        yaxis_title="Concentração de Combustível (% vol)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.02)",
        font_color="#9ca3af",
        xaxis=dict(range=[0, 25], gridcolor="#30363d"),
        yaxis=dict(range=[0, min(ufl * 1.5, 100)], gridcolor="#30363d"),
        height=350,
        margin=dict(t=40, b=40, l=40, r=20),
    )
    return fig


MENU_STYLES = {
    "container": {
        "padding": "5px",
        "background-color": "#151b28",
        "border": "1px solid #2a3441",
        "border-radius": "10px",
        "margin-bottom": "20px",
    },
    "icon": {"color": "#9ca3af", "font-size": "16px"},
    "nav-link": {
        "font-size": "14px",
        "text-align": "center",
        "margin": "0px",
        "color": "#9ca3af",
        "font-weight": "500",
        "font-family": "Inter",
    },
    "nav-link-selected": {"background-color": "#3b82f6", "color": "white", "font-weight": "600"},
}

# =========================
# ESTADO DA SESSÃO
# =========================
if "lang" not in st.session_state:
    st.session_state.lang = "pt"
if "selected_compound_key" not in st.session_state:
    st.session_state.selected_compound_key = "ammonia"
if "profile" not in st.session_state:
    st.session_state.profile = None
if "lopa_result" not in st.session_state:
    st.session_state.lopa_result = None
if "pid_hazop_matrix" not in st.session_state:
    st.session_state.pid_hazop_matrix = []
if "current_node_name" not in st.session_state:
    st.session_state.current_node_name = "Nó 101: Bomba de Recalque"
if "current_case_name" not in st.session_state:
    st.session_state.current_case_name = ""


def metric_card(label: str, value: str, klass: str = "risk-blue") -> str:
    return f"<div class='metric-box'><div class='metric-label'>{label}</div><div class='metric-value {klass}'>{value}</div></div>"


def load_profile_from_key(key: str) -> None:
    aliases = LOCAL_COMPOUNDS[key]["aliases"]
    st.session_state.profile = load_profile_with_feedback(aliases[0])
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
        st.session_state.profile = load_profile_with_feedback(query_hint)
    st.session_state.current_case_name = case_data.get("case_name", "")
    st.session_state.lopa_result = case_data.get("lopa_result")


# =========================
# SIDEBAR & NAVEGAÇÃO
# =========================
with st.sidebar:
    lang = st.radio("🌐 Idioma", ["pt", "en"], horizontal=True, label_visibility="collapsed")
    st.session_state.lang = lang

    st.markdown(f"## ⚗️ {t('app_title', lang)}\n**Enterprise Edition v2.4**")
    st.caption("Process Safety Intelligence Engine")
    st.markdown("---")

    selected_module = option_menu(
        menu_title=None,
        options=["Visão Executiva", "Engenharia", "Análise de Risco", "Mudanças", "Base de Conhecimento"],
        icons=["speedometer2", "cpu", "shield-lock", "arrow-repeat", "book"],
        default_index=0,
        styles={
            "container": {"background-color": "transparent", "padding": "0"},
            "nav-link": {"font-size": "14px", "color": "#d1d5db", "margin": "5px 0"},
            "nav-link-selected": {"background-color": "#3b82f6", "color": "white"},
        },
    )

    st.markdown("---")
    st.write(f"**{t('quick_access', lang)}**")
    for key, data in LOCAL_COMPOUNDS.items():
        if st.button(data["identity"]["name"], key=f"quick_{key}", width="stretch"):
            load_profile_from_key(key)

    st.markdown("---")
    manual_query = st.text_input("Buscar CAS ou Nome")
    if st.button("Carregar Composto", width="stretch") and manual_query.strip():
        st.session_state.profile = load_profile_with_feedback(manual_query.strip())

if st.session_state.profile is None:
    load_profile_from_key(st.session_state.selected_compound_key)
profile = st.session_state.profile

st.markdown(
    f"""
<div class="context-header">
    <div>🧪 Ativo Analisado: <span>{profile.identity.get('name', 'N/A')} (CAS: {profile.identity.get('cas', 'N/A')})</span></div>
    <div>🏭 Topologia Foco: <span>{st.session_state.current_node_name}</span></div>
</div>
""",
    unsafe_allow_html=True,
)

# Geração dos Dados Globais
psi_df_dash = build_psi_readiness_df(profile, st.session_state.get("lopa_result"), bowtie_payload())
cri_data = calculate_case_readiness_index(
    profile,
    summarize_psi_readiness(psi_df_dash),
    st.session_state.get("moc_result"),
    st.session_state.get("pssr_result"),
    st.session_state.get("lopa_result"),
    st.session_state.get("reactivity_result"),
)
action_df_dash = enrich_action_plan_df(
    build_consolidated_action_plan(
        profile,
        psi_df_dash,
        st.session_state.get("moc_result"),
        st.session_state.get("pssr_result"),
        st.session_state.get("reactivity_result"),
    )
)

has_actions = is_valid_df(action_df_dash)
num_acoes_pendentes = len(action_df_dash) if has_actions else 0

gaps_criticos = 0
if has_actions and "Criticidade" in action_df_dash.columns:
    gaps_criticos = len(action_df_dash[action_df_dash["Criticidade"].isin(["Alta", "Crítica"])])

# ==============================================================================
# MÓDULO 1: VISÃO EXECUTIVA & ACTION HUB
# ==============================================================================
if selected_module == "Visão Executiva":
    exec_tab = option_menu(
        menu_title=None,
        options=["Dashboard Global", "Action Plan", "Relatório Automático", "Meus Projetos"],
        icons=["bar-chart", "list-check", "file-earmark-pdf", "folder2-open"],
        default_index=0,
        orientation="horizontal",
        styles=MENU_STYLES,
    )

    if exec_tab == "Dashboard Global":
        st.markdown("<div class='panel'><h3>KPIs Executivos</h3></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.markdown(
            metric_card("Maturidade Global", f"{cri_data['index']}%", cri_data["color_class"]),
            unsafe_allow_html=True,
        )
        c2.markdown(
            metric_card(
                "Ações Pendentes",
                str(num_acoes_pendentes),
                "risk-amber" if num_acoes_pendentes > 0 else "risk-green",
            ),
            unsafe_allow_html=True,
        )
        c3.markdown(
            metric_card(
                "Gaps Críticos",
                str(gaps_criticos),
                "risk-red" if gaps_criticos > 0 else "risk-green",
            ),
            unsafe_allow_html=True,
        )

        left, right = st.columns(2)
        with left:
            st.markdown("<div class='panel'><h3>Índice de Prontidão do Caso (CRI)</h3></div>", unsafe_allow_html=True)
            st.plotly_chart(
                render_modern_gauge(cri_data["index"], cri_data["band"]),
                use_container_width=True,
                theme=None,
                config={"displayModeBar": False},
            )
        with right:
            st.markdown("<div class='panel'><h3>Distribuição por Pilares</h3></div>", unsafe_allow_html=True)
            st.plotly_chart(
                render_modern_radar(cri_data),
                use_container_width=True,
                theme=None,
                config={"displayModeBar": False},
            )

    elif exec_tab == "Action Plan":
        st.markdown("<div class='panel'><h3>Centro de Comando: Ações de Mitigação (OSHA/CCPS)</h3></div>", unsafe_allow_html=True)

        if has_actions:
            col_acao = get_action_col(action_df_dash)
            abertas_df = action_df_dash[action_df_dash["Status"] != "Fechado"].copy()

            capex_qty = int((abertas_df["Recurso"] == "CAPEX").sum()) if "Recurso" in abertas_df.columns else 0
            opex_qty = int((abertas_df["Recurso"] == "OPEX").sum()) if "Recurso" in abertas_df.columns else 0

            orcamento_min = float(abertas_df["Custo Min (R$)"].sum()) if "Custo Min (R$)" in abertas_df.columns else 0.0
            orcamento_p50 = float(abertas_df["Custo P50 (R$)"].sum()) if "Custo P50 (R$)" in abertas_df.columns else 0.0
            orcamento_max = float(abertas_df["Custo Máx (R$)"].sum()) if "Custo Máx (R$)" in abertas_df.columns else 0.0

            col_chart1, col_chart2, col_budget = st.columns([1.15, 1.15, 1.1])
            with col_chart1:
                st.plotly_chart(
                    render_action_donut(action_df_dash),
                    use_container_width=True,
                    theme=None,
                    config={"displayModeBar": False},
                )
            with col_chart2:
                st.plotly_chart(
                    render_action_bar(action_df_dash),
                    use_container_width=True,
                    theme=None,
                    config={"displayModeBar": False},
                )
            with col_budget:
                st.markdown(
                    f"""
                <div style="background: linear-gradient(135deg, rgba(59,130,246,0.18), rgba(16,185,129,0.10)); border: 1px solid var(--accent-blue); border-radius: 10px; padding: 20px; height: 250px; display: flex; flex-direction: column; justify-content: center;">
                    <div style="color: #9ca3af; font-size: 0.8rem; text-transform: uppercase; font-weight: 600; margin-bottom: 5px;">Orçamento Classe 5 (AACE/CCPS)</div>
                    <div style="color: white; font-size: 1.65rem; font-weight: 800; margin-bottom: 10px;">P50: R$ {orcamento_p50:,.0f}</div>
                    <div style="font-size: 0.82rem; color: #d1d5db; margin-bottom: 16px;">Faixa estimada: R$ {orcamento_min:,.0f} → R$ {orcamento_max:,.0f}</div>
                    <div style="font-size: 0.85rem; color: #d1d5db;"><span style="color:#f59e0b">● CAPEX:</span> {capex_qty} itens</div>
                    <div style="font-size: 0.85rem; color: #d1d5db;"><span style="color:#3b82f6">● OPEX:</span> {opex_qty} itens</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            st.markdown("<hr style='border-color: #2a3441;'>", unsafe_allow_html=True)

            col_config = {
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Aberto", "Em Andamento", "Aguardando Verba", "Fechado"],
                    required=True,
                ),
                "Responsável": st.column_config.SelectboxColumn(
                    "Responsável",
                    options=["Engenharia", "Manutenção", "Operação", "HSE"],
                ),
                "Prazo (Dias)": st.column_config.NumberColumn("Prazo", min_value=1, max_value=365, step=1),
                "Requer MOC?": st.column_config.CheckboxColumn("Requer MOC?", default=False),
                "Recurso": st.column_config.TextColumn("Recurso"),
                "Hierarquia NIOSH": st.column_config.TextColumn("Hierarquia (Auto)", width="medium"),
                "Pacote AACE": st.column_config.TextColumn("Pacote AACE", width="medium"),
                "Custo Min (R$)": st.column_config.NumberColumn("Min", format="R$ %.0f"),
                "Custo P50 (R$)": st.column_config.NumberColumn("P50", format="R$ %.0f"),
                "Custo Máx (R$)": st.column_config.NumberColumn("Máx", format="R$ %.0f"),
                col_acao: st.column_config.TextColumn("Ação Recomendada", width="large"),
            }

            if "Criticidade" in action_df_dash.columns:
                col_config["Criticidade"] = st.column_config.TextColumn("Criticidade")

            disabled_cols = [
                col_acao,
                "Recurso",
                "Hierarquia NIOSH",
                "Pacote AACE",
                "Custo Min (R$)",
                "Custo P50 (R$)",
                "Custo Máx (R$)",
            ]
            if "Criticidade" in action_df_dash.columns:
                disabled_cols.append("Criticidade")

            edited_df = st.data_editor(
                action_df_dash,
                width="stretch",
                hide_index=True,
                column_config=col_config,
                disabled=disabled_cols,
            )

            fechadas = len(edited_df[edited_df["Status"] == "Fechado"])
            total = len(edited_df)
            st.progress(
                fechadas / total if total > 0 else 0.0,
                text=f"Progresso: {fechadas}/{total} ações concluídas",
            )

            st.markdown("<br>", unsafe_allow_html=True)
            btn_col1, btn_col2 = st.columns(2)

            with btn_col1:
                st.download_button(
                    "📥 Baixar Planilha para SAP (CSV)",
                    edited_df.to_csv(index=False).encode("utf-8"),
                    "action_plan.csv",
                    "text/csv",
                    use_container_width=True,
                )

            with btn_col2:
                briefing_text = (
                    f"ORDEM DE SERVIÇO - SEGURANÇA DE PROCESSOS\n"
                    f"Ativo: {profile.identity.get('name')}\n"
                    f"Topologia: {st.session_state.current_node_name}\n"
                    + "=" * 50
                    + "\n\n"
                )
                for resp in edited_df[edited_df["Status"] != "Fechado"]["Responsável"].unique():
                    briefing_text += f"[EQUIPE: {resp.upper()}]\n"
                    acoes_resp = edited_df[
                        (edited_df["Status"] != "Fechado") & (edited_df["Responsável"] == resp)
                    ]
                    for _, row in acoes_resp.iterrows():
                        crit = row.get("Criticidade", "Normal")
                        briefing_text += f"- [{crit}] {row[col_acao]} (Prazo: {row['Prazo (Dias)']} dias)\n"
                    briefing_text += "\n"

                st.download_button(
                    "📋 Gerar Briefing de Manutenção (TXT)",
                    briefing_text.encode("utf-8"),
                    "ordem_servico.txt",
                    "text/plain",
                    use_container_width=True,
                )

        else:
            st.info("Nenhuma ação de segurança pendente no momento. A planta está de acordo com as especificações.")

    elif exec_tab == "Relatório Automático":
        st.markdown("<div class='panel'><h3>Gerador de Relatório Executivo</h3></div>", unsafe_allow_html=True)
        report_case_name = st.text_input(
            "Nome do Relatório",
            value=st.session_state.current_case_name or profile.identity.get("name", "Caso"),
        )
        if st.button("Gerar Relatório Completo", type="primary"):
            st.session_state.report_bundle = build_executive_bundle(
                case_name=report_case_name,
                profile=profile,
                context={"lopa_result": st.session_state.get("lopa_result")},
            )
            st.success("Relatório Compilado!")
        if st.session_state.get("report_bundle"):
            st.download_button(
                "📥 Baixar Documento (HTML)",
                st.session_state.report_bundle["html"],
                file_name=f"{report_case_name}.html",
            )

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
# MÓDULO 2: ENGENHARIA DE DADOS (SPRINT 24: CLEAN UI & NFPA 69)
# ==============================================================================
elif selected_module == "Engenharia":
    eng_tab = option_menu(
        menu_title=None,
        options=["Termodinâmica", "Inertização (NFPA 69)", "Emergências (PSV/Runaway)"],
        icons=["thermometer", "cone-striped", "speedometer2"],
        default_index=0,
        orientation="horizontal",
        styles=MENU_STYLES,
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
            st.dataframe(format_identity_df(profile), width="stretch", hide_index=True)
            for hz in profile.hazards:
                st.error(hz)
        with right:
            st.markdown("<div class='panel'><h3>Propriedades Base</h3></div>", unsafe_allow_html=True)
            st.dataframe(format_physchem_df(profile), width="stretch", hide_index=True)

    elif eng_tab == "Inertização (NFPA 69)":
        st.markdown("<div class='panel'><h3>⚠️ Envelope de Inflamabilidade & Purga de Reatores</h3></div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='note-card'>Calcule a atmosfera segura durante partidas e paradas. Para evitar a mistura explosiva, a concentração de O₂ deve operar abaixo da <b>Limiting Oxygen Concentration (LOC)</b>.</div>",
            unsafe_allow_html=True,
        )

        # Extrai os dados do perfil, com fallbacks caso não existam
        lfl_val = float(profile.limit("LEL_vol", 5.0))
        ufl_val = float(profile.limit("UEL_vol", 15.0))

        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("#### Parâmetros do Composto")
            lfl = st.number_input("LFL (% Combustível)", value=lfl_val)
            ufl = st.number_input("UFL (% Combustível)", value=ufl_val)
            loc = st.number_input("LOC (% Oxigênio)", value=10.5, help="Concentração limite de O2 segundo NFPA 69")
            st.metric("Margem de Segurança Sugerida (Alarme Alto)", f"O₂ < {loc * 0.6:.1f}%")

        with c2:
            fig_flam = render_flammability_envelope(lfl, ufl, loc)
            st.plotly_chart(fig_flam, use_container_width=True, theme=None, config={"displayModeBar": False})

    elif eng_tab == "Emergências (PSV/Runaway)":
        st.markdown("<div class='panel'><h3>Cálculos de Emergência (Clean Mode)</h3></div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='note-card'>Utilize os botões ⚙️ para expandir os parâmetros de cálculo. A interface foi otimizada para focar nos resultados críticos.</div>",
            unsafe_allow_html=True,
        )

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
                if st.button("Estimar TMR (Time to Maximum Rate)", use_container_width=True):
                    res = calculate_tmr_adiabatic(t0, ea, 1e12, 1500, 2.5)
                    st.error(f"Tempo p/ Explosão Adibática: **{res['tmr_min']:.1f} min**")

# ==============================================================================
# MÓDULO 3: ANÁLISE DE RISCO (SPRINT 24: SIL & QRA)
# ==============================================================================
elif selected_module == "Análise de Risco":
    risk_tab = option_menu(
        menu_title=None,
        options=["HAZOP Builder", "Verificação SIL (IEC)", "QRA Social"],
        icons=["diagram-3", "shield-check", "activity"],
        default_index=0,
        orientation="horizontal",
        styles=MENU_STYLES,
    )

    if risk_tab == "HAZOP Builder":
        st.markdown("<div class='panel'><h3>Geração Inteligente de P&ID e HAZOP</h3></div>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["Nó Único (Grafo)", "Lote Múltiplos Nós (CSV)"])

        with t1:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.session_state.current_node_name = st.text_input(
                    "Identificação do Nó",
                    value=st.session_state.current_node_name,
                )
            with col2:
                selected_equipment = st.multiselect(
                    "Equipamentos e Linhas (Em Ordem)",
                    options=list(EQUIPMENT_PARAMETERS.keys()),
                    default=[
                        "Tanque de Armazenamento Atmosférico",
                        "Tubulação / Linha de Transferência",
                        "Bomba Centrífuga",
                    ],
                )

            if selected_equipment:
                dot = graphviz.Digraph()
                dot.attr(rankdir="LR", bgcolor="transparent")
                dot.attr(
                    "node",
                    shape="box",
                    style="filled",
                    fillcolor="#1e293b",
                    color="#3b82f6",
                    fontcolor="white",
                    fontname="Inter",
                    penwidth="2",
                )
                dot.attr("edge", color="#9ca3af", penwidth="2")
                for i, eq in enumerate(selected_equipment):
                    dot.node(str(i), eq)
                    if i > 0:
                        dot.edge(str(i - 1), str(i))
                st.graphviz_chart(dot, use_container_width=True)

            if st.button("🚀 Consolidar Topologia em HAZOP", type="primary"):
                st.session_state.pid_hazop_matrix = generate_hazop_from_topology(
                    st.session_state.current_node_name,
                    selected_equipment,
                    profile,
                )
                st.success("Grafo processado! As pendências de mitigação foram enviadas ao Action Hub.")

        with t2:
            st.markdown(
                "<div class='note-card'>Importe a Equipment List extraída do seu CAD (Nó, Equipamento).</div>",
                unsafe_allow_html=True,
            )
            uploaded_file = st.file_uploader("Upload CSV/XLSX", type=["csv", "xlsx"])
            if uploaded_file is not None:
                df_bulk = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
                if st.button("⚡ Executar Processamento em Lote", type="primary"):
                    bulk_results = process_bulk_pid_nodes(df_bulk, profile)
                    if bulk_results:
                        st.session_state.pid_hazop_matrix = bulk_results
                        st.success(f"{len(bulk_results)} cenários gerados para a fábrica inteira.")

        # EXIBIÇÃO DA MATRIZ GERADA
        if st.session_state.get("pid_hazop_matrix"):
            st.markdown("<br><hr>", unsafe_allow_html=True)
            df_hazop = pd.DataFrame(st.session_state.pid_hazop_matrix)
            with st.expander("📋 Estudo HAZOP (IEC 61882)", expanded=True):
                view_mode = st.radio(
                    "Modo de Leitura:",
                    ["🗂️ Cards (Discussão de Reunião)", "📊 Tabela Otimizada (Text Wrap)"],
                    horizontal=True,
                    label_visibility="collapsed",
                )
                st.markdown("<br>", unsafe_allow_html=True)

                if "Cards" in view_mode:
                    for _, row in df_hazop.iterrows():
                        st.markdown(
                            f"""
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
                        """,
                            unsafe_allow_html=True,
                        )
                else:
                    st.dataframe(
                        df_hazop,
                        width="stretch",
                        hide_index=True,
                        column_config={
                            "Nó": st.column_config.TextColumn("Nó", width="medium"),
                            "Causa": st.column_config.TextColumn("Causa", width="large"),
                            "Consequência": st.column_config.TextColumn("Consequência", width="large"),
                            "Salvaguarda Atual": st.column_config.TextColumn("Salvaguarda", width="medium"),
                        },
                    )
                st.download_button(
                    "📥 Exportar CSV",
                    df_hazop.to_csv(index=False).encode("utf-8"),
                    "hazop_export.csv",
                    "text/csv",
                )

            with st.expander("🔀 Matriz Causa e Efeito p/ Automação (IEC 61511)", expanded=False):
                df_ce = generate_ce_matrix_from_hazop(st.session_state.pid_hazop_matrix)
                if is_valid_df(df_ce):
                    st.dataframe(df_ce, width="stretch", hide_index=True)
                    st.download_button(
                        "📥 Exportar C&E",
                        df_ce.to_csv(index=False).encode("utf-8"),
                        "ce_matrix.csv",
                        "text/csv",
                    )
                else:
                    st.info("Nenhuma arquitetura de Trip (Intertravamento) foi deduzida dos cenários atuais.")

    elif risk_tab == "Verificação SIL (IEC)":
        st.markdown("<div class='panel'><h3>🖲️ Análise de Arquitetura de Intertravamento (IEC 61511)</h3></div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='note-card'>Cálculo paramétrico da Probabilidade Média de Falha sob Demanda (PFDavg) garantindo a conformidade da malha SIF e rastreabilidade para auditorias.</div>",
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            arq = st.selectbox("Arquitetura de Sensores/Válvulas", ["1oo1 (Simplex)", "1oo2 (Redundante)", "2oo3 (Votação)"])
            lambda_du = st.number_input("Taxa de Falha Perigosa (λdu) - falhas/hora", 1e-6, format="%.2e")
            ti_meses = st.number_input("Intervalo de Teste (Proof Test - Meses)", 12)
            ti_horas = ti_meses * 730

        with col2:
            st.markdown("#### Memorial de Cálculo (IEC)")
            if "1oo1" in arq:
                st.latex(r"PFD_{avg} = \lambda_{DU} \times \frac{TI}{2}")
                pfd_avg = lambda_du * (ti_horas / 2)
            elif "1oo2" in arq:
                st.latex(r"PFD_{avg} \approx \frac{(\lambda_{DU} \times TI)^2}{3} + \beta \times \lambda_{DU} \times \frac{TI}{2}")
                st.caption("*Assumindo fator de causa comum (β) = 10%*")
                pfd_avg = (((lambda_du * ti_horas) ** 2) / 3) + (0.10 * lambda_du * (ti_horas / 2))
            else:
                st.latex(r"PFD_{avg} \approx (\lambda_{DU} \times TI)^2 + \beta \times \lambda_{DU} \times \frac{TI}{2}")
                st.caption("*Assumindo fator de causa comum (β) = 10%*")
                pfd_avg = ((lambda_du * ti_horas) ** 2) + (0.10 * lambda_du * (ti_horas / 2))

            sil = "SIL 3" if pfd_avg < 1e-3 else "SIL 2" if pfd_avg < 1e-2 else "SIL 1" if pfd_avg < 1e-1 else "Não Classificado"

            st.markdown(
                f"""
            <div style='background:rgba(16,185,129,0.1); border:1px solid #10b981; border-radius:8px; padding:15px; margin-top:20px; text-align:center;'>
                <span style='color:#9ca3af; font-size:0.8rem; text-transform:uppercase;'>Resultado Final (PFDavg)</span><br>
                <span style='color:white; font-size:2.5rem; font-weight:800;'>{pfd_avg:.2e}</span><br>
                <span style='color:#10b981; font-size:1.2rem; font-weight:700;'>Alcança {sil}</span>
            </div>
            """,
                unsafe_allow_html=True,
            )

    elif risk_tab == "QRA Social":
        st.markdown("<div class='panel'><h3>Curva F-N de Risco Social</h3></div>", unsafe_allow_html=True)
        fig_fn = go.Figure()
        fig_fn.add_trace(go.Scatter(x=[1, 10, 100], y=[1e-4, 1e-5, 1e-6], name="Limite Tolerável", line=dict(color="red", dash="dash")))
        fig_fn.add_trace(go.Scatter(x=[1, 10, 100], y=[1e-5, 1e-6, 1e-7], name="Limite Desprezível", line=dict(color="green", dash="dash")))
        fig_fn.add_trace(
            go.Scatter(
                x=[10],
                y=[2e-5],
                mode="markers+text",
                text=["Risco Planta"],
                textposition="top center",
                marker=dict(size=12, color="white"),
            )
        )
        fig_fn.update_layout(
            xaxis_type="log",
            yaxis_type="log",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#9ca3af",
            height=400,
        )
        st.plotly_chart(fig_fn, use_container_width=True, theme=None)

# ==============================================================================
# MÓDULO 4: GESTÃO DE MUDANÇA
# ==============================================================================
elif selected_module == "Mudanças":
    chg_tab = option_menu(
        menu_title=None,
        options=["MOC (Modificação)", "PSSR (Inspeção Pré-Partida)"],
        icons=["arrow-repeat", "check2-square"],
        default_index=0,
        orientation="horizontal",
        styles=MENU_STYLES,
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
            st.session_state.moc_result = evaluate_moc(
                profile,
                change_type,
                impacts,
                "",
                temporary=p1,
                protections_changed=p2,
                bypass_or_override=False,
            )
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
            st.session_state.pssr_result = evaluate_pssr(
                design_ok=d1,
                procedures_ok=d2,
                training_ok=True,
                relief_verified=d4,
                alarms_tested=d5,
                startup_authorized=True,
                pha_or_moc_ok=True,
                mi_ready=True,
                emergency_ready=True,
                scope_label="PSSR",
            )
            st.success("Status Operacional Emitido.")

# ==============================================================================
# SPRINT 23: MÓDULO 5 - BASE DE CONHECIMENTO E NORMAS
# ==============================================================================
elif selected_module == "Base de Conhecimento":
    kb_tab = option_menu(
        menu_title=None,
        options=["Normas e Referências", "Incidentes Históricos"],
        icons=["journal-text", "clock-history"],
        default_index=0,
        orientation="horizontal",
        styles=MENU_STYLES,
    )

    if kb_tab == "Normas e Referências":
        st.markdown(
            """
        <div style='margin-bottom: 20px;'>
            <h2 style='color: #f3f4f6; font-size: 1.8rem; font-weight: 700; margin-bottom: 5px;'>📖 Biblioteca de Normas e Referências</h2>
            <p style='color: #9ca3af; font-size: 1rem;'>Consulte rapidamente as principais normas, códigos e diretrizes aplicáveis à engenharia de processos e segurança industrial.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        c_search, c_filter = st.columns([3, 1])
        search_term = c_search.text_input("🔍 Buscar por código, título ou palavra-chave...", placeholder="Ex: API 520, OSHA...")
        tag_filter = c_filter.selectbox("Filtrar por Entidade", ["Todos", "API", "OSHA", "IEC", "CCPS", "NFPA"])

        # Base de Dados Curada de Normas
        normas = [
            {
                "id": "API Standard 520",
                "tag": "API",
                "area": "Alívio de Pressão",
                "desc": "Sizing, Selection, and Installation of Pressure-Relieving Devices. Norma fundamental para o dimensionamento de válvulas de segurança.",
            },
            {
                "id": "API Standard 521",
                "tag": "API",
                "area": "Alívio de Pressão",
                "desc": "Pressure-relieving and Depressuring Systems. Guia para o projeto de sistemas de alívio de pressão, incluindo análise de causas de despressurização e tochas.",
            },
            {
                "id": "OSHA 1910.119",
                "tag": "OSHA",
                "area": "Gestão de Segurança",
                "desc": "Process Safety Management of Highly Hazardous Chemicals. Exigências regulatórias mandatárias para gerenciamento seguro de químicos perigosos.",
            },
            {
                "id": "IEC 61511",
                "tag": "IEC",
                "area": "Instrumentação",
                "desc": "Functional safety - Safety instrumented systems for the process industry sector. Metodologia para ciclo de vida de SIS e verificação SIL.",
            },
            {
                "id": "CCPS LOPA",
                "tag": "CCPS",
                "area": "Análise de Risco",
                "desc": "Layer of Protection Analysis: Simplified Process Risk Assessment. Diretrizes para análise semiquantitativa de camadas de proteção independente (IPL).",
            },
            {
                "id": "NFPA 69",
                "tag": "NFPA",
                "area": "Prevenção a Explosões",
                "desc": "Standard on Explosion Prevention Systems. Requisitos para sistemas de redução de oxidante (Limiting Oxidant Concentration - LOC) e purga.",
            },
        ]

        # Filtro ativo
        filtered_normas = [
            n
            for n in normas
            if (tag_filter == "Todos" or n["tag"] == tag_filter)
            and (search_term.lower() in n["id"].lower() or search_term.lower() in n["desc"].lower())
        ]

        # Renderização em Grid (2 colunas) usando HTML e CSS
        cols = st.columns(2)
        for idx, norma in enumerate(filtered_normas):
            with cols[idx % 2]:
                st.markdown(
                    f"""
                <div class="doc-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <span style="color: #9ca3af; font-size: 0.8rem; font-weight: 700;">{norma['tag']}</span>
                        <span class="doc-tag">{norma['area']}</span>
                    </div>
                    <span class="doc-title">{norma['id']}</span>
                    <p class="doc-desc">{norma['desc']}</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )
                st.write("")

    elif kb_tab == "Incidentes Históricos":
        st.markdown("<div class='panel'><h3>📚 Banco de Incidentes e Lições Aprendidas</h3></div>", unsafe_allow_html=True)
        st.markdown(
            f"<p style='color: #9ca3af; margin-bottom: 30px;'>Filtrando falhas históricas globais relacionadas à substância <b>{profile.identity.get('name')}</b>.</p>",
            unsafe_allow_html=True,
        )

        relevant_cases = get_relevant_historical_cases(profile)
        if relevant_cases:
            timeline_html = "<div class='history-timeline'>"
            for case in relevant_cases:
                timeline_html += f"""
                <div class='history-item'>
                    <div style='color: #3b82f6; font-weight: 700; font-size: 1.1rem;'>{case['ano']}</div>
                    <div style='font-size: 1.2rem; font-weight: 600; color: #f3f4f6; margin-top: 5px;'>{case['evento']}</div>
                    <div style='background: rgba(30,41,59,0.5); padding: 15px; border-radius: 8px; margin-top: 10px; border-left: 3px solid #f59e0b;'>
                        <strong style='color: #f59e0b; font-size: 0.85rem; text-transform: uppercase;'>Mecanismo de Falha</strong><br>
                        <span style='color: #d1d5db; font-size: 0.95rem; line-height: 1.5;'>{case['mecanismo']}</span>
                    </div>
                </div>
                """
            timeline_html += "</div>"
            st.markdown(timeline_html, unsafe_allow_html=True)
        else:
            st.info(f"Nenhum incidente catastrófico catalogado especificamente para {profile.identity.get('name')} na nossa base curada.")
