import json
import hashlib
from database.connection import conectar, db_connect


def gerar_hash(titulo: str, empresa: str, link: str) -> str:
    conteudo = f"{titulo}{empresa}{link}".lower()
    return hashlib.md5(conteudo.encode()).hexdigest()


def inserir_vaga(vaga: dict, id_empresa: int) -> bool:
    hash_vaga = gerar_hash(vaga["titulo"], vaga["empresa"], vaga["link"])
    with db_connect() as con:
        if con.execute("SELECT id FROM fact_vaga WHERE hash = ?", [hash_vaga]).fetchone():
            return False
        id_vaga = con.execute("SELECT nextval('seq_vaga')").fetchone()[0]
        con.execute("""
            INSERT INTO fact_vaga
            (id, hash, titulo, nivel, modalidade, stacks, link, fonte, id_empresa, ativa, negada, candidatura_status, urgente, descricao, salario_min, salario_max)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, true, false, 'nao_inscrito', ?, ?, ?, ?)
        """, [id_vaga, hash_vaga,
              vaga["titulo"],
              vaga.get("nivel", "não identificado"),
              vaga.get("modalidade", "não identificado"),
              json.dumps(vaga.get("stacks", {})),
              vaga["link"], vaga["fonte"], id_empresa,
              vaga.get("urgente", False),
              vaga.get("descricao", ""),
              vaga.get("salario_min", 0),
              vaga.get("salario_max", 0)])
    return True


def inserir_vaga_manual(titulo: str, id_empresa: int, empresa_nome: str,
                        descricao: str, origem: str, contato: str) -> int:
    from transformers.stack_extractor import extrair_stacks, detectar_nivel, detectar_modalidade
    stacks = extrair_stacks(descricao)
    nivel = detectar_nivel(titulo)
    modalidade = detectar_modalidade(descricao)
    hash_vaga = gerar_hash(titulo, empresa_nome, origem or "manual")
    with db_connect() as con:
        existente = con.execute("SELECT id FROM fact_vaga WHERE hash = ?", [hash_vaga]).fetchone()
        if existente:
            return existente[0]
        id_vaga = con.execute("SELECT nextval('seq_vaga')").fetchone()[0]
        con.execute("""
            INSERT INTO fact_vaga
            (id, hash, titulo, nivel, modalidade, stacks, link, fonte,
             id_empresa, origem, contato)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [id_vaga, hash_vaga, titulo, nivel, modalidade,
              json.dumps(stacks), origem or "", "manual",
              id_empresa, origem, contato])
    return id_vaga


def verificar_vagas_encerradas(id_empresa: int, links_ativos: list) -> list:
    encerradas = []
    with db_connect() as con:
        vagas = con.execute("""
            SELECT id, link, titulo FROM fact_vaga
            WHERE id_empresa = ? AND ativa = true
        """, [id_empresa]).fetchall()
        for id_vaga, link, titulo in vagas:
            if link not in links_ativos:
                con.execute("""
                    UPDATE fact_vaga SET ativa = false, data_encerramento = current_date
                    WHERE id = ?
                """, [id_vaga])
                encerradas.append(titulo)
    return encerradas


def listar_vagas_negadas():
    with db_connect(read_only=True) as con:
        return con.execute("""
            SELECT v.id, v.titulo, v.candidatura_fase, v.candidatura_observacao,
                   v.candidatura_data, e.nome AS empresa
            FROM fact_vaga v
            JOIN dim_empresa e ON v.id_empresa = e.id
            WHERE v.negada = true
            ORDER BY v.candidatura_data DESC
        """).df()
