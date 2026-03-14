from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from chemicals import resolve_compound
from hazop_db import HAZOP_DB

IPL_CATALOG = [
    ("Válvula de alívio de pressão (PSV) — bem mantida", 0.01),
    ("SIS / SIL 1 (IEC 61511) — verificado", 0.01),
    ("SIS / SIL 2 (IEC 61511)", 0.001),
    ("SIS / SIL 3 (IEC 61511)", 0.0001),
    ("Alarme + ação do operador treinado", 0.1),
    ("Dique de contenção", 0.01),
    ("Disco de ruptura", 0.01),
    ("Procedimento administrativo com treinamento", 0.1),
    ("Sistema de detecção e combate a incêndio", 0.01),
    ("Válvula de bloqueio de emergência (ESV) automática", 0.01),
]

PG_COEF = {
    "A": {"a": 0.22, "b": 0.894, "c": 0.20, "d": 0.894},
    "B": {"a": 0.16, "b": 0.894, "c": 0.12, "d": 0.894},
    "C": {"a": 0.11, "b": 0.894, "c": 0.08, "d": 0.894},
    "D": {"a": 0.08, "b": 0.894, "c": 0.06, "d": 0.894},
    "E": {"a": 0.06, "b": 0.894, "c": 0.03, "d": 0.894},
    "F": {"a": 0.04, "b": 0.894, "c": 0.016, "d": 0.894},
}


def chemical_lookup(query: str):
    return resolve_compound(query)


def hazop_template(parameter: str, guideword: str) -> Dict:
    parameter_key = parameter if parameter in HAZOP_DB else next(iter(HAZOP_DB))
    gw_space = guideword.strip().upper()
    parameter_data = HAZOP_DB.get(parameter_key, {})
    if gw_space in parameter_data:
        return parameter_data[gw_space]
    return parameter_data.get(next(iter(parameter_data)), {})


def compute_lopa(f_ie: float, criterion: float, selected_ipls: List[Tuple[str, float]]) -> Dict:
    pfd_total = 1.0
    for _, pfd in selected_ipls:
        pfd_total *= pfd

    mcf = f_ie * pfd_total
    ratio = mcf / criterion if criterion else float("inf")

    sil = "Não requerido"
    if ratio >= 1000:
        sil = "SIL 3"
    elif ratio >= 100:
        sil = "SIL 2"
    elif ratio >= 10:
        sil = "SIL 1"

    return {
        "f_ie": f_ie,
        "pfd_total": pfd_total,
        "mcf": mcf,
        "ratio": ratio,
        "sil": sil,
        "criterion": criterion,
        "selected_ipls": selected_ipls,
    }


def gaussian_dispersion(
    q_g_s: float,
    wind_m_s: float,
    stability: str,
    idlh_ppm: float,
    molecular_weight: float,
    stack_height_m: float = 0.0,
    x_max: int = 3000,
    step: int = 25,
) -> Dict:
    pg = PG_COEF[stability]
    idlh_gm3 = idlh_ppm * molecular_weight / 24.45
    xs = list(range(10, x_max + 1, step))
    cs: List[float] = []
    x_idlh: Optional[int] = None

    for x in xs:
        sy = pg["a"] * (x ** pg["b"])
        sz = pg["c"] * (x ** pg["d"])
        c_val = q_g_s / (math.pi * sy * sz * wind_m_s) * math.exp(
            -((stack_height_m ** 2) / (2 * sz ** 2))
        )
        cs.append(c_val)
        if x_idlh is None and c_val <= idlh_gm3:
            x_idlh = x

    return {
        "xs": xs,
        "cs": cs,
        "x_idlh": x_idlh,
        "idlh_gm3": idlh_gm3,
        "c_at_100m": next((c for x, c in zip(xs, cs) if x >= 100), cs[0]),
    }


def pool_fire(
    pool_diameter_m: float,
    burn_rate_kg_m2_s: float,
    heat_of_combustion_kj_kg: float,
    receptor_distance_m: float,
) -> Dict:
    q_rel = burn_rate_kg_m2_s * (math.pi * pool_diameter_m**2 / 4) * heat_of_combustion_kj_kg
    hf = max(0.1, 0.235 * (q_rel**0.4) - 1.02 * pool_diameter_m)
    emissive_power = 58 * math.exp(-0.00823 * pool_diameter_m)

    s = max(1.01, receptor_distance_m / (pool_diameter_m / 2))
    a_v = math.sqrt((s + 1) ** 2 + (2 * hf / pool_diameter_m) ** 2 - 1)
    b_v = math.sqrt((s - 1) ** 2 + (2 * hf / pool_diameter_m) ** 2)

    try:
        form_factor = max(
            0.0001,
            (1 / (math.pi * s))
            * (
                math.atan(math.sqrt((s + 1) / (s - 1)))
                - (1 / a_v) * math.atan(math.sqrt((s + 1) / (a_v * (s - 1))))
                + (2 * hf / pool_diameter_m / b_v)
                * math.atan(math.sqrt((s + 1) / (b_v * (s - 1))))
            ),
        )
    except Exception:
        form_factor = 0.01

    tau = max(0.1, 1 - 0.058 * math.log(receptor_distance_m))
    qdot = emissive_power * form_factor * tau

    if qdot > 37.5:
        zone = "Fatalidade / dano extremo"
    elif qdot > 12.5:
        zone = "Queimaduras graves"
    elif qdot > 4.7:
        zone = "Dor intensa / queimaduras leves"
    else:
        zone = "Zona relativamente segura"

    return {
        "Q_rel_kW": q_rel,
        "Hf_m": hf,
        "E_kW_m2": emissive_power,
        "form_factor": form_factor,
        "tau": tau,
        "q_kW_m2": qdot,
        "zone": zone,
    }


def recommend_modules(process_text: str, compound_name: str = "") -> List[str]:
    txt = (process_text + " " + compound_name).lower()
    rec = []

    if any(
        key in txt
        for key in ["toxico", "toxic", "amônia", "ammonia", "chlor", "cloro", "release", "vazamento gasoso"]
    ):
        rec.append("Dispersão gaussiana / toxic release screening")

    if any(
        key in txt
        for key in ["inflam", "etanol", "solvente", "tolueno", "pool", "poça", "derramamento"]
    ):
        rec.append("Pool fire / radiação térmica")

    if any(
        key in txt
        for key in ["reator", "exotérm", "runaway", "cstr", "batch", "pressão", "vaso"]
    ):
        rec.append("HAZOP + LOPA + SIL")

    if not rec:
        rec.append("HAZOP preliminar")

    return rec
