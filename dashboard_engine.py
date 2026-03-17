from __future__ import annotations

def calculate_case_readiness_index(
    profile, 
    psi_summary: dict | None = None, 
    moc_result: dict | None = None, 
    pssr_result: dict | None = None,
    lopa_result: dict | None = None,
    reactivity_result: dict | None = None
) -> dict:
    """
    Calcula o Índice Global de Prontidão do Caso (0 a 100).
    Quanto maior, mais seguro e documentado está o cenário.
    """
    components =[]
    
    # 1. Confiança dos Dados (Alto é bom)
    conf_score = getattr(profile, "confidence_score", 0)
    components.append({"name": "Governança de Dados", "score": conf_score, "weight": 1.0})
    
    # 2. PSI Score (Alto é bom)
    if psi_summary:
        components.append({"name": "PSI / PSM", "score": psi_summary.get("score", 0), "weight": 1.5})
        
    # 3. PSSR Score (Alto é bom)
    if pssr_result:
        components.append({"name": "PSSR", "score": pssr_result["summary"].get("score", 0), "weight": 1.5})
        
    # 4. MOC Score (ALTO É RUIM na lógica do MOC. Invertendo para Readiness)
    if moc_result:
        moc_risk = moc_result["summary"].get("score", 0)
        moc_readiness = max(0, 100 - moc_risk)
        components.append({"name": "MOC Readiness", "score": moc_readiness, "weight": 1.0})
        
    # 5. Reatividade Score (ALTO É RUIM. Invertendo para Readiness)
    if reactivity_result:
        react_risk = reactivity_result["summary"].get("score", 0)
        react_readiness = max(0, 100 - react_risk)
        components.append({"name": "Compatibilidade", "score": react_readiness, "weight": 1.0})

    # 6. LOPA (Razão > 1 é ruim. <= 1 é bom)
    if lopa_result:
        ratio = lopa_result.get("ratio", 0)
        lopa_score = 100 if ratio <= 1 else max(0, 100 - ((ratio - 1) * 10)) # Penaliza gradualmente
        components.append({"name": "LOPA Adequação", "score": lopa_score, "weight": 2.0})

    # Cálculo da média ponderada
    total_weight = sum(c["weight"] for c in components)
    if total_weight == 0:
        final_index = 0
    else:
        weighted_sum = sum(c["score"] * c["weight"] for c in components)
        final_index = weighted_sum / total_weight

    # Definição das faixas (Conforme planejamento do Sprint 11)
    if final_index < 40:
        band = "Não pronto"
        color_class = "risk-red"
    elif final_index < 70:
        band = "Pronto com restrições"
        color_class = "risk-amber"
    elif final_index < 85:
        band = "Pronto para avanço técnico"
        color_class = "risk-blue"
    else:
        band = "Pacote robusto (Screening executivo)"
        color_class = "risk-green"

    return {
        "index": round(final_index, 1),
        "band": band,
        "color_class": color_class,
        "components": components
    }
