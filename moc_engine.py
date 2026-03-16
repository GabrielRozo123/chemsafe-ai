from __future__ import annotations


CHANGE_BASE_WEIGHTS = {
    "Mudança química / novo composto": 28,
    "Mudança de condição operacional": 18,
    "Mudança de equipamento / material": 20,
    "Mudança de instrumentação / controle": 22,
    "Mudança em alívio / PSV": 26,
    "Mudança de procedimento / operação": 14,
    "Mudança organizacional / treinamento": 10,
}

IMPACT_WEIGHTS = {
    "Química / composição": 14,
    "Pressão": 12,
    "Temperatura": 10,
    "Vazão": 7,
    "Inventário": 10,
    "Materiais de construção": 12,
    "Instrumentação / controle": 12,
    "Alívio / PSV": 15,
    "Ventilação / detecção": 10,
    "Procedimentos operacionais": 8,
}


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _category_from_score(score: float) -> str:
    if score < 25:
        return "Baixa"
    if score < 50:
        return "Moderada"
    if score < 75:
        return "Alta"
    return "Crítica"


def evaluate_moc(
    profile,
    change_type: str,
    impacts: list[str],
    description: str,
    *,
    temporary: bool = False,
    protections_changed: bool = False,
    procedures_changed: bool = False,
    pids_affected: bool = False,
    training_required: bool = False,
    new_chemical: bool = False,
    bypass_or_override: bool = False,
) -> dict:
    score = CHANGE_BASE_WEIGHTS.get(change_type, 12)

    for item in impacts:
        score += IMPACT_WEIGHTS.get(item, 0)

    if temporary:
        score += 5
    if protections_changed:
        score += 15
    if procedures_changed:
        score += 8
    if pids_affected:
        score += 10
    if training_required:
        score += 8
    if new_chemical:
        score += 15
    if bypass_or_override:
        score += 18

    # Sensibilidade extra pelo perfil do composto
    if profile.flags.get("flammable") and any(x in impacts for x in ["Química / composição", "Temperatura", "Inventário", "Ventilação / detecção"]):
        score += 8

    if profile.flags.get("toxic_inhalation") and any(x in impacts for x in ["Química / composição", "Ventilação / detecção", "Inventário"]):
        score += 8

    if profile.flags.get("pressurized") and any(x in impacts for x in ["Pressão", "Alívio / PSV", "Temperatura"]):
        score += 8

    if profile.flags.get("corrosive") and any(x in impacts for x in ["Materiais de construção", "Química / composição"]):
        score += 8

    score = min(float(score), 100.0)
    category = _category_from_score(score)

    required_reviews = ["Atualizar documentação do processo"]
    if "Química / composição" in impacts or new_chemical:
        required_reviews.append("Revisão de compatibilidade química e FISPQ/SDS")
    if "Pressão" in impacts or "Temperatura" in impacts or "Alívio / PSV" in impacts:
        required_reviews.append("Revisão de sobrepressão, bloqueio de linha e alívio")
    if "Instrumentação / controle" in impacts or protections_changed or bypass_or_override:
        required_reviews.append("Revisão de alarmes, intertravamentos, SIS e overrides")
    if "Materiais de construção" in impacts:
        required_reviews.append("Revisão de materiais, corrosão e integridade mecânica")
    if "Procedimentos operacionais" in impacts or procedures_changed:
        required_reviews.append("Atualização de SOP / procedimento operacional")
    if training_required:
        required_reviews.append("Treinamento antes da implementação")
    if category in ["Alta", "Crítica"]:
        required_reviews.append("Revisão formal de PHA / HAZOP da mudança")
        required_reviews.append("PSSR antes da partida")
    if category == "Crítica" or bypass_or_override:
        required_reviews.append("Aprovação gerencial / autorização especial")

    required_reviews = _dedupe(required_reviews)

    checklist_rows = [
        {
            "Pilar": "Definição da mudança",
            "Item": "Descrição técnica da mudança",
            "Status": "OK" if len((description or "").strip()) >= 20 else "GAP",
            "Comentário": "Descrever o que muda, por que muda e onde muda.",
        },
        {
            "Pilar": "Escopo documental",
            "Item": "P&ID / fluxograma / lista de linhas afetados",
            "Status": "OK" if pids_affected else "PARCIAL",
            "Comentário": "Confirmar se a documentação precisa revisão.",
        },
        {
            "Pilar": "Barreiras",
            "Item": "Mudança afeta salvaguardas / proteções",
            "Status": "PARCIAL" if protections_changed else "OK",
            "Comentário": "Alarmes, intertravamentos, detectores, PSV e contenção.",
        },
        {
            "Pilar": "Operação",
            "Item": "Mudança exige revisão de procedimentos",
            "Status": "PARCIAL" if procedures_changed else "OK",
            "Comentário": "SOP, permissões, partidas, bloqueios e contingência.",
        },
        {
            "Pilar": "Pessoas",
            "Item": "Mudança exige treinamento",
            "Status": "PARCIAL" if training_required else "OK",
            "Comentário": "Treinamento operacional, manutenção e emergência.",
        },
        {
            "Pilar": "Implementação",
            "Item": "Mudança temporária / bypass / override",
            "Status": "GAP" if bypass_or_override else ("PARCIAL" if temporary else "OK"),
            "Comentário": "Mudanças temporárias e bypasses exigem controle reforçado.",
        },
    ]

    actions_rows = [{"Ação requerida": item, "Prioridade": "Alta" if category in ["Alta", "Crítica"] else "Média"} for item in required_reviews]

    impact_rows = []
    for item in impacts:
        impact_rows.append(
            {
                "Aspecto impactado": item,
                "Peso": IMPACT_WEIGHTS.get(item, 0),
            }
        )

    gap_count = sum(1 for row in checklist_rows if row["Status"] == "GAP")
    partial_count = sum(1 for row in checklist_rows if row["Status"] == "PARCIAL")

    summary = {
        "score": score,
        "category": category,
        "gap_count": gap_count,
        "partial_count": partial_count,
        "review_count": len(required_reviews),
        "temporary": temporary,
        "new_chemical": new_chemical,
        "bypass_or_override": bypass_or_override,
    }

    return {
        "summary": summary,
        "checklist_rows": checklist_rows,
        "actions_rows": actions_rows,
        "impact_rows": impact_rows,
    }
