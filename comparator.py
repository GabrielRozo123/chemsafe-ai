from __future__ import annotations

import pandas as pd


def _prop(profile, key, default="—"):
    value = profile.prop(key, None)
    return default if value is None else value


def _limit(profile, key, default="—"):
    value = profile.limit(key, None)
    return default if value is None else value


def build_comparison_df(profile_a, profile_b) -> pd.DataFrame:
    rows = [
        ("Nome", profile_a.identity.get("name", "—"), profile_b.identity.get("name", "—")),
        ("CAS", profile_a.identity.get("cas", "—"), profile_b.identity.get("cas", "—")),
        ("Fórmula", profile_a.identity.get("formula", "—"), profile_b.identity.get("formula", "—")),
        ("Massa molar", profile_a.identity.get("molecular_weight", "—"), profile_b.identity.get("molecular_weight", "—")),
        ("Ponto de fulgor (°C)", _prop(profile_a, "flash_point_c"), _prop(profile_b, "flash_point_c")),
        ("Ponto de ebulição (°C)", _prop(profile_a, "boiling_point_c"), _prop(profile_b, "boiling_point_c")),
        ("Autoignição (°C)", _prop(profile_a, "autoignition_c"), _prop(profile_b, "autoignition_c")),
        ("LII (%vol)", _prop(profile_a, "lfl_volpct"), _prop(profile_b, "lfl_volpct")),
        ("LSI (%vol)", _prop(profile_a, "ufl_volpct"), _prop(profile_b, "ufl_volpct")),
        ("Pressão de vapor (kPa)", _prop(profile_a, "vapor_pressure_kpa", _prop(profile_a, "vapor_pressure_kpa_20c")),
         _prop(profile_b, "vapor_pressure_kpa", _prop(profile_b, "vapor_pressure_kpa_20c"))),
        ("IDLH", _limit(profile_a, "IDLH_ppm", _limit(profile_a, "IDLH_mg_m3")),
         _limit(profile_b, "IDLH_ppm", _limit(profile_b, "IDLH_mg_m3"))),
        ("Rota sugerida", "; ".join(profile_a.routing[:2]), "; ".join(profile_b.routing[:2])),
        ("Confiança do pacote", f"{profile_a.confidence_score:.0f}/100", f"{profile_b.confidence_score:.0f}/100"),
    ]

    return pd.DataFrame(rows, columns=["Item", "Composto A", "Composto B"])


def build_comparison_highlights(profile_a, profile_b) -> list[str]:
    notes = []

    flash_a = profile_a.prop("flash_point_c")
    flash_b = profile_b.prop("flash_point_c")
    if flash_a is not None and flash_b is not None:
        if flash_a < flash_b:
            notes.append(f"{profile_a.identity.get('name')} apresenta ponto de fulgor menor e tende a maior sensibilidade à ignição.")
        elif flash_b < flash_a:
            notes.append(f"{profile_b.identity.get('name')} apresenta ponto de fulgor menor e tende a maior sensibilidade à ignição.")

    idlh_a = profile_a.limit("IDLH_ppm")
    idlh_b = profile_b.limit("IDLH_ppm")
    if idlh_a is not None and idlh_b is not None:
        if idlh_a < idlh_b:
            notes.append(f"{profile_a.identity.get('name')} possui IDLH mais restritivo no screening atual.")
        elif idlh_b < idlh_a:
            notes.append(f"{profile_b.identity.get('name')} possui IDLH mais restritivo no screening atual.")

    vp_a = profile_a.prop("vapor_pressure_kpa", profile_a.prop("vapor_pressure_kpa_20c"))
    vp_b = profile_b.prop("vapor_pressure_kpa", profile_b.prop("vapor_pressure_kpa_20c"))
    if vp_a is not None and vp_b is not None:
        if vp_a > vp_b:
            notes.append(f"{profile_a.identity.get('name')} tende a maior volatilidade no screening disponível.")
        elif vp_b > vp_a:
            notes.append(f"{profile_b.identity.get('name')} tende a maior volatilidade no screening disponível.")

    if not notes:
        notes.append("Sem contraste forte identificado com o pacote atual de propriedades.")

    return notes
