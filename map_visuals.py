# map_visuals.py
import folium
from folium.plugins import MeasureControl
import streamlit as st
from streamlit_folium import st_folium

def build_risk_map(lat: float, lon: float, zones: list[dict]):
    """
    Constrói um mapa de engenharia com as zonas de impacto reais.
    """
    # Cria o mapa base centrado na coordenada
    m = folium.Map(location=[lat, lon], zoom_start=15, control_scale=True)
    
    # Camada 1: Mapa de Satélite (Esri)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satélite',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Camada 2: Mapa Claro (CartoDB Positron - bom para relatórios impressos)
    folium.TileLayer(
        tiles='CartoDB positron',
        name='Mapa Claro (Relatório)',
        overlay=False,
        control=True
    ).add_to(m)

    # Ferramenta para o engenheiro medir distâncias no mapa (ex: até casas ou vias)
    m.add_child(MeasureControl(position='topleft', primary_length_unit='meters'))
    
    # Marcador central da falha/vazamento
    folium.Marker(
        [lat, lon],
        popup="<b>Origem do Cenário</b><br>Ponto de Liberação",
        icon=folium.Icon(color="black", icon="fire", prefix="fa")
    ).add_to(m)
    
    # Ordenar zonas do maior para o menor raio para não haver sobreposição de cores
    zones.sort(key=lambda x: x.get("radius", 0), reverse=True)
    
    for zone in zones:
        radius = zone.get("radius", 0)
        if radius <= 0:
            continue
            
        color = zone.get("color", "red")
        label = zone.get("label", "Zona de Impacto")
        details = zone.get("details", "")
        
        # Popup com metadados técnicos
        popup_html = f"""
        <div style='font-family: sans-serif;'>
            <b>{label}</b><br>
            <b>Raio de Impacto:</b> {radius:.1f} m<br>
            <hr style='margin: 5px 0;'>
            <i>{details}</i>
        </div>
        """
        
        folium.Circle(
            radius=radius,
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.3,
            weight=2
        ).add_to(m)

    # Controle para alternar entre satélite e mapa claro
    folium.LayerControl(position='topright').add_to(m)
    
    return m

def build_zones_from_results(dispersion_data=None, thermal_data=None):
    """
    Puxa os dados das simulações (ex: st.session_state) e converte em zonas.
    """
    zones = []
    
    # Lógica para Dispersão Tóxica / Inflamável
    if dispersion_data:
        if dispersion_data.get("idlh_radius"):
            zones.append({
                "radius": dispersion_data["idlh_radius"], 
                "color": "#8B0000", # Vermelho Escuro
                "label": "Zona Letal (IDLH)", 
                "details": "Concentração Imediatamente Perigosa à Vida e à Saúde."
            })
        if dispersion_data.get("erpg2_radius"):
            zones.append({
                "radius": dispersion_data["erpg2_radius"], 
                "color": "#FF8C00", # Laranja
                "label": "Zona de Atenção (ERPG-2)", 
                "details": "Danos reversíveis. Rotas de fuga comprometidas."
            })

    # Lógica para Radiação Térmica (Pool Fire / Jet Fire)
    if thermal_data:
        if thermal_data.get("rad_37_5"):
            zones.append({
                "radius": thermal_data["rad_37_5"], 
                "color": "red", 
                "label": "Dano Estrutural / Letalidade 100%", 
                "details": "Radiação: 37.5 kW/m²."
            })
        if thermal_data.get("rad_4_7"):
            zones.append({
                "radius": thermal_data["rad_4_7"], 
                "color": "yellow", 
                "label": "Zona de Ferimentos Graves", 
                "details": "Radiação: 4.7 kW/m². Queimaduras de 2º grau em 20s."
            })
            
    # Mock de fallback inicial caso o engine ainda não retorne dados exatos
    if not zones:
        zones = [
            {"radius": 150, "color": "orange", "label": "Zona de Isolamento", "details": "Isolamento inicial padrão (Mock)"},
            {"radius": 50, "color": "red", "label": "Zona de Risco Imediato", "details": "Centro térmico/tóxico (Mock)"}
        ]
        
    return zones

def render_map_in_streamlit(lat: float, lon: float, dispersion_data=None, thermal_data=None):
    """
    Renderiza o mapa de forma segura dentro do layout do Streamlit.
    """
    zones = build_zones_from_results(dispersion_data, thermal_data)
    
    if not zones:
        st.warning("Nenhum dado de consequência disponível para mapeamento.")
        return
        
    m = build_risk_map(lat, lon, zones)
    # returned_objects=[] previne que o app recarregue toda vez que o usuário clica no mapa
    st_folium(m, width=1000, height=600, returned_objects=[])
