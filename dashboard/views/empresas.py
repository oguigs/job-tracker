import streamlit as st
from scrapers.company_search import buscar_empresa
from database.empresas import inserir_endereco, listar_enderecos, deletar_endereco
from dashboard.components import carregar_empresas, conectar_rw, get_favicon
from datetime import date

def safe(v):
    return "" if v is None or str(v) in ["None","nan","<NA>","NaT",""] else str(v)

def detectar_urls(url_vagas_input):
    url_vagas = url_vagas_input.strip()
    if "gupy.io" in url_vagas:
        return url_vagas, None, None
    elif "greenhouse.io" in url_vagas:
        return None, url_vagas, None
    elif "inhire.app" in url_vagas:
        return None, None, url_vagas
    return url_vagas, None, None

def render():
    st.title("Empresas monitoradas")
    df_empresas = carregar_empresas()
    st.subheader("Cadastrar nova empresa")

    if "dados_buscados" not in st.session_state:
        st.session_state.dados_buscados = {}
    if "form_key" not in st.session_state:
        st.session_state.form_key = 0

    col_busca, col_btn = st.columns([3, 1])
    nome_busca = col_busca.text_input("Nome da empresa", placeholder="Ex: Nubank")
    if col_btn.button("Buscar", use_container_width=True):
        if nome_busca:
            with st.spinner(f"Buscando informações de {nome_busca}..."):
                dados = buscar_empresa(nome_busca)
                dados["nome"] = nome_busca
                st.session_state.dados_buscados = dados
            st.success("Informações encontradas! Revise e edite antes de salvar.")
        else:
            st.warning("Digite o nome da empresa primeiro.")

    d = st.session_state.dados_buscados
    with st.form(f"form_empresa_{st.session_state.form_key}"):
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome da empresa *", value=d.get("nome", ""))
        ramo = col2.text_input("Ramo", value=d.get("ramo", ""))
        col3, col4, col5 = st.columns(3)
        cidade = col3.text_input("Cidade", value=d.get("cidade", ""))
        bairro = col4.text_input("Bairro", value=d.get("bairro", ""))
        estado = col5.text_input("Estado", value=d.get("estado", ""))
        url_vagas_input = st.text_input("URL de vagas *",
            placeholder="Ex: https://empresa.gupy.io/ ou https://boards.greenhouse.io/empresa")
        url_site_oficial = st.text_input("Site oficial",
            placeholder="https://www.empresa.com.br",
            help="Usado para buscar o logo automaticamente")

        if st.form_submit_button("Salvar empresa"):
            if not nome:
                st.error("Nome é obrigatório.")
            elif not url_vagas_input.strip():
                st.error("URL de vagas é obrigatória.")
            else:
                try:
                    favicon_url = ""
                    if url_site_oficial:
                        dominio = url_site_oficial.replace("https://www.","").replace("https://","").split("/")[0]
                        favicon_url = f"https://www.google.com/s2/favicons?domain={dominio}&sz=64"
                    con = conectar_rw()
                    existente = con.execute("SELECT id FROM dim_empresa WHERE nome=?", [nome]).fetchone()
                    if existente:
                        st.warning(f"{nome} já está cadastrada.")
                    else:
                        id_novo = con.execute("SELECT nextval('seq_empresa')").fetchone()[0]
                        con.execute("""
                            INSERT INTO dim_empresa
                            (id, nome, ramo, cidade, estado, url_vagas,
                             ativa, data_cadastro, favicon_url, url_site_oficial)
                            VALUES (?, ?, ?, ?, ?, ?, true, ?, ?, ?)
                        """, [id_novo, nome, ramo, cidade, estado,
                              url_vagas_input.strip(), date.today(),
                              favicon_url, url_site_oficial])
                        con.close()
                        st.session_state.dados_buscados = {}
                        st.session_state.form_key += 1
                        st.success(f"{nome} cadastrada!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cadastrar: {e}")

    st.divider()
    st.subheader("Empresas cadastradas")

    for _, emp in df_empresas.iterrows():
        ativa = str(emp.get("ativa","")) not in ["False","0","nan","None","<NA>","False"]
        status = "🟢 Ativa" if ativa else "🔴 Pausada"
        favicon = get_favicon(emp["nome"], safe(emp.get("favicon_url")))
        col_logo, col_titulo = st.columns([1, 8])
        if favicon:
            col_logo.image(favicon, width=32)
        col_titulo.markdown(f"**{emp['nome']}** — {status}")

        with st.expander(f"Ver detalhes — {emp['nome']}"):
            col1, col2 = st.columns(2)
            col1.write(f"**Ramo:** {safe(emp['ramo']) or '—'}")
            col2.write(f"**Cadastrada em:** {str(emp['data_cadastro'])[:10]}")
            url_v = safe(emp.get("url_vagas"))
            if url_v: st.write(f"**URL de vagas:** {url_v}")
            url_of = safe(emp.get("url_site_oficial"))
            if url_of: st.write(f"**Site oficial:** {url_of}")

            st.divider()
            with st.form(key=f"form_edit_{int(emp['id'])}"):
                st.caption("Editar informações")
                col1, col2 = st.columns(2)
                edit_ramo   = col1.text_input("Ramo", value=safe(emp["ramo"]), key=f"edit_ramo_{int(emp['id'])}")
                edit_estado = col2.text_input("Estado", value=safe(emp["estado"]), key=f"edit_estado_{int(emp['id'])}")
                edit_url    = st.text_input("URL de vagas", value=url_v,
                    placeholder="Cole a URL do Gupy, Greenhouse ou Inhire",
                    key=f"edit_url_{int(emp['id'])}")
                edit_site_oficial = st.text_input("Site oficial",
                    value=url_of, placeholder="https://www.empresa.com.br",
                    key=f"edit_site_oficial_{int(emp['id'])}")

                if st.form_submit_button("Salvar alterações"):
                    novo_favicon = safe(emp.get("favicon_url"))
                    if edit_site_oficial:
                        dominio = edit_site_oficial.replace("https://www.","").replace("https://","").split("/")[0]
                        novo_favicon = f"https://www.google.com/s2/favicons?domain={dominio}&sz=64"
                    con = conectar_rw()
                    con.execute("""
                        UPDATE dim_empresa
                        SET ramo=?, estado=?, url_vagas=?,
                            url_site_oficial=?, favicon_url=?
                        WHERE id=?
                    """, [edit_ramo, edit_estado, edit_url,
                          edit_site_oficial, novo_favicon, int(emp['id'])])
                    con.close()
                    st.success("Empresa atualizada!")
                    st.rerun()

            st.divider()
            st.write("**Polos:**")
            enderecos = listar_enderecos(int(emp['id']))
            if enderecos:
                for id_end, cid, bairro in enderecos:
                    col_end, col_del = st.columns([4, 1])
                    col_end.write(f"- {cid} / {bairro or '—'}")
                    if col_del.button("Remover", key=f"del_end_{id_end}"):
                        deletar_endereco(id_end)
                        st.rerun()
            else:
                st.caption("Nenhum polo cadastrado.")

            with st.form(key=f"form_end_{int(emp['id'])}"):
                col_c, col_b, col_add = st.columns([2, 2, 1])
                nova_cidade = col_c.text_input("Cidade", key=f"cidade_{int(emp['id'])}")
                novo_bairro = col_b.text_input("Bairro", key=f"bairro_{int(emp['id'])}")
                if col_add.form_submit_button("Adicionar polo"):
                    if nova_cidade:
                        inserir_endereco(int(emp['id']), nova_cidade, novo_bairro)
                        st.rerun()
                    else:
                        st.warning("Cidade é obrigatória.")

            st.divider()
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if ativa:
                    if st.button("Pausar monitoramento", key=f"pausar_{int(emp['id'])}", use_container_width=True):
                        con = conectar_rw()
                        con.execute("UPDATE dim_empresa SET ativa=false WHERE id=?", [int(emp['id'])])
                        con.close()
                        st.rerun()
                else:
                    if st.button("Reativar monitoramento", key=f"reativar_{int(emp['id'])}", use_container_width=True):
                        con = conectar_rw()
                        con.execute("UPDATE dim_empresa SET ativa=true WHERE id=?", [int(emp['id'])])
                        con.close()
                        st.rerun()
            with col_btn2:
                if st.button("Buscar vagas agora", key=f"buscar_{int(emp['id'])}", use_container_width=True):
                    with st.spinner(f"Coletando vagas de {emp['nome']}..."):
                        from main import processar_empresa
                        url = safe(emp.get("url_vagas"))
                        encontradas, novas, erro = processar_empresa(emp["nome"], url)
                        if erro:
                            st.error(f"Erro: {erro}")
                        else:
                            st.success(f"{encontradas} encontradas | {novas} novas")