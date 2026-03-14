"""
ChemSafe Pro — app.py v2.0
Plataforma completa de segurança de processo para engenheiros
Gabriel Hernandez Rozo — linkedin.com/in/gabriel-hernandez-rozo-30751325b
"""

import streamlit as st
import io, os, re, json, time, math
import requests
from datetime import date, datetime
import pandas as pd

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="ChemSafe Pro",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://www.linkedin.com/in/gabriel-hernandez-rozo-30751325b",
        "Report a bug": None,
        "About": "ChemSafe Pro v2.0 — Plataforma de Segurança Química Avançada\nDesenvolvido por Gabriel Hernandez Rozo\nlinkedin.com/in/gabriel-hernandez-rozo-30751325b",
    }
)

# ── CSS completo — design industrial profissional ─────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');

/* Reset e base */
*, *::before, *::after { box-sizing: border-box; }
.stApp { background: #0A0E1A; font-family: 'IBM Plex Sans', sans-serif; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0D1220 !important;
    border-right: 1px solid #1E2940;
}
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    background: transparent;
    border: 1px solid #1E2940;
    color: #8899BB;
    border-radius: 6px;
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.82rem;
    padding: 0.45rem 0.75rem;
    text-align: left;
    transition: all 0.2s;
    margin-bottom: 3px;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #162035;
    border-color: #2D5FA6;
    color: #C8D8F5;
}

/* Cabeçalho principal */
.cs-header {
    background: linear-gradient(135deg, #0D1525 0%, #142040 50%, #0D1525 100%);
    border: 1px solid #1E3060;
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.cs-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #1A4BCC, #2D8FE8, #1A4BCC);
}
.cs-header h1 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    color: #E8F0FF;
    margin: 0 0 0.25rem 0;
    letter-spacing: -0.02em;
}
.cs-header p {
    color: #6B82AA;
    font-size: 0.85rem;
    margin: 0;
    font-weight: 300;
}
.cs-badge {
    display: inline-block;
    background: rgba(45,95,166,0.2);
    border: 1px solid #2D5FA6;
    color: #7AAEF5;
    font-size: 0.7rem;
    padding: 2px 8px;
    border-radius: 4px;
    font-family: 'IBM Plex Mono', monospace;
    margin-right: 6px;
    margin-top: 8px;
}

/* Cards */
.cs-card {
    background: #0D1525;
    border: 1px solid #1A2A45;
    border-radius: 10px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    position: relative;
}
.cs-card-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.9rem;
    font-weight: 600;
    color: #C5D5F0;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
.cs-card-title .dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #2D8FE8;
    flex-shrink: 0;
}

/* Metrics */
.cs-metric {
    background: #080D18;
    border: 1px solid #1A2A45;
    border-radius: 8px;
    padding: 0.875rem 1rem;
    text-align: center;
}
.cs-metric .label {
    font-size: 0.7rem;
    color: #4A6080;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 6px;
    font-weight: 500;
}
.cs-metric .value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.4rem;
    font-weight: 600;
    color: #E8F0FF;
}
.cs-metric .value.red   { color: #F04545; }
.cs-metric .value.amber { color: #F5A623; }
.cs-metric .value.green { color: #2DD4A0; }
.cs-metric .value.blue  { color: #4DA6F5; }

/* Pills / badges */
.pill { display:inline-block; font-size:0.7rem; padding:2px 8px; border-radius:4px; font-weight:500; margin:2px; }
.pill-r { background:rgba(240,69,69,0.15); color:#F04545; border:1px solid rgba(240,69,69,0.3); }
.pill-a { background:rgba(245,166,35,0.15); color:#F5A623; border:1px solid rgba(245,166,35,0.3); }
.pill-g { background:rgba(45,212,160,0.15); color:#2DD4A0; border:1px solid rgba(45,212,160,0.3); }
.pill-b { background:rgba(77,166,245,0.15); color:#4DA6F5; border:1px solid rgba(77,166,245,0.3); }
.pill-p { background:rgba(150,120,240,0.15); color:#9678F0; border:1px solid rgba(150,120,240,0.3); }

/* Hazard boxes */
.hazard-item {
    background: rgba(240,69,69,0.06);
    border-left: 3px solid #F04545;
    border-radius: 0 6px 6px 0;
    padding: 0.5rem 0.75rem;
    margin-bottom: 6px;
    font-size: 0.85rem;
    color: #FFBBBB;
}
.warn-item {
    background: rgba(245,166,35,0.06);
    border-left: 3px solid #F5A623;
    border-radius: 0 6px 6px 0;
    padding: 0.5rem 0.75rem;
    margin-bottom: 6px;
    font-size: 0.85rem;
    color: #FFE0A0;
}

/* Tabela HAZOP */
.hazop-grid {
    display: grid;
    grid-template-columns: 120px 140px 160px 1fr 90px 160px;
    gap: 4px;
    font-size: 0.78rem;
    margin-top: 0.75rem;
}
.hg-header { color: #4A6080; font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.08em; padding: 6px 8px; font-weight: 500; }
.hg-cell {
    background: #080D18;
    border: 1px solid #1A2A45;
    border-radius: 5px;
    padding: 7px 9px;
    color: #8899BB;
    line-height: 1.4;
}
.hg-cell.accent { border-left: 2px solid #2D5FA6; }

/* Bowtie */
.bowtie-container {
    background: #080D18;
    border: 1px solid #1A2A45;
    border-radius: 10px;
    padding: 1rem;
    overflow-x: auto;
}

/* Fórmula */
.formula-block {
    background: #060A12;
    border: 1px solid #1A2A45;
    border-left: 3px solid #2D5FA6;
    border-radius: 0 8px 8px 0;
    padding: 0.875rem 1rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: #7AAEF5;
    line-height: 2;
    margin: 0.75rem 0;
    white-space: pre-wrap;
}

/* Inputs */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div > div {
    background: #080D18 !important;
    border-color: #1A2A45 !important;
    color: #C5D5F0 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    border-radius: 6px !important;
    font-size: 0.85rem !important;
}
.stTextInput label, .stNumberInput label, .stSelectbox label,
.stSlider label, .stMultiSelect label {
    color: #6B82AA !important;
    font-size: 0.8rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.02em;
}

/* Botões */
.stButton > button {
    background: transparent;
    border: 1px solid #2D5FA6;
    color: #7AAEF5;
    font-family: 'IBM Plex Sans', sans-serif;
    border-radius: 6px;
    font-size: 0.82rem;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: rgba(45,95,166,0.2);
    border-color: #4D8FD6;
    color: #AACFF5;
}
.stButton > button[kind="primary"] {
    background: #1A3D7A;
    border-color: #2D5FA6;
    color: #C5DEFF;
    font-weight: 500;
}
.stButton > button[kind="primary"]:hover {
    background: #234D9A;
    border-color: #4D8FD6;
}

/* Download button */
.stDownloadButton > button {
    background: #0E2040 !important;
    border: 1px solid #2D5FA6 !important;
    color: #7AAEF5 !important;
    width: 100%;
    font-family: 'IBM Plex Sans', sans-serif !important;
    border-radius: 6px !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    padding: 0.6rem 1rem !important;
    margin-top: 0.5rem;
}
.stDownloadButton > button:hover {
    background: #162B5A !important;
    border-color: #4D8FD6 !important;
    color: #AACFF5 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 1px solid #1A2A45;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #4A6080;
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.82rem;
    padding: 0.6rem 1rem;
    border-radius: 6px 6px 0 0;
    border: none;
    transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
    background: #0D1525 !important;
    color: #7AAEF5 !important;
    border-top: 2px solid #2D5FA6 !important;
    font-weight: 500 !important;
}

/* Alert success/info/warning/error */
.stAlert { border-radius: 8px; font-size: 0.85rem; }
.stSuccess { background: rgba(45,212,160,0.08) !important; border-color: rgba(45,212,160,0.3) !important; }
.stError { background: rgba(240,69,69,0.08) !important; border-color: rgba(240,69,69,0.3) !important; }
.stWarning { background: rgba(245,166,35,0.08) !important; border-color: rgba(245,166,35,0.3) !important; }
.stInfo { background: rgba(77,166,245,0.08) !important; border-color: rgba(77,166,245,0.3) !important; }

/* DataFrame */
.stDataFrame { border-radius: 8px; overflow: hidden; }

/* Sobre */
.about-hero {
    background: linear-gradient(135deg, #0D1525 0%, #0A1830 100%);
    border: 1px solid #1E3060;
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.about-hero::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #2D8FE8, transparent);
}
.about-avatar {
    width: 80px; height: 80px;
    border-radius: 50%;
    background: linear-gradient(135deg, #1A3D7A, #2D8FE8);
    display: flex; align-items: center; justify-content: center;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.8rem; font-weight: 700;
    color: #E8F0FF;
    margin: 0 auto 1rem;
    border: 2px solid #2D5FA6;
}
.about-name {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.3rem; font-weight: 600;
    color: #E8F0FF;
    margin-bottom: 0.25rem;
}
.about-role {
    color: #6B82AA;
    font-size: 0.9rem;
    margin-bottom: 1rem;
}
.linkedin-btn {
    display: inline-block;
    background: #0A66C2;
    color: white !important;
    padding: 0.5rem 1.25rem;
    border-radius: 6px;
    text-decoration: none;
    font-size: 0.85rem;
    font-weight: 500;
    transition: all 0.2s;
    border: none;
}
.linkedin-btn:hover { background: #0856A5; }

/* Divider */
.cs-divider {
    border: none;
    border-top: 1px solid #1A2A45;
    margin: 1rem 0;
}

/* Ref item */
.ref-block {
    background: #080D18;
    border: 1px solid #1A2A45;
    border-radius: 8px;
    padding: 0.875rem 1rem;
    margin-bottom: 0.75rem;
}
.ref-title { font-size: 0.85rem; font-weight: 500; color: #C5D5F0; margin-bottom: 4px; }
.ref-meta { font-size: 0.75rem; color: #4A6080; line-height: 1.6; }

/* SIL display */
.sil-box {
    border: 1px solid;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
    font-family: 'IBM Plex Mono', monospace;
}
.sil-ok { border-color: rgba(45,212,160,0.4); background: rgba(45,212,160,0.05); }
.sil-1  { border-color: rgba(245,166,35,0.4);  background: rgba(245,166,35,0.05); }
.sil-2  { border-color: rgba(240,130,40,0.4);  background: rgba(240,130,40,0.05); }
.sil-3  { border-color: rgba(240,69,69,0.4);   background: rgba(240,69,69,0.05); }
.sil-label { font-size: 0.7rem; color: #4A6080; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 4px; }
.sil-value { font-size: 2rem; font-weight: 600; }

/* Status dot */
.status-dot { display:inline-block; width:7px; height:7px; border-radius:50%; margin-right:5px; }
.dot-ok  { background:#2DD4A0; box-shadow: 0 0 6px rgba(45,212,160,0.6); }
.dot-off { background:#1A2A45; }
.dot-err { background:#F04545; }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
#  BANCO DE DADOS LOCAL
# ════════════════════════════════════════════════════════════════════════════
DB = {
    "ethanol": {
        "nome":"Etanol","formula":"C₂H₅OH","cas":"64-17-5","pm":"46.07","cid":702,
        "hazards":["H225 — Líquido e vapor muito inflamáveis (Cat. 2)",
                   "H319 — Provoca irritação ocular grave (Cat. 2A)",
                   "H336 — Pode provocar sonolência ou vertigens (Cat. 3)"],
        "pics":["GHS02 Inflamável","GHS07 Irritante"],"sinal":"Perigo",
        "props":[("Ponto de ebulição","78.4 °C"),("Ponto de fusão","-114.1 °C"),
                 ("Ponto de fulgor","13 °C"),("LIE / LSE","3.3 % / 19 %"),
                 ("AIT (Autoignição)","365 °C"),("Densidade","0.789 g/cm³"),
                 ("Pressão de vapor (20°C)","5.8 kPa"),("TLV-TWA","1000 ppm"),
                 ("IDLH","3300 ppm"),("MIE","0.65 mJ")],
        "nfpa":(2,3,0,""),"lie":3.3,"lse":19.0,"flash_c":13,"ait":365,"mie":0.65,
    },
    "acetone": {
        "nome":"Acetona","formula":"C₃H₆O","cas":"67-64-1","pm":"58.08","cid":180,
        "hazards":["H225 — Líquido e vapor extremamente inflamáveis (Cat. 1)",
                   "H319 — Provoca irritação ocular grave (Cat. 2A)",
                   "H336 — Pode provocar sonolência ou vertigens (Cat. 3)"],
        "pics":["GHS02 Inflamável","GHS07 Irritante"],"sinal":"Perigo",
        "props":[("Ponto de ebulição","56.1 °C"),("Ponto de fusão","-94.7 °C"),
                 ("Ponto de fulgor","-18 °C"),("LIE / LSE","2.5 % / 12.8 %"),
                 ("AIT (Autoignição)","465 °C"),("Densidade","0.791 g/cm³"),
                 ("Pressão de vapor (20°C)","23.5 kPa"),("TLV-TWA","500 ppm"),
                 ("IDLH","2500 ppm"),("MIE","1.15 mJ")],
        "nfpa":(1,3,0,""),"lie":2.5,"lse":12.8,"flash_c":-18,"ait":465,"mie":1.15,
    },
    "h2so4": {
        "nome":"Ácido Sulfúrico","formula":"H₂SO₄","cas":"7664-93-9","pm":"98.07","cid":1118,
        "hazards":["H314 — Provoca queimaduras graves na pele e nos olhos (Cat. 1A)",
                   "H335 — Pode irritar as vias respiratórias (Cat. 3)"],
        "pics":["GHS05 Corrosivo","GHS07 Irritante"],"sinal":"Perigo",
        "props":[("Ponto de ebulição","337 °C"),("Ponto de fusão","10 °C"),
                 ("Ponto de fulgor","Não inflamável"),("LIE / LSE","N/A"),
                 ("Densidade","1.84 g/cm³"),("pH (1 mol/L)","~0"),
                 ("TLV-STEL","0.2 mg/m³"),("IDLH","15 mg/m³")],
        "nfpa":(3,0,2,"W"),"lie":None,"lse":None,"flash_c":None,"ait":None,"mie":None,
    },
    "ammonia": {
        "nome":"Amônia","formula":"NH₃","cas":"7664-41-7","pm":"17.03","cid":222,
        "hazards":["H221 — Gás inflamável (Cat. 2)",
                   "H314 — Provoca queimaduras graves na pele e nos olhos (Cat. 1A)",
                   "H331 — Tóxico por inalação (Cat. 3)",
                   "H400 — Muito tóxico para organismos aquáticos (Cat. 1)"],
        "pics":["GHS02","GHS05","GHS06","GHS09"],"sinal":"Perigo",
        "props":[("Ponto de ebulição","-33.3 °C"),("Ponto de fusão","-77.7 °C"),
                 ("Ponto de fulgor","11 °C (aq)"),("LIE / LSE","15 % / 28 %"),
                 ("AIT (Autoignição)","651 °C"),("IDLH","300 ppm"),
                 ("TLV-TWA","25 ppm"),("ERPG-2","200 ppm"),("ERPG-3","1000 ppm")],
        "nfpa":(3,1,0,""),"lie":15.0,"lse":28.0,"flash_c":11,"ait":651,"mie":680,
    },
    "methane": {
        "nome":"Metano","formula":"CH₄","cas":"74-82-8","pm":"16.04","cid":297,
        "hazards":["H220 — Gás extremamente inflamável (Cat. 1A)",
                   "H280 — Contém gás sob pressão"],
        "pics":["GHS02","GHS04"],"sinal":"Perigo",
        "props":[("Ponto de ebulição","-161.5 °C"),("Ponto de fusão","-182.5 °C"),
                 ("LIE / LSE","5 % / 15 %"),("AIT (Autoignição)","537 °C"),
                 ("Densidade gás","0.717 g/L"),("MIE","0.28 mJ"),
                 ("Chama visível","Não — invisível!")],
        "nfpa":(1,4,0,""),"lie":5.0,"lse":15.0,"flash_c":-188,"ait":537,"mie":0.28,
    },
    "toluene": {
        "nome":"Tolueno","formula":"C₇H₈","cas":"108-88-3","pm":"92.14","cid":1140,
        "hazards":["H225 — Líquido e vapor muito inflamáveis (Cat. 2)",
                   "H304 — Pode ser fatal por ingestão e penetração nas vias respiratórias (Cat. 1)",
                   "H315 — Provoca irritação cutânea (Cat. 2)",
                   "H336 — Pode provocar sonolência ou vertigens (Cat. 3)",
                   "H361 — Suspeito de prejudicar a fertilidade ou o nascituro (Cat. 2)"],
        "pics":["GHS02","GHS07","GHS08"],"sinal":"Perigo",
        "props":[("Ponto de ebulição","110.6 °C"),("Ponto de fusão","-95 °C"),
                 ("Ponto de fulgor","4 °C"),("LIE / LSE","1.1 % / 7.1 %"),
                 ("AIT (Autoignição)","480 °C"),("Densidade","0.867 g/cm³"),
                 ("TLV-TWA","20 ppm"),("IDLH","500 ppm"),("MIE","0.24 mJ")],
        "nfpa":(2,3,0,""),"lie":1.1,"lse":7.1,"flash_c":4,"ait":480,"mie":0.24,
    },
}

MAPA = {"etanol":"ethanol","álcool etílico":"ethanol","alcohol":"ethanol",
        "acetona":"acetone","propanona":"acetone",
        "ácido sulfúrico":"h2so4","acido sulfurico":"h2so4","sulfuric acid":"h2so4",
        "amônia":"ammonia","amonia":"ammonia","azane":"ammonia",
        "metano":"methane","gás natural":"methane",
        "tolueno":"toluene","toluol":"toluene"}

def resolver(q):
    q = q.strip().lower()
    if q in DB: return DB[q]
    if q in MAPA: return DB[MAPA[q]]
    for k,v in DB.items():
        if (v["cas"]==q or
            v["formula"].lower().replace("₂","2").replace("₃","3").replace("₄","4")==q):
            return v
    return None

# HAZOP DB
HAZOP_DB = {
    "Temperatura":{"MAIS":{"causas":["Falha de válvula de controle (stuck open)","Falha no sistema de refrigeração/troca térmica","Reação exotérmica descontrolada (runaway)","Contaminação por catalisador não intencional","Incêndio externo"],"conseqs":["Decomposição térmica do produto","Pressurização acima do MAWP → ruptura do vaso","Formação de vapores inflamáveis acima do LIE","Emissão de gases tóxicos de decomposição","BLEVE se produto volátil inflamável"],"salvags":["TAH — alarme de alta temperatura (trip TAHH)","PSV/PRV calibrada para o máximo térmico","Chuveiro de emergência na área (TSH)","Procedimento operacional de emergência (POE)"],"rec":["Instalar TAHH independente do TAH (arquitetura SIS 1oo2)","Verificar SIL requerido pelo LOPA — provável SIL 1 ou 2","Calcular cenário de pool fire externo como evento iniciador adicional","Revisar redundância do sistema de resfriamento"]},"MENOS":{"causas":["Falha do sistema de aquecimento (vapor/elétrico)","Perda de utilidades","Contaminação com produto frio não previsto","Abertura indevida de by-pass de resfriamento"],"conseqs":["Solidificação / cristalização do produto → entupimento","Aumento de viscosidade → sobrecarga de bomba","Perda de reação → off-spec + descarte de batelada","Danos a equipamentos por variação brusca (thermal shock)"],"salvags":["TAL — alarme de baixa temperatura","Controlador de temperatura com set-point redundante"],"rec":["Instalar rastreamento elétrico com redundância em linhas críticas","Definir procedimento de arranque controlado com verificação de temperatura"]}},
    "Pressão":{"MAIS":{"causas":["Bloqueio de linha de saída (válvula fechada inadvertidamente)","Falha de válvula de controle de pressão (stuck open na entrada)","Reação exotérmica ou decomposição rápida","Falha do sistema de alívio (PSV travada fechada)","Superaquecimento por fogo externo (fire case)"],"conseqs":["Ruptura catastrófica do vaso (BLEVE)","Projeção de fragmentos e shrapnel","Incêndio e explosão se produto inflamável","Onda de sobrepressão — danos estruturais e lesões"],"salvags":["PSV (Válvula de alívio) com disco de ruptura a montante","PAHH com trip automático do feed","Sistema de despressurização de emergência (EDP)","Dique de contenção para líquidos inflamáveis"],"rec":["Calcular cenário de fire case conforme API 521","Verificar adequação da PSV para o caso de fogo externo","Instalar PAHH independente (SIL 2 se consequência for catastrófica)","Programa de inspeção periódica da PSV (NR-13)"]},"MENOS":{"causas":["Quebra de linha ou fuga em flange","Abertura inadvertida de ventilação para atmosfera","Condensação inesperada de vapor (vácuo por condensação)","Perda de carga por fuga significativa"],"conseqs":["Entrada de ar → atmosfera explosiva interna","Colapso mecânico do vaso sob vácuo (vaso não ranqueado para vácuo)","Contaminação atmosférica com produto tóxico","Perda de contenção do produto"],"salvags":["PAL — alarme de baixa pressão","Válvula de retenção (check valve) nas linhas de entrada","Inspeção periódica conforme NR-13"],"rec":["Verificar se o vaso é adequado para pressão interna negativa (vácuo)","Instalar proteção contra colapso por vácuo (rupture disk para vácuo)","Treinar operadores para sinais de fuga em flange"]}},
    "Fluxo (vazão)":{"NÃO / NENHUM":{"causas":["Falha de bomba (rolamento, cavitação, perda de NPSH)","Bloqueio de linha por corpo estranho / filtro entupido","Fechamento inadvertido de válvula de bloqueio","Perda de utilidades (energia elétrica)","Congelamento de linha em ambiente frio"],"conseqs":["Cavitação e dano mecânico na bomba","Superaquecimento de reator sem resfriamento adequado","Fluxo reverso → contaminação cruzada","Perda de produção — batelada fora de especificação"],"salvags":["FAL — alarme de baixa vazão","Check valve nas linhas de saída","Interlock de bomba stand-by com arranque automático (AOS)"],"rec":["Instalar bomba reserva 100% com arranque automático","Revisão do FMEA da bomba — priorizar rolamentos e selos","Instalar detector de bloqueio de filtro (pressão diferencial)"]},"MAIS":{"causas":["Falha de controlador de vazão (stuck open)","Rompimento da linha de by-pass de controle","Erro operacional (abertura excessiva de válvula manual)","Retorno de refluxo acima do projetado"],"conseqs":["Overfill de tanque → derramamento de produto perigoso","Inundação de vaso downstream → danos mecânicos","Carry-over de líquido para seção de vapor (liquid slugging)","Sobrepressão em equipamentos a jusante"],"salvags":["FAH — alarme de alta vazão","LSH — chave de alto nível com trip de bomba","LAHH com trip do feed"],"rec":["Instalar LAHH independente (arquitetura SIS diferente do BPCS)","Calcular cenário de overfill — risco de incêndio se produto inflamável"]}},
    "Nível":{"MAIS":{"causas":["Falha do controlador de nível (stuck open na entrada)","Bloqueio de linha de saída","Aumento não previsto de carga (feed extra)","Falha de instrumentação de nível (leitura baixa falsa → operador abre mais feed)"],"conseqs":["Overflow → derramamento de produto perigoso para bacia / solo","Carry-over de líquido para equipamento de vapor / compressor (dano mecânico)","Inundação de área → formação de nuvem inflamável ou tóxica"],"salvags":["LAH — alarme de alto nível","LAHH — chave de alto nível com trip de feed","Dique de contenção dimensionado para 110% do maior tanque (NR-20)"],"rec":["Verificar dimensionamento do dique conforme NR-20 Seção 15","Instalar LAHH em linha de instrumentação independente do LAH (SIS)","Checar FMEA do instrumento de nível — modos de falha que geram leitura baixa falsa"]},"MENOS":{"causas":["Fuga de produto pelo fundo do vaso","Excesso de saída (válvula presa aberta)","Falha de instrumentação (leitura alta falsa → operador fecha feed)","Vaporização excessiva por superaquecimento"],"conseqs":["Bomba seca → cavitação e dano mecânico","Perda de selo hidráulico → entrada de ar no sistema","Exposição de aquecedor/resistência → queima do elemento"],"salvags":["LAL — alarme de baixo nível","LALL com trip de bomba","Detector de fuga na bacia de contenção"],"rec":["Instalar detector de hidrocarboneto / produto no dique","Programa de inspeção de integridade do casco do vaso (NR-13)"]}},
}

# ── LOPA IPL defaults ─────────────────────────────────────────────────────────
IPL_CATALOG = [
    ("Válvula de alívio de pressão (PSV) — bem mantida",0.01),
    ("SIS / SIL 1 (IEC 61511) — verificado",0.01),
    ("SIS / SIL 2 (IEC 61511)",0.001),
    ("SIS / SIL 3 (IEC 61511)",0.0001),
    ("Alarme + ação do operador treinado (30 min)",0.1),
    ("Alarme + ação do operador treinado (10 min)",0.1),
    ("Dique de contenção — adequadamente dimensionado",0.01),
    ("Disco de ruptura — bem mantido",0.01),
    ("Procedimento administrativo com treinamento",0.1),
    ("Sistema de detecção e combate a incêndio (sprinkler)",0.01),
    ("Válvula de bloqueio de emergência (ESV) automática",0.01),
    ("Tanque de expansão / catch tank",0.01),
]

# ── Pasquill-Gifford coeficientes ─────────────────────────────────────────────
PG_COEF = {
    "A":{"a":0.22,"b":0.894,"c":0.20,"d":0.894},
    "B":{"a":0.16,"b":0.894,"c":0.12,"d":0.894},
    "C":{"a":0.11,"b":0.894,"c":0.08,"d":0.894},
    "D":{"a":0.08,"b":0.894,"c":0.06,"d":0.894},
    "E":{"a":0.06,"b":0.894,"c":0.03,"d":0.894},
    "F":{"a":0.04,"b":0.894,"c":0.016,"d":0.894},
}

# ── State ─────────────────────────────────────────────────────────────────────
if "dados"        not in st.session_state: st.session_state.dados = None
if "q_input"      not in st.session_state: st.session_state.q_input = ""
if "buscar"       not in st.session_state: st.session_state.buscar = False
if "ipls"         not in st.session_state: st.session_state.ipls = [("PSV — PFD 10⁻²", 0.01)]
if "hazop_gerado" not in st.session_state: st.session_state.hazop_gerado = None
if "lopa_result"  not in st.session_state: st.session_state.lopa_result = None
if "historico"    not in st.session_state: st.session_state.historico = []

# ════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='padding:0.75rem 0;'>
      <div style='font-family:Space Grotesk,sans-serif;font-size:1.1rem;font-weight:700;color:#E8F0FF;margin-bottom:2px;'>
        ⚗️ ChemSafe Pro
      </div>
      <div style='font-size:0.72rem;color:#4A6080;letter-spacing:0.05em;'>v2.0 · PROCESS SAFETY</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<hr style='border:none;border-top:1px solid #1A2A45;margin:0.5rem 0 1rem;'>", unsafe_allow_html=True)

    st.markdown("<div style='font-size:0.7rem;color:#4A6080;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;'>Status das integrações</div>", unsafe_allow_html=True)
    for name, status in [("PubChem API","ok"),("NIST WebBook","ok"),("Base GHS local","ok"),("API industrial","off")]:
        dot = "dot-ok" if status=="ok" else "dot-off"
        lbl = "Online" if status=="ok" else "Offline"
        cor_status = "#2DD4A0" if status=="ok" else "#1A2A45"
        st.markdown(f"<div style='font-size:0.78rem;color:#6B82AA;margin-bottom:3px;'><span class='status-dot {dot}'></span>{name} <span style='color:{cor_status};font-size:0.7rem;'>· {lbl}</span></div>", unsafe_allow_html=True)

    st.markdown("<hr style='border:none;border-top:1px solid #1A2A45;margin:0.75rem 0;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.7rem;color:#4A6080;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;'>Acesso rápido</div>", unsafe_allow_html=True)
    for label, key in [("Etanol (C₂H₅OH)","ethanol"),("Acetona (C₃H₆O)","acetone"),
                       ("Ácido Sulfúrico (H₂SO₄)","h2so4"),("Amônia (NH₃)","ammonia"),
                       ("Metano (CH₄)","methane"),("Tolueno (C₇H₈)","toluene")]:
        if st.button(label, key=f"sb_{key}"):
            st.session_state.q_input = key
            st.session_state.buscar = True

    if st.session_state.historico:
        st.markdown("<hr style='border:none;border-top:1px solid #1A2A45;margin:0.75rem 0;'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.7rem;color:#4A6080;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;'>Histórico</div>", unsafe_allow_html=True)
        for h in st.session_state.historico[-5:][::-1]:
            st.markdown(f"<div style='font-size:0.75rem;color:#4A6080;margin-bottom:2px;'>{h['hora']} · {h['nome']}</div>", unsafe_allow_html=True)

    st.markdown("<hr style='border:none;border-top:1px solid #1A2A45;margin:0.75rem 0;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.7rem;color:#2D5FA6;text-align:center;'>IEC 61882 · CCPS/AIChE · API RP 521<br>ABNT NBR 14725-4 · NR-26 · IEC 61511</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
#  HEADER
# ════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="cs-header">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1rem;">
    <div>
      <h1>ChemSafe Pro</h1>
      <p>Plataforma avançada de segurança de processo — HAZOP · LOPA · SIL · Pool Fire · Dispersão Gaussiana · Bow-Tie</p>
      <div style="margin-top:0.5rem;">
        <span class="cs-badge">IEC 61882:2016</span>
        <span class="cs-badge">CCPS LOPA 2001</span>
        <span class="cs-badge">API RP 521</span>
        <span class="cs-badge">Shokri-Beyler 1989</span>
        <span class="cs-badge">Pasquill-Gifford</span>
        <span class="cs-badge">IEC 61511</span>
      </div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:0.7rem;color:#4A6080;margin-bottom:4px;">Desenvolvido por</div>
      <div style="font-size:0.85rem;color:#7AAEF5;font-weight:500;">Gabriel Hernandez Rozo</div>
      <a href="https://www.linkedin.com/in/gabriel-hernandez-rozo-30751325b" target="_blank"
         style="font-size:0.72rem;color:#4A6080;text-decoration:none;">
        linkedin.com/in/gabriel-hernandez-rozo-30751325b →
      </a>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
#  TABS PRINCIPAIS
# ════════════════════════════════════════════════════════════════════════════
tab_sds, tab_hazop, tab_bowtie, tab_lopa, tab_disp, tab_fire, tab_ref, tab_sobre = st.tabs([
    "🔍 Consulta & SDS",
    "📋 HAZOP Digital",
    "🎯 Bow-Tie",
    "🛡️ LOPA → SIL",
    "💨 Dispersão Gaussiana",
    "🔥 Pool Fire",
    "📚 Referências",
    "👤 Sobre",
])

# ════════════════════════════════════════════════════════════════════════════
#  ABA 1 — CONSULTA & SDS
# ════════════════════════════════════════════════════════════════════════════
with tab_sds:
    c1, c2 = st.columns([5,1])
    with c1:
        q = st.text_input("", value=st.session_state.q_input,
                          placeholder="Nome, fórmula ou CAS… ex: etanol, H₂SO₄, 64-17-5",
                          key="campo_busca", label_visibility="collapsed")
    with c2:
        buscar = st.button("Consultar", type="primary", use_container_width=True)

    if buscar or st.session_state.buscar:
        st.session_state.buscar = False
        consulta = q or st.session_state.q_input
        if consulta:
            with st.spinner("Consultando PubChem + base GHS local…"):
                dados = resolver(consulta)
                if not dados:
                    try:
                        r = requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{requests.utils.quote(consulta)}/cids/JSON",timeout=8)
                        if r.status_code==200:
                            cid = r.json()["IdentifierList"]["CID"][0]
                            pr = requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/MolecularFormula,MolecularWeight,IUPACName/JSON",timeout=8)
                            p = pr.json()["PropertyTable"]["Properties"][0] if pr.status_code==200 else {}
                            sr = requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/synonyms/JSON",timeout=8)
                            sins = sr.json()["InformationList"]["Information"][0].get("Synonym",[]) if sr.status_code==200 else []
                            cas_p = re.compile(r"^\d{1,7}-\d{2}-\d$")
                            cas = next((s for s in sins if cas_p.match(s)),"—")
                            dados = {"nome":p.get("IUPACName",consulta).title(),"formula":p.get("MolecularFormula","—"),
                                     "cas":cas,"pm":str(p.get("MolecularWeight","—")),"cid":cid,
                                     "hazards":["Consultar SDS do fornecedor para classificação GHS completa"],
                                     "pics":[],"sinal":"—","props":[("Fórmula",p.get("MolecularFormula","—")),
                                     ("Peso mol.",f"{p.get('MolecularWeight','—')} g/mol"),("CID PubChem",str(cid))],
                                     "nfpa":(0,0,0,""),"lie":None,"lse":None,"flash_c":None,"ait":None,"mie":None}
                    except: pass
                if dados:
                    st.session_state.dados = dados
                    st.session_state.historico.append({"hora":datetime.now().strftime("%H:%M"),"nome":dados["nome"]})
                    st.success(f"Composto encontrado: **{dados['nome']}**")
                else:
                    st.error(f"Composto '{consulta}' não encontrado.")

    d = st.session_state.dados
    if d:
        c1,c2,c3,c4,c5 = st.columns(5)
        nfpa = d.get("nfpa",(0,0,0,""))
        c1.markdown(f"<div class='cs-metric'><div class='lbl'>Composto</div><div class='value' style='font-size:1rem;'>{d['nome']}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cs-metric'><div class='lbl'>Fórmula</div><div class='value' style='font-size:1.1rem;'>{d['formula']}</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='cs-metric'><div class='lbl'>CAS</div><div class='value' style='font-size:1rem;'>{d['cas']}</div></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='cs-metric'><div class='lbl'>NFPA F/H/R</div><div class='value {'red' if nfpa[0]>=3 else 'amber' if nfpa[0]>=2 else 'green'}'>{nfpa[0]}/{nfpa[1]}/{nfpa[2]}</div></div>", unsafe_allow_html=True)
        c5.markdown(f"<div class='cs-metric'><div class='lbl'>AIT</div><div class='value blue'>{d.get('ait','—') or '—'} {'°C' if d.get('ait') else ''}</div></div>", unsafe_allow_html=True)
        st.markdown("")

        col_e, col_d = st.columns(2)
        with col_e:
            st.markdown("<div class='cs-card-title'><span class='dot'></span>Perigos GHS</div>", unsafe_allow_html=True)
            sinal = d.get("sinal","—")
            if sinal and sinal != "—":
                cor = "pill-r" if "perigo" in sinal.lower() else "pill-a"
                st.markdown(f"<span class='pill {cor}'>Palavra de advertência: {sinal.upper()}</span>", unsafe_allow_html=True)
            st.markdown("")
            for h in d.get("hazards",[]):
                st.markdown(f"<div class='hazard-item'>{h}</div>", unsafe_allow_html=True)
            if d.get("pics"):
                st.markdown(f"<div style='margin-top:0.5rem;'>" + "".join([f"<span class='pill pill-b'>{p}</span>" for p in d['pics']]) + "</div>", unsafe_allow_html=True)

        with col_d:
            st.markdown("<div class='cs-card-title'><span class='dot'></span>Propriedades físico-químicas</div>", unsafe_allow_html=True)
            for k,v in d.get("props",[]):
                st.markdown(f"""<div style='display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1A2A45;font-size:0.82rem;'>
                    <span style='color:#4A6080;'>{k}</span>
                    <span style='color:#C5D5F0;font-family:IBM Plex Mono,monospace;'>{v}</span></div>""", unsafe_allow_html=True)
            if d.get("mie"):
                st.markdown(f"<div style='margin-top:8px;'><span class='pill pill-a'>MIE: {d['mie']} mJ</span></div>", unsafe_allow_html=True)

        st.markdown("<hr style='border:none;border-top:1px solid #1A2A45;margin:1rem 0;'>", unsafe_allow_html=True)
        c_pdf1, c_pdf2 = st.columns([3,1])
        with c_pdf1:
            st.markdown("<div style='font-size:0.85rem;color:#6B82AA;'>Gerar FISPQ completa (ABNT NBR 14725-4 / GHS Rev.9) com 16 seções, cabeçalho institucional e rodapé rastreável.</div>", unsafe_allow_html=True)
        with c_pdf2:
            if st.button("📄 Gerar SDS PDF", type="primary", use_container_width=True):
                with st.spinner("Gerando SDS…"):
                    try:
                        from chemsafe_sds_pdf import gerar_sds_pdf
                        pdf_path = f"/tmp/SDS_{d['cas'].replace('-','_')}.pdf"
                        gerar_sds_pdf(d, pdf_path)
                        with open(pdf_path,"rb") as f: pdf_bytes = f.read()
                        st.download_button("⬇️ Baixar SDS PDF", pdf_bytes,
                                           f"SDS_{d['nome'].replace(' ','_')}.pdf","application/pdf",
                                           use_container_width=True)
                    except Exception as e:
                        st.error(f"Erro ao gerar PDF: {e}")
    else:
        st.markdown("<div style='text-align:center;color:#2D3A50;padding:3rem 0;font-size:0.9rem;'>Digite um composto ou selecione na barra lateral para iniciar a análise.</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
#  ABA 2 — HAZOP DIGITAL
# ════════════════════════════════════════════════════════════════════════════
with tab_hazop:
    st.markdown("<div style='font-size:0.75rem;color:#4A6080;margin-bottom:1rem;'><span class='pill pill-b'>IEC 61882:2016</span> <span class='pill pill-p'>OSHA 29 CFR 1910.119</span> Hazard and Operability Study — palavras-guia aplicadas a parâmetros de processo</div>", unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    with c1:
        equip = st.selectbox("Equipamento / nó", ["Tanque de armazenamento (líq. inflamável)","Reator CSTR (exotérmico)","Trocador de calor (shell & tube)","Tubulação de processo","Vaso de pressão (vaso acumulador)","Bomba centrífuga"])
    with c2:
        param = st.selectbox("Parâmetro de processo", list(HAZOP_DB.keys()))
    with c3:
        gw_raw = st.selectbox("Palavra-guia (IEC 61882)", ["MAIS (aumento quantitativo)","MENOS (redução quantitativa)","NÃO / NENHUM (ausência completa)","REVERSO (direção oposta)","TAMBÉM (adição/contaminação)","EXCETO (substituição parcial)"])

    gw = gw_raw.split("(")[0].strip()

    c_btn1, c_btn2 = st.columns([2,3])
    with c_btn1:
        if st.button("Gerar planilha HAZOP", type="primary"):
            db = HAZOP_DB.get(param,{}).get(gw, HAZOP_DB.get(param,{}).get(list(HAZOP_DB.get(param,{}).keys())[0],{}))
            if not db:
                st.warning("Combinação não disponível na base. Tente outro parâmetro ou palavra-guia.")
            else:
                st.session_state.hazop_gerado = {"equip":equip,"param":param,"gw":gw,"db":db}
    with c_btn2:
        if st.session_state.hazop_gerado and st.button("→ Enviar para LOPA (melhor cenário)", type="primary"):
            db = st.session_state.hazop_gerado["db"]
            if db.get("causas"):
                st.session_state.lopa_prefill = {"causa":db["causas"][0],"conseq":db["conseqs"][0] if db.get("conseqs") else ""}
                st.info("Dados transferidos para a aba LOPA → SIL. Acesse a aba para calcular.")

    if st.session_state.hazop_gerado:
        hz = st.session_state.hazop_gerado
        db = hz["db"]
        st.markdown(f"""<div style='margin:1rem 0 0.5rem;font-size:0.78rem;color:#4A6080;'>
            Nó: <span style='color:#7AAEF5;'>{hz['equip']}</span> · 
            Parâmetro: <span style='color:#7AAEF5;'>{hz['param']}</span> · 
            Desvio: <span style='color:#F5A623;'>{hz['gw']} {hz['param']}</span>
        </div>""", unsafe_allow_html=True)

        st.markdown("""<div class='hazop-grid'>
            <div class='hg-header'>Desvio</div><div class='hg-header'>Causa provável</div>
            <div class='hg-header'>Consequência</div><div class='hg-header'>Salvaguarda existente</div>
            <div class='hg-header'>Risco inicial</div><div class='hg-header'>Recomendação de ação</div>
        </div>""", unsafe_allow_html=True)
        causas = db.get("causas",[])
        for i, causa in enumerate(causas):
            desvio = f"{hz['gw']} {hz['param']}" if i==0 else "↑ idem"
            conseq = (db.get("conseqs",[]) + ["—"])[i] if i < len(db.get("conseqs",[])) else db.get("conseqs",["—"])[0]
            salvag = (db.get("salvags",[]) + ["—"])[i] if i < len(db.get("salvags",[])) else db.get("salvags",["—"])[0]
            rec    = (db.get("rec",[]) + ["—"])[i] if i < len(db.get("rec",[])) else db.get("rec",["—"])[0]
            risco_cls = "pill-r" if i<2 else "pill-a"
            risco_val = "5E — Intolerável" if i<1 else "4D — Alto"
            st.markdown(f"""<div class='hazop-grid'>
                <div class='hg-cell accent' style='color:#7AAEF5;'>{desvio}</div>
                <div class='hg-cell'>{causa}</div>
                <div class='hg-cell' style='color:#FFBBBB;'>{conseq}</div>
                <div class='hg-cell' style='color:#7AAEF5;'>{salvag}</div>
                <div class='hg-cell'><span class='pill {risco_cls}'>{risco_val}</span></div>
                <div class='hg-cell' style='color:#2DD4A0;'>{rec}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<hr style='border:none;border-top:1px solid #1A2A45;margin:1rem 0;'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.78rem;color:#2D4A60;margin-top:0.25rem;'>Fonte: IEC 61882:2016 — Hazard and Operability Studies. CCPS Guidelines for Hazard Evaluation Procedures (AIChE, 3ª ed.). API RP 750 — Management of Process Hazards.</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
#  ABA 3 — BOW-TIE
# ════════════════════════════════════════════════════════════════════════════
with tab_bowtie:
    st.markdown("<div style='font-size:0.75rem;color:#4A6080;margin-bottom:1rem;'><span class='pill pill-b'>CCPS/EI Bow Ties in Risk Management (2018)</span> <span class='pill pill-p'>IEC 61511</span> Diagrama Hazard → Top Event → Consequências com barreiras de prevenção e mitigação</div>", unsafe_allow_html=True)

    c1,c2 = st.columns(2)
    with c1:
        hazard_bt = st.selectbox("Hazard (perigo)", ["Líquido inflamável em tanque de armazenamento","Gás tóxico pressurizado (amônia)","Reator com reação exotérmica runaway","Vaso de pressão com fluido em temperatura de operação","Ácido corrosivo em linha de processo"])
    with c2:
        top_event = st.selectbox("Top event (perda de controle)", ["Perda de contenção primária (LOPC)","Ruptura catastrófica do vaso (BLEVE)","Ignição de nuvem inflamável","Liberação de gás tóxico para a atmosfera","Incêndio em poça (pool fire)"])

    BT_DATA = {
        "Líquido inflamável em tanque de armazenamento":{
            "ameacas":["Corrosão / deterioração do casco","Impacto físico externo (veículo)","Overfill por falha de instrumentação","Falha de soldagem ou flange","Erro operacional — abertura de dreno errado"],
            "prev_barriers":["Programa de inspeção de integridade (NR-13 / API 653)","Sistema de proteção anti-colisão / barreiras físicas","LAHH + SIS de corte de feed (SIL 1)","Teste periódico de flanges e conexões","Procedimento de bloqueio e etiquetagem (LOTOTO)"],
            "conseqs":["Pool fire — irradiação térmica","Explosão de nuvem de vapor (VCE)","Contaminação ambiental do solo / lençol freático","Incêndio de dique","Perda de produto — impacto econômico"],
            "mit_barriers":["Dique de contenção 110% (NR-20)","Sistema de detecção e alarme de incêndio","Espuma AFFF automática no tanque (API 2021)","Plano de resposta a emergências (PRE)","Brigada de incêndio treinada (NR-23)"],
        },
        "Gás tóxico pressurizado (amônia)":{
            "ameacas":["Fratura de tubulação por fadiga / vibração","Falha de vedação de compressor","Sobrepressão por fechamento de válvula downstream","Corrosão sob isolamento (CUI)","Erro de manutenção — abertura de flange pressurizado"],
            "prev_barriers":["Inspeção ultrassônica periódica de tubulações","Monitoramento de vibração online no compressor","PAHH + trip automático de compressor (SIL 2)","Programa de inspeção CUI (API 570)","Procedimento de isolamento para manutenção"],
            "conseqs":["Nuvem tóxica — zona IDLH (300 ppm)","Intoxicação aguda de trabalhadores","Evacuação de área / comunidade próxima","Incêndio se atingir fonte de ignição (LIE 15%)","Impacto ambiental — toxicidade aquática (H400)"],
            "mit_barriers":["Detectores de amônia (NH₃) na área — alarme + evacuação","Equipamento de proteção individual — SCBA (NR-6)","Cortina d'água de absorção de amônia","Plano de atendimento à emergência (PAE)","Notificação aos órgãos (CETESB / IBAMA)"],
        },
    }

    bt = BT_DATA.get(hazard_bt, list(BT_DATA.values())[0])
    ameacas = bt["ameacas"][:3]
    prev_b  = bt["prev_barriers"][:3]
    conseqs = bt["conseqs"][:3]
    mit_b   = bt["mit_barriers"][:3]

    # Renderizar o bowtie como HTML
    def bt_col(items, color, label):
        items_html = "".join([f"<div style='background:#0D1525;border:1px solid {color}33;border-radius:6px;padding:6px 8px;margin-bottom:4px;font-size:0.75rem;color:{color};line-height:1.4;'>{item}</div>" for item in items])
        return f"<div><div style='font-size:0.65rem;color:#4A6080;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;text-align:center;'>{label}</div>{items_html}</div>"

    st.markdown(f"""
    <div style='display:grid;grid-template-columns:1fr 80px 1fr 80px 1fr 80px 1fr;gap:8px;align-items:center;margin-top:1rem;'>
      {bt_col(ameacas,'#F5A623','Ameaças')}
      <div style='text-align:center;'>
        {bt_col(prev_b,'#4DA6F5','Barreiras de prevenção')}
      </div>
      <div style='background:#1A0A2A;border:2px solid #9678F0;border-radius:8px;padding:0.75rem;text-align:center;'>
        <div style='font-size:0.65rem;color:#9678F0;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;'>Top event</div>
        <div style='font-size:0.8rem;color:#E8D0FF;font-weight:500;line-height:1.3;'>{top_event}</div>
        <div style='font-size:0.65rem;color:#6040A0;margin-top:4px;'>Perda de controle</div>
      </div>
      <div style='text-align:center;'>
        {bt_col(mit_b,'#2DD4A0','Barreiras de mitigação')}
      </div>
      {bt_col(conseqs,'#F04545','Consequências')}
    </div>
    <div style='text-align:center;margin-top:0.75rem;font-size:0.7rem;color:#2D3A50;'>
      CCPS/EI "Bow Ties in Risk Management" (2018) · Duijm N.J. (2009) Reliability Eng. System Safety 94(2):332–341 · IEC 61511
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='border:none;border-top:1px solid #1A2A45;margin:1rem 0;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.78rem;color:#4A6080;line-height:1.7;'>O diagrama Bow-Tie é centralizado no top event (momento de perda de controle). Barreiras à esquerda são <span style='color:#4DA6F5;'>preventivas</span> (evitam o top event); barreiras à direita são <span style='color:#2DD4A0;'>mitigadoras</span> (reduzem a consequência após o top event). Fonte: CCPS/EI Bow Ties in Risk Management (2018), ISBN 978-1-119-37351-0.</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
#  ABA 4 — LOPA → SIL
# ════════════════════════════════════════════════════════════════════════════
with tab_lopa:
    st.markdown("<div style='font-size:0.75rem;color:#4A6080;margin-bottom:1rem;'><span class='pill pill-b'>CCPS/AIChE LOPA (2001)</span> <span class='pill pill-p'>IEC 61511</span> MCF = F_ie × ∏PFD_j. Critério típico: ≤10⁻⁴/ano (lesão grave) | ≤10⁻⁵/ano (fatalidade)</div>", unsafe_allow_html=True)

    st.markdown("""<div class='formula-block'>MCF = F_ie × PFD_IPL1 × PFD_IPL2 × ... × PFD_IPLn   [eventos/ano]

F_ie  = Frequência do evento iniciador          [eventos/ano]
PFD_j = Probabilidade de Falha sob Demanda IPL j  [adimensional]
MCF   = Mitigated Consequence Frequency          [eventos/ano]

SIL requerido (IEC 61511 / CCPS):
  MCF/critério > 10 → SIL 1 (PFD_req 10⁻¹ a 10⁻²)
  MCF/critério > 100 → SIL 2 (PFD_req 10⁻² a 10⁻³)
  MCF/critério > 1000 → SIL 3 (PFD_req 10⁻³ a 10⁻⁴)

Fonte: CCPS/AIChE (2001), Willey R.J. (2014) Procedia Eng. 84:12–22</div>""", unsafe_allow_html=True)

    c1,c2 = st.columns(2)
    with c1:
        st.markdown("<div class='cs-card-title'><span class='dot'></span>Parâmetros do cenário</div>", unsafe_allow_html=True)
        pre = getattr(st.session_state, "lopa_prefill", {})
        if pre:
            st.info(f"Transferido do HAZOP: {pre.get('causa','—')[:80]}")

        ie_options = {
            "Falha do BPCS (Basic Process Control System) — 0.1/ano": 0.1,
            "Falha de válvula de controle (stuck open/closed) — 0.01/ano": 0.01,
            "Erro humano operacional — 1/ano": 1.0,
            "Falha de instrumento / sensor — 0.1/ano": 0.1,
            "Falha de serviços públicos (energia, vapor) — 0.1/ano": 0.1,
            "Frequência customizada (informar abaixo)": 0,
        }
        ie_sel = st.selectbox("Evento iniciador (IEC 61882 / CCPS)", list(ie_options.keys()))
        fie_custom = st.number_input("Frequência customizada (eventos/ano)", value=0.1, min_value=1e-6, format="%.4f", step=0.01)
        fie = fie_custom if ie_options[ie_sel]==0 else ie_options[ie_sel]

        sev_options = {"Cat. 5 — Fatalidade / catástrofe ambiental":0.00001,
                       "Cat. 4 — Lesão grave / dano ambiental severo":0.0001,
                       "Cat. 3 — Lesão moderada / dano ambiental":0.001,
                       "Cat. 2 — Lesão leve":0.01,
                       "Cat. 1 — Incidente sem lesão":0.1}
        sev_sel = st.selectbox("Severidade da consequência → critério de risco tolerável", list(sev_options.keys()))
        criterio = sev_options[sev_sel]
        st.caption(f"Critério MCF ≤ {criterio:.0e} eventos/ano (CCPS LOPA 2001)")

    with c2:
        st.markdown("<div class='cs-card-title'><span class='dot'></span>IPLs — Camadas de proteção independentes</div>", unsafe_allow_html=True)
        st.caption("Cada IPL deve ser independente dos demais e do evento iniciador (CCPS/IEC 61511).")
        ipl_choices = st.multiselect("Selecionar IPLs",
            options=[f"{n} (PFD={p})" for n,p in IPL_CATALOG],
            default=["Válvula de alívio de pressão (PSV) — bem mantida (PFD=0.01)"])
        ipl_pfds = []
        for choice in ipl_choices:
            for n,p in IPL_CATALOG:
                if n in choice: ipl_pfds.append((n,p)); break

        st.markdown("")
        if st.button("Calcular LOPA + SIL", type="primary", use_container_width=True):
            pfd_total = 1.0
            for _,p in ipl_pfds: pfd_total *= p
            mcf = fie * pfd_total
            ratio = mcf / criterio
            sil_needed = "Não requerido" if ratio<=1 else ("SIL 1" if ratio<=10 else ("SIL 2" if ratio<=100 else "SIL 3"))
            sil_cls = "sil-ok" if ratio<=1 else ("sil-1" if ratio<=10 else ("sil-2" if ratio<=100 else "sil-3"))
            sil_color = "#2DD4A0" if ratio<=1 else ("#F5A623" if ratio<=10 else ("#F04545" if ratio>100 else "#F08028"))
            st.session_state.lopa_result = {"fie":fie,"pfd_total":pfd_total,"mcf":mcf,"ratio":ratio,
                                             "sil":sil_needed,"sil_cls":sil_cls,"sil_color":sil_color,
                                             "criterio":criterio,"ipls":ipl_pfds}

    if st.session_state.lopa_result:
        r = st.session_state.lopa_result
        st.markdown("<hr style='border:none;border-top:1px solid #1A2A45;margin:1rem 0;'>", unsafe_allow_html=True)
        cc1,cc2,cc3,cc4 = st.columns(4)
        cc1.markdown(f"<div class='cs-metric'><div class='lbl'>F_ie</div><div class='value blue'>{r['fie']:.2e}/ano</div></div>", unsafe_allow_html=True)
        cc2.markdown(f"<div class='cs-metric'><div class='lbl'>PFD total IPLs</div><div class='value blue'>{r['pfd_total']:.2e}</div></div>", unsafe_allow_html=True)
        cc3.markdown(f"<div class='cs-metric'><div class='lbl'>MCF calculado</div><div class='value {'green' if r['ratio']<=1 else 'red'}'>{r['mcf']:.2e}/ano</div></div>", unsafe_allow_html=True)
        cc4.markdown(f"<div class='cs-metric'><div class='lbl'>Razão MCF/critério</div><div class='value {'green' if r['ratio']<=1 else 'red'}'>{r['ratio']:.2f}</div></div>", unsafe_allow_html=True)
        st.markdown("")
        c_sil, c_txt = st.columns([1,3])
        with c_sil:
            st.markdown(f"<div class='sil-box {r['sil_cls']}'><div class='sil-label'>SIL necessário</div><div class='sil-value' style='color:{r['sil_color']};'>{r['sil']}</div></div>", unsafe_allow_html=True)
        with c_txt:
            ok = r['ratio'] <= 1
            cor = "#2DD4A0" if ok else "#F04545"
            msg = "RISCO TOLERÁVEL — IPLs existentes são suficientes para atender o critério." if ok else f"RISCO INTOLERÁVEL — Necessário adicionar IPL com SIL {r['sil'].split()[-1] if 'SIL' in r['sil'] else '—'} para reduzir o MCF ao critério."
            st.markdown(f"<div style='background:rgba({('45,212,160' if ok else '240,69,69')},0.06);border:1px solid rgba({('45,212,160' if ok else '240,69,69')},0.25);border-radius:8px;padding:1rem;color:{cor};font-size:0.9rem;font-weight:500;'>{msg}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:0.78rem;color:#4A6080;margin-top:0.5rem;'>MCF = {r['fie']:.2e} × {r['pfd_total']:.2e} = {r['mcf']:.2e}/ano | Critério: {r['criterio']:.0e}/ano</div>", unsafe_allow_html=True)
            if r['ipls']:
                ipl_str = " × ".join([f"{n.split('(')[0].strip()} ({p})" for n,p in r['ipls']])
                st.markdown(f"<div style='font-size:0.72rem;color:#2D3A50;margin-top:4px;'>IPLs: {ipl_str}</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
#  ABA 5 — DISPERSÃO GAUSSIANA
# ════════════════════════════════════════════════════════════════════════════
with tab_disp:
    st.markdown("<div style='font-size:0.75rem;color:#4A6080;margin-bottom:0.5rem;'><span class='pill pill-b'>Pasquill-Gifford (1961)</span> <span class='pill pill-b'>EPA AP-42</span> <span class='pill pill-a'>Válido para gases neutros/leves</span> Para gases densos (NH₃, Cl₂) use modelo DEGADIS</div>", unsafe_allow_html=True)

    st.markdown("""<div class='formula-block'>C(x,0,0) = Q / (π·σy·σz·u) · exp(−H²/2σz²)   [eixo central, g/m³]

σy = a·x^b   σz = c·x^d     (coeficientes Pasquill-Gifford por classe de estabilidade)
τ  ≈ 1 − 0.058·ln(x)        (transmissividade atmosférica, Mudan 1984)

Fonte: Pasquill F. (1961) Meteorol. Mag. 90:33–49 · Turner D.B. (1970) EPA AP-26</div>""", unsafe_allow_html=True)

    c1,c2 = st.columns(2)
    with c1:
        Q_d  = st.number_input("Taxa de emissão Q (g/s)", value=10.0, min_value=0.001, step=0.1)
        u_d  = st.number_input("Velocidade do vento u (m/s)", value=3.0, min_value=0.5, max_value=20.0, step=0.1)
        cl_d = st.selectbox("Classe de estabilidade atmosférica", ["A — Muito instável","B — Moderadamente instável","C — Levemente instável (dia nublado)","D — Neutro","E — Levemente estável","F — Estável (noite clara)"])
        cl   = cl_d[0]
        idlh_ppm = st.number_input("Concentração crítica IDLH (ppm)", value=300.0, min_value=0.001, step=1.0)
        mw_d = st.number_input("Peso molecular do gás (g/mol)", value=17.0, min_value=1.0, step=0.1)
        H_d  = st.number_input("Altura da fonte H (m)", value=0.0, min_value=0.0, step=0.5)
        if st.button("Calcular dispersão", type="primary"):
            pg = PG_COEF[cl]
            idlh_gm3 = idlh_ppm * mw_d / 24.45
            xs = list(range(10,3001,25))
            cs = []
            x_idlh = None
            for x in xs:
                sy = pg["a"]*x**pg["b"]; sz = pg["c"]*x**pg["d"]
                c_val = Q_d/(math.pi*sy*sz*u_d)*math.exp(-(H_d**2)/(2*sz**2))
                cs.append(round(c_val,6))
                if x_idlh is None and c_val <= idlh_gm3: x_idlh = x
            sy100=pg["a"]*100**pg["b"]; sz100=pg["c"]*100**pg["d"]
            c100=Q_d/(math.pi*sy100*sz100*u_d)*math.exp(-(H_d**2)/(2*sz100**2))
            st.session_state.disp_result = {"xs":xs,"cs":cs,"x_idlh":x_idlh,"idlh_gm3":idlh_gm3,"c100":c100,"cl":cl}

    with c2:
        if "disp_result" in st.session_state:
            r = st.session_state.disp_result
            cc1,cc2 = st.columns(2)
            xstr = f"{r['x_idlh']} m" if r['x_idlh'] else "> 3 km"
            cc1.markdown(f"<div class='cs-metric'><div class='lbl'>Distância segura (IDLH)</div><div class='value {'red' if r['x_idlh'] and r['x_idlh']<500 else 'green'}'>{xstr}</div></div>", unsafe_allow_html=True)
            cc2.markdown(f"<div class='cs-metric'><div class='lbl'>Concentração @ 100m</div><div class='value blue'>{r['c100']:.4f} g/m³</div></div>", unsafe_allow_html=True)
            st.markdown("")
            try:
                import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
                fig,ax = plt.subplots(figsize=(6,3)); fig.patch.set_facecolor("#080D18"); ax.set_facecolor("#080D18")
                ax.semilogy(r['xs'],r['cs'],color="#4DA6F5",linewidth=1.5,label="Conc. eixo central")
                ax.axhline(r['idlh_gm3'],color="#F04545",linestyle="--",linewidth=1,label=f"IDLH ({r['idlh_gm3']:.3f} g/m³)")
                if r['x_idlh']: ax.axvline(r['x_idlh'],color="#F5A623",linestyle=":",linewidth=1,label=f"x_IDLH={r['x_idlh']}m")
                for s in ax.spines.values(): s.set_color("#1A2A45")
                ax.tick_params(colors="#4A6080",labelsize=8); ax.xaxis.label.set_color("#4A6080"); ax.yaxis.label.set_color("#4A6080")
                ax.set_xlabel("Distância (m)",fontsize=8); ax.set_ylabel("Concentração (g/m³)",fontsize=8)
                ax.legend(fontsize=7,facecolor="#0D1525",edgecolor="#1A2A45",labelcolor="#8899BB")
                ax.grid(True,alpha=0.1,color="#1A2A45"); plt.tight_layout()
                st.pyplot(fig,use_container_width=True); plt.close(fig)
            except Exception as e:
                st.caption(f"pip install matplotlib para ver o gráfico ({e})")

# ════════════════════════════════════════════════════════════════════════════
#  ABA 6 — POOL FIRE
# ════════════════════════════════════════════════════════════════════════════
with tab_fire:
    st.markdown("<div style='font-size:0.75rem;color:#4A6080;margin-bottom:0.5rem;'><span class='pill pill-r'>Shokri-Beyler 1989</span> <span class='pill pill-r'>Heskestad 1983</span> <span class='pill pill-b'>API RP 521</span> <span class='pill pill-b'>NISTIR 6546</span></div>", unsafe_allow_html=True)

    st.markdown("""<div class='formula-block'>Hf  = 0.235·Q_rel^0.4 − 1.02·D          [Heskestad 1983, m]
E   = 58·exp(−0.00823·D)                 [Shokri-Beyler 1989, kW/m²]  
q"  = E · F(D,Hf,L) · τ(L)              [fluxo no alvo, kW/m²]
τ   ≈ 1 − 0.058·ln(L)                   [Mudan 1984]

Limiares (API RP 521 / SFPE Handbook 5ª ed.):
  37.5 kW/m² → fatalidade 1% · 12.5 kW/m² → dor intensa / queimadura · 1.6 kW/m² → limite seguro

Fonte: Shokri M., Beyler C.L. J. Fire Prot. Eng. 1(4):141–149, 1989 · DOI:10.1177/104239158900100404</div>""", unsafe_allow_html=True)

    c1,c2 = st.columns(2)
    with c1:
        D_pf = st.number_input("Diâmetro da poça D (m)", value=5.0, min_value=0.5, max_value=200.0, step=0.5)
        mb_pf = st.selectbox("Produto / taxa de queima m\" (kg/m²·s)", ["Gasolina — 0.055","Etanol — 0.024","Tolueno — 0.048","Propano (liq.) — 0.078","Amônia (liq.) — 0.030","Diesel — 0.050","GLP — 0.099","Metanol — 0.017"])
        mb = float(mb_pf.split("—")[1].strip())
        Hc_pf = st.number_input("Calor de combustão Hc (kJ/kg)", value=44000.0, min_value=1000.0, step=100.0)
        L_pf  = st.slider("Distância ao receptor L (m)", min_value=1, max_value=300, value=20, step=1)
        if st.button("Calcular pool fire", type="primary"):
            Q_rel = mb*(math.pi*D_pf**2/4)*Hc_pf
            Hf    = max(0.1, 0.235*Q_rel**0.4 - 1.02*D_pf)
            E     = 58*math.exp(-0.00823*D_pf)
            S     = L_pf/(D_pf/2)
            if S <= 1: S = 1.01
            A_v   = math.sqrt((S+1)**2+(2*Hf/D_pf)**2-1)
            B_v   = math.sqrt((S-1)**2+(2*Hf/D_pf)**2)
            try:
                F = max(0.0001,(1/(math.pi*S))*(math.atan(math.sqrt((S+1)/(S-1)))-(1/A_v)*math.atan(math.sqrt((S+1)/(A_v*(S-1))))+(2*Hf/D_pf/B_v)*math.atan(math.sqrt((S+1)/(B_v*(S-1))))))
            except: F=0.01
            tau   = max(0.1, 1-0.058*math.log(L_pf))
            q_dot = E*F*tau
            zona  = ("red","FATALIDADE (>37.5 kW/m²)") if q_dot>37.5 else ("amber","Queimaduras graves (>12.5 kW/m²)") if q_dot>12.5 else ("amber","Queimaduras 1° grau (>4.7 kW/m²)") if q_dot>4.7 else ("green","Zona segura (<1.6 kW/m²)")
            st.session_state.pf_result = {"Hf":Hf,"E":E,"F":F,"tau":tau,"q":q_dot,"Q":Q_rel,"zona":zona,"D":D_pf,"L":L_pf}

    with c2:
        if "pf_result" in st.session_state:
            r = st.session_state.pf_result
            cc1,cc2,cc3 = st.columns(3)
            cc1.markdown(f"<div class='cs-metric'><div class='lbl'>Altura chama Hf</div><div class='value blue'>{r['Hf']:.1f} m</div></div>", unsafe_allow_html=True)
            cc2.markdown(f"<div class='cs-metric'><div class='lbl'>Poder emissivo E</div><div class='value blue'>{r['E']:.1f} kW/m²</div></div>", unsafe_allow_html=True)
            cc3.markdown(f"<div class='cs-metric'><div class='lbl'>q\" no alvo</div><div class='value {r['zona'][0]}'>{r['q']:.2f} kW/m²</div></div>", unsafe_allow_html=True)
            zcor = "#F04545" if r['zona'][0]=="red" else ("#F5A623" if r['zona'][0]=="amber" else "#2DD4A0")
            zrgb = "240,69,69" if r['zona'][0]=="red" else ("245,166,35" if r['zona'][0]=="amber" else "45,212,160")
            st.markdown(f"<div style='background:rgba({zrgb},0.07);border:1px solid {zcor}33;border-radius:8px;padding:0.75rem 1rem;color:{zcor};font-size:0.9rem;font-weight:500;margin-top:0.5rem;'>{r['zona'][1]}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:0.75rem;color:#4A6080;margin-top:0.5rem;'>Q_rel={r['Q']/1000:.0f} MW · F={r['F']:.4f} · τ={r['tau']:.3f} · D={r['D']}m · L={r['L']}m</div>", unsafe_allow_html=True)

            # Curva de radiação
            try:
                import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
                Ls = list(range(1,201,3))
                qs = []
                for L_i in Ls:
                    S_i=L_i/(r['D']/2); S_i=max(1.01,S_i)
                    A_i=math.sqrt((S_i+1)**2+(2*r['Hf']/r['D'])**2-1)
                    B_i=math.sqrt((S_i-1)**2+(2*r['Hf']/r['D'])**2)
                    try: F_i=max(0.0001,(1/(math.pi*S_i))*(math.atan(math.sqrt((S_i+1)/(S_i-1)))-(1/A_i)*math.atan(math.sqrt((S_i+1)/(A_i*(S_i-1))))+(2*r['Hf']/r['D']/B_i)*math.atan(math.sqrt((S_i+1)/(B_i*(S_i-1))))))
                    except: F_i=0.001
                    t_i=max(0.1,1-0.058*math.log(L_i)); qs.append(round(r['E']*F_i*t_i,3))
                fig,ax=plt.subplots(figsize=(6,3)); fig.patch.set_facecolor("#080D18"); ax.set_facecolor("#080D18")
                ax.plot(Ls,qs,color="#F04545",linewidth=1.5)
                ax.axhline(37.5,color="#F04545",linestyle="--",linewidth=0.8,label="37.5 kW/m² fatalidade")
                ax.axhline(12.5,color="#F5A623",linestyle="--",linewidth=0.8,label="12.5 kW/m² dor")
                ax.axhline(1.6,color="#2DD4A0",linestyle="--",linewidth=0.8,label="1.6 kW/m² seguro")
                ax.axvline(r['L'],color="#9678F0",linestyle=":",linewidth=1)
                for s in ax.spines.values(): s.set_color("#1A2A45")
                ax.tick_params(colors="#4A6080",labelsize=8); ax.grid(True,alpha=0.1,color="#1A2A45")
                ax.set_xlabel("Distância (m)",fontsize=8,color="#4A6080"); ax.set_ylabel("q\" (kW/m²)",fontsize=8,color="#4A6080")
                ax.legend(fontsize=7,facecolor="#0D1525",edgecolor="#1A2A45",labelcolor="#8899BB"); plt.tight_layout()
                st.pyplot(fig,use_container_width=True); plt.close(fig)
            except Exception as e: st.caption(f"pip install matplotlib ({e})")

# ════════════════════════════════════════════════════════════════════════════
#  ABA 7 — REFERÊNCIAS
# ════════════════════════════════════════════════════════════════════════════
with tab_ref:
    st.markdown("<div style='font-size:0.85rem;color:#6B82AA;margin-bottom:1.5rem;line-height:1.7;'>Toda fórmula e modelo do ChemSafe Pro possui referência bibliográfica verificável. Esta aba garante rastreabilidade científica para auditorias, revisões por pares e uso regulatório.</div>", unsafe_allow_html=True)

    REFS = [
        ("HAZOP & Análise de Risco","IEC 61882:2016","Hazard and Operability Studies (HAZOP Studies) — Application Guide","International Electrotechnical Commission, 2ª ed., 2016. Genebra: IEC.","Palavras-guia, parâmetros, metodologia e worksheets HAZOP","pill-b"),
        ("HAZOP & Análise de Risco","CCPS/AIChE (2008)","Guidelines for Hazard Evaluation Procedures, 3ª ed.","Center for Chemical Process Safety. John Wiley & Sons. ISBN 978-0-471-97815-2.","Base de desvios típicos por tipo de equipamento","pill-b"),
        ("LOPA & SIL","CCPS/AIChE (2001)","Layer of Protection Analysis: Simplified Process Risk Assessment","AIChE/CCPS, New York. ISBN 0-8169-0811-7. (Livro fundador do método LOPA)","Fórmula MCF = F_ie × ∏PFD_j; valores típicos de PFD por tipo de IPL","pill-p"),
        ("LOPA & SIL","Willey R.J. (2014)","Layer of Protection Analysis","Procedia Engineering 84:12–22. DOI: 10.1016/j.proeng.2014.10.405. Open Access CC BY-NC-ND.","Revisão dos valores de PFD; integração LOPA-SIL","pill-p"),
        ("LOPA & SIL","IEC 61511:2016","Functional Safety — Safety Instrumented Systems for the Process Industry Sector","International Electrotechnical Commission, 2ª ed., 2016. Parts 1–3.","Cálculo de SIL requerido a partir do MCF; verificação de PFD de SIS","pill-p"),
        ("Pool Fire","Shokri M., Beyler C.L. (1989)","Radiation from Large Pool Fires","Journal of Fire Protection Engineering 1(4):141–149. DOI: 10.1177/104239158900100404.","Modelo principal: E = 58·exp(−0.00823·D) kW/m²; fator de forma cilíndrico","pill-r"),
        ("Pool Fire","Heskestad G. (1983)","Luminous Height of Turbulent Diffusion Flames","Fire Safety Journal 5:103–108. Elsevier. Adotado pelo SFPE Handbook.","Correlação de altura de chama: Hf = 0.235·Q^0.4 − 1.02·D","pill-r"),
        ("Pool Fire","McGrattan K.B. et al. (2000)","Thermal Radiation from Large Pool Fires","NISTIR 6546, National Institute of Standards and Technology, Gaithersburg, MD.","Validação experimental dos modelos de radiação com dados de campo","pill-r"),
        ("Pool Fire","API RP 521 (2014)","Pressure-relieving and Depressuring Systems, 6ª ed.","American Petroleum Institute, Washington, DC.","Limiares de dano: 37.5 / 12.5 / 4.7 / 1.6 kW/m²","pill-r"),
        ("Dispersão Atmosférica","Pasquill F. (1961)","The Estimation of the Dispersion of Windborne Material","Meteorological Magazine 90(1063):33–49.","Modelo gaussiano + classificação de estabilidade atmosférica (A–F)","pill-b"),
        ("Dispersão Atmosférica","Turner D.B. (1970)","Workbook of Atmospheric Dispersion Estimates","EPA AP-26. U.S. Environmental Protection Agency, Research Triangle Park, NC.","Coeficientes σy, σz por classe de estabilidade e distância","pill-b"),
        ("Dispersão Atmosférica","EPA-454/R-99-005 (2000)","Meteorological Monitoring Guidance for Regulatory Modeling","U.S. EPA, Office of Air Quality Planning and Standards.","Guia oficial EPA para uso do modelo gaussiano em estudos regulatórios","pill-b"),
        ("Bow-Tie","CCPS/EI (2018)","Bow Ties in Risk Management: A Concept Book for Process Safety","AIChE/CCPS & Energy Institute. John Wiley & Sons. ISBN 978-1-119-37351-0.","Metodologia bow-tie: hazard, top event, ameaças, barreiras, consequências","pill-p"),
        ("Bow-Tie","Duijm N.J. (2009)","Safety-Barrier Diagrams as a Safety Management Tool","Reliability Engineering and System Safety 94(2):332–341. DOI: 10.1016/j.ress.2008.03.031.","Formalização matemática de diagramas de barreira e bow-tie","pill-p"),
        ("Limites de Exposição","NIOSH (2014)","NIOSH Pocket Guide to Chemical Hazards","DHHS Publication No. 2005-149. cdc.gov/niosh/npg.","IDLH — Immediately Dangerous to Life or Health (concentração para fuga em 30 min)","pill-a"),
        ("Limites de Exposição","AIHA (anual)","ERPG/WEEL Handbook","American Industrial Hygiene Association. Edição anual.","ERPG-1/2/3 — Emergency Response Planning Guidelines por composto","pill-a"),
        ("SDS / FISPQ","ABNT NBR 14725-4:2014","Produtos Químicos — Informações sobre Segurança, Saúde e Meio Ambiente — FISPQ","Associação Brasileira de Normas Técnicas, Rio de Janeiro.","16 seções obrigatórias da FISPQ; classificação GHS alinhada ao Rev.9","pill-g"),
        ("SDS / FISPQ","NR-26 (MTE, 2021)","Sinalização de Segurança","Portaria SEPRT 1.067/2021. Ministério do Trabalho e Emprego.","Pictogramas GHS obrigatórios no Brasil; integração com NR-20","pill-g"),
    ]

    cats = sorted(set(r[0] for r in REFS))
    for cat in cats:
        st.markdown(f"<div style='font-family:Space Grotesk,sans-serif;font-size:0.85rem;font-weight:600;color:#7AAEF5;margin:1.25rem 0 0.5rem;text-transform:uppercase;letter-spacing:0.08em;'>{cat}</div>", unsafe_allow_html=True)
        for _, src, title, meta, uso, pill_cls in [r for r in REFS if r[0]==cat]:
            st.markdown(f"""<div class='ref-block'>
                <div class='ref-title'>{src} — {title} <span class='pill {pill_cls}'>{uso[:50]}</span></div>
                <div class='ref-meta'>{meta}</div>
            </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
#  ABA 8 — SOBRE
# ════════════════════════════════════════════════════════════════════════════
with tab_sobre:
    st.markdown("""
    <div class='about-hero'>
      <div class='about-avatar'>GH</div>
      <div class='about-name'>Gabriel Hernandez Rozo</div>
      <div class='about-role'>Engenheiro · Segurança de Processo · Process Safety Management</div>
      <a href='https://www.linkedin.com/in/gabriel-hernandez-rozo-30751325b' target='_blank' class='linkedin-btn'>
        Conectar no LinkedIn →
      </a>
    </div>
    """, unsafe_allow_html=True)

    c1,c2 = st.columns(2)
    with c1:
        st.markdown("""<div class='cs-card'>
          <div class='cs-card-title'><span class='dot'></span>Sobre o ChemSafe Pro</div>
          <div style='font-size:0.85rem;color:#6B82AA;line-height:1.8;'>
            O ChemSafe Pro nasceu da necessidade real do engenheiro de segurança de processo ter acesso a uma plataforma integrada — do dado físico-químico à análise de risco estruturada — sem depender de software proprietário caro ou de ferramentas dispersas em múltiplas abas.<br><br>
            A plataforma une consulta de SDS (ABNT NBR 14725-4), análise HAZOP (IEC 61882:2016), diagrama Bow-Tie, cálculo LOPA+SIL (CCPS/IEC 61511), dispersão gaussiana (Pasquill-Gifford) e pool fire (Shokri-Beyler 1989) em um único ambiente web, acessível de qualquer dispositivo, sempre online e com todas as equações e referências rastreáveis para auditoria.
          </div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown("""<div class='cs-card'>
          <div class='cs-card-title'><span class='dot'></span>Metodologias e normas implementadas</div>
          <div style='display:grid;grid-template-columns:1fr 1fr;gap:6px;'>""" +
          "".join([f"<span class='pill pill-b'>{n}</span>" for n in ["IEC 61882:2016","CCPS LOPA 2001","IEC 61511:2016","API RP 521","Shokri-Beyler 1989","Heskestad 1983","Pasquill-Gifford","EPA AP-42","ABNT NBR 14725-4","NR-26 / GHS Rev.9","CCPS Bow-Tie 2018","NIOSH / ERPG / IDLH","NISTIR 6546","API RP 750","NR-13 / NR-20"]]) +
          "</div></div>", unsafe_allow_html=True)

    st.markdown("""<div class='cs-card' style='margin-top:0;'>
      <div class='cs-card-title'><span class='dot'></span>Aviso de uso e limitações</div>
      <div style='font-size:0.82rem;color:#4A6080;line-height:1.7;'>
        Os modelos e cálculos do ChemSafe Pro são baseados em correlações publicadas e validadas na literatura técnica. Os resultados são ferramentas de apoio à decisão e não substituem análises de risco formais conduzidas por profissionais habilitados (CREA/CRQ), nem o julgamento de engenheiros experientes em segurança de processo.<br><br>
        Os modelos de dispersão e incêndio são simplificados e possuem incertezas inerentes. Para estudos regulatórios, relatórios de impacto ambiental (RIMA) e projetos de SIS (IEC 61511), consulte simuladores certificados (PHAST, SAFETI, ALOHA) e a norma aplicável. O ChemSafe Pro é uma plataforma educacional e de triagem rápida (<i>screening tool</i>).
      </div>
    </div>""", unsafe_allow_html=True)

