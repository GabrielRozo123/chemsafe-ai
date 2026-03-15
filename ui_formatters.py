from __future__ import annotations

import math
import pandas as pd


FIELD_LABELS = {
    "name": "Nome",
    "preferred_name": "Nome preferencial",
    "formula": "Fórmula",
    "molecular_weight": "Massa molar",
    "pubchem_cid": "CID PubChem",
    "iupac_name": "Nome IUPAC",
    "smiles": "SMILES canônico",
    "inchikey": "InChIKey",
    "xlogp": "XlogP",
    "tpsa": "TPSA",
    "hbd": "Doadores de H",
    "hba": "Aceptores de H",
    "complexity": "Complexidade",
    "cas": "CAS",
}

PROPERTY_LABELS = {
    "flash_point_c": "Ponto de fulgor",
    "boiling_point_c": "Ponto de ebulição",
    "melting_point_c": "Ponto de fusão",
    "autoignition_c": "Temperatura de autoignição",
    "lfl_volpct": "LII",
    "ufl_volpct": "LSI",
    "vapor_pressure_kpa_20c": "Pressão de vapor a 20 °C",
    "vapor_pressure_kpa": "Pressão de vapor",
    "density_liquid_g_cm3": "Densidade do líquido",
    "vapor_density_air": "Densidade relativa do vapor",
    "mie_mj": "Energia mínima de ignição",
    "molecular_weight": "Massa molar",
    "xlogp": "XlogP",
}

LIMIT_LABELS = {
    "IDLH_ppm": "IDLH",
    "IDLH_mg_m3": "IDLH",
    "TLV_TWA_ppm": "TLV-TWA",
    "TLV_STEL_mg_m3": "TLV-STEL",
    "REL_TWA_ppm": "REL-TWA",
    "REL_ST_ppm": "REL-ST",
    "OSHA_PEL_TWA_ppm": "OSHA PEL-TWA",
    "ERPG_2_ppm": "ERPG-2",
    "ERPG_3_ppm": "ERPG-3",
}

SOURCE_LABELS = {
    "local_seed": "Base local curada",
    "PubChem": "PubChem",
    "PubChem PUG REST": "PubChem",
    "NIST WebBook": "NIST WebBook",
    "NIOSH Pocket Guide": "NIOSH Pocket Guide",
}

CONFIDENCE_LABELS = {
    "seed": "curado",
    "live": "ao vivo",
}


def _fmt_value(v):
    if isinstance(v, float):
        if math.isfinite(v):
            if abs(v) >= 100:
                return f"{v:.1f}"
            if abs(v) >= 10:
                return f"{v:.2f}"
            return f"{v:.3f}"
    return v


def format_identity_df(profile) -> pd.DataFrame:
    rows = []
    for key, value in profile.identity.items():
        if value in [None, ""]:
            continue
        rows.append(
            {
                "Campo": FIELD_LABELS.get(key, key),
                "Valor": _fmt_value(value),
            }
        )
    return pd.DataFrame(rows)


def format_physchem_df(profile) -> pd.DataFrame:
    rows = []
    for key, item in profile.physchem.items():
        rows.append(
            {
                "Propriedade": PROPERTY_LABELS.get(key, key),
                "Valor": _fmt_value(item.value),
                "Unidade": item.unit,
                "Fonte": SOURCE_LABELS.get(item.source, item.source),
                "Status": CONFIDENCE_LABELS.get(item.confidence, item.confidence),
            }
        )
    return pd.DataFrame(rows)


def format_limits_df(profile) -> pd.DataFrame:
    rows = []
    for key, item in profile.exposure_limits.items():
        rows.append(
            {
                "Limite": LIMIT_LABELS.get(key, key),
                "Valor": _fmt_value(item.value),
                "Unidade": item.unit,
                "Fonte": SOURCE_LABELS.get(item.source, item.source),
                "Status": CONFIDENCE_LABELS.get(item.confidence, item.confidence),
            }
        )
    return pd.DataFrame(rows)
