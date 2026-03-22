from __future__ import annotations

from typing import Any

import pandas as pd

from case_domain import LOGIC_VERSION, utc_now_iso


def _safe(value: Any, fallback: str = "—") -> str:
    if value in [None, "", [], {}]:
        return fallback
    return str(value)


def _origin_from_confidence(confidence: str) -> str:
    mapping = {
        "seed": "local_seed",
        "live": "live_lookup",
        "manual": "manual_override",
        "inferred": "inferred",
    }
    return mapping.get((confidence or "").lower(), "derived")


def build_traceability_matrix(
    profile,
    psi_df: pd.DataFrame | None = None,
    psi_summary: dict | None = None,
    cri_data: dict | None = None,
    lopa_result: dict | None = None,
    moc_result: dict | None = None,
    pssr_result: dict | None = None,
    reactivity_result: dict | None = None,
) -> pd.DataFrame:
    ts = utc_now_iso()
    rows: list[dict[str, Any]] = []

    identity_fields = [
        ("identity.name", profile.identity.get("name"), "Compound Engine", "live_lookup"),
        ("identity.cas", profile.identity.get("cas"), "Compound Engine", "live_lookup"),
        ("identity.formula", profile.identity.get("formula"), "Compound Engine", "live_lookup"),
        ("identity.molecular_weight", profile.identity.get("molecular_weight"), "Compound Engine", "live_lookup"),
    ]
    for field, value, module, origin in identity_fields:
        rows.append(
            {
                "Campo / cálculo": field,
                "Valor": _safe(value),
                "Módulo": module,
                "Fonte primária": "profile.identity",
                "Origem do dado": origin,
                "Confiança": f"{getattr(profile, 'confidence_score', 0):.1f}/100",
                "Versão da lógica": LOGIC_VERSION,
                "Calculado em": ts,
                "Impacto decisório": "Base mínima para identificação e screening",
            }
        )

    for key, item in getattr(profile, "physchem", {}).items():
        rows.append(
            {
                "Campo / cálculo": f"physchem.{key}",
                "Valor": _safe(getattr(item, "value", None)),
                "Módulo": "Compound Engine",
                "Fonte primária": _safe(getattr(item, "source", ""), "não informado"),
                "Origem do dado": _origin_from_confidence(getattr(item, "confidence", "")),
                "Confiança": getattr(item, "confidence", "seed"),
                "Versão da lógica": LOGIC_VERSION,
                "Calculado em": ts,
                "Impacto decisório": "Entrada para hazard fingerprint, PSI e screening técnico",
            }
        )

    for key, item in getattr(profile, "exposure_limits", {}).items():
        rows.append(
            {
                "Campo / cálculo": f"exposure_limits.{key}",
                "Valor": _safe(getattr(item, "value", None)),
                "Módulo": "Compound Engine",
                "Fonte primária": _safe(getattr(item, "source", ""), "não informado"),
                "Origem do dado": _origin_from_confidence(getattr(item, "confidence", "")),
                "Confiança": getattr(item, "confidence", "seed"),
                "Versão da lógica": LOGIC_VERSION,
                "Calculado em": ts,
                "Impacto decisório": "Base para toxicidade, evacuação e critérios de exposição",
            }
        )

    if psi_df is not None and not psi_df.empty:
        for _, row in psi_df.iterrows():
            rows.append(
                {
                    "Campo / cálculo": f"psi::{row.get('Item', 'item')}",
                    "Valor": row.get("Status", "—"),
                    "Módulo": "PSI Readiness 2.0",
                    "Fonte primária": row.get("Hint de fonte", "biblioteca interna"),
                    "Origem do dado": row.get("Tipo de evidência", "derived"),
                    "Confiança": row.get("Severidade do gap", "—"),
                    "Versão da lógica": LOGIC_VERSION,
                    "Calculado em": ts,
                    "Impacto decisório": row.get("Decisão bloqueada", "apoio ao screening"),
                }
            )

    if psi_summary:
        rows.append(
            {
                "Campo / cálculo": "psi.summary.score",
                "Valor": f"{float(psi_summary.get('score', 0) or 0):.1f}",
                "Módulo": "PSI Readiness 2.0",
                "Fonte primária": "summarize_psi_readiness",
                "Origem do dado": "derived",
                "Confiança": f"{int(psi_summary.get('critical_gaps', 0) or 0)} gaps críticos",
                "Versão da lógica": LOGIC_VERSION,
                "Calculado em": ts,
                "Impacto decisório": "Determina bloqueio de PSI e prontidão do caso",
            }
        )

    if cri_data:
        rows.append(
            {
                "Campo / cálculo": "executive.cri",
                "Valor": f"{float(cri_data.get('index', 0) or 0):.1f}",
                "Módulo": "Dashboard Engine",
                "Fonte primária": "calculate_case_readiness_index",
                "Origem do dado": "derived",
                "Confiança": cri_data.get("band", "—"),
                "Versão da lógica": LOGIC_VERSION,
                "Calculado em": ts,
                "Impacto decisório": "Gate executivo e priorização gerencial",
            }
        )

    if lopa_result:
        rows.append(
            {
                "Campo / cálculo": "lopa.ratio",
                "Valor": _safe(round(float(lopa_result.get("ratio", 0) or 0), 2)),
                "Módulo": "LOPA",
                "Fonte primária": "session_state.lopa_result",
                "Origem do dado": "derived",
                "Confiança": _safe(lopa_result.get("sil"), "screening"),
                "Versão da lógica": LOGIC_VERSION,
                "Calculado em": ts,
                "Impacto decisório": "Gate de proteção suficiente / insuficiente",
            }
        )

    if moc_result:
        rows.append(
            {
                "Campo / cálculo": "moc.summary.score",
                "Valor": _safe(moc_result.get("summary", {}).get("score")),
                "Módulo": "MOC",
                "Fonte primária": "session_state.moc_result",
                "Origem do dado": "derived",
                "Confiança": _safe(moc_result.get("summary", {}).get("category")),
                "Versão da lógica": LOGIC_VERSION,
                "Calculado em": ts,
                "Impacto decisório": "Necessidade de revisão multidisciplinar",
            }
        )

    if pssr_result:
        rows.append(
            {
                "Campo / cálculo": "pssr.summary.score",
                "Valor": _safe(pssr_result.get("summary", {}).get("score")),
                "Módulo": "PSSR",
                "Fonte primária": "session_state.pssr_result",
                "Origem do dado": "derived",
                "Confiança": _safe(pssr_result.get("summary", {}).get("readiness")),
                "Versão da lógica": LOGIC_VERSION,
                "Calculado em": ts,
                "Impacto decisório": "Liberação para partida / readiness operacional",
            }
        )

    if reactivity_result:
        rows.append(
            {
                "Campo / cálculo": "reactivity.summary.score",
                "Valor": _safe(reactivity_result.get("summary", {}).get("score")),
                "Módulo": "Reatividade",
                "Fonte primária": "session_state.reactivity_result",
                "Origem do dado": "derived",
                "Confiança": _safe(reactivity_result.get("summary", {}).get("severity")),
                "Versão da lógica": LOGIC_VERSION,
                "Calculado em": ts,
                "Impacto decisório": "Compatibilidade de materiais e segregação operacional",
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(
            columns=[
                "Campo / cálculo",
                "Valor",
                "Módulo",
                "Fonte primária",
                "Origem do dado",
                "Confiança",
                "Versão da lógica",
                "Calculado em",
                "Impacto decisório",
            ]
        )

    return df.drop_duplicates(subset=["Campo / cálculo", "Valor", "Módulo"]).reset_index(drop=True)
