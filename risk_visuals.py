from __future__ import annotations

from typing import Any, Iterable, List

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap


FIG_BG = "#07111f"
AX_BG = "#0b1730"
GRID = "#29476d"
TEXT = "#e8f1ff"
MUTED = "#9ab2d8"
BLUE = "#4da3ff"
GREEN = "#34d399"
AMBER = "#fbbf24"
RED = "#fb7185"
PURPLE = "#9b8cff"
CYAN = "#38bdf8"


def _base_figure(figsize=(6, 4)):
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(FIG_BG)
    ax.set_facecolor(AX_BG)
    return fig, ax


def _style_axes(ax, title: str | None = None, grid_axis: str = "both"):
    for spine in ax.spines.values():
        spine.set_color(GRID)
        spine.set_linewidth(0.8)

    ax.tick_params(colors=MUTED, labelsize=9)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)

    if title:
        ax.set_title(title, color=TEXT, fontsize=12, fontweight="bold", pad=12)

    ax.grid(True, axis=grid_axis, color=GRID, alpha=0.35, linestyle="--", linewidth=0.6)


def build_hazard_fingerprint_figure(profile: Any):
    labels = list(profile.fingerprint.keys())
    values = [profile.fingerprint[k] for k in labels]

    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    values_closed = values + [values[0]]
    angles_closed = angles + [angles[0]]

    fig = plt.figure(figsize=(6.8, 5.2))
    fig.patch.set_facecolor(FIG_BG)
    ax = fig.add_subplot(111, polar=True)
    ax.set_facecolor(AX_BG)

    ax.plot(angles_closed, values_closed, color=BLUE, linewidth=2.2)
    ax.fill(angles_closed, values_closed, color=BLUE, alpha=0.18)

    ax.set_xticks(angles)
    ax.set_xticklabels([lbl.replace("_", " ").title() for lbl in labels], color=MUTED, fontsize=9)
    ax.set_ylim(0, 4.0)
    ax.set_yticks([1, 2, 3, 4])
    ax.set_yticklabels(["1", "2", "3", "4"], color=MUTED, fontsize=8)
    ax.grid(color=GRID, alpha=0.4, linestyle="--", linewidth=0.6)
    ax.spines["polar"].set_color(GRID)
    ax.set_title("Hazard Fingerprint", color=TEXT, fontsize=12, fontweight="bold", pad=16)

    fig.tight_layout()
    return fig


def build_source_coverage_figure(profile: Any):
    counts = {}
    for row in getattr(profile, "source_trace", []):
        src = row.get("source", "unknown")
        counts[src] = counts.get(src, 0) + 1

    labels = list(counts.keys()) or ["no data"]
    values = list(counts.values()) or [1]
    colors = [BLUE, CYAN, GREEN, PURPLE, AMBER, RED][: len(labels)]

    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    fig.patch.set_facecolor(FIG_BG)
    ax.set_facecolor(AX_BG)

    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        autopct="%1.0f%%",
        startangle=90,
        colors=colors,
        wedgeprops={"width": 0.42, "edgecolor": FIG_BG, "linewidth": 1.0},
        textprops={"color": TEXT, "fontsize": 9},
    )

    for t in autotexts:
        t.set_color(TEXT)
        t.set_fontsize(9)
        t.set_fontweight("bold")

    ax.set_title("Cobertura de fontes", color=TEXT, fontsize=12, fontweight="bold", pad=12)
    fig.tight_layout()
    return fig


def build_confidence_figure(profile: Any):
    score = float(getattr(profile, "confidence_score", 0.0))
    remaining = max(0.0, 100.0 - score)

    fig, ax = _base_figure((6.2, 3.8))

    color = GREEN if score >= 80 else AMBER if score >= 50 else RED
    ax.barh(["Confiança"], [score], color=color, edgecolor="none", height=0.55)
    ax.barh(["Confiança"], [remaining], left=[score], color="#1b2b46", edgecolor="none", height=0.55)

    ax.set_xlim(0, 100)
    ax.set_xlabel("Score")
    _style_axes(ax, "Confiança do pacote de dados", grid_axis="x")
    ax.text(min(score + 1.5, 95), 0, f"{score:.0f}/100", color=TEXT, va="center", fontsize=10, fontweight="bold")

    fig.tight_layout()
    return fig


def build_risk_matrix_figure(priorities: Iterable[dict]):
    cmap = ListedColormap(["#17324d", "#255c8a", "#8a6d1b", "#7a1f35"])

    color_grid = np.array(
        [
            [0, 0, 1, 1, 2],
            [0, 1, 1, 2, 2],
            [1, 1, 2, 2, 3],
            [1, 2, 2, 3, 3],
            [2, 2, 3, 3, 3],
        ]
    )

    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    fig.patch.set_facecolor(FIG_BG)
    ax.set_facecolor(AX_BG)

    ax.imshow(color_grid, origin="lower", cmap=cmap, vmin=0, vmax=3)

    ax.set_xticks(range(5))
    ax.set_yticks(range(5))
    ax.set_xticklabels(["1", "2", "3", "4", "5"], color=MUTED)
    ax.set_yticklabels(["1", "2", "3", "4", "5"], color=MUTED)
    ax.set_xlabel("Probabilidade", color=MUTED)
    ax.set_ylabel("Severidade", color=MUTED)
    ax.set_title("Matriz de risco", color=TEXT, fontsize=12, fontweight="bold", pad=12)

    for i in range(5):
        for j in range(5):
            ax.text(j, i, f"{(i + 1) * (j + 1)}", ha="center", va="center", fontsize=8, color=TEXT)

    for item in priorities:
        sev = int(item.get("severity_score", 3))
        lik = int(item.get("likelihood_score", 3))
        ax.plot(lik - 1, sev - 1, "o", markersize=12, color=CYAN, markeredgecolor=TEXT, markeredgewidth=1.0)
        ax.text(
            lik - 1 + 0.08,
            sev - 1 + 0.15,
            item.get("focus", "")[:15],
            fontsize=7,
            color=TEXT,
            bbox=dict(boxstyle="round,pad=0.2", fc="#10233f", ec="none", alpha=0.9),
        )

    for spine in ax.spines.values():
        spine.set_color(GRID)

    fig.tight_layout()
    return fig


def build_ipl_layers_figure(selected_ipls: List[str], suggested_ipls: List[str]):
    labels = [
        "Evento iniciador",
        "Alarme/detecção",
        "Operador",
        "SIS/ESD",
        "Alívio",
        "Contenção",
        "Mitigação",
    ]
    score_map = {k: 0 for k in labels}

    all_text = " | ".join((selected_ipls or []) + (suggested_ipls or [])).lower()

    if all_text:
        score_map["Evento iniciador"] = 1
    if any(x in all_text for x in ["alarm", "detecção", "deteccao", "detector"]):
        score_map["Alarme/detecção"] = 1
    if "operador" in all_text:
        score_map["Operador"] = 1
    if any(x in all_text for x in ["sis", "trip", "esd", "isolamento remoto"]):
        score_map["SIS/ESD"] = 1
    if any(x in all_text for x in ["psv", "rupture", "disco", "relief", "alívio", "alivio"]):
        score_map["Alívio"] = 1
    if any(x in all_text for x in ["dique", "contain", "contenção", "containment"]):
        score_map["Contenção"] = 1
    if any(x in all_text for x in ["foam", "espuma", "sprinkler", "evac", "ventila", "abatimento", "fire"]):
        score_map["Mitigação"] = 1

    values = [score_map[k] for k in labels]
    colors = [GREEN if v == 1 else "#243750" for v in values]

    fig, ax = _base_figure((8.8, 3.3))
    x = np.arange(len(labels))
    bars = ax.bar(x, values, color=colors, edgecolor="none", width=0.65)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=18, ha="right", color=MUTED)
    ax.set_ylim(0, 1.25)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["ausente", "presente"], color=MUTED)
    _style_axes(ax, "Panorama das camadas de proteção", grid_axis="y")

    for rect, v in zip(bars, values):
        ax.text(
            rect.get_x() + rect.get_width() / 2,
            v + 0.04,
            "✓" if v == 1 else "–",
            ha="center",
            va="bottom",
            color=TEXT,
            fontsize=11,
            fontweight="bold",
        )

    fig.tight_layout()
    return fig


def build_incompatibility_matrix_figure(profile: Any):
    matrix = getattr(profile, "incompatibility_matrix", [])
    labels = [row["categoria"] for row in matrix] if matrix else ["Sem dados"]
    status = [row["status"] for row in matrix] if matrix else ["Revisar"]

    mapping = {
        "Revisar": 0,
        "Compatível": 1,
        "Cuidado": 2,
        "Incompatível": 3,
    }
    palette = ListedColormap(["#243750", "#1f7a5a", "#8a6d1b", "#7a1f35"])

    values = [mapping.get(s, 0) for s in status]
    arr = np.array(values).reshape(1, len(values))

    fig, ax = plt.subplots(figsize=(9.4, 2.9))
    fig.patch.set_facecolor(FIG_BG)
    ax.set_facecolor(AX_BG)
    ax.imshow(arr, aspect="auto", cmap=palette, vmin=0, vmax=3)

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=22, ha="right", color=MUTED)
    ax.set_yticks([0])
    ax.set_yticklabels(["Status"], color=MUTED)
    ax.set_title("Matriz de compatibilidade", color=TEXT, fontsize=12, fontweight="bold", pad=12)

    for j, s in enumerate(status):
        ax.text(j, 0, s, ha="center", va="center", fontsize=8, color=TEXT)

    for spine in ax.spines.values():
        spine.set_color(GRID)

    fig.tight_layout()
    return fig
