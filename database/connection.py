import duckdb
import os

DB_PATH = "data/curated/jobs.duckdb"

def conectar():
    return duckdb.connect(DB_PATH)