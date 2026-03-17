from __future__ import annotations
import pandas as pd

def evaluate_area_risk(profile, area_type: str) -> dict:
    """
    Avalia como o perfil do composto se comporta dependendo da área de instalação.
    Áreas: Laboratório, Almoxarifado, Sala de Cilindros, Tanque, Utilidades.
    """
    
    warnings = []
    safeguards =[]
    
    # 1. Laboratório (Baixo volume, alta interação humana)
    if area_type == "Laboratório":
        if profile.flags.get("toxic_inhalation") or profile.flags.get("flammable"):
            warnings.append("Manipulação exige Capela de Exaustão (Fume Hood).")
            safeguards.extend(["Capela de exaustão", "Chuveiro de emergência", "EPI específico (Luvas/Óculos)"])
        if profile.flags.get("pressurized"):
            warnings.append("Cilindros de bancada devem estar devidamente acorrentados.")

    # 2. Almoxarifado (Armazenamento, risco de mistura)
    elif area_type == "Almoxarifado":
        warnings.append("Atenção máxima à matriz de incompatibilidade química nas prateleiras.")
        safeguards.extend(["Bacia de contenção no piso", "Ventilação mecânica", "Sprinklers / Combate a incêndio"])
        if profile.flags.get("flammable"):
            warnings.append("Área classificada requerida. Proibido fontes de ignição.")

    # 3. Sala de Cilindros (Alta pressão, vazamento de gás)
    elif area_type == "Sala de Cilindros":
        safeguards.extend(["Cilindros acorrentados", "Reguladores de pressão verificados", "Paredes corta-fogo"])
        if profile.flags.get("toxic_inhalation"):
            warnings.append("Risco de asfixia/intoxicação rápida em ambiente fechado.")
            safeguards.append("Detector de gás com alarme sonoro/visual")

    # 4. Tanque / Parque de Tanques (Alto volume, consequências catastróficas)
    elif area_type == "Tanque":
        warnings.append("Cenário de Perda de Contenção Maior (Major Loss of Containment).")
        safeguards.extend(["Dique de contenção (110% do volume)", "Válvula SDV / Isolamento remoto", "PSV / Válvula de alívio"])
        if profile.flags.get("flammable"):
            warnings.append("Avaliar cenário de Pool Fire e Radiação Térmica.")
            safeguards.extend(["Anéis de resfriamento", "Sistema gerador de espuma"])

    # 5. Utilidades
    elif area_type == "Utilidades":
        warnings.append("Garantir que não haja contaminação cruzada com o processo principal.")
        safeguards.extend(["Válvulas de retenção (Check valves)", "Purgadores"])

    return {
        "area": area_type,
        "warnings": warnings,
        "safeguards": safeguards
    }
