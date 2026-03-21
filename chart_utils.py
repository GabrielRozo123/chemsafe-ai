from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from action_processing import sanitize_and_translate_action_df


def is_valid_df(df):
    return isinstance(df, pd.DataFrame) and not df.empty


def safe_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def render_modern_gauge(score, band):
    color = "#10b981" if score >= 80 else "#f59e0b" if score >= 50 else "#ef4444"
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "%", "font": {"color": "white", "size": 45}},
            title={
                "text": f"Status Atual:<br><span style='font-size:1.4em; color:{color}; font-weight:800;'>{band}</span>",
                "font": {"color": "#9ca3af", "size": 14},
            },
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#30363d"},
                "bar": {"color": color},
                "bgcolor": "rgba(255,255,255,0.05)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 50], "color": "rgba(239, 68, 68, 0.15)"},
                    {"range": [50, 80], "color": "rgba(245, 158, 11, 0.15)"},
                    {"range": [80, 100], "color": "rgba(16, 185, 129, 0.15)"},
                ],
            },
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter"},
        margin=dict(t=50, b=10, l=10, r=10),
        height=300,
    )
    return fig


def render_modern_radar(cri_data):
    base = cri_data.get("index", 50)
    categories = ["Engenharia/Dados", "PHA/Perigos", "LOPA/Barreiras", "MOC/PSSR"]
    values = [min(100, base + 12), min(100, base - 5), min(100, base + 8), min(100, base - 10)]
    categories.append(categories[0])
    values.append(values[0])

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=categories,
            fill="toself",
            fillcolor="rgba(59, 130, 246, 0.3)",
            line=dict(color="#3b82f6", width=2),
            marker=dict(color="#ffffff", size=6),
        )
    )
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                color="#6b7280",
                gridcolor="#30363d",
                linecolor="rgba(0,0,0,0)",
            ),
            angularaxis=dict(
                color="#d1d5db",
                gridcolor="#30363d",
                linecolor="rgba(0,0,0,0)",
            ),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=30, b=20, l=40, r=40),
        height=300,
    )
    return fig


def render_action_donut(df):
    if not is_valid_df(df):
        return go.Figure()

    base_df = sanitize_and_translate_action_df(df)
    if "Status" not in base_df.columns:
        return go.Figure()
    if "Responsável" not in base_df.columns:
        base_df["Responsável"] = "Engenharia"

    abertas = base_df[base_df["Status"] != "Fechado"]
    if abertas.empty:
        return go.Figure()

    count_df = abertas["Responsável"].value_counts().reset_index()
    count_df.columns = ["Responsável", "Count"]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=count_df["Responsável"],
                values=count_df["Count"],
                hole=0.5,
                marker=dict(colors=["#3b82f6", "#f59e0b", "#ef4444", "#10b981"]),
            )
        ]
    )
    fig.update_layout(
        title=dict(text="Ações Abertas por Equipe", font=dict(color="#d1d5db", size=14)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9ca3af", family="Inter"),
        margin=dict(t=40, b=10, l=10, r=10),
        height=250,
        showlegend=True,
        legend=dict(orientation="v", y=0.5, x=1.0),
    )
    return fig


def render_action_bar(df):
    if not is_valid_df(df):
        return go.Figure()

    base_df = sanitize_and_translate_action_df(df)
    if "Status" not in base_df.columns:
        return go.Figure()
    if "Criticidade" not in base_df.columns:
        base_df["Criticidade"] = "Média"

    count_df = base_df.groupby(["Criticidade", "Status"]).size().reset_index(name="Count")
    fig = px.bar(
        count_df,
        x="Criticidade",
        y="Count",
        color="Status",
        color_discrete_map={
            "Aberto": "#ef4444",
            "Em Andamento": "#f59e0b",
            "Aguardando Verba": "#8b5cf6",
            "Fechado": "#10b981",
        },
        barmode="group",
    )
    fig.update_layout(
        title=dict(text="Distribuição de Risco", font=dict(color="#d1d5db", size=14)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9ca3af", family="Inter"),
        margin=dict(t=40, b=10, l=10, r=10),
        height=250,
        xaxis=dict(title="", showgrid=False),
        yaxis=dict(title="", showgrid=True, gridcolor="#30363d"),
    )
    return fig


def render_flammability_envelope(lfl, ufl, loc):
    fig = go.Figure()
    x_o2 = [0, loc, 21, 21, 0]
    y_fuel = [0, lfl, lfl, ufl, 0]

    fig.add_trace(
        go.Scatter(
            x=x_o2,
            y=y_fuel,
            fill="toself",
            fillcolor="rgba(239, 68, 68, 0.2)",
            line=dict(color="#ef4444", width=2),
            name="Zona de Explosão",
        )
    )
    safe_margin_o2 = loc * 0.6
    fig.add_trace(
        go.Scatter(
            x=[safe_margin_o2],
            y=[lfl / 2],
            mode="markers+text",
            marker=dict(color="#10b981", size=12),
            text=["Zona Segura (Purga)"],
            textposition="bottom center",
            name="Margem Segura",
        )
    )
    fig.update_layout(
        title="Envelope de Inflamabilidade (O₂ vs Combustível)",
        xaxis_title="Concentração de Oxigênio (% vol)",
        yaxis_title="Concentração de Combustível (% vol)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.02)",
        font_color="#9ca3af",
        xaxis=dict(range=[0, 25], gridcolor="#30363d"),
        yaxis=dict(range=[0, min(ufl * 1.5, 100)], gridcolor="#30363d"),
        height=350,
        margin=dict(t=40, b=40, l=40, r=20),
    )
    return fig
