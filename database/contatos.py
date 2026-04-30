from database.connection import db_connect


def inserir_contato(
    nome: str, email: str, id_empresa: int, grau: str, observacoes: str = ""
) -> int:
    with db_connect() as con:
        id_contato = con.execute("SELECT nextval('seq_contato')").fetchone()[0]
        con.execute(
            """
            INSERT INTO dim_contato (id, nome, email, id_empresa, grau, observacoes)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            [id_contato, nome, email, id_empresa, grau, observacoes],
        )
    return id_contato


def listar_contatos(id_empresa: int = None):
    with db_connect() as con:
        if id_empresa:
            return con.execute(
                """
                SELECT c.id, c.nome, c.email, c.grau, c.observacoes, e.nome AS empresa
                FROM dim_contato c JOIN dim_empresa e ON c.id_empresa = e.id
                WHERE c.id_empresa = ? ORDER BY c.grau, c.nome
            """,
                [id_empresa],
            ).df()
        return con.execute("""
            SELECT c.id, c.nome, c.email, c.grau, c.observacoes, e.nome AS empresa
            FROM dim_contato c JOIN dim_empresa e ON c.id_empresa = e.id
            ORDER BY e.nome, c.grau, c.nome
        """).df()


def deletar_contato(id_contato: int):
    with db_connect() as con:
        con.execute("DELETE FROM dim_contato WHERE id = ?", [id_contato])
