from logger import get_logger

log = get_logger("snapshots")
import json
from database.connection import db_connect


def salvar_snapshot():
    """Salva snapshot das stacks do mercado hoje."""
    with db_connect() as con:
        hoje = con.execute("SELECT current_date").fetchone()[0]
        existente = con.execute(
            "SELECT COUNT(*) FROM snapshot_mercado WHERE data_ref = ?", [hoje]
        ).fetchone()[0]
        if existente > 0:
            log.info(f"Snapshot de {hoje} já existe.")
            return
        vagas = con.execute("""
            SELECT stacks FROM fact_vaga
            WHERE (negada = false OR negada IS NULL) AND ativa = true
        """).fetchall()
        contagem = {}
        for (stacks_raw,) in vagas:
            try:
                stacks = json.loads(stacks_raw) if isinstance(stacks_raw, str) else stacks_raw
                for categoria, termos in stacks.items():
                    for termo in termos:
                        key = (termo.lower(), categoria)
                        contagem[key] = contagem.get(key, 0) + 1
            except Exception:
                pass
        for (stack, categoria), quantidade in contagem.items():
            id_snap = con.execute("SELECT nextval('seq_snapshot')").fetchone()[0]
            con.execute(
                """
                INSERT INTO snapshot_mercado (id, data_ref, stack, categoria, quantidade)
                VALUES (?, ?, ?, ?, ?)
            """,
                [id_snap, hoje, stack, categoria, quantidade],
            )
    log.info(f"Snapshot salvo: {len(contagem)} stacks em {hoje}")


def carregar_historico(stack: str = None, categoria: str = None):
    with db_connect() as con:
        if stack:
            return con.execute(
                """
                SELECT strftime(data_ref, '%Y-%m-%d') as data_ref,
                       stack, categoria, quantidade
                FROM snapshot_mercado
                WHERE lower(stack) = lower(?)
                ORDER BY data_ref
            """,
                [stack],
            ).df()
        elif categoria:
            return con.execute(
                """
                SELECT strftime(data_ref, '%Y-%m-%d') as data_ref,
                       stack, SUM(quantidade) as quantidade
                FROM snapshot_mercado
                WHERE categoria = ?
                GROUP BY data_ref, stack
                ORDER BY data_ref, quantidade DESC
            """,
                [categoria],
            ).df()
        else:
            return con.execute("""
                SELECT strftime(data_ref, '%Y-%m-%d') as data_ref,
                       categoria, SUM(quantidade) as quantidade
                FROM snapshot_mercado
                GROUP BY data_ref, categoria
                ORDER BY data_ref
            """).df()


def listar_stacks_snapshot() -> list:
    with db_connect() as con:
        return con.execute("""
            SELECT DISTINCT stack, categoria
            FROM snapshot_mercado
            ORDER BY categoria, stack
        """).fetchall()
