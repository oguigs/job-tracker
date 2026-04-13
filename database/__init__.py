from database.connection import conectar
from database.schemas import criar_tabelas, TIMELINE, TIMELINE_LABELS
from database.empresas import (
    upsert_empresa, listar_empresas_ativas,
    inserir_endereco, listar_enderecos, deletar_endereco, gerar_hash
)
from database.vagas import (
    inserir_vaga, inserir_vaga_manual,
    verificar_vagas_encerradas, listar_vagas_negadas
)
from database.candidaturas import atualizar_candidatura, negar_vaga
from database.contatos import inserir_contato, listar_contatos, deletar_contato
from database.filtros import carregar_filtros, adicionar_filtro, remover_filtro, listar_filtros
from database.logs import registrar_log, ultima_execucao_sucesso