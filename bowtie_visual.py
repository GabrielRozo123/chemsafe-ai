from __future__ import annotations

import textwrap
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


def _wrap_text(text: str, width: int) -> str:
    if not text:
        return ""
    parts = []
    for paragraph in str(text).split("\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            parts.append("")
        else:
            parts.append(textwrap.fill(paragraph, width=width, break_long_words=False, break_on_hyphens=False))
    return "\n".join(parts)


def _line_count(text: str) -> int:
    if not text:
        return 1
    return max(1, len(str(text).splitlines()))


def _box_height_from_text(text: str, base: float = 0.085, per_line: float = 0.024, max_h: float = 0.17) -> float:
    h = base + (_line_count(text) - 1) * per_line
    return min(h, max_h)


def _draw_box(ax, x, y, w, h, text, facecolor, fontsize=9, wrap_width=22):
    wrapped = _wrap_text(text, wrap_width)
    rect = plt.Rectangle((x, y), w, h, facecolor=facecolor, edgecolor=GRID, linewidth=1.0)
    ax.add_patch(rect)

    txt = ax.text(
        x + w / 2,
        y + h / 2,
        wrapped,
        ha="center",
        va="center",
        color=TEXT,
        fontsize=fontsize,
        wrap=True,
        clip_on=True,
    )
    txt.set_clip_path(rect)
    return rect


def _prepare_column(items, wrap_width):
    prepared = []
    for item in items:
        wrapped = _wrap_text(item, wrap_width)
        h = _box_height_from_text(wrapped)
        prepared.append({"raw": item, "wrapped": wrapped, "height": h})
    return prepared


def _draw_column(ax, x, y_top, width, items, color, wrap_width, gap=0.045, fontsize=8.8):
    prepared = _prepare_column(items, wrap_width)
    centers = []

    y = y_top
    for item in prepared:
        h = item["height"]
        y_box = y - h
        _draw_box(ax, x, y_box, width, h, item["wrapped"], color, fontsize=fontsize, wrap_width=wrap_width)
        centers.append((x, y_box, width, h))
        y = y_box - gap

    return centers


def _arrow(ax, x0, y0, x1, y1, lw=1.2):
    ax.annotate(
        "",
        xy=(x1, y1),
        xytext=(x0, y0),
        arrowprops=dict(arrowstyle="->", color=MUTED, lw=lw),
    )


def _limit_items(items, n=4):
    return [str(x).strip() for x in items if str(x).strip()][:n]


def build_bowtie_custom_figure(threats, barriers_pre, top_event, barriers_mit, consequences):
    threats = _limit_items(threats, 4)
    barriers_pre = _limit_items(barriers_pre, 4)
    barriers_mit = _limit_items(barriers_mit, 4)
    consequences = _limit_items(consequences, 4)
    top_event = str(top_event).strip() or "Perda de contenção / perda de controle"

    fig, ax = plt.subplots(figsize=(12.2, 6.6))
    fig.patch.set_facecolor(FIG_BG)
    ax.set_facecolor(AX_BG)
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    # Títulos
    ax.text(0.12, 0.94, "Ameaças", color=BLUE, fontsize=11, fontweight="bold", ha="center")
    ax.text(0.33, 0.94, "Barreiras preventivas", color=BLUE, fontsize=11, fontweight="bold", ha="center")
    ax.text(0.50, 0.94, "Top Event", color=TEXT, fontsize=11, fontweight="bold", ha="center")
    ax.text(0.67, 0.94, "Barreiras mitigadoras", color=GREEN, fontsize=11, fontweight="bold", ha="center")
    ax.text(0.88, 0.94, "Consequências", color=RED, fontsize=11, fontweight="bold", ha="center")

    # Colunas
    x_threat = 0.03
    x_pre = 0.27
    x_top = 0.43
    x_mit = 0.59
    x_cons = 0.79

    w_threat = 0.18
    w_pre = 0.12
    w_top = 0.14
    w_mit = 0.12
    w_cons = 0.17

    y_top_start = 0.87

    threat_boxes = _draw_column(ax, x_threat, y_top_start, w_threat, threats, "#17324d", wrap_width=22, gap=0.045, fontsize=8.8)
    pre_boxes = _draw_column(ax, x_pre, y_top_start, w_pre, barriers_pre, "#1f4b77", wrap_width=15, gap=0.045, fontsize=8.5)
    mit_boxes = _draw_column(ax, x_mit, y_top_start, w_mit, barriers_mit, "#1f7a5a", wrap_width=15, gap=0.045, fontsize=8.5)
    cons_boxes = _draw_column(ax, x_cons, y_top_start, w_cons, consequences, "#7a1f35", wrap_width=20, gap=0.045, fontsize=8.8)

    # Top event: caixa maior e dinâmica
    wrapped_top = _wrap_text(top_event, 24)
    h_top = _box_height_from_text(wrapped_top, base=0.10, per_line=0.028, max_h=0.19)
    y_top_box = 0.5 - h_top / 2
    _draw_box(ax, x_top, y_top_box, w_top, h_top, wrapped_top, PURPLE, fontsize=9.5, wrap_width=24)

    top_center_x = x_top + w_top / 2
    top_center_y = y_top_box + h_top / 2

    # Ligações: ameaça -> barreira preventiva
    for (xt, yt, wt, ht), (xp, yp, wp, hp) in zip(threat_boxes, pre_boxes):
        _arrow(ax, xt + wt, yt + ht / 2, xp, yp + hp / 2, lw=1.2)

    # Ligações: barreiras preventivas -> top event
    for (xp, yp, wp, hp) in pre_boxes:
        _arrow(ax, xp + wp, yp + hp / 2, x_top, top_center_y, lw=1.1)

    # Ligações: top event -> barreiras mitigadoras
    for (xm, ym, wm, hm) in mit_boxes:
        _arrow(ax, x_top + w_top, top_center_y, xm, ym + hm / 2, lw=1.1)

    # Ligações: barreiras mitigadoras -> consequências
    for (xm, ym, wm, hm), (xc, yc, wc, hc) in zip(mit_boxes, cons_boxes):
        _arrow(ax, xm + wm, ym + hm / 2, xc, yc + hc / 2, lw=1.2)

    fig.tight_layout()
    return fig
