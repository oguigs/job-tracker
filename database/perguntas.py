from database.connection import db_connect


def adicionar_pergunta(id_vaga: int, stack: str, pergunta: str,
                       dificuldade: str, acertou: bool,
                       resposta_ideal: str = "") -> int:
    with db_connect() as con:
        id_p = con.execute("SELECT nextval('seq_pergunta')").fetchone()[0]
        con.execute("""
            INSERT INTO log_perguntas_entrevista
            (id, id_vaga, stack, pergunta, dificuldade, acertou, resposta_ideal)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [id_p, id_vaga, stack, pergunta, dificuldade, acertou, resposta_ideal])
    return id_p


def listar_perguntas(id_vaga: int = None, stack: str = None):
    with db_connect(read_only=True) as con:
        if id_vaga:
            return con.execute("""
                SELECT p.id, p.stack, p.pergunta, p.dificuldade, p.acertou,
                       p.resposta_ideal, p.data, e.nome as empresa
                FROM log_perguntas_entrevista p
                JOIN fact_vaga v ON p.id_vaga = v.id
                JOIN dim_empresa e ON v.id_empresa = e.id
                WHERE p.id_vaga = ?
                ORDER BY p.data DESC
            """, [id_vaga]).df()
        elif stack:
            return con.execute("""
                SELECT p.id, p.stack, p.pergunta, p.dificuldade, p.acertou,
                       p.resposta_ideal, p.data, e.nome as empresa
                FROM log_perguntas_entrevista p
                JOIN fact_vaga v ON p.id_vaga = v.id
                JOIN dim_empresa e ON v.id_empresa = e.id
                WHERE lower(p.stack) = lower(?)
                ORDER BY p.dificuldade, p.data DESC
            """, [stack]).df()
        else:
            return con.execute("""
                SELECT p.id, p.stack, p.pergunta, p.dificuldade, p.acertou,
                       p.resposta_ideal, p.data, e.nome as empresa
                FROM log_perguntas_entrevista p
                JOIN fact_vaga v ON p.id_vaga = v.id
                JOIN dim_empresa e ON v.id_empresa = e.id
                ORDER BY p.stack, p.dificuldade, p.data DESC
            """).df()


def deletar_pergunta(id_pergunta: int):
    with db_connect() as con:
        con.execute("DELETE FROM log_perguntas_entrevista WHERE id = ?", [id_pergunta])


def stats_perguntas():
    """Estatísticas para priorizar estudos."""
    with db_connect(read_only=True) as con:
        return con.execute("""
            SELECT
                stack,
                COUNT(*) as total,
                SUM(CASE WHEN acertou = false THEN 1 ELSE 0 END) as erros,
                SUM(CASE WHEN dificuldade = 'difícil' THEN 1 ELSE 0 END) as dificeis
            FROM log_perguntas_entrevista
            GROUP BY stack
            ORDER BY erros DESC, total DESC
        """).df()
