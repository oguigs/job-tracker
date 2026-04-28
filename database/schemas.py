from logger import get_logger
log = get_logger("schemas")
import shutil
from database.connection import DB_PATH
import os
from datetime import datetime
from database.connection import conectar, db_connect

BACKUP_DIR = "data/curated/backups"
MAX_BACKUPS = 7

TIMELINE = [
    "nao_inscrito", "inscrito", "chamado", "recrutador",
    "fase_1", "fase_2", "fase_3", "aprovado", "reprovado", "negado"
]

TIMELINE_LABELS = {
    "nao_inscrito": "Não inscrito",
    "inscrito":     "Inscrito",
    "chamado":      "Chamado",
    "recrutador":   "Entrevista RH",
    "fase_1":       "Fase 1",
    "fase_2":       "Fase 2",
    "fase_3":       "Fase 3",
    "aprovado":     "Aprovado",
    "reprovado":    "Reprovado",
    "negado":       "Negado"
}

def fazer_backup():
    if not os.path.exists(DB_PATH):
        return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = f"{BACKUP_DIR}/jobs_{timestamp}.duckdb"
    shutil.copy2(DB_PATH, destino)
    log.info(f"Backup criado: {destino}")
    backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith(".duckdb")])
    while len(backups) > MAX_BACKUPS:
        os.remove(f"{BACKUP_DIR}/{backups.pop(0)}")

def criar_tabelas():
    fazer_backup()
    con = conectar()
    try:
        con.execute("""
            CREATE TABLE IF NOT EXISTS dim_empresa (
                id               INTEGER PRIMARY KEY,
                nome             VARCHAR UNIQUE,
                ramo             VARCHAR,
                cidade           VARCHAR,
                estado           VARCHAR,
                url_vagas        VARCHAR,
                url_linkedin     VARCHAR,
                url_site_vagas   VARCHAR,
                url_site_oficial VARCHAR,
                favicon_url      VARCHAR,
                ativa            BOOLEAN DEFAULT true,
                data_cadastro    DATE DEFAULT current_date
            )
        """)
        con.execute("CREATE SEQUENCE IF NOT EXISTS seq_empresa START 1")

        con.execute("""
            CREATE TABLE IF NOT EXISTS dim_empresa_endereco (
                id          INTEGER PRIMARY KEY,
                id_empresa  INTEGER,
                cidade      VARCHAR,
                bairro      VARCHAR
            )
        """)
        con.execute("CREATE SEQUENCE IF NOT EXISTS seq_endereco START 1")

        con.execute("""
            CREATE TABLE IF NOT EXISTS fact_vaga (
                id                     INTEGER PRIMARY KEY,
                hash                   VARCHAR UNIQUE,
                titulo                 VARCHAR,
                nivel                  VARCHAR,
                modalidade             VARCHAR,
                stacks                 VARCHAR,
                descricao              VARCHAR,
                link                   VARCHAR,
                fonte                  VARCHAR,
                id_empresa             INTEGER,
                data_coleta            DATE DEFAULT current_date,
                ativa                  BOOLEAN DEFAULT true,
                data_encerramento      DATE,
                negada                 BOOLEAN DEFAULT false,
                urgente                BOOLEAN DEFAULT false,
                candidatura_status     VARCHAR DEFAULT 'nao_inscrito',
                candidatura_fase       VARCHAR,
                candidatura_observacao VARCHAR,
                candidatura_data       DATE,
                origem                 VARCHAR,
                contato                VARCHAR,
                regime                 VARCHAR,
                moeda                  VARCHAR,
                salario_min            INTEGER,
                salario_max            INTEGER,
                salario_mensal         INTEGER,
                salario_anual_total    INTEGER,
                tem_vr                 BOOLEAN DEFAULT false,
                valor_vr               INTEGER,
                tem_va                 BOOLEAN DEFAULT false,
                valor_va               INTEGER,
                tem_vt                 BOOLEAN DEFAULT false,
                valor_vt               INTEGER,
                tem_plano_saude        BOOLEAN DEFAULT false,
                tem_gympass            BOOLEAN DEFAULT false,
                tem_convenio_medico    BOOLEAN DEFAULT false,
                tem_convenio_odonto    BOOLEAN DEFAULT false,
                tem_prev_privada       BOOLEAN DEFAULT false,
                outros_beneficios      VARCHAR,
                tem_sal13              BOOLEAN DEFAULT false,
                tem_plr                BOOLEAN DEFAULT false,
                valor_plr              INTEGER,
                tem_bonus              BOOLEAN DEFAULT false,
                valor_bonus            INTEGER
            )
        """)
        con.execute("CREATE SEQUENCE IF NOT EXISTS seq_vaga START 1")
        con.execute("ALTER TABLE fact_vaga ADD COLUMN IF NOT EXISTS historico_fases VARCHAR")

        con.execute("""
            CREATE TABLE IF NOT EXISTS dim_candidato (
                id               INTEGER PRIMARY KEY,
                nome             VARCHAR,
                email            VARCHAR,
                linkedin         VARCHAR,
                cidade           VARCHAR,
                nivel            VARCHAR,
                modalidade_pref  VARCHAR,
                pretensao_min    INTEGER,
                pretensao_max    INTEGER,
                resumo           VARCHAR,
                curriculo_texto  VARCHAR,
                data_atualizacao DATE DEFAULT current_date
            )
        """)
        try:
            con.execute("ALTER TABLE dim_candidato ADD COLUMN IF NOT EXISTS curriculo_texto VARCHAR")
        except Exception:
            pass
        con.execute("CREATE SEQUENCE IF NOT EXISTS seq_candidato START 1")

        con.execute("""
            CREATE TABLE IF NOT EXISTS fact_ats_score (
                id                 INTEGER PRIMARY KEY,
                id_vaga            INTEGER UNIQUE,
                score_keywords     INTEGER,
                score_formatacao   INTEGER,
                score_secoes       INTEGER,
                score_impacto      INTEGER,
                score_final        INTEGER,
                keywords_ausentes  VARCHAR,
                keywords_presentes VARCHAR,
                data_calculo       DATE DEFAULT current_date
            )
        """)
        con.execute("CREATE SEQUENCE IF NOT EXISTS seq_ats_score START 1")

        con.execute("""
            CREATE TABLE IF NOT EXISTS dim_candidato_stack (
                id           INTEGER PRIMARY KEY,
                id_candidato INTEGER,
                stack        VARCHAR,
                categoria    VARCHAR,
                nivel_stack  VARCHAR,
                anos_exp     INTEGER
            )
        """)
        con.execute("CREATE SEQUENCE IF NOT EXISTS seq_candidato_stack START 1")

        con.execute("""
            CREATE TABLE IF NOT EXISTS dim_contato (
                id            INTEGER PRIMARY KEY,
                nome          VARCHAR,
                email         VARCHAR,
                id_empresa    INTEGER,
                grau          VARCHAR,
                observacoes   VARCHAR,
                data_cadastro DATE DEFAULT current_date
            )
        """)
        con.execute("CREATE SEQUENCE IF NOT EXISTS seq_contato START 1")

        con.execute("""
            CREATE TABLE IF NOT EXISTS log_coleta (
                id                INTEGER PRIMARY KEY,
                data_execucao     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                empresa           VARCHAR,
                vagas_encontradas INTEGER,
                vagas_novas       INTEGER,
                status            VARCHAR,
                erro              VARCHAR
            )
        """)
        con.execute("CREATE SEQUENCE IF NOT EXISTS seq_log START 1")

        con.execute("""
            CREATE TABLE IF NOT EXISTS log_candidatura (
                id        INTEGER PRIMARY KEY,
                id_vaga   INTEGER,
                data_nota DATE DEFAULT current_date,
                nota      VARCHAR
            )
        """)
        con.execute("CREATE SEQUENCE IF NOT EXISTS seq_log_candidatura START 1")

        con.execute("""
            CREATE TABLE IF NOT EXISTS config_filtros (
                id           INTEGER PRIMARY KEY,
                tipo         VARCHAR,
                termo        VARCHAR,
                data_criacao DATE DEFAULT current_date
            )
        """)
        con.execute("CREATE SEQUENCE IF NOT EXISTS seq_filtro START 1")

        con.execute("""
            CREATE TABLE IF NOT EXISTS snapshot_mercado (
                id         INTEGER PRIMARY KEY,
                data_ref   DATE DEFAULT current_date,
                stack      VARCHAR,
                categoria  VARCHAR,
                quantidade INTEGER
            )
        """)
        con.execute("CREATE SEQUENCE IF NOT EXISTS seq_snapshot START 1")

    finally:
        con.close()
    log.info("Tabelas criadas com sucesso")
