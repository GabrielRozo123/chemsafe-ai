"""
chemsafe_api.py
===============
Integração real com APIs públicas para o agente ChemSafe AI.

Fontes:
  - PubChem REST API  → https://pubchem.ncbi.nlm.nih.gov/rest/pug
  - NIST WebBook API  → https://webbook.nist.gov/cgi/cbook.cgi

Uso rápido:
    from chemsafe_api import ChemSafeAPI
    api = ChemSafeAPI()
    dados = api.buscar_composto("etanol")
    print(dados)

Dependências:
    pip install requests
"""

import requests
import json
import time
import re
from typing import Optional


# ─────────────────────────────────────────────
#  Configuração global
# ─────────────────────────────────────────────

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
NIST_BASE    = "https://webbook.nist.gov/cgi/cbook.cgi"

TIMEOUT      = 10   # segundos por requisição
RETRY_MAX    = 3    # tentativas em caso de falha
RETRY_DELAY  = 1.5  # segundos entre tentativas


# ─────────────────────────────────────────────
#  Mapeamento de pictogramas GHS
# ─────────────────────────────────────────────

GHS_PICTOGRAMAS = {
    "GHS01": "Explosivo",
    "GHS02": "Inflamável",
    "GHS03": "Comburente / Oxidante",
    "GHS04": "Gás sob pressão",
    "GHS05": "Corrosivo",
    "GHS06": "Tóxico agudo (caveira)",
    "GHS07": "Irritante / Nocivo",
    "GHS08": "Risco à saúde (crônico)",
    "GHS09": "Perigo ambiental aquático",
}

# Mapeamento de código H → descrição
H_CODES = {
    "H200": "Explosivo instável",
    "H220": "Gás extremamente inflamável",
    "H221": "Gás inflamável",
    "H222": "Aerossol extremamente inflamável",
    "H224": "Líquido e vapor extremamente inflamáveis",
    "H225": "Líquido e vapor muito inflamáveis",
    "H226": "Líquido e vapor inflamáveis",
    "H228": "Sólido inflamável",
    "H241": "Aquecimento pode causar incêndio ou explosão",
    "H270": "Pode provocar ou intensificar incêndio; oxidante",
    "H271": "Pode provocar incêndio ou explosão; oxidante forte",
    "H272": "Pode intensificar incêndio; oxidante",
    "H280": "Contém gás sob pressão",
    "H281": "Contém gás refrigerado; pode causar queimaduras criogênicas",
    "H290": "Pode ser corrosivo para metais",
    "H300": "Fatal por ingestão",
    "H301": "Tóxico por ingestão",
    "H302": "Nocivo por ingestão",
    "H304": "Pode ser fatal por ingestão e penetração nas vias respiratórias",
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
    "H334": "Pode provocar sintomas de alergia ou asma ou dificuldades respiratórias por inalação",
    "H335": "Pode irritar as vias respiratórias",
    "H336": "Pode provocar sonolência ou vertigens",
    "H340": "Pode provocar alterações genéticas",
    "H341": "Suspeito de provocar alterações genéticas",
    "H350": "Pode provocar cancro",
    "H351": "Suspeito de provocar cancro",
    "H360": "Pode prejudicar a fertilidade ou o nascituro",
    "H361": "Suspeito de prejudicar a fertilidade ou o nascituro",
    "H370": "Provoca danos nos órgãos",
    "H371": "Pode provocar danos nos órgãos",
    "H372": "Provoca danos nos órgãos por exposição prolongada ou repetida",
    "H373": "Pode provocar danos nos órgãos por exposição prolongada ou repetida",
    "H400": "Muito tóxico para os organismos aquáticos",
    "H410": "Muito tóxico para os organismos aquáticos com efeitos prolongados",
    "H411": "Tóxico para os organismos aquáticos com efeitos prolongados",
    "H412": "Nocivo para os organismos aquáticos com efeitos prolongados",
    "H413": "Pode provocar efeitos nocivos duradouros nos organismos aquáticos",
}


# ─────────────────────────────────────────────
#  Utilitário HTTP com retry
# ─────────────────────────────────────────────

def _get(url: str, params: dict = None) -> Optional[dict]:
    """GET com retry automático. Retorna dict JSON ou None."""
    for tentativa in range(1, RETRY_MAX + 1):
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 404:
                return None   # composto não encontrado
            else:
                print(f"  [HTTP {resp.status_code}] tentativa {tentativa}/{RETRY_MAX}")
        except requests.exceptions.Timeout:
            print(f"  [TIMEOUT] tentativa {tentativa}/{RETRY_MAX}")
        except requests.exceptions.ConnectionError:
            print(f"  [CONN ERROR] tentativa {tentativa}/{RETRY_MAX}")
        except Exception as e:
            print(f"  [ERRO] {e}")
            return None
        if tentativa < RETRY_MAX:
            time.sleep(RETRY_DELAY)
    return None


def _get_text(url: str, params: dict = None) -> Optional[str]:
    """GET que retorna texto bruto (para NIST)."""
    for tentativa in range(1, RETRY_MAX + 1):
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT)
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code == 404:
                return None
        except Exception as e:
            print(f"  [ERRO texto] {e}")
        if tentativa < RETRY_MAX:
            time.sleep(RETRY_DELAY)
    return None


# ─────────────────────────────────────────────
#  PubChem — busca de CID
# ─────────────────────────────────────────────

def pubchem_buscar_cid(identificador: str) -> Optional[int]:
    """
    Resolve um nome, fórmula ou número CAS para o CID do PubChem.
    Tenta por nome primeiro, depois por CAS (inchikey se necessário).
    """
    # Tentativa 1: por nome
    url = f"{PUBCHEM_BASE}/compound/name/{requests.utils.quote(identificador)}/cids/JSON"
    dados = _get(url)
    if dados and "IdentifierList" in dados:
        return dados["IdentifierList"]["CID"][0]

    # Tentativa 2: por CAS (tratado como sinônimo)
    url = f"{PUBCHEM_BASE}/compound/name/{requests.utils.quote(identificador)}/cids/JSON"
    dados = _get(url, params={"name_type": "word"})
    if dados and "IdentifierList" in dados:
        return dados["IdentifierList"]["CID"][0]

    return None


# ─────────────────────────────────────────────
#  PubChem — propriedades físico-químicas
# ─────────────────────────────────────────────

PROPS_PUBCHEM = ",".join([
    "MolecularFormula",
    "MolecularWeight",
    "IUPACName",
    "XLogP",
    "TPSA",
    "HBondDonorCount",
    "HBondAcceptorCount",
    "CanonicalSMILES",
    "InChIKey",
    "Charge",
    "RotatableBondCount",
])

def pubchem_propriedades(cid: int) -> dict:
    """Busca propriedades físico-químicas básicas pelo CID."""
    url = f"{PUBCHEM_BASE}/compound/cid/{cid}/property/{PROPS_PUBCHEM}/JSON"
    dados = _get(url)
    if not dados:
        return {}
    props = dados.get("PropertyTable", {}).get("Properties", [{}])[0]
    return {
        "formula_molecular":   props.get("MolecularFormula", "—"),
        "peso_molecular":      props.get("MolecularWeight", "—"),
        "nome_iupac":          props.get("IUPACName", "—"),
        "xlogp":               props.get("XLogP", "—"),
        "tpsa":                props.get("TPSA", "—"),
        "smiles":              props.get("CanonicalSMILES", "—"),
        "inchikey":            props.get("InChIKey", "—"),
        "doadores_h":          props.get("HBondDonorCount", "—"),
        "aceptores_h":         props.get("HBondAcceptorCount", "—"),
    }


# ─────────────────────────────────────────────
#  PubChem — dados GHS / classificações de perigo
# ─────────────────────────────────────────────

def pubchem_ghs(cid: int) -> dict:
    """
    Extrai classificações GHS, pictogramas e frases H/P via
    PubChem Safety and Hazards endpoint.
    """
    url = f"{PUBCHEM_BASE}/compound/cid/{cid}/JSON"
    dados = _get(url)
    if not dados:
        return {}

    result = {
        "pictogramas": [],
        "palavras_sinal": [],
        "frases_h": [],
        "frases_p": [],
        "ghs_raw": [],
    }

    sections = (dados.get("PC_Compounds", [{}])[0]
                     .get("props", []))

    # PubChem organiza propriedades em "props" → urn/label
    for prop in sections:
        label = prop.get("urn", {}).get("label", "")
        name  = prop.get("urn", {}).get("name", "")
        value = prop.get("value", {})
        sval  = value.get("sval", "")

        if "GHS" in label and "Pictogram" in name:
            result["pictogramas"].append(sval)
        elif "Signal" in label:
            result["palavras_sinal"].append(sval)
        elif label == "GHS Hazard Statements":
            result["frases_h"].append(sval)
        elif label == "GHS Precautionary Statements":
            result["frases_p"].append(sval)

    # Endpoint alternativo: PubChem Safety Data
    url2 = f"{PUBCHEM_BASE}/compound/cid/{cid}/classification/JSON"
    dados2 = _get(url2)
    if dados2:
        result["ghs_raw"] = dados2

    return result


# ─────────────────────────────────────────────
#  PubChem — sinônimos e número CAS
# ─────────────────────────────────────────────

def pubchem_sinonimos(cid: int) -> dict:
    """Retorna sinônimos e extrai número CAS se disponível."""
    url = f"{PUBCHEM_BASE}/compound/cid/{cid}/synonyms/JSON"
    dados = _get(url)
    if not dados:
        return {"cas": "—", "sinonimos": []}

    sinonimos = (dados.get("InformationList", {})
                      .get("Information", [{}])[0]
                      .get("Synonym", []))

    # CAS tem formato NNNNNN-NN-N
    cas_pattern = re.compile(r"^\d{1,7}-\d{2}-\d$")
    cas = next((s for s in sinonimos if cas_pattern.match(s)), "—")

    return {
        "cas": cas,
        "sinonimos": sinonimos[:10],  # primeiros 10
    }


# ─────────────────────────────────────────────
#  NIST WebBook — propriedades termodinâmicas
# ─────────────────────────────────────────────

def nist_propriedades(cas: str) -> dict:
    """
    Consulta o NIST WebBook pelo número CAS.
    Extrai propriedades termodinâmicas e de transporte do HTML retornado.
    O NIST não tem API JSON pública — fazemos parse do HTML estruturado.
    """
    if cas == "—" or not cas:
        return {}

    params = {
        "ID": cas,
        "Units": "SI",
        "Type": "JANAFG",  # dados termodinâmicos
    }
    html = _get_text(NIST_BASE, params=params)
    if not html:
        return {}

    result = {}

    # Extrai ponto de ebulição
    m = re.search(r"Boiling point[^<]*?(\d+[\.,]\d*)\s*K", html)
    if m:
        try:
            k = float(m.group(1).replace(",", "."))
            result["ponto_ebulicao_K"] = f"{k:.1f} K"
            result["ponto_ebulicao_C"] = f"{k - 273.15:.1f} °C"
        except ValueError:
            pass

    # Extrai ponto de fusão
    m = re.search(r"Melting point[^<]*?(\d+[\.,]\d*)\s*K", html)
    if m:
        try:
            k = float(m.group(1).replace(",", "."))
            result["ponto_fusao_K"] = f"{k:.1f} K"
            result["ponto_fusao_C"] = f"{k - 273.15:.1f} °C"
        except ValueError:
            pass

    # Enthalpia de formação (ΔHf)
    m = re.search(r"Enthalpy of formation[^<]*?(-?\d+[\.,]\d*)\s*kJ/mol", html)
    if m:
        result["delta_hf_kJ_mol"] = f"{m.group(1)} kJ/mol"

    # Temperatura crítica
    m = re.search(r"Critical temperature[^<]*?(\d+[\.,]\d*)\s*K", html)
    if m:
        result["temp_critica_K"] = f"{m.group(1)} K"

    # Pressão crítica
    m = re.search(r"Critical pressure[^<]*?(\d+[\.,]\d*)\s*MPa", html)
    if m:
        result["pressao_critica_MPa"] = f"{m.group(1)} MPa"

    # Capacidade calorífica Cp
    m = re.search(r"Heat capacity[^<]*?(\d+[\.,]\d*)\s*J/mol/K", html)
    if m:
        result["cp_J_mol_K"] = f"{m.group(1)} J/(mol·K)"

    result["fonte"] = f"NIST WebBook (CAS {cas})"
    result["url"]   = f"https://webbook.nist.gov/cgi/cbook.cgi?ID={cas}&Units=SI"

    return result


# ─────────────────────────────────────────────
#  NIST WebBook — limites de explosividade (LIE/LSE)
# ─────────────────────────────────────────────

def nist_explosividade(cas: str) -> dict:
    """
    Extrai LIE (Lower Explosive Limit) e LSE (Upper Explosive Limit)
    e ponto de fulgor do NIST WebBook.
    """
    if not cas or cas == "—":
        return {}

    params = {"ID": cas, "Units": "SI", "Type": "EXPDATA"}
    html = _get_text(NIST_BASE, params=params)
    if not html:
        # Fallback: página principal do composto
        params = {"ID": cas, "Units": "SI"}
        html = _get_text(NIST_BASE, params=params)
    if not html:
        return {}

    result = {}

    # LIE — Lower flammable/explosive limit
    for pat in [
        r"[Ll]ower flammable limit[^<]*?(\d+[\.,]\d*)\s*%",
        r"LFL[^<]*?(\d+[\.,]\d*)\s*%",
        r"LEL[^<]*?(\d+[\.,]\d*)\s*%",
        r"[Ll]ower [Ee]xplosive [Ll]imit[^<]*?(\d+[\.,]\d*)\s*%",
    ]:
        m = re.search(pat, html)
        if m:
            result["lie_pct"] = float(m.group(1).replace(",", "."))
            break

    # LSE — Upper flammable/explosive limit
    for pat in [
        r"[Uu]pper flammable limit[^<]*?(\d+[\.,]\d*)\s*%",
        r"UFL[^<]*?(\d+[\.,]\d*)\s*%",
        r"UEL[^<]*?(\d+[\.,]\d*)\s*%",
        r"[Uu]pper [Ee]xplosive [Ll]imit[^<]*?(\d+[\.,]\d*)\s*%",
    ]:
        m = re.search(pat, html)
        if m:
            result["lse_pct"] = float(m.group(1).replace(",", "."))
            break

    # Ponto de fulgor
    for pat in [
        r"[Ff]lash [Pp]oint[^<]*?(-?\d+[\.,]\d*)\s*[K°]",
        r"[Ff]ulgor[^<]*?(-?\d+[\.,]\d*)\s*°C",
    ]:
        m = re.search(pat, html)
        if m:
            result["ponto_fulgor"] = f"{m.group(1)} °C"
            break

    return result


# ─────────────────────────────────────────────
#  Classificação de risco NFPA 704 (heurística)
# ─────────────────────────────────────────────

def _estimar_nfpa(dados: dict) -> dict:
    """
    Estima os valores NFPA 704 a partir de frases H e propriedades.
    Esta é uma heurística — validação manual é recomendada para uso regulatório.
    """
    h = " ".join(dados.get("frases_h", []))
    lie = dados.get("lie_pct")
    flash = dados.get("ponto_fulgor_num")  # float °C se extraído

    # Saúde (H)
    saude = 0
    if any(x in h for x in ["H330", "H310", "H300"]):
        saude = 4
    elif any(x in h for x in ["H331", "H311", "H301"]):
        saude = 3
    elif any(x in h for x in ["H332", "H312", "H302", "H314"]):
        saude = 2
    elif any(x in h for x in ["H315", "H319", "H335"]):
        saude = 1

    # Inflamabilidade (F)
    inflamab = 0
    if lie is not None and lie < 1:
        inflamab = 4
    elif any(x in h for x in ["H220", "H221", "H222", "H224"]):
        inflamab = 4
    elif any(x in h for x in ["H225", "H228"]):
        inflamab = 3
    elif any(x in h for x in ["H226"]):
        inflamab = 2
    elif any(x in h for x in ["H228"]):
        inflamab = 1

    # Reatividade (R)
    reat = 0
    if any(x in h for x in ["H200", "H201", "H202", "H203"]):
        reat = 4
    elif any(x in h for x in ["H240", "H241"]):
        reat = 3
    elif any(x in h for x in ["H250", "H260", "H261", "H271"]):
        reat = 2
    elif any(x in h for x in ["H272", "H290"]):
        reat = 1

    # Especial
    especial = ""
    if "H290" in h or "reacts with water" in h.lower():
        especial = "W"
    elif any(x in h for x in ["H340", "H350"]):
        especial = "OX"

    return {"H": saude, "F": inflamab, "R": reat, "S": especial}


# ─────────────────────────────────────────────
#  Função principal: busca completa
# ─────────────────────────────────────────────

def buscar_composto(identificador: str, verbose: bool = True) -> dict:
    """
    Consulta completa de um composto nas APIs PubChem e NIST.

    Parâmetros:
        identificador : nome, fórmula molecular ou número CAS
        verbose       : imprime log de progresso

    Retorna:
        dict com todas as propriedades consolidadas
    """
    log = print if verbose else (lambda *a: None)

    log(f"\n{'='*55}")
    log(f"  ChemSafe API — consultando: {identificador}")
    log(f"{'='*55}")

    resultado = {
        "consulta":           identificador,
        "cid_pubchem":        None,
        "nome_iupac":         "—",
        "formula_molecular":  "—",
        "peso_molecular":     "—",
        "cas":                "—",
        "sinonimos":          [],
        "propriedades":       {},
        "ghs":                {},
        "nist":               {},
        "explosividade":      {},
        "nfpa_estimado":      {},
        "fontes":             [],
        "erros":              [],
    }

    # ── Etapa 1: Resolver CID ──
    log("\n[THINK] Resolvendo identificador via PubChem...")
    cid = pubchem_buscar_cid(identificador)
    if not cid:
        msg = f"Composto '{identificador}' não encontrado no PubChem."
        log(f"[ERRO] {msg}")
        resultado["erros"].append(msg)
        return resultado

    resultado["cid_pubchem"] = cid
    log(f"[OK]   CID PubChem: {cid}")

    # ── Etapa 2: Sinônimos e CAS ──
    log("\n[ACT]  Buscando sinônimos e número CAS...")
    sin = pubchem_sinonimos(cid)
    resultado["cas"]       = sin.get("cas", "—")
    resultado["sinonimos"] = sin.get("sinonimos", [])
    log(f"[OK]   CAS: {resultado['cas']}")

    # ── Etapa 3: Propriedades PubChem ──
    log("\n[ACT]  Buscando propriedades físico-químicas (PubChem)...")
    props = pubchem_propriedades(cid)
    resultado["propriedades"]    = props
    resultado["formula_molecular"] = props.get("formula_molecular", "—")
    resultado["peso_molecular"]    = props.get("peso_molecular", "—")
    resultado["nome_iupac"]        = props.get("nome_iupac", "—")
    resultado["fontes"].append("PubChem REST API")
    log(f"[OK]   Fórmula: {resultado['formula_molecular']} | PM: {resultado['peso_molecular']} g/mol")

    # ── Etapa 4: GHS / Perigos ──
    log("\n[ACT]  Buscando classificações GHS (PubChem Safety)...")
    ghs = pubchem_ghs(cid)
    resultado["ghs"] = ghs
    n_pics = len(ghs.get("pictogramas", []))
    n_h    = len(ghs.get("frases_h", []))
    log(f"[OK]   {n_pics} pictogramas, {n_h} frases H encontradas")

    # ── Etapa 5: NIST WebBook ──
    cas = resultado["cas"]
    if cas != "—":
        log(f"\n[ACT]  Consultando NIST WebBook (CAS {cas})...")
        nist = nist_propriedades(cas)
        resultado["nist"] = nist
        log(f"[OK]   {len(nist)} propriedades NIST extraídas")

        log("\n[ACT]  Buscando limites de explosividade (NIST)...")
        expl = nist_explosividade(cas)
        resultado["explosividade"] = expl
        if expl.get("lie_pct"):
            log(f"[OK]   LIE={expl['lie_pct']}% | LSE={expl.get('lse_pct','—')}%")
        else:
            log("[WARN] Limites de explosividade não encontrados no NIST para este CAS.")
        resultado["fontes"].append("NIST WebBook")
    else:
        log("\n[WARN] CAS não encontrado — pulando consulta NIST.")

    # ── Etapa 6: NFPA estimado ──
    log("\n[OBSERVE] Estimando classificação NFPA 704...")
    nfpa_input = {
        "frases_h": ghs.get("frases_h", []),
        "lie_pct":  resultado["explosividade"].get("lie_pct"),
    }
    resultado["nfpa_estimado"] = _estimar_nfpa(nfpa_input)
    n = resultado["nfpa_estimado"]
    log(f"[OK]   NFPA estimado — Saúde:{n['H']} | Inflamab:{n['F']} | Reat:{n['R']} | Esp:{n['S'] or '—'}")

    log(f"\n{'='*55}")
    log(f"  Consulta concluída. Fontes: {', '.join(resultado['fontes'])}")
    log(f"{'='*55}\n")

    return resultado


# ─────────────────────────────────────────────
#  Utilitário: formatar resultado para exibição
# ─────────────────────────────────────────────

def formatar_resumo(dados: dict) -> str:
    """Formata os dados retornados por buscar_composto() como texto."""
    if dados.get("erros"):
        return f"ERRO: {'; '.join(dados['erros'])}"

    p   = dados.get("propriedades", {})
    ghs = dados.get("ghs", {})
    ex  = dados.get("explosividade", {})
    nist= dados.get("nist", {})
    n   = dados.get("nfpa_estimado", {})

    linhas = [
        f"╔══════════════════════════════════════════════╗",
        f"  {dados['consulta'].upper()} — Ficha de segurança resumida",
        f"╠══════════════════════════════════════════════╣",
        f"  Fórmula     : {dados['formula_molecular']}",
        f"  Peso mol.   : {dados['peso_molecular']} g/mol",
        f"  CAS         : {dados['cas']}",
        f"  CID PubChem : {dados['cid_pubchem']}",
        f"  Nome IUPAC  : {dados['nome_iupac'][:60]}",
        f"",
        f"  ── Perigos GHS ──",
    ]

    pics = ghs.get("pictogramas", [])
    if pics:
        linhas.append(f"  Pictogramas : {', '.join(pics)}")

    sinal = ghs.get("palavras_sinal", [])
    if sinal:
        linhas.append(f"  Palavra-sinal: {sinal[0]}")

    for fh in ghs.get("frases_h", [])[:6]:
        cod = fh.strip()[:4]
        desc = H_CODES.get(cod, fh)
        linhas.append(f"  {cod}: {desc}")

    linhas += [
        f"",
        f"  ── Explosividade (Zabetakis) ──",
        f"  LIE : {ex.get('lie_pct', '—')} %",
        f"  LSE : {ex.get('lse_pct', '—')} %",
        f"  Ponto de fulgor: {ex.get('ponto_fulgor', '—')}",
        f"",
        f"  ── Termodinâmica (NIST) ──",
        f"  Eb  : {nist.get('ponto_ebulicao_C', '—')}",
        f"  Ef  : {nist.get('ponto_fusao_C', '—')}",
        f"  ΔHf : {nist.get('delta_hf_kJ_mol', '—')}",
        f"  Tc  : {nist.get('temp_critica_K', '—')}",
        f"",
        f"  ── NFPA 704 (estimado) ──",
        f"  Saúde (H): {n.get('H','—')}  |  Inflamab (F): {n.get('F','—')}  |  Reat (R): {n.get('R','—')}  |  Esp: {n.get('S') or '—'}",
        f"",
        f"  Fontes: {', '.join(dados['fontes'])}",
        f"╚══════════════════════════════════════════════╝",
    ]

    return "\n".join(linhas)


# ─────────────────────────────────────────────
#  Classe principal (interface orientada a objetos)
# ─────────────────────────────────────────────

class ChemSafeAPI:
    """
    Interface de alto nível para o módulo de integração ChemSafe.

    Exemplo:
        api = ChemSafeAPI()
        dados = api.buscar_composto("acetone")
        print(api.resumo(dados))
        api.exportar_json(dados, "acetona.json")
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def buscar_composto(self, identificador: str) -> dict:
        return buscar_composto(identificador, verbose=self.verbose)

    def buscar_lote(self, identificadores: list) -> list:
        """Busca uma lista de compostos. Respeita rate-limit com pausa entre consultas."""
        resultados = []
        for i, ident in enumerate(identificadores, 1):
            print(f"\n[{i}/{len(identificadores)}] Buscando: {ident}")
            r = buscar_composto(ident, verbose=self.verbose)
            resultados.append(r)
            if i < len(identificadores):
                time.sleep(0.3)  # respeita fair-use das APIs
        return resultados

    def resumo(self, dados: dict) -> str:
        return formatar_resumo(dados)

    def exportar_json(self, dados: dict, caminho: str):
        """Salva os dados em arquivo JSON."""
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        print(f"[JSON] Exportado: {caminho}")

    def get_frases_h(self, dados: dict) -> list:
        """Retorna lista de (código, descrição) para as frases H."""
        frases = dados.get("ghs", {}).get("frases_h", [])
        resultado = []
        for f in frases:
            cod  = f.strip()[:4]
            desc = H_CODES.get(cod, f)
            resultado.append((cod, desc))
        return resultado

    def get_nfpa(self, dados: dict) -> dict:
        return dados.get("nfpa_estimado", {})

    def get_explosividade(self, dados: dict) -> dict:
        return dados.get("explosividade", {})


# ─────────────────────────────────────────────
#  Execução direta (demo)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    ident = sys.argv[1] if len(sys.argv) > 1 else "ethanol"

    api  = ChemSafeAPI(verbose=True)
    dados = api.buscar_composto(ident)

    print(api.resumo(dados))

    # Salva JSON para uso posterior (ex: gerador de SDS)
    nome_arquivo = ident.replace(" ", "_").lower() + "_chemsafe.json"
    api.exportar_json(dados, nome_arquivo)
    print(f"\nDados salvos em: {nome_arquivo}")
