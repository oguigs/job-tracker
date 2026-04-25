{{
    config(
        materialized = 'view',
        description  = 'Log de execuções do pipeline com flags de status'
    )
}}

SELECT
    id,
    data_execucao,
    CAST(data_execucao AS DATE)       AS data_execucao_dt,
    empresa,
    COALESCE(vagas_encontradas, 0)    AS vagas_encontradas,
    COALESCE(vagas_novas, 0)          AS vagas_novas,
    status,
    COALESCE(erro, '')                AS erro,

    -- Flags para facilitar agregação
    CASE WHEN status = 'sucesso'   THEN 1 ELSE 0 END AS flag_sucesso,
    CASE WHEN status = 'erro'      THEN 1 ELSE 0 END AS flag_erro,
    CASE WHEN status = 'bloqueado' THEN 1 ELSE 0 END AS flag_bloqueado

FROM {{ source('raw', 'log_coleta') }}
