from __future__ import annotations
import pandas as pd

def build_consolidated_action_plan(
    profile, 
    psi_df: pd.DataFrame | None = None, 
    moc_result: dict | None = None, 
    pssr_result: dict | None = None, 
    reactivity_result: dict | None = None
) -> pd.DataFrame:
    """
    Consolida todas as ações e gaps dos diferentes módulos em um único Plano de Ação.
    """
    actions =[]

    # 1. Gaps de Governança e Propriedades (Profile)
    if getattr(profile, "validation_gaps", None):
        for gap in profile.validation_gaps:
            actions.append({
                "Origem": "Governança de Dados",
                "Ação Requerida": gap,
                "Criticidade": "Média",
                "Status": "Pendente"
            })

    # 2. Gaps de PSI / PSM
    if psi_df is not None and not psi_df.empty:
        gaps = psi_df[psi_df["Status"] == "GAP"]
        for _, row in gaps.iterrows():
            actions.append({
                "Origem": "PSI / PSM",
                "Ação Requerida": row.get("Ação recomendada", f"Resolver gap: {row.get('Item')}"),
                "Criticidade": "Alta",
                "Status": "Pendente"
            })

    # 3. Ações do MOC
    if moc_result and "actions_rows" in moc_result:
        for act in moc_result["actions_rows"]:
            actions.append({
                "Origem": "MOC",
                "Ação Requerida": act.get("Ação requerida", ""),
                "Criticidade": act.get("Prioridade", "Alta"),
                "Status": "Pendente"
            })

    # 4. Ações do PSSR
    if pssr_result and "actions_rows" in pssr_result:
        for act in pssr_result["actions_rows"]:
            actions.append({
                "Origem": "PSSR",
                "Ação Requerida": act.get("Ação requerida", ""),
                "Criticidade": act.get("Prioridade", "Crítica"),
                "Status": "Pendente"
            })

    # 5. Ações de Reatividade
    if reactivity_result and "recommendations" in reactivity_result:
        for rec in reactivity_result["recommendations"]:
            if "Não foram detectadas" not in rec: # Ignora o placeholder de quando está tudo OK
                actions.append({
                    "Origem": "Reatividade Lab",
                    "Ação Requerida": rec,
                    "Criticidade": "Alta" if reactivity_result["summary"]["severity"] in ["Incompatível", "Cuidado"] else "Média",
                    "Status": "Pendente"
                })

    if not actions:
        return pd.DataFrame(columns=["Origem", "Ação Requerida", "Criticidade", "Status"])
    
    return pd.DataFrame(actions)
