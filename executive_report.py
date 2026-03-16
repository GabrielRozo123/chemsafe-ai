from __future__ import annotations

from datetime import datetime
from html import escape


def _safe(x):
    return "—" if x in [None, ""] else str(x)


def _list_md(items):
    if not items:
        return "- —"
    return "\n".join(f"- {item}" for item in items)


def _list_html(items):
    if not items:
        return "<li>—</li>"
    return "".join(f"<li>{escape(str(item))}</li>" for item in items)


def build_executive_bundle(case_name: str, profile, context: dict) -> dict:
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    evidence_summary = context.get("evidence_summary", {})
    evidence_recs = context.get("evidence_recommendations", [])
    hazop_priorities = context.get("hazop_priorities", [])
    lopa_result = context.get("lopa_result")
    psi_summary = context.get("psi_summary")
    moc_result = context.get("moc_result")
    pssr_result = context.get("pssr_result")
    reactivity_result = context.get("reactivity_result")

    key_actions = []
    for item in evidence_recs[:3]:
        key_actions.append(item)

    if lopa_result and lopa_result.get("ratio", 0) > 1:
        key_actions.append("Revisar IPLs e reduzir MCF antes de considerar o caso aceitável.")

    if psi_summary and psi_summary.get("gap", 0) > 0:
        key_actions.append("Fechar gaps do PSI/PSM readiness antes do avanço para estudo mais formal.")

    if moc_result:
        for row in moc_result.get("actions_rows", [])[:3]:
            key_actions.append(row["Ação requerida"])

    if pssr_result:
        for row in pssr_result.get("actions_rows", [])[:3]:
            key_actions.append(row["Ação requerida"])

    if reactivity_result and reactivity_result["summary"]["severity"] in ["Cuidado", "Incompatível"]:
        key_actions.append("Segregar substâncias incompatíveis e revisar cenário de mistura acidental.")

    # dedupe
    dedup = []
    seen = set()
    for item in key_actions:
        if item not in seen:
            seen.add(item)
            dedup.append(item)
    key_actions = dedup[:8]

    md = f"""# Relatório Executivo — {case_name}

**Data:** {ts}

## 1. Resumo executivo

- **Composto principal:** {_safe(profile.identity.get("name"))}
- **CAS:** {_safe(profile.identity.get("cas"))}
- **Confiança do pacote de dados:** {_safe(round(profile.confidence_score, 1))}/100
- **Rotas priorizadas:** {", ".join(profile.routing) if profile.routing else "—"}

## 2. Identidade e risco base

- **Fórmula:** {_safe(profile.identity.get("formula"))}
- **Massa molar:** {_safe(profile.identity.get("molecular_weight"))}
- **Perigos principais:** {", ".join(profile.hazards) if profile.hazards else "—"}

## 3. Governança de fontes

- **Campos rastreados:** {_safe(evidence_summary.get("linhas"))}
- **Fontes oficiais:** {_safe(evidence_summary.get("oficial"))}
- **Curado:** {_safe(evidence_summary.get("curado"))}
- **Revisar:** {_safe(evidence_summary.get("revisar"))}
- **Com link oficial:** {_safe(evidence_summary.get("com_link"))}

### Recomendações de governança
{_list_md(evidence_recs)}

## 4. HAZOP prioritário

{_list_md([f"{item.get('focus', '—')} — {item.get('why', '—')}" for item in hazop_priorities])}

## 5. LOPA

- **Resultado:** {_safe(lopa_result.get("sil")) if lopa_result else "—"}
- **MCF:** {_safe(f"{lopa_result.get('mcf', 0):.2e}/ano") if lopa_result else "—"}
- **Razão MCF/critério:** {_safe(round(lopa_result.get("ratio", 0), 2)) if lopa_result else "—"}

## 6. PSI / PSM Readiness

- **Score:** {_safe(round(psi_summary.get("score", 0), 1)) if psi_summary else "—"}/100
- **Itens OK:** {_safe(psi_summary.get("ok")) if psi_summary else "—"}
- **Itens parciais:** {_safe(psi_summary.get("partial")) if psi_summary else "—"}
- **Gaps:** {_safe(psi_summary.get("gap")) if psi_summary else "—"}

## 7. MOC

- **Classe:** {_safe(moc_result["summary"]["category"]) if moc_result else "—"}
- **Score:** {_safe(round(moc_result["summary"]["score"], 1)) if moc_result else "—"}/100

## 8. PSSR

- **Readiness:** {_safe(pssr_result["summary"]["readiness"]) if pssr_result else "—"}
- **Score:** {_safe(round(pssr_result["summary"]["score"], 1)) if pssr_result else "—"}/100

## 9. Compatibilidade entre substâncias

- **Severidade:** {_safe(reactivity_result["summary"]["severity"]) if reactivity_result else "—"}
- **Score:** {_safe(reactivity_result["summary"]["score"]) if reactivity_result else "—"}/100
- **Regras disparadas:** {_safe(reactivity_result["summary"]["rule_hits"]) if reactivity_result else "—"}

### Recomendações de compatibilidade
{_list_md(reactivity_result.get("recommendations", [])) if reactivity_result else "- —"}

## 10. Ações prioritárias

{_list_md(key_actions)}
"""

    html = f"""
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<title>Relatório Executivo - {escape(case_name)}</title>
<style>
body {{
    font-family: Arial, sans-serif;
    background: #f4f7fb;
    color: #142033;
    margin: 0;
    padding: 0;
}}
.container {{
    max-width: 1100px;
    margin: 24px auto;
    background: white;
    border-radius: 14px;
    padding: 28px 34px;
    box-shadow: 0 10px 24px rgba(0,0,0,0.10);
}}
h1 {{
    color: #0b2a52;
    margin-bottom: 6px;
}}
h2 {{
    color: #163e73;
    border-bottom: 1px solid #d9e3f0;
    padding-bottom: 6px;
    margin-top: 28px;
}}
.meta {{
    color: #5d708d;
    margin-bottom: 18px;
}}
ul {{
    line-height: 1.55;
}}
.grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
}}
.card {{
    background: #f8fbff;
    border: 1px solid #dbe6f5;
    border-radius: 10px;
    padding: 14px;
}}
.k {{
    color: #627792;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}
.v {{
    color: #0f2340;
    font-size: 22px;
    font-weight: bold;
    margin-top: 6px;
}}
</style>
</head>
<body>
<div class="container">
    <h1>Relatório Executivo — {escape(case_name)}</h1>
    <div class="meta">Emitido em {escape(ts)}</div>

    <div class="grid">
        <div class="card"><div class="k">Composto principal</div><div class="v">{escape(_safe(profile.identity.get("name")))}</div></div>
        <div class="card"><div class="k">CAS</div><div class="v">{escape(_safe(profile.identity.get("cas")))}</div></div>
        <div class="card"><div class="k">Confiança</div><div class="v">{escape(_safe(round(profile.confidence_score, 1)))}/100</div></div>
        <div class="card"><div class="k">Rotas priorizadas</div><div class="v">{escape(str(len(profile.routing)))}</div></div>
    </div>

    <h2>Governança de fontes</h2>
    <ul>
        <li>Campos rastreados: {escape(_safe(evidence_summary.get("linhas")))}</li>
        <li>Fontes oficiais: {escape(_safe(evidence_summary.get("oficial")))}</li>
        <li>Curado: {escape(_safe(evidence_summary.get("curado")))}</li>
        <li>Revisar: {escape(_safe(evidence_summary.get("revisar")))}</li>
        <li>Com link oficial: {escape(_safe(evidence_summary.get("com_link")))}</li>
    </ul>
    <ul>{_list_html(evidence_recs)}</ul>

    <h2>HAZOP prioritário</h2>
    <ul>{_list_html([f"{item.get('focus', '—')} — {item.get('why', '—')}" for item in hazop_priorities])}</ul>

    <h2>LOPA</h2>
    <ul>
        <li>SIL: {escape(_safe(lopa_result.get("sil")) if lopa_result else "—")}</li>
        <li>MCF: {escape(_safe(f"{lopa_result.get('mcf', 0):.2e}/ano") if lopa_result else "—")}</li>
        <li>Razão MCF/critério: {escape(_safe(round(lopa_result.get("ratio", 0), 2)) if lopa_result else "—")}</li>
    </ul>

    <h2>PSI / PSM</h2>
    <ul>
        <li>Score: {escape(_safe(round(psi_summary.get("score", 0), 1)) if psi_summary else "—")}/100</li>
        <li>Gaps: {escape(_safe(psi_summary.get("gap")) if psi_summary else "—")}</li>
    </ul>

    <h2>MOC / PSSR</h2>
    <ul>
        <li>MOC: {escape(_safe(moc_result["summary"]["category"]) if moc_result else "—")} ({escape(_safe(round(moc_result["summary"]["score"], 1)) if moc_result else "—")}/100)</li>
        <li>PSSR: {escape(_safe(pssr_result["summary"]["readiness"]) if pssr_result else "—")} ({escape(_safe(round(pssr_result["summary"]["score"], 1)) if pssr_result else "—")}/100)</li>
    </ul>

    <h2>Compatibilidade entre substâncias</h2>
    <ul>
        <li>Severidade: {escape(_safe(reactivity_result["summary"]["severity"]) if reactivity_result else "—")}</li>
        <li>Score: {escape(_safe(reactivity_result["summary"]["score"]) if reactivity_result else "—")}/100</li>
        <li>Regras disparadas: {escape(_safe(reactivity_result["summary"]["rule_hits"]) if reactivity_result else "—")}</li>
    </ul>
    <ul>{_list_html(reactivity_result.get("recommendations", [])) if reactivity_result else "<li>—</li>"}</ul>

    <h2>Ações prioritárias</h2>
    <ul>{_list_html(key_actions)}</ul>
</div>
</body>
</html>
"""

    return {
        "markdown": md.encode("utf-8"),
        "html": html.encode("utf-8"),
    }
