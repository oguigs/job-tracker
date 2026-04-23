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
