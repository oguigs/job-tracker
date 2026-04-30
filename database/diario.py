from database.connection import db_connect


def adicionar_nota(id_vaga: int, nota: str, impressao: str = None) -> int:
    with db_connect() as con:
        id_nota = con.execute("SELECT nextval('seq_log_candidatura')").fetchone()[0]
        con.execute(
            "INSERT INTO log_candidatura (id, id_vaga, nota, impressao) VALUES (?, ?, ?, ?)",
            [id_nota, id_vaga, nota, impressao],
        )
    return id_nota


def listar_notas(id_vaga: int):
    with db_connect() as con:
        return con.execute(
            """
            SELECT id, data_nota, nota, impressao
            FROM log_candidatura
            WHERE id_vaga = ?
            ORDER BY data_nota DESC, id DESC
        """,
            [id_vaga],
        ).df()


def deletar_nota(id_nota: int):
    with db_connect() as con:
        con.execute("DELETE FROM log_candidatura WHERE id = ?", [id_nota])
