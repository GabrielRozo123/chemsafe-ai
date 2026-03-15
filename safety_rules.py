from __future__ import annotations

from typing import Any


def build_confidence_score(profile: Any) -> float:
    score = 0.0

    # identidade
    if profile.identity.get("name"):
        score += 10
    if profile.identity.get("formula"):
        score += 10
    if profile.identity.get("molecular_weight"):
        score += 10
    if profile.identity.get("pubchem_cid"):
        score += 10

    # inflamabilidade
    if profile.flags.get("flammable", False):
        if profile.prop("flash_point_c") is not None:
            score += 10
        if profile.prop("lfl_volpct") is not None and profile.prop("ufl_volpct") is not None:
            score += 10
        if profile.prop("autoignition_c") is not None:
            score += 5
    else:
        score += 10

    # toxicidade
    if profile.flags.get("toxic_inhalation", False):
        if profile.limit("IDLH_ppm") is not None or profile.limit("IDLH_mg_m3") is not None:
            score += 10
        if any(k in profile.exposure_limits for k in ["TLV_TWA_ppm", "TLV_STEL_mg_m3", "ERPG_2_ppm", "ERPG_3_ppm"]):
            score += 5
    else:
        score += 10

    # reatividade / incompatibilidade
    if profile.storage.get("incompatibilities"):
        score += 10
    if profile.reactivity:
        score += 5

    # diversidade de fonte
    unique_sources = set()
    for row in profile.source_trace:
        src = row.get("source")
        if src:
            unique_sources.add(src)
    score += min(len(unique_sources) * 2.5, 5.0)

    return min(score, 100.0)


def build_incompatibility_matrix(profile: Any) -> list[dict]:
    incompat_text = " | ".join(profile.storage.get("incompatibilities", [])).lower()

    categories = [
        "Water",
        "Oxidizers",
        "Strong Acids",
        "Strong Bases",
        "Reactive Metals",
        "Ignition Sources",
        "Organics/Solvents",
        "Air/Moisture",
    ]

    def classify(label: str) -> str:
        txt = incompat_text
        if label == "Water":
            if "agua" in txt or "água" in txt or "water" in txt:
                return "Incompatible"
            return "Review"
        if label == "Oxidizers":
            if "oxid" in txt:
                return "Incompatible"
            return "Review"
        if label == "Strong Acids":
            if "ácido" in txt or "acido" in txt or "acid" in txt:
                return "Incompatible"
            return "Review"
        if label == "Strong Bases":
            if "base" in txt:
                return "Incompatible"
            return "Review"
        if label == "Reactive Metals":
            if "metal" in txt or "cobre" in txt:
                return "Caution"
            return "Review"
        if label == "Ignition Sources":
            if "igni" in txt or "quente" in txt or "hot" in txt:
                return "Incompatible"
            if profile.flags.get("flammable", False):
                return "Caution"
            return "Review"
        if label == "Organics/Solvents":
            if "orgân" in txt or "organ" in txt or "solvent" in txt:
                return "Caution"
            return "Review"
        if label == "Air/Moisture":
            if "air" in txt or "moist" in txt or "umidade" in txt:
                return "Caution"
            return "Review"
        return "Review"

    rows = []
    for cat in categories:
        rows.append({"category": cat, "status": classify(cat)})
    return rows
