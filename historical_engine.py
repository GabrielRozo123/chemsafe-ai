# historical_engine.py
from historical_db import HISTORICAL_CASES

def get_relevant_historical_cases(profile) -> list[dict]:
    """
    Retorna os casos históricos mais relevantes com base no composto atual (profile).
    A lógica de priorização:
    1. Match exato pelo CAS.
    2. Match parcial pelo nome/sinônimos.
    3. Match por família de perigos (Flags).
    """
    target_cas = profile.identity.get("cas", "")
    target_name = profile.identity.get("name", "").lower()
    
    # Extrair flags de perigo do composto atual
    profile_flags = set()
    if profile.flags.get("flammable"): profile_flags.add("Inflamável")
    if profile.flags.get("toxic_inhalation"): profile_flags.add("Tóxico")
    
    scored_cases = []
    
    for case in HISTORICAL_CASES:
        score = 0
        match_reason = []
        
        # 1. Match de CAS
        if target_cas and case["cas_associado"] == target_cas:
            score += 100
            match_reason.append("Match exato de substância (CAS)")
            
        # 2. Match de nome/sinônimo
        if target_name and target_name in case["substancia_principal"].lower():
            score += 80
            match_reason.append("Match exato de substância (Nome)")
            
        # 3. Match por perigo (Tags)
        case_tags = set(case.get("tags", []))
        overlap = profile_flags.intersection(case_tags)
        if overlap:
            score += (len(overlap) * 10)
            match_reason.append(f"Perigos similares ({', '.join(overlap)})")
            
        if score > 0:
            # Adiciona os motivos ao dicionário do caso para exibição
            case_copy = case.copy()
            case_copy["score"] = score
            case_copy["relevancia"] = " | ".join(match_reason)
            scored_cases.append(case_copy)
            
    # Ordenar pelos mais relevantes primeiro
    scored_cases.sort(key=lambda x: x["score"], reverse=True)
    
    return scored_cases
