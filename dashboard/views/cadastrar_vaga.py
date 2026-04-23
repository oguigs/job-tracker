import json
import streamlit as st
from database.vagas import inserir_vaga_manual
from database.empresas import inserir_endereco
from transformers.stack_extractor import extrair_stacks, detectar_nivel, detectar_modalidade
from dashboard.components import conectar, conectar_rw, render_stacks
from datetime import date


def render():
    st.title("Cadastrar vaga manualmente")
    st.caption("Para vagas recebidas por indicação, headhunter ou LinkedIn direto.")

    con = conectar()
    empresas_db = con.execute("""
        SELECT id, nome FROM dim_empresa WHERE ativa = true ORDER BY nome
    """).fetchall()
    con.close()

    nomes_empresas = [e[1] for e in empresas_db]
    mapa_empresas = {e[1]: e[0] for e in empresas_db}

    if "preview_stacks" not in st.session_state:
        st.session_state.preview_stacks = None
    if "form_manual_key" not in st.session_state:
        st.session_state.form_manual_key = 0

    col_form, col_preview = st.columns([3, 2])

    with col_form:
        with st.form(f"form_manual_{st.session_state.form_manual_key}"):
            titulo = st.text_input("Título da vaga *", placeholder="Ex: Senior Data Engineer")
            empresa_sel = st.selectbox("Empresa *", options=["— selecione —"] + nomes_empresas)
            origem = st.selectbox("Origem", ["Indicação", "Headhunter", "LinkedIn", "WhatsApp", "Email", "Site próprio", "Outro"])
            contato = st.text_input("Contato", placeholder="Ex: João Silva — joao@empresa.com")
            descricao = st.text_area("Descrição da vaga *",
                placeholder="Cole aqui o texto completo da vaga...", height=250)

            col_prev, col_salvar = st.columns(2)
            preview_clicked = col_prev.form_submit_button("Analisar descrição", use_container_width=True)
            salvar_clicked = col_salvar.form_submit_button("Salvar vaga", type="primary", use_container_width=True)

            if preview_clicked or salvar_clicked:
                if not titulo:
                    st.error("Título é obrigatório.")
                elif empresa_sel == "— selecione —":
                    st.error("Selecione uma empresa.")
                elif not descricao:
                    st.error("Cole a descrição da vaga.")
                else:
                    stacks = extrair_stacks(descricao)
                    nivel = detectar_nivel(titulo)
                    modalidade = detectar_modalidade(descricao)
                    st.session_state.preview_stacks = {
                        "stacks": stacks, "nivel": nivel, "modalidade": modalidade,
                        "titulo": titulo, "empresa": empresa_sel,
                        "descricao": descricao, "origem": origem, "contato": contato,
                    }
                    if salvar_clicked:
                        id_empresa = mapa_empresas[empresa_sel]
                        inserir_vaga_manual(
                            titulo=titulo, id_empresa=id_empresa,
                            empresa_nome=empresa_sel, descricao=descricao,
                            origem=origem, contato=contato
                        )
                        st.success(f"Vaga '{titulo}' salva com sucesso!")
                        st.session_state.preview_stacks = None
                        st.session_state.form_manual_key += 1
                        st.rerun()

    with col_preview:
        if st.session_state.preview_stacks:
            p = st.session_state.preview_stacks
            st.subheader("Preview da análise")
            col_n, col_m = st.columns(2)
            col_n.metric("Nível detectado", p["nivel"])
            col_m.metric("Modalidade", p["modalidade"])
            st.divider()
            render_stacks(json.dumps(p["stacks"]))
            if not p["stacks"]:
                st.info("Nenhuma stack detectada.")
        else:
            st.info("Cole a descrição e clique em **Analisar descrição** para ver as stacks extraídas.")

    st.divider()

    @st.dialog("Cadastrar nova empresa")
    def modal_nova_empresa():
        from scrapers.company_search import buscar_empresa as _buscar
        if "modal_dados" not in st.session_state:
            st.session_state.modal_dados = {}
        col_b, col_btn = st.columns([3, 1])
        nome_busca = col_b.text_input("Nome da empresa", placeholder="Ex: Nubank")
        if col_btn.button("Buscar", use_container_width=True):
            if nome_busca:
                with st.spinner("Buscando..."):
                    dados = _buscar(nome_busca)
                    dados["nome"] = nome_busca
                    st.session_state.modal_dados = dados
        d = st.session_state.modal_dados
        with st.form("form_modal_empresa"):
            col1, col2 = st.columns(2)
            nome = col1.text_input("Nome *", value=d.get("nome", ""))
            ramo = col2.text_input("Ramo", value=d.get("ramo", ""))
            col3, col4, col5 = st.columns(3)
            cidade = col3.text_input("Cidade", value=d.get("cidade", ""))
            estado = col4.text_input("Estado", value=d.get("estado", ""))
            bairro = col5.text_input("Bairro", value="")
            url_vagas = st.text_input("URL Gupy", placeholder="https://empresa.gupy.io/")
            url_site_oficial = st.text_input("Site oficial", placeholder="https://www.empresa.com.br")
            if st.form_submit_button("Salvar empresa", type="primary", use_container_width=True):
                if not nome:
                    st.error("Nome é obrigatório.")
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
                                (id, nome, ramo, cidade, estado, url_vagas,
                                 ativa, data_cadastro, favicon_url, url_site_oficial)
                                VALUES (?, ?, ?, ?, ?, ?, true, ?, ?, ?)
                            """, [id_novo, nome, ramo, cidade, estado,
                                  url_vagas,
                                  date.today(), favicon_url, url_site_oficial])
                            con.close()
                            st.session_state.modal_dados = {}
                            st.success(f"{nome} cadastrada!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

    if st.button("+ Cadastrar nova empresa"):
        modal_nova_empresa()