# ml_reliability_engine.py
from __future__ import annotations
import math

def calculate_dynamic_pfd(base_pfd: float, time_in_service_months: float, anomaly_score_0_to_1: float, equipment_type: str) -> dict:
    """
    Motor de Confiabilidade Dinâmica baseado na Distribuição de Weibull e Dados OREDA.
    Ajusta o PFD (Probability of Failure on Demand) estático com base no desgaste temporal
    e alertas preditivos (simulando ingestão de dados de Machine Learning/Sensores).
    
    Referências:
    1. OREDA (Offshore Reliability Data Handbook)
    2. IEC 61508-6 (Functional Safety) - Modelagem de Falhas dependentes do tempo.
    """
    # Fator de forma de Weibull (beta) - >1 indica fase de desgaste (wear-out)
    beta = 1.5 if "Bomba" in equipment_type or "Compressor" in equipment_type else 1.2
    
    # Ajuste de envelhecimento (Tempo)
    # Assumimos que o base_pfd é validado para t=12 meses.
    time_factor = (time_in_service_months / 12.0) ** beta
    
    # Ajuste Preditivo (Anomalia de ML, ex: vibração alta, ruído)
    # Se anomaly_score = 0, fator = 1. Se = 1 (crítico), fator = 10 (multiplica o risco por 10)
    predictive_factor = 1.0 + (9.0 * anomaly_score_0_to_1)
    
    # Cálculo Final
    dynamic_pfd = base_pfd * time_factor * predictive_factor
    
    # Cap em 1.0 (100% de chance de falha)
    dynamic_pfd = min(dynamic_pfd, 1.0)
    
    # Delta (aumento percentual do risco)
    risk_increase = ((dynamic_pfd - base_pfd) / base_pfd) * 100
    
    return {
        "dynamic_pfd": dynamic_pfd,
        "pfd_str": f"{dynamic_pfd:.2e}",
        "risk_increase_pct": risk_increase,
        "formula": "PFD(t) = PFD_base * (t/t_ref)^β * F_pred",
        "references": "OREDA Handbook; Modelagem de Falhas de Weibull (IEC 61508-6)."
    }
