from __future__ import annotations

NORMS_DB = [
    {
        "id": "OSHA 1910.119",
        "tag": "OSHA",
        "area": "PSM",
        "title": "Process Safety Management of Highly Hazardous Chemicals",
        "desc": "Requisitos regulatórios para gestão de segurança de processos em instalações com químicos perigosos.",
        "application": "PHA, MOC, PSSR, integridade mecânica, treinamento, investigação.",
        "status_note": "Base curada interna. Validar edição vigente oficial antes de uso regulatório.",
    },
    {
        "id": "IEC 61511",
        "tag": "IEC",
        "area": "SIS / SIL",
        "title": "Functional Safety for the Process Industry Sector",
        "desc": "Norma para ciclo de vida de sistemas instrumentados de segurança e verificação SIL.",
        "application": "SIF, PFDavg, proof test, arquitetura 1oo1/1oo2/2oo3.",
        "status_note": "Base curada interna. Confirmar parte/edição vigente no projeto.",
    },
    {
        "id": "IEC 61882",
        "tag": "IEC",
        "area": "PHA / HAZOP",
        "title": "Hazard and Operability Studies (HAZOP Studies)",
        "desc": "Guia para execução estruturada de estudos HAZOP.",
        "application": "Nós, desvios, causas, consequências, salvaguardas e recomendações.",
        "status_note": "Base curada interna. Validar edição oficial aplicável.",
    },
    {
        "id": "NFPA 69",
        "tag": "NFPA",
        "area": "Explosões / Inertização",
        "title": "Standard on Explosion Prevention Systems",
        "desc": "Requisitos para prevenção de explosões, inertização e concentração limite de oxidante.",
        "application": "LOC, purga, envelope de inflamabilidade e partidas/paradas.",
        "status_note": "Base curada interna. Confirmar edição oficial vigente.",
    },
    {
        "id": "API 520",
        "tag": "API",
        "area": "Alívio de Pressão",
        "title": "Sizing, Selection, and Installation of Pressure-Relieving Devices",
        "desc": "Critérios para dimensionamento e seleção de dispositivos de alívio.",
        "application": "PSV/PRV, cenários de alívio, seleção preliminar de orifício.",
        "status_note": "Base curada interna. Confirmar parte/edição oficial.",
    },
    {
        "id": "API 521",
        "tag": "API",
        "area": "Alívio de Pressão",
        "title": "Pressure-Relieving and Depressuring Systems",
        "desc": "Guia para definição de cenários, carga térmica e sistemas de despressurização.",
        "application": "Cenários de fogo, blowdown, flare, contingências de alívio.",
        "status_note": "Base curada interna. Revisar edição vigente oficial.",
    },
    {
        "id": "CCPS LOPA",
        "tag": "CCPS",
        "area": "LOPA",
        "title": "Layer of Protection Analysis",
        "desc": "Referência clássica para análise semiquantitativa de camadas independentes de proteção.",
        "application": "IPL, frequência mitigada, risco residual, decisão de barreiras.",
        "status_note": "Referência técnica curada. Verificar edição física/digital utilizada pela equipe.",
    },
    {
        "id": "CCPS RBPS",
        "tag": "CCPS",
        "area": "Governança PSM",
        "title": "Risk Based Process Safety",
        "desc": "Estrutura de pilares e elementos de gestão para segurança de processos.",
        "application": "Governança, indicadores, cultura, integridade e ciclo de melhoria.",
        "status_note": "Referência técnica curada. Confirmar versão institucional adotada.",
    },
    {
        "id": "AACE Class 5",
        "tag": "AACE",
        "area": "Estimativa de Custos",
        "title": "Class 5 Estimate",
        "desc": "Faixa conceitual de estimativa em estágio inicial para apoio à decisão.",
        "application": "Order-of-magnitude, estimativas preliminares CAPEX/OPEX.",
        "status_note": "Modelo referencial curado. Ajustar à prática interna da empresa.",
    },
    {
        "id": "CCPS Guidelines for Chemical Reactivity Evaluation",
        "tag": "CCPS",
        "area": "Reatividade",
        "title": "Chemical Reactivity Evaluation and Application",
        "desc": "Diretrizes para avaliação de incompatibilidade, runaway e riscos reativos.",
        "application": "Triagem reativa, incompatibilidades e cenários térmicos.",
        "status_note": "Referência técnica curada. Validar edição consultada.",
    },
]

NORMS_LOOKUP = {item["id"]: item for item in NORMS_DB}

MODULE_GOVERNANCE = {
    "Visão Executiva": {
        "basis": "Consolidação executiva baseada em KPIs do caso, criticidade, plano de ação consolidado e estimativas conceituais de investimento.",
        "refs": ["CCPS RBPS", "OSHA 1910.119", "AACE Class 5"],
        "confidence": "Alta",
    },
    "Engenharia": {
        "basis": "Resultados de engenharia baseados em propriedades do composto, envelopes de inflamabilidade e cálculos determinísticos preliminares.",
        "refs": ["NFPA 69", "API 520", "API 521", "CCPS Guidelines for Chemical Reactivity Evaluation"],
        "confidence": "Alta",
    },
    "Análise de Risco": {
        "basis": "Estruturação de cenários, desvios e barreiras com leitura técnica voltada a PHA, SIF e análise semiquantitativa.",
        "refs": ["IEC 61882", "IEC 61511", "CCPS LOPA"],
        "confidence": "Alta",
    },
    "Mudanças": {
        "basis": "Fluxo de governança para mudança e pré-partida segura com foco em integridade operacional e rastreabilidade.",
        "refs": ["OSHA 1910.119", "CCPS RBPS"],
        "confidence": "Média-Alta",
    },
    "Base de Conhecimento": {
        "basis": "Consulta curada de normas, referências e incidentes para suporte à decisão em engenharia e PSM.",
        "refs": ["API 520", "API 521", "OSHA 1910.119", "IEC 61511", "IEC 61882", "NFPA 69", "CCPS LOPA"],
        "confidence": "Alta",
    },
}
