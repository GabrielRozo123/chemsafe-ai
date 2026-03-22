from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


LOGIC_VERSION = "sprint1-case-governance-v1"


CASE_STATUS_OPTIONS = [
    "rascunho",
    "em triagem técnica",
    "em revisão multidisciplinar",
    "aprovado para screening",
    "aprovado para budgetary study",
    "não usar para projeto",
    "bloqueado por PSI",
    "bloqueado por proteção insuficiente",
    "pronto para PSSR",
    "pronto para partida",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_case_status(value: str | None) -> str:
    text = (value or "").strip().lower()
    if text in CASE_STATUS_OPTIONS:
        return text
    return "rascunho"


def build_case_header(profile, node_name: str, case_name: str = "", owner: str = "", reviewer: str = "") -> dict[str, Any]:
    return {
        "case_name": (case_name or "").strip() or profile.identity.get("name", "Caso"),
        "compound_name": profile.identity.get("name", "—"),
        "cas": profile.identity.get("cas", "—"),
        "node_name": node_name or "—",
        "owner": owner or "Não definido",
        "reviewer": reviewer or "Não definido",
        "logic_version": LOGIC_VERSION,
        "generated_at": utc_now_iso(),
    }


def infer_case_gate(
    cri_data: dict | None = None,
    psi_summary: dict | None = None,
    gaps_criticos: int = 0,
    moc_result: dict | None = None,
    pssr_result: dict | None = None,
    lopa_result: dict | None = None,
) -> str:
    cri_index = float((cri_data or {}).get("index", 0) or 0)
    psi_gaps = int((psi_summary or {}).get("gap", 0) or 0)
    critical_psi = int((psi_summary or {}).get("critical_gaps", 0) or 0)

    if critical_psi > 0 or psi_gaps >= 4:
        return "Bloqueado por PSI"

    if gaps_criticos > 0:
        return "Bloqueado por proteção insuficiente"

    if lopa_result and float(lopa_result.get("ratio", 0) or 0) > 1.0:
        return "Bloqueado por proteção insuficiente"

    if pssr_result and float(pssr_result.get("summary", {}).get("score", 0) or 0) >= 85:
        return "Pronto para partida"

    if pssr_result and float(pssr_result.get("summary", {}).get("score", 0) or 0) >= 70:
        return "Pronto para PSSR"

    if cri_index >= 80:
        return "Aprovado para budgetary study"

    if cri_index >= 65:
        return "Aprovado para screening"

    if moc_result:
        return "Em revisão multidisciplinar"

    return "Em triagem técnica"


def gate_to_status(gate: str) -> str:
    mapping = {
        "Bloqueado por PSI": "bloqueado por PSI",
        "Bloqueado por proteção insuficiente": "bloqueado por proteção insuficiente",
        "Aprovado para screening": "aprovado para screening",
        "Aprovado para budgetary study": "aprovado para budgetary study",
        "Pronto para PSSR": "pronto para PSSR",
        "Pronto para partida": "pronto para partida",
        "Em revisão multidisciplinar": "em revisão multidisciplinar",
        "Em triagem técnica": "em triagem técnica",
    }
    return mapping.get(gate, "rascunho")


def build_review_event(
    status: str,
    note: str = "",
    actor: str = "",
    gate: str = "",
) -> dict[str, Any]:
    return {
        "timestamp": utc_now_iso(),
        "status": normalize_case_status(status),
        "gate": gate or "—",
        "actor": actor or "sistema",
        "note": (note or "").strip() or "Sem observações adicionais.",
        "logic_version": LOGIC_VERSION,
    }
