from __future__ import annotations

import re
import streamlit as st


def normalize_whitespace(value):
    if not isinstance(value, str):
        return value
    value = value.replace("\xa0", " ")
    value = value.replace("Â\xa0", " ")
    value = value.replace("Â ", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


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
