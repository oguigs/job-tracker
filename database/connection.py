import duckdb
import os
from contextlib import contextmanager

DB_PATH = os.getenv("JOB_TRACKER_DB", "data/curated/jobs.duckdb")


def conectar():
    """Conexão simples — usar preferencialmente o context manager."""
    return duckdb.connect(DB_PATH)


@contextmanager
def db_connect(read_only=False):
    """
    Context manager para conexão DuckDB.
    Nota: read_only ignorado — DuckDB não suporta múltiplas conexões
    com configurações diferentes no mesmo processo.
    """
    con = duckdb.connect(DB_PATH)
    try:
        yield con
    finally:
        con.close()


# alias para compatibilidade
db_connect_rw = db_connect
