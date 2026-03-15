from __future__ import annotations


def classify_dispersion_mode(profile):
    vapor_density = profile.prop("vapor_density_air")
    boiling_point = profile.prop("boiling_point_c")
    pressurized = profile.flags.get("pressurized", False)

    reasons = []

    if vapor_density is not None and vapor_density > 1.2:
        reasons.append("vapor mais denso que o ar")
    if boiling_point is not None and boiling_point < -10:
        reasons.append("baixa temperatura de ebulição")
    if pressurized:
        reasons.append("serviço pressurizado")

    if reasons:
        return {
            "mode": "dense_gas_screening",
            "label": "Dispersão densa / conservadora",
            "reasons": reasons,
        }

    return {
        "mode": "neutral_gaussian_screening",
        "label": "Dispersão gaussiana neutra",
        "reasons": ["sem indícios fortes de gás denso no screening inicial"],
    }
