from __future__ import annotations
import folium
from folium.plugins import MeasureControl

def build_risk_map(lat: float, lon: float, zones: list[dict]):
    """
    Constrói um mapa interativo com zonas de risco (círculos) sobrepostas.
    zones =[{"radius": 150, "color": "red", "label": "Zona Letal (IDLH)"}]
    """
    # Cria o mapa focado na coordenada com visão de satélite
    m = folium.Map(location=[lat, lon], zoom_start=15, tiles="CartoDB positron")
    
    # Adiciona a ferramenta de medição (para o engenheiro medir distâncias no mapa)
    m.add_child(MeasureControl(position='topleft', primary_length_unit='meters'))
    
    # Marcador central (A origem do vazamento/fogo)
    folium.Marker(
        [lat, lon],
        popup="Origem do Cenário",
        icon=folium.Icon(color="black", icon="fire", prefix="fa")
    ).add_to(m)
    
    # Desenha os círculos de impacto ordenados (do maior para o menor para não sobrepor)
    zones.sort(key=lambda x: x["radius"], reverse=True)
    
    for zone in zones:
        folium.Circle(
            radius=zone["radius"],
            location=[lat, lon],
            popup=zone["label"],
            color=zone["color"],
            fill=True,
            fill_color=zone["color"],
            fill_opacity=0.3
        ).add_to(m)

    return m
