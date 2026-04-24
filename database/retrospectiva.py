from database.connection import db_connect


def salvar_retrospectiva(id_vaga: int, nao_soube: str, faria_diferente: str,
                          impressao_geral: str, motivo_encerramento: str) -> int:
    with db_connect() as con:
        # remove retrospectiva anterior se existir
        con.execute("DELETE FROM log_retrospectiva WHERE id_vaga = ?", [id_vaga])
        id_r = con.execute("SELECT nextval('seq_retrospectiva')").fetchone()[0]
        con.execute("""
            INSERT INTO log_retrospectiva
            (id, id_vaga, nao_soube, faria_diferente, impressao_geral, motivo_encerramento)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [id_r, id_vaga, nao_soube, faria_diferente, impressao_geral, motivo_encerramento])
    return id_r


def carregar_retrospectiva(id_vaga: int):
    with db_connect() as con:
        return con.execute("""
            SELECT nao_soube, faria_diferente, impressao_geral, motivo_encerramento, data
            FROM log_retrospectiva WHERE id_vaga = ?
        """, [id_vaga]).fetchone()


def listar_retrospectivas():
    with db_connect() as con:
        return con.execute("""
            SELECT r.id, r.nao_soube, r.faria_diferente, r.impressao_geral,
                   r.motivo_encerramento, r.data,
                   v.titulo, e.nome as empresa, v.candidatura_status
            FROM log_retrospectiva r
            JOIN fact_vaga v ON r.id_vaga = v.id
            JOIN dim_empresa e ON v.id_empresa = e.id
            ORDER BY r.data DESC
        """).df()
