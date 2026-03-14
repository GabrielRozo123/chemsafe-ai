from __future__ import annotations

DB = {
    'ethanol': {
        'nome':'Etanol','formula':'C₂H₅OH','cas':'64-17-5','pm':'46.07','cid':702,
        'hazards':['H225 — Líquido e vapor muito inflamáveis (Cat. 2)',
                   'H319 — Provoca irritação ocular grave (Cat. 2A)',
                   'H336 — Pode provocar sonolência ou vertigens (Cat. 3)'],
        'pics':['GHS02 Inflamável','GHS07 Irritante'],'sinal':'Perigo',
        'props':[('Ponto de ebulição','78.4 °C'),('Ponto de fusão','-114.1 °C'),
                 ('Ponto de fulgor','13 °C'),('LIE / LSE','3.3 % / 19 %'),
                 ('AIT (Autoignição)','365 °C'),('Densidade','0.789 g/cm³'),
                 ('Pressão de vapor (20°C)','5.8 kPa'),('TLV-TWA','1000 ppm'),
                 ('IDLH','3300 ppm'),('MIE','0.65 mJ')],
        'nfpa':(2,3,0,''),'lie':3.3,'lse':19.0,'flash_c':13,'ait':365,'mie':0.65,
    },
    'acetone': {
        'nome':'Acetona','formula':'C₃H₆O','cas':'67-64-1','pm':'58.08','cid':180,
        'hazards':['H225 — Líquido e vapor extremamente inflamáveis (Cat. 1)',
                   'H319 — Provoca irritação ocular grave (Cat. 2A)',
                   'H336 — Pode provocar sonolência ou vertigens (Cat. 3)'],
        'pics':['GHS02 Inflamável','GHS07 Irritante'],'sinal':'Perigo',
        'props':[('Ponto de ebulição','56.1 °C'),('Ponto de fusão','-94.7 °C'),
                 ('Ponto de fulgor','-18 °C'),('LIE / LSE','2.5 % / 12.8 %'),
                 ('AIT (Autoignição)','465 °C'),('Densidade','0.791 g/cm³'),
                 ('Pressão de vapor (20°C)','23.5 kPa'),('TLV-TWA','500 ppm'),
                 ('IDLH','2500 ppm'),('MIE','1.15 mJ')],
        'nfpa':(1,3,0,''),'lie':2.5,'lse':12.8,'flash_c':-18,'ait':465,'mie':1.15,
    },
    'h2so4': {
        'nome':'Ácido Sulfúrico','formula':'H₂SO₄','cas':'7664-93-9','pm':'98.07','cid':1118,
        'hazards':['H314 — Provoca queimaduras graves na pele e nos olhos (Cat. 1A)',
                   'H335 — Pode irritar as vias respiratórias (Cat. 3)'],
        'pics':['GHS05 Corrosivo','GHS07 Irritante'],'sinal':'Perigo',
        'props':[('Ponto de ebulição','337 °C'),('Ponto de fusão','10 °C'),
                 ('Ponto de fulgor','Não inflamável'),('LIE / LSE','N/A'),
                 ('Densidade','1.84 g/cm³'),('pH (1 mol/L)','~0'),
                 ('TLV-STEL','0.2 mg/m³'),('IDLH','15 mg/m³')],
        'nfpa':(3,0,2,'W'),'lie':None,'lse':None,'flash_c':None,'ait':None,'mie':None,
    },
    'ammonia': {
        'nome':'Amônia','formula':'NH₃','cas':'7664-41-7','pm':'17.03','cid':222,
        'hazards':['H221 — Gás inflamável (Cat. 2)',
                   'H314 — Provoca queimaduras graves na pele e nos olhos (Cat. 1A)',
                   'H331 — Tóxico por inalação (Cat. 3)',
                   'H400 — Muito tóxico para organismos aquáticos (Cat. 1)'],
        'pics':['GHS02','GHS05','GHS06','GHS09'],'sinal':'Perigo',
        'props':[('Ponto de ebulição','-33.3 °C'),('Ponto de fusão','-77.7 °C'),
                 ('Ponto de fulgor','11 °C (aq)'),('LIE / LSE','15 % / 28 %'),
                 ('AIT (Autoignição)','651 °C'),('IDLH','300 ppm'),
                 ('TLV-TWA','25 ppm'),('ERPG-2','200 ppm'),('ERPG-3','1000 ppm')],
        'nfpa':(3,1,0,''),'lie':15.0,'lse':28.0,'flash_c':11,'ait':651,'mie':680,
    },
    'methane': {
        'nome':'Metano','formula':'CH₄','cas':'74-82-8','pm':'16.04','cid':297,
        'hazards':['H220 — Gás extremamente inflamável (Cat. 1A)',
                   'H280 — Contém gás sob pressão'],
        'pics':['GHS02','GHS04'],'sinal':'Perigo',
        'props':[('Ponto de ebulição','-161.5 °C'),('Ponto de fusão','-182.5 °C'),
                 ('LIE / LSE','5 % / 15 %'),('AIT (Autoignição)','537 °C'),
                 ('Densidade gás','0.717 g/L'),('MIE','0.28 mJ'),
                 ('Chama visível','Não — invisível!')],
        'nfpa':(1,4,0,''),'lie':5.0,'lse':15.0,'flash_c':-188,'ait':537,'mie':0.28,
    },
    'toluene': {
        'nome':'Tolueno','formula':'C₇H₈','cas':'108-88-3','pm':'92.14','cid':1140,
        'hazards':['H225 — Líquido e vapor muito inflamáveis (Cat. 2)',
                   'H304 — Pode ser fatal por ingestão e penetração nas vias respiratórias (Cat. 1)',
                   'H315 — Provoca irritação cutânea (Cat. 2)',
                   'H336 — Pode provocar sonolência ou vertigens (Cat. 3)',
                   'H361 — Suspeito de prejudicar a fertilidade ou o nascituro (Cat. 2)'],
        'pics':['GHS02','GHS07','GHS08'],'sinal':'Perigo',
        'props':[('Ponto de ebulição','110.6 °C'),('Ponto de fusão','-95 °C'),
                 ('Ponto de fulgor','4 °C'),('LIE / LSE','1.1 % / 7.1 %'),
                 ('AIT (Autoignição)','480 °C'),('Densidade','0.867 g/cm³'),
                 ('TLV-TWA','20 ppm'),('IDLH','500 ppm'),('MIE','0.24 mJ')],
        'nfpa':(2,3,0,''),'lie':1.1,'lse':7.1,'flash_c':4,'ait':480,'mie':0.24,
    },
}

MAPA = {'etanol':'ethanol','álcool etílico':'ethanol','alcohol':'ethanol',
        'acetona':'acetone','propanona':'acetone',
        'ácido sulfúrico':'h2so4','acido sulfurico':'h2so4','sulfuric acid':'h2so4',
        'amônia':'ammonia','amonia':'ammonia','azane':'ammonia',
        'metano':'methane','gás natural':'methane',
        'tolueno':'toluene','toluol':'toluene'}


def resolve_compound(query: str):
    q = query.strip().lower()
    if q in DB:
        return DB[q]
    if q in MAPA:
        return DB[MAPA[q]]
    for _, value in DB.items():
        if value['cas'] == q:
            return value
    return None
