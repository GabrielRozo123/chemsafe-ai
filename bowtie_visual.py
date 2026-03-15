from __future__ import annotations

import matplotlib.pyplot as plt


FIG_BG = "#07111f"
AX_BG = "#0b1730"
TEXT = "#e8f1ff"
MUTED = "#9ab2d8"
BLUE = "#4da3ff"
GREEN = "#34d399"
RED = "#fb7185"
GRID = "#29476d"
PURPLE = "#5b4bb7"


def _draw_bowtie(threats, barriers_pre, top_event, barriers_mit, consequences):
    fig, ax = plt.subplots(figsize=(10.8, 5.8))
    fig.patch.set_facecolor(FIG_BG)
    ax.set_facecolor(AX_BG)
    ax.axis("off")

    def box(x, y, text, color, w=0.2, h=0.1, fs=9):
        rect = plt.Rectangle((x, y), w, h, facecolor=color, edgecolor=GRID, linewidth=1.0)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=TEXT, fontsize=fs, wrap=True)

    x_threat = 0.03
    x_pre = 0.28
    x_top = 0.43
    x_mit = 0.59
    x_cons = 0.80

    y_positions = [0.76, 0.58, 0.40, 0.22]

    for y, t in zip(y_positions, threats):
        box(x_threat, y, t, "#17324d", w=0.20, h=0.11)

    for y, b in zip(y_positions, barriers_pre):
        box(x_pre, y, b, "#1f4b77", w=0.12, h=0.11)

    box(x_top, 0.45, top_event, PURPLE, w=0.12, h=0.12, fs=10)

    for y, b in zip(y_positions, barriers_mit):
        box(x_mit, y, b, "#1f7a5a", w=0.12, h=0.11)

    for y, c in zip(y_positions, consequences):
        box(x_cons, y, c, "#7a1f35", w=0.17, h=0.11)

    for y in y_positions[: len(threats)]:
        ax.annotate("", xy=(x_pre, y + 0.055), xytext=(x_threat + 0.20, y + 0.055),
                    arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.2))
    for y in y_positions[: len(barriers_pre)]:
        ax.annotate("", xy=(x_top, 0.51), xytext=(x_pre + 0.12, y + 0.055),
                    arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.0))
    for y in y_positions[: len(barriers_mit)]:
        ax.annotate("", xy=(x_cons, y + 0.055), xytext=(x_mit + 0.12, y + 0.055),
                    arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.2))
    for y in y_positions[: len(consequences)]:
        ax.annotate("", xy=(x_mit, y + 0.055), xytext=(x_top + 0.12, 0.51),
                    arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.0))

    ax.text(0.13, 0.92, "Ameaças", color=BLUE, fontsize=11, fontweight="bold", ha="center")
    ax.text(0.34, 0.92, "Barreiras preventivas", color=BLUE, fontsize=11, fontweight="bold", ha="center")
    ax.text(0.49, 0.92, "Top Event", color=TEXT, fontsize=11, fontweight="bold", ha="center")
    ax.text(0.65, 0.92, "Barreiras mitigadoras", color=GREEN, fontsize=11, fontweight="bold", ha="center")
    ax.text(0.885, 0.92, "Consequências", color=RED, fontsize=11, fontweight="bold", ha="center")

    fig.tight_layout()
    return fig


def build_bowtie_custom_figure(threats, barriers_pre, top_event, barriers_mit, consequences):
    threats = threats[:4]
    barriers_pre = barriers_pre[:4]
    barriers_mit = barriers_mit[:4]
    consequences = consequences[:4]
    return _draw_bowtie(threats, barriers_pre, top_event, barriers_mit, consequences)
