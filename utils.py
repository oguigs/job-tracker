"""
Utilitários globais do Job Tracker.
Centraliza tratamento de NA, strings e tipos para evitar repetição.
"""

NA_VALUES = {'nan', 'none', '<na>', 'nat', 'null', ''}


def safe_bool(val: object) -> bool:
    """Converte valor pandas/python para bool seguro."""
    if val is None:
        return False
    return str(val).strip().lower() not in {'false', '0', 'nan', 'none', '<na>', 'nat', ''}


def safe_str(val: object, default: str = '') -> str:
    """Converte valor para string segura, retorna default se NA."""
    if val is None:
        return default
    s = str(val).strip()
    return default if s.lower() in NA_VALUES else s


def safe_int(val: object, default: int = 0) -> int:
    """Converte valor para int seguro."""
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def nivel_fmt(val: object) -> str:
    """Formata nível para exibição."""
    s = safe_str(val, '—')
    return '—' if s.lower() in {'não identificado', 'nao identificado'} else s


def modal_fmt(val: object) -> str:
    """Formata modalidade para exibição."""
    s = safe_str(val, '—')
    return '—' if s.lower() in {'não identificado', 'nao identificado'} else s


def data_fmt(val: object) -> str:
    """Formata data para exibição."""
    s = safe_str(val, 'N/A')
    return s[:10] if len(s) >= 10 else 'N/A'


def status_badge(status_cand: str, is_nova: bool) -> tuple[str, str]:
    """
    Retorna (label, cor) para badge de status da vaga.
    """
    if status_cand not in ('nao_inscrito', None, ''):
        if status_cand == 'inscrito':
            return 'Inscrito', '#1D9E75'
        return 'Em processo', '#F0C040'
    if is_nova:
        return 'Novo', '#E8A020'
    return 'Não inscrito', '#378ADD'

# re-exporta do theme para compatibilidade
def cor_score(score: int) -> str:
    from dashboard.theme import cor_score as _cor_score
    return _cor_score(score)
