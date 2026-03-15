from __future__ import annotations

from typing import Any, Dict, Optional

from chemicals_seed import LOCAL_COMPOUNDS
from compound_profile import CompoundProfile, PropertyValue
from niosh_client import fetch_niosh_record
from nist_client import fetch_nist_record
from pubchem_client import fetch_pubchem_record
from references_registry import build_references
from safety_rules import build_confidence_score, build_incompatibility_matrix
from source_links import build_official_source_links


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
        .replace(" ", "")
        .replace("-", "")
    )


def _pv(value: Any, unit: str = "", source: str = "", confidence: str = "seed") -> PropertyValue:
    return PropertyValue(value=value, unit=unit, source=source, confidence=confidence)


def resolve_local_compound(query: str) -> Optional[Dict[str, Any]]:
    q = _normalize(query)
    for _, item in LOCAL_COMPOUNDS.items():
        aliases = [_normalize(a) for a in item.get("aliases", [])]
        identity = item.get("identity", {})
        candidates = aliases + [
            _normalize(identity.get("name", "")),
            _normalize(identity.get("preferred_name", "")),
            _normalize(identity.get("cas", "")),
            _normalize(identity.get("formula", "")),
        ]
        if q in candidates:
            return item
    return None


def _bool_flag_from_hazards(hazards: list[str], codes: list[str], contains: list[str]) -> bool:
    text = " | ".join(hazards).lower()
    return any(code.lower() in text for code in codes) or any(word.lower() in text for word in contains)


def _merge_missing_physchem(profile: CompoundProfile, key: str, value: Any, unit: str, source: str) -> None:
    if value is None:
        return
    if key not in profile.physchem or profile.physchem[key].value in [None, ""]:
        profile.physchem[key] = _pv(value, unit, source, "live")


def _merge_missing_limit(profile: CompoundProfile, key: str, value: Any, unit: str, source: str) -> None:
    if value is None:
        return
    if key not in profile.exposure_limits or profile.exposure_limits[key].value in [None, ""]:
        profile.exposure_limits[key] = _pv(value, unit, source, "live")


def _recompute_flags(profile: CompoundProfile) -> None:
    hazards = profile.hazards or []
    profile.flags = {
        "flammable": bool(
            profile.prop("flash_point_c") is not None
            or profile.prop("lfl_volpct") is not None
            or profile.nfpa.get("fire", 0) >= 3
            or _bool_flag_from_hazards(hazards, ["H220", "H221", "H225"], ["inflam"])
        ),
        "toxic_inhalation": bool(
            profile.limit("IDLH_ppm") is not None
            or profile.limit("IDLH_mg_m3") is not None
            or _bool_flag_from_hazards(hazards, ["H330", "H331"], ["toxico por inala", "toxic by inhal"])
        ),
        "corrosive": bool(
            profile.reactivity.get("corrosive", False)
            or _bool_flag_from_hazards(hazards, ["H314", "H290"], ["corros"])
        ),
        "pressurized": bool(
            profile.reactivity.get("pressurized", False)
            or (profile.prop("boiling_point_c") is not None and profile.prop("boiling_point_c") < -20)
        ),
        "reactive_hazard": bool(profile.reactivity.get("reactive_hazard", False)),
    }


def _score_flammability(profile: CompoundProfile) -> float:
    score = float(profile.nfpa.get("fire", 0) or 0.5)
    flash = profile.prop("flash_point_c")
    lfl = profile.prop("lfl_volpct")
    if flash is not None and flash < 25:
        score = max(score, 4.0)
    if lfl is not None and lfl <= 5:
        score = max(score, 4.0)
    if lfl is not None and profile.prop("ufl_volpct") is not None:
        score = max(score, 3.0)
    return min(score if score > 0 else 0.5, 4.0)


def _score_toxicity(profile: CompoundProfile) -> float:
    score = float(profile.nfpa.get("health", 0) or 0.5)
    idlh = profile.limit("IDLH_ppm")
    if idlh is not None:
        if idlh <= 100:
            score = max(score, 4.0)
        elif idlh <= 300:
            score = max(score, 3.5)
        elif idlh <= 1000:
            score = max(score, 2.5)
    return min(score if score > 0 else 0.5, 4.0)


def _score_pressure(profile: CompoundProfile) -> float:
    if profile.flags.get("pressurized"):
        return 4.0
    bp = profile.prop("boiling_point_c")
    if bp is not None and bp < 0:
        return 3.5
    return 0.5


def _score_corrosivity(profile: CompoundProfile) -> float:
    return 4.0 if profile.flags.get("corrosive") else 0.5


def _score_reactivity(profile: CompoundProfile) -> float:
    if profile.flags.get("reactive_hazard"):
        return 3.5
    return float(profile.nfpa.get("reactivity", 0) or 0.5)


def _score_volatility(profile: CompoundProfile) -> float:
    vp = profile.prop("vapor_pressure_kpa_20c")
    if vp is None:
        vp = profile.prop("vapor_pressure_kpa")
    bp = profile.prop("boiling_point_c")

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


def _build_routing(profile: CompoundProfile) -> list[str]:
    routing = []
    if profile.flags.get("flammable"):
        routing += ["HAZOP: ignição e perda de contenção", "Pool fire screening", "Ventilação e controle de ignição"]
    if profile.flags.get("toxic_inhalation"):
        routing += ["Dispersão tóxica", "Detecção e evacuação", "Isolamento e contenção"]
    if profile.flags.get("corrosive"):
        routing += ["Materiais de construção", "Integridade mecânica", "Containment / eyewash / shower"]
    if profile.flags.get("pressurized"):
        routing += ["Relief / sobrepressão / bloqueio", "Isolamento remoto", "Fire case / escalonamento"]
    if profile.flags.get("reactive_hazard"):
        routing += ["Incompatibilidade química", "Contaminação cruzada", "Revisão de reação / runaway"]
    if not routing:
        routing = ["Buscar pacote adicional de dados antes do screening detalhado"]
    return list(dict.fromkeys(routing))


def _build_readiness(profile: CompoundProfile) -> list[dict]:
    checks = []

    checks.append(
        {
            "check": "Identidade química",
            "status": "OK" if profile.identity.get("formula") and profile.identity.get("molecular_weight") else "GAP",
            "detail": "Nome, fórmula, MW e identificadores",
        }
    )

    flammable = profile.flags.get("flammable", False)
    toxic = profile.flags.get("toxic_inhalation", False)
    corrosive = profile.flags.get("corrosive", False)

    flamm_ok = all(profile.prop(k) is not None for k in ["lfl_volpct", "autoignition_c"]) if flammable else True
    tox_ok = (profile.limit("IDLH_ppm") is not None or profile.limit("IDLH_mg_m3") is not None) if toxic else True
    corr_ok = bool(profile.storage.get("incompatibilities")) if corrosive else True

    checks.append(
        {
            "check": "Pacote de inflamabilidade",
            "status": "OK" if flamm_ok else "GAP",
            "detail": "LFL/UFL, flash point, AIT",
        }
    )
    checks.append(
        {
            "check": "Pacote de toxicidade/exposição",
            "status": "OK" if tox_ok else "GAP",
            "detail": "IDLH, REL/PEL/STEL/ERPG/AEGL quando aplicável",
        }
    )
    checks.append(
        {
            "check": "Reatividade/compatibilidade",
            "status": "OK" if corr_ok else "GAP",
            "detail": "Corrosividade, incompatibilidades e materiais",
        }
    )
    checks.append(
        {
            "check": "Roteamento de cenários",
            "status": "OK" if profile.routing else "GAP",
            "detail": "HAZOP, LOPA e consequence modules priorizados",
        }
    )

    return checks


def _apply_live_enrichment(profile: CompoundProfile, nist: Dict[str, Any], niosh: Dict[str, Any]) -> None:
    if nist:
        _merge_missing_physchem(profile, "boiling_point_c", nist.get("boiling_point_c"), "°C", "NIST WebBook")
        _merge_missing_physchem(profile, "melting_point_c", nist.get("melting_point_c"), "°C", "NIST WebBook")
        _merge_missing_physchem(profile, "vapor_pressure_kpa", nist.get("vapor_pressure_kpa"), "kPa", "NIST WebBook")

    if niosh:
        _merge_missing_physchem(profile, "boiling_point_c", niosh.get("boiling_point_c"), "°C", "NIOSH Pocket Guide")
        _merge_missing_physchem(profile, "flash_point_c", niosh.get("flash_point_c"), "°C", "NIOSH Pocket Guide")
        _merge_missing_physchem(profile, "vapor_pressure_kpa", niosh.get("vapor_pressure_kpa"), "kPa", "NIOSH Pocket Guide")
        _merge_missing_physchem(profile, "lfl_volpct", niosh.get("lfl_volpct"), "%vol", "NIOSH Pocket Guide")
        _merge_missing_physchem(profile, "ufl_volpct", niosh.get("ufl_volpct"), "%vol", "NIOSH Pocket Guide")

        _merge_missing_limit(profile, "IDLH_ppm", niosh.get("IDLH_ppm"), "ppm", "NIOSH Pocket Guide")
        _merge_missing_limit(profile, "REL_TWA_ppm", niosh.get("REL_TWA_ppm"), "ppm", "NIOSH Pocket Guide")
        _merge_missing_limit(profile, "REL_ST_ppm", niosh.get("REL_ST_ppm"), "ppm", "NIOSH Pocket Guide")
        _merge_missing_limit(profile, "OSHA_PEL_TWA_ppm", niosh.get("OSHA_PEL_TWA_ppm"), "ppm", "NIOSH Pocket Guide")

        if not profile.storage.get("incompatibilities") and niosh.get("incompatibilities"):
            profile.storage["incompatibilities"] = niosh.get("incompatibilities", [])


def _build_generic_profile(query: str, pubchem: Dict[str, Any], nist: Dict[str, Any], niosh: Dict[str, Any]) -> Optional[CompoundProfile]:
    if not pubchem:
        return None

    profile = CompoundProfile()
    profile.identity = {
        "name": pubchem.get("title") or query.title(),
        "preferred_name": pubchem.get("title") or query.title(),
        "cas": "",
        "formula": pubchem.get("molecular_formula"),
        "molecular_weight": pubchem.get("molecular_weight"),
        "pubchem_cid": pubchem.get("cid"),
        "iupac_name": pubchem.get("iupac_name"),
        "smiles": pubchem.get("canonical_smiles"),
        "inchikey": pubchem.get("inchikey"),
        "xlogp": pubchem.get("xlogp"),
        "tpsa": pubchem.get("tpsa"),
        "hbd": pubchem.get("hbd"),
        "hba": pubchem.get("hba"),
        "complexity": pubchem.get("complexity"),
    }

    profile.hazards = []
    profile.nfpa = {"health": 0, "fire": 0, "reactivity": 0, "special": ""}

    if pubchem.get("xlogp") is not None:
        profile.physchem["xlogp"] = _pv(pubchem["xlogp"], "", "PubChem", "live")
    if pubchem.get("molecular_weight") is not None:
        profile.physchem["molecular_weight"] = _pv(pubchem["molecular_weight"], "g/mol", "PubChem", "live")

    profile.reactivity = {
        "corrosive": False,
        "pressurized": False,
        "reactive_hazard": False,
        "incompatibilities": [],
        "notes": [
            "Perfil genérico gerado a partir de lookup universal.",
            "Completar com dados adicionais antes de um screening aprofundado.",
        ],
    }
    profile.storage = {
        "incompatibilities": [],
        "notes": profile.reactivity["notes"],
    }

    _apply_live_enrichment(profile, nist, niosh)

    profile.source_trace = [{"field": "identity_descriptors", "source": "PubChem PUG REST"}]
    if nist:
        profile.source_trace.append({"field": "thermophysical", "source": "NIST WebBook"})
    if niosh:
        profile.source_trace.append({"field": "occupational_hygiene", "source": "NIOSH Pocket Guide"})

    _recompute_flags(profile)
    profile.fingerprint = {
        "flammability": _score_flammability(profile),
        "toxicity": _score_toxicity(profile),
        "pressure": _score_pressure(profile),
        "corrosivity": _score_corrosivity(profile),
        "reactivity": _score_reactivity(profile),
        "volatility": _score_volatility(profile),
    }
    profile.routing = _build_routing(profile)

    profile.storage["official_links"] = build_official_source_links(profile)
    profile.references = build_references(profile)
    profile.incompatibility_matrix = build_incompatibility_matrix(profile)
    profile.readiness = _build_readiness(profile)
    profile.confidence_score = build_confidence_score(profile)

    gaps = []
    if profile.flags.get("flammable") and profile.prop("autoignition_c") is None:
        gaps.append("Faltando temperatura de autoignição.")
    if profile.flags.get("toxic_inhalation") and profile.limit("IDLH_ppm") is None:
        gaps.append("Faltando IDLH.")
    if not nist and not niosh:
        gaps.append("Sem enriquecimento NIST/NIOSH para este composto.")
    profile.validation_gaps = gaps

    return profile


def build_compound_profile(query: str) -> Optional[CompoundProfile]:
    seed = resolve_local_compound(query)

    if seed is None:
        pubchem = fetch_pubchem_record(query)
        nist = fetch_nist_record(name=query, cas="")
        niosh = fetch_niosh_record(name=query, cas="")
        return _build_generic_profile(query, pubchem, nist, niosh)

    pubchem = fetch_pubchem_record(seed["identity"]["cas"] or seed["identity"]["name"])
    nist = fetch_nist_record(name=seed["identity"]["preferred_name"], cas=seed["identity"]["cas"])
    niosh = fetch_niosh_record(name=seed["identity"]["preferred_name"], cas=seed["identity"]["cas"])

    profile = CompoundProfile()
    profile.identity = {
        "name": seed["identity"]["name"],
        "preferred_name": seed["identity"]["preferred_name"],
        "cas": seed["identity"]["cas"],
        "formula": pubchem.get("molecular_formula", seed["identity"]["formula"]),
        "molecular_weight": pubchem.get("molecular_weight", seed["identity"]["molecular_weight"]),
        "pubchem_cid": pubchem.get("cid"),
        "iupac_name": pubchem.get("iupac_name"),
        "smiles": pubchem.get("canonical_smiles"),
        "inchikey": pubchem.get("inchikey"),
        "xlogp": pubchem.get("xlogp"),
        "tpsa": pubchem.get("tpsa"),
        "hbd": pubchem.get("hbd"),
        "hba": pubchem.get("hba"),
        "complexity": pubchem.get("complexity"),
    }

    profile.hazards = list(seed.get("hazards", []))
    profile.nfpa = dict(seed.get("nfpa", {}))

    for key, meta in seed.get("physchem", {}).items():
        profile.physchem[key] = _pv(meta.get("value"), meta.get("unit", ""), meta.get("source", "local_seed"), "seed")

    for key, meta in seed.get("exposure_limits", {}).items():
        profile.exposure_limits[key] = _pv(meta.get("value"), meta.get("unit", ""), meta.get("source", "local_seed"), "seed")

    if pubchem.get("xlogp") is not None:
        profile.physchem["xlogp"] = _pv(pubchem["xlogp"], "", "PubChem", "live")

    profile.reactivity = dict(seed.get("reactivity", {}))
    profile.storage = {
        "incompatibilities": seed.get("reactivity", {}).get("incompatibilities", []),
        "notes": seed.get("reactivity", {}).get("notes", []),
        "official_links": {},  # preenchido abaixo
    }

    _apply_live_enrichment(profile, nist, niosh)

    profile.source_trace = [{"field": "identity_descriptors", "source": pubchem.get("source", "local_seed")}]
    if nist:
        profile.source_trace.append({"field": "thermophysical", "source": "NIST WebBook"})
    if niosh:
        profile.source_trace.append({"field": "occupational_hygiene", "source": "NIOSH Pocket Guide"})
    profile.source_trace.append({"field": "process_safety_seed", "source": "local_seed"})

    _recompute_flags(profile)
    profile.fingerprint = {
        "flammability": _score_flammability(profile),
        "toxicity": _score_toxicity(profile),
        "pressure": _score_pressure(profile),
        "corrosivity": _score_corrosivity(profile),
        "reactivity": _score_reactivity(profile),
        "volatility": _score_volatility(profile),
    }
    profile.routing = _build_routing(profile)

    profile.storage["official_links"] = build_official_source_links(profile)
    profile.references = build_references(profile)
    profile.incompatibility_matrix = build_incompatibility_matrix(profile)
    profile.readiness = _build_readiness(profile)
    profile.confidence_score = build_confidence_score(profile)

    gaps = []
    if profile.flags.get("flammable") and profile.prop("autoignition_c") is None:
        gaps.append("Faltando temperatura de autoignição.")
    if profile.flags.get("toxic_inhalation") and profile.limit("IDLH_ppm") is None and profile.limit("IDLH_mg_m3") is None:
        gaps.append("Faltando IDLH.")
    if profile.flags.get("corrosive") and not profile.storage.get("incompatibilities"):
        gaps.append("Faltando incompatibilidades relevantes.")
    profile.validation_gaps = gaps

    return profile


def suggest_hazop_priorities(profile: CompoundProfile, equipment: str) -> list[dict]:
    items = []

    if profile.flags.get("flammable"):
        items.append(
            {
                "priority": "Alta",
                "focus": "Ignição / atmosfera inflamável",
                "why": "Flash point, LFL/UFL ou NFPA fire indicam risco relevante de incêndio/explosão.",
                "severity_score": 4,
                "likelihood_score": 3,
            }
        )

    if profile.flags.get("toxic_inhalation"):
        items.append(
            {
                "priority": "Alta",
                "focus": "Perda de contenção / toxic release",
                "why": "IDLH e hazard statements sugerem impacto ocupacional/comunitário relevante.",
                "severity_score": 5,
                "likelihood_score": 3,
            }
        )

    if profile.flags.get("pressurized"):
        items.append(
            {
                "priority": "Alta",
                "focus": "Sobrepressão / isolamento / alívio",
                "why": "Serviço pressurizado aumenta relevância de bloqueio, fire case e falha de alívio.",
                "severity_score": 4,
                "likelihood_score": 3,
            }
        )

    if profile.flags.get("corrosive"):
        items.append(
            {
                "priority": "Média-Alta",
                "focus": "Integridade mecânica / materiais",
                "why": "Corrosividade exige olhar para vedação, flange, corrosão e materiais compatíveis.",
                "severity_score": 4,
                "likelihood_score": 2,
            }
        )

    if profile.flags.get("reactive_hazard"):
        items.append(
            {
                "priority": "Média-Alta",
                "focus": "Contaminação / incompatibilidade",
                "why": "Reatividade exige desvio ALSO AS / OTHER THAN / mistura inadvertida.",
                "severity_score": 5,
                "likelihood_score": 2,
            }
        )

    if not items:
        items.append(
            {
                "priority": "Média",
                "focus": "Condições operacionais básicas",
                "why": "Sem sinais dominantes, começar por flow, pressure, level, temperature e composition.",
                "severity_score": 3,
                "likelihood_score": 2,
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
