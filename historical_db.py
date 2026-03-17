# historical_db.py

HISTORICAL_CASES = [
    {
        "id": "HC-001",
        "evento": "Desastre de Bhopal",
        "ano": 1984,
        "local": "Madhya Pradesh, Índia",
        "substancia_principal": "Isocianato de Metila",
        "cas_associado": "624-83-9",
        "tipo_evento": "Runaway Reaction / Toxic Release",
        "mecanismo": "Ingresso de água no tanque de armazenamento causou reação exotérmica descontrolada, superpressurização e liberação de nuvem tóxica.",
        "barreiras_falharam": [
            "Sistema de refrigeração do tanque (desligado)",
            "Scrubber de gases (inoperante/subdimensionado)",
            "Flare tower (tubulação desconectada para manutenção)",
            "Sirene de alarme comunitário (desativada para não alarmar a vizinhança)"
        ],
        "consequencias": "Milhares de fatalidades imediatas; lesões crônicas na população; abandono da planta.",
        "licoes_aprendidas": [
            "Sistemas de mitigação (Scrubbers/Flares) não podem ser colocados offline simultaneamente se o inventário perigoso permanece.",
            "A minimização de inventário de intermediários tóxicos (Inherent Safety) deve ser prioritária.",
            "O isolamento de utilidades (água) de reagentes incompatíveis requer barreiras físicas rígidas, não apenas válvulas de bloqueio simples."
        ],
        "fonte": "CSB / Relatórios Governamentais da Índia",
        "classe_fonte": "Oficial / Investigação",
        "tags": ["Tóxico", "Runaway", "Falha de Manutenção"]
    },
    {
        "id": "HC-002",
        "evento": "Explosão de Flixborough",
        "ano": 1974,
        "local": "Inglaterra, Reino Unido",
        "substancia_principal": "Ciclohexano",
        "cas_associado": "110-82-7",
        "tipo_evento": "Vapor Cloud Explosion (VCE)",
        "mecanismo": "Falha mecânica de um bypass temporário (tubo de 20 polegadas com foles não suportados adequadamente) liberou grandes quantidades de ciclohexano a quente sob pressão.",
        "barreiras_falharam": [
            "Gestão de Mudança (MOC) inexistente para a instalação do bypass temporário.",
            "Projeto mecânico inadequado (ausência de suporte estrutural para a força de cisalhamento nos foles).",
            "Controle de ignição de área."
        ],
        "consequencias": "28 fatalidades; 36 feridos; destruição total da planta.",
        "licoes_aprendidas": [
            "Qualquer modificação temporária no processo exige avaliação rigorosa de engenharia (Nascimento do conceito moderno de MOC).",
            "Plantas que operam com líquidos inflamáveis acima do ponto de ebulição (superheated) têm potencial catastrófico de VCE."
        ],
        "fonte": "Relatório de Inquérito Britânico",
        "classe_fonte": "Oficial / Investigação",
        "tags": ["Inflamável", "VCE", "MOC", "Mecânica"]
    },
    {
        "id": "HC-003",
        "evento": "Explosão na Texas City Refinery (BP)",
        "ano": 2005,
        "local": "Texas, EUA",
        "substancia_principal": "Hidrocarbonetos (Mistura inflamável)",
        "cas_associado": "N/A",  # Usado por tag
        "tipo_evento": "Overfill / VCE",
        "mecanismo": "Transbordamento de uma torre de separação de isômeros (Raffinate Splitter) durante o startup, com alívio para um tambor de blowdown (aberto para a atmosfera), gerando nuvem de vapor.",
        "barreiras_falharam": [
            "Transmissores de nível da torre (marcavam nível normal quando estava cheia)",
            "Válvulas de controle de saída operadas em manual e fechadas.",
            "Design do sistema de alívio (tambor com chaminé atmosférica em vez de flare fechado)."
        ],
        "consequencias": "15 fatalidades; 180 feridos. Destruição de trailers temporários localizados perto do processo.",
        "licoes_aprendidas": [
            "Sistemas de alívio de líquidos inflamáveis não devem ser direcionados para atmosfera sem contenção/queima.",
            "A fadiga do operador e instrumentação deficiente durante o startup (fase transiente) multiplicam o risco.",
            "Trailers e escritórios não devem estar na zona de sobrepressão (Facility Siting)."
        ],
        "fonte": "US Chemical Safety Board (CSB)",
        "classe_fonte": "Oficial / CSB",
        "tags": ["Inflamável", "VCE", "Startup", "Falha de Instrumentação"]
    },
    {
        "id": "HC-004",
        "evento": "Incidente em Seveso",
        "ano": 1976,
        "local": "Lombardia, Itália",
        "substancia_principal": "TCDD (Dioxina)",
        "cas_associado": "1746-01-6",
        "tipo_evento": "Runaway / Toxic Release",
        "mecanismo": "Reação exotérmica descontrolada após parada de fim de semana (sem agitação ou resfriamento) em um reator de TCB, levando ao alívio para a atmosfera de nuvem contendo Dioxina.",
        "barreiras_falharam": [
            "Falta de sistema de contenção secundária (disco de ruptura aliviava direto pro teto).",
            "Procedimento de parada incompleto (deixou o reator com carga térmica residual).",
            "Ausência de instrumentação para detectar a formação da Dioxina."
        ],
        "consequencias": "Contaminação em massa do solo; sacrifício de milhares de animais; doenças de pele severas na população (Cloracne).",
        "licoes_aprendidas": [
            "Sistemas de alívio de emergência de reatores devem obrigatoriamente contar com contenção (catch tanks) e tratamento (scrubbers).",
            "A importância vital do monitoramento de temperaturas durante paradas parciais ou em 'hold'.",
            "Deu origem à Diretiva Seveso na Europa (obrigatoriedade de relatórios públicos de segurança)."
        ],
        "fonte": "Diretiva Seveso / Literatura Técnica",
        "classe_fonte": "Oficial / Marco Regulatório",
        "tags": ["Tóxico", "Runaway", "Procedimento"]
    }
]
