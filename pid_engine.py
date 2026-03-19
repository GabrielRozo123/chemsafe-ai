# pid_engine.py
from __future__ import annotations
import pandas as pd

# Tabela Verdade Expandida: Equipamentos vs Parâmetros
EQUIPMENT_PARAMETERS = {
    # Rotação e Movimentação
    "Bomba Centrífuga": ["Vazão", "Pressão", "Temperatura (Atrito)"],
    "Bomba de Deslocamento Positivo": ["Vazão", "Pressão", "Temperatura (Atrito)", "Alívio Térmico"],
    "Compressor (Centrífugo/Alternativo)": ["Pressão", "Vazão", "Temperatura"],
    "Soprador (Blower)": ["Pressão", "Vazão"],
    
    # Vasos e Armazenamento
    "Tanque de Armazenamento Atmosférico": ["Nível", "Pressão (Respiro)", "Temperatura"],
    "Vaso de Pressão / Acumulador": ["Pressão", "Nível"],
    "Separador Trifásico (Óleo/Água/Gás)": ["Nível", "Nível de Interface", "Pressão"],
    
    # Troca Térmica
    "Trocador de Calor (Casco-Tubo/Placas)": ["Temperatura", "Pressão", "Vazão", "Vazamento (Tubo-Casco)"],
    "Torre de Resfriamento": ["Temperatura", "Vazão", "Nível"],
    "Forno Fired Heater": ["Temperatura", "Pressão", "Controle de Combustão"],
    
    # Reação e Separação
    "Reator Químico": ["Temperatura", "Pressão", "Nível", "Agitação", "Reação"],
    "Coluna de Destilação / Absorção": ["Pressão", "Temperatura", "Nível (Fundo)", "Vazão (Refluxo)"],
    
    # Tubulação e Acessórios
    "Tubulação / Linha de Transferência": ["Vazão", "Pressão"],
    "Válvula de Controle": ["Vazão", "Pressão"],
    "Válvula de Segurança (PSV/PRV)": ["Alívio de Pressão", "Passagem (Vazamento)"],
    "Filtro / Strainer": ["Pressão (ΔP)"],
    "Flare / Sistema de Blowdown": ["Pressão", "Vazão", "Ignição"]
}

# Matriz de Palavras-Guia
GUIDEWORDS_MAP = {
    "Vazão": ["NENHUMA", "MAIOR", "MENOR", "REVERSA"],
    "Pressão": ["MAIOR (ALTA)", "MENOR (BAIXA)"],
    "Pressão (ΔP)": ["MAIOR (ALTA)"],
    "Temperatura": ["MAIOR (ALTA)", "MENOR (BAIXA)"],
    "Temperatura (Atrito)": ["MAIOR (ALTA)"],
    "Nível": ["MAIOR (ALTO)", "MENOR (BAIXO)"],
    "Reação": ["MAIOR (RUNAWAY)", "CONTAMINAÇÃO"],
    "Agitação": ["NENHUMA", "MENOR"],
    "Alívio de Pressão": ["FALHA AO ABRIR", "ABERTURA PREMATURA"],
    "Pressão (Respiro)": ["FALHA / BLOQUEIO"]
}

def generate_hazop_from_topology(node_name: str, equipment_list: list[str], profile) -> list[dict]:
    """
    Gera a matriz HAZOP de um Nó específico cruzando equipamentos e a física do composto.
    """
    if not equipment_list:
        return []

    is_flammable = profile.flags.get("flammable", False)
    is_toxic = profile.flags.get("toxic_inhalation", False)
    is_reactive = profile.flags.get("reactive", False)
    compound_name = profile.identity.get("name", "Composto")

    # Mapear parâmetros inerentes ao Nó
    node_parameters = set()
    for eq in equipment_list:
        for param in EQUIPMENT_PARAMETERS.get(eq, []):
            node_parameters.add(param)

    hazop_rows = []

    for param in sorted(node_parameters):
        for gw in GUIDEWORDS_MAP.get(param, []):
            causa = "Falha de equipamento, instrumentação ou erro operacional"
            consequencia = f"Desvio de processo afetando o manuseio de {compound_name}"
            salvaguarda = "Sistemas básicos de controle (BPCS)"
            rec = "Revisar projeto e matriz de causa e efeito"

            # Lógica Determinística Avançada
            if param == "Vazão" and gw == "NENHUMA":
                causa = "Bomba/Compressor parado, válvula bloqueada inadvertidamente ou entupimento severo."
                if any("Bomba" in eq for eq in equipment_list):
                    consequencia = "Superaquecimento da bomba (dead-head) e falha mecânica do selo."
                    salvaguarda = "Trip de baixa vazão / Alarme de baixa corrente no motor."

            elif param == "Pressão" and "MAIOR" in gw:
                causa = "Fechamento de válvula a jusante, falha no controle de pressão, ou expansão térmica."
                consequencia = f"Ruptura de tubulação/vaso e perda de contenção de {compound_name}."
                if is_flammable:
                    consequencia += " Risco iminente de Incêndio/Explosão (VCE)."
                if is_toxic:
                    consequencia += " Risco letal de liberação de nuvem tóxica ERPG-3."
                salvaguarda = "Válvula de Segurança (PSV), Alarme de Alta Pressão (PAH)."

            elif param == "Temperatura" and "MAIOR" in gw:
                causa = "Falha no sistema de resfriamento, perda de água gelada, ou fogo externo em área adjacente."
                if is_reactive:
                    consequencia = f"Início de Reação Runaway com polimerização/decomposição exotérmica do {compound_name}. Sobrepressurização severa."
                    salvaguarda = "Disco de ruptura, Sistema Quench, Intertravamento SIL 2 de Alta Temp."
                elif is_flammable:
                    consequencia = "Aumento da pressão de vapor do líquido. Possível alívio pela PSV ou autoignição."
                    salvaguarda = "Alarme de Alta Temperatura (TAH)."

            elif param == "Nível" and "MAIOR" in gw:
                causa = "Falha no transmissor de nível (LIT), fechamento da válvula de saída, erro de balanço de massa."
                consequencia = "Transbordamento (Overfill) do vaso ou tanque."
                if is_flammable:
                    consequencia += " Formação de poça inflamável (Pool Fire hazard)."
                salvaguarda = "Dique de contenção, Chave de Nível Alto-Alto (LSHH) com fecho da admissão."

            elif param == "Reação" and "MAIOR" in gw:
                causa = "Dosagem excessiva de catalisador, falha no resfriamento, contaminação."
                consequencia = "Runaway térmico, perda de contenção catastrófica."
                salvaguarda = "Inibidor de reação, alívio de emergência para Catch Tank."

            elif param == "Pressão (Respiro)" and "BLOQUEIO" in gw:
                causa = "Corta-chamas entupido, cristalização de produto no bocal, respiro subdimensionado."
                consequencia = "Implosão do tanque durante bombeamento (vácuo) ou ruptura do teto."
                salvaguarda = "Válvula de Pressão e Vácuo (PVRV), Alarme de pressão diferencial."

            hazop_rows.append({
                "Nó": node_name,
                "Parâmetro": param,
                "Palavra-Guia": gw,
                "Causa": causa,
                "Consequência": consequencia,
                "Salvaguarda Atual": salvaguarda,
                "Recomendação": rec
            })

    return hazop_rows

def process_bulk_pid_nodes(df: pd.DataFrame, profile) -> list[dict]:
    """
    Processa um DataFrame inteiro vindo de um CSV/Excel.
    O DataFrame deve conter as colunas 'Nó' e 'Equipamento'.
    """
    all_hazop_rows = []
    
    # Normaliza colunas
    df.columns = [col.strip().title() for col in df.columns]
    
    # Se não tiver a coluna Nó ou Equipamento, aborta
    if "Nó" not in df.columns and "No" not in df.columns:
        return []
    
    col_no = "Nó" if "Nó" in df.columns else "No"
    col_eq = "Equipamento" if "Equipamento" in df.columns else df.columns[1]
    
    # Agrupa por Nó
    grouped = df.groupby(col_no)
    
    for node_name, group in grouped:
        equipment_list = group[col_eq].dropna().tolist()
        # Mapeia para equipamentos válidos do nosso dicionário
        valid_eqs = [eq for eq in equipment_list if eq in EQUIPMENT_PARAMETERS]
        
        if valid_eqs:
            rows = generate_hazop_from_topology(str(node_name), valid_eqs, profile)
            all_hazop_rows.extend(rows)
            
    return all_hazop_rows
