# ce_matrix_engine.py
from __future__ import annotations
import pandas as pd

def generate_ce_matrix_from_hazop(hazop_matrix: list[dict]) -> pd.DataFrame:
    """
    Gera a Matriz de Causa e Efeito (C&E Matrix) baseada nos princípios da 
    IEC 61511 (Segurança Funcional) e API RP 14C.
    
    Extrai as "Causas/Desvios" (Inputs do PLC/SIS) e mapeia contra 
    as "Salvaguardas" (Outputs/Atuadores).
    """
    if not hazop_matrix:
        return pd.DataFrame()

    # Prepara listas para o cruzamento
    causas_inputs = []
    salvaguardas_outputs = set()
    
    # Varre o HAZOP para extrair os "Nós Lógicos"
    for row in hazop_matrix:
        causa_formatada = f"[{row.get('Nó', 'Geral')}] {row.get('Palavra-Guia', '')} {row.get('Parâmetro', '')}"
        salvaguarda = row.get("Salvaguarda Atual", "")
        
        # Só consideramos salvaguardas que parecem ser ativas/instrumentadas para a matriz
        if "Alarme" in salvaguarda or "Trip" in salvaguarda or "Intertravamento" in salvaguarda or "Fecho" in salvaguarda or "SIS" in salvaguarda:
            causas_inputs.append({"Input (Causa)": causa_formatada, "Output": salvaguarda})
            # Podemos ter múltiplas salvaguardas em uma string (separadas por vírgula)
            for s in salvaguarda.split(","):
                salvaguardas_outputs.add(s.strip())

    if not causas_inputs:
        return pd.DataFrame()

    salvaguardas_outputs = sorted(list(salvaguardas_outputs))
    
    # Constrói a Matriz Pivotada
    matrix_data = []
    for item in causas_inputs:
        row_data = {"Input (Causa - Sensor)": item["Input (Causa)"]}
        for output in salvaguardas_outputs:
            # Se o output está associado a esta causa, marca um 'X' (Lógica 1)
            if output in item["Output"]:
                row_data[output] = "❌ Ação Requerida"
            else:
                row_data[output] = ""
        matrix_data.append(row_data)

    df_ce = pd.DataFrame(matrix_data)
    return df_ce.drop_duplicates(subset=["Input (Causa - Sensor)"])
