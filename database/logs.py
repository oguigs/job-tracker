from datetime import datetime, timezone
from database.connection import db_connect


def registrar_log(empresa: str, encontradas: int, novas: int,
                  status: str, erro: str = ""):
    with db_connect() as con:
        id_log = con.execute("SELECT nextval('seq_log')").fetchone()[0]
        con.execute("""
            INSERT INTO log_coleta (id, data_execucao, empresa, vagas_encontradas, vagas_novas, status, erro)
            VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?)
        """, [id_log, empresa, encontradas, novas, status, erro])


def ultima_execucao_sucesso(nome_empresa: str) -> float:
    with db_connect(read_only=True) as con:
        resultado = con.execute("""
            SELECT data_execucao FROM log_coleta
            WHERE empresa = ? AND status = 'sucesso'
            ORDER BY data_execucao DESC LIMIT 1
        """, [nome_empresa]).fetchone()
    if not resultado or resultado[0] is None:
        return 999
    ultima = resultado[0]
    try:
        if ultima.tzinfo is None:
            ultima = ultima.replace(tzinfo=timezone.utc)
        return round((datetime.now(timezone.utc) - ultima).total_seconds() / 3600, 1)
    except Exception:
        return 999


def empresa_bloqueada(nome_empresa: str) -> bool:
    with db_connect(read_only=True) as con:
        resultado = con.execute("""
            SELECT data_execucao FROM log_coleta
            WHERE empresa = ? AND status = 'bloqueado'
            ORDER BY data_execucao DESC LIMIT 1
        """, [nome_empresa]).fetchone()
    if not resultado:
        return False
    ultima = resultado[0]
    if ultima.tzinfo is None:
        ultima = ultima.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - ultima).total_seconds() / 3600 < 48
