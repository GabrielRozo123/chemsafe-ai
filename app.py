from __future__ import annotations
from bowtie_visual import build_bowtie_figure
from dense_gas_router import classify_dispersion_mode
from risk_register import build_risk_register
from ui_formatters import format_identity_df, format_physchem_df, format_limits_df

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st

from chemicals_seed import LOCAL_COMPOUNDS
from compound_engine import (
    build_compound_profile,
    suggest_hazop_priorities,
    suggest_lopa_ipls,
)
from deterministic import IPL_CATALOG, compute_lopa, gaussian_dispersion, pool_fire
from hazop_db import HAZOP_DB
from risk_visuals import (
    build_confidence_figure,
    build_hazard_fingerprint_figure,
    build_incompatibility_matrix_figure,
    build_ipl_layers_figure,
    build_risk_matrix_figure,
    build_source_coverage_figure,
)

APP_CSS = """
<style>
.stApp {
    background: linear-gradient(180deg, #07111f, #081a31);
    color: #e9f1ff;
}
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}
.hero {
    background: linear-gradient(135deg, #0d2345, #0b1830);
    border: 1px solid #1c3f78;
    border-radius: 18px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
}
.hero h1 {
    margin: 0 0 0.35rem 0;
    color: #f4f8ff;
}
.hero p {
    margin: 0;
    color: #9fc1ff;
}
.badge {
    display: inline-block;
    margin: 0.35rem 0.35rem 0 0;
    padding: 0.22rem 0.55rem;
    border-radius: 999px;
    border: 1px solid #2b5aa1;
    color: #cfe1ff;
    font-size: 0.78rem;
}
.metric-box {
    background: rgba(10,22,42,0.95);
    border: 1px solid #1d365f;
    border-radius: 16px;
    padding: 1rem;
    min-height: 112px;
}
.metric-label {
    color: #7ea8ea;
    font-size: 0.78rem;
    text-transform: uppercase;
}
.metric-value {
    color: white;
    font-size: 1.55rem;
    font-weight: 700;
    margin-top: 0.45rem;
}
.risk-blue { color: #62a8ff; }
.risk-green { color: #34d399; }
.risk-amber { color: #fbbf24; }
.risk-red { color: #fb7185; }

.panel {
    background: rgba(9,17,31,0.92);
    border: 1px solid #1d365f;
    border-radius: 16px;
    padding: 1rem;
    margin-bottom: 0.8rem;
}
.panel h3 {
    margin-top: 0;
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
}
.source-card {
    background: rgba(12, 24, 43, 0.95);
    border: 1px solid #21416e;
    border-radius: 14px;
    padding: 0.9rem;
    height: 100%;
}
.section-title {
    font-size: 1.02rem;
    font-weight: 700;
    color: #d9e8ff;
    margin-bottom: 0.45rem;
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

if "selected_compound_key" not in st.session_state:
    st.session_state.selected_compound_key = "ammonia"
if "profile" not in st.session_state:
    st.session_state.profile = None
if "lopa_result" not in st.session_state:
    st.session_state.lopa_result = None
if "dispersion_result" not in st.session_state:
    st.session_state.dispersion_result = None
if "pool_fire_result" not in st.session_state:
    st.session_state.pool_fire_result = None
if "selected_ipl_names" not in st.session_state:
    st.session_state.selected_ipl_names = []


def metric_card(label: str, value: str, klass: str = "risk-blue") -> str:
    return f"<div class='metric-box'><div class='metric-label'>{label}</div><div class='metric-value {klass}'>{value}</div></div>"


def quick_compounds():
    return {k: v["identity"]["name"] for k, v in LOCAL_COMPOUNDS.items()}


def load_profile_from_key(key: str) -> None:
    aliases = LOCAL_COMPOUNDS[key]["aliases"]
    profile = build_compound_profile(aliases[0])
    st.session_state.selected_compound_key = key
    st.session_state.profile = profile


with st.sidebar:
    st.markdown("## ⚗️ ChemSafe Pro Deterministic")
    st.caption("Property-aware process safety screening")
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
                st.warning("Composto não encontrado nem na base local nem no fallback do PubChem.")
            else:
                st.session_state.profile = profile

    st.markdown("---")
    st.write("**Meta do produto**")
    st.caption("Perfil canônico → HAZOP → LOPA → Consequências → Referências")

if st.session_state.profile is None:
    load_profile_from_key(st.session_state.selected_compound_key)

profile = st.session_state.profile

st.markdown(
    """
    <div class="hero">
      <h1>ChemSafe Pro Deterministic</h1>
      <p>Segurança de processo guiada por propriedades reais, referências oficiais e lógica de decisão transparente.</p>
      <div>
        <span class="badge">compound profile</span>
        <span class="badge">hazard fingerprint</span>
        <span class="badge">risk matrix</span>
        <span class="badge">IPL stack</span>
        <span class="badge">incompatibility matrix</span>
        <span class="badge">confidence score</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

overview_tab, compound_tab, hazop_tab, bowtie_tab, lopa_tab, consequence_tab, refs_tab = st.tabs(
    ["Overview", "Composto", "HAZOP", "Bow-Tie", "LOPA", "Consequências", "Referências"]
)
dispersion_mode = classify_dispersion_mode(profile)
with overview_tab:
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
    a, b = st.columns(2)
    with a:
        st.markdown("<div class='panel'><h3>Hazard fingerprint</h3></div>", unsafe_allow_html=True)
        st.pyplot(build_hazard_fingerprint_figure(profile), width="stretch")
    with b:
        st.markdown("<div class='panel'><h3>Confiança do pacote de dados</h3></div>", unsafe_allow_html=True)
        st.pyplot(build_confidence_figure(profile), width="stretch")

    a, b = st.columns(2)
    with a:
        st.markdown("<div class='panel'><h3>Cobertura de fontes</h3></div>", unsafe_allow_html=True)
        st.pyplot(build_source_coverage_figure(profile), width="stretch")
    with b:
        st.markdown("<div class='panel'><h3>Readiness para screening</h3></div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(profile.readiness), width="stretch", hide_index=True)

    st.markdown("<div class='panel'><h3>Roteamento automático</h3></div>", unsafe_allow_html=True)
    if profile.routing:
        for item in profile.routing:
            st.success(item)
    else:
        st.info("Nenhuma rota dominante identificada.")

    if profile.validation_gaps:
        st.markdown("<div class='panel'><h3>Lacunas de dados</h3></div>", unsafe_allow_html=True)
        for gap in profile.validation_gaps:
            st.warning(gap)

with compound_tab:
    left, right = st.columns(2)

    with left:
        st.markdown("<div class='panel'><h3>Identidade e descritores</h3></div>", unsafe_allow_html=True)
        identity_rows = []
        for key, value in profile.identity.items():
            if value not in [None, ""]:
                identity_rows.append({"field": key, "value": value})
        st.dataframe(pd.DataFrame(identity_rows), width="stretch", hide_index=True)

        st.markdown("<div class='panel'><h3>Perigos / GHS</h3></div>", unsafe_allow_html=True)
        if profile.hazards:
            for hz in profile.hazards:
                st.error(hz)
        else:
            st.info("Sem hazards locais cadastrados para este composto.")

        st.markdown("<div class='panel'><h3>NFPA</h3></div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([profile.nfpa]), width="stretch", hide_index=True)

    with right:
        st.markdown("<div class='panel'><h3>Propriedades físico-químicas</h3></div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(profile.to_flat_physchem()), width="stretch", hide_index=True)

        st.markdown("<div class='panel'><h3>Limites de exposição</h3></div>", unsafe_allow_html=True)
        limits = profile.to_flat_limits()
        if limits:
            st.dataframe(pd.DataFrame(limits), width="stretch", hide_index=True)
        else:
            st.info("Sem limites locais cadastrados para este composto.")

        st.markdown("<div class='panel'><h3>Incompatibilidades / armazenamento</h3></div>", unsafe_allow_html=True)
        incompat = profile.storage.get("incompatibilities", [])
        notes = profile.storage.get("notes", [])
        if incompat:
            for item in incompat:
                st.warning(item)
        else:
            st.info("Sem incompatibilidades locais estruturadas.")
        if notes:
            for item in notes:
                st.info(item)

    st.markdown("<div class='panel'><h3>Matriz de incompatibilidade</h3></div>", unsafe_allow_html=True)
    st.pyplot(build_incompatibility_matrix_figure(profile), width="stretch")

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

    st.markdown("<div class='panel'><h3>Prioridades de HAZOP orientadas pelo composto</h3></div>", unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(priorities), width="stretch", hide_index=True)

    st.markdown("<div class='panel'><h3>Risk matrix dos focos priorizados</h3></div>", unsafe_allow_html=True)
    st.pyplot(build_risk_matrix_figure(priorities), width="stretch")

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
                    "desvio": f"{guideword} {param}" if i == 0 else "idem",
                    "causa": cause,
                    "consequência": cons[i] if i < len(cons) else (cons[0] if cons else "—"),
                    "salvaguarda": sav[i] if i < len(sav) else (sav[0] if sav else "—"),
                    "recomendação": rec[i] if i < len(rec) else (rec[0] if rec else "—"),
                }
            )
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    st.markdown(
        "<div class='note-card'>Nesta versão, o HAZOP deixa de ser apenas uma checklist: o composto altera o peso relativo de ignição, toxic release, sobrepressão, corrosão e incompatibilidade.</div>",
        unsafe_allow_html=True,
    )

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

        st.markdown("<div class='panel'><h3>IPL stack</h3></div>", unsafe_allow_html=True)
        selected_names = st.session_state.get("selected_ipl_names", [])
        st.pyplot(build_ipl_layers_figure(selected_names, suggested_ipls), width="stretch")

with consequence_tab:
    st.markdown("<div class='panel'><h3>Roteamento de consequências</h3></div>", unsafe_allow_html=True)
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
            idlh_ppm = d1.number_input("IDLH (ppm)", value=float(default_idlh), min_value=0.001)
            mw = d2.number_input("PM do gás", value=float(profile.identity.get("molecular_weight", 20.0) or 20.0), min_value=1.0)
            h = d3.number_input("Altura da fonte (m)", value=0.0, min_value=0.0)

            if st.button("Rodar dispersão", type="primary"):
                st.session_state.dispersion_result = gaussian_dispersion(q_g_s, wind, stability, idlh_ppm, mw, h)

            if st.session_state.dispersion_result:
                r = st.session_state.dispersion_result
                st.dataframe(
                    pd.DataFrame(
                        [
                            {"item": "Distância até IDLH", "value": f"{r['x_idlh']} m" if r["x_idlh"] else "> 3 km"},
                            {"item": "Concentração @100 m", "value": f"{r['c_at_100m']:.4f} g/m³"},
                        ]
                    ),
                    width="stretch",
                    hide_index=True,
                )
        else:
            st.info("O perfil do composto não sugere toxic screening dominante neste momento.")

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
                            {"item": "Altura da chama", "value": f"{r['Hf_m']:.1f} m"},
                            {"item": "Poder emissivo", "value": f"{r['E_kW_m2']:.1f} kW/m²"},
                            {"item": "Fluxo no alvo", "value": f"{r['q_kW_m2']:.2f} kW/m²"},
                            {"item": "Zona", "value": r["zone"]},
                        ]
                    ),
                    width="stretch",
                    hide_index=True,
                )
        else:
            st.info("O perfil do composto não sugere pool fire dominante neste momento.")

with refs_tab:
    st.markdown("<div class='panel'><h3>Referências do caso</h3></div>", unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(profile.references), width="stretch", hide_index=True)

    st.markdown("<div class='panel'><h3>Rastreabilidade de fonte</h3></div>", unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(profile.source_trace), width="stretch", hide_index=True)

    st.markdown("<div class='panel'><h3>Links oficiais</h3></div>", unsafe_allow_html=True)
    for item in profile.storage.get("official_links", []):
        st.link_button(f"{item['source']} — {item['purpose']}", item["url"], width="stretch")
