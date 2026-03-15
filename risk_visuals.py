from __future__ import annotations

from typing import Any, Iterable, List

import matplotlib.pyplot as plt
import numpy as np


def build_hazard_fingerprint_figure(profile: Any):
    labels = list(profile.fingerprint.keys())
    values = [profile.fingerprint[k] for k in labels]

    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    y = np.arange(len(labels))
    ax.barh(y, values)
    ax.set_yticks(y)
    ax.set_yticklabels([lbl.replace("_", " ").title() for lbl in labels])
    ax.set_xlim(0, 4.2)
    ax.set_xlabel("Score")
    ax.set_title("Hazard Fingerprint")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    return fig


def build_source_coverage_figure(profile: Any):
    counts = {}
    for row in getattr(profile, "source_trace", []):
        src = row.get("source", "unknown")
        counts[src] = counts.get(src, 0) + 1

    labels = list(counts.keys()) or ["no data"]
    values = list(counts.values()) or [0]

    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    x = np.arange(len(labels))
    ax.bar(x, values)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylabel("Fields")
    ax.set_title("Source Coverage")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return fig


def build_risk_matrix_figure(priorities: Iterable[dict]):
    fig, ax = plt.subplots(figsize=(5.8, 4.8))
    grid = np.arange(1, 26).reshape(5, 5)
    ax.imshow(grid, origin="lower")

    ax.set_xticks(range(5))
    ax.set_yticks(range(5))
    ax.set_xticklabels(["1", "2", "3", "4", "5"])
    ax.set_yticklabels(["1", "2", "3", "4", "5"])
    ax.set_xlabel("Likelihood")
    ax.set_ylabel("Severity")
    ax.set_title("Risk Matrix")

    for i in range(5):
        for j in range(5):
            ax.text(j, i, str((i + 1) * (j + 1)), ha="center", va="center", fontsize=8)

    for item in priorities:
        sev = int(item.get("severity_score", 3))
        lik = int(item.get("likelihood_score", 3))
        ax.plot(lik - 1, sev - 1, "o", markersize=10)
        ax.text(lik - 1 + 0.08, sev - 1 + 0.08, item.get("focus", "")[:12], fontsize=7)

    fig.tight_layout()
    return fig


def build_ipl_layers_figure(selected_ipls: List[str], suggested_ipls: List[str]):
    labels = ["Initiating event", "BPCS/Alarm", "Operator", "SIS", "Relief", "Containment", "Fire/Toxic Mitigation"]
    score_map = {
        "Initiating event": 1,
        "BPCS/Alarm": 0,
        "Operator": 0,
        "SIS": 0,
        "Relief": 0,
        "Containment": 0,
        "Fire/Toxic Mitigation": 0,
    }

    for text in suggested_ipls + selected_ipls:
        t = text.lower()
        if "alarm" in t or "detecção" in t or "deteccao" in t:
            score_map["BPCS/Alarm"] = 1
        if "operador" in t:
            score_map["Operator"] = 1
        if "sis" in t or "trip" in t or "esd" in t or "isolamento remoto" in t:
            score_map["SIS"] = 1
        if "psv" in t or "rupture" in t or "disco" in t or "relief" in t or "alívio" in t:
            score_map["Relief"] = 1
        if "dique" in t or "contain" in t or "contenção" in t or "containment" in t:
            score_map["Containment"] = 1
        if "foam" in t or "espuma" in t or "sprinkler" in t or "evac" in t or "ventila" in t or "abatimento" in t:
            score_map["Fire/Toxic Mitigation"] = 1

    values = [score_map[k] for k in labels]

    fig, ax = plt.subplots(figsize=(8.0, 2.6))
    x = np.arange(len(labels))
    ax.bar(x, values)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylim(0, 1.4)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["missing", "present"])
    ax.set_title("Protection Layers Snapshot")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return fig
