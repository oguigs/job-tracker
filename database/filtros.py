from database.connection import db_connect


def carregar_filtros():
    with db_connect() as con:
        resultado = con.execute(
            "SELECT tipo, termo FROM config_filtros ORDER BY tipo, termo"
        ).fetchall()
    interesse = [r[1].lower() for r in resultado if r[0] == "interesse"]
    bloqueio = [r[1].lower() for r in resultado if r[0] == "bloqueio"]
    return interesse, bloqueio


def adicionar_filtro(tipo: str, termo: str):
    with db_connect() as con:
        existente = con.execute(
            "SELECT id FROM config_filtros WHERE tipo = ? AND lower(termo) = lower(?)",
            [tipo, termo],
        ).fetchone()
        if not existente:
            con.execute(
                "INSERT INTO config_filtros VALUES (nextval('seq_filtro'), ?, ?, current_date)",
                [tipo, termo],
            )


def remover_filtro(id_filtro: int):
    with db_connect() as con:
        con.execute("DELETE FROM config_filtros WHERE id = ?", [id_filtro])


def listar_filtros():
    with db_connect() as con:
        return con.execute(
            "SELECT id, tipo, termo, data_criacao FROM config_filtros ORDER BY tipo, termo"
        ).df()


def carregar_filtros_localizacao():
    with db_connect() as con:
        df = con.execute("""
            SELECT tipo, termo FROM config_filtros
            WHERE tipo IN ('pais_permitido', 'pais_bloqueado', 'cidade_permitida', 'cidade_bloqueada')
        """).df()
    permitidos = df[df["tipo"].isin(["pais_permitido", "cidade_permitida"])]["termo"].tolist()
    bloqueados = df[df["tipo"].isin(["pais_bloqueado", "cidade_bloqueada"])]["termo"].tolist()
    return permitidos, bloqueados
