import duckdb
import os

DB_PATH = "data/curated/jobs.duckdb"

def conectar(read_only=False):
    return duckdb.connect(DB_PATH, read_only=read_only)