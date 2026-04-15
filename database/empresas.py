import hashlib
from database.connection import conectar

def gerar_hash(titulo: str, empresa: str, link: str) -> str:
    conteudo = f"{titulo}{empresa}{link}".lower()
    return hashlib.md5(conteudo.encode()).hexdigest()

def upsert_empresa(nome: str, url_gupy: str, **kwargs) -> int:
    con = conectar()
    resultado = con.execute(
        "SELECT id FROM dim_empresa WHERE nome = ?", [nome]
    ).fetchone()

    if resultado:
        id_empresa = resultado[0]
    else:
        id_empresa = con.execute("SELECT nextval('seq_empresa')").fetchone()[0]
        dominio = url_gupy.replace("https://", "").split("/")[0]
        favicon_url = f"https://www.google.com/s2/favicons?domain={dominio}&sz=64"
        con.execute("""
            INSERT INTO dim_empresa
            (id, nome, url_gupy, ramo, cidade, estado,
             url_linkedin, url_site_vagas, favicon_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            id_empresa, nome, url_gupy,
            kwargs.get("ramo", ""),
            kwargs.get("cidade", ""),
            kwargs.get("estado", ""),
            kwargs.get("url_linkedin", ""),
            kwargs.get("url_site_vagas", ""),
            favicon_url
        ])
    con.close()
    return id_empresa

def listar_empresas_ativas() -> list:
    con = conectar()
    empresas = con.execute("""
        SELECT nome, url_vagas FROM dim_empresa
        WHERE ativa = true AND url_vagas IS NOT NULL AND url_vagas != ''
    """).fetchall()
    con.close()
    return empresas

def inserir_endereco(id_empresa: int, cidade: str, bairro: str):
    con = conectar()
    id_end = con.execute("SELECT nextval('seq_endereco')").fetchone()[0]
    con.execute("""
        INSERT INTO dim_empresa_endereco (id, id_empresa, cidade, bairro)
        VALUES (?, ?, ?, ?)
    """, [id_end, id_empresa, cidade, bairro])
    con.close()

def listar_enderecos(id_empresa: int) -> list:
    con = conectar()
    enderecos = con.execute("""
        SELECT id, cidade, bairro FROM dim_empresa_endereco
        WHERE id_empresa = ?
        ORDER BY cidade, bairro
    """, [id_empresa]).fetchall()
    con.close()
    return enderecos

def deletar_endereco(id_endereco: int):
    con = conectar()
    con.execute("DELETE FROM dim_empresa_endereco WHERE id = ?", [id_endereco])
    con.close()