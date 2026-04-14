from database.connection import conectar

def adicionar_nota(id_vaga: int, nota: str) -> int:
    con = conectar()
    id_nota = con.execute("SELECT nextval('seq_log_candidatura')").fetchone()[0]
    con.execute("""
        INSERT INTO log_candidatura (id, id_vaga, nota)
        VALUES (?, ?, ?)
    """, [id_nota, id_vaga, nota])
    con.close()
    return id_nota

def listar_notas(id_vaga: int):
    con = conectar()
    df = con.execute("""
        SELECT id, data_nota, nota
        FROM log_candidatura
        WHERE id_vaga = ?
        ORDER BY data_nota DESC, id DESC
    """, [id_vaga]).df()
    con.close()
    return df

def deletar_nota(id_nota: int):
    con = conectar()
    con.execute("DELETE FROM log_candidatura WHERE id = ?", [id_nota])
    con.close()