from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import pandas as pd


FAMILY_LABELS = {
    "agua_umidade": "Água / umidade",
    "oxidante": "Oxidante",
    "acido_forte": "Ácido forte",
    "base_forte": "Base forte",
    "base": "Base",
    "amonia": "Amônia / base volátil",
    "organico": "Orgânico / solvente",
    "inflamavel": "Inflamável",
    "redutor": "Redutor",
    "reativo_com_agua": "Reativo com água",
    "metal_reativo": "Metal reativo",
    "doador_cloro": "Doador de cloro / hipoclorito",
    "corrosivo": "Corrosivo",
}

SEVERITY_ORDER = {"OK": 0, "Revisar": 1, "Cuidado": 2, "Incompatível": 3}
SEVERITY_SCORE = {"OK": 10, "Revisar": 30, "Cuidado": 65, "Incompatível": 92}


def _profile_text(profile) -> str:
    parts = [
        str(profile.identity.get("name", "")),
        str(profile.identity.get("preferred_name", "")),
        str(profile.identity.get("iupac_name", "")),
        str(profile.identity.get("formula", "")),
        " ".join(profile.storage.get("incompatibilities", []) or []),
        " ".join(profile.storage.get("notes", []) or []),
    ]
    return " ".join(parts).lower()


def infer_reactivity_families(profile) -> list[str]:
    text = _profile_text(profile)
    families = set()

    if "water" in text or "água" in text or "h2o" in text:
        families.add("agua_umidade")

    oxidizer_keys = [
        "peroxide", "peróxido", "nitrate", "nitric acid", "nitric",
        "chlorate", "perchlorate", "permanganate", "hypochlorite",
        "oxidizer", "oxidante", "oxygen",
    ]
    if any(k in text for k in oxidizer_keys):
        families.add("oxidante")

    acid_keys = [
        "sulfuric acid", "ácido sulfúrico", "hydrochloric acid", "ácido clorídrico",
        "nitric acid", "ácido nítrico", "perchloric acid", "phosphoric acid",
    ]
    if any(k in text for k in acid_keys):
        families.add("acido_forte")

    strong_base_keys = [
        "sodium hydroxide", "naoh", "potassium hydroxide", "koh", "caustic soda",
        "soda cáustica",
    ]
    if any(k in text for k in strong_base_keys):
        families.add("base_forte")
        families.add("base")

    base_keys = ["amine", "amina", "ammonia", "amônia", "nh3", "ammonium hydroxide"]
    if any(k in text for k in base_keys):
        families.add("base")

    ammonia_keys = ["ammonia", "amônia", "nh3"]
    if any(k in text for k in ammonia_keys):
        families.add("amonia")

    organic_keys = [
        "ethanol", "etanol", "methanol", "metanol", "acetone", "acetona",
        "toluene", "tolueno", "benzene", "benzeno", "propane", "propano",
        "butane", "butano", "hexane", "hexano", "heptane", "heptano",
        "organic", "orgânico", "solvent", "solvente", "hydrocarbon", "hidrocarboneto",
    ]
    if any(k in text for k in organic_keys):
        families.add("organico")

    if profile.flags.get("flammable", False):
        families.add("inflamavel")
        families.add("organico")

    water_reactive_keys = [
        "sodium metal", "potassium metal", "metal hydride", "carbide",
        "water reactive", "reativo com água",
    ]
    if any(k in text for k in water_reactive_keys):
        families.add("reativo_com_agua")

    reactive_metal_keys = [
        "sodium", "potassium", "lithium", "magnesium powder",
        "aluminum powder", "metal powder",
    ]
    if any(k in text for k in reactive_metal_keys):
        families.add("metal_reativo")

    chlorine_donor_keys = [
        "hypochlorite", "hipoclorito", "bleach", "cloro", "chlorine donor",
    ]
    if any(k in text for k in chlorine_donor_keys):
        families.add("doador_cloro")

    reducer_keys = ["hydrazine", "hidrazina", "sulfite", "bisulfite", "reducing agent", "redutor"]
    if any(k in text for k in reducer_keys):
        families.add("redutor")

    if profile.flags.get("corrosive", False):
        families.add("corrosivo")

    return sorted(families)


@dataclass
class RuleHit:
    family_a: str
    family_b: str
    severity: str
    rationale: str
    mitigation: str


RULES = [
    (
        {"oxidante", "organico"},
        "Incompatível",
        "Oxidantes podem reagir intensamente com orgânicos/solventes e elevar o risco de incêndio ou decomposição.",
        "Segregar armazenagem, eliminar fontes de contaminação cruzada e revisar compatibilidade de embalagem e drenagem.",
    ),
    (
        {"oxidante", "inflamavel"},
        "Incompatível",
        "Oxidantes intensificam combustão e podem agravar rapidamente cenários de ignição.",
        "Separação física, controle de inventário, ventilação e revisão de cenários de incêndio.",
    ),
    (
        {"oxidante", "redutor"},
        "Incompatível",
        "Pares oxidante/redutor podem gerar reação exotérmica ou decomposição acelerada.",
        "Segregação total, revisão de mistura acidental e barreiras administrativas.",
    ),
    (
        {"reativo_com_agua", "agua_umidade"},
        "Incompatível",
        "Material reativo com água pode gerar calor, gás inflamável/tóxico ou reação violenta.",
        "Armazenar em seco, inertizar quando aplicável e controlar ingresso de umidade.",
    ),
    (
        {"acido_forte", "base_forte"},
        "Cuidado",
        "Contato ácido-base forte pode gerar neutralização altamente exotérmica e respingos/corrosão.",
        "Segregar, controlar transferência, definir EPI e contenção de derrame compatível.",
    ),
    (
        {"acido_forte", "amonia"},
        "Cuidado",
        "Mistura pode gerar reação ácido-base intensa e vapores irritantes/corrosivos em cenários de liberação.",
        "Separar áreas, revisar drenagem, ventilação e procedimentos de resposta.",
    ),
    (
        {"doador_cloro", "amonia"},
        "Incompatível",
        "Amônia e doadores de cloro/hipoclorito podem gerar gases perigosos e subprodutos reativos.",
        "Segregação rigorosa, prevenção de mistura em limpeza e revisão de emergência.",
    ),
    (
        {"corrosivo", "metal_reativo"},
        "Cuidado",
        "Corrosivos podem atacar metais reativos e comprometer integridade, gerando calor ou gás.",
        "Revisar materiais de construção, segregação e compatibilidade de recipientes.",
    ),
    (
        {"inflamavel", "inflamavel"},
        "Revisar",
        "Não é incompatibilidade clássica, mas aumenta carga de incêndio e severidade de eventos.",
        "Controlar inventário, ventilação, aterramento e distanciamento.",
    ),
]


def _rule_for_pair(fa: str, fb: str) -> tuple[str, str, str]:
    for famset, severity, rationale, mitigation in RULES:
        if {fa, fb} == famset:
            return severity, rationale, mitigation
    return "OK", "Nenhuma incompatibilidade forte detectada por regra de screening.", "Manter revisão por SDS/FISPQ e prática de segregação."


def evaluate_pairwise_reactivity(profile_a, profile_b) -> dict[str, Any]:
    families_a = infer_reactivity_families(profile_a)
    families_b = infer_reactivity_families(profile_b)

    if not families_a:
        families_a = ["Revisar manualmente"]
    if not families_b:
        families_b = ["Revisar manualmente"]

    hits: list[RuleHit] = []
    matrix_rows = []

    for fa in families_a:
        row = {"Família A": FAMILY_LABELS.get(fa, fa)}
        for fb in families_b:
            severity, rationale, mitigation = _rule_for_pair(fa, fb)
            row[FAMILY_LABELS.get(fb, fb)] = severity
            if severity != "OK":
                hits.append(
                    RuleHit(
                        family_a=FAMILY_LABELS.get(fa, fa),
                        family_b=FAMILY_LABELS.get(fb, fb),
                        severity=severity,
                        rationale=rationale,
                        mitigation=mitigation,
                    )
                )
        matrix_rows.append(row)

    matrix_df = pd.DataFrame(matrix_rows)
    if not matrix_df.empty:
        matrix_df = matrix_df.set_index("Família A")

    max_severity = "OK"
    for hit in hits:
        if SEVERITY_ORDER[hit.severity] > SEVERITY_ORDER[max_severity]:
            max_severity = hit.severity

    score = SEVERITY_SCORE[max_severity]
    if len(hits) >= 3:
        score = min(score + 5, 100)

    recommendations = []
    for hit in hits:
        recommendations.append(hit.mitigation)

    if not recommendations:
        recommendations.append("Não foram detectadas incompatibilidades fortes por regra de screening. Confirmar sempre por SDS/FISPQ e critérios do processo.")

    # remover duplicatas
    dedup = []
    seen = set()
    for item in recommendations:
        if item not in seen:
            seen.add(item)
            dedup.append(item)

    hits_df = pd.DataFrame(
        [
            {
                "Família A": h.family_a,
                "Família B": h.family_b,
                "Severidade": h.severity,
                "Racional": h.rationale,
                "Mitigação": h.mitigation,
            }
            for h in hits
        ]
    )

    summary = {
        "compound_a": profile_a.identity.get("name", "Composto A"),
        "compound_b": profile_b.identity.get("name", "Composto B"),
        "severity": max_severity,
        "score": score,
        "rule_hits": len(hits),
    }

    return {
        "summary": summary,
        "families_a": [FAMILY_LABELS.get(x, x) for x in families_a],
        "families_b": [FAMILY_LABELS.get(x, x) for x in families_b],
        "matrix_df": matrix_df,
        "hits_df": hits_df,
        "recommendations": dedup,
    }
