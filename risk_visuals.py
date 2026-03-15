from __future__ import annotations

from typing import Any, Iterable, List

import matplotlib.pyplot as plt
import numpy as np


def build_hazard_fingerprint_figure(profile: Any):
    labels = list(profile.fingerprint.keys())
    values = [profile.fingerprint[k] for k in labels]

    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    values_closed = values + [values[0]]
    angles_closed = angles + [angles[0]]

    fig = plt.figure(figsize=(6.8, 5.2))
    ax = fig.add_subplot(111, polar=True)
    ax.plot(angles_closed, values_closed, linewidth=2)
    ax.fill(angles_closed, values_closed, alpha=0.20)
    ax.set_xticks(angles)
    ax.set_xticklabels([lbl.replace("_", " ").title() for lbl in labels])
    ax.set_ylim(0, 4.0)
    ax.set_yticks([1, 2, 3, 4])
    ax.set_title("Hazard Fingerprint", pad=18)
    fig.tight_layout()
    return fig


def build_source_coverage_figure(profile: Any):
    counts = {}
    for row in getattr(profile, "source_trace", []):
        src = row.get("source", "unknown")
        counts[src] = counts.get(src, 0) + 1

    labels = list(counts.keys()) or ["no data"]
    values = list(counts.values()) or [1]

    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.pie(values, labels=labels, autopct="%1.0f%%", startangle=90)
    ax.set_title("Source Coverage")
    fig.tight_layout()
    return fig


def build_confidence_figure(profile: Any):
    score = float(getattr(profile, "confidence_score", 0.0))
    remaining = max(0.0, 100.0 - score)

    fig, ax = plt.subplots(figsize=(6.0, 3.6))
    ax.barh(["Confidence"], [score], label="Score")
    ax.barh(["Confidence"], [remaining], left=[score], label="Missing")
    ax.set_xlim(0, 100)
    ax.set_xlabel("Score")
    ax.set_title("Data Confidence")
    ax.text(min(score + 2, 95), 0, f"{score:.0f}/100", va="center")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    return fig


def build_risk_matrix_figure(priorities: Iterable[dict]):
    fig, ax = plt.subplots(figsize=(6.0, 5.2))

    color_grid = np.array(
        [
            [1, 1, 2, 2, 3],
            [1, 2, 2, 3, 3],
            [2, 2, 3, 3, 4],
            [2, 3, 3, 4, 4],
            [3, 3, 4, 4, 4],
        ]
    )

    ax.imshow(color_grid, origin="lower")

    ax.set_xticks(range(5))
    ax.set_yticks(range(5))
    ax.set_xticklabels(["1", "2", "3", "4", "5"])
    ax.set_yticklabels(["1", "2", "3", "4", "5"])
    ax.set_xlabel("Likelihood")
    ax.set_ylabel("Severity")
    ax.set_title("Risk Matrix")

    for i in range(5):
        for j in range(5):
            ax.text(j, i, f"{(i+1)*(j+1)}", ha="center", va="center", fontsize=8)

    for item in priorities:
        sev = int(item.get("severity_score", 3))
        lik = int(item.get("likelihood_score", 3))
        ax.plot(lik - 1, sev - 1, "o", markersize=11)
        ax.text(lik - 1 + 0.08, sev - 1 + 0.12, item.get("focus", "")[:14], fontsize=7)

    fig.tight_layout()
    return fig


def build_ipl_layers_figure(selected_ipls: List[str], suggested_ipls: List[str]):
    labels = ["Initiating", "Alarm/Detect", "Operator", "SIS/ESD", "Relief", "Containment", "Mitigation"]
    score_map = {k: 0 for k in labels}

    all_text = " | ".join((selected_ipls or []) + (suggested_ipls or [])).lower()

    if all_text:
        score_map["Initiating"] = 1
    if any(x in all_text for x in ["alarm", "detecção", "deteccao", "detector"]):
        score_map["Alarm/Detect"] = 1
    if "operador" in all_text:
        score_map["Operator"] = 1
    if any(x in all_text for x in ["sis", "trip", "esd", "isolamento remoto"]):
        score_map["SIS/ESD"] = 1
    if any(x in all_text for x in ["psv", "rupture", "disco", "relief", "alívio", "alivio"]):
        score_map["Relief"] = 1
    if any(x in all_text for x in ["dique", "contain", "contenção", "containment"]):
        score_map["Containment"] = 1
    if any(x in all_text for x in ["foam", "espuma", "sprinkler", "evac", "ventila", "abatimento", "fire"]):
        score_map["Mitigation"] = 1

    values = [score_map[k] for k in labels]

    fig, ax = plt.subplots(figsize=(8.2, 3.0))
    x = np.arange(len(labels))
    ax.bar(x, values)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylim(0, 1.3)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["missing", "present"])
    ax.set_title("Protection Layers Snapshot")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return fig


def build_incompatibility_matrix_figure(profile: Any):
    matrix = getattr(profile, "incompatibility_matrix", [])
    labels = [row["category"] for row in matrix] if matrix else ["No data"]
    status = [row["status"] for row in matrix] if matrix else ["Review"]

    mapping = {
        "Compatible": 1,
        "Caution": 2,
        "Incompatible": 3,
        "Review": 0,
    }

    values = [mapping.get(s, 0) for s in status]
    arr = np.array(values).reshape(1, len(values))

    fig, ax = plt.subplots(figsize=(8.6, 2.4))
    ax.imshow(arr, aspect="auto")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_yticks([0])
    ax.set_yticklabels(["Status"])
    ax.set_title("Incompatibility Matrix")

    for j, s in enumerate(status):
        ax.text(j, 0, s, ha="center", va="center", fontsize=8)

    fig.tight_layout()
    return fig
