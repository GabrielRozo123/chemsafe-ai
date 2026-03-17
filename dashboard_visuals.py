from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

FIG_BG = "#07111f"
AX_BG = "#0b1730"
GRID = "#29476d"
TEXT = "#e8f1ff"
MUTED = "#9ab2d8"

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

def build_readiness_gauge_figure(index_data: dict):
    score = index_data.get("index", 0)
    # Cores baseadas nas faixas executivas
    color = "#ef4444" if score < 40 else "#f59e0b" if score < 70 else "#34d399" if score < 85 else "#4ea3ff"
    remaining = max(0.0, 100.0 - score)

    fig, ax = _base_figure((6.2, 3.8))
    ax.barh(["Readiness Global"], [score], color=color, edgecolor="none", height=0.55)
    ax.barh(["Readiness Global"], [remaining], left=[score], color="#1b2b46", edgecolor="none", height=0.55)

    ax.set_xlim(0, 100)
    ax.set_xlabel("Score (0-100)")
    _style_axes(ax, "Case Readiness Index (CRI)", grid_axis="x")
    ax.text(min(score + 2, 95), 0, f"{score:.1f}%", color=TEXT, va="center", fontsize=11, fontweight="bold")
    
    fig.tight_layout()
    return fig

def build_components_figure(index_data: dict):
    components = index_data.get("components",[])
    if not components:
        fig, ax = _base_figure((6, 3))
        return fig
        
    labels = [c["name"] for c in components]
    scores = [c["score"] for c in components]
    
    fig, ax = _base_figure((7.2, 4.2))
    y = np.arange(len(labels))
    
    # Degradê de cor baseado no status individual de cada pilar
    colors =["#34d399" if s >= 80 else "#f59e0b" if s >= 50 else "#ef4444" for s in scores]
    
    ax.barh(y, scores, color=colors, edgecolor="none", height=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, color=MUTED)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Desempenho por Módulo (%)")
    _style_axes(ax, "Composição do Readiness", grid_axis="x")
    
    for i, v in enumerate(scores):
        ax.text(min(v + 2, 95), i, f"{v:.0f}", color=TEXT, va="center", fontsize=9)
        
    fig.tight_layout()
    return fig
