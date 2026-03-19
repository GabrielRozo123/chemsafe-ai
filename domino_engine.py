# domino_engine.py
from __future__ import annotations
import math

def calculate_domino_effect(distance_m: float, mass_burning_rate_kg_s: float, heat_of_combustion_j_kg: float, radiation_fraction: float = 0.3) -> dict:
    """
    Motor termodinâmico auditável para cálculo de Efeito Dominó (Facility Siting).
    
    Bases de Cálculo e Normas:
    1. Modelo Físico: Point Source Model (TNO Yellow Book / CCPS Guidelines for Evaluating Vapor Cloud Explosions and Flash Fires).
       Equação: q = (eta * m_dot * Hc) / (4 * pi * x^2)
    2. Critérios de Dano: API Standard 521 (Pressure-relieving and Depressuring Systems).
    """
    # Evitar divisão por zero se a distância for muito pequena
    if distance_m <= 0.5:
        distance_m = 0.5
        
    # q_W = (fração_radiante * taxa_de_queima * calor_de_combustao) / (4 * pi * distancia^2)
    q_W_m2 = (radiation_fraction * mass_burning_rate_kg_s * heat_of_combustion_j_kg) / (4 * math.pi * (distance_m ** 2))
    q_kW_m2 = q_W_m2 / 1000.0
    
    # Avaliação rigorosa baseada na API 521
    if q_kW_m2 >= 37.5:
        status = "DANO ESTRUTURAL IMINENTE (RUPTURA)"
        color = "red"
        impact = "API 521: Falha catastrófica de vasos de pressão e colapso de estruturas de aço. Efeito dominó acionado."
    elif q_kW_m2 >= 12.5:
        status = "PERDA DE CONTROLE (IGNIÇÃO)"
        color = "orange"
        impact = "API 521: Ignição de plásticos/madeira, derretimento de cabos de instrumentação. Perda do SIS do equipamento alvo."
    elif q_kW_m2 >= 4.7:
        status = "ZONA LETAL / RESTRIÇÃO OPERACIONAL"
        color = "yellow"
        impact = "API 521: Dor extrema e fatalidade em menos de 20 segundos. Operadores não podem atuar em válvulas manuais."
    elif q_kW_m2 >= 1.6:
        status = "ZONA DE ATENÇÃO (FUGA)"
        color = "blue"
        impact = "API 521: Máximo aceitável para exposição prolongada de pessoal com EPI básico durante emergência."
    else:
        status = "ZONA SEGURA"
        color = "green"
        impact = "Radiação irrelevante para equipamentos e tolerável para humanos."

    return {
        "q_kW_m2": q_kW_m2,
        "status": status,
        "color": color,
        "impact": impact,
        "formula": "q'' = (η · ṁ · ΔHc) / (4πx²)",
        "references": "Cálculo: Point Source Model (CCPS/TNO). Limiares: API STD 521."
    }
