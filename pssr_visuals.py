from __future__ import annotations

import matplotlib.pyplot as plt


FIG_BG = "#07111f"
AX_BG = "#0b1730"
GRID = "#29476d"
TEXT = "#e8f1ff"
MUTED = "#9ab2d8"
GREEN = "#34d399"
AMBER = "#fbbf24"
RED = "#fb7185"


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


def build_pssr_score_figure(summary: dict):
    score = float(summary.get("score", 0))
    remaining = max(0.0, 100.0 - score)
    color = GREEN if score >= 80 else AMBER if score >= 60 else RED

    fig, ax = _base_figure((6.2, 3.8))
    ax.barh(["PSSR"], [score], color=color, edgecolor="none", height=0.55)
    ax.barh(["PSSR"], [remaining], left=[score], color="#1b2b46", edgecolor="none", height=0.55)

    ax.set_xlim(0, 100)
    ax.set_xlabel("Score")
    _style_axes(ax, "PSSR Readiness", grid_axis="x")
    ax.text(min(score + 2, 95), 0, f"{score:.0f}/100", color=TEXT, va="center", fontsize=10, fontweight="bold")

    fig.tight_layout()
    return fig
