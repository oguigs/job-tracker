{{
    config(
        materialized = 'view',
        description  = 'Empresas normalizadas com plataforma detectada pela URL'
    )
}}

SELECT
    id,
    nome,
    COALESCE(ramo, 'Não informado') AS ramo,
    COALESCE(cidade, '')            AS cidade,
    COALESCE(estado, '')            AS estado,
    url_vagas,
    favicon_url,
    COALESCE(ativa, true)           AS ativa,
    CAST(data_cadastro AS DATE)     AS data_cadastro,

    -- Plataforma inferida pela URL
    CASE
        WHEN url_vagas LIKE '%gupy.io%'            THEN 'Gupy'
        WHEN url_vagas LIKE '%greenhouse.io%'       THEN 'Greenhouse'
        WHEN url_vagas LIKE '%inhire.app%'          THEN 'InHire'
        WHEN url_vagas LIKE '%smartrecruiters.com%' THEN 'SmartRecruiters'
        WHEN url_vagas LIKE '%amazon.jobs%'         THEN 'Amazon Jobs'
        WHEN url_vagas LIKE '%bcg.com%'
          OR url_vagas LIKE '%careers.bcg%'         THEN 'BCG'
        WHEN url_vagas IS NULL OR url_vagas = ''    THEN 'Manual'
        ELSE 'Outro'
    END AS plataforma

FROM {{ source('raw', 'dim_empresa') }}
