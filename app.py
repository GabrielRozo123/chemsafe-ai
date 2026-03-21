from __future__ import annotations

import sys
from pathlib import Path
import io
import math
import re
import time
import textwrap

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
from ui_components import (
    metric_card,
    render_reference_chips,
    render_hero_panel,
    render_trust_ribbon,
    render_evidence_panel,
)

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

APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

:root {
  --bg-0: #07111e;
  --bg-1: #0b1422;
  --bg-2: #111c2d;
  --card-bg: rgba(17, 28, 45, 0.78);
  --card-strong: rgba(21, 32, 50, 0.92);
  --border-color: rgba(148, 163, 184, 0.16);
  --border-strong: rgba(96, 165, 250, 0.26);
  --text-main: #e5edf7;
  --text-soft: #9fb0c7;
  --text-faint: #7c8aa0;

  --accent-blue: #60a5fa;
  --accent-cyan: #22d3ee;
  --accent-green: #34d399;
  --accent-amber: #fbbf24;
  --accent-red: #f87171;
  --accent-violet: #a78bfa;

  --glow-blue: rgba(96, 165, 250, 0.16);
  --glow-green: rgba(52, 211, 153, 0.16);
  --glow-red: rgba(248, 113, 113, 0.16);

  --shadow-soft: 0 10px 30px rgba(0, 0, 0, 0.22);
  --shadow-card: 0 18px 45px rgba(0, 0, 0, 0.28);
  --radius-xl: 18px;
  --radius-lg: 14px;
  --radius-md: 10px;
}

html, body, [class*="css"]  {
  font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.stApp {
  color: var(--text-main);
  background:
    radial-gradient(circle at 12% 10%, rgba(34, 211, 238, 0.08), transparent 20%),
    radial-gradient(circle at 88% 8%, rgba(96, 165, 250, 0.10), transparent 24%),
    radial-gradient(circle at 50% 100%, rgba(52, 211, 153, 0.05), transparent 30%),
    linear-gradient(180deg, var(--bg-0) 0%, var(--bg-1) 52%, #09111c 100%);
}

.block-container {
  padding-top: 1.2rem;
  padding-bottom: 3rem;
  max-width: 1480px;
}

section[data-testid="stSidebar"] {
  background:
    linear-gradient(180deg, rgba(9, 15, 28, 0.98) 0%, rgba(11, 20, 34, 0.98) 100%);
  border-right: 1px solid rgba(148, 163, 184, 0.10);
}

.context-header {
  background:
    linear-gradient(135deg, rgba(17, 28, 45, 0.92) 0%, rgba(18, 31, 50, 0.88) 100%);
  border: 1px solid var(--border-color);
  padding: 18px 24px;
  border-radius: var(--radius-xl);
  margin-bottom: 18px;
  font-weight: 500;
  font-size: 0.96rem;
  color: var(--text-soft);
  display: flex;
  justify-content: space-between;
  gap: 16px;
  box-shadow: var(--shadow-soft);
  backdrop-filter: blur(10px);
}

.context-header span {
  color: #f8fbff;
  font-weight: 700;
}

.panel {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: 1.35rem 1.35rem 1.2rem 1.35rem;
  margin-bottom: 1rem;
  box-shadow: var(--shadow-soft);
  backdrop-filter: blur(10px);
  transition: transform 0.18s ease, border-color 0.22s ease, box-shadow 0.22s ease;
}

.panel:hover {
  transform: translateY(-1px);
  border-color: var(--border-strong);
  box-shadow: 0 16px 38px rgba(0,0,0,0.24), 0 0 0 1px rgba(96,165,250,0.05);
}

.panel h3 {
  margin-top: 0;
  color: #f4f8fd;
  font-size: 1.02rem;
  font-weight: 700;
  letter-spacing: 0.01em;
  border-bottom: 1px solid rgba(148,163,184,0.10);
  padding-bottom: 10px;
  margin-bottom: 16px;
}

.hero-panel {
  background:
    linear-gradient(135deg, rgba(20, 33, 52, 0.94) 0%, rgba(13, 23, 38, 0.95) 100%);
  border: 1px solid rgba(96, 165, 250, 0.18);
  border-radius: 20px;
  padding: 20px 22px;
  margin-bottom: 18px;
  box-shadow: var(--shadow-card);
}

.hero-kicker {
  color: var(--accent-cyan);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 0.72rem;
  font-weight: 800;
  margin-bottom: 8px;
}

.hero-title {
  color: #f8fbff;
  font-size: 1.35rem;
  font-weight: 800;
  margin-bottom: 6px;
}

.hero-subtitle {
  color: var(--text-soft);
  font-size: 0.96rem;
  line-height: 1.55;
}

.metric-box {
  background:
    linear-gradient(180deg, rgba(24, 37, 58, 0.82) 0%, rgba(17, 27, 43, 0.90) 100%);
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 14px;
  padding: 16px 18px;
  text-align: center;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 124px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
}

.metric-label {
  color: var(--text-faint);
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-weight: 700;
}

.metric-value {
  color: #f8fbff;
  font-size: 1.78rem;
  font-weight: 800;
  margin-top: 8px;
  line-height: 1.18;
  white-space: normal;
  word-wrap: break-word;
}

.metric-mono {
  font-family: 'JetBrains Mono', monospace;
}

.risk-blue { color: var(--accent-blue); }
.risk-green { color: var(--accent-green); }
.risk-amber { color: var(--accent-amber); }
.risk-red { color: var(--accent-red); }
.risk-violet { color: var(--accent-violet); }

.note-card {
  background: linear-gradient(90deg, rgba(96, 165, 250, 0.09), rgba(34, 211, 238, 0.06));
  border: 1px solid rgba(96, 165, 250, 0.12);
  border-left: 4px solid var(--accent-blue);
  padding: 14px 15px;
  border-radius: 10px;
  font-size: 0.92rem;
  margin-bottom: 16px;
  color: #d6e8fb;
  line-height: 1.6;
}

.trust-ribbon {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: flex-start;
  background:
    linear-gradient(135deg, rgba(12, 22, 36, 0.96) 0%, rgba(18, 31, 50, 0.92) 100%);
  border: 1px solid rgba(52, 211, 153, 0.20);
  border-radius: 18px;
  padding: 16px 18px;
  margin-bottom: 18px;
  box-shadow: var(--shadow-soft);
}

.trust-left { flex: 1; }
.trust-kicker {
  color: var(--accent-green);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 0.70rem;
  font-weight: 800;
  margin-bottom: 6px;
}
.trust-title {
  color: #f7fbff;
  font-size: 1.05rem;
  font-weight: 800;
  margin-bottom: 4px;
}
.trust-text {
  color: var(--text-soft);
  font-size: 0.91rem;
  line-height: 1.5;
}
.trust-right {
  min-width: 180px;
  text-align: right;
}
.trust-pill {
  display: inline-block;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(52, 211, 153, 0.14);
  border: 1px solid rgba(52, 211, 153, 0.24);
  color: #b7f7de;
  font-size: 0.78rem;
  font-weight: 800;
  margin-bottom: 8px;
}
.trust-meta {
  color: var(--text-faint);
  font-size: 0.80rem;
}

.ref-chip-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}
.ref-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 0.76rem;
  color: #d9e7f8;
  background: rgba(148, 163, 184, 0.08);
  border: 1px solid rgba(148, 163, 184, 0.12);
}
.ref-chip::before {
  content: "▣";
  color: var(--accent-cyan);
  font-size: 0.72rem;
}

.doc-card {
  background: linear-gradient(180deg, rgba(23, 36, 57, 0.78) 0%, rgba(16, 26, 42, 0.88) 100%);
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 16px;
  padding: 20px;
  height: 100%;
  transition: all 0.22s ease;
  box-shadow: var(--shadow-soft);
}

.doc-card:hover {
  border-color: rgba(96, 165, 250, 0.28);
  transform: translateY(-2px);
  box-shadow: 0 16px 36px rgba(0,0,0,0.26);
}

.doc-tag {
  background: rgba(96, 165, 250, 0.12);
  color: #9fcbff;
  font-size: 0.74rem;
  padding: 4px 10px;
  border-radius: 999px;
  font-weight: 800;
  text-transform: uppercase;
  display: inline-block;
  margin-bottom: 10px;
  border: 1px solid rgba(96, 165, 250, 0.18);
}

.doc-title {
  font-size: 1.06rem;
  font-weight: 800;
  color: #f4f8fd;
  margin-bottom: 8px;
  display: block;
}

.doc-desc {
  font-size: 0.91rem;
  color: var(--text-soft);
  line-height: 1.58;
}

.history-timeline {
  border-left: 3px solid rgba(96, 165, 250, 0.55);
  margin-left: 20px;
  padding-left: 22px;
}
.history-item {
  margin-bottom: 24px;
  position: relative;
}
.history-item::before {
  content: '';
  position: absolute;
  left: -30px;
  top: 2px;
  width: 14px;
  height: 14px;
  background: #08111f;
  border: 3px solid var(--accent-blue);
  border-radius: 50%;
}

.evidence-panel {
  background: linear-gradient(180deg, rgba(12, 21, 34, 0.92) 0%, rgba(15, 25, 40, 0.96) 100%);
  border: 1px solid rgba(167, 139, 250, 0.16);
  border-radius: 16px;
  padding: 18px;
  margin-bottom: 16px;
  box-shadow: var(--shadow-soft);
}
.evidence-kicker {
  color: var(--accent-violet);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 0.70rem;
  font-weight: 800;
  margin-bottom: 6px;
}
.evidence-title {
  color: #f7fbff;
  font-size: 1.02rem;
  font-weight: 800;
  margin-bottom: 8px;
}
.evidence-sub {
  color: var(--text-soft);
  font-size: 0.91rem;
  line-height: 1.56;
  margin-bottom: 14px;
}
.evidence-grid {
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  gap: 14px;
}
.evidence-card {
  background: rgba(148, 163, 184, 0.05);
  border: 1px solid rgba(148, 163, 184, 0.10);
  border-radius: 12px;
  padding: 12px 13px;
}
.evidence-card h4 {
  margin: 0 0 8px 0;
  color: #f0f6ff;
  font-size: 0.86rem;
  font-weight: 800;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}
.evidence-card ul {
  margin: 0;
  padding-left: 18px;
}
.evidence-card li {
  color: var(--text-soft);
  font-size: 0.88rem;
  line-height: 1.55;
  margin-bottom: 4px;
}
.evidence-code {
  font-family: 'JetBrains Mono', monospace;
  background: rgba(96, 165, 250, 0.08);
  color: #d5e7ff;
  border: 1px solid rgba(96, 165, 250, 0.12);
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 0.82rem;
  line-height: 1.5;
  white-space: pre-wrap;
}
.evidence-inputs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0,1fr));
  gap: 8px;
}
.evidence-input-item {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(148,163,184,0.08);
  border-radius: 10px;
  padding: 9px 10px;
}
.evidence-input-label {
  color: var(--text-faint);
  font-size: 0.73rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 4px;
}
.evidence-input-value {
  color: #f4f9ff;
  font-size: 0.89rem;
  font-weight: 700;
}

.stExpander {
  border: 1px solid rgba(148, 163, 184, 0.12) !important;
  border-radius: 14px !important;
  background: rgba(17, 28, 45, 0.62) !important;
  overflow: hidden;
}

.stButton > button,
.stDownloadButton > button {
  border-radius: 12px !important;
  border: 1px solid rgba(96, 165, 250, 0.18) !important;
  background: linear-gradient(180deg, rgba(25, 39, 61, 0.92) 0%, rgba(18, 29, 46, 0.96) 100%) !important;
  color: #edf5ff !important;
  font-weight: 700 !important;
  transition: all 0.18s ease !important;
  box-shadow: 0 6px 16px rgba(0,0,0,0.18);
}

.stButton > button:hover,
.stDownloadButton > button:hover {
  transform: translateY(-1px);
  border-color: rgba(96, 165, 250, 0.30) !important;
  box-shadow: 0 10px 22px rgba(0,0,0,0.24), 0 0 0 3px rgba(96,165,250,0.08);
}

.nav-link {
  font-family: 'Inter', sans-serif !important;
}

[data-testid="stMetric"] {
  background: rgba(17, 28, 45, 0.68);
  border: 1px solid rgba(148, 163, 184, 0.10);
  padding: 12px 14px;
  border-radius: 12px;
}

small, .stCaption {
  color: var(--text-faint) !important;
}
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
# BASE CURADA DE NORMAS E REFERÊNCIAS
# ==============================================================================
NORMS_DB = [
    {
        "id": "OSHA 1910.119",
        "tag": "OSHA",
        "area": "PSM",
        "title": "Process Safety Management of Highly Hazardous Chemicals",
        "desc": "Requisitos regulatórios para gestão de segurança de processos em instalações com químicos perigosos.",
        "application": "PHA, MOC, PSSR, integridade mecânica, treinamento, investigação.",
        "status_note": "Base curada interna. Validar edição vigente oficial antes de uso regulatório.",
    },
    {
        "id": "IEC 61511",
        "tag": "IEC",
        "area": "SIS / SIL",
        "title": "Functional Safety for the Process Industry Sector",
        "desc": "Norma para ciclo de vida de sistemas instrumentados de segurança e verificação SIL.",
        "application": "SIF, PFDavg, proof test, arquitetura 1oo1/1oo2/2oo3.",
        "status_note": "Base curada interna. Confirmar parte/edição vigente no projeto.",
    },
    {
        "id": "IEC 61882",
        "tag": "IEC",
        "area": "PHA / HAZOP",
        "title": "Hazard and Operability Studies (HAZOP Studies)",
        "desc": "Guia para execução estruturada de estudos HAZOP.",
        "application": "Nós, desvios, causas, consequências, salvaguardas e recomendações.",
        "status_note": "Base curada interna. Validar edição oficial aplicável.",
    },
    {
        "id": "NFPA 69",
        "tag": "NFPA",
        "area": "Explosões / Inertização",
        "title": "Standard on Explosion Prevention Systems",
        "desc": "Requisitos para prevenção de explosões, inertização e concentração limite de oxidante.",
        "application": "LOC, purga, envelope de inflamabilidade e partidas/paradas.",
        "status_note": "Base curada interna. Confirmar edição oficial vigente.",
    },
    {
        "id": "API 520",
        "tag": "API",
        "area": "Alívio de Pressão",
        "title": "Sizing, Selection, and Installation of Pressure-Relieving Devices",
        "desc": "Critérios para dimensionamento e seleção de dispositivos de alívio.",
        "application": "PSV/PRV, cenários de alívio, seleção preliminar de orifício.",
        "status_note": "Base curada interna. Confirmar parte/edição oficial.",
    },
    {
        "id": "API 521",
        "tag": "API",
        "area": "Alívio de Pressão",
        "title": "Pressure-Relieving and Depressuring Systems",
        "desc": "Guia para definição de cenários, carga térmica e sistemas de despressurização.",
        "application": "Cenários de fogo, blowdown, flare, contingências de alívio.",
        "status_note": "Base curada interna. Revisar edição vigente oficial.",
    },
    {
        "id": "CCPS LOPA",
        "tag": "CCPS",
        "area": "LOPA",
        "title": "Layer of Protection Analysis",
        "desc": "Referência clássica para análise semiquantitativa de camadas independentes de proteção.",
        "application": "IPL, frequência mitigada, risco residual, decisão de barreiras.",
        "status_note": "Referência técnica curada. Verificar edição física/digital utilizada pela equipe.",
    },
    {
        "id": "CCPS RBPS",
        "tag": "CCPS",
        "area": "Governança PSM",
        "title": "Risk Based Process Safety",
        "desc": "Estrutura de pilares e elementos de gestão para segurança de processos.",
        "application": "Governança, indicadores, cultura, integridade e ciclo de melhoria.",
        "status_note": "Referência técnica curada. Confirmar versão institucional adotada.",
    },
    {
        "id": "AACE Class 5",
        "tag": "AACE",
        "area": "Estimativa de Custos",
        "title": "Class 5 Estimate",
        "desc": "Faixa conceitual de estimativa em estágio inicial para apoio à decisão.",
        "application": "Order-of-magnitude, estimativas preliminares CAPEX/OPEX.",
        "status_note": "Modelo referencial curado. Ajustar à prática interna da empresa.",
    },
    {
        "id": "CCPS Guidelines for Chemical Reactivity Evaluation",
        "tag": "CCPS",
        "area": "Reatividade",
        "title": "Chemical Reactivity Evaluation and Application",
        "desc": "Diretrizes para avaliação de incompatibilidade, runaway e riscos reativos.",
        "application": "Triagem reativa, incompatibilidades e cenários térmicos.",
        "status_note": "Referência técnica curada. Validar edição consultada.",
    },
]

NORMS_LOOKUP = {item["id"]: item for item in NORMS_DB}

MODULE_GOVERNANCE = {
    "Visão Executiva": {
        "basis": "Consolidação executiva baseada em KPIs do caso, criticidade, plano de ação consolidado e estimativas conceituais de investimento.",
        "refs": ["CCPS RBPS", "OSHA 1910.119", "AACE Class 5"],
        "confidence": "Alta",
    },
    "Engenharia": {
        "basis": "Resultados de engenharia baseados em propriedades do composto, envelopes de inflamabilidade e cálculos determinísticos preliminares.",
        "refs": ["NFPA 69", "API 520", "API 521", "CCPS Guidelines for Chemical Reactivity Evaluation"],
        "confidence": "Alta",
    },
    "Análise de Risco": {
        "basis": "Estruturação de cenários, desvios e barreiras com leitura técnica voltada a PHA, SIF e análise semiquantitativa.",
        "refs": ["IEC 61882", "IEC 61511", "CCPS LOPA"],
        "confidence": "Alta",
    },
    "Mudanças": {
        "basis": "Fluxo de governança para mudança e pré-partida segura com foco em integridade operacional e rastreabilidade.",
        "refs": ["OSHA 1910.119", "CCPS RBPS"],
        "confidence": "Média-Alta",
    },
    "Base de Conhecimento": {
        "basis": "Consulta curada de normas, referências e incidentes para suporte à decisão em engenharia e PSM.",
        "refs": ["API 520", "API 521", "OSHA 1910.119", "IEC 61511", "IEC 61882", "NFPA 69", "CCPS LOPA"],
        "confidence": "Alta",
    },
}


# ==============================================================================
# FUNÇÕES DE APOIO
# ==============================================================================
def is_valid_df(df):
    return isinstance(df, pd.DataFrame) and not df.empty


def safe_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def normalize_whitespace(value):
    if not isinstance(value, str):
        return value
    value = value.replace("\xa0", " ")
    value = value.replace("Â\xa0", " ")
    value = value.replace("Â ", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def get_action_col(df):
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


def translate_value(value, mapping):
    if not isinstance(value, str):
        return value
    key = normalize_whitespace(value).lower()
    return mapping.get(key, normalize_whitespace(value))


def get_norm_ref_list(ref_ids: list[str] | None):
    if not ref_ids:
        return []
    return [NORMS_LOOKUP[ref] for ref in ref_ids if ref in NORMS_LOOKUP]


def load_profile_with_feedback(query: str):
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
    fig = go.Figure()
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


def metric_card(label: str, value: str, klass: str = "risk-blue", mono: bool = False) -> str:
    extra = "metric-mono" if mono else ""
    return (
        f"<div class='metric-box'>"
        f"<div class='metric-label'>{label}</div>"
        f"<div class='metric-value {klass} {extra}'>{value}</div>"
        f"</div>"
    )


def render_reference_chips(refs: list[str] | None) -> str:
    if not refs:
        return ""
    chips = "".join(
        f"<span class='ref-chip'>{normalize_whitespace(ref)}</span>"
        for ref in refs
    )
    return f"<div class='ref-chip-wrap'>{chips}</div>"


def render_hero_panel(title: str, subtitle: str, kicker: str = "Process Safety Intelligence") -> None:
    st.markdown(
        f"""
        <div class="hero-panel">
            <div class="hero-kicker">{kicker}</div>
            <div class="hero-title">{title}</div>
            <div class="hero-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_trust_ribbon(module_name: str, basis: str, refs: list[str] | None = None, confidence: str = "Alta") -> None:
    refs_html = render_reference_chips(refs)
    st.markdown(
        f"""
        <div class="trust-ribbon">
            <div class="trust-left">
                <div class="trust-kicker">Safety Basis</div>
                <div class="trust-title">{module_name}</div>
                <div class="trust-text">{basis}</div>
                {refs_html}
            </div>
            <div class="trust-right">
                <div class="trust-pill">Confiança {confidence}</div>
                <div class="trust-meta">Rastreabilidade técnica habilitada</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _html_list(items):
    if not items:
        return "<li>—</li>"
    return "".join(f"<li>{normalize_whitespace(str(item))}</li>" for item in items)


def _html_inputs(inputs: dict | None):
    if not inputs:
        return (
            "<div class='evidence-input-item'>"
            "<div class='evidence-input-label'>Entrada</div>"
            "<div class='evidence-input-value'>—</div>"
            "</div>"
        )

    blocks = []
    for k, v in inputs.items():
        blocks.append(
            (
                "<div class='evidence-input-item'>"
                f"<div class='evidence-input-label'>{normalize_whitespace(str(k))}</div>"
                f"<div class='evidence-input-value'>{normalize_whitespace(str(v))}</div>"
                "</div>"
            )
        )
    return "".join(blocks)


def render_evidence_panel(
    title: str,
    purpose: str,
    method: str,
    references: list[str] | None = None,
    assumptions: list[str] | None = None,
    inputs: dict | None = None,
    formula: str | None = None,
    note: str | None = None,
):
    references = references or []
    assumptions = assumptions or []
    inputs = inputs or {}
    formula_html = normalize_whitespace(formula) if formula else "—"
    note_html = normalize_whitespace(note) if note else "Sem observações adicionais."

    st.markdown(
        """
        <div class="evidence-panel">
            <div class="evidence-kicker">Painel de Evidências por Cálculo</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown(f"### {title}")
        st.caption(purpose)

        c1, c2 = st.columns(2)

        with c1:
            with st.container(border=True):
                st.markdown("#### Método e Referências")
                st.markdown(f"- **Método:** {normalize_whitespace(method)}")
                if references:
                    for ref in references:
                        st.markdown(f"- {normalize_whitespace(ref)}")
                else:
                    st.markdown("- —")

            with st.container(border=True):
                st.markdown("#### Hipóteses / Limites")
                if assumptions:
                    for item in assumptions:
                        st.markdown(f"- {normalize_whitespace(item)}")
                else:
                    st.markdown("- —")

        with c2:
            with st.container(border=True):
                st.markdown("#### Entradas Relevantes")
                if inputs:
                    input_cols = st.columns(2)
                    items = list(inputs.items())
                    for idx, (k, v) in enumerate(items):
                        with input_cols[idx % 2]:
                            st.caption(normalize_whitespace(str(k)))
                            st.markdown(f"**{normalize_whitespace(str(v))}**")
                else:
                    st.markdown("—")

            with st.container(border=True):
                st.markdown("#### Expressão / Lógica")
                st.code(formula_html, language="text")

        with st.container(border=True):
            st.markdown("#### Observação de Aplicabilidade")
            st.markdown(f"- {note_html}")

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


# ==============================================================================
# ESTADO DA SESSÃO
# ==============================================================================
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
if "audit_mode" not in st.session_state:
    st.session_state.audit_mode = True
if "psv_result" not in st.session_state:
    st.session_state.psv_result = None
if "psv_inputs" not in st.session_state:
    st.session_state.psv_inputs = None
if "tmr_result" not in st.session_state:
    st.session_state.tmr_result = None
if "tmr_inputs" not in st.session_state:
    st.session_state.tmr_inputs = None


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


# ==============================================================================
# SIDEBAR
# ==============================================================================
with st.sidebar:
    lang = st.radio("🌐 Idioma", ["pt", "en"], horizontal=True, label_visibility="collapsed")
    st.session_state.lang = lang

    st.markdown(f"## ⚗️ {t('app_title', lang)}\n**Enterprise Edition v2.5**")
    st.caption("Process Safety Intelligence Engine")
    st.session_state.audit_mode = st.toggle(
        "Modo Auditoria / Evidências",
        value=st.session_state.audit_mode,
        help="Exibe base normativa, rastreabilidade e fundamento técnico do módulo.",
    )
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

if st.session_state.audit_mode:
    gov = MODULE_GOVERNANCE.get(
        selected_module,
        {"basis": "Base técnica curada.", "refs": [], "confidence": "Média"},
    )
    render_trust_ribbon(
        module_name=selected_module,
        basis=gov["basis"],
        refs=gov["refs"],
        confidence=gov["confidence"],
    )

# ==============================================================================
# DADOS GLOBAIS
# ==============================================================================
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
# MÓDULO 1: VISÃO EXECUTIVA
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
        render_hero_panel(
            title="Cockpit Executivo de Segurança de Processos",
            subtitle="Visão consolidada da prontidão do caso, gaps críticos e ações abertas para acelerar decisão com governança técnica.",
        )

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="KPIs executivos do caso",
                purpose="Este painel consolida prontidão, gaps críticos e pendências para leitura gerencial rápida com foco em PSM e execução.",
                method="Agregação interna de readiness do caso + plano de ação consolidado + criticidade registrada.",
                references=["CCPS RBPS", "OSHA 1910.119", "AACE Class 5"],
                assumptions=[
                    "Indicadores têm caráter gerencial e de priorização, não substituindo estudo formal detalhado.",
                    "A maturidade global depende da qualidade dos dados alimentados no caso.",
                    "A criticidade consolidada reflete o estado atual do conjunto de ações disponível no app.",
                ],
                inputs={
                    "Maturidade global": f"{cri_data.get('index', 0)}%",
                    "Ações pendentes": num_acoes_pendentes,
                    "Gaps críticos": gaps_criticos,
                    "Modo auditoria": "Ativo",
                },
                formula="CRI = função consolidada do caso\nGaps críticos = contagem de ações com criticidade Alta/Crítica\nPendências = total de ações abertas/consolidadas",
                note="Painel executivo voltado a priorização. Para aprovação de investimento ou aceite de risco, complementar com revisão técnica formal.",
            )

        st.markdown("<div class='panel'><h3>KPIs Executivos</h3></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.markdown(metric_card("Maturidade Global", f"{cri_data['index']}%", cri_data["color_class"], mono=True), unsafe_allow_html=True)
        c2.markdown(metric_card("Ações Pendentes", str(num_acoes_pendentes), "risk-amber" if num_acoes_pendentes > 0 else "risk-green", mono=True), unsafe_allow_html=True)
        c3.markdown(metric_card("Gaps Críticos", str(gaps_criticos), "risk-red" if gaps_criticos > 0 else "risk-green", mono=True), unsafe_allow_html=True)

        left, right = st.columns(2)
        with left:
            st.markdown("<div class='panel'><h3>Índice de Prontidão do Caso (CRI)</h3></div>", unsafe_allow_html=True)
            st.plotly_chart(render_modern_gauge(cri_data["index"], cri_data["band"]), use_container_width=True, theme=None, config={"displayModeBar": False})
        with right:
            st.markdown("<div class='panel'><h3>Distribuição por Pilares</h3></div>", unsafe_allow_html=True)
            st.plotly_chart(render_modern_radar(cri_data), use_container_width=True, theme=None, config={"displayModeBar": False})

    elif exec_tab == "Action Plan":
        render_hero_panel(
            title="Action Hub com Priorização e Faixa de Investimento",
            subtitle="As ações são organizadas para execução operacional, com criticidade, responsável, prazo e estimativa financeira de referência.",
            kicker="Execution Readiness",
        )

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="Estimativa preliminar do Action Hub",
                purpose="O orçamento consolidado usa classificação por palavras-chave técnicas e faixas conceituais tipo Classe 5 para orientar decisão inicial.",
                method="Roteamento textual da ação para pacotes CAPEX/OPEX + biblioteca interna AACE/CCPS.",
                references=["AACE Class 5", "CCPS RBPS"],
                assumptions=[
                    "Estimativa conceitual preliminar, sem caráter de proposta comercial nem orçamento executivo.",
                    "Classificação depende da qualidade semântica do texto da ação.",
                    "Faixas devem ser recalibradas à realidade da planta, fornecedor e escopo final.",
                ],
                inputs={
                    "Ações consolidadas": len(action_df_dash) if has_actions else 0,
                    "Critérios": "keyword routing + hierarquia",
                    "Saída": "CAPEX/OPEX + faixa min/P50/máx",
                },
                formula="Ação -> pacote técnico -> recurso -> faixa min/P50/máx\nOrçamento total = soma das ações abertas",
                note="Use este painel para triagem e priorização. Para CAPEX formal, aplicar engenharia de escopo e orçamento detalhado.",
            )

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
                st.plotly_chart(render_action_donut(action_df_dash), use_container_width=True, theme=None, config={"displayModeBar": False})
            with col_chart2:
                st.plotly_chart(render_action_bar(action_df_dash), use_container_width=True, theme=None, config={"displayModeBar": False})
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
                "Status": st.column_config.SelectboxColumn("Status", options=["Aberto", "Em Andamento", "Aguardando Verba", "Fechado"], required=True),
                "Responsável": st.column_config.SelectboxColumn("Responsável", options=["Engenharia", "Manutenção", "Operação", "HSE"]),
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

            disabled_cols = [col_acao, "Recurso", "Hierarquia NIOSH", "Pacote AACE", "Custo Min (R$)", "Custo P50 (R$)", "Custo Máx (R$)"]
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
            st.progress(fechadas / total if total > 0 else 0.0, text=f"Progresso: {fechadas}/{total} ações concluídas")

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
                    acoes_resp = edited_df[(edited_df["Status"] != "Fechado") & (edited_df["Responsável"] == resp)]
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
        render_hero_panel(
            title="Relatório Executivo Automatizado",
            subtitle="Geração rápida de documento consolidado do caso com foco em comunicação técnica e tomada de decisão.",
            kicker="Reporting",
        )
        st.markdown("<div class='panel'><h3>Gerador de Relatório Executivo</h3></div>", unsafe_allow_html=True)
        report_case_name = st.text_input("Nome do Relatório", value=st.session_state.current_case_name or profile.identity.get("name", "Caso"))
        if st.button("Gerar Relatório Completo", type="primary"):
            st.session_state.report_bundle = build_executive_bundle(
                case_name=report_case_name,
                profile=profile,
                context={"lopa_result": st.session_state.get("lopa_result")},
            )
            st.success("Relatório Compilado!")
        if st.session_state.get("report_bundle"):
            st.download_button("📥 Baixar Documento (HTML)", st.session_state.report_bundle["html"], file_name=f"{report_case_name}.html")

    elif exec_tab == "Meus Projetos":
        render_hero_panel(
            title="Gestão de Projetos e Casos",
            subtitle="Salve e recupere estudos em andamento para manter continuidade analítica e rastreabilidade do trabalho.",
            kicker="Project Memory",
        )
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
# MÓDULO 2: ENGENHARIA
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
        render_hero_panel(
            title="Base de Propriedades e Comportamento do Ativo",
            subtitle="Leitura rápida do composto com foco em risco de processo, propriedades-chave e suporte a decisões de projeto e operação.",
            kicker="Engineering View",
        )

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="Perfil do composto e classificação de dispersão",
                purpose="Painel de leitura rápida para apoiar engenharia, segurança de processos e resposta inicial sobre o ativo analisado.",
                method="Perfil do composto gerado pelo motor do app + classificação de dispersão por regras internas.",
                references=["CCPS RBPS"],
                assumptions=[
                    "Os dados do composto dependem da qualidade do identificador usado na busca.",
                    "A classificação de dispersão é assistiva e não substitui modelagem formal de dispersão.",
                    "Validação adicional é necessária para estudo QRA ou projeto de mitigação.",
                ],
                inputs={
                    "Ativo": profile.identity.get("name", "—"),
                    "CAS": profile.identity.get("cas", "—"),
                    "Peso molecular": f"{profile.identity.get('molecular_weight', '—')} g/mol",
                    "Confiança do perfil": f"{safe_float(getattr(profile, 'confidence_score', 0)):.0f}%",
                },
                formula="Perfil = identidade + perigos + propriedades\nDispersão = classificação assistida por regras do motor interno",
                note="Use este painel como base de triagem técnica. Para engenharia final, confirmar dados físico-químicos com referência oficial adotada pela empresa.",
            )

        dispersion_mode = classify_dispersion_mode(profile)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(metric_card("Ativo Base", profile.identity.get("name", "—")), unsafe_allow_html=True)
        c2.markdown(metric_card("Peso Molar", f"{profile.identity.get('molecular_weight', '—')} g/mol", mono=True), unsafe_allow_html=True)
        c3.markdown(metric_card("Dispersão", dispersion_mode["label"]), unsafe_allow_html=True)
        c4.markdown(metric_card("Confiança", f"{getattr(profile, 'confidence_score', 0):.0f}%", mono=True), unsafe_allow_html=True)

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
        render_hero_panel(
            title="Envelope de Inflamabilidade e Faixa Operacional de Purga",
            subtitle="Ferramenta visual para raciocínio preliminar de inertização, envelope seguro e margem operacional durante partida e parada.",
            kicker="Explosion Prevention",
        )

        lfl_val = safe_float(profile.limit("LEL_vol", 5.0), 5.0)
        ufl_val = safe_float(profile.limit("UEL_vol", 15.0), 15.0)

        st.markdown("<div class='panel'><h3>⚠️ Envelope de Inflamabilidade & Purga de Reatores</h3></div>", unsafe_allow_html=True)
        st.markdown("<div class='note-card'>Calcule a atmosfera segura durante partidas e paradas. Para evitar a mistura explosiva, a concentração de O₂ deve operar abaixo da <b>Limiting Oxygen Concentration (LOC)</b>.</div>", unsafe_allow_html=True)

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

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="Envelope O₂ vs combustível para inertização",
                purpose="Apoiar decisão preliminar sobre faixa segura de operação abaixo da concentração limite de oxidante.",
                method="Representação gráfica simplificada do envelope com LFL, UFL e LOC informados/estimados.",
                references=["NFPA 69"],
                assumptions=[
                    "Modelo visual simplificado para suporte inicial, não substituindo validação detalhada do sistema real.",
                    "LFL, UFL e LOC devem ser confirmados para mistura, temperatura, pressão e diluentes específicos.",
                    "A margem de alarme aqui é conservadora e assistiva.",
                ],
                inputs={
                    "LFL": f"{lfl:.2f} % vol combustível",
                    "UFL": f"{ufl:.2f} % vol combustível",
                    "LOC": f"{loc:.2f} % vol O₂",
                    "Margem sugerida": f"O₂ < {loc*0.6:.2f} %",
                },
                formula="Operação segura preliminar: O₂ < LOC\nMargem interna sugerida no painel: O₂ < 0.6 × LOC",
                note="Use o gráfico para raciocínio preliminar. Em projeto ou autorização operacional, confirmar LOC, estratégia de purga, instrumentação e lógica permissiva.",
            )

    elif eng_tab == "Emergências (PSV/Runaway)":
        render_hero_panel(
            title="Toolkit de Emergências de Processo",
            subtitle="Ferramentas rápidas para sizing preliminar de alívio e leitura inicial de runaway térmico em modo de apoio à decisão.",
            kicker="Emergency Engineering",
        )

        st.markdown("<div class='panel'><h3>Cálculos de Emergência</h3></div>", unsafe_allow_html=True)
        st.markdown("<div class='note-card'>Os cálculos abaixo são preliminares e devem ser usados como apoio à triagem de engenharia. Para projeto final, revisar cenários, hipóteses e referência normativa oficial.</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.markdown("#### 🔥 Dimensionamento de Alívio (API 520)")
                with st.popover("⚙️ Configurar Parâmetros da Válvula"):
                    w = st.number_input("Vazão (kg/h)", 10000.0)
                    p = st.number_input("Pressão Setpoint (kPag)", 500.0)
                    t_rel = st.number_input("Temp. no Alívio (°C)", 50.0)

                if st.button("Executar Sizing", use_container_width=True, type="primary"):
                    mw = safe_float(profile.identity.get("molecular_weight", 28.0), 28.0)
                    res = size_psv_gas(w, t_rel, p, 1.0, mw)
                    st.session_state.psv_result = res
                    st.session_state.psv_inputs = {
                        "Vazão": f"{w:.2f} kg/h",
                        "Set pressure": f"{p:.2f} kPag",
                        "Temperatura": f"{t_rel:.2f} °C",
                        "Peso molecular": f"{mw:.2f} g/mol",
                    }
                    st.success(f"Orifício preliminar: **Letra {res['api_letter']}** ({res['api_area_mm2']} mm²)")

            if st.session_state.get("psv_result"):
                res = st.session_state.psv_result
                st.info(f"Resultado armazenado: API Letter **{res['api_letter']}** | Área **{res['api_area_mm2']} mm²**")
                if st.session_state.audit_mode:
                    render_evidence_panel(
                        title="Sizing preliminar de alívio gasoso",
                        purpose="Fornecer leitura rápida do orifício API preliminar para triagem de engenharia.",
                        method="Rotina interna de cálculo para gás com saída em letra/área API.",
                        references=["API 520", "API 521"],
                        assumptions=[
                            "Leitura preliminar para triagem. Não substitui definição completa de cenário de alívio.",
                            "Cenário de contingência, backpressure, propriedades reais e acúmulo devem ser revisados externamente.",
                            "Confirmar unidade, estado do fluido e critério aplicável ao caso real.",
                        ],
                        inputs=st.session_state.get("psv_inputs"),
                        formula="A_orifício = f(vazão, pressão, temperatura, MW, coeficientes e hipótese de gás)",
                        note="Resultado útil para screening inicial. Para projeto final, revisar cenário, fluidodinâmica e exigências normativas detalhadas.",
                    )

        with c2:
            with st.container(border=True):
                st.markdown("#### ⚡ Runaway Térmico (Triagem)")
                with st.popover("⚙️ Configurar Cinética"):
                    t0 = st.number_input("Temp. Processo (°C)", 80.0)
                    ea = st.number_input("Energia Ativação (kJ/mol)", 100.0)

                if st.button("Estimar TMR (Time to Maximum Rate)", use_container_width=True):
                    res = calculate_tmr_adiabatic(t0, ea, 1e12, 1500, 2.5)
                    st.session_state.tmr_result = res
                    st.session_state.tmr_inputs = {
                        "Temperatura inicial": f"{t0:.2f} °C",
                        "Energia de ativação": f"{ea:.2f} kJ/mol",
                        "Modelo": "Triagem adiabática",
                    }
                    st.error(f"Tempo estimado p/ máximo térmico: **{res['tmr_min']:.1f} min**")

            if st.session_state.get("tmr_result"):
                res = st.session_state.tmr_result
                st.warning(f"Resultado armazenado: TMR estimado **{res['tmr_min']:.1f} min**")
                if st.session_state.audit_mode:
                    render_evidence_panel(
                        title="Triagem de runaway térmico",
                        purpose="Estimar rapidamente a severidade temporal de um cenário térmico adiabático para priorização de salvaguardas.",
                        method="Rotina interna de triagem adiabática usando entrada cinética simplificada.",
                        references=["CCPS Guidelines for Chemical Reactivity Evaluation"],
                        assumptions=[
                            "Modelo simplificado para screening, não substitui calorimetria reativa nem estudo dedicado.",
                            "Regime assumido como adiabático de triagem.",
                            "Parâmetros cinéticos informados devem ser tratados como aproximados quando não vierem de ensaio.",
                        ],
                        inputs=st.session_state.get("tmr_inputs"),
                        formula="TMR = f(T0, Ea, parâmetros cinéticos, hipótese adiabática)",
                        note="Use para triagem de severidade. Para decisão de projeto, complementar com dados experimentais e análise térmica formal.",
                    )

# ==============================================================================
# MÓDULO 3: ANÁLISE DE RISCO
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
        render_hero_panel(
            title="HAZOP Builder com Topologia Assistida",
            subtitle="Estruture nós, desvios, causas, consequências e salvaguardas em uma experiência mais legível para workshop técnico.",
            kicker="Risk Study Workspace",
        )

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="Geração assistida de matriz HAZOP",
                purpose="Suportar workshops e pré-estruturação do estudo com base na topologia selecionada.",
                method="Mapeamento assistido de equipamentos/linhas para cenários HAZOP e matriz de desvios.",
                references=["IEC 61882"],
                assumptions=[
                    "A saída é assistiva e não substitui workshop formal com equipe multidisciplinar.",
                    "A qualidade da matriz depende da topologia e dos equipamentos selecionados.",
                    "Salvaguardas e recomendações exigem revisão humana antes de congelamento.",
                ],
                inputs={
                    "Nó atual": st.session_state.current_node_name,
                    "Modo": "Grafo / processamento em lote",
                    "Saída": "Matriz HAZOP + C&E assistida",
                },
                formula="Topologia + tipo de equipamento -> cenários de desvio -> causas/consequências/salvaguardas",
                note="Use a geração como ponto de partida de estudo. A consolidação final deve ocorrer em sessão HAZOP validada.",
            )

        st.markdown("<div class='panel'><h3>Geração Inteligente de P&ID e HAZOP</h3></div>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["Nó Único (Grafo)", "Lote Múltiplos Nós (CSV)"])

        with t1:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.session_state.current_node_name = st.text_input("Identificação do Nó", value=st.session_state.current_node_name)
            with col2:
                selected_equipment = st.multiselect(
                    "Equipamentos e Linhas (Em Ordem)",
                    options=list(EQUIPMENT_PARAMETERS.keys()),
                    default=["Tanque de Armazenamento Atmosférico", "Tubulação / Linha de Transferência", "Bomba Centrífuga"],
                )

            if selected_equipment:
                dot = graphviz.Digraph()
                dot.attr(rankdir="LR", bgcolor="transparent")
                dot.attr("node", shape="box", style="filled", fillcolor="#1e293b", color="#3b82f6", fontcolor="white", fontname="Inter", penwidth="2")
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
            st.markdown("<div class='note-card'>Importe a Equipment List extraída do seu CAD (Nó, Equipamento).</div>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader("Upload CSV/XLSX", type=["csv", "xlsx"])
            if uploaded_file is not None:
                df_bulk = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
                if st.button("⚡ Executar Processamento em Lote", type="primary"):
                    bulk_results = process_bulk_pid_nodes(df_bulk, profile)
                    if bulk_results:
                        st.session_state.pid_hazop_matrix = bulk_results
                        st.success(f"{len(bulk_results)} cenários gerados para a fábrica inteira.")

        if st.session_state.get("pid_hazop_matrix"):
            st.markdown("<br><hr>", unsafe_allow_html=True)
            df_hazop = pd.DataFrame(st.session_state.pid_hazop_matrix)

            with st.expander("📋 Estudo HAZOP (IEC 61882)", expanded=True):
                view_mode = st.radio("Modo de Leitura:", ["🗂️ Cards (Discussão de Reunião)", "📊 Tabela Otimizada (Text Wrap)"], horizontal=True, label_visibility="collapsed")
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
                st.download_button("📥 Exportar CSV", df_hazop.to_csv(index=False).encode("utf-8"), "hazop_export.csv", "text/csv")

            with st.expander("🔀 Matriz Causa e Efeito p/ Automação (IEC 61511)", expanded=False):
                df_ce = generate_ce_matrix_from_hazop(st.session_state.pid_hazop_matrix)
                if is_valid_df(df_ce):
                    st.dataframe(df_ce, width="stretch", hide_index=True)
                    st.download_button("📥 Exportar C&E", df_ce.to_csv(index=False).encode("utf-8"), "ce_matrix.csv", "text/csv")
                else:
                    st.info("Nenhuma arquitetura de Trip (Intertravamento) foi deduzida dos cenários atuais.")

    elif risk_tab == "Verificação SIL (IEC)":
        render_hero_panel(
            title="Verificação Paramétrica de SIL / PFDavg",
            subtitle="Leitura rápida da robustez da arquitetura de intertravamento com base em hipótese simplificada de falha perigosa e intervalo de teste.",
            kicker="Functional Safety",
        )

        st.markdown("<div class='panel'><h3>🖲️ Análise de Arquitetura de Intertravamento (IEC 61511)</h3></div>", unsafe_allow_html=True)
        st.markdown("<div class='note-card'>Cálculo paramétrico da Probabilidade Média de Falha sob Demanda (PFDavg) garantindo leitura preliminar da malha SIF.</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            arq = st.selectbox("Arquitetura de Sensores/Válvulas", ["1oo1 (Simplex)", "1oo2 (Redundante)", "2oo3 (Votação)"])
            lambda_du = st.number_input("Taxa de Falha Perigosa (λdu) - falhas/hora", 1e-6, format="%.2e")
            ti_meses = st.number_input("Intervalo de Teste (Proof Test - Meses)", 12)
            ti_horas = ti_meses * 730

        with col2:
            st.markdown("#### Memorial de Cálculo (IEC)")
            if "1oo1" in arq:
                formula = r"PFD_{avg} = \lambda_{DU} \times \frac{TI}{2}"
                st.latex(formula)
                pfd_avg = lambda_du * (ti_horas / 2)
            elif "1oo2" in arq:
                formula = r"PFD_{avg} \approx \frac{(\lambda_{DU} \times TI)^2}{3} + \beta \times \lambda_{DU} \times \frac{TI}{2}"
                st.latex(formula)
                st.caption("*Assumindo fator de causa comum (β) = 10%*")
                pfd_avg = (((lambda_du * ti_horas) ** 2) / 3) + (0.10 * lambda_du * (ti_horas / 2))
            else:
                formula = r"PFD_{avg} \approx (\lambda_{DU} \times TI)^2 + \beta \times \lambda_{DU} \times \frac{TI}{2}"
                st.latex(formula)
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

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="Verificação paramétrica de PFDavg",
                purpose="Oferecer leitura preliminar de atendimento SIL sob hipóteses simplificadas de arquitetura, falha perigosa e intervalo de teste.",
                method="Equações simplificadas por arquitetura 1oo1, 1oo2 e 2oo3 com hipótese de β = 10% em redundância.",
                references=["IEC 61511"],
                assumptions=[
                    "Leitura preliminar. Não substitui cálculo SIL verification formal.",
                    "Assume β fixo de 10% nos casos redundantes.",
                    "Não contempla todos os fatores reais de proof test coverage, bypass, repair, diagnostics e common cause detalhado.",
                ],
                inputs={
                    "Arquitetura": arq,
                    "λDU": f"{lambda_du:.2e} falhas/h",
                    "Proof test interval": f"{ti_meses} meses",
                    "TI": f"{ti_horas} h",
                    "Resultado": f"{pfd_avg:.2e} ({sil})",
                },
                formula=formula,
                note="Painel útil para screening e comparações. Para especificação de SIF, conduzir cálculo formal conforme procedimento da organização.",
            )

    elif risk_tab == "QRA Social":
        render_hero_panel(
            title="Curva F-N de Risco Social",
            subtitle="Visualização ilustrativa para posicionamento preliminar do risco social frente a envelopes de tolerabilidade.",
            kicker="Risk Communication",
        )

        st.markdown("<div class='panel'><h3>Curva F-N de Risco Social</h3></div>", unsafe_allow_html=True)
        fig_fn = go.Figure()
        fig_fn.add_trace(go.Scatter(x=[1, 10, 100], y=[1e-4, 1e-5, 1e-6], name="Limite Tolerável", line=dict(color="red", dash="dash")))
        fig_fn.add_trace(go.Scatter(x=[1, 10, 100], y=[1e-5, 1e-6, 1e-7], name="Limite Desprezível", line=dict(color="green", dash="dash")))
        fig_fn.add_trace(go.Scatter(x=[10], y=[2e-5], mode="markers+text", text=["Risco Planta"], textposition="top center", marker=dict(size=12, color="white")))
        fig_fn.update_layout(
            xaxis_type="log",
            yaxis_type="log",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#9ca3af",
            height=400,
        )
        st.plotly_chart(fig_fn, use_container_width=True, theme=None)

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="Curva F-N ilustrativa",
                purpose="Apoiar comunicação preliminar de risco social de forma visual e executiva.",
                method="Gráfico ilustrativo com envelopes de tolerabilidade e ponto representativo da planta.",
                references=["CCPS RBPS"],
                assumptions=[
                    "Gráfico atual é ilustrativo e não resulta de um QRA quantitativo completo.",
                    "Não usar para licenciamento, aceite formal de risco ou justificativa regulatória.",
                    "Exige modelagem quantitativa formal para aplicação decisória robusta.",
                ],
                inputs={
                    "Escala": "Log-log",
                    "Limites": "Tolerável / Desprezível",
                    "Status": "Demonstrativo",
                },
                formula="F(N) vs N em escala logarítmica",
                note="Painel intencionalmente didático. Para uso formal, substituir por resultados oriundos de QRA quantitativo real.",
            )

# ==============================================================================
# MÓDULO 4: MUDANÇAS
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
        render_hero_panel(
            title="Avaliação de Gestão de Mudança",
            subtitle="Classificação inicial de mudança com foco em impacto técnico, proteções afetadas e necessidade de governança adicional.",
            kicker="Management of Change",
        )
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
            st.success("MOC submetido e classificado.")

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="Classificação inicial de MOC",
                purpose="Ajudar a equipe a identificar se a mudança demanda fluxo formal de gestão, revisão de barreiras e governança complementar.",
                method="Triagem assistida por tipo de mudança, impactos críticos e condições restritivas selecionadas.",
                references=["OSHA 1910.119", "CCPS RBPS"],
                assumptions=[
                    "A decisão final de MOC deve seguir o procedimento interno da organização.",
                    "A triagem depende da completude das respostas fornecidas pelo usuário.",
                    "Mudanças complexas podem exigir revisão multidisciplinar adicional.",
                ],
                inputs={
                    "Tipo": change_type,
                    "Impactos": ", ".join(impacts) if impacts else "Nenhum selecionado",
                    "Temporária": "Sim" if p1 else "Não",
                    "Override/bypass": "Sim" if p2 else "Não",
                },
                formula="Mudança + impactos + restrições -> necessidade de governança adicional",
                note="Use a saída como triagem inicial. Abertura formal de MOC deve obedecer o procedimento documentado da empresa.",
            )

    elif chg_tab == "PSSR (Inspeção Pré-Partida)":
        render_hero_panel(
            title="Checklist de Pré-Partida Segura",
            subtitle="Consolide verificações críticas antes de partida ou retorno à operação após modificação relevante.",
            kicker="Pre-Startup Safety Review",
        )
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
            st.success("Status operacional emitido.")

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="Checklist PSSR assistido",
                purpose="Apoiar a revisão pré-partida de itens críticos de prontidão operacional.",
                method="Checklist estruturado com foco em construção, procedimentos, proteções e testes de automação.",
                references=["OSHA 1910.119", "CCPS RBPS"],
                assumptions=[
                    "Checklist é assistivo e não substitui a rotina formal da organização.",
                    "Itens não marcados exigem avaliação antes da liberação.",
                    "Pode haver requisitos locais adicionais de engenharia, manutenção e operação.",
                ],
                inputs={
                    "P&ID validado": "Sim" if d1 else "Não",
                    "Procedimentos revisados": "Sim" if d2 else "Não",
                    "SIS/PSVs verificados": "Sim" if d4 else "Não",
                    "C&E validada": "Sim" if d5 else "Não",
                },
                formula="Checklist crítico -> prontidão operacional preliminar",
                note="Use como apoio visual. A autorização de partida deve seguir o fluxo formal de PSSR da planta.",
            )

# ==============================================================================
# MÓDULO 5: BASE DE CONHECIMENTO
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
        render_hero_panel(
            title="Biblioteca Curada de Normas e Referências",
            subtitle="Consulta rápida a fundamentos técnicos relevantes para engenharia e segurança de processos. Validar sempre a edição vigente oficial antes de uso formal.",
            kicker="Knowledge Base",
        )

        st.markdown("<div class='note-card'><strong>Importante:</strong> esta é uma base curada interna no app para acelerar consulta. Antes de usar em auditoria, projeto ou aprovação formal, confirme a edição oficial vigente com a fonte publicadora da norma.</div>", unsafe_allow_html=True)

        c_search, c_filter, c_area = st.columns([2.2, 1, 1.2])
        search_term = c_search.text_input("🔍 Buscar por código, título ou palavra-chave...", placeholder="Ex: API 520, HAZOP, SIS...")
        tag_filter = c_filter.selectbox("Entidade", ["Todos", "API", "OSHA", "IEC", "NFPA", "CCPS", "AACE"])
        area_filter = c_area.selectbox("Área", ["Todas"] + sorted(list({n["area"] for n in NORMS_DB})))

        filtered_normas = []
        for n in NORMS_DB:
            s = search_term.lower().strip()
            matches_search = (
                s in n["id"].lower()
                or s in n["title"].lower()
                or s in n["desc"].lower()
                or s in n["application"].lower()
            ) if s else True
            matches_tag = (tag_filter == "Todos" or n["tag"] == tag_filter)
            matches_area = (area_filter == "Todas" or n["area"] == area_filter)
            if matches_search and matches_tag and matches_area:
                filtered_normas.append(n)

        cols = st.columns(2)
        for idx, norma in enumerate(filtered_normas):
            with cols[idx % 2]:
                st.markdown(
                    f"""
                    <div class="doc-card">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                            <span style="color:#9ca3af; font-size:0.8rem; font-weight:700;">{norma['tag']}</span>
                            <span class="doc-tag">{norma['area']}</span>
                        </div>
                        <span class="doc-title">{norma['id']} — {norma['title']}</span>
                        <p class="doc-desc"><strong>Escopo:</strong> {norma['desc']}</p>
                        <p class="doc-desc"><strong>Aplicação típica:</strong> {norma['application']}</p>
                        <p class="doc-desc"><strong>Nota:</strong> {norma['status_note']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.write("")

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="Base interna de normas do app",
                purpose="Permitir consulta rápida e estruturada de referências técnicas relevantes ao fluxo do software.",
                method="Biblioteca local curada embutida no app com tags, área, escopo e aplicação típica.",
                references=[n["id"] for n in filtered_normas[:6]] if filtered_normas else ["CCPS RBPS"],
                assumptions=[
                    "A base não é uma sincronização automática com publishers ou bases regulatórias oficiais.",
                    "A edição vigente deve ser confirmada externamente antes de uso formal.",
                    "A biblioteca foi desenhada para apoio de engenharia e não para substituir gestão documental corporativa.",
                ],
                inputs={
                    "Itens exibidos": len(filtered_normas),
                    "Filtro entidade": tag_filter,
                    "Filtro área": area_filter,
                    "Busca": search_term or "Sem filtro textual",
                },
                formula="Consulta = filtro textual + entidade + área",
                note="Esta biblioteca melhora velocidade e padronização da consulta. Para compliance formal, integrar futuramente com gestão documental oficial da empresa.",
            )

    elif kb_tab == "Incidentes Históricos":
        render_hero_panel(
            title="Incidentes Históricos e Lições Aprendidas",
            subtitle="Contextualize o risco do ativo com eventos históricos relacionados para enriquecer discussão de barreiras, consequências e governança.",
            kicker="Lessons Learned",
        )

        st.markdown("<div class='panel'><h3>📚 Banco de Incidentes e Lições Aprendidas</h3></div>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #9ca3af; margin-bottom: 30px;'>Filtrando falhas históricas globais relacionadas à substância <b>{profile.identity.get('name')}</b>.</p>", unsafe_allow_html=True)

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
            st.info(f"Nenhum incidente catastrófico catalogado especificamente para {profile.identity.get('name')} na base curada atual.")

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="Incidentes históricos relacionados ao ativo",
                purpose="Apoiar análise de lições aprendidas e enriquecer discussão sobre falhas, mecanismos e barreiras relevantes.",
                method="Consulta à base curada interna de incidentes relacionados ao perfil do composto.",
                references=["CCPS RBPS"],
                assumptions=[
                    "Base histórica depende da cobertura interna disponível no projeto.",
                    "Ausência de caso não significa ausência de risco.",
                    "Os eventos exibidos devem ser usados para aprendizado e contextualização, não como substituto de análise local.",
                ],
                inputs={
                    "Ativo": profile.identity.get("name", "—"),
                    "Casos encontrados": len(relevant_cases) if relevant_cases else 0,
                    "Base": "Curada interna",
                },
                formula="Composto/perfil -> busca de casos históricos relacionados",
                note="Os incidentes enriquecem a discussão de risco, mas não substituem estudo específico da instalação.",
            )
