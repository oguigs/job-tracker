import hashlib
from database.connection import db_connect


def gerar_hash(titulo: str, empresa: str, link: str) -> str:
    conteudo = f"{titulo}{empresa}{link}".lower()
    return hashlib.md5(conteudo.encode()).hexdigest()


def upsert_empresa(nome: str, url_vagas: str, **kwargs) -> int:
    with db_connect() as con:
        resultado = con.execute("SELECT id FROM dim_empresa WHERE nome = ?", [nome]).fetchone()
        if resultado:
            return resultado[0]
        id_empresa = con.execute("SELECT nextval('seq_empresa')").fetchone()[0]
        dominio = url_vagas.replace("https://", "").split("/")[0]
        favicon_url = f"https://www.google.com/s2/favicons?domain={dominio}&sz=64"
        con.execute("""
            INSERT INTO dim_empresa
            (id, nome, url_vagas, ramo, cidade, estado,
             url_linkedin, url_site_vagas, favicon_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [id_empresa, nome, url_vagas,
              kwargs.get("ramo", ""), kwargs.get("cidade", ""),
              kwargs.get("estado", ""), kwargs.get("url_linkedin", ""),
              kwargs.get("url_site_vagas", ""), favicon_url])
    return id_empresa


def listar_empresas_ativas() -> list:
    with db_connect(read_only=True) as con:
        return con.execute("""
            SELECT nome, url_vagas FROM dim_empresa
            WHERE ativa = true AND url_vagas IS NOT NULL AND url_vagas != ''
        """).fetchall()


def inserir_endereco(id_empresa: int, cidade: str, bairro: str):
    with db_connect() as con:
        id_end = con.execute("SELECT nextval('seq_endereco')").fetchone()[0]
        con.execute("""
            INSERT INTO dim_empresa_endereco (id, id_empresa, cidade, bairro)
            VALUES (?, ?, ?, ?)
        """, [id_end, id_empresa, cidade, bairro])


def listar_enderecos(id_empresa: int) -> list:
    with db_connect(read_only=True) as con:
        return con.execute("""
            SELECT id, cidade, bairro FROM dim_empresa_endereco
            WHERE id_empresa = ? ORDER BY cidade, bairro
        """, [id_empresa]).fetchall()


def deletar_endereco(id_endereco: int):
    with db_connect() as con:
        con.execute("DELETE FROM dim_empresa_endereco WHERE id = ?", [id_endereco])


def gerar_briefing_empresa(nome: str) -> dict:
    """
    Gera briefing automático de uma empresa com dados do banco.
    Usado quando candidatura avança para entrevista.
    """
    with db_connect(read_only=True) as con:
        stats = con.execute("""
            SELECT
                COUNT(*) as total_vagas,
                COUNT(CASE WHEN v.ativa=true THEN 1 END) as ativas,
                COUNT(CASE WHEN v.candidatura_status != 'nao_inscrito' THEN 1 END) as candidaturas,
                COUNT(CASE WHEN v.urgente=true THEN 1 END) as urgentes
            FROM fact_vaga v
            JOIN dim_empresa e ON v.id_empresa=e.id
            WHERE e.nome=? AND (v.negada=false OR v.negada IS NULL)
        """, [nome]).fetchone()

        niveis = con.execute("""
            SELECT v.nivel, COUNT(*) as total
            FROM fact_vaga v JOIN dim_empresa e ON v.id_empresa=e.id
            WHERE e.nome=? AND (v.negada=false OR v.negada IS NULL)
            GROUP BY v.nivel ORDER BY total DESC LIMIT 3
        """, [nome]).fetchall()

        modalidades = con.execute("""
            SELECT v.modalidade, COUNT(*) as total
            FROM fact_vaga v JOIN dim_empresa e ON v.id_empresa=e.id
            WHERE e.nome=? AND (v.negada=false OR v.negada IS NULL)
            GROUP BY v.modalidade ORDER BY total DESC LIMIT 2
        """, [nome]).fetchall()

        stacks_raw = con.execute("""
            SELECT v.stacks FROM fact_vaga v
            JOIN dim_empresa e ON v.id_empresa=e.id
            WHERE e.nome=? AND (v.negada=false OR v.negada IS NULL)
            AND v.stacks IS NOT NULL
        """, [nome]).fetchall()

        contatos = con.execute("""
            SELECT c.nome, c.grau, c.email
            FROM dim_contato c JOIN dim_empresa e ON c.id_empresa=e.id
            WHERE e.nome=?
        """, [nome]).fetchall()

        logs = con.execute("""
            SELECT data_execucao FROM log_coleta
            WHERE empresa=? AND status='sucesso'
            ORDER BY data_execucao DESC LIMIT 1
        """, [nome]).fetchone()

    # conta stacks mais pedidas
    import json
    from collections import Counter
    stacks_counter = Counter()
    for (stacks_json,) in stacks_raw:
        try:
            stacks = json.loads(stacks_json) if isinstance(stacks_json, str) else stacks_json
            for termos in stacks.values():
                stacks_counter.update(t.lower() for t in termos)
        except Exception:
            pass
    top_stacks = stacks_counter.most_common(8)

    ultima_coleta = str(logs[0])[:10] if logs else "desconhecida"

    return {
        "total_vagas": stats[0] if stats else 0,
        "vagas_ativas": stats[1] if stats else 0,
        "candidaturas": stats[2] if stats else 0,
        "urgentes": stats[3] if stats else 0,
        "niveis": niveis,
        "modalidades": modalidades,
        "top_stacks": top_stacks,
        "contatos": contatos,
        "ultima_coleta": ultima_coleta,
    }
