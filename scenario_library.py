from __future__ import annotations

def get_typical_scenarios(profile) -> list[dict]:
    scenarios =[]
    
    # Variáveis Físico-Químicas do Perfil
    flammable = profile.flags.get("flammable", False)
    toxic = profile.flags.get("toxic_inhalation", False)
    pressurized = profile.flags.get("pressurized", False)
    corrosive = profile.flags.get("corrosive", False)
    reactive = profile.flags.get("reactive_hazard", False)
    
    vapor_density = profile.prop("vapor_density_air", 0)
    boiling_point = profile.prop("boiling_point_c", 100)

    # 1. BLEVE / Fireball (Pressurizado + Inflamável)
    if flammable and pressurized:
        scenarios.append({
            "titulo": "🔥 Ruptura Catastrófica sob Fogo (BLEVE / Fireball)",
            "desvio": "Mais Pressão / Mais Temperatura",
            "causa": "Fogo em poça (pool fire) externo impingindo chamas na parede não molhada do vaso pressurizado.",
            "consequencia": "Enfraquecimento metálico, ruptura catastrófica, bola de fogo massiva e projeção de fragmentos (ondas de choque letal).",
            "salvaguardas": "Válvula PSV dimensionada para fire case, Isolamento térmico à prova de fogo, Sistema de dilúvio (Water Spray), Distanciamento seguro.",
            "tipo": "Incêndio/Explosão"
        })

    # 2. Pool Fire / Flash Fire (Inflamável Líquido)
    if flammable and not pressurized:
        scenarios.append({
            "titulo": "🧨 Fogo em Poça (Pool Fire) / Flash Fire",
            "desvio": "Mais Nível / Vazamento",
            "causa": "Transbordamento de tanque ou ruptura de tubulação formando poça, seguido de ignição por eletricidade estática ou trabalho a quente.",
            "consequencia": "Radiação térmica extrema afetando equipamentos adjacentes e risco de fatalidade para operadores na área.",
            "salvaguardas": "Dique de contenção, Aterramento e Equipotencialização, Sistema gerador de espuma, Detectores de Gás (LEL).",
            "tipo": "Incêndio"
        })

    # 3. Dispersão de Gás Tóxico Denso (Tóxico + Densidade > 1)
    if toxic and vapor_density > 1.1:
        scenarios.append({
            "titulo": "☠️ Acúmulo de Gás Tóxico Denso em Áreas Baixas",
            "desvio": "Vazamento / Perda de Contenção",
            "causa": "Falha de selo mecânico ou gaxeta, liberando gás que é mais pesado que o ar.",
            "consequencia": "Gás viaja rente ao solo, acumulando em trincheiras, esgotos ou áreas confinadas. Risco de asfixia/intoxicação letal em espaços confinados.",
            "salvaguardas": "Detectores de gás tóxico instalados próximos ao solo, Ventilação exaustora dedicada, Proibição de acesso a trincheiras sem liberação de PT.",
            "tipo": "Toxicidade"
        })

    # 4. Vapor Cloud Explosion - VCE (Inflamável + Risco de Confinamento)
    if flammable and boiling_point < 40:
        scenarios.append({
            "titulo": "💥 Explosão de Nuvem de Vapor (VCE)",
            "desvio": "Vazamento",
            "causa": "Liberação contínua de produto altamente volátil formando nuvem explosiva em área com alto congestionamento de tubulações.",
            "consequencia": "Ignição tardia gera sobrepressão severa (Blast Wave), destruindo estruturas metálicas e construções.",
            "salvaguardas": "Layout aberto para evitar congestionamento, Detectores LEL com intertravamento para fechamento de válvulas SDV, Cortinas de água.",
            "tipo": "Explosão"
        })

    # 5. Reatividade Exotérmica (Runaway)
    if reactive:
        scenarios.append({
            "titulo": "🌡️ Reação Descontrolada (Thermal Runaway)",
            "desvio": "Mais Temperatura / Outro Que (Contaminação)",
            "causa": "Falha no resfriamento do reator, acúmulo de reagentes não reagidos ou contaminação com incompatíveis.",
            "consequencia": "Aumento exponencial de temperatura e pressão, excedendo a capacidade da PSV, resultando em ruptura do vaso.",
            "salvaguardas": "Sistemas de resfriamento redundantes (SIS), Inibição automática de reação (Quench system), Disco de ruptura em paralelo com PSV.",
            "tipo": "Reatividade"
        })

    # 6. Degradação de Materiais (Corrosivos)
    if corrosive:
        scenarios.append({
            "titulo": "🧪 Perda de Integridade por Corrosão Acelerada",
            "desvio": "Menos Espessura / Mais Temperatura",
            "causa": "Operação fora da janela de temperatura/concentração ou entrada de umidade no sistema.",
            "consequencia": "Vazamento em spray (pinhole) de material agressivo, causando queimaduras químicas graves nos operadores.",
            "salvaguardas": "Programa de inspeção de integridade (Espessimetria), Chuveiro e lava-olhos de emergência, Flange guards (protetores de flange).",
            "tipo": "Integridade"
        })

    # Cenário Padrão de Bloqueio (Se não for nada de muito agressivo)
    if not scenarios:
        scenarios.append({
            "titulo": "🛑 Sobrepressão por Bloqueio (Blocked Discharge)",
            "desvio": "Mais Pressão",
            "causa": "Fechamento inadvertido de válvula manual a jusante de uma bomba ou compressor.",
            "consequencia": "Falha de juntas, flanges ou selos mecânicos por sobrepressão mecânica.",
            "salvaguardas": "Válvula de alívio na descarga da bomba (Thermal Relief), Treinamento operacional.",
            "tipo": "Operacional"
        })

    return scenarios
