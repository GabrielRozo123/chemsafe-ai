from __future__ import annotations

def check_regulatory_framework(profile, inventory_kg: float) -> dict:
    """
    Avalia o enquadramento em normas globais de Segurança de Processos
    baseado na massa armazenada (kg).
    """
    alerts =[]
    
    flammable = profile.flags.get("flammable", False)
    toxic = profile.flags.get("toxic_inhalation", False)
    
    # 1. OSHA PSM 1910.119 (EUA)
    # Limite padrão inflamáveis: 10,000 lbs (4535 kg)
    if flammable and inventory_kg >= 4535:
        alerts.append("🇺🇸 **OSHA PSM (1910.119):** Produto inflamável excede TQ de 10.000 lbs. Programa completo de Gestão de Segurança de Processo (14 pilares) é mandatário.")
    elif toxic and inventory_kg >= 680: # TQ médio conservador para tóxicos (ex: Cloro é 1500 lbs / 680 kg)
        alerts.append("🇺🇸 **OSHA PSM (1910.119):** Produto altamente tóxico excede TQ. Aplicabilidade de PSM requerida.")

    # 2. SEVESO III (Europa)
    if toxic and inventory_kg >= 5000:
        alerts.append("🇪🇺 **Diretiva SEVESO III:** Quantidade tóxica excede Lower-Tier. Relatório de Segurança e Política de Prevenção de Acidentes Maiores (MAPP) exigidos.")
    if flammable and inventory_kg >= 50000:
        alerts.append("🇪🇺 **Diretiva SEVESO III:** Inventário de inflamáveis excede Lower-Tier.")

    # 3. NR-20 (Brasil) - Inflamáveis e Combustíveis
    if flammable:
        if inventory_kg >= 50000:
            alerts.append("🇧🇷 **NR-20 (Brasil):** Instalação Classe III (Maior Risco). Requer Prontuário Completo, Análise de Risco complexa e certificações plenas.")
        elif inventory_kg >= 10000:
            alerts.append("🇧🇷 **NR-20 (Brasil):** Instalação Classe II. Requer Prontuário, Análise de Risco e treinamento intermediário.")
        else:
            alerts.append("🇧🇷 **NR-20 (Brasil):** Instalação Classe I ou isenta dependendo do invólucro. Prontuário básico e treinamento requeridos.")

    if not alerts:
        alerts.append("✅ **Isento de Normas Maiores:** Com base neste inventário, não atinge limiares críticos de Seveso, OSHA PSM ou classes altas da NR-20. Regras gerais de SST ainda se aplicam.")

    return alerts

def generate_facilitator_questions(profile) -> list[str]:
    """
    Gera perguntas provocativas para o facilitador de HAZOP.
    """
    questions =["A documentação do P&ID está " "as-built" " (como construída)? A equipe confirma?"]
    
    if profile.flags.get("toxic_inhalation"):
        questions.append("Se o detector de gás tóxico falhar silenciosamente (fail-to-danger), quanto tempo a equipe leva para perceber pelo odor ou sintomas?")
        questions.append("A rota de evacuação cruza a direção predominante do vento local?")
    
    if profile.flags.get("flammable"):
        questions.append("As rotinas de manutenção garantem que a equipotencialização (aterramento) não seja rompida após pintura?")
        questions.append("Existe algum cenário onde um vazamento não detectado possa entrar no sistema de captação de ar condicionado da sala de controle?")
        
    if profile.flags.get("pressurized"):
        questions.append("As válvulas PSV descarregam para atmosfera segura ou para um Flare/Scrubber? Qual o cenário se o Flare estiver apagado?")

    return questions
