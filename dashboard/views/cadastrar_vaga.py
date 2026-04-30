import streamlit as st
from database.vagas import inserir_vaga_manual
from transformers.stack_extractor import (
    extrair_stacks,
    detectar_nivel,
    detectar_modalidade,
    analisar_escopo_descricao,
)
from database.connection import db_connect
from datetime import date


def _analisar_descricao(titulo: str, descricao: str, modalidade_hint: str = ""):
    stacks = extrair_stacks(descricao)
    nivel = detectar_nivel(titulo)
    modalidade = detectar_modalidade(descricao, modalidade_hint)
    escopo = analisar_escopo_descricao(descricao)
    return stacks, nivel, modalidade, escopo


def _preview_editavel(p: dict):
    """Renderiza o painel de preview com stacks editáveis."""
    col_n, col_m = st.columns(2)
    nivel_opcoes = ["Júnior", "Pleno", "Sênior", "Especialista", "Estágio", "Não especificado"]
    nivel_idx = nivel_opcoes.index(p["nivel"]) if p["nivel"] in nivel_opcoes else 0
    novo_nivel = col_n.selectbox("Nível", nivel_opcoes, index=nivel_idx, key="prev_nivel")

    modal_opcoes = ["Remoto", "Híbrido", "Presencial", "Não especificado"]
    modal_idx = modal_opcoes.index(p["modalidade"]) if p["modalidade"] in modal_opcoes else 3
    nova_modal = col_m.selectbox("Modalidade", modal_opcoes, index=modal_idx, key="prev_modal")

    p["nivel"] = novo_nivel
    p["modalidade"] = nova_modal

    st.divider()

    # ── Stacks editáveis ─────────────────────────────────────────
    st.markdown("**Stacks extraídas** — remova as incorretas ou adicione manualmente")

    stacks = p.get("stacks", {})
    stacks_editadas: dict[str, list[str]] = {}

    for categoria, itens in stacks.items():
        if not itens:
            continue
        st.caption(categoria.upper())
        novos_itens = []
        cols = st.columns(3)
        for i, item in enumerate(itens):
            chave = f"stack_{categoria}_{i}"
            if cols[i % 3].checkbox(item, value=True, key=chave):
                novos_itens.append(item)
        stacks_editadas[categoria] = novos_itens

    # adicionar stack manual
    with st.expander("+ Adicionar stack manualmente"):
        col_nome, col_cat, col_add = st.columns([3, 2, 1])
        nova_stack = col_nome.text_input(
            "Nome", placeholder="Ex: dbt Cloud", key="nova_stack_nome", label_visibility="collapsed"
        )
        categorias_disponiveis = list(stacks.keys()) or [
            "linguagens",
            "cloud",
            "processamento",
            "armazenamento",
            "infraestrutura",
            "visualizacao",
            "integracao",
        ]
        nova_cat = col_cat.selectbox(
            "Categoria", categorias_disponiveis, key="nova_stack_cat", label_visibility="collapsed"
        )
        if col_add.button("Adicionar", key="btn_add_stack", use_container_width=True):
            if nova_stack.strip():
                stacks_editadas.setdefault(nova_cat, [])
                if nova_stack.strip() not in stacks_editadas[nova_cat]:
                    stacks_editadas[nova_cat].append(nova_stack.strip())
                st.session_state.preview_stacks["stacks"] = stacks_editadas
                st.rerun()

    p["stacks"] = stacks_editadas

    # ── Escopo da vaga ────────────────────────────────────────────
    escopo = p.get("escopo", {})
    tem_escopo = any(escopo.get(k) for k in ("responsabilidades", "obrigatorios", "desejaveis"))

    if tem_escopo:
        st.divider()
        st.markdown("**Escopo detectado**")

        if escopo.get("responsabilidades"):
            with st.expander(f"📋 Responsabilidades ({len(escopo['responsabilidades'])})"):
                for item in escopo["responsabilidades"]:
                    st.markdown(f"- {item}")

        if escopo.get("obrigatorios"):
            with st.expander(f"✅ Requisitos obrigatórios ({len(escopo['obrigatorios'])})"):
                for item in escopo["obrigatorios"]:
                    st.markdown(f"- {item}")

        if escopo.get("desejaveis"):
            with st.expander(f"⭐ Diferenciais ({len(escopo['desejaveis'])})"):
                for item in escopo["desejaveis"]:
                    st.markdown(f"- {item}")


def render():
    st.title("Cadastrar vaga manualmente")
    st.caption("Para vagas recebidas por indicação, headhunter ou LinkedIn direto.")

    with db_connect() as con:
        empresas_db = con.execute("SELECT id, nome FROM dim_empresa ORDER BY nome").fetchall()

    nomes_empresas = [e[1] for e in empresas_db]
    mapa_empresas = {e[1]: e[0] for e in empresas_db}

    if "preview_stacks" not in st.session_state:
        st.session_state.preview_stacks = None
    if "form_manual_key" not in st.session_state:
        st.session_state.form_manual_key = 0
    if "link_prefill" not in st.session_state:
        st.session_state.link_prefill = {}

    # ── BUSCAR POR LINK ──────────────────────────────────────────
    st.markdown("**Importar pelo link da vaga**")
    col_link, col_buscar = st.columns([5, 1], vertical_alignment="bottom")
    link_url = col_link.text_input(
        "link_vaga",
        label_visibility="collapsed",
        placeholder="Cole o link da vaga (Gupy, Greenhouse, Lever, 99jobs)...",
    )
    if col_buscar.button("🔍 Importar", use_container_width=True):
        if link_url.strip():
            with st.spinner("Buscando dados da vaga..."):
                from scrapers.link_parser import buscar_vaga_por_link

                dados = buscar_vaga_por_link(link_url.strip())
            if dados:
                st.session_state.link_prefill = dados
                st.session_state.preview_stacks = None
                st.session_state.form_manual_key += 1
                st.rerun()
            else:
                st.error("Plataforma não suportada ou vaga não encontrada. Preencha manualmente.")
        else:
            st.warning("Cole o link antes de importar.")

    prefill = st.session_state.link_prefill
    if prefill.get("titulo"):
        fonte_label = prefill.get("fonte", "").upper()
        st.success(f"✅ Vaga importada via **{fonte_label}** — revise os campos e salve.")

    st.divider()

    # ── FORMULÁRIO + PREVIEW ──────────────────────────────────────
    col_form, col_preview = st.columns([3, 2])

    with col_form:
        empresa_prefill = prefill.get("empresa", "")
        empresa_idx = 0
        opcoes_selectbox = ["— selecione —"] + nomes_empresas
        if empresa_prefill:
            empresa_lower = empresa_prefill.lower()
            for i, nome in enumerate(nomes_empresas):
                if (
                    nome.lower() == empresa_lower
                    or empresa_lower in nome.lower()
                    or nome.lower() in empresa_lower
                ):
                    empresa_idx = i + 1
                    break

        with st.form(f"form_manual_{st.session_state.form_manual_key}"):
            titulo = st.text_input(
                "Título da vaga *",
                value=prefill.get("titulo", ""),
                placeholder="Ex: Senior Data Engineer",
            )
            empresa_sel = st.selectbox("Empresa *", options=opcoes_selectbox, index=empresa_idx)

            if empresa_prefill and empresa_idx == 0:
                st.caption(
                    f"💡 Empresa detectada: **{empresa_prefill}** — não encontrada no banco. Selecione ou cadastre."
                )

            origens = [
                "Indicação",
                "Headhunter",
                "LinkedIn",
                "WhatsApp",
                "Email",
                "Site próprio",
                "Outro",
            ]
            origem_prefill = prefill.get("fonte", "")
            origem_idx = 0
            if origem_prefill in ("gupy", "greenhouse", "lever", "99jobs", "smartrecruiters"):
                origem_idx = origens.index("Site próprio")

            origem = st.selectbox("Origem", origens, index=origem_idx)
            contato = st.text_input("Contato", placeholder="Ex: João Silva — joao@empresa.com")
            descricao = st.text_area(
                "Descrição da vaga *",
                value=prefill.get("descricao", ""),
                placeholder="Cole aqui o texto completo da vaga...",
                height=250,
            )

            col_prev, col_salvar = st.columns(2)
            preview_clicked = col_prev.form_submit_button(
                "🔍 Analisar descrição", use_container_width=True
            )
            salvar_clicked = col_salvar.form_submit_button(
                "💾 Salvar vaga", type="primary", use_container_width=True
            )

            if preview_clicked or salvar_clicked:
                if not titulo:
                    st.error("Título é obrigatório.")
                elif empresa_sel == "— selecione —":
                    st.error("Selecione uma empresa.")
                elif not descricao:
                    st.error("Cole a descrição da vaga.")
                else:
                    stacks, nivel, modalidade, escopo = _analisar_descricao(
                        titulo, descricao, prefill.get("modalidade", "")
                    )
                    st.session_state.preview_stacks = {
                        "stacks": stacks,
                        "nivel": nivel,
                        "modalidade": modalidade,
                        "escopo": escopo,
                        "titulo": titulo,
                        "empresa": empresa_sel,
                        "descricao": descricao,
                        "origem": origem,
                        "contato": contato,
                    }
                    if salvar_clicked:
                        p = st.session_state.preview_stacks
                        id_empresa = mapa_empresas[empresa_sel]
                        link_salvo = prefill.get("link", "") or origem
                        inserir_vaga_manual(
                            titulo=titulo,
                            id_empresa=id_empresa,
                            empresa_nome=empresa_sel,
                            descricao=descricao,
                            origem=link_salvo,
                            contato=contato,
                            stacks_override=p["stacks"],
                            nivel_override=p["nivel"],
                            modalidade_override=p["modalidade"],
                        )
                        st.success(f"Vaga '{titulo}' salva com sucesso!")
                        st.session_state.preview_stacks = None
                        st.session_state.link_prefill = {}
                        st.session_state.form_manual_key += 1
                        st.rerun()

    with col_preview:
        if st.session_state.preview_stacks:
            st.subheader("Revisar antes de salvar")
            _preview_editavel(st.session_state.preview_stacks)
        else:
            st.info(
                "Cole a descrição e clique em **🔍 Analisar descrição** para ver e editar as stacks antes de salvar."
            )
            st.caption(
                "Você poderá remover stacks incorretas, adicionar manualmente e corrigir nível e modalidade."
            )

    st.divider()

    @st.dialog("Cadastrar nova empresa")
    def modal_nova_empresa():
        from scrapers.company_search import buscar_empresa as _buscar

        if "modal_dados" not in st.session_state:
            st.session_state.modal_dados = {}
        col_b, col_btn = st.columns([3, 1], vertical_alignment="bottom")
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
            url_site_oficial = st.text_input(
                "Site oficial", placeholder="https://www.empresa.com.br"
            )
            if st.form_submit_button("Salvar empresa", type="primary", use_container_width=True):
                if not nome:
                    st.error("Nome é obrigatório.")
                else:
                    try:
                        favicon_url = ""
                        if url_site_oficial:
                            dominio = (
                                url_site_oficial.replace("https://www.", "")
                                .replace("https://", "")
                                .split("/")[0]
                            )
                            favicon_url = (
                                f"https://www.google.com/s2/favicons?domain={dominio}&sz=64"
                            )
                        with db_connect() as con:
                            existente = con.execute(
                                "SELECT id FROM dim_empresa WHERE nome = ?", [nome]
                            ).fetchone()
                            if existente:
                                st.warning(f"{nome} já está cadastrada.")
                            else:
                                id_novo = con.execute("SELECT nextval('seq_empresa')").fetchone()[0]
                                con.execute(
                                    """
                                    INSERT INTO dim_empresa
                                    (id, nome, ramo, cidade, estado, url_vagas,
                                     ativa, data_cadastro, favicon_url, url_site_oficial)
                                    VALUES (?, ?, ?, ?, ?, ?, true, ?, ?, ?)
                                """,
                                    [
                                        id_novo,
                                        nome,
                                        ramo,
                                        cidade,
                                        estado,
                                        url_vagas,
                                        date.today(),
                                        favicon_url,
                                        url_site_oficial,
                                    ],
                                )
                                st.session_state.modal_dados = {}
                                st.success(f"{nome} cadastrada!")
                                st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

    if st.button("+ Cadastrar nova empresa"):
        modal_nova_empresa()
