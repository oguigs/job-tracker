from database.connection import conectar
from datetime import datetime, timezone

def registrar_log(empresa: str, encontradas: int, novas: int,
                  status: str, erro: str = ""):
    con = conectar()
    id_log = con.execute("SELECT nextval('seq_log')").fetchone()[0]
    con.execute("""
        INSERT INTO log_coleta (id, data_execucao, empresa, vagas_encontradas, vagas_novas, status, erro)
        VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?)
    """, [id_log, empresa, encontradas, novas, status, erro])
    con.close()

def ultima_execucao_sucesso(nome_empresa: str) -> float:
    con = conectar()
    resultado = con.execute("""
        SELECT data_execucao FROM log_coleta
        WHERE empresa = ? AND status = 'sucesso'
        ORDER BY data_execucao DESC LIMIT 1
    """, [nome_empresa]).fetchone()
    con.close()
    if not resultado or resultado[0] is None:
        return 999
    ultima = resultado[0]
    try:
        from datetime import datetime, timezone
        if ultima.tzinfo is None:
            ultima = ultima.replace(tzinfo=timezone.utc)
        agora = datetime.now(timezone.utc)
        return round((agora - ultima).total_seconds() / 3600, 1)
    except Exception:
        return 999
    
def empresa_bloqueada(nome_empresa: str) -> bool:
    """Verifica se empresa foi bloqueada nas últimas 48h."""
    con = conectar()
    resultado = con.execute("""
        SELECT data_execucao FROM log_coleta
        WHERE empresa = ? AND status = 'bloqueado'
        ORDER BY data_execucao DESC LIMIT 1
    """, [nome_empresa]).fetchone()
    con.close()
    if not resultado:
        return False
    from datetime import datetime, timezone
    ultima = resultado[0]
    if ultima.tzinfo is None:
        ultima = ultima.replace(tzinfo=timezone.utc)
    horas = (datetime.now(timezone.utc) - ultima).total_seconds() / 3600
    return horas < 48    