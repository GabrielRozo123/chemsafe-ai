from __future__ import annotations

BASE_REFERENCES = [
    {
        "Grupo": "Normas e standards",
        "Título": "IEC 61882:2016",
        "Observação": "Base para HAZOP: intenção de projeto, guidewords, causas, consequências, salvaguardas e ações.",
    },
    {
        "Grupo": "Normas e standards",
        "Título": "IEC 61511-1:2016 + A1:2017",
        "Observação": "Base para SIS, SIL e camadas instrumentadas de proteção.",
    },
    {
        "Grupo": "Normas e standards",
        "Título": "OSHA 29 CFR 1910.119",
        "Observação": "PSM e requisitos de process safety information antes da PHA.",
    },
    {
        "Grupo": "Normas e standards",
        "Título": "NR-20",
        "Observação": "Inflamáveis e combustíveis.",
    },
    {
        "Grupo": "Normas e standards",
        "Título": "NR-13",
        "Observação": "Caldeiras, vasos de pressão, tubulações e tanques metálicos.",
    },
    {
        "Grupo": "Bases oficiais",
        "Título": "PubChem",
        "Observação": "Identidade química, sinônimos, descritores e metadados públicos.",
    },
    {
        "Grupo": "Bases oficiais",
        "Título": "NIST Chemistry WebBook",
        "Observação": "Propriedades termodinâmicas e termofísicas.",
    },
    {
        "Grupo": "Bases oficiais",
        "Título": "NIOSH Pocket Guide",
        "Observação": "IDLH, REL, PEL, propriedades, incompatibilidades e higiene ocupacional.",
    },
    {
        "Grupo": "Bases oficiais",
        "Título": "CAMEO Chemicals",
        "Observação": "Reatividade química, resposta emergencial e hazards de mistura.",
    },
    {
        "Grupo": "Bases oficiais",
        "Título": "EPA CompTox",
        "Observação": "Exposure, hazard e dados químicos ampliados.",
    },
    {
        "Grupo": "Métodos de cálculo",
        "Título": "Pasquill-Gifford / screening gaussiano",
        "Observação": "Base para dispersão neutra simplificada no app.",
    },
    {
        "Grupo": "Métodos de cálculo",
        "Título": "Shokri-Beyler / Heskestad / screening de pool fire",
        "Observação": "Base para altura de chama, poder emissivo e fluxo no alvo.",
    },
]


def build_references(profile) -> list[dict]:
    refs = list(BASE_REFERENCES)

    if profile.flags.get("flammable"):
        refs.append(
            {
                "Grupo": "Métodos de cálculo",
                "Título": "Crowl & Louvar — incêndios, explosões e inflamabilidade",
                "Observação": "Apoio conceitual para LII/LSI, ignição, ventilação e screening de fogo/explosão.",
            }
        )

    if profile.flags.get("toxic_inhalation"):
        refs.append(
            {
                "Grupo": "Métodos de cálculo",
                "Título": "Crowl & Louvar — toxicologia e dispersão",
                "Observação": "Apoio conceitual para IDLH, exposição e screening de dispersão.",
            }
        )

    if profile.flags.get("corrosive") or profile.flags.get("reactive_hazard"):
        refs.append(
            {
                "Grupo": "Métodos de cálculo",
                "Título": "Crowl & Louvar — reatividade química e materiais",
                "Observação": "Apoio conceitual para incompatibilidade, corrosão e seleção de materiais.",
            }
        )

    return refs
