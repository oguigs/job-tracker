import streamlit as st
from database.connection import DB_PATH, db_connect
import duckdb


def conectar_rw():
    return duckdb.connect(DB_PATH)


@st.cache_data(ttl=60)
def carregar_vagas():
    with db_connect(read_only=True) as con:
        return con.execute("""
            SELECT v.id, v.titulo, v.nivel, v.modalidade, v.stacks,
                   v.link, v.fonte, v.data_coleta, v.ativa, v.data_encerramento,
                   v.candidatura_status, v.candidatura_fase, v.candidatura_observacao, v.candidatura_data,
                   v.urgente, v.regime, v.moeda, v.salario_min, v.salario_max,
                   v.salario_anual, v.tem_vr, v.valor_vr, v.tem_va, v.valor_va,
                   v.tem_vt, v.valor_vt, v.outros_beneficios,
                   e.nome AS empresa, e.ramo, e.cidade, e.favicon_url
            FROM fact_vaga v
            JOIN dim_empresa e ON v.id_empresa = e.id
            WHERE v.negada = false OR v.negada IS NULL
            ORDER BY v.data_coleta DESC
        """).df()


@st.cache_data(ttl=60)
def carregar_empresas():
    with db_connect(read_only=True) as con:
        return con.execute("""
            SELECT id, nome, ramo, cidade, estado, url_vagas,
                   url_site_oficial, favicon_url, ativa, data_cadastro
            FROM dim_empresa ORDER BY nome
        """).df()


@st.cache_data(ttl=120)
def carregar_logs():
    with db_connect(read_only=True) as con:
        return con.execute("""
            SELECT empresa, vagas_encontradas, vagas_novas, status, data_execucao
            FROM log_coleta ORDER BY data_execucao DESC LIMIT 10
        """).df()


def carregar_perfil_empresa(nome: str):
    with db_connect(read_only=True) as con:
        empresa = con.execute("""
            SELECT id, nome, ramo, cidade, estado, url_vagas,
                   url_site_oficial, favicon_url, data_cadastro
            FROM dim_empresa WHERE nome = ?
        """, [nome]).df()
        vagas = con.execute("""
            SELECT id, titulo, nivel, modalidade, stacks, link,
                   data_coleta, ativa, candidatura_status
            FROM fact_vaga
            WHERE id_empresa = (SELECT id FROM dim_empresa WHERE nome = ?)
            AND (negada = false OR negada IS NULL)
            ORDER BY data_coleta DESC
        """, [nome]).df()
        logs = con.execute("""
            SELECT vagas_encontradas, vagas_novas, status, data_execucao
            FROM log_coleta WHERE empresa = ?
            ORDER BY data_execucao DESC LIMIT 5
        """, [nome]).df()
        enderecos = con.execute("""
            SELECT cidade, bairro FROM dim_empresa_endereco
            WHERE id_empresa = (SELECT id FROM dim_empresa WHERE nome = ?)
        """, [nome]).fetchall()
    return empresa, vagas, logs, enderecos


@st.cache_data(ttl=120)
def calcular_scores_vagas():
    from database.candidato import carregar_perfil
    from database.score import calcular_scores_todos
    df_perfil = carregar_perfil()
    if df_perfil.empty:
        return {}
    id_candidato = int(df_perfil.iloc[0]["id"])
    return calcular_scores_todos(id_candidato)
