import json
import hashlib
from database.connection import conectar, db_connect


def gerar_hash(titulo: str, empresa: str, link: str) -> str:
    conteudo = f"{titulo}{empresa}{link}".lower()
    return hashlib.md5(conteudo.encode()).hexdigest()


def inserir_vaga(vaga: dict, id_empresa: int) -> int | None:
    """Returns the new vaga id if inserted, None if already exists."""
    hash_vaga = gerar_hash(vaga["titulo"], vaga["empresa"], vaga["link"])
    with db_connect() as con:
        if con.execute("SELECT id FROM fact_vaga WHERE hash = ?", [hash_vaga]).fetchone():
            return None
        id_vaga = con.execute("SELECT nextval('seq_vaga')").fetchone()[0]
        con.execute("""
            INSERT INTO fact_vaga
            (id, hash, titulo, nivel, modalidade, stacks, link, fonte,
            id_empresa, ativa, negada, candidatura_status, urgente,
            descricao, salario_min, salario_max)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, true, false, 'nao_inscrito',
                    ?, ?, ?, ?)
        """, [id_vaga, hash_vaga,
            vaga["titulo"],
            vaga.get("nivel", "não identificado"),
            vaga.get("modalidade", "não identificado"),
            json.dumps(vaga.get("stacks", {})),
            vaga["link"], vaga["fonte"], id_empresa,
            vaga.get("urgente", False),
            vaga.get("descricao", ""),
            vaga.get("salario_min", 0),
            vaga.get("salario_max", 0),
        ])
    return id_vaga


def inserir_vaga_manual(titulo: str, id_empresa: int, empresa_nome: str,
                        descricao: str, origem: str, contato: str) -> int:
    from transformers.stack_extractor import extrair_stacks, detectar_nivel, detectar_modalidade
    stacks    = extrair_stacks(descricao)
    nivel     = detectar_nivel(titulo)
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
             id_empresa, origem, contato, descricao, ativa, negada, candidatura_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, true, false, 'nao_inscrito')
        """, [id_vaga, hash_vaga, titulo, nivel, modalidade,
              json.dumps(stacks), origem or "", "manual",
              id_empresa, origem, contato, descricao or ""])
    return id_vaga


def verificar_vagas_encerradas(id_empresa: int, links_ativos: list) -> list:
    encerradas = []
    links_set = set(links_ativos)
    with db_connect() as con:
        vagas = con.execute("""
            SELECT id, link, titulo, ausencias_consecutivas
            FROM fact_vaga
            WHERE id_empresa = ? AND ativa = true AND fonte != 'manual'
        """, [id_empresa]).fetchall()
        for id_vaga, link, titulo, ausencias in vagas:
            ausencias = ausencias or 0
            if link not in links_set:
                if ausencias >= 1:
                    con.execute("""
                        UPDATE fact_vaga
                        SET ativa = false, data_encerramento = current_date,
                            ausencias_consecutivas = 0
                        WHERE id = ?
                    """, [id_vaga])
                    encerradas.append(titulo)
                else:
                    con.execute("""
                        UPDATE fact_vaga SET ausencias_consecutivas = ausencias_consecutivas + 1
                        WHERE id = ?
                    """, [id_vaga])
            else:
                if ausencias > 0:
                    con.execute("""
                        UPDATE fact_vaga SET ausencias_consecutivas = 0 WHERE id = ?
                    """, [id_vaga])
    return encerradas


def atualizar_descricao_vaga(id_vaga: int, descricao: str, stacks_json: str = None, modalidade: str = None):
    with db_connect() as con:
        if stacks_json and modalidade:
            con.execute(
                "UPDATE fact_vaga SET descricao=?, stacks=?, modalidade=? WHERE id=?",
                [descricao, stacks_json, modalidade, id_vaga]
            )
        elif stacks_json:
            con.execute(
                "UPDATE fact_vaga SET descricao=?, stacks=? WHERE id=?",
                [descricao, stacks_json, id_vaga]
            )
        else:
            con.execute(
                "UPDATE fact_vaga SET descricao=? WHERE id=?",
                [descricao, id_vaga]
            )


def listar_vagas_sem_descricao() -> list:
    """Returns [(id, titulo, link, fonte)] for active vagas with NULL/empty description."""
    with db_connect() as con:
        return con.execute("""
            SELECT id, titulo, link, fonte
            FROM fact_vaga
            WHERE ativa = true
              AND (descricao IS NULL OR descricao = '')
            ORDER BY fonte, id
        """).fetchall()


def listar_vagas_negadas():
    with db_connect() as con:
        return con.execute("""
            SELECT v.id, v.titulo, v.candidatura_fase, v.candidatura_observacao,
                   v.candidatura_data, e.nome AS empresa
            FROM fact_vaga v
            JOIN dim_empresa e ON v.id_empresa = e.id
            WHERE v.negada = true
            ORDER BY v.candidatura_data DESC
        """).df()
