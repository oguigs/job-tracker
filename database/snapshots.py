from database.connection import conectar
import json

def salvar_snapshot():
    """Salva snapshot das stacks do mercado hoje."""
    con = conectar()

    # verifica se já tem snapshot hoje
    hoje = con.execute("SELECT current_date").fetchone()[0]
    existente = con.execute("""
        SELECT COUNT(*) FROM snapshot_mercado WHERE data_ref = ?
    """, [hoje]).fetchone()[0]

    if existente > 0:
        con.close()
        print(f"Snapshot de {hoje} já existe.")
        return

    # extrai stacks de todas as vagas ativas
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

    # insere snapshot
    for (stack, categoria), quantidade in contagem.items():
        id_snap = con.execute("SELECT nextval('seq_snapshot')").fetchone()[0]
        con.execute("""
            INSERT INTO snapshot_mercado (id, data_ref, stack, categoria, quantidade)
            VALUES (?, ?, ?, ?, ?)
        """, [id_snap, hoje, stack, categoria, quantidade])

    con.close()
    print(f"Snapshot salvo: {len(contagem)} stacks em {hoje}")

def carregar_historico(stack: str = None, categoria: str = None):
    con = conectar()
    if stack:
        df = con.execute("""
            SELECT strftime(data_ref, '%Y-%m-%d') as data_ref, 
                   stack, categoria, quantidade
            FROM snapshot_mercado
            WHERE lower(stack) = lower(?)
            ORDER BY data_ref
        """, [stack]).df()
    elif categoria:
        df = con.execute("""
            SELECT strftime(data_ref, '%Y-%m-%d') as data_ref,
                   stack, SUM(quantidade) as quantidade
            FROM snapshot_mercado
            WHERE categoria = ?
            GROUP BY data_ref, stack
            ORDER BY data_ref, quantidade DESC
        """, [categoria]).df()
    else:
        df = con.execute("""
            SELECT strftime(data_ref, '%Y-%m-%d') as data_ref,
                   categoria, SUM(quantidade) as quantidade
            FROM snapshot_mercado
            GROUP BY data_ref, categoria
            ORDER BY data_ref
        """).df()
    con.close()
    return df

def listar_stacks_snapshot():
    """Lista todas as stacks que têm histórico."""
    con = conectar()
    stacks = con.execute("""
        SELECT DISTINCT stack, categoria
        FROM snapshot_mercado
        ORDER BY categoria, stack
    """).fetchall()
    con.close()
    return stacks