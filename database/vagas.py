import json
import hashlib
from database.connection import conectar

def gerar_hash(titulo: str, empresa: str, link: str) -> str:
    conteudo = f"{titulo}{empresa}{link}".lower()
    return hashlib.md5(conteudo.encode()).hexdigest()

def inserir_vaga(vaga: dict, id_empresa: int) -> bool:
    con = conectar()
    hash_vaga = gerar_hash(vaga["titulo"], vaga["empresa"], vaga["link"])
    existente = con.execute(
        "SELECT id FROM fact_vaga WHERE hash = ?", [hash_vaga]
    ).fetchone()
    if existente:
        con.close()
        return False
    id_vaga = con.execute("SELECT nextval('seq_vaga')").fetchone()[0]
    con.execute("""
        INSERT INTO fact_vaga
        (id, hash, titulo, nivel, modalidade, stacks, link, fonte, id_empresa)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        id_vaga, hash_vaga,
        vaga["titulo"],
        vaga.get("nivel", "não identificado"),
        vaga.get("modalidade", "não identificado"),
        json.dumps(vaga.get("stacks", {})),
        vaga["link"],
        vaga["fonte"],
        id_empresa
    ])
    con.close()
    return True

def inserir_vaga_manual(titulo: str, id_empresa: int, empresa_nome: str,
                         descricao: str, origem: str, contato: str) -> int:
    from transformers.stack_extractor import extrair_stacks, detectar_nivel, detectar_modalidade
    stacks = extrair_stacks(descricao)
    nivel = detectar_nivel(titulo)
    modalidade = detectar_modalidade(descricao)
    con = conectar()
    hash_vaga = gerar_hash(titulo, empresa_nome, origem or "manual")
    existente = con.execute(
        "SELECT id FROM fact_vaga WHERE hash = ?", [hash_vaga]
    ).fetchone()
    if existente:
        con.close()
        return existente[0]
    id_vaga = con.execute("SELECT nextval('seq_vaga')").fetchone()[0]
    con.execute("""
        INSERT INTO fact_vaga
        (id, hash, titulo, nivel, modalidade, stacks, link, fonte,
         id_empresa, origem, contato)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        id_vaga, hash_vaga, titulo, nivel, modalidade,
        json.dumps(stacks), origem or "", "manual",
        id_empresa, origem, contato
    ])
    con.close()
    return id_vaga

def verificar_vagas_encerradas(id_empresa: int, links_ativos: list):
    con = conectar()
    vagas_no_banco = con.execute("""
        SELECT id, link, titulo FROM fact_vaga
        WHERE id_empresa = ? AND ativa = true
    """, [id_empresa]).fetchall()
    encerradas = []
    for id_vaga, link, titulo in vagas_no_banco:
        if link not in links_ativos:
            con.execute("""
                UPDATE fact_vaga
                SET ativa = false, data_encerramento = current_date
                WHERE id = ?
            """, [id_vaga])
            encerradas.append(titulo)
    con.close()
    return encerradas

def listar_vagas_negadas():
    con = conectar()
    df = con.execute("""
        SELECT v.id, v.titulo, v.candidatura_fase, v.candidatura_observacao,
               v.candidatura_data, e.nome AS empresa
        FROM fact_vaga v
        JOIN dim_empresa e ON v.id_empresa = e.id
        WHERE v.negada = true
        ORDER BY v.candidatura_data DESC
    """).df()
    con.close()
    return df