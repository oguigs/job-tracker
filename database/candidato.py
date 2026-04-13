import json
from database.connection import conectar

def salvar_perfil(nome: str, email: str, linkedin: str, cidade: str,
                  nivel: str, modalidade_pref: str, pretensao_min: int,
                  pretensao_max: int, resumo: str) -> int:
    con = conectar()
    existente = con.execute("SELECT id FROM dim_candidato LIMIT 1").fetchone()
    if existente:
        con.execute("""
            UPDATE dim_candidato SET
                nome=?, email=?, linkedin=?, cidade=?, nivel=?,
                modalidade_pref=?, pretensao_min=?, pretensao_max=?,
                resumo=?, data_atualizacao=current_date
            WHERE id=?
        """, [nome, email, linkedin, cidade, nivel,
              modalidade_pref, pretensao_min, pretensao_max,
              resumo, existente[0]])
        id_candidato = existente[0]
    else:
        id_candidato = con.execute("SELECT nextval('seq_candidato')").fetchone()[0]
        con.execute("""
            INSERT INTO dim_candidato
            (id, nome, email, linkedin, cidade, nivel,
             modalidade_pref, pretensao_min, pretensao_max, resumo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [id_candidato, nome, email, linkedin, cidade, nivel,
              modalidade_pref, pretensao_min, pretensao_max, resumo])
    con.close()
    return id_candidato

def carregar_perfil():
    con = conectar()
    resultado = con.execute("SELECT * FROM dim_candidato LIMIT 1").df()
    con.close()
    return resultado

def salvar_stack(id_candidato: int, stack: str, categoria: str,
                 nivel_stack: str, anos_exp: int):
    con = conectar()
    existente = con.execute("""
        SELECT id FROM dim_candidato_stack
        WHERE id_candidato=? AND stack=?
    """, [id_candidato, stack]).fetchone()
    if existente:
        con.execute("""
            UPDATE dim_candidato_stack
            SET nivel_stack=?, anos_exp=?
            WHERE id=?
        """, [nivel_stack, anos_exp, existente[0]])
    else:
        id_stack = con.execute("SELECT nextval('seq_candidato_stack')").fetchone()[0]
        con.execute("""
            INSERT INTO dim_candidato_stack
            (id, id_candidato, stack, categoria, nivel_stack, anos_exp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [id_stack, id_candidato, stack, categoria, nivel_stack, anos_exp])
    con.close()

def carregar_stacks(id_candidato: int):
    con = conectar()
    df = con.execute("""
        SELECT id, stack, categoria, nivel_stack, anos_exp
        FROM dim_candidato_stack
        WHERE id_candidato=?
        ORDER BY categoria, stack
    """, [id_candidato]).df()
    con.close()
    return df

def deletar_stack(id_stack: int):
    con = conectar()
    con.execute("DELETE FROM dim_candidato_stack WHERE id=?", [id_stack])
    con.close()