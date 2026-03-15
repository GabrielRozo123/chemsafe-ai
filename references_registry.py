from __future__ import annotations

BASE_REFERENCES = [
    {
        "group": "Normas e standards",
        "title": "IEC 61882:2016",
        "note": "Estrutura de HAZOP, intenção de projeto, guidewords, causas, consequências, salvaguardas e ações.",
    },
    {
        "group": "Normas e standards",
        "title": "IEC 61511-1:2016 + A1:2017",
        "note": "Base para SIS, SIL e camadas instrumentadas de proteção.",
    },
    {
        "group": "Normas e standards",
        "title": "OSHA 29 CFR 1910.119",
        "note": "PSM e requisitos de process safety information antes da PHA.",
    },
    {
        "group": "Normas e standards",
        "title": "NR-20",
        "note": "Inflamáveis e combustíveis.",
    },
    {
        "group": "Normas e standards",
        "title": "NR-13",
        "note": "Caldeiras, vasos de pressão, tubulações e tanques metálicos.",
    },
    {
        "group": "Fontes de dados",
        "title": "PubChem",
        "note": "Identidade química, sinônimos, CID, fórmula e metadados públicos.",
    },
    {
        "group": "Fontes de dados",
        "title": "NIST Chemistry WebBook",
        "note": "Termodinâmica, vapor pressure e propriedades termofísicas públicas.",
    },
    {
        "group": "Fontes de dados",
        "title": "NIOSH Pocket Guide",
        "note": "IDLH, REL, limites ocupacionais e incompatibilidades úteis para triagem.",
    },
    {
        "group": "Fontes de dados",
        "title": "CAMEO Chemicals",
        "note": "Incompatibilidade química, resposta emergencial e reatividade de mistura.",
    },
    {
        "group": "Fontes de dados",
        "title": "EPA CompTox Dashboard",
        "note": "Hazard, exposure e dados químicos ampliados.",
    },
]


def build_references(profile) -> list[dict]:
    refs = list(BASE_REFERENCES)

    if profile.flags.get("flammable"):
        refs.append(
            {
                "group": "Métodos e cálculos",
                "title": "Crowl & Louvar — Flammability, Fires and Explosions",
                "note": "Base conceitual para LFL/UFL, ignição, ventilação, inertização e screening de incêndio/explosão.",
            }
        )

    if profile.flags.get("toxic_inhalation"):
        refs.append(
            {
                "group": "Métodos e cálculos",
                "title": "Crowl & Louvar — Toxicology / Dispersion",
                "note": "Base conceitual para IDLH, critérios de toxicidade e screening de dispersão.",
            }
        )

    if profile.flags.get("corrosive") or profile.flags.get("reactive_hazard"):
        refs.append(
            {
                "group": "Métodos e cálculos",
                "title": "Crowl & Louvar — Chemical Reactivity / Materials",
                "note": "Base conceitual para reatividade, incompatibilidade e materiais de construção.",
            }
        )

    return refs
