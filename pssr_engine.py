from __future__ import annotations


CORE_WEIGHTS = {
    "design": 18,
    "procedures": 16,
    "pha_moc": 18,
    "training": 14,
}

BEST_PRACTICE_WEIGHTS = {
    "mi_ready": 8,
    "relief_verified": 8,
    "alarms_tested": 7,
    "emergency_ready": 6,
    "startup_authorized": 5,
}


def _status(ok: bool) -> str:
    return "OK" if ok else "GAP"


def evaluate_pssr(
    *,
    design_ok: bool,
    procedures_ok: bool,
    pha_or_moc_ok: bool,
    training_ok: bool,
    mi_ready: bool,
    relief_verified: bool,
    alarms_tested: bool,
    emergency_ready: bool,
    startup_authorized: bool,
    scope_label: str,
) -> dict:
    score = 0.0

    if design_ok:
        score += CORE_WEIGHTS["design"]
    if procedures_ok:
        score += CORE_WEIGHTS["procedures"]
    if pha_or_moc_ok:
        score += CORE_WEIGHTS["pha_moc"]
    if training_ok:
        score += CORE_WEIGHTS["training"]

    if mi_ready:
        score += BEST_PRACTICE_WEIGHTS["mi_ready"]
    if relief_verified:
        score += BEST_PRACTICE_WEIGHTS["relief_verified"]
    if alarms_tested:
        score += BEST_PRACTICE_WEIGHTS["alarms_tested"]
    if emergency_ready:
        score += BEST_PRACTICE_WEIGHTS["emergency_ready"]
    if startup_authorized:
        score += BEST_PRACTICE_WEIGHTS["startup_authorized"]

    blockers = []
    if not design_ok:
        blockers.append("Construção/equipamento não confirmados contra a especificação de projeto.")
    if not procedures_ok:
        blockers.append("Procedimentos de segurança, operação, manutenção ou emergência não estão adequados.")
    if not pha_or_moc_ok:
        blockers.append("Base de PHA/MOC não está resolvida para a partida.")
    if not training_ok:
        blockers.append("Treinamento do pessoal envolvido não está concluído.")

    if blockers:
        readiness = "NÃO PRONTO"
    elif score < 75:
        readiness = "PRONTO COM CONDICIONANTES"
    else:
        readiness = "PRONTO PARA STARTUP"

    checklist_rows = [
        {
            "Pilar": "Projeto",
            "Item": "Construção e equipamentos conforme especificação",
            "Status": _status(design_ok),
            "Referência": "PSSR",
            "Comentário": "Confirmar aderência ao projeto e às mudanças aprovadas.",
        },
        {
            "Pilar": "Procedimentos",
            "Item": "Procedimentos de segurança, operação, manutenção e emergência",
            "Status": _status(procedures_ok),
            "Referência": "PSSR",
            "Comentário": "Devem existir e estar adequados antes da introdução do químico.",
        },
        {
            "Pilar": "PHA / MOC",
            "Item": f"Base de {scope_label}",
            "Status": _status(pha_or_moc_ok),
            "Referência": "PSSR",
            "Comentário": "Para nova instalação: PHA resolvida. Para modificação: MOC atendido.",
        },
        {
            "Pilar": "Treinamento",
            "Item": "Treinamento concluído para os envolvidos no processo",
            "Status": _status(training_ok),
            "Referência": "PSSR",
            "Comentário": "Treinamento antes da introdução do químico.",
        },
        {
            "Pilar": "Integridade",
            "Item": "Mechanical integrity / prontidão de equipamento",
            "Status": _status(mi_ready),
            "Referência": "Boa prática",
            "Comentário": "Teste, inspeção, torque, vedação, interligações e condição operacional.",
        },
        {
            "Pilar": "Relief / proteção",
            "Item": "PSV / alívio / bloqueios revisados",
            "Status": _status(relief_verified),
            "Referência": "Boa prática",
            "Comentário": "Revisar cenários de sobrepressão, bloqueio e fire case quando aplicável.",
        },
        {
            "Pilar": "Instrumentação",
            "Item": "Alarmes, detectores, trips e permissivos testados",
            "Status": _status(alarms_tested),
            "Referência": "Boa prática",
            "Comentário": "Confirmar laços críticos antes da partida.",
        },
        {
            "Pilar": "Emergência",
            "Item": "Plano de emergência e resposta disponíveis",
            "Status": _status(emergency_ready),
            "Referência": "Boa prática",
            "Comentário": "Evacuação, comunicação e recursos mínimos de resposta.",
        },
        {
            "Pilar": "Liberação",
            "Item": "Autorização formal para startup",
            "Status": _status(startup_authorized),
            "Referência": "Boa prática",
            "Comentário": "Liberar partida somente após fechamento das pendências críticas.",
        },
    ]

    actions_rows = []
    for row in checklist_rows:
        if row["Status"] == "GAP":
            actions_rows.append(
                {
                    "Ação requerida": row["Item"],
                    "Prioridade": "Alta" if row["Referência"] == "PSSR" else "Média",
                    "Comentário": row["Comentário"],
                }
            )

    summary = {
        "score": min(score, 100.0),
        "readiness": readiness,
        "blocker_count": len(blockers),
        "action_count": len(actions_rows),
    }

    return {
        "summary": summary,
        "blockers": blockers,
        "checklist_rows": checklist_rows,
        "actions_rows": actions_rows,
    }
