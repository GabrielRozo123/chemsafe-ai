from __future__ import annotations

import math
from typing import Any, Dict, Optional

import requests

from chemicals_seed import LOCAL_COMPOUNDS
from compound_profile import CompoundProfile, PropertyValue
from references_registry import build_references


def _normalize(text: str) -> str:
    return (
        text.strip()
        .lower()
        .replace("á", "a")
        .replace("ã", "a")
        .replace("â", "a")
        .replace("é", "e")
        .replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ô", "o")
        .replace("õ", "o")
        .replace("ú", "u")
        .replace("ç", "c")
    )


def resolve_local_compound(query: str) -> Optional[Dict[str, Any]]:
    q = _normalize(query)
    for _, item in LOCAL_COMPOUNDS.items():
        aliases = [_normalize(a) for a in item.get("aliases", [])]
        if q in aliases:
            return item
    return None


def fetch_pubchem_identity(query: str) -> Dict[str, Any]:
    try:
        q = requests.utils.quote(query)
        cid_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{q}/cids/JSON"
        r = requests.get(cid_url, timeout=6)
        r.raise_for_status()
        cid = r.json()["IdentifierList"]["CID"][0]

        prop_url = (
            "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/"
            f"{cid}/property/Title,IUPACName,MolecularFormula,MolecularWeight/JSON"
        )
        pr = requests.get(prop_url, timeout=6)
        pr.raise_for_status()
        props = pr.json()["PropertyTable"]["Properties"][0]

        return {
            "cid": cid,
            "title": props.get("Title"),
            "iupac_name": props.get("IUPACName"),
            "molecular_formula": props.get("MolecularFormula"),
            "molecular_weight": props.get("MolecularWeight"),
            "source": "PubChem PUG REST",
        }
    except Exception:
        return {}


def _pv(value: Any, unit: str = "", source: str = "", confidence: str = "seed") -> PropertyValue:
    return PropertyValue(value=value, unit=unit, source=source, confidence=confidence)


def _score_flammability(seed: Dict[str, Any]) -> float:
    nfpa_fire = seed["nfpa"]["fire"]
    flash = seed.get("physchem", {}).get("flash_point_c", {}).get("value")
    lfl = seed.get("physchem", {}).get("lfl_volpct", {}).get("value")
    score = float(nfpa_fire)
    if flash is not None and flash < 25:
        score = max(score, 4.0)
    if lfl is not None and lfl <= 5:
        score = max(score, 4.0)
    return min(score, 4.0)


def _score_toxicity(seed: Dict[str, Any]) -> float:
    idlh = seed.get("exposure_limits", {}).get("IDLH_ppm", {}).get("value")
    nfpa_h = seed["nfpa"]["health"]
    score = float(nfpa_h)
    if idlh is not None:
        if idlh <= 100:
            score = max(score, 4.0)
        elif idlh <= 300:
            score = max(score, 3.5)
        elif idlh <= 1000:
            score = max(score, 2.5)
    return min(score, 4.0)


def _score_pressure(seed: Dict[str, Any]) -> float:
    pressurized = seed.get("reactivity", {}).get("pressurized", False)
    bp = seed.get("physchem", {}).get("boiling_point_c", {}).get("value")
    if pressurized:
        return 4.0
    if bp is not None and bp < 0:
        return 3.5
    return 0.5


def _score_corrosivity(seed: Dict[str, Any]) -> float:
    return 4.0 if seed.get("reactivity", {}).get("corrosive", False) else 0.5


def _score_reactivity(seed: Dict[str, Any]) -> float:
    if seed.get("reactivity", {}).get("reactive_hazard", False):
        return 3.5
    return float(seed["nfpa"]["reactivity"])


def _score_volatility(seed: Dict[str, Any]) -> float:
    vp = seed.get("physchem", {}).get("vapor_pressure_kpa_20c", {}).get("value")
    bp = seed.get("physchem", {}).get("boiling_point_c", {}).get("value")
    if vp is not None:
        if vp >= 20:
            return 4.0
        if vp >= 5:
            return 3.0
        if vp >= 1:
            return 2.0
    if bp is not None and bp < 40:
        return 3.0
    return 1.0


def build_compound_profile(query: str) -> Optional[CompoundProfile]:
    seed = resolve_local_compound(query)
    if seed is None:
        return None

    pubchem = fetch_pubchem_identity(seed["identity"]["cas"])

    profile = CompoundProfile()
    profile.identity = {
        "name": seed["identity"]["name"],
        "preferred_name": seed["identity"]["preferred_name"],
        "cas": seed["identity"]["cas"],
        "formula": pubchem.get("molecular_formula", seed["identity"]["formula"]),
        "molecular_weight": pubchem.get("molecular_weight", seed["identity"]["molecular_weight"]),
        "pubchem_cid": pubchem.get("cid"),
        "iupac_name": pubchem.get("iupac_name"),
    }

    profile.hazards = list(seed.get("hazards", []))
    profile.nfpa = dict(seed.get("nfpa", {}))

    for key, meta in seed.get("physchem", {}).items():
        profile.physchem[key] = _pv(
            meta.get("value"),
            meta.get("unit", ""),
            meta.get("source", "local_seed"),
            "seed",
        )

    for key, meta in seed.get("exposure_limits", {}).items():
        profile.exposure_limits[key] = _pv(
            meta.get("value"),
            meta.get("unit", ""),
            meta.get("source", "local_seed"),
            "seed",
        )

    profile.reactivity = dict(seed.get("reactivity", {}))
    profile.storage = {
        "incompatibilities": seed.get("reactivity", {}).get("incompatibilities", []),
        "notes": seed.get("reactivity", {}).get("notes", []),
    }

    flammable = bool(profile.prop("flash_point_c") is not None or profile.prop("lfl_volpct") is not None or profile.nfpa.get("fire", 0) >= 3)
    toxic_inhalation = bool(profile.limit("IDLH_ppm") is not None or profile.limit("IDLH_mg_m3") is not None or any("toxico por inala" in h.lower() or "toxic" in h.lower() for h in profile.hazards))
    corrosive = bool(profile.reactivity.get("corrosive"))
    pressurized = bool(profile.reactivity.get("pressurized"))
    reactive_hazard = bool(profile.reactivity.get("reactive_hazard"))

    profile.flags = {
        "flammable": flammable,
        "toxic_inhalation": toxic_inhalation,
        "corrosive": corrosive,
        "pressurized": pressurized,
        "reactive_hazard": reactive_hazard,
    }

    profile.fingerprint = {
        "flammability": _score_flammability(seed),
        "toxicity": _score_toxicity(seed),
        "pressure": _score_pressure(seed),
        "corrosivity": _score_corrosivity(seed),
        "reactivity": _score_reactivity(seed),
        "volatility": _score_volatility(seed),
    }

    routing = []
    if flammable:
        routing += ["HAZOP com foco em ignição e perda de contenção", "Pool fire screening", "Ventilação e fontes de ignição"]
    if toxic_inhalation:
        routing += ["Dispersão tóxica", "Detecção e evacuação", "Isolamento e contenção"]
    if corrosive:
        routing += ["Materiais de construção", "Integridade mecânica", "Containment / showers / eyewash"]
    if pressurized:
        routing += ["Relief / sobrepressão / bloqueio", "Isolamento remoto", "Fire case / escalonamento"]
    if reactive_hazard:
        routing += ["Incompatibilidade química", "Contaminação cruzada", "Revisão de reação / runaway"]
    profile.routing = list(dict.fromkeys(routing))

    gaps = []
    if flammable and profile.prop("lfl_volpct") is None:
        gaps.append("Faltando LFL para screening de inflamabilidade.")
    if flammable and profile.prop("autoignition_c") is None:
        gaps.append("Faltando autoignition temperature.")
    if toxic_inhalation and profile.limit("IDLH_ppm") is None and profile.limit("IDLH_mg_m3") is None:
        gaps.append("Faltando IDLH para toxic screening.")
    if pressurized and profile.prop("boiling_point_c") is None:
        gaps.append("Faltando boiling point para avaliar volatilidade/pressurização.")
    if corrosive and not profile.storage.get("incompatibilities"):
        gaps.append("Faltando incompatibilidades relevantes para composto corrosivo.")
    profile.validation_gaps = gaps

    profile.source_trace = [
        {"field": "identity", "source": "PubChem PUG REST" if pubchem else "local_seed"},
        {"field": "physchem", "source": "local_seed"},
        {"field": "exposure_limits", "source": "local_seed"},
        {"field": "reactivity", "source": "local_seed"},
    ]

    profile.references = build_references(profile)
    return profile


def suggest_hazop_priorities(profile: CompoundProfile, equipment: str) -> list[dict]:
    items = []

    if profile.flags.get("flammable"):
        items.append(
            {
                "priority": "Alta",
                "focus": "Ignição / atmosfera inflamável",
                "why": "Flash point, LFL/UFL ou NFPA fire indicam risco relevante de incêndio/explosão.",
            }
        )

    if profile.flags.get("toxic_inhalation"):
        items.append(
            {
                "priority": "Alta",
                "focus": "Perda de contenção / toxic release",
                "why": "IDLH e hazard statements sugerem impacto ocupacional/comunitário relevante.",
            }
        )

    if profile.flags.get("pressurized"):
        items.append(
            {
                "priority": "Alta",
                "focus": "Sobrepressão / isolamento / alívio",
                "why": "Serviço pressurizado aumenta relevância de bloqueio, fire case e falha de alívio.",
            }
        )

    if profile.flags.get("corrosive"):
        items.append(
            {
                "priority": "Média-Alta",
                "focus": "Integridade mecânica / materiais",
                "why": "Corrosividade exige olhar para vedação, flange, corrosão e materiais compatíveis.",
            }
        )

    if profile.flags.get("reactive_hazard"):
        items.append(
            {
                "priority": "Média-Alta",
                "focus": "Contaminação / incompatibilidade",
                "why": "Reatividade exige desvio do tipo ALSO AS / OTHER THAN / mistura inadvertida.",
            }
        )

    if not items:
        items.append(
            {
                "priority": "Média",
                "focus": "Condições operacionais básicas",
                "why": "Sem sinais dominantes, começar por flow, pressure, level, temperature e composition.",
            }
        )

    return items


def suggest_lopa_ipls(profile: CompoundProfile) -> list[str]:
    ipls = []

    if profile.flags.get("flammable"):
        ipls += [
            "Detecção de gás inflamável",
            "Aterramento / bonding / controle de ignição",
            "Dique / contenção secundária",
            "Sistema fixo de combate a incêndio",
        ]

    if profile.flags.get("toxic_inhalation"):
        ipls += [
            "Detecção específica do tóxico",
            "Alarmes de evacuação",
            "Isolamento remoto / ESD",
            "Ventilação / abatimento quando aplicável",
        ]

    if profile.flags.get("pressurized"):
        ipls += [
            "PSV / disco de ruptura",
            "PAHH com trip",
            "Inspeção periódica de integridade",
        ]

    if profile.flags.get("corrosive"):
        ipls += [
            "Materiais compatíveis",
            "Programa de inspeção e espessimetria",
            "Containment / eyewash / shower",
        ]

    return list(dict.fromkeys(ipls))
