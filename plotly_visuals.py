# plotly_visuals.py
from __future__ import annotations
import plotly.graph_objects as go
from PIL import Image

def build_executive_gauge(cri_index: float, band: str) -> go.Figure:
    """
    Constrói um medidor (Gauge) interativo estilo BI para o Índice de Prontidão.
    """
    # Mapeamento de cores
    if cri_index >= 80:
        color = "#10b981" # Green
    elif cri_index >= 50:
        color = "#f59e0b" # Amber
    else:
        color = "#ef4444" # Red

    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = cri_index,
        number = {'suffix': "%", 'font': {'color': 'white', 'size': 40}},
        title = {'text': f"Prontidão Global<br><span style='font-size:0.8em;color:gray'>{band}</span>", 'font': {'color': '#9ca3af'}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': color},
            'bgcolor': "rgba(255,255,255,0.1)",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 50], 'color': "rgba(239, 68, 68, 0.15)"},
                {'range': [50, 80], 'color': "rgba(245, 158, 11, 0.15)"},
                {'range': [80, 100], 'color': "rgba(16, 185, 129, 0.15)"}],
        }
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", 
        font={'color': "#d1d5db", 'family': "Inter"}, 
        margin=dict(l=20, r=20, t=30, b=20), 
        height=280
    )
    return fig

def build_radar_chart() -> go.Figure:
    """
    Constrói um gráfico de radar interativo para os pilares de maturidade.
    (Valores simulados para demonstração do design).
    """
    categories = ['Dados Químicos', 'Engenharia P&ID', 'LOPA/Risco', 'MOC/PSSR']
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[85, 90, 75, 60],
        theta=categories,
        fill='toself',
        fillcolor='rgba(59, 130, 246, 0.3)',
        line_color='#3b82f6',
        name='Maturidade Atual'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], color="#9ca3af", gridcolor="rgba(255,255,255,0.1)"),
            angularaxis=dict(color="#d1d5db")
        ),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#d1d5db", family="Inter"),
        margin=dict(l=40, r=40, t=20, b=20),
        height=280
    )
    return fig

def build_plant_layout_heatmap(image_file, scale_m_px: float, x_origin: int, y_origin: int, zones: list[dict]) -> go.Figure:
    """
    Sobrepõe zonas de risco (Heatmaps) em uma imagem 2D da planta real (Layout/Plot Plan).
    """
    img = Image.open(image_file)
    width, height = img.size

    fig = go.Figure()

    # Adiciona a imagem da planta como fundo
    fig.add_layout_image(
        dict(
            source=img, xref="x", yref="y",
            x=0, y=height, sizex=width, sizey=height,
            sizing="stretch", opacity=0.85, layer="below"
        )
    )

    # Desenha as zonas térmicas/tóxicas sobrepostas
    # Ordena do maior raio para o menor para garantir visibilidade
    for zone in sorted(zones, key=lambda x: x['radius_m'], reverse=True):
        r_px = zone['radius_m'] / scale_m_px
        
        # Cor de preenchimento com transparência
        fill_hex = zone['color'].replace("red", "#ef4444").replace("orange", "#f59e0b").replace("yellow", "#eab308").replace("darkred", "#991b1b")
        
        fig.add_shape(
            type="circle",
            xref="x", yref="y",
            x0=x_origin - r_px, y0=y_origin - r_px,
            x1=x_origin + r_px, y1=y_origin + r_px,
            fillcolor=fill_hex,
            opacity=0.4,
            line_color=fill_hex,
            line_width=2,
        )
        
        # Label do anel
        fig.add_annotation(
            x=x_origin, y=y_origin + r_px,
            text=f"{zone['label']} ({zone['radius_m']}m)",
            showarrow=False,
            font=dict(color="white", size=11, family="Inter"),
            bgcolor="rgba(0,0,0,0.6)"
        )

    # Marca a origem do vazamento/fogo
    fig.add_trace(go.Scatter(
        x=[x_origin], y=[y_origin],
        mode='markers',
        marker=dict(size=14, color='white', symbol='x', line=dict(color='black', width=2)),
        name='Origem do Evento',
        hoverinfo='name'
    ))

    fig.update_layout(
        xaxis=dict(visible=False, range=[0, width]),
        yaxis=dict(visible=False, range=[0, height]),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=650,
        dragmode="pan" # Permite navegar pela planta
    )
    return fig
