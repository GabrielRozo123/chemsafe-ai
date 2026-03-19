# hra_engine.py
from __future__ import annotations

def calculate_human_error_probability(time_available: str, stress_level: str, complexity: str) -> dict:
    """
    Calcula a Probabilidade de Erro Humano (HEP) baseado no método THERP (NUREG/CR-1278).
    """
    # Probabilidades base nominais (Diagnóstico + Ação)
    base_hep = 0.01 
    
    # Multiplicadores de Tempo (PSF - Performance Shaping Factors)
    time_factor = {
        "Menos de 5 minutos": 10.0,
        "5 a 10 minutos": 2.0,
        "10 a 30 minutos": 1.0,
        "Mais de 30 minutos": 0.1
    }.get(time_available, 1.0)
    
    # Multiplicadores de Estresse
    stress_factor = {
        "Extremo (Emergência Crítica)": 5.0,
        "Alto (Alarme de Alta Prioridade)": 2.0,
        "Nominal (Operação Normal)": 1.0
    }.get(stress_level, 1.0)
    
    # Multiplicadores de Complexidade
    complexity_factor = {
        "Alta (Múltiplas válvulas/painéis)": 3.0,
        "Média (Ação em painel único)": 1.0,
        "Baixa (Pressionar botão de emergência)": 0.5
    }.get(complexity, 1.0)
    
    final_hep = base_hep * time_factor * stress_factor * complexity_factor
    
    # Cap máximo de erro (não pode ser maior que 1.0, ou 100%)
    if final_hep > 1.0:
        final_hep = 1.0
        
    return {
        "hep": final_hep,
        "pfd_equivalent": f"{final_hep:.1e}",
        "sil_equivalent": "N/A (Falha Humana)" if final_hep > 0.1 else f"Equivalente SIL {int(abs(math.log10(final_hep)))}",
        "references": "NUREG/CR-1278 (THERP) - Human Reliability Analysis."
    }
import math
