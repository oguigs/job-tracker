from logger import get_logger

log = get_logger("migrations")
"""
migrations.py — Corrige tipos errados no banco existente.
Seguro para rodar múltiplas vezes (idempotente).
"""
from database.connection import db_connect


def migrar_v1_tipos_fact_vaga():
    """
    Corrige colunas criadas sem tipo explícito via ALTER TABLE
    que o DuckDB inferiu como INTEGER ou BOOLEAN incorretamente.
    """
    correcoes = [
        ("origem", "VARCHAR"),
        ("contato", "VARCHAR"),
        ("regime", "VARCHAR"),
        ("moeda", "VARCHAR"),
        ("outros_beneficios", "VARCHAR"),
        ("salario_anual", "INTEGER"),
    ]

    with db_connect() as con:
        info = con.execute("PRAGMA table_info(fact_vaga)").fetchall()
        tipos_atuais = {row[1]: row[2] for row in info}

        for coluna, tipo_correto in correcoes:
            tipo_atual = tipos_atuais.get(coluna)
            if tipo_atual and tipo_atual != tipo_correto:
                log.info(f"  Migrando {coluna}: {tipo_atual} → {tipo_correto}")
                try:
                    con.execute(f"""
                        ALTER TABLE fact_vaga
                        ALTER COLUMN {coluna} SET DATA TYPE {tipo_correto}
                        USING CAST({coluna} AS {tipo_correto})
                    """)
                    log.info(f"  ✓ {coluna} migrado")
                except Exception as e:
                    log.error(f"  ✗ {coluna} erro: {e}")
            else:
                log.info(f"  ✓ {coluna} já está correto ({tipo_atual})")


def migrar_v2_adicionar_colunas_faltantes():
    """
    Adiciona colunas que existem no código mas não no banco.
    """
    with db_connect() as con:
        info = con.execute("PRAGMA table_info(fact_vaga)").fetchall()
        colunas_existentes = {row[1] for row in info}

        novas_colunas = [
            ("data_coleta", "DATE DEFAULT current_date"),
            ("descricao", "VARCHAR"),
        ]

        for coluna, definicao in novas_colunas:
            if coluna not in colunas_existentes:
                log.info(f"  Adicionando {coluna}...")
                con.execute(f"ALTER TABLE fact_vaga ADD COLUMN {coluna} {definicao}")
                log.info(f"  ✓ {coluna} adicionada")


def rodar_migracoes():
    """Ponto de entrada — roda todas as migrações em ordem."""
    log.info("=== Iniciando migrações ===")
    log.info("\n[v1] Corrigindo tipos de fact_vaga...")
    migrar_v1_tipos_fact_vaga()
    log.info("\n[v2] Verificando colunas faltantes...")
    migrar_v2_adicionar_colunas_faltantes()
    log.info("\n[v3] Corrigindo tipos de dim_contato...")
    migrar_v3_tipos_dim_contato()
    log.info("\n[v4] Corrigindo tipos de log_candidatura...")
    migrar_v4_tipos_log_candidatura()
    log.info("\n=== Migrações concluídas ===")


if __name__ == "__main__":
    rodar_migracoes()


def migrar_v3_tipos_dim_contato():
    """Corrige colunas VARCHAR criadas como INTEGER em dim_contato."""
    correcoes = [
        ("nome", "VARCHAR"),
        ("email", "VARCHAR"),
        ("grau", "VARCHAR"),
        ("observacoes", "VARCHAR"),
    ]
    with db_connect() as con:
        info = con.execute("PRAGMA table_info(dim_contato)").fetchall()
        tipos_atuais = {row[1]: row[2] for row in info}
        for coluna, tipo_correto in correcoes:
            tipo_atual = tipos_atuais.get(coluna)
            if tipo_atual and tipo_atual != tipo_correto:
                log.info(f"  Migrando dim_contato.{coluna}: {tipo_atual} → {tipo_correto}")
                con.execute(f"""
                    ALTER TABLE dim_contato
                    ALTER COLUMN {coluna} SET DATA TYPE {tipo_correto}
                    USING CAST({coluna} AS {tipo_correto})
                """)
                log.info(f"  ✓ {coluna} migrado")
            else:
                log.info(f"  ✓ {coluna} já correto")


def migrar_v4_tipos_log_candidatura():
    """Corrige nota de INTEGER para VARCHAR em log_candidatura."""
    with db_connect() as con:
        info = con.execute("PRAGMA table_info(log_candidatura)").fetchall()
        tipos_atuais = {row[1]: row[2] for row in info}
        if tipos_atuais.get("nota") != "VARCHAR":
            log.info("  Migrando log_candidatura.nota: INTEGER → VARCHAR")
            con.execute("""
                ALTER TABLE log_candidatura
                ALTER COLUMN nota SET DATA TYPE VARCHAR
                USING CAST(nota AS VARCHAR)
            """)
            log.info("  ✓ nota migrado")
        else:
            log.info("  ✓ nota já correto")
