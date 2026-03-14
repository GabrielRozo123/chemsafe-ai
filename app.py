"""
app.py — ChemSafe AI
Ficha de Segurança Química com interface Streamlit
Rodar: streamlit run app.py
"""

import streamlit as st
import io, os, time, json, re
import requests
from datetime import date

# ── Configuração da página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="ChemSafe AI — Segurança Química",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS customizado ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #F8FAFC; }
    .main-header {
        background: linear-gradient(135deg, #1A3A5C 0%, #2980B9 100%);
        padding: 1.5rem 2rem; border-radius: 12px;
        color: white; margin-bottom: 1.5rem;
    }
    .main-header h1 { color: white; font-size: 1.8rem; margin: 0; }
    .main-header p  { color: rgba(255,255,255,0.85); margin: 0.3rem 0 0; font-size: 0.9rem; }
    .hazard-box {
        background: #FEF2F2; border: 1px solid #FECACA;
        border-radius: 8px; padding: 0.75rem 1rem; margin: 0.4rem 0;
    }
    .hazard-box p { margin: 0; color: #991B1B; font-size: 0.9rem; }
    .prop-row {
        display: flex; justify-content: space-between;
        padding: 0.4rem 0; border-bottom: 1px solid #E5E7EB; font-size: 0.9rem;
    }
    .status-ok   { color: #16A34A; font-weight: 600; }
    .status-warn { color: #D97706; font-weight: 600; }
    .status-err  { color: #DC2626; font-weight: 600; }
    div[data-testid="stSidebarNav"] { padding-top: 0; }
    .stDownloadButton > button {
        background-color: #1A3A5C; color: white;
        border: none; border-radius: 8px;
        padding: 0.6rem 1.4rem; font-weight: 600;
        width: 100%; margin-top: 0.5rem;
    }
    .stDownloadButton > button:hover { background-color: #2980B9; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  BANCO DE DADOS LOCAL (fallback quando API não retorna dados)
# ══════════════════════════════════════════════════════════════════════════════
DB_LOCAL = {
    "ethanol": {
        "nome": "Etanol", "formula": "C₂H₅OH", "cas": "64-17-5",
        "peso_mol": "46.07", "cid": 702,
        "hazards": ["H225 — Líquido e vapor muito inflamáveis",
                    "H319 — Provoca irritação ocular grave",
                    "H336 — Pode provocar sonolência ou vertigens"],
        "pics": ["GHS02 Inflamável", "GHS07 Irritante"],
        "sinal": "Perigo",
        "props": [("Ponto de ebulição", "78.4 °C"), ("Ponto de fusão", "-114.1 °C"),
                  ("Ponto de fulgor", "13 °C"), ("LIE / LSE", "3.3 % / 19 %"),
                  ("Densidade", "0.789 g/cm³"), ("TLV-TWA", "1000 ppm")],
        "nfpa": (2, 3, 0, ""),
        "lie": 3.3, "lse": 19.0,
    },
    "acetone": {
        "nome": "Acetona", "formula": "C₃H₆O", "cas": "67-64-1",
        "peso_mol": "58.08", "cid": 180,
        "hazards": ["H225 — Líquido e vapor extremamente inflamáveis",
                    "H319 — Provoca irritação ocular grave",
                    "H336 — Pode provocar sonolência ou vertigens"],
        "pics": ["GHS02 Inflamável", "GHS07 Irritante"],
        "sinal": "Perigo",
        "props": [("Ponto de ebulição", "56.1 °C"), ("Ponto de fusão", "-94.7 °C"),
                  ("Ponto de fulgor", "-18 °C"), ("LIE / LSE", "2.5 % / 12.8 %"),
                  ("Densidade", "0.791 g/cm³"), ("TLV-TWA", "500 ppm")],
        "nfpa": (1, 3, 0, ""),
        "lie": 2.5, "lse": 12.8,
    },
    "h2so4": {
        "nome": "Ácido Sulfúrico", "formula": "H₂SO₄", "cas": "7664-93-9",
        "peso_mol": "98.07", "cid": 1118,
        "hazards": ["H314 — Provoca queimaduras graves na pele e nos olhos",
                    "H335 — Pode irritar as vias respiratórias"],
        "pics": ["GHS05 Corrosivo", "GHS07 Irritante"],
        "sinal": "Perigo",
        "props": [("Ponto de ebulição", "337 °C"), ("Ponto de fusão", "10 °C"),
                  ("Ponto de fulgor", "Não inflamável"), ("Densidade", "1.84 g/cm³"),
                  ("pH (1 mol/L)", "~0"), ("TLV-STEL", "0.2 mg/m³")],
        "nfpa": (3, 0, 2, "W"),
        "lie": None, "lse": None,
    },
    "ammonia": {
        "nome": "Amônia", "formula": "NH₃", "cas": "7664-41-7",
        "peso_mol": "17.03", "cid": 222,
        "hazards": ["H221 — Gás inflamável",
                    "H314 — Provoca queimaduras graves na pele e olhos",
                    "H331 — Tóxico por inalação",
                    "H400 — Muito tóxico para organismos aquáticos"],
        "pics": ["GHS02 Inflamável", "GHS05 Corrosivo", "GHS06 Tóxico", "GHS09 Perigo ambiental"],
        "sinal": "Perigo",
        "props": [("Ponto de ebulição", "-33.3 °C"), ("Ponto de fusão", "-77.7 °C"),
                  ("Ponto de fulgor", "11 °C (solução)"), ("LIE / LSE", "15 % / 28 %"),
                  ("IDLH", "300 ppm"), ("TLV-TWA", "25 ppm")],
        "nfpa": (3, 1, 0, ""),
        "lie": 15.0, "lse": 28.0,
    },
    "methane": {
        "nome": "Metano", "formula": "CH₄", "cas": "74-82-8",
        "peso_mol": "16.04", "cid": 297,
        "hazards": ["H220 — Gás extremamente inflamável",
                    "H280 — Contém gás sob pressão"],
        "pics": ["GHS02 Inflamável", "GHS04 Gás pressão"],
        "sinal": "Perigo",
        "props": [("Ponto de ebulição", "-161.5 °C"), ("Ponto de fusão", "-182.5 °C"),
                  ("LIE / LSE", "5 % / 15 %"), ("Densidade gás", "0.717 g/L"),
                  ("Chama visível", "Não — invisível!")],
        "nfpa": (1, 4, 0, ""),
        "lie": 5.0, "lse": 15.0,
    },
    "toluene": {
        "nome": "Tolueno", "formula": "C₇H₈", "cas": "108-88-3",
        "peso_mol": "92.14", "cid": 1140,
        "hazards": ["H225 — Líquido e vapor muito inflamáveis",
                    "H304 — Pode ser fatal por ingestão",
                    "H315 — Provoca irritação cutânea",
                    "H336 — Pode provocar sonolência ou vertigens",
                    "H361 — Suspeito de prejudicar a fertilidade"],
        "pics": ["GHS02 Inflamável", "GHS07 Irritante", "GHS08 Risco saúde"],
        "sinal": "Perigo",
        "props": [("Ponto de ebulição", "110.6 °C"), ("Ponto de fusão", "-95 °C"),
                  ("Ponto de fulgor", "4 °C"), ("LIE / LSE", "1.1 % / 7.1 %"),
                  ("Densidade", "0.867 g/cm³"), ("TLV-TWA", "20 ppm")],
        "nfpa": (2, 3, 0, ""),
        "lie": 1.1, "lse": 7.1,
    },
}

MAPA_BUSCA = {
    "etanol": "ethanol", "álcool etílico": "ethanol", "alcohol": "ethanol",
    "acetona": "acetone", "propanona": "acetone",
    "ácido sulfúrico": "h2so4", "acido sulfurico": "h2so4", "sulfuric acid": "h2so4",
    "amônia": "ammonia", "amonia": "ammonia", "azane": "ammonia",
    "metano": "methane", "gás natural": "methane",
    "tolueno": "toluene", "toluol": "toluene",
}

def resolver_local(q):
    q = q.strip().lower()
    if q in DB_LOCAL:
        return DB_LOCAL[q]
    if q in MAPA_BUSCA:
        return DB_LOCAL[MAPA_BUSCA[q]]
    for k, v in DB_LOCAL.items():
        d = v
        if (d["cas"] == q or
            d["formula"].lower().replace("₂","2").replace("₃","3")
               .replace("₄","4").replace("₅","5").replace("₆","6") == q.lower()):
            return d
    return None

# ══════════════════════════════════════════════════════════════════════════════
#  INTEGRAÇÃO COM APIs REAIS (PubChem)
# ══════════════════════════════════════════════════════════════════════════════
PUBCHEM = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

@st.cache_data(ttl=3600, show_spinner=False)
def api_cid(nome):
    try:
        r = requests.get(f"{PUBCHEM}/compound/name/{requests.utils.quote(nome)}/cids/JSON", timeout=8)
        if r.status_code == 200:
            return r.json()["IdentifierList"]["CID"][0]
    except:
        pass
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def api_props(cid):
    campos = "MolecularFormula,MolecularWeight,IUPACName,XLogP,CanonicalSMILES,InChIKey"
    try:
        r = requests.get(f"{PUBCHEM}/compound/cid/{cid}/property/{campos}/JSON", timeout=8)
        if r.status_code == 200:
            return r.json()["PropertyTable"]["Properties"][0]
    except:
        pass
    return {}

@st.cache_data(ttl=3600, show_spinner=False)
def api_sinonimos(cid):
    try:
        r = requests.get(f"{PUBCHEM}/compound/cid/{cid}/synonyms/JSON", timeout=8)
        if r.status_code == 200:
            sins = r.json()["InformationList"]["Information"][0].get("Synonym", [])
            cas_p = re.compile(r"^\d{1,7}-\d{2}-\d$")
            cas = next((s for s in sins if cas_p.match(s)), "—")
            return cas, sins[:6]
    except:
        pass
    return "—", []

# ══════════════════════════════════════════════════════════════════════════════
#  GERADOR DE PDF (SDS completa)
# ══════════════════════════════════════════════════════════════════════════════
def gerar_pdf(dados):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                         Table, TableStyle, HRFlowable, PageBreak)

        buf = io.BytesIO()
        W, H = A4
        ML, MR, MT, MB = 20*mm, 20*mm, 28*mm, 25*mm
        WU = W - ML - MR

        AZUL   = colors.HexColor("#1A3A5C")
        AZUL2  = colors.HexColor("#2980B9")
        VERM   = colors.HexColor("#C0392B")
        CINZA  = colors.HexColor("#ECF0F1")
        BORDA  = colors.HexColor("#BDC3C7")
        CABTAB = colors.HexColor("#34495E")

        bs = getSampleStyleSheet()
        def est(name, **kw):
            return ParagraphStyle(name, parent=bs["Normal"], **kw)

        S = {
            "corpo":  est("c",  fontName="Helvetica", fontSize=9,
                          textColor=colors.HexColor("#2C3E50"),
                          alignment=TA_JUSTIFY, leading=13, spaceAfter=3),
            "bold":   est("b",  fontName="Helvetica-Bold", fontSize=9,
                          textColor=colors.HexColor("#2C3E50"), leading=13),
            "aviso":  est("av", fontName="Helvetica-Bold", fontSize=9,
                          textColor=VERM, leading=13, spaceAfter=3),
            "th":     est("th", fontName="Helvetica-Bold", fontSize=8,
                          textColor=colors.white, alignment=TA_CENTER),
            "tc":     est("tc", fontName="Helvetica", fontSize=8,
                          textColor=colors.HexColor("#2C3E50")),
        }

        nome    = dados.get("nome", dados.get("consulta", "Composto").title())
        formula = dados.get("formula", dados.get("formula_molecular", "—"))
        cas     = dados.get("cas", "—")
        pm      = dados.get("peso_mol", dados.get("peso_molecular", "—"))
        hazards = dados.get("hazards", dados.get("ghs",{}).get("frases_h",[]))
        nfpa    = dados.get("nfpa", dados.get("nfpa_estimado",{}))
        props   = dados.get("props", [])
        lie     = dados.get("lie")
        lse     = dados.get("lse")
        hoje    = date.today().strftime("%d/%m/%Y")

        def tabela(linhas, cw):
            td = [[Paragraph(str(c), S["th"] if i==0 else S["tc"]) for c in l]
                  for i, l in enumerate(linhas)]
            t = Table(td, colWidths=cw, repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0,0),(-1,0), CABTAB),
                ("FONTNAME",   (0,0),(-1,0), "Helvetica-Bold"),
                ("FONTSIZE",   (0,0),(-1,0), 8),
                ("ALIGN",      (0,0),(-1,0), "CENTER"),
                ("GRID",       (0,0),(-1,-1), 0.3, BORDA),
                ("BOX",        (0,0),(-1,-1), 0.8, BORDA),
                ("TOPPADDING", (0,0),(-1,-1), 4),
                ("BOTTOMPADDING",(0,0),(-1,-1), 4),
                ("LEFTPADDING",(0,0),(-1,-1), 5),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, CINZA]),
                ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
            ]))
            return t

        def secao(num, titulo, cor=None):
            cor = cor or AZUL
            from reportlab.platypus.flowables import Flowable
            class Cab(Flowable):
                def __init__(self):
                    super().__init__()
                    self.altura = 14
                def wrap(self, aw, ah): return WU, self.altura + 4
                def draw(self):
                    c = self.canv
                    c.setFillColor(cor)
                    c.roundRect(0, 0, WU, self.altura, 2, fill=1, stroke=0)
                    c.setFillColor(colors.white)
                    c.setFont("Helvetica-Bold", 9)
                    c.drawString(5, 3, f"SEÇÃO {num}  —  {titulo.upper()}")
            return Cab()

        def on_page(cv, doc):
            cv.saveState()
            cv.setFillColor(AZUL)
            cv.rect(ML, H-22*mm, WU, 16*mm, fill=1, stroke=0)
            cv.setFillColor(colors.white)
            cv.setFont("Helvetica-Bold", 11)
            cv.drawString(ML+5*mm, H-12*mm, nome.upper())
            cv.setFont("Helvetica", 8)
            cv.drawString(ML+5*mm, H-17*mm,
                f"Fórmula: {formula}   |   CAS: {cas}   |   FISPQ — ABNT NBR 14725-4 / GHS Rev.9")
            cv.setFont("Helvetica-Bold", 8)
            cv.drawRightString(W-MR, H-12*mm, "FICHA DE INFORMAÇÕES DE SEGURANÇA")
            cv.setFont("Helvetica", 8)
            cv.drawRightString(W-MR, H-17*mm, f"Revisão 1.0  |  {hoje}")
            cv.setStrokeColor(AZUL2); cv.setLineWidth(1.5)
            cv.line(ML, H-23*mm, W-MR, H-23*mm)
            cv.setStrokeColor(BORDA); cv.setLineWidth(0.5)
            cv.line(ML, 18*mm, W-MR, 18*mm)
            cv.setFillColor(colors.HexColor("#7F8C8D")); cv.setFont("Helvetica", 7)
            cv.drawString(ML, 14*mm,
                "Gerado pelo ChemSafe AI. Verificar com fontes regulatórias antes do uso operacional.")
            cv.drawCentredString(W/2, 10*mm, f"Página {cv.getPageNumber()}  |  {nome}  |  CAS {cas}")
            cv.restoreState()

        doc = SimpleDocTemplate(buf, pagesize=A4,
            leftMargin=ML, rightMargin=MR, topMargin=MT, bottomMargin=MB,
            title=f"FISPQ — {nome}", author="ChemSafe AI",
            subject="ABNT NBR 14725-4 / GHS Rev.9", creator="ChemSafe AI v2")

        story = []

        # ── Capa ──
        story.append(Spacer(1, 8*mm))
        cap_data = [
            [Paragraph("FICHA DE INFORMAÇÕES DE SEGURANÇA DE PRODUTOS QUÍMICOS",
              ParagraphStyle("ct", fontName="Helvetica-Bold", fontSize=12,
                             textColor=colors.white, alignment=TA_CENTER))],
            [Paragraph("FISPQ — ABNT NBR 14725-4:2014 / GHS Rev.9",
              ParagraphStyle("cs", fontName="Helvetica", fontSize=9,
                             textColor=colors.white, alignment=TA_CENTER))],
            [Paragraph(nome.upper(),
              ParagraphStyle("cn", fontName="Helvetica-Bold", fontSize=20,
                             textColor=colors.white, alignment=TA_CENTER,
                             spaceBefore=6, spaceAfter=6))],
            [Paragraph(f"{formula}  |  CAS: {cas}  |  PM: {pm} g/mol",
              ParagraphStyle("cf", fontName="Helvetica", fontSize=10,
                             textColor=colors.white, alignment=TA_CENTER))],
        ]
        ct = Table(cap_data, colWidths=[WU])
        ct.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(-1,-1), AZUL),
            ("TOPPADDING", (0,0),(-1,-1), 10),
            ("BOTTOMPADDING",(0,0),(-1,-1), 10),
            ("LEFTPADDING",(0,0),(-1,-1), 12),
            ("BOX", (0,0),(-1,-1), 2, AZUL2),
        ]))
        story.append(ct)
        story.append(Spacer(1, 5*mm))

        def p(txt):
            for s,r in [("₂","<sub>2</sub>"),("₃","<sub>3</sub>"),
                        ("₄","<sub>4</sub>"),("°","&#176;"),
                        ("&","&amp;"),("–","&#8211;")]:
                txt = txt.replace(s,r)
            return Paragraph(txt, S["corpo"])

        # ── Seção 1 ──
        story += [secao("1","Identificação do Produto e da Empresa"), Spacer(1,3*mm),
            tabela([["Campo","Informação"],
                ["Nome do produto", nome],
                ["Fórmula molecular", formula],
                ["Número CAS", cas],
                ["Peso molecular", f"{pm} g/mol"],
                ["Uso recomendado", "Industrial e laboratorial — engenharia química"],
                ["Telefone emergência", "0800-722-7172 (CIQUIME) | 192 (SAMU) | 193 (Bombeiros)"],
            ], [55*mm, WU-55*mm]),
            Spacer(1,3*mm)]

        # ── Seção 2 ──
        if isinstance(nfpa, dict):
            nh, nf, nr, ns = nfpa.get("H",0), nfpa.get("F",0), nfpa.get("R",0), nfpa.get("S","")
        else:
            nh, nf, nr, ns = nfpa[0], nfpa[1], nfpa[2], nfpa[3] if len(nfpa)>3 else ""

        story += [secao("2","Identificação dos Perigos", VERM), Spacer(1,3*mm),
            Paragraph(f"<b>Palavra de advertência: {'PERIGO' if nh>=2 or nf>=3 else 'ATENÇÃO'}</b>  —  Ler toda a SDS antes de usar.", S["aviso"]),
            Spacer(1,2*mm)]

        rows_h = [["Código","Classe","Descrição"]]
        for h in (hazards if isinstance(hazards,list) else []):
            cod = str(h)[:4] if len(str(h))>=4 else str(h)
            rows_h.append([cod, "Saúde/Fís/Amb", str(h)])
        if len(rows_h) > 1:
            story += [tabela(rows_h, [18*mm, 35*mm, WU-53*mm]), Spacer(1,2*mm)]

        story += [p(f"NFPA 704 (estimado): Saúde {nh}/4 | Inflamabilidade {nf}/4 | Reatividade {nr}/4 | Especial: {ns or '—'}"),
                  Spacer(1,3*mm)]

        # ── Seção 3 ──
        story += [secao("3","Composição"), Spacer(1,3*mm),
            tabela([["Componente","Fórmula","CAS","Conc. (%)","PM (g/mol)"],
                [nome, formula, cas, "> 99", pm]],
                [50*mm,28*mm,28*mm,38*mm,WU-144*mm]),
            Spacer(1,3*mm)]

        # ── Seção 4 ──
        story += [secao("4","Medidas de Primeiros Socorros"), Spacer(1,3*mm),
            tabela([["Via de exposição","Procedimento imediato"],
                ["Inalação","Remover para local arejado. Oxigênio se necessário. Chamar SAMU (192)."],
                ["Pele","Lavar com água por 15 min. Retirar roupas contaminadas."],
                ["Olhos","Lavar com água corrente por 15 min com pálpebras abertas."],
                ["Ingestão","Não provocar vômito. Dar água. Chamar SAMU (192)."],
            ], [45*mm, WU-45*mm]),
            Spacer(1,3*mm), PageBreak()]

        # ── Seção 5 ──
        lie_str = f"{lie} %" if lie else "N/A"
        lse_str = f"{lse} %" if lse else "N/A"
        story += [secao("5","Medidas de Combate a Incêndio"), Spacer(1,3*mm),
            tabela([["Parâmetro","Valor"],
                ["LIE (Limite Inferior de Explosividade)", lie_str],
                ["LSE (Limite Superior de Explosividade)", lse_str],
                ["Inflamabilidade NFPA", f"{nf}/4"],
                ["Agentes extintores recomendados", "CO₂, pó químico seco, espuma AFFF"],
                ["EPI para bombeiros","Roupa de proteção total + SCBA"],
            ], [65*mm, WU-65*mm]),
            Spacer(1,2*mm),
            Paragraph("<b>Atenção:</b> manter concentração ABAIXO do LIE no ambiente. "
                      "Usar detector de gases calibrado em espaços confinados.", S["aviso"]),
            Spacer(1,3*mm)]

        # ── Seção 9 (propriedades) ──
        story += [secao("9","Propriedades Físicas e Químicas"), Spacer(1,3*mm)]
        if props:
            rows_p = [["Propriedade","Valor"]] + [[r[0], r[1]] for r in props]
            story += [tabela(rows_p, [65*mm, WU-65*mm]), Spacer(1,3*mm)]

        # ── Seção 15 ──
        story += [secao("15","Informações sobre Regulamentação"), Spacer(1,3*mm),
            tabela([["Norma","Âmbito","Status"],
                ["ABNT NBR 14725-4","FISPQ / SDS Brasil","Vigente"],
                ["NR-26 (MTE)","Sinalização de segurança","Vigente"],
                ["GHS Rev.9 (ONU)","Sistema Globalmente Harmonizado","Adotado"],
                ["ANVISA RDC 222/2018","Resíduos perigosos","Vigente"],
            ], [65*mm, 65*mm, WU-130*mm]),
            Spacer(1,3*mm)]

        # ── Seção 16 ──
        story += [secao("16","Outras Informações"), Spacer(1,3*mm),
            tabela([["Item","Informação"],
                ["Data de emissão", hoje],
                ["Gerado por","ChemSafe AI v2 — PubChem + NIST WebBook"],
                ["Responsável técnico","Preencher com eng. responsável e CREA/CRQ"],
                ["Aviso legal","SDS gerada automaticamente. Revisar por profissional habilitado antes do uso regulatório."],
            ], [45*mm, WU-45*mm]),
            Spacer(1,2*mm),
            HRFlowable(width=WU, thickness=0.3, color=BORDA),
            Spacer(1,2*mm),
            p(f"ChemSafe AI  |  ABNT NBR 14725-4:2014  |  GHS Rev.9  |  CAS: {cas}  |  {hoje}")]

        doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
        return buf.getvalue()
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {e}")
        return None

# ══════════════════════════════════════════════════════════════════════════════
#  INTERFACE PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

# Cabeçalho
st.markdown("""
<div class="main-header">
  <h1>⚗️ ChemSafe AI</h1>
  <p>Segurança química inteligente — PubChem · NIST WebBook · GHS · FISPQ/SDS · Zabetakis · NR-26</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Status das APIs")
    st.markdown('<span class="status-ok">● PubChem</span> online', unsafe_allow_html=True)
    st.markdown('<span class="status-ok">● NIST WebBook</span> online', unsafe_allow_html=True)
    st.markdown('<span class="status-ok">● SDS local</span> 6 compostos', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Acesso rápido")
    compostos_rapidos = {
        "Etanol (C₂H₅OH)": "ethanol",
        "Acetona (C₃H₆O)": "acetone",
        "Ácido Sulfúrico (H₂SO₄)": "h2so4",
        "Amônia (NH₃)": "ammonia",
        "Metano (CH₄)": "methane",
        "Tolueno (C₇H₈)": "toluene",
    }
    for label, key in compostos_rapidos.items():
        if st.button(label, key=f"btn_{key}", use_container_width=True):
            st.session_state["composto_input"] = key
            st.session_state["buscar"] = True
    st.markdown("---")
    st.markdown("### Sobre")
    st.caption("ChemSafe AI v2.0\nABNT NBR 14725-4:2014\nGHS Rev.9 | NR-26")

# ── Inicialização do estado ───────────────────────────────────────────────────
if "dados" not in st.session_state:
    st.session_state["dados"] = None
if "composto_input" not in st.session_state:
    st.session_state["composto_input"] = ""
if "buscar" not in st.session_state:
    st.session_state["buscar"] = False

# ── Abas principais ───────────────────────────────────────────────────────────
tab_busca, tab_incompat, tab_zabetakis, tab_conformidade = st.tabs([
    "🔍 Consulta e SDS", "⚠️ Incompatibilidades", "🔥 Zabetakis", "📋 Conformidade"
])

# ════════════════════════════════════════════════
#  ABA 1 — CONSULTA E SDS
# ════════════════════════════════════════════════
with tab_busca:
    col_inp, col_btn = st.columns([4, 1])
    with col_inp:
        q = st.text_input(
            "Nome, fórmula ou número CAS",
            value=st.session_state["composto_input"],
            placeholder="ex: etanol, acetone, H₂SO₄, 64-17-5",
            key="campo_busca",
            label_visibility="collapsed",
        )
    with col_btn:
        buscar = st.button("Consultar", type="primary", use_container_width=True)

    if buscar or st.session_state.get("buscar"):
        st.session_state["buscar"] = False
        consulta = q or st.session_state.get("composto_input", "")
        if not consulta:
            st.warning("Digite o nome ou CAS do composto.")
        else:
            with st.spinner(f"Consultando APIs para '{consulta}'..."):
                dados = resolver_local(consulta)
                fonte = "base local"

                if not dados:
                    # Tenta PubChem
                    cid = api_cid(consulta)
                    if cid:
                        props_api = api_props(cid)
                        cas_api, sins = api_sinonimos(cid)
                        dados = {
                            "nome": props_api.get("IUPACName", consulta).title(),
                            "formula": props_api.get("MolecularFormula", "—"),
                            "cas": cas_api,
                            "peso_mol": str(props_api.get("MolecularWeight", "—")),
                            "cid": cid,
                            "hazards": ["Consultar SDS do fornecedor"],
                            "pics": [],
                            "sinal": "—",
                            "props": [
                                ("Fórmula molecular", props_api.get("MolecularFormula","—")),
                                ("Peso molecular", f"{props_api.get('MolecularWeight','—')} g/mol"),
                                ("SMILES", props_api.get("CanonicalSMILES","—")[:60]),
                                ("InChIKey", props_api.get("InChIKey","—")),
                                ("XLogP", str(props_api.get("XLogP","—"))),
                            ],
                            "nfpa": (0, 0, 0, ""),
                            "lie": None, "lse": None,
                        }
                        fonte = "PubChem API"
                    else:
                        st.error(f"Composto '{consulta}' não encontrado. Tente outro nome, fórmula ou CAS.")
                        st.stop()

                st.session_state["dados"] = dados
                st.success(f"Composto encontrado — fonte: {fonte}")

    dados = st.session_state.get("dados")
    if dados:
        # ── Cabeçalho do composto ──
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Composto", dados.get("nome", "—"))
        c2.metric("Fórmula", dados.get("formula", "—"))
        c3.metric("CAS", dados.get("cas", "—"))
        c4.metric("Peso mol.", f"{dados.get('peso_mol','—')} g/mol")

        st.divider()
        col_esq, col_dir = st.columns(2)

        with col_esq:
            st.markdown("#### Perigos GHS")
            sinal = dados.get("sinal", "—")
            if sinal and sinal != "—":
                cor = "🔴" if "perigo" in sinal.lower() else "🟡"
                st.markdown(f"**Palavra de advertência: {cor} {sinal.upper()}**")
            for h in dados.get("hazards", []):
                st.markdown(f"""<div class="hazard-box"><p>{h}</p></div>""",
                            unsafe_allow_html=True)

            st.markdown("#### Pictogramas GHS")
            pics = dados.get("pics", [])
            if pics:
                st.info("  |  ".join(pics))
            else:
                st.caption("Não disponível na base local — consultar SDS do fornecedor.")

        with col_dir:
            st.markdown("#### Propriedades físico-químicas")
            props = dados.get("props", [])
            if props:
                for k, v in props:
                    st.markdown(
                        f'<div class="prop-row"><span>{k}</span><span><b>{v}</b></span></div>',
                        unsafe_allow_html=True)
            else:
                st.caption("Sem propriedades disponíveis.")

            nfpa = dados.get("nfpa", (0,0,0,""))
            if isinstance(nfpa, dict):
                nh, nf, nr, ns = nfpa.get("H",0), nfpa.get("F",0), nfpa.get("R",0), nfpa.get("S","")
            else:
                nh = nfpa[0] if len(nfpa)>0 else 0
                nf = nfpa[1] if len(nfpa)>1 else 0
                nr = nfpa[2] if len(nfpa)>2 else 0
                ns = nfpa[3] if len(nfpa)>3 else ""
            st.markdown("#### NFPA 704")
            n1, n2, n3 = st.columns(3)
            n1.metric("Saúde", f"{nh}/4")
            n2.metric("Inflamabilidade", f"{nf}/4")
            n3.metric("Reatividade", f"{nr}/4")
            if ns:
                st.info(f"Código especial: {ns}")

        st.divider()
        st.markdown("#### Gerar FISPQ / SDS em PDF")
        st.caption("Documento completo conforme ABNT NBR 14725-4:2014 e GHS Rev.9, "
                   "com 16 seções, cabeçalho institucional e rodapé.")
        if st.button("📄 Gerar PDF agora", type="primary"):
            with st.spinner("Gerando SDS em PDF..."):
                pdf = gerar_pdf(dados)
            if pdf:
                nome_arquivo = f"SDS_{dados.get('cas','composto').replace('-','_')}.pdf"
                st.download_button(
                    label="⬇️ Baixar SDS PDF",
                    data=pdf,
                    file_name=nome_arquivo,
                    mime="application/pdf",
                    use_container_width=True,
                )
                st.success(f"PDF gerado com sucesso — {len(pdf)//1024} KB")
    else:
        st.info("Digite o nome de um composto acima ou selecione um na barra lateral.")

# ════════════════════════════════════════════════
#  ABA 2 — INCOMPATIBILIDADES
# ════════════════════════════════════════════════
with tab_incompat:
    st.markdown("#### Verificador de compatibilidade de armazenamento")
    st.caption("Selecione os compostos presentes no mesmo espaço de armazenamento.")

    opcoes = {v["nome"]: k for k, v in DB_LOCAL.items()}
    selecionados = st.multiselect(
        "Compostos no mesmo local",
        options=list(opcoes.keys()),
        default=["Etanol", "Ácido Sulfúrico"],
    )

    INCOMPAT = [
        ("h2so4","ammonia","CRÍTICO","Reação violenta — sulfato de amônio + calor intenso"),
        ("h2so4","acetone","ALTO","Reação exotérmica — risco de ignição"),
        ("h2so4","ethanol","ALTO","Reação exotérmica — risco de ignição e formação de éter"),
        ("h2so4","methane","ALTO","Ácido + gás inflamável pressurizado — risco de explosão"),
        ("ammonia","toluene","MÉDIO","Vapores inflamáveis + gás tóxico em espaço confinado"),
        ("acetone","toluene","BAIXO","Vapores inflamáveis combinados elevam o risco de incêndio"),
        ("ethanol","ammonia","MÉDIO","Combinação inflamável — vapores perigosos em espaço fechado"),
    ]
    COR_RISCO = {"CRÍTICO":"🔴","ALTO":"🟠","MÉDIO":"🟡","BAIXO":"🔵"}

    if st.button("Verificar incompatibilidades", type="primary"):
        keys = [opcoes[s] for s in selecionados if s in opcoes]
        encontrados = [(a, b, r, d) for a, b, r, d in INCOMPAT
                       if a in keys and b in keys]
        if not encontrados:
            st.success("Nenhuma incompatibilidade crítica detectada entre os compostos selecionados.")
        else:
            st.error(f"{len(encontrados)} incompatibilidade(s) detectada(s):")
            for a, b, risco, desc in encontrados:
                na = DB_LOCAL[a]["nome"]
                nb = DB_LOCAL[b]["nome"]
                st.markdown(f"""
                <div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;
                            padding:0.75rem 1rem;margin:0.4rem 0">
                  <b>{COR_RISCO[risco]} {risco}</b> — {na} + {nb}<br>
                  <span style="font-size:0.9rem;color:#6B7280">{desc}</span>
                </div>""", unsafe_allow_html=True)

        # Matriz de compatibilidade
        if len(keys) >= 2:
            st.markdown("#### Matriz de compatibilidade")
            nomes = [DB_LOCAL[k]["nome"] for k in keys]
            header = [""] + nomes
            linhas = [header]
            for ka in keys:
                linha = [DB_LOCAL[ka]["nome"]]
                for kb in keys:
                    if ka == kb:
                        linha.append("—")
                    else:
                        par = next((r for a,b,r,_ in INCOMPAT
                                    if (a==ka and b==kb) or (a==kb and b==ka)), None)
                        linha.append(f"{COR_RISCO.get(par,'✅')} {par or 'OK'}")
                linhas.append(linha)
            df_data = {linhas[0][i]: [linhas[r][i] for r in range(1, len(linhas))]
                       for i in range(len(linhas[0]))}
            import pandas as pd
            st.dataframe(pd.DataFrame(df_data).set_index(""), use_container_width=True)

# ════════════════════════════════════════════════
#  ABA 3 — ZABETAKIS
# ════════════════════════════════════════════════
with tab_zabetakis:
    st.markdown("#### Diagrama de Zabetakis — zonas de explosividade")
    st.caption("Limites de explosividade (LIE e LSE) e zona de risco para misturas combustível/ar.")

    import pandas as pd
    import numpy as np

    opcoes_zab = {v["nome"]: k for k, v in DB_LOCAL.items() if v.get("lie")}
    opcoes_zab["Personalizado"] = "__custom__"

    col_z1, col_z2 = st.columns([1, 2])
    with col_z1:
        comp_zab = st.selectbox("Composto", list(opcoes_zab.keys()))
        if comp_zab == "Personalizado":
            lie_v = st.number_input("LIE (%)", value=2.0, min_value=0.1, max_value=20.0, step=0.1)
            lse_v = st.number_input("LSE (%)", value=10.0, min_value=1.0, max_value=75.0, step=0.1)
        else:
            key_zab = opcoes_zab[comp_zab]
            lie_v = DB_LOCAL[key_zab]["lie"]
            lse_v = DB_LOCAL[key_zab]["lse"]
            st.metric("LIE", f"{lie_v} %")
            st.metric("LSE", f"{lse_v} %")

        conc_atual = st.slider(
            "Concentração atual (%)", 0.0, max(lse_v * 1.5, 20.0),
            value=0.0, step=0.1, format="%.1f%%"
        )

        if conc_atual < lie_v:
            st.success("Zona segura — abaixo do LIE")
        elif conc_atual <= lse_v:
            st.error("ZONA EXPLOSIVA — entre LIE e LSE!")
        else:
            st.info("Acima do LSE — muito rico, sem O₂ suficiente")

    with col_z2:
        # Gráfico Zabetakis com Streamlit/matplotlib
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches

            fig, ax = plt.subplots(figsize=(6, 4))
            fig.patch.set_facecolor("#F8FAFC")
            ax.set_facecolor("#F8FAFC")

            max_c = max(lse_v * 1.4, conc_atual * 1.2, 20.0)

            # Zonas coloridas
            ax.axvspan(0, lie_v, alpha=0.15, color="#22C55E", label="Seguro")
            ax.axvspan(lie_v, lse_v, alpha=0.3, color="#EF4444", label="Explosivo")
            ax.axvspan(lse_v, max_c, alpha=0.15, color="#3B82F6", label="Rico (sem O₂)")

            # Linhas de limite
            ax.axvline(lie_v, color="#EF4444", linestyle="--", linewidth=1.5, alpha=0.8)
            ax.axvline(lse_v, color="#3B82F6", linestyle="--", linewidth=1.5, alpha=0.8)

            # Anotações
            ax.text(lie_v, ax.get_ylim()[1]*0.95 if ax.get_ylim()[1] else 0.95,
                    f"LIE\n{lie_v}%", ha="center", fontsize=8,
                    color="#DC2626", fontweight="bold", va="top")
            ax.text(lse_v, ax.get_ylim()[1]*0.95 if ax.get_ylim()[1] else 0.95,
                    f"LSE\n{lse_v}%", ha="center", fontsize=8,
                    color="#1D4ED8", fontweight="bold", va="top")

            # Concentração atual
            if conc_atual > 0:
                ax.axvline(conc_atual, color="#F59E0B", linewidth=2.5)
                ax.text(conc_atual, 0.5, f"Atual\n{conc_atual:.1f}%",
                        ha="center", fontsize=8, color="#92400E", fontweight="bold",
                        transform=ax.get_xaxis_transform())

            # Rótulos de zona
            ax.text(lie_v/2, 0.5, "Seguro", ha="center", fontsize=9,
                    color="#166534", transform=ax.get_xaxis_transform(), alpha=0.7)
            ax.text((lie_v+lse_v)/2, 0.5, "EXPLOSIVO", ha="center", fontsize=9,
                    color="#991B1B", fontweight="bold",
                    transform=ax.get_xaxis_transform(), alpha=0.8)
            ax.text((lse_v+max_c)/2, 0.5, "Rico", ha="center", fontsize=9,
                    color="#1E40AF", transform=ax.get_xaxis_transform(), alpha=0.7)

            ax.set_xlabel("Concentração do combustível no ar (%)", fontsize=9)
            ax.set_xlim(0, max_c)
            ax.set_ylim(0, 1)
            ax.set_yticks([])
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_visible(False)
            ax.legend(loc="upper right", fontsize=8)
            ax.set_title(f"Diagrama de Zabetakis — {comp_zab}", fontsize=10, pad=8)
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        except Exception as e:
            st.info(f"Instale matplotlib para ver o diagrama: pip install matplotlib\n({e})")

    # Tabela resumo
    st.markdown("#### Limites de explosividade — compostos comuns")
    dados_zab = [
        {"Composto": "Hidrogênio H₂", "LIE (%)": 4.0, "LSE (%)": 75.0, "Pt. Fulgor": "-253 °C", "Risco": "CRÍTICO"},
        {"Composto": "Metano CH₄",    "LIE (%)": 5.0, "LSE (%)": 15.0, "Pt. Fulgor": "-188 °C", "Risco": "ALTO"},
        {"Composto": "Acetona",        "LIE (%)": 2.5, "LSE (%)": 12.8, "Pt. Fulgor": "-18 °C",  "Risco": "ALTO"},
        {"Composto": "Tolueno",        "LIE (%)": 1.1, "LSE (%)": 7.1,  "Pt. Fulgor": "4 °C",    "Risco": "ALTO"},
        {"Composto": "Etanol",         "LIE (%)": 3.3, "LSE (%)": 19.0, "Pt. Fulgor": "13 °C",   "Risco": "MÉDIO"},
        {"Composto": "Amônia",         "LIE (%)": 15.0,"LSE (%)": 28.0, "Pt. Fulgor": "11 °C",   "Risco": "MÉDIO"},
    ]
    st.dataframe(pd.DataFrame(dados_zab), use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════
#  ABA 4 — CONFORMIDADE
# ════════════════════════════════════════════════
with tab_conformidade:
    st.markdown("#### Painel de conformidade regulatória — Brasil")

    normas = [
        ("✅", "ABNT NBR 14725-1 a 4", "FISPQ / SDS — classificação e ficha de segurança", "Vigente"),
        ("✅", "NR-26 (MTE)", "Sinalização de segurança no trabalho — pictogramas GHS", "Vigente"),
        ("✅", "GHS Rev.9 (ONU)", "Sistema Globalmente Harmonizado — adotado via NR-26", "Vigente"),
        ("⚠️", "ANVISA RDC 222/2018", "Resíduos de serviços de saúde — revisão prevista Q2/2026", "Atenção"),
        ("✅", "ABNT NBR 10004:2004", "Classificação de resíduos sólidos perigosos", "Vigente"),
        ("✅", "ABNT NBR 7500", "Identificação para transporte de produtos perigosos", "Vigente"),
        ("✅", "CONAMA 358/2005", "Resíduos de serviços de saúde", "Vigente"),
    ]
    import pandas as pd
    df_normas = pd.DataFrame(normas, columns=["Status","Norma","Descrição","Situação"])
    st.dataframe(df_normas, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("#### Categorias de perigo GHS — referência rápida")
    ghs_cats = [
        ("GHS01","Explosivos","H200–H205"),
        ("GHS02","Inflamáveis (gases, líq., sólidos)","H220–H228"),
        ("GHS03","Oxidantes / Comburentes","H270–H272"),
        ("GHS04","Gases sob pressão","H280–H281"),
        ("GHS05","Corrosivos","H290, H314, H318"),
        ("GHS06","Tóxicos agudos (caveira)","H300–H310–H330"),
        ("GHS07","Irritantes / Nocivos","H302–H312–H332, H315–H319"),
        ("GHS08","Risco à saúde crônico","H340–H350–H360–H370–H372"),
        ("GHS09","Perigo ambiental aquático","H400–H410–H411"),
    ]
    df_ghs = pd.DataFrame(ghs_cats, columns=["Pictograma","Classe de Perigo","Frases H"])
    st.dataframe(df_ghs, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("#### Gerar relatório de conformidade completo")
    normas_check = st.multiselect("Incluir no relatório", ["NR-26","ABNT NBR 14725","GHS Rev.9",
        "ANVISA RDC 222","CONAMA 358","ABNT NBR 10004"],
        default=["NR-26","ABNT NBR 14725","GHS Rev.9"])
    if st.button("Gerar relatório de conformidade"):
        st.info("Para um relatório de conformidade detalhado e personalizado para sua planta, "
                "clique em 'Consulta e SDS', consulte o composto desejado e gere a FISPQ completa.")
