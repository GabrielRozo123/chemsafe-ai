from __future__ import annotations

from typing import Any


def build_confidence_score(profile: Any) -> float:
    score = 0.0

    if profile.identity.get("name"):
        score += 10
    if profile.identity.get("formula"):
        score += 10
    if profile.identity.get("molecular_weight"):
        score += 10
    if profile.identity.get("pubchem_cid"):
        score += 10

    if profile.flags.get("flammable", False):
        if profile.prop("flash_point_c") is not None:
            score += 10
        if profile.prop("lfl_volpct") is not None and profile.prop("ufl_volpct") is not None:
            score += 10
        if profile.prop("autoignition_c") is not None:
            score += 5
    else:
        score += 10

    if profile.flags.get("toxic_inhalation", False):
        if profile.limit("IDLH_ppm") is not None or profile.limit("IDLH_mg_m3") is not None:
            score += 10
        if any(
            k in profile.exposure_limits
            for k in ["TLV_TWA_ppm", "TLV_STEL_mg_m3", "ERPG_2_ppm", "ERPG_3_ppm"]
        ):
            score += 5
    else:
        score += 10

    if profile.storage.get("incompatibilities"):
        score += 10
    if profile.reactivity:
        score += 5

    unique_sources = set()
    for row in profile.source_trace:
        src = row.get("source")
        if src:
            unique_sources.add(src)
    score += min(len(unique_sources) * 2.5, 5.0)

    return min(score, 100.0)


def build_incompatibility_matrix(profile: Any) -> list[dict]:
    incompat_text = " | ".join(profile.storage.get("incompatibilities", [])).lower()

    categorias = [
        "Água",
        "Oxidantes",
        "Ácidos fortes",
        "Bases fortes",
        "Metais reativos",
        "Fontes de ignição",
        "Orgânicos/solventes",
        "Ar/umidade",
    ]

    def classificar(rotulo: str) -> str:
        txt = incompat_text

        if rotulo == "Água":
            if "agua" in txt or "água" in txt or "water" in txt:
                return "Incompatível"
            return "Revisar"

        if rotulo == "Oxidantes":
            if "oxid" in txt:
                return "Incompatível"
            return "Revisar"

        if rotulo == "Ácidos fortes":
            if "ácido" in txt or "acido" in txt or "acid" in txt:
                return "Incompatível"
            return "Revisar"

        if rotulo == "Bases fortes":
            if "base" in txt:
                return "Incompatível"
            return "Revisar"

        if rotulo == "Metais reativos":
            if "metal" in txt or "cobre" in txt:
                return "Cuidado"
            return "Revisar"

        if rotulo == "Fontes de ignição":
            if "igni" in txt or "quente" in txt or "hot" in txt:
                return "Incompatível"
            if profile.flags.get("flammable", False):
                return "Cuidado"
            return "Revisar"

        if rotulo == "Orgânicos/solventes":
            if "orgân" in txt or "organ" in txt or "solvent" in txt:
                return "Cuidado"
            return "Revisar"

        if rotulo == "Ar/umidade":
            if "air" in txt or "moist" in txt or "umidade" in txt:
                return "Cuidado"
            return "Revisar"

        return "Revisar"

    linhas = []
    for cat in categorias:
        linhas.append({"categoria": cat, "status": classificar(cat)})
    return linhas
