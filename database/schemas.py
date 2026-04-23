import shutil
from database.connection import DB_PATH
import os
from datetime import datetime
from database.connection import conectar

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
    print(f"Backup criado: {destino}")
    backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith(".duckdb")])
    while len(backups) > MAX_BACKUPS:
        os.remove(f"{BACKUP_DIR}/{backups.pop(0)}")

def criar_tabelas():
    fazer_backup()
    con = conectar()

    con.execute("""
        CREATE TABLE IF NOT EXISTS dim_empresa (
            id               INTEGER PRIMARY KEY,
            nome             VARCHAR UNIQUE,
            ramo             VARCHAR,
            cidade           VARCHAR,
            estado           VARCHAR,
            url_vagas         VARCHAR,
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
        CREATE TABLE IF NOT EXISTS fact_vaga (
            id                     INTEGER PRIMARY KEY,
            hash                   VARCHAR UNIQUE,
            titulo                 VARCHAR,
            nivel                  VARCHAR,
            modalidade             VARCHAR,
            stacks                 JSON,
            link                   VARCHAR,
            fonte                  VARCHAR,
            id_empresa             INTEGER,
            data_coleta            DATE DEFAULT current_date,
            ativa                  BOOLEAN DEFAULT true,
            data_encerramento      DATE,
            negada                 BOOLEAN DEFAULT false,
            candidatura_status     VARCHAR DEFAULT 'nao_inscrito',
            candidatura_fase       VARCHAR,
            candidatura_observacao VARCHAR,
            candidatura_data       DATE,
            origem                 VARCHAR,
            contato                VARCHAR
        )
    """)
    con.execute("CREATE SEQUENCE IF NOT EXISTS seq_vaga START 1")

    con.execute("""
        CREATE TABLE IF NOT EXISTS log_coleta (
            id                INTEGER PRIMARY KEY,
            data_execucao     TIMESTAMP DEFAULT current_timestamp,
            empresa           VARCHAR,
            vagas_encontradas INTEGER,
            vagas_novas       INTEGER,
            status            VARCHAR,
            erro              VARCHAR
        )
    """)
    con.execute("CREATE SEQUENCE IF NOT EXISTS seq_log START 1")

    con.execute("""
        CREATE TABLE IF NOT EXISTS dim_empresa_endereco (
            id         INTEGER PRIMARY KEY,
            id_empresa INTEGER,
            cidade     VARCHAR,
            bairro     VARCHAR
        )
    """)
    con.execute("CREATE SEQUENCE IF NOT EXISTS seq_endereco START 1")

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

    print("Tabelas criadas com sucesso")
    con.close()