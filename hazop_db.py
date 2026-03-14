from __future__ import annotations

HAZOP_DB = {
    'Temperatura': {
        'MAIS': {
            'causas': ['Falha de válvula de controle (stuck open)', 'Falha no sistema de refrigeração', 'Reação exotérmica descontrolada (runaway)', 'Contaminação por catalisador não intencional'],
            'conseqs': ['Decomposição térmica do produto', 'Pressurização acima do MAWP', 'Formação de vapores inflamáveis acima do LIE', 'Emissão de gases tóxicos de decomposição'],
            'salvags': ['TAH / TAHH', 'PSV/PRV calibrada', 'Procedimento de emergência', 'Resfriamento redundante'],
            'rec': ['Verificar cenário fire case', 'Separar BPCS e SIS', 'Revisar redundância térmica', 'Executar LOPA do cenário runaway'],
        },
        'MENOS': {
            'causas': ['Falha de aquecimento', 'Perda de utilidades', 'Carga fria inesperada'],
            'conseqs': ['Solidificação', 'Aumento de viscosidade', 'Off-spec'],
            'salvags': ['TAL', 'Intertravamento de partida'],
            'rec': ['Adicionar rastreamento térmico', 'Formalizar procedimento de start-up'],
        },
    },
    'Pressão': {
        'MAIS': {
            'causas': ['Bloqueio de linha de saída', 'Falha de controlador de pressão', 'Decomposição rápida', 'Fogo externo'],
            'conseqs': ['Ruptura de vaso', 'BLEVE', 'Incêndio / explosão', 'Projeção de fragmentos'],
            'salvags': ['PSV', 'PAHH + trip', 'Despressurização de emergência'],
            'rec': ['Calcular API RP 521 fire case', 'Avaliar SIL 2', 'Checar capacidade de PSV'],
        },
        'MENOS': {
            'causas': ['Quebra de linha', 'Abertura inadvertida de vent', 'Vácuo por condensação'],
            'conseqs': ['Entrada de ar', 'Colapso por vácuo', 'Perda de contenção'],
            'salvags': ['PAL', 'Check valve', 'Inspeção periódica'],
            'rec': ['Adicionar proteção contra vácuo', 'Treinar operadores'],
        },
    },
    'Fluxo': {
        'NÃO / NENHUM': {
            'causas': ['Falha de bomba', 'Filtro entupido', 'Válvula fechada', 'Perda de energia'],
            'conseqs': ['Dano mecânico', 'Perda de resfriamento', 'Contaminação cruzada', 'Off-spec'],
            'salvags': ['FAL', 'Check valve', 'Bomba stand-by'],
            'rec': ['Adicionar detecção de ΔP no filtro', 'Garantir stand-by 100%'],
        },
        'MAIS': {
            'causas': ['FCV stuck open', 'Erro operacional', 'By-pass indevido'],
            'conseqs': ['Overfill', 'Slugging', 'Sobrepressão a jusante'],
            'salvags': ['FAH', 'LSH', 'LAHH'],
            'rec': ['Instalar LAHH independente', 'Executar cenário de overfill'],
        },
    },
    'Nível': {
        'MAIS': {
            'causas': ['Falha do LIC', 'Bloqueio de saída', 'Instrumento de nível com leitura baixa falsa'],
            'conseqs': ['Overflow', 'Carry-over', 'Nuvem inflamável ou tóxica'],
            'salvags': ['LAH', 'LAHH', 'Dique'],
            'rec': ['Validar arquitetura SIS', 'Revisar FMEA do medidor de nível'],
        },
        'MENOS': {
            'causas': ['Fuga de produto', 'Excesso de saída', 'Leitura alta falsa'],
            'conseqs': ['Bomba seca', 'Entrada de ar', 'Queima de resistência'],
            'salvags': ['LAL', 'LALL', 'Detector de fuga'],
            'rec': ['Ampliar inspeção de integridade', 'Adicionar detector no dique'],
        },
    },
}
