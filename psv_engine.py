# psv_engine.py
from __future__ import annotations
import math

def size_psv_gas(W_kg_h: float, T_C: float, P1_kPag: float, Z: float, MW: float, k: float = 1.31) -> dict:
    """
    Dimensionamento de Válvula de Segurança (PSV) para Gases/Vapores.
    Referência: API Standard 520 Part I, 9th Edition.
    """
    # Conversões e Constantes
    T_K = T_C + 273.15
    P1_kPaa = P1_kPag + 101.325 # Pressão de alívio absoluta
    C = 520 * math.sqrt(k * ((2 / (k + 1)) ** ((k + 1) / (k - 1)))) # Coeficiente do gás
    
    Kd = 0.975 # Coeficiente de descarga (efetivo)
    Kb = 1.0   # Fator de contrapressão
    Kc = 1.0   # Fator de disco de ruptura
    
    # Fórmula API 520: A (mm²) = (W / (C * Kd * P1 * Kb * Kc)) * sqrt((T * Z) / M)
    try:
        area_mm2 = (W_kg_h / (C * Kd * P1_kPaa * Kb * Kc)) * math.sqrt((T_K * Z) / MW) * 1000
    except ZeroDivisionError:
        area_mm2 = 0.0

    # Seleção de Letra de Orifício API
    api_orifices = {
        "D": 71.0, "E": 126.0, "F": 198.0, "G": 325.0, "H": 506.0,
        "J": 830.0, "K": 1186.0, "L": 1841.0, "M": 2323.0, "N": 2800.0,
        "P": 4116.0, "Q": 7129.0, "R": 10323.0, "T": 16774.0
    }
    
    selected_letter = "Fora de Padrão (Requer múltiplas PSVs)"
    selected_area = 0.0
    for letter, std_area in api_orifices.items():
        if std_area >= area_mm2:
            selected_letter = letter
            selected_area = std_area
            break

    return {
        "calculated_area_mm2": area_mm2,
        "api_letter": selected_letter,
        "api_area_mm2": selected_area,
        "formula": "A = (W / (C·Kd·P1·Kb·Kc)) · √((T·Z)/M)",
        "references": "API STD 520 Part I - Sizing, Selection, and Installation of Pressure-relieving Devices."
    }
