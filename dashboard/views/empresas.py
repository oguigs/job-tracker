import streamlit as st
from scrapers.company_search import buscar_empresa
from database.empresas import inserir_endereco, listar_enderecos, deletar_endereco
from dashboard.components import carregar_empresas, conectar_rw, get_favicon
from database.connection import db_connect
from datetime import date


def safe(v):
    return "" if v is None or str(v) in ["None","nan","<NA>","NaT",""] else str(v)


def detectar_plataforma(url: str) -> str:
    if "gupy.io" in url: return "Gupy"
    if "greenhouse.io" in url: return "Greenhouse"
    if "inhire.app" in url: return "Inhire"
    if "smartrecruiters.com" in url: return "SmartRecruiters"
    return "Desconhecida"


def buscar_vagas_empresa(nome: str, url: str):
    from utils import safe_str
    plataforma = detectar_plataforma(url)
    if plataforma == "Greenhouse":
        from main import processar_empresa_greenhouse
        slug = url.split("greenhouse.io/")[-1].split("/")[0]
        return processar_empresa_greenhouse(nome, slug)
    elif plataforma == "Inhire":
        from main import processar_empresa_inhire
        return processar_empresa_inhire(nome, url)
    elif plataforma == "SmartRecruiters":
        from main import processar_empresa_smartrecruiters
        return processar_empresa_smartrecruiters(nome, url)
    else:
        from main import processar_empresa
        return processar_empresa(nome, url)


def render():
    st.title("Empresas monitoradas")
    df_empresas = carregar_empresas()

    # ── CADASTRAR ──────────────────────────────────────────────
    with st.expander("➕ Cadastrar nova empresa", expanded=False):
        if "dados_buscados" not in st.session_state:
            st.session_state.dados_buscados = {}
        if "form_key" not in st.session_state:
            st.session_state.form_key = 0

        col_busca, col_btn = st.columns([3, 1])
        nome_busca = col_busca.text_input("Nome da empresa", placeholder="Ex: Nubank")
        col_btn.text_input("Nome da empresa")
        if col_btn.button("🔍 Buscar", use_container_width=True):
            if nome_busca:
                with st.spinner(f"Buscando {nome_busca}..."):
                    dados = buscar_empresa(nome_busca)
                    dados["nome"] = nome_busca
                    st.session_state.dados_buscados = dados
                st.success("Informações encontradas! Revise antes de salvar.")
            else:
                st.warning("Digite o nome da empresa primeiro.")

        d = st.session_state.dados_buscados
        with st.form(f"form_empresa_{st.session_state.form_key}"):
            col1, col2 = st.columns(2)
            nome = col1.text_input("Nome *", value=d.get("nome", ""))
            ramo = col2.text_input("Ramo", value=d.get("ramo", ""))
            col3, col4 = st.columns(2)
            cidade = col3.text_input("Cidade", value=d.get("cidade", ""))
            estado = col4.text_input("Estado", value=d.get("estado", ""))
            url_vagas_input = st.text_input("URL de vagas *",
                placeholder="Gupy, Greenhouse, Inhire ou SmartRecruiters")
            url_site_oficial = st.text_input("Site oficial",
                placeholder="https://www.empresa.com.br")

            if url_vagas_input:
                plat = detectar_plataforma(url_vagas_input)
                st.caption(f"Plataforma detectada: **{plat}**")

            if st.form_submit_button("💾 Salvar empresa", use_container_width=True):
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
                            st.success(f"✅ {nome} cadastrada com sucesso!")
                            st.cache_data.clear()
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

    st.divider()

    # ── CONTROLES GLOBAIS ──────────────────────────────────────
    col_stats, col_on, col_off = st.columns([3, 1, 1])
    ativas = df_empresas[df_empresas["ativa"] == True].shape[0]
    col_stats.markdown(f"**{len(df_empresas)} empresas** — {ativas} ativas · {len(df_empresas)-ativas} pausadas")
    if col_on.button("✅ Ativar todas", use_container_width=True):
        con = conectar_rw()
        con.execute("UPDATE dim_empresa SET ativa = true")
        con.close()
        st.cache_data.clear()
        st.rerun()
    if col_off.button("⏸ Pausar todas", use_container_width=True):
        con = conectar_rw()
        con.execute("UPDATE dim_empresa SET ativa = false")
        con.close()
        st.cache_data.clear()
        st.rerun()

    st.divider()

# ── LISTA DE EMPRESAS ──────────────────────────────────────
    empresas_list = list(df_empresas.iterrows())
    for i in range(0, len(empresas_list), 5):
        grupo = empresas_list[i:i+5]
        cols = st.columns(5)
        for j in range(5):
            with cols[j]:
                if j >= len(grupo):
                    st.empty()
                    continue
                _, emp = grupo[j]
                ativa = str(emp.get("ativa","")) not in ["False","0","nan","None","<NA>"]
                favicon = get_favicon(emp["nome"], safe(emp.get("favicon_url")))
                url_v = safe(emp.get("url_vagas"))
                plataforma = detectar_plataforma(url_v) if url_v else "—"
                status_cor = "#1D9E75" if ativa else "#888"
                status_label = "Ativa" if ativa else "Pausada"

                with st.container(border=True):
                    col_fav, col_nome, col_badge = st.columns([0.5, 3, 1.5])
                    if favicon:
                        col_fav.image(favicon, width=20)
                    col_nome.markdown(f"**{emp['nome']}**")
                    col_badge.markdown(
                        f"<div style='text-align:right'>"
                        f"<span style='background:{status_cor};color:white;font-size:11px;"
                        f"font-weight:600;padding:3px 8px;border-radius:10px'>{status_label}</span></div>",
                        unsafe_allow_html=True)

                    st.caption(f"🔌 {plataforma}")

                    if st.button("⚙️ Configurar", key=f"cfg_{int(emp['id'])}", use_container_width=True):
                        st.session_state["config_emp_atual"] = int(emp['id'])

    # ── DIALOGS DE CONFIGURAÇÃO ────────────────────────────────
    emp_id_atual = st.session_state.get("config_emp_atual")
    if emp_id_atual:
        rows = df_empresas[df_empresas["id"] == emp_id_atual]
        if not rows.empty:
            emp = rows.iloc[0]
            ativa = str(emp.get("ativa","")) not in ["False","0","nan","None","<NA>"]
            url_v = safe(emp.get("url_vagas"))
            url_of = safe(emp.get("url_site_oficial"))

            @st.dialog(emp['nome'], width="large")
            def config_empresa():
                tab_info, tab_polos, tab_acoes = st.tabs(["📋 Informações", "📍 Polos", "⚡ Ações"])

                with tab_info:
                    if url_v: st.caption(f"🔗 {url_v}")
                    if url_of: st.caption(f"🌐 {url_of}")
                    st.caption(f"📅 {str(emp['data_cadastro'])[:10]}")
                    st.divider()
                    with st.form(key=f"form_edit_{int(emp['id'])}"):
                        col1, col2 = st.columns(2)
                        edit_ramo = col1.text_input("Ramo", value=safe(emp["ramo"]))
                        edit_estado = col2.text_input("Estado", value=safe(emp["estado"]))
                        edit_url = st.text_input("URL de vagas", value=url_v)
                        if edit_url:
                            st.caption(f"Plataforma: **{detectar_plataforma(edit_url)}**")
                        edit_site = st.text_input("Site oficial", value=url_of)
                        if st.form_submit_button("💾 Salvar", use_container_width=True):
                            novo_favicon = safe(emp.get("favicon_url"))
                            if edit_site:
                                dominio = edit_site.replace("https://www.","").replace("https://","").split("/")[0]
                                novo_favicon = f"https://www.google.com/s2/favicons?domain={dominio}&sz=64"
                            con = conectar_rw()
                            con.execute("""
                                UPDATE dim_empresa SET ramo=?, estado=?, url_vagas=?, url_site_oficial=?, favicon_url=?
                                WHERE id=?
                            """, [edit_ramo, edit_estado, edit_url, edit_site, novo_favicon, int(emp['id'])])
                            con.close()
                            st.session_state["config_emp_atual"] = None
                            st.success("Atualizado!")
                            st.cache_data.clear()
                            st.rerun()

                with tab_polos:
                    enderecos = listar_enderecos(int(emp['id']))
                    if enderecos:
                        for id_end, cid, bairro in enderecos:
                            col_end, col_del = st.columns([4, 1])
                            col_end.write(f"📍 {cid} / {bairro or '—'}")
                            if col_del.button("🗑", key=f"del_end_{id_end}"):
                                deletar_endereco(id_end)
                                st.cache_data.clear()
                                st.rerun()
                    else:
                        st.caption("Nenhum polo cadastrado.")
                    with st.form(key=f"form_end_{int(emp['id'])}"):
                        col_c, col_b, col_add = st.columns([2, 2, 1])
                        nova_cidade = col_c.text_input("Cidade")
                        novo_bairro = col_b.text_input("Bairro")
                        if col_add.form_submit_button("➕"):
                            if nova_cidade:
                                inserir_endereco(int(emp['id']), nova_cidade, novo_bairro)
                                st.cache_data.clear()
                                st.rerun()

                with tab_acoes:
                    col_a1, col_a2 = st.columns(2)
                    if ativa:
                        if col_a1.button("⏸ Pausar", use_container_width=True):
                            con = conectar_rw()
                            con.execute("UPDATE dim_empresa SET ativa=false WHERE id=?", [int(emp['id'])])
                            con.close()
                            st.session_state["config_emp_atual"] = None
                            st.cache_data.clear()
                            st.rerun()
                    else:
                        if col_a1.button("▶️ Ativar", use_container_width=True):
                            con = conectar_rw()
                            con.execute("UPDATE dim_empresa SET ativa=true WHERE id=?", [int(emp['id'])])
                            con.close()
                            st.session_state["config_emp_atual"] = None
                            st.cache_data.clear()
                            st.rerun()
                    st.divider()
                    if st.button("🗑 Deletar empresa", key=f"del_emp_{emp['id']}", 
                                 use_container_width=True, type="secondary"):
                        confirmar_key = f"confirmar_del_{emp['id']}"
                        st.session_state[confirmar_key] = True
                    if st.session_state.get(f"confirmar_del_{emp['id']}"):
                        st.warning(f"Tem certeza que deseja deletar **{emp['nome']}**? Isso remove a empresa e todas as suas vagas.")
                        col_sim, col_nao = st.columns(2)
                        if col_sim.button("✅ Sim, deletar", key=f"sim_del_{emp['id']}", type="primary"):
                            with db_connect() as con:
                                con.execute("DELETE FROM fact_vaga WHERE id_empresa = ?", [int(emp['id'])])
                                con.execute("DELETE FROM dim_empresa_endereco WHERE id_empresa = ?", [int(emp['id'])])
                                con.execute("DELETE FROM dim_empresa WHERE id = ?", [int(emp['id'])])
                            st.cache_data.clear()
                            st.toast(f"✅ {emp['nome']} deletada!")
                            st.rerun()
                        if col_nao.button("❌ Cancelar", key=f"nao_del_{emp['id']}"):
                            st.session_state[f"confirmar_del_{emp['id']}"] = False
                            st.rerun()        
                    if col_a2.button("🔄 Buscar vagas", use_container_width=True):
                        with st.spinner(f"Coletando {emp['nome']}..."):
                            try:
                                encontradas, novas, erro = buscar_vagas_empresa(emp["nome"], url_v)
                                if erro:
                                    st.error(f"Erro: {erro}")
                                else:
                                    st.success(f"✅ {encontradas} encontradas | {novas} novas")
                            except Exception as e:
                                st.error(f"Erro: {e}")

            config_empresa()