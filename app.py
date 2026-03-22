from __future__ import annotations

import importlib
import sys
import traceback
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# =============================================================================
# HELPERS
# =============================================================================
def _safe_import(module_name: str):
    try:
        module = importlib.import_module(module_name)
        return module, None
    except Exception:
        return None, traceback.format_exc()


def _safe_attr(module_name: str, attr_name: str, default=None):
    module, err = _safe_import(module_name)
    if module is None:
        return default, err
    try:
        return getattr(module, attr_name), None
    except Exception:
        return default, traceback.format_exc()


def _render_diag_block(title: str, content: str, level: str = "error") -> None:
    if level == "error":
        st.error(title)
    elif level == "warning":
        st.warning(title)
    else:
        st.info(title)
    with st.expander("Detalhes técnicos", expanded=False):
        st.code(content, language="python")


def _safe_text(value, fallback: str = "—") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


# =============================================================================
# BASE CSS
# =============================================================================
APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

:root {
  --bg-0: #07111e;
  --bg-1: #0b1422;
  --bg-2: #111c2d;
  --card-bg: rgba(17, 28, 45, 0.78);
  --border-color: rgba(148, 163, 184, 0.16);
  --text-main: #e5edf7;
  --text-soft: #9fb0c7;
  --text-faint: #7c8aa0;
  --accent-blue: #60a5fa;
  --accent-green: #34d399;
  --accent-amber: #fbbf24;
  --accent-red: #f87171;
  --accent-violet: #a78bfa;
  --shadow-soft: 0 10px 30px rgba(0, 0, 0, 0.22);
  --radius-xl: 18px;
}

html, body, [class*="css"] {
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
  background: linear-gradient(180deg, rgba(9, 15, 28, 0.98) 0%, rgba(11, 20, 34, 0.98) 100%);
  border-right: 1px solid rgba(148, 163, 184, 0.10);
}

.context-header {
  background: linear-gradient(135deg, rgba(17, 28, 45, 0.92) 0%, rgba(18, 31, 50, 0.88) 100%);
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
}

.panel h3 {
  margin-top: 0;
  color: #f4f8fd;
  font-size: 1.02rem;
  font-weight: 700;
  border-bottom: 1px solid rgba(148,163,184,0.10);
  padding-bottom: 10px;
  margin-bottom: 16px;
}

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

.metric-box {
  background: linear-gradient(180deg, rgba(24, 37, 58, 0.82) 0%, rgba(17, 27, 43, 0.90) 100%);
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 14px;
  padding: 16px 18px;
  text-align: center;
  min-height: 124px;
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
}

.risk-blue { color: #60a5fa; }
.risk-green { color: #34d399; }
.risk-amber { color: #fbbf24; }
.risk-red { color: #f87171; }
.risk-violet { color: #a78bfa; }

.stButton > button,
.stDownloadButton > button {
  border-radius: 12px !important;
  border: 1px solid rgba(96, 165, 250, 0.18) !important;
  background: linear-gradient(180deg, rgba(25, 39, 61, 0.92) 0%, rgba(18, 29, 46, 0.96) 100%) !important;
  color: #edf5ff !important;
  font-weight: 700 !important;
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


# =============================================================================
# IMPORTS SEGUROS
# =============================================================================
import_errors: dict[str, str] = {}

app_bootstrap_mod, err = _safe_import("app_bootstrap")
if err:
    import_errors["app_bootstrap"] = err

app_runtime_mod, err = _safe_import("app_runtime")
if err:
    import_errors["app_runtime"] = err

reference_data_mod, err = _safe_import("reference_data")
if err:
    import_errors["reference_data"] = err

chemicals_seed_mod, err = _safe_import("chemicals_seed")
if err:
    import_errors["chemicals_seed"] = err

case_domain_mod, err = _safe_import("case_domain")
if err:
    import_errors["case_domain"] = err

ui_components_mod, err = _safe_import("ui_components")
if err:
    import_errors["ui_components"] = err

# Se bootstrap falhar, ainda assim o app mostra algo
if app_bootstrap_mod is not None:
    MENU_STYLES = getattr(app_bootstrap_mod, "MENU_STYLES", {})
    initialize_session_state = getattr(app_bootstrap_mod, "initialize_session_state", lambda: None)
else:
    MENU_STYLES = {}
    initialize_session_state = lambda: None  # noqa: E731

initialize_session_state()

# Blindagem extra
defaults = {
    "lang": "pt",
    "selected_compound_key": "ammonia",
    "profile": None,
    "lopa_result": None,
    "pid_hazop_matrix": [],
    "current_node_name": "Nó 101: Bomba de Recalque",
    "current_case_name": "",
    "audit_mode": True,
    "psv_result": None,
    "psv_inputs": None,
    "tmr_result": None,
    "tmr_inputs": None,
    "moc_result": None,
    "pssr_result": None,
    "reactivity_result": None,
    "psi_summary": None,
    "case_status": "rascunho",
    "case_status_note": "",
    "case_owner": "",
    "case_reviewer": "",
    "case_decision_gate": "",
    "review_history": [],
    "traceability_rows": [],
    "report_bundle": None,
}
for key, value in defaults.items():
    st.session_state.setdefault(key, value)

# Helpers importados com fallback
LOCAL_COMPOUNDS = getattr(chemicals_seed_mod, "LOCAL_COMPOUNDS", {}) if chemicals_seed_mod else {}
NORMS_DB = getattr(reference_data_mod, "NORMS_DB", []) if reference_data_mod else []
MODULE_GOVERNANCE = getattr(reference_data_mod, "MODULE_GOVERNANCE", {}) if reference_data_mod else {}

load_profile_with_feedback = getattr(app_runtime_mod, "load_profile_with_feedback", None) if app_runtime_mod else None
load_profile_from_key = getattr(app_runtime_mod, "load_profile_from_key", None) if app_runtime_mod else None
bowtie_payload = getattr(app_runtime_mod, "bowtie_payload", None) if app_runtime_mod else None
apply_loaded_case = getattr(app_runtime_mod, "apply_loaded_case", None) if app_runtime_mod else None

build_case_header = getattr(case_domain_mod, "build_case_header", None) if case_domain_mod else None
gate_to_status = getattr(case_domain_mod, "gate_to_status", None) if case_domain_mod else None
infer_case_gate = getattr(case_domain_mod, "infer_case_gate", None) if case_domain_mod else None

render_trust_ribbon = getattr(ui_components_mod, "render_trust_ribbon", None) if ui_components_mod else None


# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("## ⚗️ ChemSafe Pro Enterprise")
    st.caption("Process Safety Intelligence Engine")

    st.session_state.lang = st.radio(
        "Idioma",
        ["pt", "en"],
        horizontal=True,
        label_visibility="collapsed",
        index=0 if st.session_state.get("lang", "pt") == "pt" else 1,
    )

    st.session_state.audit_mode = st.toggle(
        "Modo Auditoria / Evidências",
        value=st.session_state.get("audit_mode", True),
    )

    st.markdown("---")

    selected_module = st.radio(
        "Módulo",
        ["Visão Executiva", "Engenharia", "Análise de Risco", "Mudanças", "Base de Conhecimento"],
        index=0,
    )

    st.markdown("---")
    st.write("**Acesso rápido**")

    if LOCAL_COMPOUNDS and load_profile_from_key:
        for key, data in LOCAL_COMPOUNDS.items():
            if st.button(data["identity"]["name"], key=f"quick_{key}", use_container_width=True):
                try:
                    load_profile_from_key(key)
                    st.rerun()
                except Exception:
                    _render_diag_block("Falha ao carregar composto rápido.", traceback.format_exc())
    else:
        st.caption("Quick access indisponível no momento.")

    st.markdown("---")
    manual_query = st.text_input("Buscar CAS ou Nome")

    if st.button("Carregar Composto", use_container_width=True):
        if not load_profile_with_feedback:
            st.error("Função de carregamento de perfil indisponível.")
        elif not manual_query.strip():
            st.warning("Digite um CAS ou nome de composto.")
        else:
            try:
                st.session_state.profile = load_profile_with_feedback(manual_query.strip())
                st.rerun()
            except Exception:
                _render_diag_block("Falha ao carregar composto manualmente.", traceback.format_exc())

    if import_errors:
        with st.expander("Diagnóstico de imports", expanded=False):
            for mod_name, err_text in import_errors.items():
                st.markdown(f"**{mod_name}**")
                st.code(err_text, language="python")


# =============================================================================
# ESTADO INICIAL
# =============================================================================
profile = st.session_state.get("profile")

if profile is None:
    st.markdown(
        """
        <div class="panel">
            <h3>Inicialização segura do app</h3>
            <div class="note-card">
                O app iniciou sem autocarregar o composto. Isso foi feito para evitar travamentos
                na largada do Streamlit Cloud. Carregue um composto manualmente pela sidebar ou clique
                no botão abaixo para iniciar com a amônia.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1, 1.4])

    with c1:
        if st.button("Carregar composto padrão (amônia)", type="primary", use_container_width=True):
            if not load_profile_from_key:
                st.error("Função de carregamento padrão indisponível.")
            else:
                try:
                    with st.spinner("Carregando perfil padrão..."):
                        load_profile_from_key(st.session_state.get("selected_compound_key", "ammonia"))
                    st.rerun()
                except Exception:
                    _render_diag_block("Falha ao carregar o composto padrão.", traceback.format_exc())

    with c2:
        st.info("Você também pode usar os botões de acesso rápido ou buscar por CAS/nome na sidebar.")

    st.stop()


# =============================================================================
# HEADER DO CASO
# =============================================================================
if build_case_header:
    try:
        case_header = build_case_header(
            profile=profile,
            node_name=st.session_state.get("current_node_name", "—"),
            case_name=st.session_state.get("current_case_name", ""),
            owner=st.session_state.get("case_owner", ""),
            reviewer=st.session_state.get("case_reviewer", ""),
        )
    except Exception:
        case_header = {
            "case_name": st.session_state.get("current_case_name", "") or profile.identity.get("name", "Caso"),
            "compound_name": profile.identity.get("name", "—"),
            "cas": profile.identity.get("cas", "—"),
        }
        _render_diag_block("Falha ao montar cabeçalho do caso.", traceback.format_exc(), level="warning")
else:
    case_header = {
        "case_name": st.session_state.get("current_case_name", "") or profile.identity.get("name", "Caso"),
        "compound_name": profile.identity.get("name", "—"),
        "cas": profile.identity.get("cas", "—"),
    }

st.markdown(
    f"""
<div class="context-header">
    <div>🧪 Ativo Analisado: <span>{profile.identity.get('name', 'N/A')} (CAS: {profile.identity.get('cas', 'N/A')})</span></div>
    <div>🏭 Topologia Foco: <span>{st.session_state.get('current_node_name', '—')}</span></div>
    <div>📂 Caso: <span>{case_header.get('case_name', 'Caso')}</span></div>
</div>
""",
    unsafe_allow_html=True,
)

if st.session_state.get("audit_mode", True) and render_trust_ribbon:
    gov = MODULE_GOVERNANCE.get(
        selected_module,
        {"basis": "Base técnica curada.", "refs": [], "confidence": "Média"},
    )
    try:
        render_trust_ribbon(
            module_name=selected_module,
            basis=gov["basis"],
            refs=gov["refs"],
            confidence=gov["confidence"],
        )
    except Exception:
        _render_diag_block("Falha ao renderizar trust ribbon.", traceback.format_exc(), level="warning")


# =============================================================================
# IMPORTS DE MOTORES
# =============================================================================
build_psi_readiness_df, err = _safe_attr("psi_readiness", "build_psi_readiness_df")
if err:
    import_errors["psi_readiness.build_psi_readiness_df"] = err

summarize_psi_readiness, err = _safe_attr("psi_readiness", "summarize_psi_readiness")
if err:
    import_errors["psi_readiness.summarize_psi_readiness"] = err

calculate_case_readiness_index, err = _safe_attr("dashboard_engine", "calculate_case_readiness_index")
if err:
    import_errors["dashboard_engine.calculate_case_readiness_index"] = err

build_consolidated_action_plan, err = _safe_attr("action_hub", "build_consolidated_action_plan")
if err:
    import_errors["action_hub.build_consolidated_action_plan"] = err

enrich_action_plan_df, err = _safe_attr("action_processing", "enrich_action_plan_df")
if err:
    import_errors["action_processing.enrich_action_plan_df"] = err

get_action_col, err = _safe_attr("action_processing", "get_action_col")
if err:
    import_errors["action_processing.get_action_col"] = err

build_traceability_matrix, err = _safe_attr("traceability_engine", "build_traceability_matrix")
if err:
    import_errors["traceability_engine.build_traceability_matrix"] = err

chart_utils_mod, err = _safe_import("chart_utils")
if err:
    import_errors["chart_utils"] = err

if import_errors and (
    build_psi_readiness_df is None
    or summarize_psi_readiness is None
    or calculate_case_readiness_index is None
    or build_consolidated_action_plan is None
    or enrich_action_plan_df is None
    or get_action_col is None
    or build_traceability_matrix is None
    or chart_utils_mod is None
):
    st.markdown("<div class='panel'><h3>Diagnóstico do app</h3></div>", unsafe_allow_html=True)
    st.error("O app iniciou, mas um ou mais motores essenciais falharam no import.")
    with st.expander("Ver detalhes técnicos", expanded=True):
        for mod_name, err_text in import_errors.items():
            st.markdown(f"**{mod_name}**")
            st.code(err_text, language="python")
    st.stop()

is_valid_df = getattr(chart_utils_mod, "is_valid_df")
safe_float = getattr(chart_utils_mod, "safe_float")
render_modern_gauge = getattr(chart_utils_mod, "render_modern_gauge")
render_modern_radar = getattr(chart_utils_mod, "render_modern_radar")
render_action_donut = getattr(chart_utils_mod, "render_action_donut")
render_action_bar = getattr(chart_utils_mod, "render_action_bar")
render_flammability_envelope = getattr(chart_utils_mod, "render_flammability_envelope")


# =============================================================================
# PIPELINE DO CASO
# =============================================================================
try:
    psi_df_dash = build_psi_readiness_df(
        profile,
        st.session_state.get("lopa_result"),
        bowtie_payload() if bowtie_payload else {},
    )
    psi_summary_dash = summarize_psi_readiness(psi_df_dash)
    st.session_state.psi_summary = psi_summary_dash

    cri_data = calculate_case_readiness_index(
        profile,
        psi_summary_dash,
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

    traceability_df = build_traceability_matrix(
        profile=profile,
        psi_df=psi_df_dash,
        psi_summary=psi_summary_dash,
        cri_data=cri_data,
        lopa_result=st.session_state.get("lopa_result"),
        moc_result=st.session_state.get("moc_result"),
        pssr_result=st.session_state.get("pssr_result"),
        reactivity_result=st.session_state.get("reactivity_result"),
    )
    st.session_state.traceability_rows = (
        traceability_df.to_dict(orient="records") if not traceability_df.empty else []
    )

    if infer_case_gate:
        st.session_state.case_decision_gate = st.session_state.get("case_decision_gate") or infer_case_gate(
            cri_data=cri_data,
            psi_summary=psi_summary_dash,
            gaps_criticos=int(psi_summary_dash.get("critical_gaps", 0)),
            moc_result=st.session_state.get("moc_result"),
            pssr_result=st.session_state.get("pssr_result"),
            lopa_result=st.session_state.get("lopa_result"),
        )

    if (
        gate_to_status
        and st.session_state.get("case_status", "rascunho") == "rascunho"
        and st.session_state.get("case_decision_gate")
    ):
        st.session_state.case_status = gate_to_status(st.session_state.get("case_decision_gate"))

    has_actions = is_valid_df(action_df_dash)
    num_acoes_pendentes = len(action_df_dash) if has_actions else 0
    gaps_criticos = int(psi_summary_dash.get("critical_gaps", 0))

except Exception:
    _render_diag_block("Falha na pipeline principal do caso.", traceback.format_exc())
    st.stop()


# =============================================================================
# RENDER DOS MÓDULOS
# =============================================================================
def _import_view_fn(module_name: str, fn_name: str):
    module, err_local = _safe_import(module_name)
    if err_local:
        _render_diag_block(f"Falha ao importar {module_name}.", err_local)
        return None
    try:
        return getattr(module, fn_name)
    except Exception:
        _render_diag_block(f"Falha ao localizar {fn_name} em {module_name}.", traceback.format_exc())
        return None


if selected_module == "Visão Executiva":
    render_executive_module = _import_view_fn("views_executive", "render_executive_module")
    if render_executive_module:
        try:
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
                psi_df_dash=psi_df_dash,
                psi_summary=psi_summary_dash,
                traceability_df=traceability_df,
            )
        except Exception:
            _render_diag_block("Falha ao renderizar o módulo executivo.", traceback.format_exc())

elif selected_module == "Engenharia":
    render_engineering_module = _import_view_fn("views_engineering", "render_engineering_module")
    if render_engineering_module:
        try:
            render_engineering_module(
                profile=profile,
                menu_styles=MENU_STYLES,
                safe_float_fn=safe_float,
                render_flammability_envelope_fn=render_flammability_envelope,
            )
        except Exception:
            _render_diag_block("Falha ao renderizar o módulo de engenharia.", traceback.format_exc())

elif selected_module == "Análise de Risco":
    render_risk_module = _import_view_fn("views_risk", "render_risk_module")
    if render_risk_module:
        try:
            render_risk_module(
                profile=profile,
                menu_styles=MENU_STYLES,
                is_valid_df_fn=is_valid_df,
            )
        except Exception:
            _render_diag_block("Falha ao renderizar o módulo de risco.", traceback.format_exc())

elif selected_module == "Mudanças":
    render_change_module = _import_view_fn("views_change", "render_change_module")
    if render_change_module:
        try:
            render_change_module(
                profile=profile,
                menu_styles=MENU_STYLES,
            )
        except Exception:
            _render_diag_block("Falha ao renderizar o módulo de mudanças.", traceback.format_exc())

elif selected_module == "Base de Conhecimento":
    render_knowledge_module = _import_view_fn("views_knowledge", "render_knowledge_module")
    if render_knowledge_module:
        try:
            render_knowledge_module(
                profile=profile,
                menu_styles=MENU_STYLES,
                norms_db=NORMS_DB,
            )
        except Exception:
            _render_diag_block("Falha ao renderizar a base de conhecimento.", traceback.format_exc())
