# runaway_engine.py
from __future__ import annotations
import math

def calculate_tmr_adiabatic(T0_C: float, Ea_kJ_mol: float, A_s1: float, delta_H_kJ_kg: float, Cp_kJ_kgK: float) -> dict:
    """
    Calcula o Time to Maximum Rate (TMR) sob condições adiabáticas para reações Runaway.
    
    Referências:
    1. CCPS Guidelines for Safe Storage and Handling of Reactive Materials.
    2. Equação de Semenov / Townsend (1980) baseada em cinética de Arrhenius.
    """
    R = 8.314 # J/(mol.K)
    T0_K = T0_C + 273.15
    Ea_J_mol = Ea_kJ_mol * 1000.0
    delta_H_J_kg = abs(delta_H_kJ_kg) * 1000.0 # Assumindo exotérmica (valor absoluto)
    Cp_J_kgK = Cp_kJ_kgK * 1000.0
    
    try:
        # 1. Taxa de Geração de Calor Inicial (q0 em W/kg) = A * exp(-Ea/RT) * deltaH
        q0 = A_s1 * math.exp(-Ea_J_mol / (R * T0_K)) * delta_H_J_kg
        
        if q0 <= 1e-10:
            return {"tmr_min": float('inf'), "status": "Estável", "color": "green", "formula": "", "references": ""}

        # 2. TMR Adiabático (Semenov) = (Cp * R * T0^2) / (q0 * Ea)
        tmr_seconds = (Cp_J_kgK * R * (T0_K ** 2)) / (q0 * Ea_J_mol)
        tmr_minutes = tmr_seconds / 60.0
        
    except (ZeroDivisionError, OverflowError):
        tmr_minutes = float('inf')

    # Classificação de Risco (Regras de Ouro de Segurança de Processo)
    if tmr_minutes < 60:
        status = "CRÍTICO (Intervenção Imediata)"
        color = "red"
    elif tmr_minutes < 1440: # 24 horas
        status = "ALERTA (Requer Quench/Descarte)"
        color = "orange"
    else:
        status = "SEGURO (Tempo de Resposta Adequado)"
        color = "green"

    return {
        "tmr_min": tmr_minutes,
        "status": status,
        "color": color,
        "formula": "TMR_ad = (Cp * R * T0²) / (q0 * Ea)",
        "references": "CCPS Guidelines (Reactive Materials); Townsend & Touok (1980) Arrhenius Kinetics."
    }
