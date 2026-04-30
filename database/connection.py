import duckdb
import os
from contextlib import contextmanager

DB_PATH = os.getenv("JOB_TRACKER_DB", "data/curated/jobs.duckdb")


def conectar(read_only=False):
    """Conexão simples — usar preferencialmente o context manager."""
    return duckdb.connect(DB_PATH, read_only=read_only)


@contextmanager
def db_connect(read_only=False):
    """
    Context manager para conexão DuckDB.
    Garante que a conexão seja fechada mesmo em caso de erro.

    Uso:
        with db_connect() as con:
            df = con.execute("SELECT ...").df()
    """
    con = duckdb.connect(DB_PATH, read_only=read_only)
    try:
        yield con
    finally:
        con.close()


@contextmanager
def db_connect_rw():
    """Context manager para conexão de leitura e escrita."""
    con = duckdb.connect(DB_PATH, read_only=False)
    try:
        yield con
    finally:
        con.close()
