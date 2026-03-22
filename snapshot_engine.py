from __future__ import annotations

from html import escape
from typing import Any

import pandas as pd

from case_domain import utc_now_iso


def _safe(value: Any, fallback: str = "—") -> str:
    if value in [None, "", [], {}]:
        return fallback
    return str(value)


def _table_from_df(df: pd.DataFrame | None, limit: int = 25) -> str:
    if df is None or getattr(df, "empty", True):
        return "<p>—</p>"
    use_df = df.head(limit).copy()
    return use_df.to_html(index=False, border=0, classes="data-table")


def build_case_snapshot_payload(
    case_header: dict,
    profile,
    psi_summary: dict,
    cri_data: dict,
    case_status: str,
    case_gate: str,
    status_note: str,
    review_history: list[dict] | None = None,
    traceability_df: pd.DataFrame | None = None,
    action_df = None,
) -> dict[str, Any]:
    return {
        "snapshot_generated_at": utc_now_iso(),
        "case_header": case_header,
        "workflow": {
            "status": case_status,
            "gate": case_gate,
            "status_note": status_note or "",
            "review_history": review_history or [],
        },
        "compound": {
            "name": profile.identity.get("name"),
            "cas": profile.identity.get("cas"),
            "formula": profile.identity.get("formula"),
            "molecular_weight": profile.identity.get("molecular_weight"),
            "confidence_score": getattr(profile, "confidence_score", 0),
            "routing": getattr(profile, "routing", []),
            "validation_gaps": getattr(profile, "validation_gaps", []),
        },
        "executive": {
            "cri_index": cri_data.get("index", 0),
            "cri_band": cri_data.get("band", "—"),
            "psi_score": psi_summary.get("score", 0),
            "psi_gaps": psi_summary.get("gap", 0),
            "psi_critical_gaps": psi_summary.get("critical_gaps", 0),
            "blocked_decisions": psi_summary.get("blocked_decisions", []),
        },
        "traceability_rows": [] if traceability_df is None else traceability_df.to_dict(orient="records"),
        "action_rows": [] if action_df is None or getattr(action_df, "empty", True) else action_df.to_dict(orient="records"),
    }


def build_case_snapshot_html(
    payload: dict[str, Any],
    traceability_df: pd.DataFrame | None = None,
    action_df = None,
) -> bytes:
    header = payload.get("case_header", {})
    workflow = payload.get("workflow", {})
    compound = payload.get("compound", {})
    executive = payload.get("executive", {})
    review_history = workflow.get("review_history", [])

    review_items = "".join(
        f"<li><strong>{escape(str(item.get('timestamp', '—')))}</strong> — "
        f"{escape(str(item.get('status', '—')))} | {escape(str(item.get('gate', '—')))} | "
        f"{escape(str(item.get('actor', '—')))}<br>{escape(str(item.get('note', '')))}</li>"
        for item in review_history[:15]
    ) or "<li>—</li>"

    html = f"""
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<title>Snapshot Técnico do Caso</title>
<style>
body {{
    font-family: Arial, sans-serif;
    background: #f5f8fc;
    color: #10243d;
    margin: 0;
}}
.container {{
    max-width: 1180px;
    margin: 28px auto;
    background: #ffffff;
    border-radius: 14px;
    padding: 28px 32px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.10);
}}
h1, h2 {{
    color: #153a6b;
}}
.grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
}}
.card {{
    background: #f8fbff;
    border: 1px solid #dbe6f5;
    border-radius: 12px;
    padding: 14px;
}}
.k {{
    color: #5d708d;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}
.v {{
    color: #0f2340;
    font-size: 20px;
    font-weight: bold;
    margin-top: 6px;
}}
.data-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
}}
.data-table th, .data-table td {{
    border: 1px solid #dbe6f5;
    padding: 8px;
    text-align: left;
    vertical-align: top;
}}
.data-table th {{
    background: #eef5fe;
}}
ul {{
    line-height: 1.55;
}}
.note {{
    background: #fff7e6;
    border: 1px solid #f6d28b;
    color: #7b5b1f;
    border-radius: 10px;
    padding: 12px 14px;
}}
</style>
</head>
<body>
<div class="container">
    <h1>Snapshot Técnico do Caso</h1>
    <p class="note">Documento de snapshot para triagem, revisão e rastreabilidade. Não substituir revisão formal de engenharia.</p>

    <h2>Cabeçalho do caso</h2>
    <div class="grid">
        <div class="card"><div class="k">Caso</div><div class="v">{escape(_safe(header.get('case_name')))}</div></div>
        <div class="card"><div class="k">Ativo</div><div class="v">{escape(_safe(header.get('compound_name')))}</div></div>
        <div class="card"><div class="k">CAS</div><div class="v">{escape(_safe(header.get('cas')))}</div></div>
        <div class="card"><div class="k">Nó</div><div class="v">{escape(_safe(header.get('node_name')))}</div></div>
        <div class="card"><div class="k">Owner</div><div class="v">{escape(_safe(header.get('owner')))}</div></div>
        <div class="card"><div class="k">Reviewer</div><div class="v">{escape(_safe(header.get('reviewer')))}</div></div>
    </div>

    <h2>Workflow e decisão</h2>
    <ul>
        <li>Status: {escape(_safe(workflow.get('status')))}</li>
        <li>Gate: {escape(_safe(workflow.get('gate')))}</li>
        <li>Nota técnica: {escape(_safe(workflow.get('status_note')))}</li>
        <li>Gerado em: {escape(_safe(payload.get('snapshot_generated_at')))}</li>
    </ul>

    <h2>Resumo executivo</h2>
    <div class="grid">
        <div class="card"><div class="k">CRI</div><div class="v">{escape(_safe(executive.get('cri_index')))}</div></div>
        <div class="card"><div class="k">Faixa CRI</div><div class="v">{escape(_safe(executive.get('cri_band')))}</div></div>
        <div class="card"><div class="k">PSI Score</div><div class="v">{escape(_safe(executive.get('psi_score')))}</div></div>
        <div class="card"><div class="k">PSI Gaps</div><div class="v">{escape(_safe(executive.get('psi_gaps')))}</div></div>
        <div class="card"><div class="k">PSI Gaps críticos</div><div class="v">{escape(_safe(executive.get('psi_critical_gaps')))}</div></div>
        <div class="card"><div class="k">Confiança do perfil</div><div class="v">{escape(_safe(compound.get('confidence_score')))}</div></div>
    </div>

    <h2>Rotas priorizadas</h2>
    <ul>{"".join(f"<li>{escape(str(x))}</li>" for x in compound.get("routing", [])) or "<li>—</li>"}</ul>

    <h2>Gaps de validação</h2>
    <ul>{"".join(f"<li>{escape(str(x))}</li>" for x in compound.get("validation_gaps", [])) or "<li>—</li>"}</ul>

    <h2>Decisões bloqueadas</h2>
    <ul>{"".join(f"<li>{escape(str(x))}</li>" for x in executive.get("blocked_decisions", [])) or "<li>—</li>"}</ul>

    <h2>Histórico de revisão</h2>
    <ul>{review_items}</ul>

    <h2>Matriz de rastreabilidade</h2>
    {_table_from_df(traceability_df)}

    <h2>Plano de ação consolidado</h2>
    {_table_from_df(action_df)}
</div>
</body>
</html>
"""
    return html.encode("utf-8")
