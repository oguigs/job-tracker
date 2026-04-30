"""
theme.py — Paleta de cores centralizada do Job Tracker.
Importar daqui em vez de usar strings hardcoded nos arquivos.
"""

# Cores principais
COR_SUCESSO = "#1D9E75"  # verde — match, inscrito, ativo
COR_INFO = "#378ADD"  # azul — não inscrito, info
COR_PERIGO = "#D85A30"  # laranja escuro — erro, reprovado
COR_ALERTA = "#BA7517"  # âmbar — score médio, atenção
COR_NEUTRO = "#767676"  # cinza — texto auxiliar (passa WCAG AA)

# Badges de status — progressão funil: cinza → azul → verde → âmbar
COR_PENDENTE = "#64748B"  # cinza-ardósia — inerte, sem ação
COR_NOVO = "#2563EB"  # azul — informativo, vaga recém-postada
COR_INSCRITO = "#059669"  # verde esmeralda — ação concluída
COR_PROCESSO = "#D97706"  # âmbar — ativo, em andamento

# Fundos suaves
COR_FUNDO_SUCESSO = "#E8F5F0"
COR_FUNDO_PERIGO = "#FBF0EB"
COR_FUNDO_ALERTA = "#FFF8E1"
COR_FUNDO_INFO = "#EBF3FB"


# Score de fit
def cor_score(score: int) -> str:
    """Retorna cor baseada no score de fit."""
    if score >= 70:
        return COR_SUCESSO
    if score >= 40:
        return COR_ALERTA
    return COR_NEUTRO


# Badge de status
def status_badge(status_cand: str, is_nova: bool) -> tuple[str, str]:
    """Retorna (label, cor) para badge de status da vaga."""
    if status_cand not in ("nao_inscrito", None, ""):
        if status_cand == "inscrito":
            return "Inscrito", COR_INSCRITO
        return "Em processo", COR_PROCESSO
    if is_nova:
        return "Novo", COR_NOVO
    return "Pendente", COR_PENDENTE
