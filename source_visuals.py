from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np


FIG_BG = "#07111f"
AX_BG = "#0b1730"
GRID = "#29476d"
TEXT = "#e8f1ff"
MUTED = "#9ab2d8"
GREEN = "#34d399"
AMBER = "#fbbf24"
RED = "#fb7185"
BLUE = "#4da3ff"
PURPLE = "#8b5cf6"


def _base_figure(figsize=(6, 4)):
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(FIG_BG)
    ax.set_facecolor(AX_BG)
    return fig, ax


def _style_axes(ax, title=None, grid_axis="x"):
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)
    ax.grid(True, axis=grid_axis, color=GRID, alpha=0.35, linestyle="--", linewidth=0.6)
    if title:
        ax.set_title(title, color=TEXT, fontsize=12, fontweight="bold", pad=12)


def build_source_summary_figure(summary: dict):
    labels = ["Oficial", "Curado", "Revisar"]
    values = [
        summary.get("oficial", 0),
        summary.get("curado", 0),
        summary.get("revisar", 0),
    ]
    colors = [GREEN, BLUE, RED]

    fig, ax = _base_figure((6.4, 4.2))
    x = np.arange(len(labels))
    bars = ax.bar(x, values, color=colors, edgecolor="none", width=0.6)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, color=MUTED)
    ax.set_ylabel("Quantidade")
    _style_axes(ax, "Cobertura de fontes", grid_axis="y")

    for rect, v in zip(bars, values):
        ax.text(
            rect.get_x() + rect.get_width() / 2,
            rect.get_height() + 0.1,
            str(v),
            ha="center",
            va="bottom",
            color=TEXT,
            fontsize=9,
        )

    fig.tight_layout()
    return fig


def build_link_coverage_figure(summary: dict):
    total = max(summary.get("linhas", 0), 1)
    linked = summary.get("com_link", 0)
    missing = max(total - linked, 0)

    fig, ax = _base_figure((6.2, 3.8))
    ax.barh(["Links oficiais"], [linked], color=PURPLE, edgecolor="none", height=0.55)
    ax.barh(["Links oficiais"], [missing], left=[linked], color="#1b2b46", edgecolor="none", height=0.55)

    ax.set_xlim(0, total)
    ax.set_xlabel("Campos")
    _style_axes(ax, "Cobertura de links", grid_axis="x")
    ax.text(min(linked + 0.3, total * 0.95), 0, f"{linked}/{total}", color=TEXT, va="center", fontsize=10, fontweight="bold")

    fig.tight_layout()
    return fig
