from __future__ import annotations

import pandas as pd


def _status_label(item) -> str:
    if item is None:
        return "faltante"
    if getattr(item, "confidence", "") == "seed":
        return "curado"
    if getattr(item, "confidence", "") == "live":
        return "ao vivo"
    return "revisar"


def build_property_status_df(profile) -> pd.DataFrame:
    rows = []

    important_physchem = [
        ("flash_point_c", "Ponto de fulgor"),
        ("boiling_point_c", "Ponto de ebulição"),
        ("autoignition_c", "Temperatura de autoignição"),
        ("lfl_volpct", "LII"),
        ("ufl_volpct", "LSI"),
        ("vapor_pressure_kpa", "Pressão de vapor"),
        ("vapor_pressure_kpa_20c", "Pressão de vapor a 20 °C"),
        ("density_liquid_g_cm3", "Densidade do líquido"),
        ("vapor_density_air", "Densidade relativa do vapor"),
        ("mie_mj", "Energia mínima de ignição"),
        ("xlogp", "XlogP"),
    ]

    for key, label in important_physchem:
        item = profile.physchem.get(key)
        rows.append(
            {
                "Grupo": "Físico-química",
                "Item": label,
                "Status": _status_label(item),
                "Fonte": getattr(item, "source", "") if item else "",
                "Valor": getattr(item, "value", "") if item else "",
                "Unidade": getattr(item, "unit", "") if item else "",
            }
        )

    important_limits = [
        ("IDLH_ppm", "IDLH"),
        ("IDLH_mg_m3", "IDLH"),
        ("TLV_TWA_ppm", "TLV-TWA"),
        ("REL_TWA_ppm", "REL-TWA"),
        ("REL_ST_ppm", "REL-ST"),
        ("OSHA_PEL_TWA_ppm", "OSHA PEL-TWA"),
        ("ERPG_2_ppm", "ERPG-2"),
        ("ERPG_3_ppm", "ERPG-3"),
    ]

    for key, label in important_limits:
        item = profile.exposure_limits.get(key)
        rows.append(
            {
                "Grupo": "Exposição",
                "Item": label,
                "Status": _status_label(item),
                "Fonte": getattr(item, "source", "") if item else "",
                "Valor": getattr(item, "value", "") if item else "",
                "Unidade": getattr(item, "unit", "") if item else "",
            }
        )

    return pd.DataFrame(rows)


def summarize_property_status(profile) -> dict:
    df = build_property_status_df(profile)
    counts = df["Status"].value_counts().to_dict()
    return {
        "curado": counts.get("curado", 0),
        "ao vivo": counts.get("ao vivo", 0),
        "faltante": counts.get("faltante", 0),
        "revisar": counts.get("revisar", 0),
    }
