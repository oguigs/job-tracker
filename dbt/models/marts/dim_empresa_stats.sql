{{
    config(
        materialized = 'table',
        description  = 'Empresas com estatísticas agregadas de vagas, pipeline e candidaturas'
    )
}}

WITH empresas AS (
    SELECT * FROM {{ ref('stg_empresas') }}
),

vagas AS (
    SELECT * FROM {{ ref('stg_vagas') }}
),

log AS (
    SELECT * FROM {{ ref('stg_log_coleta') }}
),

vagas_stats AS (
    SELECT
        id_empresa,
        COUNT(*)                                                    AS total_vagas,
        COUNT(CASE WHEN ativa THEN 1 END)                          AS vagas_ativas,
        COUNT(CASE WHEN candidatura_status != 'nao_inscrito' THEN 1 END) AS candidaturas,
        COUNT(CASE WHEN urgente THEN 1 END)                        AS vagas_urgentes,
        MAX(data_coleta)                                            AS ultima_coleta,
        -- Nível
        COUNT(CASE WHEN nivel = 'junior'       THEN 1 END)         AS vagas_junior,
        COUNT(CASE WHEN nivel = 'pleno'        THEN 1 END)         AS vagas_pleno,
        COUNT(CASE WHEN nivel = 'senior'       THEN 1 END)         AS vagas_senior,
        COUNT(CASE WHEN nivel = 'especialista' THEN 1 END)         AS vagas_especialista,
        -- Modalidade
        COUNT(CASE WHEN modalidade = 'remoto'     THEN 1 END)      AS vagas_remoto,
        COUNT(CASE WHEN modalidade = 'hibrido'    THEN 1 END)      AS vagas_hibrido,
        COUNT(CASE WHEN modalidade = 'presencial' THEN 1 END)      AS vagas_presencial,
        -- Salário médio quando informado
        ROUND(AVG(CASE WHEN salario_mensal > 0 THEN salario_mensal END), 0) AS salario_medio_mensal
    FROM vagas
    GROUP BY id_empresa
),

pipeline_stats AS (
    SELECT
        empresa,
        COUNT(*)                                    AS total_execucoes,
        SUM(flag_sucesso)                           AS execucoes_sucesso,
        SUM(flag_erro)                              AS execucoes_erro,
        SUM(flag_bloqueado)                         AS execucoes_bloqueado,
        ROUND(
            100.0 * SUM(flag_sucesso) / NULLIF(COUNT(*), 0), 1
        )                                           AS taxa_sucesso_pct,
        MAX(data_execucao)                          AS ultima_execucao
    FROM log
    GROUP BY empresa
)

SELECT
    e.id,
    e.nome,
    e.ramo,
    e.cidade,
    e.estado,
    e.plataforma,
    e.url_vagas,
    e.favicon_url,
    e.ativa,
    e.data_cadastro,

    -- Vagas
    COALESCE(vs.total_vagas, 0)        AS total_vagas,
    COALESCE(vs.vagas_ativas, 0)       AS vagas_ativas,
    COALESCE(vs.candidaturas, 0)       AS candidaturas,
    COALESCE(vs.vagas_urgentes, 0)     AS vagas_urgentes,
    vs.ultima_coleta,
    vs.salario_medio_mensal,

    -- Nível breakdown
    COALESCE(vs.vagas_junior, 0)       AS vagas_junior,
    COALESCE(vs.vagas_pleno, 0)        AS vagas_pleno,
    COALESCE(vs.vagas_senior, 0)       AS vagas_senior,
    COALESCE(vs.vagas_especialista, 0) AS vagas_especialista,

    -- Modalidade breakdown
    COALESCE(vs.vagas_remoto, 0)       AS vagas_remoto,
    COALESCE(vs.vagas_hibrido, 0)      AS vagas_hibrido,
    COALESCE(vs.vagas_presencial, 0)   AS vagas_presencial,

    -- Pipeline health
    COALESCE(ps.total_execucoes, 0)    AS pipeline_execucoes,
    COALESCE(ps.execucoes_sucesso, 0)  AS pipeline_sucessos,
    COALESCE(ps.execucoes_erro, 0)     AS pipeline_erros,
    COALESCE(ps.taxa_sucesso_pct, 0)   AS pipeline_taxa_sucesso_pct,
    ps.ultima_execucao

FROM empresas e
LEFT JOIN vagas_stats vs     ON e.id = vs.id_empresa
LEFT JOIN pipeline_stats ps  ON e.nome = ps.empresa
