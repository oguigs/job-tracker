import duckdb
import json
import hashlib
import shutil
import os
from datetime import date, datetime, timezone

DB_PATH = "data/curated/jobs.duckdb"
BACKUP_DIR = "data/curated/backups"
MAX_BACKUPS = 7


def conectar():
    return duckdb.connect(DB_PATH)


def fazer_backup():
    if not os.path.exists(DB_PATH):
        return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = f"{BACKUP_DIR}/jobs_{timestamp}.duckdb"
    shutil.copy2(DB_PATH, destino)
    print(f"Backup criado: {destino}")

    # mantém apenas os últimos MAX_BACKUPS
    backups = sorted([
        f for f in os.listdir(BACKUP_DIR) if f.endswith(".duckdb")
    ])
    while len(backups) > MAX_BACKUPS:
        os.remove(f"{BACKUP_DIR}/{backups.pop(0)}")


def criar_tabelas():
    fazer_backup()
    con = conectar()

    con.execute("""
        CREATE TABLE IF NOT EXISTS dim_empresa (
            id          INTEGER PRIMARY KEY,
            nome        VARCHAR UNIQUE,
            ramo        VARCHAR,
            cidade      VARCHAR,
            estado      VARCHAR,
            url_gupy    VARCHAR,
            url_linkedin VARCHAR,
            url_site_vagas VARCHAR,
            favicon_url VARCHAR,
            ativa       BOOLEAN DEFAULT true,
            data_cadastro DATE DEFAULT current_date
        )
    """)

    con.execute("CREATE SEQUENCE IF NOT EXISTS seq_empresa START 1")

    con.execute("""
        CREATE TABLE IF NOT EXISTS fact_vaga (
            id              INTEGER PRIMARY KEY,
            hash            VARCHAR UNIQUE,
            titulo          VARCHAR,
            nivel           VARCHAR,
            modalidade      VARCHAR,
            stacks          JSON,
            link            VARCHAR,
            fonte           VARCHAR,
            id_empresa      INTEGER REFERENCES dim_empresa(id),
            data_coleta     DATE DEFAULT current_date,
            ativa           BOOLEAN DEFAULT true,
            data_encerramento DATE,
            negada          BOOLEAN DEFAULT false,
            candidatura_status VARCHAR DEFAULT 'nao_inscrito',
            candidatura_fase VARCHAR,
            candidatura_observacao VARCHAR,
            candidatura_data DATE
        )
    """)

    con.execute("CREATE SEQUENCE IF NOT EXISTS seq_vaga START 1")

    con.execute("""
        CREATE TABLE IF NOT EXISTS log_coleta (
            id              INTEGER PRIMARY KEY,
            data_execucao   TIMESTAMP DEFAULT current_timestamp,
            empresa         VARCHAR,
            vagas_encontradas INTEGER,
            vagas_novas     INTEGER,
            status          VARCHAR,
            erro            VARCHAR
        )
    """)

    con.execute("CREATE SEQUENCE IF NOT EXISTS seq_log START 1")

    con.execute("""
        CREATE TABLE IF NOT EXISTS dim_empresa_endereco (
            id          INTEGER PRIMARY KEY,
            id_empresa  INTEGER REFERENCES dim_empresa(id),
            cidade      VARCHAR,
            bairro      VARCHAR
        )
    """)

    con.execute("CREATE SEQUENCE IF NOT EXISTS seq_endereco START 1")

    con.execute("""
        CREATE TABLE IF NOT EXISTS config_filtros (
            id          INTEGER PRIMARY KEY,
            tipo        VARCHAR,
            termo       VARCHAR,
            data_criacao DATE DEFAULT current_date
        )
    """)

    con.execute("CREATE SEQUENCE IF NOT EXISTS seq_filtro START 1")

    print("Tabelas criadas com sucesso")
    con.close()


def gerar_hash(titulo: str, empresa: str, link: str) -> str:
    conteudo = f"{titulo}{empresa}{link}".lower()
    return hashlib.md5(conteudo.encode()).hexdigest()


def upsert_empresa(nome: str, url_gupy: str, **kwargs) -> int:
    con = conectar()
    resultado = con.execute(
        "SELECT id FROM dim_empresa WHERE nome = ?", [nome]
    ).fetchone()

    if resultado:
        id_empresa = resultado[0]
    else:
        id_empresa = con.execute("SELECT nextval('seq_empresa')").fetchone()[0]

        # gera favicon_url a partir do domínio
        dominio = url_gupy.replace("https://", "").split("/")[0]
        favicon_url = f"https://www.google.com/s2/favicons?domain={dominio}&sz=64"

        con.execute("""
            INSERT INTO dim_empresa
            (id, nome, url_gupy, ramo, cidade, estado, url_linkedin, url_site_vagas, favicon_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            id_empresa, nome, url_gupy,
            kwargs.get("ramo", ""),
            kwargs.get("cidade", ""),
            kwargs.get("estado", ""),
            kwargs.get("url_linkedin", ""),
            kwargs.get("url_site_vagas", ""),
            favicon_url
        ])

    con.close()
    return id_empresa


def inserir_vaga(vaga: dict, id_empresa: int) -> bool:
    con = conectar()
    hash_vaga = gerar_hash(vaga["titulo"], vaga["empresa"], vaga["link"])

    existente = con.execute(
        "SELECT id FROM fact_vaga WHERE hash = ?", [hash_vaga]
    ).fetchone()

    if existente:
        con.close()
        return False

    id_vaga = con.execute("SELECT nextval('seq_vaga')").fetchone()[0]
    con.execute("""
        INSERT INTO fact_vaga (id, hash, titulo, nivel, modalidade, stacks, link, fonte, id_empresa)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        id_vaga, hash_vaga,
        vaga["titulo"],
        vaga.get("nivel", "não identificado"),
        vaga.get("modalidade", "não identificado"),
        json.dumps(vaga.get("stacks", {})),
        vaga["link"],
        vaga["fonte"],
        id_empresa
    ])

    con.close()
    return True


def registrar_log(empresa: str, encontradas: int, novas: int, status: str, erro: str = ""):
    con = conectar()
    id_log = con.execute("SELECT nextval('seq_log')").fetchone()[0]
    con.execute("""
        INSERT INTO log_coleta (id, empresa, vagas_encontradas, vagas_novas, status, erro)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [id_log, empresa, encontradas, novas, status, erro])
    con.close()


def listar_empresas_ativas() -> list:
    con = conectar()
    empresas = con.execute("""
        SELECT nome, url_gupy FROM dim_empresa
        WHERE ativa = true AND url_gupy IS NOT NULL
    """).fetchall()
    con.close()
    return empresas


def verificar_vagas_encerradas(id_empresa: int, links_ativos: list):
    con = conectar()
    vagas_no_banco = con.execute("""
        SELECT id, link, titulo FROM fact_vaga
        WHERE id_empresa = ? AND ativa = true
    """, [id_empresa]).fetchall()

    encerradas = []
    for id_vaga, link, titulo in vagas_no_banco:
        if link not in links_ativos:
            con.execute("""
                UPDATE fact_vaga
                SET ativa = false, data_encerramento = current_date
                WHERE id = ?
            """, [id_vaga])
            encerradas.append(titulo)

    con.close()
    return encerradas


def inserir_endereco(id_empresa: int, cidade: str, bairro: str):
    con = conectar()
    id_end = con.execute("SELECT nextval('seq_endereco')").fetchone()[0]
    con.execute("""
        INSERT INTO dim_empresa_endereco (id, id_empresa, cidade, bairro)
        VALUES (?, ?, ?, ?)
    """, [id_end, id_empresa, cidade, bairro])
    con.close()


def listar_enderecos(id_empresa: int) -> list:
    con = conectar()
    enderecos = con.execute("""
        SELECT id, cidade, bairro FROM dim_empresa_endereco
        WHERE id_empresa = ?
        ORDER BY cidade, bairro
    """, [id_empresa]).fetchall()
    con.close()
    return enderecos


def deletar_endereco(id_endereco: int):
    con = conectar()
    con.execute("DELETE FROM dim_empresa_endereco WHERE id = ?", [id_endereco])
    con.close()


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


def atualizar_candidatura(id_vaga: int, status: str, fase: str = None, observacao: str = None):
    con = conectar()
    con.execute("""
        UPDATE fact_vaga
        SET candidatura_status = ?,
            candidatura_fase = ?,
            candidatura_observacao = ?,
            candidatura_data = current_date
        WHERE id = ?
    """, [status, fase, observacao, id_vaga])
    con.close()


def negar_vaga(id_vaga: int, observacao: str = None):
    con = conectar()
    con.execute("""
        UPDATE fact_vaga
        SET negada = true,
            candidatura_status = 'negado',
            candidatura_fase = candidatura_status,
            candidatura_observacao = ?,
            candidatura_data = current_date
        WHERE id = ?
    """, [observacao, id_vaga])
    con.close()


def listar_vagas_negadas():
    con = conectar()
    df = con.execute("""
        SELECT v.id, v.titulo, v.candidatura_fase, v.candidatura_observacao,
               v.candidatura_data, e.nome AS empresa
        FROM fact_vaga v
        JOIN dim_empresa e ON v.id_empresa = e.id
        WHERE v.negada = true
        ORDER BY v.candidatura_data DESC
    """).df()
    con.close()
    return df


def carregar_filtros():
    con = conectar()
    resultado = con.execute("""
        SELECT tipo, termo FROM config_filtros
        ORDER BY tipo, termo
    """).fetchall()
    con.close()
    interesse = [r[1].lower() for r in resultado if r[0] == "interesse"]
    bloqueio = [r[1].lower() for r in resultado if r[0] == "bloqueio"]
    return interesse, bloqueio


def adicionar_filtro(tipo: str, termo: str):
    con = conectar()
    existente = con.execute(
        "SELECT id FROM config_filtros WHERE tipo = ? AND lower(termo) = lower(?)",
        [tipo, termo]
    ).fetchone()
    if not existente:
        con.execute("""
            INSERT INTO config_filtros VALUES (nextval('seq_filtro'), ?, ?, current_date)
        """, [tipo, termo])
    con.close()


def remover_filtro(id_filtro: int):
    con = conectar()
    con.execute("DELETE FROM config_filtros WHERE id = ?", [id_filtro])
    con.close()


def listar_filtros():
    con = conectar()
    df = con.execute("""
        SELECT id, tipo, termo, data_criacao
        FROM config_filtros
        ORDER BY tipo, termo
    """).df()
    con.close()
    return df


def ultima_execucao_sucesso(nome_empresa: str) -> float:
    con = conectar()
    resultado = con.execute("""
        SELECT data_execucao FROM log_coleta
        WHERE empresa = ? AND status = 'sucesso'
        ORDER BY data_execucao DESC
        LIMIT 1
    """, [nome_empresa]).fetchone()
    con.close()

    if not resultado:
        return 999

    ultima = resultado[0]
    if ultima.tzinfo is None:
        ultima = ultima.replace(tzinfo=timezone.utc)
    agora = datetime.now(timezone.utc)
    return round((agora - ultima).total_seconds() / 3600, 1)

def inserir_vaga_manual(titulo: str, id_empresa: int, empresa_nome: str,
                         descricao: str, origem: str, contato: str) -> int:
    from transformers.stack_extractor import extrair_stacks, detectar_nivel, detectar_modalidade

    stacks = extrair_stacks(descricao)
    nivel = detectar_nivel(titulo)
    modalidade = detectar_modalidade(descricao)

    con = conectar()
    hash_vaga = gerar_hash(titulo, empresa_nome, origem or "manual")

    existente = con.execute(
        "SELECT id FROM fact_vaga WHERE hash = ?", [hash_vaga]
    ).fetchone()

    if existente:
        con.close()
        return existente[0]

    id_vaga = con.execute("SELECT nextval('seq_vaga')").fetchone()[0]
    con.execute("""
        INSERT INTO fact_vaga
        (id, hash, titulo, nivel, modalidade, stacks, link, fonte,
         id_empresa, origem, contato)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        id_vaga, hash_vaga, titulo, nivel, modalidade,
        json.dumps(stacks), origem or "", "manual",
        id_empresa, origem, contato
    ])
    con.close()
    return id_vaga

def inserir_contato(nome: str, email: str, id_empresa: int,
                    grau: str, observacoes: str = "") -> int:
    con = conectar()
    id_contato = con.execute("SELECT nextval('seq_contato')").fetchone()[0]
    con.execute("""
        INSERT INTO dim_contato (id, nome, email, id_empresa, grau, observacoes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [id_contato, nome, email, id_empresa, grau, observacoes])
    con.close()
    return id_contato

def listar_contatos(id_empresa: int = None) -> list:
    con = conectar()
    if id_empresa:
        df = con.execute("""
            SELECT c.id, c.nome, c.email, c.grau, c.observacoes,
                   e.nome AS empresa
            FROM dim_contato c
            JOIN dim_empresa e ON c.id_empresa = e.id
            WHERE c.id_empresa = ?
            ORDER BY c.grau, c.nome
        """, [id_empresa]).df()
    else:
        df = con.execute("""
            SELECT c.id, c.nome, c.email, c.grau, c.observacoes,
                   e.nome AS empresa
            FROM dim_contato c
            JOIN dim_empresa e ON c.id_empresa = e.id
            ORDER BY e.nome, c.grau, c.nome
        """).df()
    con.close()
    return df

def deletar_contato(id_contato: int):
    con = conectar()
    con.execute("DELETE FROM dim_contato WHERE id = ?", [id_contato])
    con.close()


if __name__ == "__main__":
    criar_tabelas()
    print("\nEmpresas cadastradas:")
    con = conectar()
    print(con.execute("SELECT id, nome, url_gupy, ativa FROM dim_empresa").df())
    con.close()