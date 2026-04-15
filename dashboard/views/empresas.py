import streamlit as st
from scrapers.company_search import buscar_empresa
from database.empresas import inserir_endereco, listar_enderecos, deletar_endereco
from dashboard.components import carregar_empresas, conectar_rw, get_favicon

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
            placeholder="Cole a URL do Gupy ou Greenhouse — ex: https://empresa.gupy.io/ ou https://boards.greenhouse.io/empresa")
        # detecta plataforma automaticamente
        url_gupy = ""
        url_greenhouse = None
        if "gupy.io" in url_vagas_input:
            url_gupy = url_vagas_input
        elif "greenhouse.io" in url_vagas_input:
            url_greenhouse = url_vagas_input.split("greenhouse.io/")[-1].split("/")[0]

        url_linkedin = st.text_input("URL LinkedIn", value=d.get("url_linkedin", ""))
        url_site_vagas = st.text_input("URL site de vagas", value=d.get("url_site_vagas", ""))
        url_site_oficial = st.text_input("Site oficial da empresa",
            placeholder="https://www.empresa.com.br",
            help="Usado para buscar o logo da empresa automaticamente")

        if st.form_submit_button("Salvar empresa"):
            if not nome:
                st.error("Nome da empresa é obrigatório.")
            elif not url_gupy:
                st.error("URL Gupy é obrigatória.")
            else:
                try:
                    favicon_url = ""
                    if url_site_oficial:
                        dominio = url_site_oficial.replace("https://www.", "").replace("https://", "").split("/")[0]
                        favicon_url = f"https://www.google.com/s2/favicons?domain={dominio}&sz=64"
                    con = conectar_rw()
                    existente = con.execute("SELECT id FROM dim_empresa WHERE nome = ?", [nome]).fetchone()
                    if existente:
                        st.warning(f"{nome} já está cadastrada.")
                    else:
                        id_novo = con.execute("SELECT nextval('seq_empresa')").fetchone()[0]
                        con.execute("""
                            INSERT INTO dim_empresa
                            (id, nome, ramo, cidade, estado, url_gupy, url_linkedin,
                             url_site_vagas, url_site_oficial, favicon_url)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, [id_novo, nome, ramo, cidade, estado,
                              url_gupy, url_linkedin, url_site_vagas, url_site_oficial, favicon_url])
                        con.close()
                        st.session_state.dados_buscados = {}
                        st.session_state.form_key += 1
                        st.success(f"{nome} cadastrada com sucesso!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cadastrar: {e}")

    st.divider()
    st.subheader("Empresas cadastradas")

    for _, emp in df_empresas.iterrows():
        status = "🟢 Ativa" if emp["ativa"] else "🔴 Pausada"
        favicon = get_favicon(emp["nome"], emp.get("favicon_url") or "")
        col_logo, col_titulo = st.columns([1, 8])
        if favicon:
            col_logo.image(favicon, width=32)
        col_titulo.markdown(f"**{emp['nome']}** — {status}")

        with st.expander(f"Ver detalhes — {emp['nome']}"):
            col1, col2 = st.columns(2)
            col1.write(f"**Ramo:** {emp['ramo'] or '—'}")
            col2.write(f"**Cadastrada em:** {emp['data_cadastro']}")
            if emp["url_gupy"]: st.write(f"**Gupy:** {emp['url_gupy']}")
            if emp["url_linkedin"]: st.write(f"**LinkedIn:** {emp['url_linkedin']}")
            if emp.get("url_site_oficial"): st.write(f"**Site oficial:** {emp['url_site_oficial']}")

            st.divider()
            with st.form(key=f"form_edit_{emp['id']}"):
                st.caption("Editar informações")
                col1, col2 = st.columns(2)
                edit_ramo = col1.text_input("Ramo", value=emp["ramo"] or "", key=f"edit_ramo_{emp['id']}")
                edit_estado = col2.text_input("Estado", value=emp["estado"] or "", key=f"edit_estado_{emp['id']}")
                edit_url_vagas = st.text_input("URL de vagas",
                    value=emp.get("url_gupy") or (f"https://boards.greenhouse.io/{emp.get('url_greenhouse')}" if emp.get("url_greenhouse") else ""),
                    placeholder="Cole a URL do Gupy ou Greenhouse",
                    key=f"edit_url_{emp['id']}")
                edit_gupy = ""
                edit_greenhouse = None
                if "gupy.io" in edit_url_vagas:
                    edit_gupy = edit_url_vagas
                elif "greenhouse.io" in edit_url_vagas:
                    edit_greenhouse = edit_url_vagas.split("greenhouse.io/")[-1].split("/")[0]
                edit_linkedin = st.text_input("URL LinkedIn", value=emp["url_linkedin"] or "", key=f"edit_linkedin_{emp['id']}")
                edit_site = st.text_input("URL site de vagas", value=emp["url_site_vagas"] or "", key=f"edit_site_{emp['id']}")
                edit_site_oficial = st.text_input("Site oficial",
                    value=emp.get("url_site_oficial") or "",
                    placeholder="https://www.empresa.com.br",
                    key=f"edit_site_oficial_{emp['id']}")

                if st.form_submit_button("Salvar alterações"):
                    if edit_site_oficial:
                        dominio = edit_site_oficial.replace("https://www.", "").replace("https://", "").split("/")[0]
                        novo_favicon = f"https://www.google.com/s2/favicons?domain={dominio}&sz=64"
                    else:
                        novo_favicon = get_favicon(emp["nome"], emp.get("favicon_url") or "")
                    con = conectar_rw()
                    con.execute("""
                        UPDATE dim_empresa
                        SET ramo=?, estado=?, url_gupy=?, url_linkedin=?,
                            url_site_vagas=?, url_site_oficial=?, favicon_url=?
                        WHERE id=?
                    """, [edit_ramo, edit_estado, edit_gupy, edit_linkedin,
                          edit_site, edit_site_oficial, novo_favicon, emp["id"]])
                    con.close()
                    st.success("Empresa atualizada!")
                    st.rerun()

            st.divider()
            st.write("**Polos:**")
            enderecos = listar_enderecos(emp["id"])
            if enderecos:
                for id_end, cidade, bairro in enderecos:
                    col_end, col_del = st.columns([4, 1])
                    col_end.write(f"- {cidade} / {bairro or '—'}")
                    if col_del.button("Remover", key=f"del_end_{id_end}"):
                        deletar_endereco(id_end)
                        st.rerun()
            else:
                st.caption("Nenhum polo cadastrado.")

            with st.form(key=f"form_end_{emp['id']}"):
                col_c, col_b, col_add = st.columns([2, 2, 1])
                nova_cidade = col_c.text_input("Cidade", key=f"cidade_{emp['id']}")
                novo_bairro = col_b.text_input("Bairro", key=f"bairro_{emp['id']}")
                if col_add.form_submit_button("Adicionar polo"):
                    if nova_cidade:
                        inserir_endereco(emp["id"], nova_cidade, novo_bairro)
                        st.rerun()
                    else:
                        st.warning("Cidade é obrigatória.")

            st.divider()
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if emp["ativa"]:
                    if st.button("Pausar monitoramento", key=f"pausar_{emp['id']}", use_container_width=True):
                        con = conectar_rw()
                        con.execute("UPDATE dim_empresa SET ativa = false WHERE id = ?", [emp["id"]])
                        con.close()
                        st.rerun()
                else:
                    if st.button("Reativar monitoramento", key=f"reativar_{emp['id']}", use_container_width=True):
                        con = conectar_rw()
                        con.execute("UPDATE dim_empresa SET ativa = true WHERE id = ?", [emp["id"]])
                        con.close()
                        st.rerun()
            with col_btn2:
                if st.button("Buscar vagas agora", key=f"buscar_{emp['id']}", use_container_width=True):
                    with st.spinner(f"Coletando vagas de {emp['nome']}..."):
                        from main import processar_empresa
                        encontradas, novas, erro = processar_empresa(emp["nome"], emp["url_gupy"])
                        if erro:
                            st.error(f"Erro: {erro}")
                        else:
                            st.success(f"{encontradas} encontradas | {novas} novas")