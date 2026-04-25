{{
    config(
        materialized = 'table',
        description  = 'Stacks extraídas e unnestadas do JSON — ranking por categoria e nível de senioridade'
    )
}}

WITH vagas_com_stacks AS (
    SELECT
        id,
        data_coleta,
        nivel,
        stacks
    FROM {{ ref('stg_vagas') }}
    WHERE stacks IS NOT NULL AND stacks != '' AND stacks != '{}'
),

-- Unnest cada categoria de stack separadamente
linguagens AS (
    SELECT id, data_coleta, nivel, 'linguagens' AS categoria,
           UNNEST(TRY_CAST(json_extract(stacks, '$.linguagens') AS VARCHAR[])) AS stack
    FROM vagas_com_stacks
),
cloud AS (
    SELECT id, data_coleta, nivel, 'cloud' AS categoria,
           UNNEST(TRY_CAST(json_extract(stacks, '$.cloud') AS VARCHAR[])) AS stack
    FROM vagas_com_stacks
),
processamento AS (
    SELECT id, data_coleta, nivel, 'processamento' AS categoria,
           UNNEST(TRY_CAST(json_extract(stacks, '$.processamento') AS VARCHAR[])) AS stack
    FROM vagas_com_stacks
),
orquestracao AS (
    SELECT id, data_coleta, nivel, 'orquestracao' AS categoria,
           UNNEST(TRY_CAST(json_extract(stacks, '$.orquestracao') AS VARCHAR[])) AS stack
    FROM vagas_com_stacks
),
armazenamento AS (
    SELECT id, data_coleta, nivel, 'armazenamento' AS categoria,
           UNNEST(TRY_CAST(json_extract(stacks, '$.armazenamento') AS VARCHAR[])) AS stack
    FROM vagas_com_stacks
),
infraestrutura AS (
    SELECT id, data_coleta, nivel, 'infraestrutura' AS categoria,
           UNNEST(TRY_CAST(json_extract(stacks, '$.infraestrutura') AS VARCHAR[])) AS stack
    FROM vagas_com_stacks
),
visualizacao AS (
    SELECT id, data_coleta, nivel, 'visualizacao' AS categoria,
           UNNEST(TRY_CAST(json_extract(stacks, '$.visualizacao') AS VARCHAR[])) AS stack
    FROM vagas_com_stacks
),
ml_ia AS (
    SELECT id, data_coleta, nivel, 'ml_ia' AS categoria,
           UNNEST(TRY_CAST(json_extract(stacks, '$.ml_ia') AS VARCHAR[])) AS stack
    FROM vagas_com_stacks
),

all_stacks AS (
    SELECT * FROM linguagens
    UNION ALL SELECT * FROM cloud
    UNION ALL SELECT * FROM processamento
    UNION ALL SELECT * FROM orquestracao
    UNION ALL SELECT * FROM armazenamento
    UNION ALL SELECT * FROM infraestrutura
    UNION ALL SELECT * FROM visualizacao
    UNION ALL SELECT * FROM ml_ia
)

SELECT
    lower(stack)                                                 AS stack,
    categoria,
    COUNT(*)                                                     AS total_vagas,
    COUNT(CASE WHEN nivel = 'junior'       THEN 1 END)          AS vagas_junior,
    COUNT(CASE WHEN nivel = 'pleno'        THEN 1 END)          AS vagas_pleno,
    COUNT(CASE WHEN nivel = 'senior'       THEN 1 END)          AS vagas_senior,
    COUNT(CASE WHEN nivel = 'especialista' THEN 1 END)          AS vagas_especialista,
    MAX(data_coleta)                                             AS ultima_aparicao,
    MIN(data_coleta)                                             AS primeira_aparicao
FROM all_stacks
WHERE stack IS NOT NULL AND stack != ''
GROUP BY lower(stack), categoria
ORDER BY total_vagas DESC
