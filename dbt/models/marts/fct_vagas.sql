{{
    config(
        materialized = 'table',
        description  = 'Tabela fato central — vagas com empresa joinada, campos limpos e flags analíticas'
    )
}}

WITH vagas AS (
    SELECT * FROM {{ ref('stg_vagas') }}
),

empresas AS (
    SELECT * FROM {{ ref('stg_empresas') }}
),

ats AS (
    SELECT id_vaga, score_final AS ats_score_final
    FROM {{ source('raw', 'fact_ats_score') }}
)

SELECT
    -- Identificação
    v.id          AS id_vaga,
    v.hash,
    v.titulo,
    v.link,
    v.fonte,

    -- Classificação
    v.nivel,
    v.modalidade,
    v.urgente,
    v.ativa,
    v.data_coleta,
    v.data_encerramento,

    -- Candidatura
    v.candidatura_status,
    v.candidatura_fase,
    v.candidatura_data,
    v.origem,

    -- Remuneração
    v.salario_min,
    v.salario_max,
    v.salario_mensal,
    v.salario_anual_total,

    -- Benefícios
    v.tem_vr,
    v.tem_va,
    v.tem_vt,
    v.tem_plano_saude,
    v.tem_gympass,
    v.tem_bonus,
    v.tem_sal13,
    v.tem_plr,
    v.tem_convenio_medico,
    v.tem_convenio_odonto,
    v.tem_prev_privada,

    -- Empresa (desnormalizada para consultas diretas)
    e.id          AS id_empresa,
    e.nome        AS empresa,
    e.ramo        AS empresa_ramo,
    e.cidade      AS empresa_cidade,
    e.estado      AS empresa_estado,
    e.plataforma,

    -- ATS
    a.ats_score_final,

    -- Flags derivadas
    CASE
        WHEN v.candidatura_status != 'nao_inscrito' THEN true
        ELSE false
    END AS candidatura_iniciada,

    CASE
        WHEN v.candidatura_status IN ('chamado', 'recrutador', 'fase_1', 'fase_2', 'fase_3', 'aprovado')
        THEN true
        ELSE false
    END AS em_processo_ativo,

    CASE
        WHEN v.salario_mensal IS NOT NULL AND v.salario_mensal > 0 THEN true
        ELSE false
    END AS tem_salario_informado,

    -- Contagem de benefícios
    (
        CAST(v.tem_vr AS INTEGER) +
        CAST(v.tem_va AS INTEGER) +
        CAST(v.tem_vt AS INTEGER) +
        CAST(v.tem_plano_saude AS INTEGER) +
        CAST(v.tem_gympass AS INTEGER) +
        CAST(v.tem_bonus AS INTEGER) +
        CAST(v.tem_sal13 AS INTEGER) +
        CAST(v.tem_plr AS INTEGER) +
        CAST(v.tem_convenio_medico AS INTEGER) +
        CAST(v.tem_convenio_odonto AS INTEGER) +
        CAST(v.tem_prev_privada AS INTEGER)
    ) AS qtd_beneficios

FROM vagas v
LEFT JOIN empresas e ON v.id_empresa = e.id
LEFT JOIN ats a ON v.id = a.id_vaga
