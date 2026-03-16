from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st

from bowtie_visual import build_bowtie_custom_figure
from case_store import list_cases, load_case, save_case
from chemicals_seed import LOCAL_COMPOUNDS
from comparator import build_comparison_df, build_comparison_highlights
from compound_engine import (
    build_compound_profile,
    suggest_hazop_priorities,
    suggest_lopa_ipls,
)
from dense_gas_router import classify_dispersion_mode
from deterministic import IPL_CATALOG, compute_lopa, gaussian_dispersion, pool_fire
from executive_report import build_executive_bundle
from hazop_db import HAZOP_DB
from moc_engine import evaluate_moc
from moc_visuals import build_moc_impacts_figure, build_moc_score_figure
from property_status import build_property_status_df, summarize_property_status
from psi_readiness import build_psi_readiness_df, summarize_psi_readiness
from psi_visuals import build_psi_pillars_figure, build_psi_score_figure
from pssr_engine import evaluate_pssr
from pssr_visuals import build_pssr_score_figure
from reactivity_engine import evaluate_pairwise_reactivity
from reactivity_visuals import build_pairwise_matrix_figure
from risk_register import build_risk_register
from risk_visuals import (
    build_confidence_figure,
    build_hazard_fingerprint_figure,
    build_incompatibility_matrix_figure,
    build_ipl_layers_figure,
    build_risk_matrix_figure,
    build_source_coverage_figure,
)
from source_governance import (
    build_evidence_ledger_df,
    build_source_recommendations,
    summarize_evidence,
)
from source_visuals import build_link_coverage_figure, build_source_summary_figure
from ui_formatters import format_identity_df, format_limits_df, format_physchem_df


APP_CSS = """
<style>
.stApp {
    background: linear-gradient(180deg, #07111f, #081a31);
    color: #e9f1ff;
}
.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 1450px;
}
.hero {
    background: linear-gradient(135deg, #0d2345, #0b1830);
    border: 1px solid #1c3f78;
    border-radius: 20px;
    padding: 1.3rem 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 12px 30px rgba(0,0,0,0.18);
}
.hero h1 {
    margin: 0 0 0.35rem 0;
    color: #f4f8ff;
    font-size: 2rem;
    font-weight: 800;
}
.hero p {
    margin: 0;
    color: #9fc1ff;
    font-size: 1rem;
}
.badge {
    display: inline-block;
    margin: 0.40rem 0.35rem 0 0;
    padding: 0.28rem 0.65rem;
    border-radius: 999px;
    border: 1px solid #2b5aa1;
    color: #cfe1ff;
    background: rgba(31, 74, 139, 0.18);
    font-size: 0.78rem;
}
.metric-box {
    background: rgba(10,22,42,0.95);
    border: 1px solid #1d365f;
    border-radius: 18px;
    padding: 1rem;
    min-height: 118px;
    box-shadow: 0 8px 18px rgba(0,0,0,0.12);
}
.metric-label {
    color: #7ea8ea;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.metric-value {
    color: white;
    font-size: 1.55rem;
    font-weight: 800;
    margin-top: 0.45rem;
    line-height: 1.1;
}
.risk-blue { color: #62a8ff; }
.risk-green { color: #34d399; }
.risk-amber { color: #fbbf24; }
.risk-red { color: #fb7185; }

.panel {
    background: rgba(9,17,31,0.94);
    border: 1px solid #1d365f;
    border-radius: 18px;
    padding: 1rem 1rem 0.95rem 1rem;
    margin-bottom: 0.9rem;
    box-shadow: 0 8px 18px rgba(0,0,0,0.10);
}
.panel h3 {
    margin-top: 0;
    margin-bottom: 0.8rem;
    color: #f0f6ff;
    font-size: 1rem;
    font-weight: 800;
}
.small-muted {
    color: #9ab2d8;
    font-size: 0.9rem;
}
.note-card {
    background: rgba(12, 28, 54, 0.95);
    border-left: 4px solid #4b88ff;
    border-radius: 12px;
    padding: 0.9rem 1rem;
    color: #e9f1ff;
}
.source-card {
    background: rgba(12, 24, 43, 0.95);
    border: 1px solid #21416e;
    border-radius: 14px;
    padding: 0.9rem;
    height: 100%;
}
.kpi-chip {
    display: inline-block;
    padding: 0.28rem 0.65rem;
    border-radius: 999px;
    border: 1px solid #2b5aa1;
    margin-right: 0.45rem;
    margin-bottom: 0.35rem;
    color: #d9e8ff;
    background: rgba(31, 74, 139, 0.14);
    font-size: 0.78rem;
}
</style>
"""

st.set_page_config(
    page_title="ChemSafe Pro Deterministic",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(APP_CSS, unsafe_allow_html=True)


# =========================
# Estado da sessão
# =========================
DEFAULT_COMPOUND_KEY = "ammonia"

if "selected_compound_key" not in st.session_state:
    st.session_state.selected_compound_key = DEFAULT_COMPOUND_KEY
if "profile" not in st.session_state:
    st.session_state.profile = None
if "compare_profile" not in st.session_state:
    st.session_state.compare_profile = None
if "compare_query" not in st.session_state:
    st.session_state.compare_query = ""
if "lopa_result" not in st.session_state:
    st.session_state.lopa_result = None
if "dispersion_result" not in st.session_state:
    st.session_state.dispersion_result = None
if "pool_fire_result" not in st.session_state:
    st.session_state.pool_fire_result = None
if "selected_ipl_names" not in st.session_state:
    st.session_state.selected_ipl_names = []
if "current_case_name" not in st.session_state:
    st.session_state.current_case_name = ""
if "current_case_notes" not in st.session_state:
    st.session_state.current_case_notes = ""
if "bowtie_initialized_for" not in st.session_state:
    st.session_state.bowtie_initialized_for = ""
if "moc_result" not in st.session_state:
    st.session_state.moc_result = None
if "pssr_result" not in st.session_state:
    st.session_state.pssr_result = None
if "reactivity_partner_profile" not in st.session_state:
    st.session_state.reactivity_partner_profile = None
if "reactivity_result" not in st.session_state:
    st.session_state.reactivity_result = None
if "report_bundle" not in st.session_state:
    st.session_state.report_bundle = None


# =========================
# Helpers
# =========================
def metric_card(label: str, value: str, klass: str = "risk-blue") -> str:
    return (
        f"<div class='metric-box'>"
        f"<div class='metric-label'>{label}</div>"
        f"<div class='metric-value {klass}'>{value}</div>"
        f"</div>"
    )


def quick_compounds():
    return {k: v["identity"]["name"] for k, v in LOCAL_COMPOUNDS.items()}


def load_profile_from_key(key: str) -> None:
    aliases = LOCAL_COMPOUNDS[key]["aliases"]
    profile = build_compound_profile(aliases[0])
    st.session_state.selected_compound_key = key
    st.session_state.profile = profile


def _default_bowtie_lists(profile):
    threats = []
    barriers_pre = []
    consequences = []
    barriers_mit = []

    if profile.flags.get("flammable"):
        threats += ["Fonte de ignição", "Vazamento", "Ventilação insuficiente"]
        barriers_pre += ["Controle de ignição", "Detecção", "Aterramento"]
        consequences += ["Incêndio", "Flash fire", "Dano à instalação"]
        barriers_mit += ["Combate a incêndio", "Contenção", "Plano de emergência"]

    if profile.flags.get("toxic_inhalation"):
        threats += ["Falha de vedação", "Abertura indevida", "Sobrepressão"]
        barriers_pre += ["Isolamento", "ESD", "Inspeção"]
        consequences += ["Exposição ocupacional", "Evacuação", "Impacto comunitário"]
        barriers_mit += ["Alarme", "Evacuação", "Abatimento / ventilação"]

    if profile.flags.get("corrosive"):
        threats += ["Corrosão", "Material incompatível"]
        barriers_pre += ["Seleção de materiais", "Inspeção de integridade"]
        consequences += ["Perda de contenção", "Dano a equipamento"]
        barriers_mit += ["Chuveiro / lava-olhos", "Containment"]

    threats = list(dict.fromkeys(threats))[:5]
    barriers_pre = list(dict.fromkeys(barriers_pre))[:5]
    consequences = list(dict.fromkeys(consequences))[:5]
    barriers_mit = list(dict.fromkeys(barriers_mit))[:5]

    if not threats:
        threats = ["Desvio operacional", "Falha de válvula", "Falha de instrumentação"]
    if not barriers_pre:
        barriers_pre = ["Procedimento operacional", "Inspeção", "Alarme"]
    if not consequences:
        consequences = ["Perda de contenção", "Parada de processo", "Exposição ocupacional"]
    if not barriers_mit:
        barriers_mit = ["Evacuação", "Resposta à emergência", "Containment"]

    return {
        "threats": threats,
        "barriers_pre": barriers_pre,
        "top_event": "Perda de contenção / perda de controle",
        "barriers_mit": barriers_mit,
        "consequences": consequences,
    }


def ensure_bowtie_state(profile):
    compound_marker = profile.identity.get("name", "")
    if st.session_state.bowtie_initialized_for != compound_marker:
        defaults = _default_bowtie_lists(profile)
        st.session_state.bowtie_threats = "\n".join(defaults["threats"])
        st.session_state.bowtie_pre = "\n".join(defaults["barriers_pre"])
        st.session_state.bowtie_top = defaults["top_event"]
        st.session_state.bowtie_mit = "\n".join(defaults["barriers_mit"])
        st.session_state.bowtie_cons = "\n".join(defaults["consequences"])
        st.session_state.bowtie_initialized_for = compound_marker


def bowtie_payload():
    return {
        "threats": [x.strip() for x in st.session_state.get("bowtie_threats", "").splitlines() if x.strip()],
        "barriers_pre": [x.strip() for x in st.session_state.get("bowtie_pre", "").splitlines() if x.strip()],
        "top_event": st.session_state.get("bowtie_top", "Perda de contenção / perda de controle"),
        "barriers_mit": [x.strip() for x in st.session_state.get("bowtie_mit", "").splitlines() if x.strip()],
        "consequences": [x.strip() for x in st.session_state.get("bowtie_cons", "").splitlines() if x.strip()],
    }


def apply_loaded_case(case_data: dict):
    query_hint = case_data.get("query_hint") or case_data.get("compound_name")
    if query_hint:
        profile = build_compound_profile(query_hint)
        if profile is not None:
            st.session_state.profile = profile

    st.session_state.current_case_name = case_data.get("case_name", "")
    st.session_state.current_case_notes = case_data.get("notes", "")
    st.session_state.selected_ipl_names = case_data.get("selected_ipl_names", [])
    st.session_state.lopa_result = case_data.get("lopa_result")
    st.session_state.moc_result = case_data.get("moc_result")
    st.session_state.pssr_result = case_data.get("pssr_result")
    st.session_state.reactivity_result = case_data.get("reactivity_result")

    bowtie = case_data.get("bowtie", {})
    if bowtie:
        st.session_state.bowtie_threats = "\n".join(bowtie.get("threats", []))
        st.session_state.bowtie_pre = "\n".join(bowtie.get("barriers_pre", []))
        st.session_state.bowtie_top = bowtie.get("top_event", "Perda de contenção / perda de controle")
        st.session_state.bowtie_mit = "\n".join(bowtie.get("barriers_mit", []))
        st.session_state.bowtie_cons = "\n".join(bowtie.get("consequences", []))
        if st.session_state.profile is not None:
            st.session_state.bowtie_initialized_for = st.session_state.profile.identity.get("name", "")


# =========================
# Sidebar
# =========================
with st.sidebar:
    st.markdown("## ⚗️ ChemSafe Pro")
    st.caption("Plataforma determinística de segurança de processo")
    st.markdown("---")

    st.write("**Acesso rápido**")
    for key, name in quick_compounds().items():
        if st.button(name, key=f"quick_{key}", width="stretch"):
            load_profile_from_key(key)

    st.markdown("---")
    manual_query = st.text_input("Buscar composto", placeholder="Nome, CAS ou fórmula")
    if st.button("Carregar composto", width="stretch"):
        if manual_query.strip():
            profile = build_compound_profile(manual_query.strip())
            if profile is None:
                st.warning("Composto não encontrado nem nas bases consultadas.")
            else:
                st.session_state.profile = profile

    st.markdown("---")
    st.write("**Meta do produto**")
    st.caption("PSI + HAZOP + LOPA + Consequências + Governança + Reatividade")
    st.markdown("---")

    saved_cases = list_cases()
    if saved_cases:
        st.write("**Casos salvos**")
        for item in saved_cases[:6]:
            st.caption(f"• {item['case_name']}")


# Inicialização
if st.session_state.profile is None:
    load_profile_from_key(st.session_state.selected_compound_key)

profile = st.session_state.profile
ensure_bowtie_state(profile)


# =========================
# Hero
# =========================
st.markdown(
    """
    <div class="hero">
      <h1>ChemSafe Pro Deterministic</h1>
      <p>Segurança de processo guiada por propriedades reais, fontes rastreáveis e lógica de decisão transparente.</p>
      <div>
        <span class="badge">Busca universal</span>
        <span class="badge">Pacote curado + ao vivo</span>
        <span class="badge">Governança de fontes</span>
        <span class="badge">HAZOP</span>
        <span class="badge">LOPA</span>
        <span class="badge">PSI / PSM</span>
        <span class="badge">MOC</span>
        <span class="badge">PSSR</span>
        <span class="badge">Reatividade</span>
        <span class="badge">Relatório executivo</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================
# Tabs
# =========================
overview_tab, compound_tab, sources_tab, compare_tab, reactivity_tab, hazop_tab, bowtie_tab, lopa_tab, psi_tab, moc_tab, pssr_tab, consequence_tab, report_tab, refs_tab, cases_tab = st.tabs(
    ["Overview", "Composto", "Fontes / Evidências", "Comparador", "Reatividade", "HAZOP", "Bow-Tie", "LOPA", "PSI / PSM", "MOC", "PSSR", "Consequências", "Relatório", "Referências", "Casos"]
)


# =========================
# OVERVIEW
# =========================
with overview_tab:
    dispersion_mode = classify_dispersion_mode(profile)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.markdown(metric_card("Composto", profile.identity.get("name", "—")), unsafe_allow_html=True)
    c2.markdown(metric_card("CAS", profile.identity.get("cas", "—")), unsafe_allow_html=True)
    c3.markdown(metric_card("Rotas priorizadas", str(len(profile.routing))), unsafe_allow_html=True)
    c4.markdown(
        metric_card(
            "Confiança",
            f"{profile.confidence_score:.0f}/100",
            "risk-green" if profile.confidence_score >= 80 else "risk-amber" if profile.confidence_score >= 50 else "risk-red",
        ),
        unsafe_allow_html=True,
    )
    c5.markdown(metric_card("Modo de dispersão", dispersion_mode["label"]), unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        st.markdown("<div class='panel'><h3>Hazard fingerprint</h3></div>", unsafe_allow_html=True)
        st.pyplot(build_hazard_fingerprint_figure(profile), clear_figure=True)
    with right:
        st.markdown("<div class='panel'><h3>Confiança do pacote de dados</h3></div>", unsafe_allow_html=True)
        st.pyplot(build_confidence_figure(profile), clear_figure=True)

    left, right = st.columns(2)
    with left:
        st.markdown("<div class='panel'><h3>Cobertura de fontes</h3></div>", unsafe_allow_html=True)
        st.pyplot(build_source_coverage_figure(profile), clear_figure=True)
    with right:
        st.markdown("<div class='panel'><h3>Readiness para screening</h3></div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(profile.readiness), width="stretch", hide_index=True)

    st.markdown("<div class='panel'><h3>Status do pacote de propriedades</h3></div>", unsafe_allow_html=True)
    status_summary = summarize_property_status(profile)
    chips = [f"<span class='kpi-chip'>{k}: {v}</span>" for k, v in status_summary.items()]
    st.markdown("".join(chips), unsafe_allow_html=True)
    st.dataframe(build_property_status_df(profile), width="stretch", hide_index=True)

    st.markdown("<div class='panel'><h3>Roteamento automático</h3></div>", unsafe_allow_html=True)
    for item in profile.routing:
        st.success(item)

    if profile.validation_gaps:
        st.markdown("<div class='panel'><h3>Lacunas de dados</h3></div>", unsafe_allow_html=True)
        for gap in profile.validation_gaps:
            st.warning(gap)


# =========================
# COMPOSTO
# =========================
with compound_tab:
    left, right = st.columns(2)

    with left:
        st.markdown("<div class='panel'><h3>Identidade e descritores</h3></div>", unsafe_allow_html=True)
        st.dataframe(format_identity_df(profile), width="stretch", hide_index=True)

        st.markdown("<div class='panel'><h3>Perigos / GHS</h3></div>", unsafe_allow_html=True)
        if profile.hazards:
            for hz in profile.hazards:
                st.error(hz)
        else:
            st.info("Sem hazards estruturados para este composto.")

        st.markdown("<div class='panel'><h3>NFPA</h3></div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([profile.nfpa]), width="stretch", hide_index=True)

    with right:
        st.markdown("<div class='panel'><h3>Propriedades físico-químicas</h3></div>", unsafe_allow_html=True)
        st.dataframe(format_physchem_df(profile), width="stretch", hide_index=True)

        st.markdown("<div class='panel'><h3>Limites de exposição</h3></div>", unsafe_allow_html=True)
        limits_df = format_limits_df(profile)
        if not limits_df.empty:
            st.dataframe(limits_df, width="stretch", hide_index=True)
        else:
            st.info("Sem limites estruturados para este composto.")

        st.markdown("<div class='panel'><h3>Incompatibilidades / armazenamento</h3></div>", unsafe_allow_html=True)
        incompat = profile.storage.get("incompatibilities", [])
        notes = profile.storage.get("notes", [])
        if incompat:
            for item in incompat:
                st.warning(item)
        else:
            st.info("Sem incompatibilidades estruturadas.")
        if notes:
            for item in notes:
                st.info(item)

    st.markdown("<div class='panel'><h3>Matriz de compatibilidade</h3></div>", unsafe_allow_html=True)
    st.pyplot(build_incompatibility_matrix_figure(profile), clear_figure=True)

    st.markdown("<div class='panel'><h3>Links oficiais</h3></div>", unsafe_allow_html=True)
    links = profile.storage.get("official_links", [])
    link_cols = st.columns(3)
    for i, item in enumerate(links):
        with link_cols[i % 3]:
            st.markdown(
                f"<div class='source-card'><b>{item['source']}</b><br><span class='small-muted'>{item['purpose']}</span></div>",
                unsafe_allow_html=True,
            )
            st.link_button(f"Abrir {item['source']}", item["url"], width="stretch")


# =========================
# FONTES / EVIDÊNCIAS
# =========================
with sources_tab:
    st.markdown("<div class='panel'><h3>Governança de fontes e evidências</h3></div>", unsafe_allow_html=True)

    evidence_df = build_evidence_ledger_df(profile)
    source_summary = summarize_evidence(profile)

    a, b, c, d, e = st.columns(5)
    a.markdown(metric_card("Campos rastreados", str(source_summary["linhas"]), "risk-blue"), unsafe_allow_html=True)
    b.markdown(metric_card("Fontes oficiais", str(source_summary["oficial"]), "risk-green"), unsafe_allow_html=True)
    c.markdown(metric_card("Curado", str(source_summary["curado"]), "risk-blue"), unsafe_allow_html=True)
    d.markdown(metric_card("Revisar", str(source_summary["revisar"]), "risk-red"), unsafe_allow_html=True)
    e.markdown(metric_card("Com link oficial", str(source_summary["com_link"]), "risk-amber"), unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        st.markdown("<div class='panel'><h3>Cobertura de fontes</h3></div>", unsafe_allow_html=True)
        st.pyplot(build_source_summary_figure(source_summary), clear_figure=True)

    with right:
        st.markdown("<div class='panel'><h3>Cobertura de links</h3></div>", unsafe_allow_html=True)
        st.pyplot(build_link_coverage_figure(source_summary), clear_figure=True)

    st.markdown("<div class='panel'><h3>Ledger de evidências</h3></div>", unsafe_allow_html=True)
    st.dataframe(evidence_df, width="stretch", hide_index=True)

    st.markdown("<div class='panel'><h3>Recomendações de governança</h3></div>", unsafe_allow_html=True)
    for item in build_source_recommendations(profile):
        st.info(item)


# =========================
# COMPARADOR
# =========================
with compare_tab:
    st.markdown("<div class='panel'><h3>Comparador entre compostos</h3></div>", unsafe_allow_html=True)

    c1, c2 = st.columns([3, 1])
    with c1:
        st.session_state.compare_query = st.text_input(
            "Segundo composto para comparação",
            value=st.session_state.compare_query,
            placeholder="Ex.: propane, propano, 74-98-6, C3H8",
        )
    with c2:
        if st.button("Comparar", type="primary", width="stretch"):
            if st.session_state.compare_query.strip():
                st.session_state.compare_profile = build_compound_profile(st.session_state.compare_query.strip())

    compare_profile = st.session_state.compare_profile
    if compare_profile is not None:
        st.dataframe(build_comparison_df(profile, compare_profile), width="stretch", hide_index=True)
        st.markdown("<div class='panel'><h3>Leitura rápida da comparação</h3></div>", unsafe_allow_html=True)
        for line in build_comparison_highlights(profile, compare_profile):
            st.info(line)
    else:
        st.info("Carregue um segundo composto para comparar propriedades e riscos.")


# =========================
# REATIVIDADE
# =========================
with reactivity_tab:
    st.markdown("<div class='panel'><h3>Reactivity Lab — compatibilidade entre substâncias</h3></div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='note-card'>Esta aba implementa a sugestão de matriz de incompatibilidade entre substâncias. Ela serve para screening inicial de mistura acidental, segregação e revisão de mitigação.</div>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([3, 1])
    with c1:
        partner_query = st.text_input(
            "Segundo composto para análise de compatibilidade",
            value="",
            placeholder="Ex.: hipoclorito de sódio, sodium hypochlorite, água, ácido nítrico...",
            key="reactivity_partner_query",
        )
    with c2:
        if st.button("Carregar segundo composto", type="primary", width="stretch"):
            if partner_query.strip():
                st.session_state.reactivity_partner_profile = build_compound_profile(partner_query.strip())
                if st.session_state.reactivity_partner_profile is not None:
                    st.session_state.reactivity_result = evaluate_pairwise_reactivity(
                        profile,
                        st.session_state.reactivity_partner_profile,
                    )

    partner = st.session_state.get("reactivity_partner_profile")
    result = st.session_state.get("reactivity_result")

    if partner is not None and result is not None:
        summary = result["summary"]

        a, b, c, d = st.columns(4)
        a.markdown(metric_card("Composto A", summary["compound_a"], "risk-blue"), unsafe_allow_html=True)
        b.markdown(metric_card("Composto B", summary["compound_b"], "risk-blue"), unsafe_allow_html=True)
        c.markdown(
            metric_card(
                "Severidade",
                summary["severity"],
                "risk-green" if summary["severity"] == "OK" else "risk-amber" if summary["severity"] in ["Revisar", "Cuidado"] else "risk-red",
            ),
            unsafe_allow_html=True,
        )
        d.markdown(
            metric_card(
                "Score de compatibilidade",
                f"{summary['score']}/100",
                "risk-green" if summary["score"] < 40 else "risk-amber" if summary["score"] < 80 else "risk-red",
            ),
            unsafe_allow_html=True,
        )

        left, right = st.columns(2)
        with left:
            st.markdown("<div class='panel'><h3>Famílias inferidas — composto A</h3></div>", unsafe_allow_html=True)
            for fam in result["families_a"]:
                st.info(fam)

        with right:
            st.markdown("<div class='panel'><h3>Famílias inferidas — composto B</h3></div>", unsafe_allow_html=True)
            for fam in result["families_b"]:
                st.info(fam)

        st.markdown("<div class='panel'><h3>Matriz de compatibilidade</h3></div>", unsafe_allow_html=True)
        st.pyplot(build_pairwise_matrix_figure(result["matrix_df"]), clear_figure=True)

        st.markdown("<div class='panel'><h3>Regras disparadas</h3></div>", unsafe_allow_html=True)
        hits_df = result["hits_df"]
        if hits_df.empty:
            st.success("Nenhuma regra forte de incompatibilidade foi disparada no screening atual.")
        else:
            st.dataframe(hits_df, width="stretch", hide_index=True)

        st.markdown("<div class='panel'><h3>Mitigações sugeridas</h3></div>", unsafe_allow_html=True)
        for item in result["recommendations"]:
            st.warning(item)
    else:
        st.info("Carregue um segundo composto para montar a matriz de compatibilidade entre substâncias.")


# =========================
# HAZOP
# =========================
with hazop_tab:
    equipment = st.selectbox(
        "Equipamento / nó",
        [
            "Tanque atmosférico",
            "Reator CSTR exotérmico",
            "Vaso de pressão",
            "Trocador de calor",
            "Tubulação de processo",
            "Bomba centrífuga",
        ],
    )

    priorities = suggest_hazop_priorities(profile, equipment)
    risk_register_df = build_risk_register(
        profile=profile,
        hazop_priorities=priorities,
        lopa_result=st.session_state.get("lopa_result"),
        dispersion_mode=classify_dispersion_mode(profile),
    )

    st.markdown("<div class='panel'><h3>Prioridades de HAZOP orientadas pelo composto</h3></div>", unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(priorities), width="stretch", hide_index=True)

    st.markdown("<div class='panel'><h3>Matriz de risco dos focos priorizados</h3></div>", unsafe_allow_html=True)
    st.pyplot(build_risk_matrix_figure(priorities), clear_figure=True)

    st.markdown("<div class='panel'><h3>Registro inicial de riscos</h3></div>", unsafe_allow_html=True)
    st.dataframe(risk_register_df, width="stretch", hide_index=True)

    st.markdown("<div class='panel'><h3>Worksheet HAZOP base</h3></div>", unsafe_allow_html=True)
    param = st.selectbox("Parâmetro", list(HAZOP_DB.keys()))
    guideword = st.selectbox("Palavra-guia", ["MAIS", "MENOS", "NÃO / NENHUM"])
    db = HAZOP_DB.get(param, {}).get(guideword, {})
    if db:
        rows = []
        causes = db.get("causas", [])
        cons = db.get("conseqs", [])
        sav = db.get("salvags", [])
        rec = db.get("rec", [])
        for i, cause in enumerate(causes):
            rows.append(
                {
                    "Desvio": f"{guideword} {param}" if i == 0 else "idem",
                    "Causa": cause,
                    "Consequência": cons[i] if i < len(cons) else (cons[0] if cons else "—"),
                    "Salvaguarda": sav[i] if i < len(sav) else (sav[0] if sav else "—"),
                    "Recomendação": rec[i] if i < len(rec) else (rec[0] if rec else "—"),
                }
            )
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


# =========================
# BOW-TIE
# =========================
with bowtie_tab:
    st.markdown("<div class='panel'><h3>Bow-Tie editável do caso</h3></div>", unsafe_allow_html=True)

    modo_bowtie = st.radio(
        "Modo de visualização",
        options=["Executivo", "Técnico"],
        horizontal=True,
    )
    modo_bowtie_internal = "executivo" if modo_bowtie == "Executivo" else "tecnico"

    c1, c2 = st.columns(2)
    with c1:
        st.text_area("Ameaças (uma por linha)", key="bowtie_threats", height=160)
        st.text_area("Barreiras preventivas (uma por linha)", key="bowtie_pre", height=160)
    with c2:
        st.text_input("Top Event", key="bowtie_top")
        st.text_area("Barreiras mitigadoras (uma por linha)", key="bowtie_mit", height=160)
        st.text_area("Consequências (uma por linha)", key="bowtie_cons", height=160)

    bt = bowtie_payload()
    st.pyplot(
        build_bowtie_custom_figure(
            threats=bt["threats"],
            barriers_pre=bt["barriers_pre"],
            top_event=bt["top_event"],
            barriers_mit=bt["barriers_mit"],
            consequences=bt["consequences"],
            mode=modo_bowtie_internal,
        ),
        clear_figure=True,
    )

    st.markdown(
        "<div class='note-card'><b>Modo Executivo:</b> visão mais limpa para reunião, cliente e resumo.<br><b>Modo Técnico:</b> maior densidade de informação para engenharia.</div>",
        unsafe_allow_html=True,
    )


# =========================
# LOPA
# =========================
with lopa_tab:
    st.markdown("<div class='panel'><h3>IPLs sugeridas pelo perfil do composto</h3></div>", unsafe_allow_html=True)
    suggested_ipls = suggest_lopa_ipls(profile)
    if suggested_ipls:
        for item in suggested_ipls:
            st.success(item)
    else:
        st.info("Nenhuma IPL sugerida automaticamente para este perfil.")

    left, right = st.columns(2)
    with left:
        f_ie = st.number_input("Frequência do evento iniciador (1/ano)", value=0.1, min_value=0.000001, format="%.6f")
        criterion_label = st.selectbox(
            "Critério tolerável",
            [
                "Fatalidade / catástrofe ambiental — 1e-5/ano",
                "Lesão grave / dano severo — 1e-4/ano",
                "Lesão moderada — 1e-3/ano",
            ],
        )
        criterion = {
            "Fatalidade / catástrofe ambiental — 1e-5/ano": 1e-5,
            "Lesão grave / dano severo — 1e-4/ano": 1e-4,
            "Lesão moderada — 1e-3/ano": 1e-3,
        }[criterion_label]

    with right:
        selected = st.multiselect(
            "IPLs selecionadas",
            options=[f"{n} (PFD={p})" for n, p in IPL_CATALOG],
            default=[f"{IPL_CATALOG[0][0]} (PFD={IPL_CATALOG[0][1]})"],
        )

    if st.button("Calcular LOPA / SIL", type="primary"):
        chosen = []
        selected_names = []
        for label in selected:
            selected_names.append(label)
            for name, pfd in IPL_CATALOG:
                if name in label:
                    chosen.append((name, pfd))
                    break
        st.session_state.selected_ipl_names = selected_names
        st.session_state.lopa_result = compute_lopa(f_ie, criterion, chosen)

    if st.session_state.lopa_result:
        r = st.session_state.lopa_result
        a, b, c, d = st.columns(4)
        a.markdown(metric_card("F_ie", f"{r['f_ie']:.2e}/ano"), unsafe_allow_html=True)
        b.markdown(metric_card("PFD total", f"{r['pfd_total']:.2e}"), unsafe_allow_html=True)
        c.markdown(metric_card("MCF", f"{r['mcf']:.2e}/ano", "risk-red" if r["ratio"] > 1 else "risk-green"), unsafe_allow_html=True)
        d.markdown(metric_card("SIL", r["sil"], "risk-amber"), unsafe_allow_html=True)

        st.dataframe(pd.DataFrame(r["selected_ipls"], columns=["IPL", "PFD"]), width="stretch", hide_index=True)

        st.markdown("<div class='panel'><h3>Panorama das camadas de proteção</h3></div>", unsafe_allow_html=True)
        selected_names = st.session_state.get("selected_ipl_names", [])
        st.pyplot(build_ipl_layers_figure(selected_names, suggested_ipls), clear_figure=True)


# =========================
# PSI / PSM
# =========================
with psi_tab:
    st.markdown("<div class='panel'><h3>PSI / PSM Readiness do caso</h3></div>", unsafe_allow_html=True)

    psi_df = build_psi_readiness_df(
        profile=profile,
        lopa_result=st.session_state.get("lopa_result"),
        bowtie=bowtie_payload(),
    )
    psi_summary = summarize_psi_readiness(psi_df)

    a, b, c, d = st.columns(4)
    a.markdown(
        metric_card(
            "Score PSI / PSM",
            f"{psi_summary['score']:.0f}/100",
            "risk-green" if psi_summary["score"] >= 80 else "risk-amber" if psi_summary["score"] >= 50 else "risk-red",
        ),
        unsafe_allow_html=True,
    )
    b.markdown(metric_card("Itens OK", str(psi_summary["ok"]), "risk-green"), unsafe_allow_html=True)
    c.markdown(metric_card("Itens parciais", str(psi_summary["partial"]), "risk-amber"), unsafe_allow_html=True)
    d.markdown(metric_card("Gaps", str(psi_summary["gap"]), "risk-red"), unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        st.markdown("<div class='panel'><h3>Score de prontidão</h3></div>", unsafe_allow_html=True)
        st.pyplot(build_psi_score_figure(psi_summary), clear_figure=True)

    with right:
        st.markdown("<div class='panel'><h3>Cobertura por pilar</h3></div>", unsafe_allow_html=True)
        st.pyplot(build_psi_pillars_figure(psi_df), clear_figure=True)

    st.markdown("<div class='panel'><h3>Checklist PSI / PSM</h3></div>", unsafe_allow_html=True)
    st.dataframe(psi_df, width="stretch", hide_index=True)

    gaps = psi_df[psi_df["Status"] == "GAP"]
    if not gaps.empty:
        st.markdown("<div class='panel'><h3>Ações prioritárias</h3></div>", unsafe_allow_html=True)
        for _, row in gaps.head(5).iterrows():
            st.warning(f"{row['Item']}: {row['Ação recomendada']}")


# =========================
# MOC
# =========================
with moc_tab:
    st.markdown("<div class='panel'><h3>MOC — Management of Change</h3></div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='note-card'>Use este módulo para triagem inicial da criticidade de mudanças em química, processo, materiais, instrumentação, alívio e procedimentos.</div>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        change_type = st.selectbox(
            "Tipo principal de mudança",
            [
                "Mudança química / novo composto",
                "Mudança de condição operacional",
                "Mudança de equipamento / material",
                "Mudança de instrumentação / controle",
                "Mudança em alívio / PSV",
                "Mudança de procedimento / operação",
                "Mudança organizacional / treinamento",
            ],
        )

        impacts = st.multiselect(
            "Aspectos impactados",
            [
                "Química / composição",
                "Pressão",
                "Temperatura",
                "Vazão",
                "Inventário",
                "Materiais de construção",
                "Instrumentação / controle",
                "Alívio / PSV",
                "Ventilação / detecção",
                "Procedimentos operacionais",
            ],
        )

        description = st.text_area(
            "Descrição da mudança",
            height=160,
            placeholder="Descreva o que muda, por que muda, onde muda e qual o objetivo técnico/operacional.",
        )

    with c2:
        temporary = st.checkbox("Mudança temporária")
        protections_changed = st.checkbox("Afeta barreiras / proteções")
        procedures_changed = st.checkbox("Exige revisão de procedimentos")
        pids_affected = st.checkbox("Afeta P&ID / documentação")
        training_required = st.checkbox("Exige treinamento")
        new_chemical = st.checkbox("Introduce novo composto / nova composição")
        bypass_or_override = st.checkbox("Envolve bypass / override / desabilitação")

    if st.button("Avaliar MOC", type="primary"):
        st.session_state.moc_result = evaluate_moc(
            profile=profile,
            change_type=change_type,
            impacts=impacts,
            description=description,
            temporary=temporary,
            protections_changed=protections_changed,
            procedures_changed=procedures_changed,
            pids_affected=pids_affected,
            training_required=training_required,
            new_chemical=new_chemical,
            bypass_or_override=bypass_or_override,
        )

    moc_result = st.session_state.get("moc_result")
    if moc_result:
        summary = moc_result["summary"]
        checklist_df = pd.DataFrame(moc_result["checklist_rows"])
        actions_df = pd.DataFrame(moc_result["actions_rows"])

        a, b, c, d = st.columns(4)
        a.markdown(
            metric_card(
                "Score MOC",
                f"{summary['score']:.0f}/100",
                "risk-green" if summary["score"] < 25 else "risk-amber" if summary["score"] < 75 else "risk-red",
            ),
            unsafe_allow_html=True,
        )
        b.markdown(
            metric_card(
                "Classe",
                summary["category"],
                "risk-green" if summary["category"] == "Baixa" else "risk-amber" if summary["category"] in ["Moderada", "Alta"] else "risk-red",
            ),
            unsafe_allow_html=True,
        )
        c.markdown(metric_card("Gaps", str(summary["gap_count"]), "risk-red"), unsafe_allow_html=True)
        d.markdown(metric_card("Revisões requeridas", str(summary["review_count"]), "risk-blue"), unsafe_allow_html=True)

        left, right = st.columns(2)
        with left:
            st.markdown("<div class='panel'><h3>Score de criticidade</h3></div>", unsafe_allow_html=True)
            st.pyplot(build_moc_score_figure(summary), clear_figure=True)

        with right:
            st.markdown("<div class='panel'><h3>Impactos da mudança</h3></div>", unsafe_allow_html=True)
            st.pyplot(build_moc_impacts_figure(moc_result["impact_rows"]), clear_figure=True)

        st.markdown("<div class='panel'><h3>Checklist de revisão</h3></div>", unsafe_allow_html=True)
        st.dataframe(checklist_df, width="stretch", hide_index=True)

        st.markdown("<div class='panel'><h3>Ações requeridas</h3></div>", unsafe_allow_html=True)
        st.dataframe(actions_df, width="stretch", hide_index=True)

        critical_gaps = checklist_df[checklist_df["Status"] == "GAP"]
        if not critical_gaps.empty:
            st.markdown("<div class='panel'><h3>Pontos críticos</h3></div>", unsafe_allow_html=True)
            for _, row in critical_gaps.iterrows():
                st.warning(f"{row['Item']}: {row['Comentário']}")


# =========================
# PSSR
# =========================
with pssr_tab:
    st.markdown("<div class='panel'><h3>PSSR — Pre-Startup Safety Review</h3></div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='note-card'>Esta aba usa os requisitos mínimos de PSSR como base e adiciona verificações práticas de prontidão para partida.</div>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        scope_label = st.selectbox("Escopo do PSSR", ["PHA para nova instalação", "MOC para instalação modificada"])
        design_ok = st.checkbox("Construção/equipamento conforme especificação de projeto")
        procedures_ok = st.checkbox("Procedimentos de segurança/operação/manutenção/emergência adequados")
        training_ok = st.checkbox("Treinamento concluído para os envolvidos")
        pha_or_moc_ok = st.checkbox("Base de PHA/MOC resolvida para a partida")
    with c2:
        mi_ready = st.checkbox("Mechanical integrity / prontidão de equipamento")
        relief_verified = st.checkbox("PSV / alívio / bloqueios revisados")
        alarms_tested = st.checkbox("Alarmes, trips, detectores e permissivos testados")
        emergency_ready = st.checkbox("Plano de emergência e resposta disponível")
        startup_authorized = st.checkbox("Autorização formal para startup")

    if st.button("Avaliar PSSR", type="primary"):
        st.session_state.pssr_result = evaluate_pssr(
            design_ok=design_ok,
            procedures_ok=procedures_ok,
            pha_or_moc_ok=pha_or_moc_ok,
            training_ok=training_ok,
            mi_ready=mi_ready,
            relief_verified=relief_verified,
            alarms_tested=alarms_tested,
            emergency_ready=emergency_ready,
            startup_authorized=startup_authorized,
            scope_label=scope_label,
        )

    pssr_result = st.session_state.get("pssr_result")
    if pssr_result:
        summary = pssr_result["summary"]
        checklist_df = pd.DataFrame(pssr_result["checklist_rows"])
        actions_df = pd.DataFrame(pssr_result["actions_rows"])

        a, b, c, d = st.columns(4)
        a.markdown(
            metric_card(
                "Score PSSR",
                f"{summary['score']:.0f}/100",
                "risk-green" if summary["score"] >= 80 else "risk-amber" if summary["score"] >= 60 else "risk-red",
            ),
            unsafe_allow_html=True,
        )
        b.markdown(
            metric_card(
                "Readiness",
                summary["readiness"],
                "risk-green" if summary["readiness"] == "PRONTO PARA STARTUP" else "risk-amber" if summary["readiness"] == "PRONTO COM CONDICIONANTES" else "risk-red",
            ),
            unsafe_allow_html=True,
        )
        c.markdown(metric_card("Bloqueadores", str(summary["blocker_count"]), "risk-red"), unsafe_allow_html=True)
        d.markdown(metric_card("Ações requeridas", str(summary["action_count"]), "risk-blue"), unsafe_allow_html=True)

        left, right = st.columns(2)
        with left:
            st.markdown("<div class='panel'><h3>Score de prontidão</h3></div>", unsafe_allow_html=True)
            st.pyplot(build_pssr_score_figure(summary), clear_figure=True)

        with right:
            st.markdown("<div class='panel'><h3>Bloqueadores de partida</h3></div>", unsafe_allow_html=True)
            blockers = pssr_result.get("blockers", [])
            if blockers:
                for item in blockers:
                    st.error(item)
            else:
                st.success("Sem bloqueadores centrais de PSSR identificados no checklist atual.")

        st.markdown("<div class='panel'><h3>Checklist PSSR</h3></div>", unsafe_allow_html=True)
        st.dataframe(checklist_df, width="stretch", hide_index=True)

        st.markdown("<div class='panel'><h3>Ações antes da partida</h3></div>", unsafe_allow_html=True)
        if actions_df.empty:
            st.success("Sem ações pendentes registradas no checklist atual.")
        else:
            st.dataframe(actions_df, width="stretch", hide_index=True)


# =========================
# CONSEQUÊNCIAS
# =========================
with consequence_tab:
    dispersion_mode = classify_dispersion_mode(profile)
    st.markdown(
        f"<div class='note-card'><b>Modo sugerido de dispersão:</b> {dispersion_mode['label']}<br>{'; '.join(dispersion_mode['reasons'])}</div>",
        unsafe_allow_html=True,
    )

    for item in profile.routing:
        st.info(item)

    toxic_ok = profile.flags.get("toxic_inhalation", False)
    fire_ok = profile.flags.get("flammable", False)

    tox_tab, fire_tab = st.tabs(["Dispersão tóxica", "Pool fire"])

    with tox_tab:
        if toxic_ok:
            a, b, c = st.columns(3)
            q_g_s = a.number_input("Q (g/s)", value=10.0, min_value=0.001)
            wind = b.number_input("u (m/s)", value=3.0, min_value=0.2)
            stability = c.selectbox("Classe de estabilidade", list("ABCDEF"), index=3)

            d1, d2, d3 = st.columns(3)
            default_idlh = profile.limit("IDLH_ppm", 300.0)
            idlh_ppm = d1.number_input("IDLH (ppm)", value=float(default_idlh or 300.0), min_value=0.001)
            mw = d2.number_input("PM do gás", value=float(profile.identity.get("molecular_weight", 20.0) or 20.0), min_value=1.0)
            h = d3.number_input("Altura da fonte (m)", value=0.0, min_value=0.0)

            if st.button("Rodar dispersão", type="primary"):
                st.session_state.dispersion_result = gaussian_dispersion(q_g_s, wind, stability, idlh_ppm, mw, h)

            if st.session_state.dispersion_result:
                r = st.session_state.dispersion_result
                st.dataframe(
                    pd.DataFrame(
                        [
                            {"Item": "Distância até IDLH", "Valor": f"{r['x_idlh']} m" if r["x_idlh"] else "> 3 km"},
                            {"Item": "Concentração a 100 m", "Valor": f"{r['c_at_100m']:.4f} g/m³"},
                        ]
                    ),
                    width="stretch",
                    hide_index=True,
                )
        else:
            st.info("O perfil do composto não sugere screening tóxico dominante neste momento.")

    with fire_tab:
        if fire_ok:
            a, b, c, d = st.columns(4)
            diameter = a.number_input("Diâmetro da poça (m)", value=5.0, min_value=0.5)
            default_burn = 0.024 if profile.identity["name"].lower().startswith("etanol") else 0.05
            burn = b.number_input('m" (kg/m²·s)', value=float(default_burn), min_value=0.001)
            hc = c.number_input("Hc (kJ/kg)", value=44000.0, min_value=1000.0)
            distance = d.number_input("Distância ao alvo (m)", value=20.0, min_value=1.0)

            if st.button("Rodar pool fire", type="primary"):
                st.session_state.pool_fire_result = pool_fire(diameter, burn, hc, distance)

            if st.session_state.pool_fire_result:
                r = st.session_state.pool_fire_result
                st.dataframe(
                    pd.DataFrame(
                        [
                            {"Item": "Altura da chama", "Valor": f"{r['Hf_m']:.1f} m"},
                            {"Item": "Poder emissivo", "Valor": f"{r['E_kW_m2']:.1f} kW/m²"},
                            {"Item": "Fluxo no alvo", "Valor": f"{r['q_kW_m2']:.2f} kW/m²"},
                            {"Item": "Zona", "Valor": r["zone"]},
                        ]
                    ),
                    width="stretch",
                    hide_index=True,
                )
        else:
            st.info("O perfil do composto não sugere pool fire dominante neste momento.")


# =========================
# RELATÓRIO
# =========================
with report_tab:
    st.markdown("<div class='panel'><h3>Relatório executivo com trilha de evidências</h3></div>", unsafe_allow_html=True)

    report_case_name = st.text_input(
        "Nome do relatório",
        value=st.session_state.current_case_name or profile.identity.get("name", "Caso"),
        key="report_case_name",
    )

    if st.button("Gerar relatório executivo", type="primary"):
        evidence_summary = summarize_evidence(profile)
        evidence_recs = build_source_recommendations(profile)
        psi_df = build_psi_readiness_df(
            profile=profile,
            lopa_result=st.session_state.get("lopa_result"),
            bowtie=bowtie_payload(),
        )
        psi_summary = summarize_psi_readiness(psi_df)

        hazop_priorities_for_report = suggest_hazop_priorities(profile, "Vaso de pressão")

        bundle = build_executive_bundle(
            case_name=report_case_name,
            profile=profile,
            context={
                "evidence_summary": evidence_summary,
                "evidence_recommendations": evidence_recs,
                "hazop_priorities": hazop_priorities_for_report,
                "lopa_result": st.session_state.get("lopa_result"),
                "psi_summary": psi_summary,
                "moc_result": st.session_state.get("moc_result"),
                "pssr_result": st.session_state.get("pssr_result"),
                "reactivity_result": st.session_state.get("reactivity_result"),
            },
        )
        st.session_state.report_bundle = bundle
        st.success("Relatório gerado.")

    report_bundle = st.session_state.get("report_bundle")
    if report_bundle:
        st.download_button(
            "Baixar Markdown",
            report_bundle["markdown"],
            file_name=f"{report_case_name.replace(' ', '_')}_executivo.md",
            mime="text/markdown",
            width="stretch",
        )
        st.download_button(
            "Baixar HTML",
            report_bundle["html"],
            file_name=f"{report_case_name.replace(' ', '_')}_executivo.html",
            mime="text/html",
            width="stretch",
        )

        with st.expander("Pré-visualizar Markdown"):
            st.markdown(report_bundle["markdown"].decode("utf-8"))


# =========================
# REFERÊNCIAS
# =========================
with refs_tab:
    st.markdown("<div class='panel'><h3>Referências do caso</h3></div>", unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(profile.references), width="stretch", hide_index=True)

    st.markdown("<div class='panel'><h3>Rastreabilidade de fonte</h3></div>", unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(profile.source_trace), width="stretch", hide_index=True)

    st.markdown("<div class='panel'><h3>Links oficiais</h3></div>", unsafe_allow_html=True)
    for item in profile.storage.get("official_links", []):
        st.link_button(f"{item['source']} — {item['purpose']}", item["url"], width="stretch")


# =========================
# CASOS
# =========================
with cases_tab:
    st.markdown("<div class='panel'><h3>Salvar e carregar casos</h3></div>", unsafe_allow_html=True)

    c1, c2 = st.columns([2, 3])
    with c1:
        case_name = st.text_input("Nome do caso", value=st.session_state.current_case_name or profile.identity.get("name", "Caso sem nome"))
    with c2:
        case_notes = st.text_area("Notas do caso", value=st.session_state.current_case_notes, height=100)

    col_save, col_load = st.columns([1, 1])

    with col_save:
        if st.button("Salvar caso", type="primary", width="stretch"):
            save_case(
                case_name=case_name,
                profile=profile,
                notes=case_notes,
                lopa_result=st.session_state.get("lopa_result"),
                selected_ipl_names=st.session_state.get("selected_ipl_names", []),
                bowtie=bowtie_payload(),
                moc_result=st.session_state.get("moc_result"),
                pssr_result=st.session_state.get("pssr_result"),
                reactivity_result=st.session_state.get("reactivity_result"),
            )
            st.session_state.current_case_name = case_name
            st.session_state.current_case_notes = case_notes
            st.success("Caso salvo com sucesso.")

    cases = list_cases()
    if cases:
        case_options = [c["case_name"] for c in cases]
        selected_case = col_load.selectbox("Casos disponíveis", case_options)
        if col_load.button("Carregar caso", width="stretch"):
            loaded = load_case(selected_case)
            if loaded:
                apply_loaded_case(loaded)
                st.success("Caso carregado.")
                st.rerun()

        st.markdown("<div class='panel'><h3>Resumo dos casos salvos</h3></div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(cases), width="stretch", hide_index=True)
    else:
        st.info("Nenhum caso salvo ainda.")
