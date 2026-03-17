from __future__ import annotations
import pandas as pd

def build_what_if_comparison(base_lopa: dict, mod_lopa: dict) -> pd.DataFrame:
    """
    Gera um DataFrame comparando o cenário atual com a simulação.
    """
    rows =[]
    
    def safe_fmt(val, is_mcf=False):
        if val is None:
            return "—"
        if isinstance(val, (int, float)):
            if is_mcf:
                return f"{val:.2e}/ano"
            return f"{val:.2e}"
        return str(val)

    rows.append({
        "Indicador de Risco": "Frequência Iniciadora (F_ie)", 
        "Cenário Atual": safe_fmt(base_lopa.get('f_ie'), is_mcf=True), 
        "Cenário Simulado": safe_fmt(mod_lopa.get('f_ie'), is_mcf=True)
    })
    rows.append({
        "Indicador de Risco": "PFD Total (Falha na Proteção)", 
        "Cenário Atual": safe_fmt(base_lopa.get('pfd_total')), 
        "Cenário Simulado": safe_fmt(mod_lopa.get('pfd_total'))
    })
    rows.append({
        "Indicador de Risco": "Frequência Mitigada (MCF)", 
        "Cenário Atual": safe_fmt(base_lopa.get('mcf'), is_mcf=True), 
        "Cenário Simulado": safe_fmt(mod_lopa.get('mcf'), is_mcf=True)
    })
    
    # Comparação Executiva do SIL
    sil_atual = base_lopa.get('sil', '—')
    sil_sim = mod_lopa.get('sil', '—')
    rows.append({
        "Indicador de Risco": "Classificação SIL Requerida", 
        "Cenário Atual": sil_atual, 
        "Cenário Simulado": sil_sim
    })
    
    return pd.DataFrame(rows)
