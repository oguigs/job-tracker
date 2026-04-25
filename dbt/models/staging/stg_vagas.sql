{{
    config(
        materialized = 'view',
        description  = 'Vagas normalizadas — modalidade e nível padronizados, nulls tratados'
    )
}}

SELECT
    id,
    hash,
    titulo,

    -- Nível padronizado
    CASE
        WHEN lower(nivel) IN ('senior', 'sênior', 'sr', 'sr.')   THEN 'senior'
        WHEN lower(nivel) IN ('pleno', 'pl', 'pl.')               THEN 'pleno'
        WHEN lower(nivel) IN ('junior', 'júnior', 'jr', 'jr.')    THEN 'junior'
        WHEN lower(nivel) = 'especialista'                         THEN 'especialista'
        WHEN lower(nivel) = 'lead'                                 THEN 'lead'
        ELSE 'não identificado'
    END AS nivel,

    -- Modalidade padronizada (unifica híbrido/hibrido)
    CASE
        WHEN lower(modalidade) IN ('hibrido', 'híbrido', 'hybrid') THEN 'hibrido'
        WHEN lower(modalidade) IN ('remoto', 'remote', '100% remote', 'fully remote') THEN 'remoto'
        WHEN lower(modalidade) IN ('presencial', 'on-site', 'on site') THEN 'presencial'
        ELSE 'não identificado'
    END AS modalidade,

    stacks,
    COALESCE(descricao, '')      AS descricao,
    link,
    COALESCE(fonte, 'desconhecida') AS fonte,
    id_empresa,
    CAST(data_coleta AS DATE)    AS data_coleta,
    COALESCE(ativa, true)        AS ativa,
    data_encerramento,
    COALESCE(negada, false)      AS negada,
    COALESCE(urgente, false)     AS urgente,
    COALESCE(candidatura_status, 'nao_inscrito') AS candidatura_status,
    candidatura_fase,
    candidatura_data,
    origem,
    salario_min,
    salario_max,
    salario_mensal,
    salario_anual_total,
    COALESCE(tem_vr, false)            AS tem_vr,
    COALESCE(tem_va, false)            AS tem_va,
    COALESCE(tem_vt, false)            AS tem_vt,
    COALESCE(tem_plano_saude, false)   AS tem_plano_saude,
    COALESCE(tem_gympass, false)       AS tem_gympass,
    COALESCE(tem_bonus, false)         AS tem_bonus,
    COALESCE(tem_sal13, false)         AS tem_sal13,
    COALESCE(tem_plr, false)           AS tem_plr,
    COALESCE(tem_convenio_medico, false)  AS tem_convenio_medico,
    COALESCE(tem_convenio_odonto, false)  AS tem_convenio_odonto,
    COALESCE(tem_prev_privada, false)     AS tem_prev_privada

FROM {{ source('raw', 'fact_vaga') }}
WHERE COALESCE(negada, false) = false
