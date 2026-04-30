"""
components.py — Re-exporta tudo para compatibilidade com imports existentes.
Novos imports devem usar os módulos específicos:
  - from dashboard.data_loaders import carregar_vagas
  - from dashboard.charts import grafico_stacks
  - from dashboard.ui_components import render_vaga_card
"""

import duckdb  # noqa: F401
from database.connection import DB_PATH, conectar  # noqa: F401


def conectar_rw():
    return duckdb.connect(DB_PATH)


from dashboard.data_loaders import (  # noqa: F401
    carregar_vagas,
    carregar_empresas,
    carregar_logs,
    carregar_perfil_empresa,
    calcular_scores_vagas,
)
from dashboard.charts import (  # noqa: F401
    extrair_stacks_flat,
    grafico_stacks,
)
from dashboard.ui_components import (  # noqa: F401
    get_favicon,
    render_stacks,
    render_score_breakdown,
    render_diario,
    render_preparacao_entrevista,
    render_remuneracao,
    render_checklist_preparacao,
    render_vaga_card,
)
