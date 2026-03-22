from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path


CASE_DIR = Path(".chemsafe_cases")
CASE_DIR.mkdir(parents=True, exist_ok=True)


def _slug(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9áàâãéêíóôõúç_-]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "caso"


def _case_path(case_name: str) -> Path:
    return CASE_DIR / f"{_slug(case_name)}.json"


def save_case(
    case_name: str,
    profile,
    notes: str = "",
    lopa_result: dict | None = None,
    selected_ipl_names: list[str] | None = None,
    bowtie: dict | None = None,
    moc_result: dict | None = None,
    pssr_result: dict | None = None,
    reactivity_result: dict | None = None,
    current_node_name: str = "",
    case_status: str = "rascunho",
    case_status_note: str = "",
    case_owner: str = "",
    case_reviewer: str = "",
    case_decision_gate: str = "",
    review_history: list[dict] | None = None,
    traceability_rows: list[dict] | None = None,
    psi_summary: dict | None = None,
    case_header: dict | None = None,
):
    payload = {
        "case_name": case_name,
        "saved_at": datetime.utcnow().isoformat() + "Z",
        "compound_name": profile.identity.get("name", ""),
        "query_hint": profile.identity.get("cas") or profile.identity.get("preferred_name") or profile.identity.get("name"),
        "notes": notes,
        "selected_ipl_names": selected_ipl_names or [],
        "lopa_result": lopa_result,
        "bowtie": bowtie or {},
        "moc_result": moc_result,
        "pssr_result": pssr_result,
        "reactivity_result": reactivity_result,
        "routing": profile.routing,
        "confidence_score": profile.confidence_score,
        "current_node_name": current_node_name,
        "case_status": case_status,
        "case_status_note": case_status_note,
        "case_owner": case_owner,
        "case_reviewer": case_reviewer,
        "case_decision_gate": case_decision_gate,
        "review_history": review_history or [],
        "traceability_rows": traceability_rows or [],
        "psi_summary": psi_summary or {},
        "case_header": case_header or {},
    }
    _case_path(case_name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def list_cases() -> list[dict]:
    rows = []
    for path in sorted(CASE_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            rows.append(
                {
                    "case_name": data.get("case_name", path.stem),
                    "compound_name": data.get("compound_name", ""),
                    "saved_at": data.get("saved_at", ""),
                    "confidence_score": data.get("confidence_score", ""),
                    "case_status": data.get("case_status", "rascunho"),
                    "case_decision_gate": data.get("case_decision_gate", ""),
                    "node_name": data.get("current_node_name", ""),
                }
            )
        except Exception:
            continue

    rows.sort(key=lambda x: x.get("saved_at", ""), reverse=True)
    return rows


def load_case(case_name: str) -> dict | None:
    path = _case_path(case_name)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
