from __future__ import annotations

def get_typical_scenarios(profile) -> list[dict]:
    """
    Motor do Sprint 13: Lê as propriedades do composto e sugere os cenários clássicos da engenharia química.
    """
    scenarios =[]
    compound_name = profile.identity.get("name", "o produto").lower()
    incompatibilities = " ".join(profile.storage.get("incompatibilities",[])).lower()

    # 1. Fogo Externo (Pool Fire / BLEVE)
    if profile.flags.get("flammable"):
        scenarios.append({
            "titulo": "🔥 Fogo Externo (Fire Case / Pool Fire)",
            "desvio": "Mais Temperatura / Mais Pressão",
            "causa": "Vazamento em equipamento adjacente gerando poça em chamas sob o vaso/tanque.",
            "consequencia": "Aquecimento do inventário, sobrepressão rápida, possível ruptura catastrófica (BLEVE) ou Major Pool Fire.",
            "salvaguardas": "PSV dimensionada para fire case, Dique de contenção, Sistema de dilúvio/espuma, Válvula de isolamento (SDV).",
            "tipo": "Incêndio"
        })

    # 2. Falha de Vedação (Emissão Tóxica ou Inflamável)
    if profile.flags.get("pressurized") or profile.flags.get("toxic_inhalation"):
        impact = "Nuvem tóxica com impacto em operadores e comunidade." if profile.flags.get("toxic_inhalation") else "Formação de nuvem explosiva (VCE)."
        scenarios.append({
            "titulo": "💨 Falha de Vedação (Perda de Contenção Menor)",
            "desvio": "Menos Nível / Fluxo Reverso (Vazamento)",
            "causa": "Ruptura de selo mecânico de bomba, falha em gaxeta de válvula ou corrosão em flange.",
            "consequencia": impact,
            "salvaguardas": "Detector de gás (LEL ou Tóxico), Inspeção termográfica/espessimetria, Uso de bombas de acoplamento magnético.",
            "tipo": "Vazamento"
        })

    # 3. Sobrepressão por Bloqueio
    if profile.flags.get("pressurized") or profile.prop("vapor_pressure_kpa_20c", 0) > 100:
        scenarios.append({
            "titulo": "🛑 Sobrepressão por Bloqueio de Saída (Blocked Discharge)",
            "desvio": "Mais Pressão",
            "causa": "Fechamento inadvertido de válvula manual na descarga ou falha de válvula de controle em posição fechada.",
            "consequencia": "Aumento contínuo de pressão pela bomba/compressor a montante, resultando em fadiga mecânica e perda de contenção.",
            "salvaguardas": "PSV/PRV na linha de recalque, Transmissor de pressão (PT) com alarme de alta (PAH) e trip da bomba.",
            "tipo": "Operacional"
        })

    # 4. Amônia + Hipoclorito (Cenário Específico)
    if "amônia" in compound_name or "ammonia" in compound_name:
        scenarios.append({
            "titulo": "☠️ Mistura Inadvertida: Amônia + Hipoclorito",
            "desvio": "Outro que (Composição Indesejada)",
            "causa": "Erro operacional durante o descarregamento ou retorno de linha não drenada.",
            "consequencia": "Reação violenta formando cloraminas altamente tóxicas e explosivas. Risco letal agudo.",
            "salvaguardas": "Conexões de engate incompatíveis (Poka-yoke), Procedimento rigoroso de liberação, Segregação total de bacias.",
            "tipo": "Reatividade"
        })

    # 5. Solvente + Oxidante (Cenário Específico)
    if profile.flags.get("flammable") and ("oxid" in incompatibilities or "nitric" in incompatibilities):
        scenarios.append({
            "titulo": "💥 Mistura Inadvertida: Solvente + Oxidante",
            "desvio": "Outro que (Contaminação)",
            "causa": "Contaminação cruzada em reator batch ou uso de mangueira contaminada.",
            "consequencia": "Reação exotérmica descontrolada (Runaway), autoignição imediata e explosão do equipamento.",
            "salvaguardas": "Matriz de incompatibilidade aplicada ao piso, Bloqueios mecânicos (raquete/figura 8) entre linhas.",
            "tipo": "Reatividade"
        })

    # 6. Mistura Ácido-Base
    if profile.flags.get("corrosive"):
        scenarios.append({
            "titulo": "🧪 Mistura Ácido-Base (Neutralização Exotérmica)",
            "desvio": "Mais Temperatura / Outro que (Composição)",
            "causa": "Mistura acidental no sistema de tratamento de efluentes ou tanque pulmão.",
            "consequencia": "Fervura instantânea (boil-over), projeção de material corrosivo quente sobre operadores.",
            "salvaguardas": "Controle de pH instrumentado, Adição dosificada automática, Uso de EPI nível B/C.",
            "tipo": "Reatividade"
        })

    return scenarios
