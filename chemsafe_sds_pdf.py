"""
chemsafe_sds_pdf.py
===================
Gerador de Ficha de Informações de Segurança de Produtos Químicos (FISPQ/SDS)
conforme ABNT NBR 14725-4:2014 e GHS Rev.9.

Estrutura: 16 seções obrigatórias
Formatação: cabeçalho com faixa colorida, rodapé com paginação,
            tabelas, pictogramas textuais e sumário de conformidade.

Uso:
    from chemsafe_sds_pdf import gerar_sds_pdf
    from chemsafe_api import ChemSafeAPI

    api  = ChemSafeAPI()
    dados = api.buscar_composto("ethanol")
    gerar_sds_pdf(dados, "SDS_Etanol.pdf")

Ou direto, com dados manuais:
    gerar_sds_pdf(dados_dict, "saida.pdf")

Dependências:
    pip install reportlab
"""

from reportlab.lib.pagesizes    import A4
from reportlab.lib.units        import mm, cm
from reportlab.lib              import colors
from reportlab.lib.styles       import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums        import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus         import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.pdfgen           import canvas as rl_canvas
from reportlab.platypus.flowables import Flowable
import datetime
import os


# ─────────────────────────────────────────────
#  Paleta de cores (conformidade visual GHS/ABNT)
# ─────────────────────────────────────────────

COR_VERMELHO     = colors.HexColor("#C0392B")   # cabeçalho seção perigo
COR_LARANJA      = colors.HexColor("#E67E22")   # alertas
COR_AMARELO      = colors.HexColor("#F39C12")   # avisos
COR_AZUL_ESCURO  = colors.HexColor("#1A3A5C")   # cabeçalho principal
COR_AZUL_MEDIO   = colors.HexColor("#2980B9")   # subseções
COR_CINZA_ESCURO = colors.HexColor("#2C3E50")   # texto principal
COR_CINZA_CLARO  = colors.HexColor("#ECF0F1")   # fundo alternado de tabela
COR_BRANCO       = colors.white
COR_PRETO        = colors.black
COR_BORDA        = colors.HexColor("#BDC3C7")   # bordas de tabela
COR_VERDE        = colors.HexColor("#27AE60")   # status OK
COR_CABECALHO_TAB= colors.HexColor("#34495E")   # cabeçalho de tabela


# ─────────────────────────────────────────────
#  Dimensões da página
# ─────────────────────────────────────────────

LARGURA, ALTURA = A4
MARGEM_L = 20 * mm
MARGEM_R = 20 * mm
MARGEM_T = 28 * mm
MARGEM_B = 25 * mm

LARGURA_UTIL = LARGURA - MARGEM_L - MARGEM_R


# ─────────────────────────────────────────────
#  Estilos tipográficos
# ─────────────────────────────────────────────

def _criar_estilos():
    base = getSampleStyleSheet()

    estilos = {}

    estilos["titulo_doc"] = ParagraphStyle(
        "titulo_doc", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=13,
        textColor=COR_BRANCO, alignment=TA_CENTER,
        spaceAfter=2, leading=16,
    )
    estilos["subtitulo_doc"] = ParagraphStyle(
        "subtitulo_doc", parent=base["Normal"],
        fontName="Helvetica", fontSize=9,
        textColor=COR_BRANCO, alignment=TA_CENTER,
        spaceAfter=0,
    )
    estilos["nome_produto"] = ParagraphStyle(
        "nome_produto", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=16,
        textColor=COR_BRANCO, alignment=TA_CENTER,
        spaceBefore=2, spaceAfter=2,
    )
    estilos["secao_titulo"] = ParagraphStyle(
        "secao_titulo", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=10,
        textColor=COR_BRANCO, alignment=TA_LEFT,
        spaceBefore=0, spaceAfter=0, leading=14,
        leftIndent=4,
    )
    estilos["secao_perigo"] = ParagraphStyle(
        "secao_perigo", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=10,
        textColor=COR_BRANCO, alignment=TA_LEFT,
        spaceBefore=0, spaceAfter=0, leading=14,
        leftIndent=4,
    )
    estilos["corpo"] = ParagraphStyle(
        "corpo", parent=base["Normal"],
        fontName="Helvetica", fontSize=9,
        textColor=COR_CINZA_ESCURO, alignment=TA_JUSTIFY,
        spaceBefore=2, spaceAfter=3, leading=13,
    )
    estilos["corpo_bold"] = ParagraphStyle(
        "corpo_bold", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=9,
        textColor=COR_CINZA_ESCURO, alignment=TA_LEFT,
        spaceBefore=2, spaceAfter=2, leading=13,
    )
    estilos["item"] = ParagraphStyle(
        "item", parent=base["Normal"],
        fontName="Helvetica", fontSize=9,
        textColor=COR_CINZA_ESCURO, alignment=TA_LEFT,
        spaceBefore=1, spaceAfter=1, leading=13,
        leftIndent=12, firstLineIndent=-8,
        bulletText=None,
    )
    estilos["aviso"] = ParagraphStyle(
        "aviso", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=9,
        textColor=COR_VERMELHO, alignment=TA_LEFT,
        spaceBefore=3, spaceAfter=3, leading=13,
    )
    estilos["rodape"] = ParagraphStyle(
        "rodape", parent=base["Normal"],
        fontName="Helvetica", fontSize=7,
        textColor=colors.HexColor("#7F8C8D"), alignment=TA_CENTER,
    )
    estilos["tab_header"] = ParagraphStyle(
        "tab_header", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=8,
        textColor=COR_BRANCO, alignment=TA_CENTER,
    )
    estilos["tab_cell"] = ParagraphStyle(
        "tab_cell", parent=base["Normal"],
        fontName="Helvetica", fontSize=8,
        textColor=COR_CINZA_ESCURO, alignment=TA_LEFT,
    )
    estilos["conformidade_ok"] = ParagraphStyle(
        "conformidade_ok", parent=base["Normal"],
        fontName="Helvetica", fontSize=8,
        textColor=COR_VERDE,
    )

    return estilos


# ─────────────────────────────────────────────
#  Flowables customizados
# ─────────────────────────────────────────────

class CabecalhoSecao(Flowable):
    """Faixa colorida com número e título da seção."""

    def __init__(self, numero: str, titulo: str, cor=None, largura=None):
        super().__init__()
        self.numero  = numero
        self.titulo  = titulo
        self.cor     = cor or COR_AZUL_ESCURO
        self.largura = largura or LARGURA_UTIL
        self.altura  = 14

    def wrap(self, availW, availH):
        return self.largura, self.altura + 4

    def draw(self):
        c = self.canv
        # Fundo colorido
        c.setFillColor(self.cor)
        c.roundRect(0, 0, self.largura, self.altura, 2, fill=1, stroke=0)
        # Texto
        c.setFillColor(COR_BRANCO)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(5, 3, f"SEÇÃO {self.numero}  —  {self.titulo.upper()}")


class DivisorFino(Flowable):
    """Linha divisória fina."""

    def __init__(self, cor=None, largura=None):
        super().__init__()
        self.cor     = cor or COR_BORDA
        self.largura = largura or LARGURA_UTIL

    def wrap(self, availW, availH):
        return self.largura, 4

    def draw(self):
        c = self.canv
        c.setStrokeColor(self.cor)
        c.setLineWidth(0.3)
        c.line(0, 2, self.largura, 2)


class CaixaPerigo(Flowable):
    """Caixa de alerta de perigo com borda vermelha."""

    def __init__(self, texto: str, largura=None):
        super().__init__()
        self.texto   = texto
        self.largura = largura or LARGURA_UTIL
        self.altura  = 28

    def wrap(self, availW, availH):
        return self.largura, self.altura

    def draw(self):
        c = self.canv
        c.setStrokeColor(COR_VERMELHO)
        c.setFillColor(colors.HexColor("#FDEDEC"))
        c.setLineWidth(1.2)
        c.roundRect(0, 0, self.largura, self.altura, 3, fill=1, stroke=1)
        c.setFillColor(COR_VERMELHO)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(8, self.altura - 14, "PALAVRA DE ADVERTENCIA:")
        c.setFont("Helvetica", 8)
        c.drawString(8, 7, self.texto[:140])


# ─────────────────────────────────────────────
#  Cabeçalho e rodapé da página (canvas callback)
# ─────────────────────────────────────────────

def _cabecalho_rodape(canvas_obj, doc, dados: dict, total_pages_ref: list):
    nome_produto = dados.get("consulta", "Composto químico").title()
    cas          = dados.get("cas", "—")
    formula      = dados.get("formula_molecular", "—")
    data_hoje    = datetime.date.today().strftime("%d/%m/%Y")
    pagina       = canvas_obj.getPageNumber()

    canvas_obj.saveState()

    # ── Cabeçalho ──
    canvas_obj.setFillColor(COR_AZUL_ESCURO)
    canvas_obj.rect(MARGEM_L, ALTURA - 22*mm, LARGURA_UTIL, 16*mm, fill=1, stroke=0)

    canvas_obj.setFillColor(COR_BRANCO)
    canvas_obj.setFont("Helvetica-Bold", 11)
    canvas_obj.drawString(MARGEM_L + 5*mm, ALTURA - 12*mm, nome_produto.upper())

    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.drawString(MARGEM_L + 5*mm, ALTURA - 17*mm,
        f"Fórmula: {formula}   |   CAS: {cas}   |   FISPQ — ABNT NBR 14725-4:2014 / GHS Rev.9")

    canvas_obj.setFont("Helvetica-Bold", 8)
    canvas_obj.drawRightString(LARGURA - MARGEM_R, ALTURA - 12*mm,
        "FICHA DE INFORMAÇÕES DE SEGURANÇA")
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.drawRightString(LARGURA - MARGEM_R, ALTURA - 17*mm,
        f"Revisão: 1.0   |   {data_hoje}")

    # Linha abaixo do cabeçalho
    canvas_obj.setStrokeColor(COR_AZUL_MEDIO)
    canvas_obj.setLineWidth(1.5)
    canvas_obj.line(MARGEM_L, ALTURA - 23*mm, LARGURA - MARGEM_R, ALTURA - 23*mm)

    # ── Rodapé ──
    canvas_obj.setStrokeColor(COR_BORDA)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(MARGEM_L, 18*mm, LARGURA - MARGEM_R, 18*mm)

    canvas_obj.setFillColor(colors.HexColor("#7F8C8D"))
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.drawString(MARGEM_L, 14*mm,
        "Este documento é gerado automaticamente pelo ChemSafe AI. "
        "Verificar com fontes regulatórias antes do uso operacional.")
    canvas_obj.drawCentredString(LARGURA / 2, 10*mm,
        f"Página {pagina}  |  {nome_produto}  |  CAS {cas}")
    canvas_obj.drawRightString(LARGURA - MARGEM_R, 10*mm,
        "CONFIDENCIAL — USO INTERNO")

    canvas_obj.restoreState()


# ─────────────────────────────────────────────
#  Helpers para construção das seções
# ─────────────────────────────────────────────

def _tabela(linhas: list, col_larguras: list, estilos: dict,
            tem_cabecalho: bool = True) -> Table:
    """Gera uma tabela formatada no padrão ChemSafe."""
    tab_data = []
    for i, linha in enumerate(linhas):
        tab_data.append([
            Paragraph(str(c), estilos["tab_header"] if (i == 0 and tem_cabecalho)
                      else estilos["tab_cell"])
            for c in linha
        ])

    estilo = TableStyle([
        # Cabeçalho
        ("BACKGROUND",  (0, 0), (-1, 0), COR_CABECALHO_TAB),
        ("TEXTCOLOR",   (0, 0), (-1, 0), COR_BRANCO),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 8),
        ("ALIGN",       (0, 0), (-1, 0), "CENTER"),
        ("BOTTOMPADDING",(0, 0), (-1, 0), 5),
        ("TOPPADDING",  (0, 0), (-1, 0), 5),
        # Corpo
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 1), (-1, -1), 8),
        ("ALIGN",       (0, 1), (-1, -1), "LEFT"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 1), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",(0, 0), (-1, -1), 5),
        # Alternância de cor
        *[("BACKGROUND", (0, i), (-1, i), COR_CINZA_CLARO)
          for i in range(2, len(linhas), 2)],
        # Grade
        ("GRID",        (0, 0), (-1, -1), 0.3, COR_BORDA),
        ("BOX",         (0, 0), (-1, -1), 0.8, COR_BORDA),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COR_BRANCO, COR_CINZA_CLARO]),
    ])

    t = Table(tab_data, colWidths=col_larguras, repeatRows=1)
    t.setStyle(estilo)
    return t


def _p(texto: str, estilo) -> Paragraph:
    """Cria Paragraph escapando caracteres especiais do ReportLab."""
    # Substitui subscripts unicode por tags XML do ReportLab
    subs = {"₂": "<sub>2</sub>", "₃": "<sub>3</sub>", "₄": "<sub>4</sub>",
            "₅": "<sub>5</sub>", "₆": "<sub>6</sub>", "₇": "<sub>7</sub>",
            "₈": "<sub>8</sub>", "₉": "<sub>9</sub>", "₁": "<sub>1</sub>",
            "₀": "<sub>0</sub>",
            "°": "&#176;", "³": "<super>3</super>",
            "·": "&#183;", "≥": "&#8805;", "≤": "&#8804;",
            "–": "&#8211;", "—": "&#8212;",
            "&": "&amp;"}
    for orig, rep in subs.items():
        texto = texto.replace(orig, rep)
    return Paragraph(texto, estilo)


# ─────────────────────────────────────────────
#  16 Seções da FISPQ / SDS
# ─────────────────────────────────────────────

H_CODES = {
    "H200": "Explosivo instável",
    "H220": "Gás extremamente inflamável",
    "H221": "Gás inflamável",
    "H224": "Líquido e vapor extremamente inflamáveis",
    "H225": "Líquido e vapor muito inflamáveis",
    "H226": "Líquido e vapor inflamáveis",
    "H228": "Sólido inflamável",
    "H280": "Contém gás sob pressão",
    "H290": "Pode ser corrosivo para metais",
    "H300": "Fatal por ingestão",
    "H301": "Tóxico por ingestão",
    "H302": "Nocivo por ingestão",
    "H304": "Pode ser fatal por ingestão — penetração nas vias respiratórias",
    "H310": "Fatal em contato com a pele",
    "H311": "Tóxico em contato com a pele",
    "H312": "Nocivo em contato com a pele",
    "H314": "Provoca queimaduras graves na pele e nos olhos",
    "H315": "Provoca irritação cutânea",
    "H317": "Pode provocar reação alérgica cutânea",
    "H318": "Provoca lesões oculares graves",
    "H319": "Provoca irritação ocular grave",
    "H330": "Fatal por inalação",
    "H331": "Tóxico por inalação",
    "H332": "Nocivo por inalação",
    "H335": "Pode irritar as vias respiratórias",
    "H336": "Pode provocar sonolência ou vertigens",
    "H340": "Pode provocar alterações genéticas",
    "H350": "Pode provocar cancro",
    "H360": "Pode prejudicar a fertilidade ou o nascituro",
    "H361": "Suspeito de prejudicar a fertilidade ou o nascituro",
    "H370": "Provoca danos nos órgãos",
    "H372": "Provoca danos nos órgãos por exposição prolongada",
    "H400": "Muito tóxico para os organismos aquáticos",
    "H410": "Muito tóxico para os organismos aquáticos — efeitos prolongados",
}

P_CODES = {
    "P201": "Obter instruções específicas antes da utilização.",
    "P210": "Manter afastado de fontes de calor, faíscas, chamas abertas. Não fumar.",
    "P233": "Manter o recipiente bem fechado.",
    "P240": "Ligar à terra/equipar com ligação de potencial o recipiente.",
    "P241": "Utilizar equipamento elétrico/de ventilação/de iluminação antideflagrante.",
    "P242": "Utilizar apenas ferramentas sem faíscas.",
    "P243": "Tomar medidas preventivas contra descargas estáticas.",
    "P260": "Não respirar os vapores/névoas.",
    "P264": "Lavar as mãos cuidadosamente após manuseamento.",
    "P270": "Não comer, beber ou fumar durante a utilização.",
    "P271": "Utilizar apenas ao ar livre ou em local bem ventilado.",
    "P272": "A roupa de trabalho contaminada não deve sair do local de trabalho.",
    "P273": "Evitar a libertação para o ambiente.",
    "P280": "Usar luvas/roupas de proteção/proteção ocular/proteção facial.",
    "P301+P330+P331": "SE INGERIDO: enxaguar a boca. NAO provocar o vómito.",
    "P303+P361+P353": "SE SOBRE A PELE (ou o cabelo): retirar imediatamente toda a roupa contaminada.",
    "P304+P340": "SE INALADO: retirar a pessoa para o ar fresco e mante-la em repouso.",
    "P305+P351+P338": "SE ENTRAR EM CONTACTO COM OS OLHOS: enxaguar cuidadosamente com água durante vários minutos.",
    "P370+P378": "Em caso de incêndio: utilizar areia seca / dióxido de carbono / espuma para extinção.",
    "P403+P235": "Armazenar em local bem ventilado. Manter em ambiente fresco.",
    "P405": "Guardar fechado à chave.",
    "P501": "Eliminar o conteúdo/recipiente de acordo com os regulamentos locais.",
}

GHS_PICS = {
    "GHS01": "[EXPLOSIVO]",
    "GHS02": "[INFLAMÁVEL]",
    "GHS03": "[OXIDANTE]",
    "GHS04": "[GÁS PRESSÃO]",
    "GHS05": "[CORROSIVO]",
    "GHS06": "[TÓXICO]",
    "GHS07": "[IRRITANTE]",
    "GHS08": "[RISCO SAÚDE]",
    "GHS09": "[PERIGO AMBIENTAL]",
}


def _secao_1(dados, e) -> list:
    """Identificação do produto e da empresa."""
    props = dados.get("propriedades", {})
    sin   = dados.get("sinonimos", [])
    return [
        CabecalhoSecao("1", "Identificação do Produto e da Empresa"),
        Spacer(1, 3*mm),
        _tabela([
            ["Campo", "Informação"],
            ["Nome do produto",        dados.get("consulta", "—").title()],
            ["Nome IUPAC",             props.get("nome_iupac", "—")[:60]],
            ["Fórmula molecular",      dados.get("formula_molecular", "—")],
            ["Número CAS",             dados.get("cas", "—")],
            ["CID PubChem",            str(dados.get("cid_pubchem", "—"))],
            ["Peso molecular",         f"{dados.get('peso_molecular', '—')} g/mol"],
            ["Sinônimos (principais)", ", ".join(sin[:4]) if sin else "—"],
            ["Uso recomendado",        "Uso industrial e laboratorial — engenharia química"],
            ["Uso restrito",           "Conforme legislação aplicável (ANVISA, IBAMA)"],
            ["Fornecedor / contato",   "Preencher conforme fornecedor específico"],
            ["Telefone emergência",    "0800-722-7172 (CIQUIME Brasil) / 193 (Bombeiros)"],
        ],
        [55*mm, LARGURA_UTIL - 55*mm], e),
        Spacer(1, 3*mm),
    ]


def _secao_2(dados, e) -> list:
    """Identificação dos perigos."""
    ghs    = dados.get("ghs", {})
    nfpa   = dados.get("nfpa_estimado", {})
    frases_h = ghs.get("frases_h", [])
    pics     = ghs.get("pictogramas", [])
    sinal    = (ghs.get("palavras_sinal") or ["—"])[0]

    # Determina cor da palavra-sinal
    cor_sinal = COR_VERMELHO if "perigo" in sinal.lower() else COR_LARANJA

    conteudo = [
        CabecalhoSecao("2", "Identificação dos Perigos", cor=COR_VERMELHO),
        Spacer(1, 3*mm),
        CaixaPerigo(f"{sinal.upper()}  —  Ver frases H abaixo e EPI recomendado na Seção 8."),
        Spacer(1, 3*mm),
    ]

    # Pictogramas GHS
    if pics:
        pic_texto = "  ".join([GHS_PICS.get(p, f"[{p}]") for p in pics])
        conteudo += [
            _p(f"<b>Pictogramas GHS:</b>  {pic_texto}", e["corpo"]),
            Spacer(1, 2*mm),
        ]

    # Tabela de frases H
    if frases_h:
        rows = [["Código H", "Classe de perigo", "Descrição"]]
        for fh in frases_h[:10]:
            cod  = fh.strip()[:4] if len(fh) >= 4 else fh
            desc = H_CODES.get(cod, fh)
            rows.append([cod, _classificar_h(cod), desc])
        conteudo += [
            _tabela(rows, [18*mm, 50*mm, LARGURA_UTIL - 68*mm], e),
            Spacer(1, 3*mm),
        ]
    else:
        conteudo.append(_p("Frases H não disponíveis — consultar SDS do fornecedor.", e["corpo"]))

    # NFPA resumido
    conteudo += [
        _p(f"<b>NFPA 704 (estimado):</b>  "
           f"Saúde: {nfpa.get('H','—')} | "
           f"Inflamabilidade: {nfpa.get('F','—')} | "
           f"Reatividade: {nfpa.get('R','—')} | "
           f"Especial: {nfpa.get('S','—') or '—'}", e["corpo"]),
        Spacer(1, 2*mm),
        _p("<i>Nota: classificação NFPA estimada heuristicamente pelo ChemSafe AI. "
           "Validar contra SDS oficial do fornecedor para uso regulatório.</i>", e["corpo"]),
        Spacer(1, 3*mm),
    ]
    return conteudo


def _classificar_h(cod: str) -> str:
    prefixo = cod[:3] if len(cod) >= 3 else cod
    mapa = {
        "H2": "Físico",
        "H3": "Saúde",
        "H4": "Ambiental",
    }
    for k, v in mapa.items():
        if cod.startswith(k):
            return v
    return "—"


def _secao_3(dados, e) -> list:
    """Composição e informação sobre os componentes."""
    props = dados.get("propriedades", {})
    return [
        CabecalhoSecao("3", "Composição e Informação sobre os Componentes"),
        Spacer(1, 3*mm),
        _tabela([
            ["Componente", "Fórmula", "CAS", "Concentração (%)", "Peso Mol. (g/mol)"],
            [dados.get("consulta","—").title(),
             dados.get("formula_molecular","—"),
             dados.get("cas","—"),
             "> 99 (substância pura)",
             str(dados.get("peso_molecular","—"))],
        ],
        [50*mm, 28*mm, 28*mm, 42*mm, LARGURA_UTIL - 148*mm], e),
        Spacer(1, 2*mm),
        _p("SMILES: " + props.get("smiles","—"), e["corpo"]),
        _p("InChIKey: " + props.get("inchikey","—"), e["corpo"]),
        Spacer(1, 3*mm),
    ]


def _secao_4(e) -> list:
    """Medidas de primeiros socorros."""
    return [
        CabecalhoSecao("4", "Medidas de Primeiros Socorros"),
        Spacer(1, 3*mm),
        _tabela([
            ["Via de exposição", "Procedimento imediato"],
            ["Inalação",
             "Remover a vítima para local arejado. Se respiração difícil, administrar "
             "oxigênio. Se parou de respirar, iniciar RCP. Chamar médico."],
            ["Contato com a pele",
             "Lavar com água corrente abundante por no mínimo 15 minutos. "
             "Remover roupas contaminadas. Procurar atendimento médico se irritação persistir."],
            ["Contato com os olhos",
             "Lavar com água corrente por no mínimo 15 minutos com pálpebras abertas. "
             "Não usar colírios. Procurar oftalmologista imediatamente."],
            ["Ingestão",
             "Não provocar vômito. Lavar a boca com água. Dar água para beber "
             "(se consciente). Chamar 192 (SAMU) ou médico imediatamente."],
        ],
        [45*mm, LARGURA_UTIL - 45*mm], e),
        Spacer(1, 2*mm),
        _p("<b>Telefone médico de emergência:</b>  0800-722-7172 (CIQUIME) | 192 (SAMU) | 193 (Bombeiros)", e["aviso"]),
        Spacer(1, 3*mm),
    ]


def _secao_5(dados, e) -> list:
    """Medidas de combate a incêndio."""
    ex = dados.get("explosividade", {})
    lie = ex.get("lie_pct", "—")
    lse = ex.get("lse_pct", "—")
    flash = ex.get("ponto_fulgor", "—")
    nfpa  = dados.get("nfpa_estimado", {})
    inflamab = nfpa.get("F", 0)

    agentes = "Pó químico seco, CO2, espuma AFFF" if inflamab >= 2 \
              else "Água em névoa, CO2, pó químico"

    return [
        CabecalhoSecao("5", "Medidas de Combate a Incêndio"),
        Spacer(1, 3*mm),
        _tabela([
            ["Parâmetro", "Valor"],
            ["Ponto de fulgor",          str(flash)],
            ["LIE (Limite Inf. Explosividade)",  f"{lie} %"],
            ["LSE (Limite Sup. Explosividade)",  f"{lse} %"],
            ["Inflamabilidade NFPA",     f"{inflamab}/4"],
            ["Agentes extintores recomendados", agentes],
            ["Agentes extintores proibidos", "Jato direto de água (verificar reatividade)"],
            ["EPI bombeiros",
             "Roupa de proteção total, SCBA (aparelho de respiração autônomo)"],
        ],
        [70*mm, LARGURA_UTIL - 70*mm], e),
        Spacer(1, 2*mm),
        _p("<b>Atenção Zabetakis:</b> manter concentração ABAIXO do LIE em todo o ambiente. "
           "Em espaços confinados, usar detector de gases calibrado.", e["aviso"]),
        Spacer(1, 3*mm),
    ]


def _secao_6(e) -> list:
    """Medidas em caso de derramamento acidental."""
    return [
        CabecalhoSecao("6", "Medidas em Caso de Derramamento Acidental"),
        Spacer(1, 3*mm),
        _p("<b>Precauções pessoais:</b>  Evacuar a área. Eliminar fontes de ignição. "
           "Usar EPI completo (luvas, óculos, respirador). Garantir ventilação adequada.", e["corpo"]),
        Spacer(1, 2*mm),
        _p("<b>Precauções ambientais:</b>  Impedir a entrada em redes de esgoto, "
           "cursos d'água e solo. Notificar autoridades competentes (IBAMA/CETESB) "
           "se o derramamento for significativo.", e["corpo"]),
        Spacer(1, 2*mm),
        _p("<b>Métodos de limpeza:</b>  Absorver com material inerte (areia, vermiculita, "
           "terra diatomácea). Recolher em recipiente fechado rotulado. "
           "Descontaminar a área com solução adequada. "
           "Descartar conforme Seção 13.", e["corpo"]),
        Spacer(1, 3*mm),
    ]


def _secao_7(e) -> list:
    """Manuseamento e armazenamento."""
    return [
        CabecalhoSecao("7", "Manuseamento e Armazenamento"),
        Spacer(1, 3*mm),
        _tabela([
            ["Aspecto", "Orientação"],
            ["Manuseamento",
             "Usar em local ventilado. Evitar contato com pele e olhos. "
             "Não ingerir. Usar EPI (Seção 8). Eliminar fontes de ignição."],
            ["Armazenamento",
             "Local fresco, seco, ventilado, longe de fontes de calor e chamas. "
             "Recipientes bem fechados e aterrados (se inflamável)."],
            ["Temperatura de armazenamento", "Ambiente (15–30°C) salvo indicação contrária"],
            ["Incompatibilidades",
             "Verificar Seção 10. Separar de oxidantes, ácidos fortes, bases fortes."],
            ["Requisitos NR-26",
             "Rotulagem GHS obrigatória. Sinalização de área. "
             "FISPQ disponível no local de trabalho."],
        ],
        [55*mm, LARGURA_UTIL - 55*mm], e),
        Spacer(1, 3*mm),
    ]


def _secao_8(dados, e) -> list:
    """Controles de exposição e proteção individual."""
    props = dados.get("propriedades", {})
    return [
        CabecalhoSecao("8", "Controles de Exposição / Proteção Individual"),
        Spacer(1, 3*mm),
        _tabela([
            ["EPI", "Especificação mínima", "Norma"],
            ["Luvas",
             "Nitrila espessura >= 0,4 mm ou neoprene",
             "ABNT NBR 13392"],
            ["Óculos / protetor facial",
             "Óculos vedados + protetor facial se risco de respingo",
             "ABNT NBR 14725"],
            ["Respirador",
             "Semifacial com filtro para vapores orgânicos (P2/OV) "
             "ou SCBA se concentrações altas",
             "ABNT NBR 13697"],
            ["Jaleco / avental",
             "Material resistente ao produto (ver SDS fornecedor)",
             "ABNT NBR 13283"],
            ["Calçado",
             "Bota de segurança antiestática",
             "ABNT NBR 16243"],
        ],
        [35*mm, LARGURA_UTIL - 75*mm, 40*mm], e),
        Spacer(1, 2*mm),
        _p("<b>Limites de exposição ocupacional:</b>  Consultar NR-15 e ACGIH TLV-TWA/STEL "
           "para o composto específico. Utilizar medidores de concentração no ar em "
           "locais de uso intensivo.", e["corpo"]),
        Spacer(1, 3*mm),
    ]


def _secao_9(dados, e) -> list:
    """Propriedades físico-químicas."""
    props = dados.get("propriedades", {})
    nist  = dados.get("nist", {})
    ex    = dados.get("explosividade", {})

    linhas = [["Propriedade", "Valor", "Fonte"]]
    campos = [
        ("Fórmula molecular",     dados.get("formula_molecular","—"),   "PubChem"),
        ("Peso molecular",        f"{dados.get('peso_molecular','—')} g/mol", "PubChem"),
        ("Aparência",             "Ver SDS do fornecedor",               "—"),
        ("Odor",                  "Ver SDS do fornecedor",               "—"),
        ("Ponto de ebulição",     nist.get("ponto_ebulicao_C","—"),      "NIST"),
        ("Ponto de fusão",        nist.get("ponto_fusao_C","—"),         "NIST"),
        ("Ponto de fulgor",       ex.get("ponto_fulgor","—"),            "NIST"),
        ("LIE",                   f"{ex.get('lie_pct','—')} %",          "NIST"),
        ("LSE",                   f"{ex.get('lse_pct','—')} %",          "NIST"),
        ("Temperatura crítica",   nist.get("temp_critica_K","—"),        "NIST"),
        ("Pressão crítica",       nist.get("pressao_critica_MPa","—"),   "NIST"),
        ("Entalpia formação (Hf)",nist.get("delta_hf_kJ_mol","—"),       "NIST"),
        ("LogP (XLogP)",          str(props.get("xlogp","—")),           "PubChem"),
        ("TPSA",                  f"{props.get('tpsa','—')} A&#178;",    "PubChem"),
        ("Doadores H",            str(props.get("doadores_h","—")),      "PubChem"),
        ("Aceptores H",           str(props.get("aceptores_h","—")),     "PubChem"),
        ("Solubilidade em água",  "Ver SDS do fornecedor",               "—"),
    ]
    linhas.extend(campos)

    return [
        CabecalhoSecao("9", "Propriedades Físicas e Químicas"),
        Spacer(1, 3*mm),
        _tabela(linhas, [65*mm, LARGURA_UTIL - 100*mm, 35*mm], e),
        Spacer(1, 3*mm),
    ]


def _secao_10(e) -> list:
    """Estabilidade e reatividade."""
    return [
        CabecalhoSecao("10", "Estabilidade e Reatividade"),
        Spacer(1, 3*mm),
        _tabela([
            ["Aspecto", "Informação"],
            ["Estabilidade química",
             "Estável em condições normais de temperatura e pressão."],
            ["Possibilidade de reações perigosas",
             "Pode reagir com oxidantes fortes, ácidos concentrados ou bases fortes. "
             "Ver SDS do fornecedor para reagentes incompatíveis específicos."],
            ["Condições a evitar",
             "Calor excessivo, fontes de ignição, umidade (se reativo com água), "
             "radiação UV intensa."],
            ["Materiais incompatíveis",
             "Verificar com ChemSafe AI — módulo de incompatibilidades. "
             "Fonte: NFPA 49 e SDS do fornecedor."],
            ["Produtos de decomposição perigosos",
             "Depende do composto — CO, CO2, NOx, SOx, HCl podem ser gerados. "
             "Consultar seção de estabilidade na SDS do fornecedor."],
        ],
        [55*mm, LARGURA_UTIL - 55*mm], e),
        Spacer(1, 3*mm),
    ]


def _secao_11(e) -> list:
    """Informações toxicológicas."""
    return [
        CabecalhoSecao("11", "Informações Toxicológicas"),
        Spacer(1, 3*mm),
        _tabela([
            ["Parâmetro", "Valor / Observação"],
            ["DL50 oral (rato)",      "Consultar ECHA / PubChem Bioassay / fornecedor"],
            ["DL50 dérmica (rato)",   "Consultar ECHA / PubChem Bioassay / fornecedor"],
            ["CL50 inalação (rato)",  "Consultar ECHA / PubChem Bioassay / fornecedor"],
            ["Irritação cutânea",     "Ver frases H3xx na Seção 2"],
            ["Irritação ocular",      "Ver frases H3xx na Seção 2"],
            ["Sensibilização",        "Ver frases H3xx na Seção 2"],
            ["Mutagenicidade",        "Ver frases H340/H341 na Seção 2"],
            ["Carcinogenicidade",     "Ver frases H350/H351 — verificar IARC"],
            ["Toxicidade reprodutiva","Ver frases H360/H361 na Seção 2"],
            ["Toxicidade sistêmica",  "Ver frases H370/H372 na Seção 2"],
            ["Perigo por aspiração",  "Ver frase H304 na Seção 2"],
        ],
        [65*mm, LARGURA_UTIL - 65*mm], e),
        Spacer(1, 3*mm),
    ]


def _secao_12(e) -> list:
    """Informações ecológicas."""
    return [
        CabecalhoSecao("12", "Informações Ecológicas"),
        Spacer(1, 3*mm),
        _tabela([
            ["Parâmetro ecológico", "Valor / Observação"],
            ["Toxicidade aquática aguda",     "Ver frases H4xx na Seção 2. Consultar ECHA."],
            ["Toxicidade aquática crônica",   "Ver frases H4xx na Seção 2. Consultar ECHA."],
            ["Persistência/degradabilidade",  "Consultar ficha ECHA — DBO/DQO se disponível"],
            ["Potencial de bioacumulação",    f"LogP (XLogP) — ver Seção 9"],
            ["Mobilidade no solo",            "Depende da solubilidade e adsorção — Koc"],
            ["Outros efeitos adversos",       "Notificar derrames ao IBAMA e CETESB"],
        ],
        [65*mm, LARGURA_UTIL - 65*mm], e),
        Spacer(1, 3*mm),
    ]


def _secao_13(e) -> list:
    """Considerações sobre descarte."""
    return [
        CabecalhoSecao("13", "Consideracoes sobre Descarte"),
        Spacer(1, 3*mm),
        _p("<b>Resíduo do produto:</b>  Classificar conforme ABNT NBR 10004 (Classe I ou II). "
           "Encaminhar para empresa licenciada de tratamento de resíduos perigosos. "
           "Não descartar em esgoto, aterro comum ou solo.", e["corpo"]),
        Spacer(1, 2*mm),
        _p("<b>Embalagem contaminada:</b>  Seguir ABNT NBR 10004. Descontaminar a embalagem "
           "ou encaminhar para coleta específica conforme ANVISA RDC 222/2018.", e["corpo"]),
        Spacer(1, 2*mm),
        _p("<b>Código de resíduo (CONAMA 358):</b>  Verificar lista específica pelo CAS "
           f"{'{dados[cas]}'}. Licença IBAMA/CETESB obrigatória para geração acima "
           "dos limites regulatórios.", e["corpo"]),
        Spacer(1, 3*mm),
    ]


def _secao_14(e) -> list:
    """Informações sobre transporte."""
    return [
        CabecalhoSecao("14", "Informacoes sobre Transporte"),
        Spacer(1, 3*mm),
        _tabela([
            ["Modalidade", "Informação (verificar com ANTT/IMO/IATA)"],
            ["Transporte rodoviário (ANTT)", "Conforme Resolução ANTT 5.232/2016 (RTPP)"],
            ["Número ONU",    "Consultar lista ONU pelo CAS — exemplo: UN1170 (etanol)"],
            ["Designação ONU","Indicada na embalagem conforme ABNT NBR 7500"],
            ["Classe de risco","Consultar tabela ABNT NBR 7503 / GHS"],
            ["Grupo embalagem","I, II ou III conforme toxicidade e volatilidade"],
            ["Poluente marinho","Verificar MARPOL — ver coluna especial da lista ONU"],
            ["Transporte aéreo (IATA)","Ver IATA Dangerous Goods Regulations (DGR)"],
        ],
        [55*mm, LARGURA_UTIL - 55*mm], e),
        Spacer(1, 3*mm),
    ]


def _secao_15(e) -> list:
    """Informações sobre regulamentação."""
    return [
        CabecalhoSecao("15", "Informacoes sobre Regulamentacao"),
        Spacer(1, 3*mm),
        _tabela([
            ["Norma / Regulamento", "Âmbito", "Status"],
            ["ABNT NBR 14725-1 a 4", "Classificação e FISPQ (Brasil)", "Vigente"],
            ["NR-26 (MTE)",          "Sinalização de segurança no trabalho", "Vigente"],
            ["GHS Rev.9 (ONU)",      "Sistema Globalmente Harmonizado", "Adotado via NR-26"],
            ["ANVISA RDC 222/2018",  "Resíduos perigosos em serviços de saúde", "Vigente"],
            ["CONAMA 358/2005",      "Resíduos sólidos de serviços de saúde", "Vigente"],
            ["ABNT NBR 10004:2004",  "Classificação de resíduos sólidos", "Vigente"],
            ["ABNT NBR 7500",        "Transporte de produtos perigosos", "Vigente"],
            ["REACH (UE)",           "Registro europeu — se exportação", "Verificar"],
            ["OSHA 29 CFR 1910.1200","HazCom USA — se importação/exportação", "Verificar"],
        ],
        [65*mm, 55*mm, LARGURA_UTIL - 120*mm], e),
        Spacer(1, 3*mm),
    ]


def _secao_16(dados, e) -> list:
    """Outras informações."""
    fontes = dados.get("fontes", [])
    data   = datetime.date.today().strftime("%d/%m/%Y")
    return [
        CabecalhoSecao("16", "Outras Informacoes"),
        Spacer(1, 3*mm),
        _tabela([
            ["Item", "Informação"],
            ["Data de emissão",       data],
            ["Versão",                "1.0 (gerada automaticamente — ChemSafe AI)"],
            ["Fontes de dados",       ", ".join(fontes) if fontes else "PubChem, NIST WebBook"],
            ["Responsável técnico",   "Preencher com engenheiro responsável e CREA/CRQ"],
            ["Próxima revisão",       "A cada 5 anos ou quando houver alteração relevante"],
            ["Abreviações",
             "FISPQ: Ficha de Informações de Segurança de Produtos Químicos | "
             "GHS: Globally Harmonized System | NR: Norma Regulamentadora | "
             "EPI: Equipamento de Proteção Individual | "
             "LIE/LSE: Limite Inferior/Superior de Explosividade"],
            ["Aviso legal",
             "Esta FISPQ foi gerada automaticamente com base em dados de APIs "
             "públicas (PubChem, NIST). Deve ser revisada por profissional habilitado "
             "antes do uso regulatório ou operacional. "
             "O gerador ChemSafe AI não se responsabiliza por decisões baseadas "
             "exclusivamente neste documento."],
        ],
        [45*mm, LARGURA_UTIL - 45*mm], e),
        Spacer(1, 3*mm),
        DivisorFino(),
        Spacer(1, 2*mm),
        _p("Gerado por ChemSafe AI  |  ABNT NBR 14725-4:2014  |  GHS Rev.9  |  "
           f"PubChem CID: {dados.get('cid_pubchem','—')}  |  {data}", e["corpo"]),
    ]


# ─────────────────────────────────────────────
#  Função principal de geração do PDF
# ─────────────────────────────────────────────

def gerar_sds_pdf(dados: dict, caminho_saida: str) -> str:
    """
    Gera a SDS/FISPQ completa em PDF.

    Parâmetros:
        dados         : dict retornado por chemsafe_api.buscar_composto()
        caminho_saida : caminho do arquivo PDF de saída

    Retorna:
        caminho_saida (string)
    """
    print(f"\n[PDF] Iniciando geração da SDS para: {dados.get('consulta','—')}")

    estilos = _criar_estilos()

    # Template do documento
    doc = SimpleDocTemplate(
        caminho_saida,
        pagesize=A4,
        leftMargin=MARGEM_L,
        rightMargin=MARGEM_R,
        topMargin=MARGEM_T,
        bottomMargin=MARGEM_B,
        title=f"FISPQ — {dados.get('consulta','Composto').title()}",
        author="ChemSafe AI",
        subject="Ficha de Informações de Segurança — ABNT NBR 14725-4",
        creator="ChemSafe AI v2",
    )

    # Callback de página (cabeçalho + rodapé)
    total_pages_ref = [0]

    def on_page(canvas_obj, doc_obj):
        _cabecalho_rodape(canvas_obj, doc_obj, dados, total_pages_ref)

    # ── Capa ──
    story = []

    # Bloco de capa
    story.append(Spacer(1, 8*mm))

    capa_data = [
        [Paragraph(
            "FICHA DE INFORMAÇÕES DE SEGURANÇA DE PRODUTOS QUÍMICOS",
            ParagraphStyle("capa_t", fontName="Helvetica-Bold", fontSize=13,
                           textColor=COR_BRANCO, alignment=TA_CENTER)
        )],
        [Paragraph(
            "FISPQ — ABNT NBR 14725-4:2014 / GHS Rev.9",
            ParagraphStyle("capa_s", fontName="Helvetica", fontSize=9,
                           textColor=COR_BRANCO, alignment=TA_CENTER)
        )],
        [Paragraph(
            dados.get("consulta", "Composto Químico").upper(),
            ParagraphStyle("capa_n", fontName="Helvetica-Bold", fontSize=20,
                           textColor=COR_BRANCO, alignment=TA_CENTER,
                           spaceBefore=6, spaceAfter=6)
        )],
        [Paragraph(
            f"{dados.get('formula_molecular','—')}  |  CAS: {dados.get('cas','—')}  |  "
            f"PM: {dados.get('peso_molecular','—')} g/mol",
            ParagraphStyle("capa_f", fontName="Helvetica", fontSize=10,
                           textColor=COR_BRANCO, alignment=TA_CENTER)
        )],
    ]
    capa_tab = Table(capa_data, colWidths=[LARGURA_UTIL])
    capa_tab.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), COR_AZUL_ESCURO),
        ("TOPPADDING",  (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",(0, 0), (-1, -1), 12),
        ("BOX",         (0, 0), (-1, -1), 2, COR_AZUL_MEDIO),
        ("ROUNDEDCORNERS", (0, 0), (-1, -1), [5, 5, 5, 5]),
    ]))
    story.append(capa_tab)
    story.append(Spacer(1, 6*mm))

    # Aviso de perigo destaque na capa (se houver frases H)
    ghs = dados.get("ghs", {})
    sinal = (ghs.get("palavras_sinal") or [""])[0]
    if sinal:
        story.append(CaixaPerigo(
            f"PALAVRA DE ADVERTÊNCIA: {sinal.upper()}  —  "
            "Ler todas as instruções antes de usar este produto."
        ))
        story.append(Spacer(1, 4*mm))

    story.append(DivisorFino())
    story.append(Spacer(1, 4*mm))

    # ── 16 Seções ──
    secoes = [
        _secao_1(dados, estilos),
        _secao_2(dados, estilos),
        _secao_3(dados, estilos),
        _secao_4(estilos),
        _secao_5(dados, estilos),
        _secao_6(estilos),
        _secao_7(estilos),
        _secao_8(dados, estilos),
        _secao_9(dados, estilos),
        _secao_10(estilos),
        _secao_11(estilos),
        _secao_12(estilos),
        _secao_13(estilos),
        _secao_14(estilos),
        _secao_15(estilos),
        _secao_16(dados, estilos),
    ]

    for i, secao in enumerate(secoes, 1):
        story.extend(secao)
        # Quebra de página a cada 2 seções (exceto última)
        if i % 2 == 0 and i < 16:
            story.append(PageBreak())

    # ── Build ──
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)

    tamanho_kb = os.path.getsize(caminho_saida) // 1024
    print(f"[PDF] Gerado com sucesso: {caminho_saida}  ({tamanho_kb} KB)")
    return caminho_saida


# ─────────────────────────────────────────────
#  Execução direta (demo com dados simulados)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    # Dados de demonstração (sem precisar da API para testar o layout)
    dados_demo = {
        "consulta":          "etanol",
        "cid_pubchem":       702,
        "nome_iupac":        "ethanol",
        "formula_molecular": "C2H6O",
        "peso_molecular":    "46.07",
        "cas":               "64-17-5",
        "sinonimos":         ["ethyl alcohol", "grain alcohol", "EtOH", "alcohol"],
        "propriedades": {
            "formula_molecular": "C2H6O",
            "peso_molecular":    "46.07",
            "nome_iupac":        "ethanol",
            "xlogp":             "-0.1",
            "tpsa":              "20.2",
            "smiles":            "CCO",
            "inchikey":          "LFQSCWFLJHTTHZ-UHFFFAOYSA-N",
            "doadores_h":        "1",
            "aceptores_h":       "1",
        },
        "ghs": {
            "pictogramas":    ["GHS02", "GHS07"],
            "palavras_sinal": ["Perigo"],
            "frases_h":       ["H225", "H319", "H336"],
            "frases_p":       ["P210", "P233", "P240", "P241", "P242", "P280"],
        },
        "nist": {
            "ponto_ebulicao_C":    "78.4 °C",
            "ponto_fusao_C":       "-114.1 °C",
            "delta_hf_kJ_mol":     "-277.7 kJ/mol",
            "temp_critica_K":      "513.9 K",
            "pressao_critica_MPa": "6.14 MPa",
            "cp_J_mol_K":          "112.4 J/(mol·K)",
        },
        "explosividade": {
            "lie_pct":      3.3,
            "lse_pct":      19.0,
            "ponto_fulgor": "13 °C",
        },
        "nfpa_estimado": {"H": 2, "F": 3, "R": 0, "S": ""},
        "fontes": ["PubChem REST API", "NIST WebBook"],
    }

    # Se receber argumento JSON na linha de comando, usa ele
    if len(sys.argv) > 1 and sys.argv[1].endswith(".json"):
        import json
        with open(sys.argv[1]) as f:
            dados_demo = json.load(f)

    nome   = dados_demo.get("consulta", "composto").replace(" ", "_").lower()
    saida  = sys.argv[2] if len(sys.argv) > 2 else f"SDS_{nome}.pdf"

    gerar_sds_pdf(dados_demo, saida)
    print(f"\nAbra o arquivo: {saida}")
