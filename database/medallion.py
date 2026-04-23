from database.connection import db_connect


def bronze_to_silver():
    """Normaliza e deduplica dados da camada bronze para silver."""
    with db_connect() as con:
        con.execute("""
            CREATE OR REPLACE VIEW silver_vagas AS
            SELECT
                id, hash,
                TRIM(titulo) as titulo,
                LOWER(COALESCE(nivel, 'não identificado')) as nivel,
                LOWER(COALESCE(modalidade, 'não identificado')) as modalidade,
                stacks, link, fonte, id_empresa,
                data_coleta, ativa, negada,
                candidatura_status, candidatura_data
            FROM fact_vaga
            WHERE negada = false OR negada IS NULL
        """)


def silver_to_gold():
    """Agrega dados para camada gold — pronta para o dashboard."""
    with db_connect() as con:
        con.execute("""
            CREATE OR REPLACE VIEW gold_vagas AS
            SELECT
                v.id, v.titulo, v.nivel, v.modalidade,
                v.stacks, v.link, v.data_coleta,
                v.candidatura_status,
                e.nome AS empresa, e.favicon_url
            FROM silver_vagas v
            JOIN dim_empresa e ON v.id_empresa = e.id
        """)
        con.execute("""
            CREATE OR REPLACE VIEW gold_empresas_ativas AS
            SELECT id, nome, url_vagas, favicon_url
            FROM dim_empresa
            WHERE ativa = true AND url_vagas IS NOT NULL
        """)


def criar_views_medallion():
    bronze_to_silver()
    silver_to_gold()
    print("Views Medallion criadas: silver_vagas, gold_vagas, gold_empresas_ativas")
