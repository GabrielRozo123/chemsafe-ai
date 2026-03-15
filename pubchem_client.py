from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests


PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


def _safe_get(url: str, timeout: int = 8) -> Optional[Dict[str, Any]]:
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def fetch_pubchem_record(query: str) -> Dict[str, Any]:
    query = (query or "").strip()
    if not query:
        return {}

    cid_data = _safe_get(f"{PUBCHEM_BASE}/compound/name/{requests.utils.quote(query)}/cids/JSON")
    if not cid_data:
        return {}

    try:
        cid = cid_data["IdentifierList"]["CID"][0]
    except Exception:
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
            synonyms = synonyms_data["InformationList"]["Information"][0]["Synonym"][:25]
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
