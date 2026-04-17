from database.connection import conectar

def carregar_filtros():
    con = conectar()
    resultado = con.execute("""
        SELECT tipo, termo FROM config_filtros ORDER BY tipo, termo
    """).fetchall()
    con.close()
    interesse = [r[1].lower() for r in resultado if r[0] == "interesse"]
    bloqueio  = [r[1].lower() for r in resultado if r[0] == "bloqueio"]
    return interesse, bloqueio

def adicionar_filtro(tipo: str, termo: str):
    con = conectar()
    existente = con.execute(
        "SELECT id FROM config_filtros WHERE tipo = ? AND lower(termo) = lower(?)",
        [tipo, termo]
    ).fetchone()
    if not existente:
        con.execute("""
            INSERT INTO config_filtros VALUES (nextval('seq_filtro'), ?, ?, current_date)
        """, [tipo, termo])
    con.close()

def remover_filtro(id_filtro: int):
    con = conectar()
    con.execute("DELETE FROM config_filtros WHERE id = ?", [id_filtro])
    con.close()

def listar_filtros():
    con = conectar()
    df = con.execute("""
        SELECT id, tipo, termo, data_criacao
        FROM config_filtros ORDER BY tipo, termo
    """).df()
    con.close()
    return df

def carregar_filtros_localizacao():
    """Retorna listas de países/cidades permitidos e bloqueados."""
    con = conectar()
    df = con.execute("""
        SELECT tipo, termo FROM config_filtros 
        WHERE tipo IN ('pais_permitido', 'pais_bloqueado', 'cidade_permitida', 'cidade_bloqueada')
    """).df()
    con.close()
    
    permitidos = df[df["tipo"].isin(["pais_permitido","cidade_permitida"])]["termo"].tolist()
    bloqueados = df[df["tipo"].isin(["pais_bloqueado","cidade_bloqueada"])]["termo"].tolist()
    return permitidos, bloqueados