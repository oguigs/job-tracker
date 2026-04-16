from database.connection import conectar

def bronze_to_silver():
    """Normaliza e deduplica dados da camada bronze para silver."""
    con = conectar()

    con.execute("""
        CREATE OR REPLACE VIEW silver.vagas AS
        SELECT
            id,
            hash,
            TRIM(titulo) as titulo,
            LOWER(COALESCE(nivel, 'não identificado')) as nivel,
            LOWER(COALESCE(modalidade, 'não identificado')) as modalidade,
            stacks,
            link,
            fonte,
            id_empresa,
            data_coleta,
            ativa,
            data_encerramento,
            negada,
            candidatura_status,
            urgente,
            regime,
            moeda,
            salario_mensal,
            salario_anual_total
        FROM main.fact_vaga
        WHERE hash IS NOT NULL
    """)

    con.execute("""
        CREATE OR REPLACE VIEW silver.empresas AS
        SELECT
            id,
            TRIM(nome) as nome,
            COALESCE(ramo, 'Não informado') as ramo,
            COALESCE(cidade, 'Não informado') as cidade,
            COALESCE(estado, 'Não informado') as estado,
            url_vagas,
            ativa,
            data_cadastro
        FROM main.dim_empresa
    """)

    con.close()
    print("Silver views criadas")

def silver_to_gold():
    """Cria views analíticas na camada gold."""
    con = conectar()

    con.execute("""
        CREATE OR REPLACE VIEW gold.vagas_ativas AS
        SELECT
            v.id,
            v.titulo,
            v.nivel,
            v.modalidade,
            v.stacks,
            v.data_coleta,
            v.urgente,
            v.candidatura_status,
            e.nome as empresa,
            e.ramo,
            e.cidade
        FROM silver.vagas v
        JOIN silver.empresas e ON v.id_empresa = e.id
        WHERE v.ativa = true
        AND (v.negada = false OR v.negada IS NULL)
    """)

    con.execute("""
        CREATE OR REPLACE VIEW gold.mercado_stacks AS
        SELECT
            stack,
            categoria,
            quantidade,
            data_ref
        FROM main.snapshot_mercado
        ORDER BY data_ref DESC, quantidade DESC
    """)

    con.execute("""
        CREATE OR REPLACE VIEW gold.funil_candidaturas AS
        SELECT
            candidatura_status,
            COUNT(*) as total,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentual
        FROM main.fact_vaga
        WHERE candidatura_status IS NOT NULL
        AND candidatura_status != 'nao_inscrito'
        AND (negada = false OR negada IS NULL)
        GROUP BY candidatura_status
    """)

    con.close()
    print("Gold views criadas")

def criar_camadas():
    bronze_to_silver()
    silver_to_gold()
    print("Medallion architecture criada!")