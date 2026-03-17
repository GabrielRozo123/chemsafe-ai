from __future__ import annotations

import io
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# =========================
# Imports opcionais / resilientes
# =========================
try:
    import folium
except Exception:
    folium = None

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

# Projeto base
try:
    from chemicals_seed import LOCAL_COMPOUNDS
except Exception:
    LOCAL_COMPOUNDS = {}

try:
    from compound_engine import build_compound_profile, suggest_hazop_priorities, suggest_lopa_ipls
except Exception:
    build_compound_profile = None
    suggest_hazop_priorities = None
    suggest_lopa_ipls = None

try:
    from comparator import build_comparison_df, build_comparison_highlights
except Exception:
    build_comparison_df = None
    build_comparison_highlights = None

try:
    from source_governance import build_evidence_ledger_df, build_source_recommendations, summarize_evidence
except Exception:
    build_evidence_ledger_df = None
    build_source_recommendations = None
    summarize_evidence = None

try:
    from source_links import build_official_source_links
except Exception:
    build_official_source_links = None

try:
    from bowtie_visual import build_bowtie_custom_figure
except Exception:
    build_bowtie_custom_figure = None

try:
    from deterministic import IPL_CATALOG, compute_lopa, gaussian_dispersion, pool_fire
except Exception:
    IPL_CATALOG = [
        ("PSV — bem mantida", 0.01),
        ("Alarme + ação do operador", 0.1),
        ("SIS / SIL 1", 0.01),
        ("SIS / SIL 2", 0.001),
        ("Dique de contenção", 0.01),
    ]

    def compute_lopa(f_ie: float, criterion: float, chosen: list[tuple[str, float]]) -> dict:
        pfd_total = 1.0
        for _, p in chosen:
            pfd_total *= p
        mcf = f_ie * pfd_total
        ratio = mcf / criterion if criterion else 0
        sil = "Não requerido" if ratio <= 1 else ("SIL 1" if ratio <= 10 else ("SIL 2" if ratio <= 100 else "SIL 3"))
        return {
            "f_ie": f_ie,
            "pfd_total": pfd_total,
            "mcf": mcf,
            "ratio": ratio,
            "sil": sil,
            "selected_ipls": chosen,
        }

    def gaussian_dispersion(q_g_s: float, wind: float, stability: str, idlh_ppm: float, mw: float, h: float) -> dict:
        xs = list(range(25, 3001, 25))
        cs = []
        idlh_gm3 = idlh_ppm * mw / 24.45
        x_idlh = None
        for x in xs:
            sigma = max(8.0, 0.08 * x)
            c = q_g_s / max(wind * sigma * sigma * math.pi, 1e-6)
            c *= math.exp(-(h**2)/(2*sigma**2))
            cs.append(c)
            if x_idlh is None and c <= idlh_gm3:
                x_idlh = x
        c100 = cs[3] if len(cs) > 3 else cs[0]
        return {"xs": xs, "cs": cs, "x_idlh": x_idlh, "c_at_100m": c100, "idlh_gm3": idlh_gm3}

    def pool_fire(diameter: float, burn: float, hc: float, distance: float) -> dict:
        q = burn * hc * (diameter / max(distance, 1.0)) * 0.02
        zone = "Severa" if q > 12.5 else ("Moderada" if q > 4.7 else "Baixa")
        return {"Hf_m": 0.23 * (burn * hc) ** 0.4, "E_kW_m2": 58.0, "q_kW_m2": q, "zone": zone}

try:
    from hazop_db import HAZOP_DB
except Exception:
    HAZOP_DB = {
        "Pressão": {"MAIS": {"causas": ["Bloqueio de linha", "Falha de controle"], "conseqs": ["Sobrepressão", "Ruptura"], "salvags": ["PSV", "PAHH"], "rec": ["Verificar alívio", "Revisar cenário de bloqueio"]}},
        "Temperatura": {"MAIS": {"causas": ["Falha de resfriamento", "Reação exotérmica"], "conseqs": ["Decomposição", "Runaway"], "salvags": ["TAHH", "Intertravamento"], "rec": ["Revisar proteção térmica", "Verificar contingência"]}},
        "Vazão": {"NÃO / NENHUM": {"causas": ["Falha de bomba"], "conseqs": ["Perda de função"], "salvags": ["Alarme"], "rec": ["Bomba reserva"]}},
    }

try:
    from reactivity_engine import evaluate_pairwise_reactivity
except Exception:
    evaluate_pairwise_reactivity = None

try:
    from action_hub import build_consolidated_action_plan
except Exception:
    build_consolidated_action_plan = None

try:
    from dashboard_engine import calculate_case_readiness_index
except Exception:
    calculate_case_readiness_index = None

try:
    from dashboard_visuals import build_readiness_gauge_figure, build_components_figure
except Exception:
    build_readiness_gauge_figure = None
    build_components_figure = None

try:
    from psi_readiness import build_psi_readiness_df, summarize_psi_readiness
except Exception:
    build_psi_readiness_df = None
    summarize_psi_readiness = None

try:
    from moc_engine import evaluate_moc
except Exception:
    evaluate_moc = None

try:
    from pssr_engine import evaluate_pssr
except Exception:
    evaluate_pssr = None

try:
    from executive_report import build_executive_bundle
except Exception:
    build_executive_bundle = None

try:
    from case_store import save_case, load_case, list_cases
except Exception:
    save_case = None
    load_case = None
    list_cases = None

# =========================
# Fallback profile
# =========================
@dataclass
class FallbackProfile:
    identity: dict
    hazards: list
    nfpa: dict
    physchem: dict
    exposure_limits: dict
    reactivity: dict
    storage: dict
    flags: dict
    fingerprint: dict
    routing: list
    validation_gaps: list
    source_trace: list
    references: list
    readiness: list
    confidence_score: float
    incompatibility_matrix: list

    def prop(self, key: str, default=None):
        item = self.physchem.get(key)
        if isinstance(item, dict):
            return item.get("value", default)
        if hasattr(item, "value"):
            return item.value
        return default

    def limit(self, key: str, default=None):
        item = self.exposure_limits.get(key)
        if isinstance(item, dict):
            return item.get("value", default)
        if hasattr(item, "value"):
            return item.value
        return default


def fallback_profile_from_seed(key: str) -> FallbackProfile:
    item = LOCAL_COMPOUNDS[key]
    react = item.get("reactivity", {})
    hazards = item.get("hazards", [])
    flags = {
        "flammable": item.get("nfpa", {}).get("fire", 0) >= 3 or any("inflam" in h.lower() for h in hazards),
        "toxic_inhalation": any("inala" in h.lower() for h in hazards) or "IDLH_ppm" in item.get("exposure_limits", {}),
        "corrosive": react.get("corrosive", False) or any("corros" in h.lower() for h in hazards),
        "pressurized": react.get("pressurized", False),
        "reactive_hazard": react.get("reactive_hazard", False),
    }
    routing = []
    if flags["flammable"]:
        routing += ["HAZOP de ignição e perda de contenção", "Pool fire screening"]
    if flags["toxic_inhalation"]:
        routing += ["Dispersão tóxica", "Detecção e evacuação"]
    if flags["corrosive"]:
        routing += ["Materiais de construção", "Integridade mecânica"]
    if not routing:
        routing = ["Pacote adicional de dados para screening detalhado"]

    storage = {
        "incompatibilities": react.get("incompatibilities", []),
        "notes": react.get("notes", []),
        "official_links": build_official_source_links(item.get("identity", {}).get("name", ""), item.get("identity", {}).get("cas", "")) if build_official_source_links else [],
    }
    return FallbackProfile(
        identity=item.get("identity", {}),
        hazards=hazards,
        nfpa=item.get("nfpa", {}),
        physchem=item.get("physchem", {}),
        exposure_limits=item.get("exposure_limits", {}),
        reactivity=react,
        storage=storage,
        flags=flags,
        fingerprint={
            "Inflamabilidade": 4 if flags["flammable"] else 1,
            "Toxicidade": 3 if flags["toxic_inhalation"] else 1,
            "Pressão": 4 if flags["pressurized"] else 1,
            "Corrosividade": 4 if flags["corrosive"] else 1,
            "Reatividade": 3 if flags["reactive_hazard"] else 1,
        },
        routing=routing,
        validation_gaps=[],
        source_trace=[],
        references=[],
        readiness=[],
        confidence_score=75.0,
        incompatibility_matrix=[],
    )


def build_profile(query: str):
    if build_compound_profile is not None:
        try:
            prof = build_compound_profile(query)
            if prof is not None:
                return prof
        except Exception:
            pass
    q = query.strip().lower()
    for key, item in LOCAL_COMPOUNDS.items():
        aliases = [a.lower() for a in item.get("aliases", [])]
        ident = item.get("identity", {})
        checks = aliases + [str(ident.get("cas", "")).lower(), str(ident.get("formula", "")).lower(), str(ident.get("name", "")).lower(), str(ident.get("preferred_name", "")).lower()]
        if q in checks:
            return fallback_profile_from_seed(key)
    return None

# =========================
# Dados históricos (Sprint 16)
# =========================
HISTORICAL_INCIDENTS = [
    {
        "ano": 1984, "evento": "Bhopal", "local": "Índia", "substancia": "Isocianato de metila",
        "tipo": "Liberação tóxica", "mecanismo": "Entrada de água e reação descontrolada em tanque",
        "barreiras_falharam": "Isolamento, refrigeração, contenção e resposta à emergência",
        "licoes": "MOC, integridade mecânica, inventário mínimo, isolamento e prontidão de emergência.",
        "fonte": "Caso histórico curado", "tags": ["toxicidade", "reatividade", "MOC", "emergência"]
    },
    {
        "ano": 1974, "evento": "Flixborough", "local": "Reino Unido", "substancia": "Ciclohexano",
        "tipo": "Explosão / VCE", "mecanismo": "Modificação temporária inadequada e perda de contenção",
        "barreiras_falharam": "MOC, projeto mecânico, revisão independente",
        "licoes": "Mudanças temporárias precisam de revisão formal de engenharia e PSSR.",
        "fonte": "Caso histórico curado", "tags": ["inflamável", "MOC", "PSSR", "sobrepressão"]
    },
    {
        "ano": 2005, "evento": "Texas City", "local": "EUA", "substancia": "Hidrocarbonetos leves",
        "tipo": "Explosão / incêndio", "mecanismo": "Overfill, blowdown atmosférico e ignição",
        "barreiras_falharam": "Projeto de alívio, procedimentos, supervisão e layout",
        "licoes": "Revisar blowdown, segregação, gestão operacional e cultura de segurança.",
        "fonte": "Caso histórico curado", "tags": ["inflamável", "LOPA", "alívio", "layout"]
    },
    {
        "ano": 1947, "evento": "Texas City (amônio nitrato)", "local": "EUA", "substancia": "Nitrato de amônio",
        "tipo": "Explosão", "mecanismo": "Incêndio e decomposição violenta",
        "barreiras_falharam": "Armazenamento, resposta a incêndio, entendimento do perigo",
        "licoes": "Compatibilidade, controle de estoque e cenários de decomposição devem ser explícitos.",
        "fonte": "Caso histórico curado", "tags": ["oxidante", "armazenamento", "decomposição"]
    },
    {
        "ano": 2020, "evento": "Beirute", "local": "Líbano", "substancia": "Nitrato de amônio",
        "tipo": "Explosão", "mecanismo": "Armazenamento inseguro prolongado",
        "barreiras_falharam": "Governança, segregação e fiscalização",
        "licoes": "Segregação, inventário, governança de risco e compliance documental são críticos.",
        "fonte": "Caso histórico curado", "tags": ["oxidante", "armazenamento", "governança"]
    },
    {
        "ano": 2013, "evento": "West Fertilizer", "local": "EUA", "substancia": "Nitrato de amônio",
        "tipo": "Incêndio / explosão", "mecanismo": "Incêndio inicial e propagação para estoque incompatível",
        "barreiras_falharam": "Segregação, proteção passiva, resposta de emergência",
        "licoes": "Compatibilidade entre substâncias e segregação por área reduzem cenários catastróficos.",
        "fonte": "Caso histórico curado", "tags": ["segregação", "almoxarifado", "oxidante"]
    },
]

# =========================
# Mapas (Sprint 15)
# =========================
SATELLITE_TILE = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
SATELLITE_ATTR = "Esri World Imagery"


def build_consequence_zones(profile, dispersion_result: Optional[dict], pool_fire_result: Optional[dict]) -> list[dict]:
    zones: list[dict] = []

    if dispersion_result:
        x_idlh = dispersion_result.get("x_idlh")
        if x_idlh:
            zones.append({
                "radius": float(x_idlh),
                "color": "#a62b45",
                "label": f"Zona IDLH — {x_idlh:.0f} m",
                "scenario": "Dispersão tóxica",
                "criterion": "IDLH",
            })
            zones.append({
                "radius": float(max(25, x_idlh * 1.5)),
                "color": "#d4a72c",
                "label": f"Zona de controle operacional — {max(25, x_idlh * 1.5):.0f} m",
                "scenario": "Dispersão tóxica",
                "criterion": "Buffer operacional",
            })

    if pool_fire_result:
        q = float(pool_fire_result.get("q_kW_m2", 0.0))
        base = 30.0 if q <= 0 else max(20.0, min(250.0, 15.0 + 4.5 * q))
        zones.append({
            "radius": base,
            "color": "#a62b45",
            "label": f"37,5 kW/m² — zona severa (~{base:.0f} m)",
            "scenario": "Pool fire",
            "criterion": "Fluxo térmico severo",
        })
        zones.append({
            "radius": base * 1.8,
            "color": "#f59e0b",
            "label": f"12,5 kW/m² — dor/queimadura (~{base*1.8:.0f} m)",
            "scenario": "Pool fire",
            "criterion": "Fluxo térmico moderado",
        })
        zones.append({
            "radius": base * 2.6,
            "color": "#4ea3ff",
            "label": f"4,7 kW/m² — exposição prolongada (~{base*2.6:.0f} m)",
            "scenario": "Pool fire",
            "criterion": "Fluxo térmico leve",
        })

    # ordenar sem mutar a entrada
    return sorted(zones, key=lambda x: x["radius"], reverse=True)


def build_risk_map(lat: float, lon: float, zones: list[dict], use_satellite: bool = True):
    if folium is None:
        return None

    tile_args = {
        "tiles": SATELLITE_TILE if use_satellite else "CartoDB positron",
        "attr": SATELLITE_ATTR if use_satellite else "CartoDB positron",
        "zoom_start": 15,
        "control_scale": True,
    }
    m = folium.Map(location=[lat, lon], **tile_args)

    # alternativa base clara
    if use_satellite:
        folium.TileLayer("CartoDB positron", name="Mapa claro").add_to(m)
    else:
        folium.TileLayer(SATELLITE_TILE, attr=SATELLITE_ATTR, name="Satélite").add_to(m)

    folium.Marker(
        [lat, lon],
        tooltip="Origem do cenário",
        popup="Origem do cenário",
        icon=folium.Icon(color="black", icon="info-sign"),
    ).add_to(m)

    for zone in zones:
        popup = (
            f"<b>{zone.get('label', 'Zona')}</b><br>"
            f"Cenário: {zone.get('scenario', '—')}<br>"
            f"Critério: {zone.get('criterion', '—')}<br>"
            f"Raio: {zone.get('radius', 0):.0f} m"
        )
        folium.Circle(
            radius=float(zone["radius"]),
            location=[lat, lon],
            popup=popup,
            tooltip=zone.get("label", "Zona"),
            color=zone.get("color", "#4ea3ff"),
            fill=True,
            fill_color=zone.get("color", "#4ea3ff"),
            fill_opacity=0.25,
            weight=2,
        ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m

# =========================
# P&ID Auto-Nó Beta (Sprint 17)
# =========================
TAG_PATTERNS = {
    "Tanques": r"\bT[- ]?\d{2,4}[A-Z]?\b",
    "Bombas": r"\bP[- ]?\d{2,4}[A-Z]?\b",
    "Trocadores": r"\bE[- ]?\d{2,4}[A-Z]?\b",
    "Vasos": r"\bV[- ]?\d{2,4}[A-Z]?\b",
    "Válvulas de controle": r"\bF[VICLTA]-?\d{2,4}[A-Z]?\b",
    "Instrumentos de pressão": r"\bP[ITAHL]{1,3}-?\d{2,4}[A-Z]?\b",
    "Instrumentos de temperatura": r"\bT[ITAHL]{1,3}-?\d{2,4}[A-Z]?\b",
    "Linhas": r"\b\d{1,3}[""A-Z-]{2,12}\b",
}


def read_pdf_text(file_bytes: bytes) -> str:
    if fitz is None:
        return ""
    text_parts = []
    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                text_parts.append(page.get_text("text"))
    except Exception:
        return ""
    return "\n".join(text_parts)


def suggest_pid_nodes(text: str, filename: str = "") -> dict:
    text = text or ""
    found: dict[str, list[str]] = {}
    for label, pattern in TAG_PATTERNS.items():
        hits = sorted(set(re.findall(pattern, text, flags=re.IGNORECASE)))
        if hits:
            found[label] = hits[:20]

    equipment_order = []
    for key in ["Tanques", "Vasos", "Bombas", "Trocadores"]:
        equipment_order.extend(found.get(key, []))

    line_tags = found.get("Linhas", [])[:10]
    nodes = []
    node_id = 1
    for eq in equipment_order[:8]:
        params = ["Vazão", "Pressão", "Temperatura"]
        if eq.upper().startswith("P"):
            params += ["NPSH / Cavitação"]
        if eq.upper().startswith("T") or eq.upper().startswith("V"):
            params += ["Nível"]
        nodes.append({
            "Nó": f"Nó {node_id}",
            "Descrição": f"Entorno do equipamento {eq}",
            "Tags relacionadas": ", ".join([eq] + line_tags[:2]),
            "Parâmetros sugeridos": ", ".join(params),
            "Confiabilidade": "Média" if text else "Baixa",
        })
        node_id += 1

    if not nodes and filename:
        nodes.append({
            "Nó": "Nó 1",
            "Descrição": f"Triagem manual para {filename}",
            "Tags relacionadas": "Sem extração automática robusta",
            "Parâmetros sugeridos": "Vazão, Pressão, Temperatura, Nível",
            "Confiabilidade": "Baixa",
        })

    summary = {
        "equipamentos_detectados": sum(len(v) for k, v in found.items() if k in ["Tanques", "Vasos", "Bombas", "Trocadores"]),
        "instrumentos_detectados": sum(len(v) for k, v in found.items() if "Instrumentos" in k or "Válvulas" in k),
        "linhas_detectadas": len(found.get("Linhas", [])),
        "familias_detectadas": len(found),
    }
    return {"found": found, "nodes": nodes, "summary": summary}

# =========================
# UI helpers
# =========================
APP_CSS = """
<style>
.stApp { background: linear-gradient(180deg, #07111f, #081a31); color: #e9f1ff; }
.block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 1480px; }
.hero { background: linear-gradient(135deg, #0d2345, #0b1830); border: 1px solid #1c3f78; border-radius: 20px; padding: 1.2rem 1.5rem; margin-bottom: 1rem; }
.hero h1 { margin: 0 0 0.35rem 0; color: #f4f8ff; font-size: 2rem; font-weight: 800; }
.hero p { margin: 0; color: #9fc1ff; font-size: 1rem; }
.badge { display: inline-block; margin: .35rem .35rem 0 0; padding: .28rem .65rem; border-radius: 999px; border: 1px solid #2b5aa1; color: #cfe1ff; background: rgba(31,74,139,.18); font-size: .78rem; }
.panel { background: rgba(9,17,31,.94); border: 1px solid #1d365f; border-radius: 18px; padding: 1rem; margin-bottom: .9rem; }
.metric-box { background: rgba(10,22,42,.95); border: 1px solid #1d365f; border-radius: 18px; padding: 1rem; min-height: 110px; }
.metric-label { color: #7ea8ea; font-size: .78rem; text-transform: uppercase; }
.metric-value { color: white; font-size: 1.55rem; font-weight: 800; margin-top: .45rem; }
.risk-blue { color: #62a8ff; } .risk-green { color: #34d399; } .risk-amber { color: #fbbf24; } .risk-red { color: #fb7185; }
.kpi-chip { display:inline-block; padding:.28rem .65rem; border-radius:999px; border:1px solid #2b5aa1; margin-right:.45rem; margin-bottom:.35rem; color:#d9e8ff; background:rgba(31,74,139,.14); font-size:.78rem; }
.note-card { background: rgba(12, 28, 54, 0.95); border-left: 4px solid #4b88ff; border-radius: 12px; padding: 0.9rem 1rem; color: #e9f1ff; }
</style>
"""


def metric_card(label: str, value: str, klass: str = "risk-blue") -> str:
    return f"<div class='metric-box'><div class='metric-label'>{label}</div><div class='metric-value {klass}'>{value}</div></div>"


def quick_compounds() -> dict[str, str]:
    return {k: v["identity"]["name"] for k, v in LOCAL_COMPOUNDS.items()}


def draw_simple_bar(label: str, value: float, max_value: float = 100.0, title: str | None = None):
    fig, ax = plt.subplots(figsize=(6.2, 2.8))
    fig.patch.set_facecolor("#07111f")
    ax.set_facecolor("#0b1730")
    color = "#34d399" if value >= 80 else "#f59e0b" if value >= 50 else "#ef4444"
    ax.barh([label], [value], color=color, edgecolor="none", height=0.55)
    ax.barh([label], [max(0, max_value - value)], left=[value], color="#1b2b46", edgecolor="none", height=0.55)
    ax.set_xlim(0, max_value)
    ax.grid(True, axis="x", color="#29476d", alpha=0.35, linestyle="--", linewidth=0.6)
    ax.tick_params(colors="#9ab2d8", labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#29476d")
    if title:
        ax.set_title(title, color="#e8f1ff", fontsize=12, fontweight="bold", pad=10)
    ax.text(min(value + 2, max_value * 0.95), 0, f"{value:.1f}", color="#e8f1ff", va="center", fontsize=10, fontweight="bold")
    fig.tight_layout()
    return fig


def get_default_coordinates(profile) -> tuple[float, float]:
    # ponto default: Campinas para demo, mas editável
    return -22.9099, -47.0626


st.set_page_config(page_title="ChemSafe Pro Deterministic", page_icon="⚗️", layout="wide", initial_sidebar_state="expanded")
st.markdown(APP_CSS, unsafe_allow_html=True)

# Session state
for key, default in {
    "selected_compound_key": next(iter(LOCAL_COMPOUNDS.keys()), ""),
    "profile": None,
    "compare_profile": None,
    "reactivity_partner_profile": None,
    "lopa_result": None,
    "dispersion_result": None,
    "pool_fire_result": None,
    "moc_result": None,
    "pssr_result": None,
    "reactivity_result": None,
    "report_bundle": None,
    "current_case_name": "",
    "current_case_notes": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# Sidebar
with st.sidebar:
    st.markdown("## ⚗️ ChemSafe Pro")
    st.caption("Segurança de processo orientada por evidência")
    st.markdown("---")
    st.write("**Acesso rápido**")
    for key, name in quick_compounds().items():
        if st.button(name, key=f"quick_{key}", width="stretch"):
            st.session_state.profile = build_profile(name)
            st.session_state.selected_compound_key = key

    st.markdown("---")
    q = st.text_input("Buscar composto", placeholder="Nome, CAS ou fórmula")
    if st.button("Carregar composto", width="stretch"):
        if q.strip():
            prof = build_profile(q.strip())
            if prof is not None:
                st.session_state.profile = prof
            else:
                st.warning("Composto não encontrado na base curada / motores disponíveis.")

if st.session_state.profile is None and LOCAL_COMPOUNDS:
    default_name = LOCAL_COMPOUNDS[st.session_state.selected_compound_key]["aliases"][0]
    st.session_state.profile = build_profile(default_name)

profile = st.session_state.profile
if profile is None:
    st.stop()

st.markdown(
    """
    <div class="hero">
      <h1>ChemSafe Pro Deterministic</h1>
      <p>Segurança de processo guiada por propriedades reais, governança de fontes, reatividade, consequência, ações e prontidão do caso.</p>
      <div>
        <span class="badge">Governança</span>
        <span class="badge">HAZOP</span>
        <span class="badge">LOPA</span>
        <span class="badge">MOC</span>
        <span class="badge">PSSR</span>
        <span class="badge">Reatividade</span>
        <span class="badge">Mapa de impacto</span>
        <span class="badge">Acidentes históricos</span>
        <span class="badge">P&ID Auto-Nó Beta</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Derived summaries
psi_df = build_psi_readiness_df(profile, st.session_state.get("lopa_result"), {}) if build_psi_readiness_df else pd.DataFrame()
psi_summary = summarize_psi_readiness(psi_df) if summarize_psi_readiness and not psi_df.empty else {"score": 0, "ok": 0, "partial": 0, "gap": 0}
action_df = build_consolidated_action_plan(profile, psi_df, st.session_state.get("moc_result"), st.session_state.get("pssr_result"), st.session_state.get("reactivity_result")) if build_consolidated_action_plan else pd.DataFrame(columns=["Origem", "Ação Requerida", "Criticidade", "Status"])
cri = calculate_case_readiness_index(profile, psi_summary, st.session_state.get("moc_result"), st.session_state.get("pssr_result"), st.session_state.get("lopa_result"), st.session_state.get("reactivity_result")) if calculate_case_readiness_index else {"index": profile.confidence_score, "band": "Screening", "color_class": "risk-blue", "components": []}

# Tabs
(
    overview_tab,
    compound_tab,
    sources_tab,
    reactivity_tab,
    hazop_tab,
    lopa_tab,
    change_tab,
    consequence_tab,
    map_tab,
    historical_tab,
    pid_tab,
    report_tab,
    cases_tab,
) = st.tabs([
    "Overview",
    "Composto",
    "Fontes / Evidências",
    "Reatividade",
    "HAZOP / Bow-Tie",
    "LOPA",
    "MOC / PSSR",
    "Consequências",
    "Mapa de Impacto",
    "Acidentes Históricos",
    "P&ID Auto-Nó (Beta)",
    "Relatório",
    "Casos",
])

with overview_tab:
    dm = "Gaussiano" if profile.flags.get("toxic_inhalation") else "Térmico / inflamável"
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.markdown(metric_card("Composto", profile.identity.get("name", "—")), unsafe_allow_html=True)
    c2.markdown(metric_card("CAS", str(profile.identity.get("cas", "—"))), unsafe_allow_html=True)
    c3.markdown(metric_card("Confiança", f"{profile.confidence_score:.0f}/100", "risk-green" if profile.confidence_score >= 80 else "risk-amber"), unsafe_allow_html=True)
    c4.markdown(metric_card("Readiness Global", f"{cri.get('index', 0)}", cri.get("color_class", "risk-blue")), unsafe_allow_html=True)
    c5.markdown(metric_card("Rota de consequência", dm), unsafe_allow_html=True)

    st.markdown("<div class='panel'><h3>Roteamento automático</h3></div>", unsafe_allow_html=True)
    for item in getattr(profile, "routing", []) or []:
        st.success(item)

    st.markdown("<div class='panel'><h3>Painel executivo</h3></div>", unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        if build_readiness_gauge_figure:
            st.pyplot(build_readiness_gauge_figure(cri), clear_figure=True)
        else:
            st.pyplot(draw_simple_bar("Readiness", float(cri.get("index", 0)), title="Case Readiness Index"), clear_figure=True)
    with right:
        if build_components_figure and cri.get("components"):
            st.pyplot(build_components_figure(cri), clear_figure=True)
        else:
            comp_df = pd.DataFrame(cri.get("components", []))
            st.dataframe(comp_df, width="stretch", hide_index=True)

    st.markdown("<div class='panel'><h3>Plano de ação consolidado</h3></div>", unsafe_allow_html=True)
    st.dataframe(action_df, width="stretch", hide_index=True)

with compound_tab:
    left, right = st.columns(2)
    with left:
        st.markdown("<div class='panel'><h3>Identidade</h3></div>", unsafe_allow_html=True)
        ident_rows = [{"campo": k, "valor": v} for k, v in profile.identity.items()]
        st.dataframe(pd.DataFrame(ident_rows), width="stretch", hide_index=True)
        st.markdown("<div class='panel'><h3>Perigos / GHS</h3></div>", unsafe_allow_html=True)
        if profile.hazards:
            for hz in profile.hazards:
                st.error(hz)
        else:
            st.info("Sem hazards estruturados.")
    with right:
        st.markdown("<div class='panel'><h3>Propriedades físico-químicas</h3></div>", unsafe_allow_html=True)
        phys_rows = []
        for k, v in getattr(profile, "physchem", {}).items():
            if isinstance(v, dict):
                phys_rows.append({"property": k, "value": v.get("value"), "unit": v.get("unit"), "source": v.get("source")})
            else:
                phys_rows.append({"property": k, "value": getattr(v, "value", None), "unit": getattr(v, "unit", ""), "source": getattr(v, "source", "")})
        st.dataframe(pd.DataFrame(phys_rows), width="stretch", hide_index=True)

        st.markdown("<div class='panel'><h3>Limites de exposição</h3></div>", unsafe_allow_html=True)
        lim_rows = []
        for k, v in getattr(profile, "exposure_limits", {}).items():
            if isinstance(v, dict):
                lim_rows.append({"limit": k, "value": v.get("value"), "unit": v.get("unit"), "source": v.get("source")})
            else:
                lim_rows.append({"limit": k, "value": getattr(v, "value", None), "unit": getattr(v, "unit", ""), "source": getattr(v, "source", "")})
        st.dataframe(pd.DataFrame(lim_rows), width="stretch", hide_index=True)

with sources_tab:
    st.markdown("<div class='panel'><h3>Governança de fontes</h3></div>", unsafe_allow_html=True)
    if build_evidence_ledger_df and summarize_evidence:
        evidence_df = build_evidence_ledger_df(profile)
        summary = summarize_evidence(profile)
        cols = st.columns(5)
        cols[0].markdown(metric_card("Campos", str(summary.get("linhas", 0))), unsafe_allow_html=True)
        cols[1].markdown(metric_card("Oficial", str(summary.get("oficial", 0)), "risk-green"), unsafe_allow_html=True)
        cols[2].markdown(metric_card("Curado", str(summary.get("curado", 0)), "risk-blue"), unsafe_allow_html=True)
        cols[3].markdown(metric_card("Revisar", str(summary.get("revisar", 0)), "risk-red"), unsafe_allow_html=True)
        cols[4].markdown(metric_card("Com link", str(summary.get("com_link", 0)), "risk-amber"), unsafe_allow_html=True)
        st.dataframe(evidence_df, width="stretch", hide_index=True)
        if build_source_recommendations:
            for item in build_source_recommendations(profile):
                st.info(item)
    else:
        st.info("Módulo de governança não encontrado no ambiente atual.")
        links = profile.storage.get("official_links", []) if hasattr(profile, "storage") else []
        for item in links:
            st.link_button(f"{item.get('source','Fonte')} — {item.get('purpose','consulta')}", item.get("url", ""), width="stretch")

with reactivity_tab:
    st.markdown("<div class='panel'><h3>Matriz de compatibilidade entre substâncias</h3></div>", unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1:
        q2 = st.text_input("Segundo composto", placeholder="Ex.: hipoclorito de sódio, água, ácido nítrico", key="reactivity_partner_query")
    with c2:
        if st.button("Avaliar compatibilidade", type="primary", width="stretch") and q2.strip():
            st.session_state.reactivity_partner_profile = build_profile(q2.strip())
            if st.session_state.reactivity_partner_profile is not None:
                if evaluate_pairwise_reactivity:
                    st.session_state.reactivity_result = evaluate_pairwise_reactivity(profile, st.session_state.reactivity_partner_profile)
                else:
                    st.session_state.reactivity_result = None

    result = st.session_state.get("reactivity_result")
    if result:
        s = result["summary"]
        a, b, c, d = st.columns(4)
        a.markdown(metric_card("Composto A", s["compound_a"]), unsafe_allow_html=True)
        b.markdown(metric_card("Composto B", s["compound_b"]), unsafe_allow_html=True)
        c.markdown(metric_card("Severidade", s["severity"], "risk-red" if s["severity"] == "Incompatível" else "risk-amber"), unsafe_allow_html=True)
        d.markdown(metric_card("Score", f"{s['score']}/100", "risk-red" if s["score"] >= 80 else "risk-amber"), unsafe_allow_html=True)
        st.dataframe(result["matrix_df"], width="stretch")
        if not result["hits_df"].empty:
            st.dataframe(result["hits_df"], width="stretch", hide_index=True)
        for item in result["recommendations"]:
            st.warning(item)
    else:
        st.info("Carregue um segundo composto para comparar incompatibilidade química.")

with hazop_tab:
    st.markdown("<div class='panel'><h3>HAZOP orientado por propriedades</h3></div>", unsafe_allow_html=True)
    equipment = st.selectbox("Equipamento / nó", ["Tanque atmosférico", "Reator CSTR exotérmico", "Vaso de pressão", "Trocador de calor", "Tubulação de processo", "Bomba centrífuga"])
    priorities = suggest_hazop_priorities(profile, equipment) if suggest_hazop_priorities else []
    if priorities:
        st.dataframe(pd.DataFrame(priorities), width="stretch", hide_index=True)
    else:
        st.info("Módulo de priorização HAZOP não disponível; use a worksheet base abaixo.")

    st.markdown("<div class='panel'><h3>Worksheet base</h3></div>", unsafe_allow_html=True)
    param = st.selectbox("Parâmetro", list(HAZOP_DB.keys()))
    gw = st.selectbox("Palavra-guia", list(HAZOP_DB.get(param, {}).keys()))
    db = HAZOP_DB.get(param, {}).get(gw, {})
    rows = []
    for i, cause in enumerate(db.get("causas", [])):
        rows.append({
            "Desvio": f"{gw} {param}" if i == 0 else "idem",
            "Causa": cause,
            "Consequência": db.get("conseqs", ["—"])[i if i < len(db.get("conseqs", [])) else 0],
            "Salvaguarda": db.get("salvags", ["—"])[i if i < len(db.get("salvags", [])) else 0],
            "Recomendação": db.get("rec", ["—"])[i if i < len(db.get("rec", [])) else 0],
        })
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    st.markdown("<div class='panel'><h3>Bow-Tie (edição rápida)</h3></div>", unsafe_allow_html=True)
    th = st.text_area("Ameaças (uma por linha)", value="\n".join(["Falha de vedação", "Erro operacional", "Fonte de ignição"]), key="bowtie_th")
    pr = st.text_area("Barreiras preventivas", value="\n".join(["Detecção", "Intertravamento", "Procedimento"]), key="bowtie_pr")
    top = st.text_input("Top Event", value="Perda de contenção", key="bowtie_top")
    mi = st.text_area("Barreiras mitigadoras", value="\n".join(["Plano de emergência", "Combate", "Evacuação"]), key="bowtie_mi")
    co = st.text_area("Consequências", value="\n".join(["Incêndio", "Exposição", "Dano à instalação"]), key="bowtie_co")
    if build_bowtie_custom_figure:
        fig = build_bowtie_custom_figure([x for x in th.splitlines() if x.strip()], [x for x in pr.splitlines() if x.strip()], top, [x for x in mi.splitlines() if x.strip()], [x for x in co.splitlines() if x.strip()], mode="executivo")
        st.pyplot(fig, clear_figure=True)

with lopa_tab:
    st.markdown("<div class='panel'><h3>LOPA preliminar</h3></div>", unsafe_allow_html=True)
    if suggest_lopa_ipls:
        for item in suggest_lopa_ipls(profile):
            st.success(item)
    left, right = st.columns(2)
    with left:
        f_ie = st.number_input("Frequência do evento iniciador (1/ano)", value=0.1, min_value=0.000001, format="%.6f")
        criterion = st.selectbox("Critério tolerável", [1e-5, 1e-4, 1e-3], format_func=lambda x: f"{x:.0e}/ano")
    with right:
        selected = st.multiselect("IPLs", [f"{n} (PFD={p})" for n, p in IPL_CATALOG], default=[f"{IPL_CATALOG[0][0]} (PFD={IPL_CATALOG[0][1]})"])
    if st.button("Calcular LOPA / SIL", type="primary"):
        chosen = []
        for label in selected:
            for name, pfd in IPL_CATALOG:
                if name in label:
                    chosen.append((name, pfd))
                    break
        st.session_state.lopa_result = compute_lopa(f_ie, criterion, chosen)
    if st.session_state.get("lopa_result"):
        lr = st.session_state["lopa_result"]
        a, b, c, d = st.columns(4)
        a.markdown(metric_card("F_ie", f"{lr['f_ie']:.2e}/ano"), unsafe_allow_html=True)
        b.markdown(metric_card("PFD total", f"{lr['pfd_total']:.2e}"), unsafe_allow_html=True)
        c.markdown(metric_card("MCF", f"{lr['mcf']:.2e}/ano", "risk-red" if lr["ratio"] > 1 else "risk-green"), unsafe_allow_html=True)
        d.markdown(metric_card("SIL", lr["sil"], "risk-amber"), unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(lr["selected_ipls"], columns=["IPL", "PFD"]), width="stretch", hide_index=True)

with change_tab:
    st.markdown("<div class='panel'><h3>MOC / PSSR</h3></div>", unsafe_allow_html=True)
    moc_sub, pssr_sub = st.tabs(["MOC", "PSSR"])
    with moc_sub:
        if evaluate_moc:
            c1, c2 = st.columns(2)
            with c1:
                change_type = st.selectbox("Tipo principal de mudança", [
                    "Mudança química / novo composto", "Mudança de condição operacional", "Mudança de equipamento / material",
                    "Mudança de instrumentação / controle", "Mudança em alívio / PSV", "Mudança de procedimento / operação"
                ])
                impacts = st.multiselect("Aspectos impactados", ["Química / composição", "Pressão", "Temperatura", "Vazão", "Inventário", "Materiais de construção", "Instrumentação / controle", "Alívio / PSV", "Ventilação / detecção", "Procedimentos operacionais"])
                description = st.text_area("Descrição da mudança")
            with c2:
                temporary = st.checkbox("Mudança temporária")
                protections_changed = st.checkbox("Afeta barreiras / proteções")
                procedures_changed = st.checkbox("Exige revisão de procedimentos")
                pids_affected = st.checkbox("Afeta P&ID / documentação")
                training_required = st.checkbox("Exige treinamento")
                new_chemical = st.checkbox("Introduz novo composto / composição")
                bypass_or_override = st.checkbox("Envolve bypass / override")
            if st.button("Avaliar MOC", type="primary"):
                st.session_state.moc_result = evaluate_moc(profile, change_type, impacts, description, temporary=temporary, protections_changed=protections_changed, procedures_changed=procedures_changed, pids_affected=pids_affected, training_required=training_required, new_chemical=new_chemical, bypass_or_override=bypass_or_override)
            if st.session_state.get("moc_result"):
                st.json(st.session_state["moc_result"]["summary"])
                st.dataframe(pd.DataFrame(st.session_state["moc_result"]["checklist_rows"]), width="stretch", hide_index=True)
        else:
            st.info("Módulo MOC não disponível no ambiente atual.")
    with pssr_sub:
        if evaluate_pssr:
            c1, c2 = st.columns(2)
            with c1:
                scope_label = st.selectbox("Escopo do PSSR", ["PHA para nova instalação", "MOC para instalação modificada"])
                design_ok = st.checkbox("Construção/equipamento conforme especificação")
                procedures_ok = st.checkbox("Procedimentos adequados")
                training_ok = st.checkbox("Treinamento concluído")
                pha_or_moc_ok = st.checkbox("Base de PHA/MOC resolvida")
            with c2:
                mi_ready = st.checkbox("Mechanical integrity / prontidão")
                relief_verified = st.checkbox("PSV / alívio revisados")
                alarms_tested = st.checkbox("Alarmes e permissivos testados")
                emergency_ready = st.checkbox("Plano de emergência disponível")
                startup_authorized = st.checkbox("Autorização formal para startup")
            if st.button("Avaliar PSSR", type="primary"):
                st.session_state.pssr_result = evaluate_pssr(design_ok=design_ok, procedures_ok=procedures_ok, pha_or_moc_ok=pha_or_moc_ok, training_ok=training_ok, mi_ready=mi_ready, relief_verified=relief_verified, alarms_tested=alarms_tested, emergency_ready=emergency_ready, startup_authorized=startup_authorized, scope_label=scope_label)
            if st.session_state.get("pssr_result"):
                st.json(st.session_state["pssr_result"]["summary"])
                st.dataframe(pd.DataFrame(st.session_state["pssr_result"]["checklist_rows"]), width="stretch", hide_index=True)
        else:
            st.info("Módulo PSSR não disponível no ambiente atual.")

with consequence_tab:
    st.markdown("<div class='panel'><h3>Consequências</h3></div>", unsafe_allow_html=True)
    tox_tab, fire_tab = st.tabs(["Dispersão tóxica", "Pool fire"])
    with tox_tab:
        if profile.flags.get("toxic_inhalation", False):
            a, b, c = st.columns(3)
            q_g_s = a.number_input("Q (g/s)", value=10.0, min_value=0.001)
            wind = b.number_input("u (m/s)", value=3.0, min_value=0.2)
            stability = c.selectbox("Classe de estabilidade", list("ABCDEF"), index=3)
            d1, d2, d3 = st.columns(3)
            idlh_ppm = d1.number_input("IDLH (ppm)", value=float(profile.limit("IDLH_ppm", 300.0) or 300.0), min_value=0.001)
            mw = d2.number_input("PM", value=float(profile.identity.get("molecular_weight", 20.0) or 20.0), min_value=1.0)
            h = d3.number_input("Altura da fonte (m)", value=0.0, min_value=0.0)
            if st.button("Rodar dispersão", type="primary"):
                st.session_state.dispersion_result = gaussian_dispersion(q_g_s, wind, stability, idlh_ppm, mw, h)
            if st.session_state.get("dispersion_result"):
                dr = st.session_state["dispersion_result"]
                st.dataframe(pd.DataFrame([
                    {"Item": "Distância até IDLH", "Valor": f"{dr['x_idlh']} m" if dr.get('x_idlh') else "> 3 km"},
                    {"Item": "Concentração a 100 m", "Valor": f"{dr['c_at_100m']:.4f} g/m³"},
                ]), width="stretch", hide_index=True)
        else:
            st.info("O perfil não sugere screening tóxico dominante.")
    with fire_tab:
        if profile.flags.get("flammable", False):
            a, b, c, d = st.columns(4)
            diameter = a.number_input("Diâmetro da poça (m)", value=5.0, min_value=0.5)
            burn = b.number_input('m" (kg/m²·s)', value=0.024, min_value=0.001)
            hc = c.number_input("Hc (kJ/kg)", value=44000.0, min_value=1000.0)
            distance = d.number_input("Distância ao alvo (m)", value=20.0, min_value=1.0)
            if st.button("Rodar pool fire", type="primary"):
                st.session_state.pool_fire_result = pool_fire(diameter, burn, hc, distance)
            if st.session_state.get("pool_fire_result"):
                pr = st.session_state["pool_fire_result"]
                st.dataframe(pd.DataFrame([
                    {"Item": "Altura da chama", "Valor": f"{pr['Hf_m']:.1f} m"},
                    {"Item": "Poder emissivo", "Valor": f"{pr['E_kW_m2']:.1f} kW/m²"},
                    {"Item": "Fluxo no alvo", "Valor": f"{pr['q_kW_m2']:.2f} kW/m²"},
                    {"Item": "Zona", "Valor": pr['zone']},
                ]), width="stretch", hide_index=True)
        else:
            st.info("O perfil não sugere pool fire dominante.")

with map_tab:
    st.markdown("<div class='panel'><h3>Mapa de impacto geográfico (Sprint 15)</h3></div>", unsafe_allow_html=True)
    st.markdown("<div class='note-card'>Sugestão: usar este mapa como camada visual de screening, não como substituto de modelagem geoespacial detalhada.</div>", unsafe_allow_html=True)
    default_lat, default_lon = get_default_coordinates(profile)
    c1, c2, c3 = st.columns(3)
    lat = c1.number_input("Latitude", value=float(default_lat), format="%.6f")
    lon = c2.number_input("Longitude", value=float(default_lon), format="%.6f")
    use_sat = c3.checkbox("Base satélite", value=True)

    zones = build_consequence_zones(profile, st.session_state.get("dispersion_result"), st.session_state.get("pool_fire_result"))
    if zones:
        zone_df = pd.DataFrame(zones)
        st.dataframe(zone_df[["label", "scenario", "criterion", "radius"]], width="stretch", hide_index=True)
        fmap = build_risk_map(lat, lon, zones, use_satellite=use_sat)
        if fmap is not None:
            st.components.v1.html(fmap._repr_html_(), height=560, scrolling=False)
        else:
            st.warning("folium não está instalado no ambiente. Adicione `folium` ao requirements.txt para habilitar o mapa.")
    else:
        st.info("Rode primeiro um cenário de dispersão e/ou pool fire para gerar zonas de impacto.")

with historical_tab:
    st.markdown("<div class='panel'><h3>Acidentes históricos rastreáveis (Sprint 16)</h3></div>", unsafe_allow_html=True)
    st.markdown("<div class='note-card'>A base abaixo é curada e deve ser expandida com rastreabilidade de fonte. Use-a como memória técnica para reforçar HAZOP, MOC e PSSR.</div>", unsafe_allow_html=True)
    df_hist = pd.DataFrame(HISTORICAL_INCIDENTS)
    all_types = sorted(df_hist["tipo"].unique())
    all_tags = sorted({tag for tags in df_hist["tags"] for tag in tags})
    c1, c2, c3 = st.columns(3)
    event_type = c1.selectbox("Tipo de evento", ["Todos"] + all_types)
    tag_filter = c2.selectbox("Tag / lição", ["Todas"] + all_tags)
    name_hint = c3.text_input("Filtrar por substância/evento", value=profile.identity.get("name", ""))

    filt = df_hist.copy()
    if event_type != "Todos":
        filt = filt[filt["tipo"] == event_type]
    if tag_filter != "Todas":
        filt = filt[filt["tags"].apply(lambda xs: tag_filter in xs)]
    if name_hint.strip():
        qh = name_hint.strip().lower()
        filt = filt[filt.apply(lambda r: qh in str(r["substancia"]).lower() or qh in str(r["evento"]).lower() or qh in str(r["mecanismo"]).lower(), axis=1)]

    st.dataframe(filt[["ano", "evento", "local", "substancia", "tipo", "mecanismo", "barreiras_falharam", "licoes", "fonte"]], width="stretch", hide_index=True)

with pid_tab:
    st.markdown("<div class='panel'><h3>P&ID Auto-Nó (Beta) — Sprint 17</h3></div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='note-card'>Recomendação técnica: implementar primeiro a versão Beta determinística (extração de texto e tags de engenharia). A versão com Visão Computacional / IA deve entrar depois, plugando um provedor específico e mantendo auditoria do resultado.</div>",
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader("Upload do P&ID em PDF", type=["pdf"], key="pid_pdf")
    if uploaded is not None:
        raw = uploaded.read()
        pid_text = read_pdf_text(raw)
        result = suggest_pid_nodes(pid_text, uploaded.name)
        s = result["summary"]
        a, b, c, d = st.columns(4)
        a.markdown(metric_card("Equipamentos detectados", str(s["equipamentos_detectados"]), "risk-blue"), unsafe_allow_html=True)
        b.markdown(metric_card("Instrumentos detectados", str(s["instrumentos_detectados"]), "risk-blue"), unsafe_allow_html=True)
        c.markdown(metric_card("Linhas detectadas", str(s["linhas_detectadas"]), "risk-blue"), unsafe_allow_html=True)
        d.markdown(metric_card("Famílias detectadas", str(s["familias_detectadas"]), "risk-amber" if s["familias_detectadas"] < 2 else "risk-green"), unsafe_allow_html=True)

        st.markdown("<div class='panel'><h3>Tags de engenharia detectadas</h3></div>", unsafe_allow_html=True)
        found_rows = []
        for fam, tags in result["found"].items():
            for tag in tags:
                found_rows.append({"Família": fam, "Tag": tag})
        st.dataframe(pd.DataFrame(found_rows), width="stretch", hide_index=True)

        st.markdown("<div class='panel'><h3>Nós sugeridos automaticamente</h3></div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(result["nodes"]), width="stretch", hide_index=True)

        with st.expander("Prévia do texto extraído"):
            st.text(pid_text[:6000] if pid_text else "Sem texto extraído. O PDF pode ser escaneado/imagem; nesse caso, a próxima etapa é integrar visão computacional.")
    else:
        st.info("Envie um PDF de P&ID para a triagem automática de tags e sugestão inicial de nós de estudo.")

with report_tab:
    st.markdown("<div class='panel'><h3>Relatório executivo</h3></div>", unsafe_allow_html=True)
    case_name = st.text_input("Nome do relatório", value=st.session_state.current_case_name or profile.identity.get("name", "Caso"))
    if st.button("Gerar relatório executivo", type="primary"):
        if build_executive_bundle is not None:
            evidence_summary = summarize_evidence(profile) if summarize_evidence else {}
            evidence_recs = build_source_recommendations(profile) if build_source_recommendations else []
            priorities = suggest_hazop_priorities(profile, "Vaso de pressão") if suggest_hazop_priorities else []
            bundle = build_executive_bundle(
                case_name=case_name,
                profile=profile,
                context={
                    "evidence_summary": evidence_summary,
                    "evidence_recommendations": evidence_recs,
                    "hazop_priorities": priorities,
                    "lopa_result": st.session_state.get("lopa_result"),
                    "psi_summary": psi_summary,
                    "moc_result": st.session_state.get("moc_result"),
                    "pssr_result": st.session_state.get("pssr_result"),
                    "reactivity_result": st.session_state.get("reactivity_result"),
                },
            )
            st.session_state.report_bundle = bundle
            st.success("Relatório gerado.")
        else:
            st.warning("Módulo de relatório não encontrado no ambiente.")

    bundle = st.session_state.get("report_bundle")
    if bundle:
        st.download_button("Baixar Markdown", bundle["markdown"], file_name=f"{case_name.replace(' ', '_')}.md", mime="text/markdown", width="stretch")
        st.download_button("Baixar HTML", bundle["html"], file_name=f"{case_name.replace(' ', '_')}.html", mime="text/html", width="stretch")
        with st.expander("Pré-visualizar Markdown"):
            st.markdown(bundle["markdown"].decode("utf-8"))

with cases_tab:
    st.markdown("<div class='panel'><h3>Salvar e carregar casos</h3></div>", unsafe_allow_html=True)
    c1, c2 = st.columns([2, 3])
    with c1:
        case_name = st.text_input("Nome do caso", value=st.session_state.current_case_name or profile.identity.get("name", "Caso sem nome"), key="case_name_input")
    with c2:
        case_notes = st.text_area("Notas do caso", value=st.session_state.current_case_notes, height=100, key="case_notes_input")
    col_save, col_load = st.columns([1, 1])
    with col_save:
        if st.button("Salvar caso", type="primary", width="stretch"):
            if save_case is not None:
                save_case(
                    case_name=case_name,
                    profile=profile,
                    notes=case_notes,
                    lopa_result=st.session_state.get("lopa_result"),
                    selected_ipl_names=[],
                    bowtie={},
                    moc_result=st.session_state.get("moc_result"),
                    pssr_result=st.session_state.get("pssr_result"),
                    reactivity_result=st.session_state.get("reactivity_result"),
                )
                st.success("Caso salvo com sucesso.")
            else:
                st.warning("case_store.py não encontrado no ambiente.")

    if list_cases is not None:
        cases = list_cases()
        if cases:
            options = [c["case_name"] for c in cases]
            sel = col_load.selectbox("Casos disponíveis", options)
            if col_load.button("Carregar caso", width="stretch") and load_case is not None:
                loaded = load_case(sel)
                if loaded:
                    apply_loaded_case = loaded  # placeholder para evitar erro de referência antiga
                    st.success("Caso carregado. Atualize a página se quiser recarregar o estado completo.")
            st.dataframe(pd.DataFrame(cases), width="stretch", hide_index=True)
        else:
            st.info("Nenhum caso salvo ainda.")
    else:
        st.info("Módulo de persistência não encontrado.")
