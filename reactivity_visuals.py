from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np


FIG_BG = "#07111f"
AX_BG = "#0b1730"
GRID = "#29476d"
TEXT = "#e8f1ff"
MUTED = "#9ab2d8"

STATUS_TO_VALUE = {"OK": 0, "Revisar": 1, "Cuidado": 2, "Incompatível": 3}
VALUE_TO_COLOR = {
    0: "#223c5d",
    1: "#4b5563",
    2: "#d4a72c",
    3: "#a62b45",
}


def build_pairwise_matrix_figure(matrix_df):
    if matrix_df is None or matrix_df.empty:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        fig.patch.set_facecolor(FIG_BG)
        ax.set_facecolor(AX_BG)
        ax.axis("off")
        ax.text(0.5, 0.5, "Sem matriz disponível", color=TEXT, ha="center", va="center", fontsize=12)
        return fig

    arr = matrix_df.copy()
    labels_y = list(arr.index)
    labels_x = list(arr.columns)

    values = arr.replace(STATUS_TO_VALUE).values.astype(float)

    fig, ax = plt.subplots(figsize=(max(6.5, 1.5 + 1.2 * len(labels_x)), max(3.8, 1.5 + 0.75 * len(labels_y))))
    fig.patch.set_facecolor(FIG_BG)
    ax.set_facecolor(AX_BG)

    color_grid = np.empty(values.shape, dtype=object)
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            color_grid[i, j] = VALUE_TO_COLOR.get(int(values[i, j]), "#223c5d")

    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            rect = plt.Rectangle((j, i), 1, 1, facecolor=color_grid[i, j], edgecolor=GRID, linewidth=1.0)
            ax.add_patch(rect)
            ax.text(j + 0.5, i + 0.5, arr.iloc[i, j], ha="center", va="center", color=TEXT, fontsize=9, wrap=True)

    ax.set_xlim(0, values.shape[1])
    ax.set_ylim(values.shape[0], 0)
    ax.set_xticks(np.arange(values.shape[1]) + 0.5)
    ax.set_yticks(np.arange(values.shape[0]) + 0.5)
    ax.set_xticklabels(labels_x, rotation=22, ha="right", color=MUTED, fontsize=9)
    ax.set_yticklabels(labels_y, color=MUTED, fontsize=9)

    for spine in ax.spines.values():
        spine.set_color(GRID)

    ax.set_title("Matriz de compatibilidade entre substâncias", color=TEXT, fontsize=12, fontweight="bold", pad=12)
    fig.tight_layout()
    return fig
