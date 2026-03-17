from __future__ import annotations

# Dicionário central de traduções
DICT = {
    "pt": {
        "app_title": "ChemSafe Pro Determinístico",
        "quick_access": "Acesso rápido",
        "search_compound": "Buscar composto",
        "load_compound": "Carregar composto",
        "btn_save_case": "Salvar Caso",
        "btn_load_case": "Carregar Caso",
        "tab_dash": "Dashboard Executivo",
        "tab_action": "Plano de Ação",
        "tab_whatif": "What-If",
        "tab_compound": "Dados do Composto",
        "tab_hazop": "HAZOP / Bow-Tie",
        "module_exec": "📊 Visão Executiva",
        "module_eng": "🔬 Engenharia de Dados",
        "module_risk": "🛡️ Análise de Risco",
        "module_change": "⚙️ Gestão de Mudança"
    },
    "en": {
        "app_title": "ChemSafe Pro Deterministic",
        "quick_access": "Quick Access",
        "search_compound": "Search compound",
        "load_compound": "Load compound",
        "btn_save_case": "Save Case",
        "btn_load_case": "Load Case",
        "tab_dash": "Executive Dashboard",
        "tab_action": "Action Plan",
        "tab_whatif": "What-If Analysis",
        "tab_compound": "Compound Data",
        "tab_hazop": "HAZOP / Bow-Tie",
        "module_exec": "📊 Executive View",
        "module_eng": "🔬 Data Engineering",
        "module_risk": "🛡️ Risk Analysis",
        "module_change": "⚙️ Change Management"
    }
}

def t(key: str, lang: str = "pt") -> str:
    """Função que busca a tradução. Se não achar, retorna a própria chave."""
    return DICT.get(lang, DICT["pt"]).get(key, key)
