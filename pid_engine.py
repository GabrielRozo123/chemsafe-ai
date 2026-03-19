# pid_engine.py
from __future__ import annotations

# Dicionário mestre de equipamentos e seus parâmetros de processo inerentes
EQUIPMENT_PARAMETERS = {
    "Bomba Centrífuga": ["Vazão", "Pressão"],
    "Bomba de Deslocamento Positivo": ["Vazão", "Pressão", "Temperatura (Atrito)"],
    "Tanque de Armazenamento": ["Nível", "Pressão", "Temperatura"],
    "Vaso de Pressão / Separador": ["Pressão", "Nível"],
    "Trocador de Calor": ["Temperatura", "Vazão", "Pressão"],
    "Reator": ["Temperatura", "Pressão", "Nível", "Reação"],
    "Tubulação / Linha de Transferência": ["Vazão", "Pressão"],
    "Válvula de Controle": ["Vazão", "Pressão"],
    "Filtro": ["Pressão (ΔP)"]
}

# Palavras-guia padrão do HAZOP associadas a cada parâmetro
GUIDEWORDS_MAP = {
    "Vazão": ["NENHUMA", "MAIOR", "MENOR", "REVERSA"],
    "Pressão": ["MAIOR (ALTA)", "MENOR (BAIXA)"],
    "Pressão (ΔP)": ["MAIOR (ALTA)"],
    "Temperatura": ["MAIOR (ALTA)", "MENOR (BAIXA)"],
    "Temperatura (Atrito)": ["MAIOR (ALTA)"],
    "Nível": ["MAIOR (ALTO)", "MENOR (BAIXO)"],
    "Reação": ["MAIOR (RUNAWAY)", "CONTAMINAÇÃO"]
}

def generate_hazop_from_topology(node_name: str, equipment_list: list[str], profile) -> list[dict]:
    """
    Gera uma matriz HAZOP automática baseada na topologia do Nó e nas propriedades do composto.
    """
    if not equipment_list:
        return []

    # Extrai as flags de perigo do composto atual
    is_flammable = profile.flags.get("flammable", False)
    is_toxic = profile.flags.get("toxic_inhalation", False)
    is_reactive = profile.flags.get("reactive", False)
    compound_name = profile.identity.get("name", "Composto")

    # Descobrir quais parâmetros o Nó possui, juntando os parâmetros dos equipamentos selecionados
    node_parameters = set()
    for eq in equipment_list:
        for param in EQUIPMENT_PARAMETERS.get(eq, []):
            node_parameters.add(param)

    hazop_rows = []

    for param in sorted(node_parameters):
        for gw in GUIDEWORDS_MAP.get(param, []):
            causa = "Falha de equipamento ou erro operacional"
            consequencia = "Desvio de processo"
            salvaguarda = "Sistemas básicos de controle (BPCS)"
            rec = "Revisar projeto mecânico e matriz de causa e efeito"

            # Lógica Determinística Avançada: Cruzando Desvio x Físico-Química
            if param == "Vazão" and gw == "NENHUMA":
                causa = "Bomba parada, válvula de bloqueio fechada indevidamente, ou entupimento."
                if "Bomba Centrífuga" in equipment_list or "Bomba de Deslocamento Positivo" in equipment_list:
                    consequencia = "Cavitação ou superaquecimento da bomba (dead-head)."
                    salvaguarda = "Trip de baixa vazão / Alarme de baixa corrente."

            elif param == "Pressão" and "MAIOR" in gw:
                causa = "Fechamento inadvertido de válvula a jusante, falha no controle de pressão, ou expansão térmica."
                consequencia = f"Ruptura de tubulação/equipamento e perda de contenção de {compound_name}."
                if is_flammable:
                    consequencia += " Risco de Incêndio/Explosão (VCE/Jet Fire)."
                if is_toxic:
                    consequencia += " Risco de liberação de nuvem tóxica letal."
                salvaguarda = "Válvula de Segurança (PSV), Alarme de Alta Pressão (PAH)."

            elif param == "Temperatura" and "MAIOR" in gw:
                causa = "Falha no sistema de resfriamento, perda de utilidade (água gelada), ou fogo externo."
                if is_reactive:
                    consequencia = f"Reação runaway do {compound_name}, sobrepressurização severa."
                    salvaguarda = "Disco de ruptura, Sistema de Quench, SIS de Alta Temperatura."
                elif is_flammable:
                    consequencia = "Aumento da pressão de vapor, possível alívio pela PSV ou autoignição."
                    salvaguarda = "Alarme de Alta Temperatura (TAH), Resfriamento de emergência."
                else:
                    consequencia = "Aumento de pressão, degradação do produto."

            elif param == "Nível" and "MAIOR" in gw:
                causa = "Falha na malha de controle de nível, fechamento de válvula de saída, erro de recálculo."
                if "Tanque de Armazenamento" in equipment_list:
                    consequencia = "Transbordamento (Overfill) do tanque, gerando poça."
                    if is_flammable:
                        consequencia += " Risco de Pool Fire."
                    salvaguarda = "Dique de contenção, Chave de Nível Alto-Alto (LSHH) com intertravamento."

            elif param == "Vazão" and gw == "MAIOR":
                causa = "Falha da válvula de controle totalmente aberta (Fail Open)."
                if is_flammable:
                    consequencia = "Excesso de inventário em equipamentos a jusante. Possível geração de estática em linhas."
                else:
                    consequencia = "Sobrecarga de vasos separadores, arraste de líquido."

            elif param == "Vazão" and gw == "REVERSA":
                causa = "Falha em válvula de retenção e parada de bomba."
                consequencia = "Retorno de fluido de alta pressão/temperatura para área de baixa pressão. Contaminação."
                salvaguarda = "Válvula de Retenção (Check Valve)."

            # Adiciona a linha ao DataFrame do HAZOP
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
