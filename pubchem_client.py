from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List, Optional

import requests

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


def _safe_get(url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


@lru_cache(maxsize=512)
def _get_first_cid_from_name(query: str) -> Optional[int]:
    data = _safe_get(f"{PUBCHEM_BASE}/compound/name/{requests.utils.quote(query)}/cids/JSON")
    if not data:
        return None
    try:
        return data["IdentifierList"]["CID"][0]
    except Exception:
        return None


@lru_cache(maxsize=512)
def _get_first_cid_from_formula(query: str) -> Optional[int]:
    data = _safe_get(f"{PUBCHEM_BASE}/compound/fastformula/{requests.utils.quote(query)}/cids/JSON")
    if not data:
        return None
    try:
        return data["IdentifierList"]["CID"][0]
    except Exception:
        return None


def _normalize_formula_candidate(text: str) -> str:
    return text.strip().replace(" ", "").upper()


def _resolve_cid(query: str) -> Optional[int]:
    q = (query or "").strip()
    if not q:
        return None

    cid = _get_first_cid_from_name(q)
    if cid is not None:
        return cid

    formula_candidate = _normalize_formula_candidate(q)
    if formula_candidate:
        cid = _get_first_cid_from_formula(formula_candidate)
        if cid is not None:
            return cid

    return None


@lru_cache(maxsize=512)
def fetch_pubchem_record(query: str) -> Dict[str, Any]:
    q = (query or "").strip()
    if not q:
        return {}

    cid = _resolve_cid(q)
    if cid is None:
        return {}

    prop_names = ",".join(
        [
            "Title",
            "IUPACName",
            "MolecularFormula",
            "MolecularWeight",
            "CanonicalSMILES",
            "InChIKey",
            "XLogP",
            "TPSA",
            "HBondDonorCount",
            "HBondAcceptorCount",
            "Complexity",
            "Charge",
        ]
    )

    prop_data = _safe_get(f"{PUBCHEM_BASE}/compound/cid/{cid}/property/{prop_names}/JSON")
    synonyms_data = _safe_get(f"{PUBCHEM_BASE}/compound/cid/{cid}/synonyms/JSON")

    props = {}
    if prop_data:
        try:
            props = prop_data["PropertyTable"]["Properties"][0]
        except Exception:
            props = {}

    synonyms: List[str] = []
    if synonyms_data:
        try:
            synonyms = synonyms_data["InformationList"]["Information"][0]["Synonym"][:50]
        except Exception:
            synonyms = []

    return {
        "cid": cid,
        "title": props.get("Title"),
        "iupac_name": props.get("IUPACName"),
        "molecular_formula": props.get("MolecularFormula"),
        "molecular_weight": props.get("MolecularWeight"),
        "canonical_smiles": props.get("CanonicalSMILES"),
        "inchikey": props.get("InChIKey"),
        "xlogp": props.get("XLogP"),
        "tpsa": props.get("TPSA"),
        "hbd": props.get("HBondDonorCount"),
        "hba": props.get("HBondAcceptorCount"),
        "complexity": props.get("Complexity"),
        "charge": props.get("Charge"),
        "synonyms": synonyms,
        "source": "PubChem PUG REST",
    }
