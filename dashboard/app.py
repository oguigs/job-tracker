import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import duckdb
import pandas as pd
import json
from scrapers.company_search import buscar_empresa
from database.db_manager import inserir_endereco, listar_enderecos, deletar_endereco

DB_PATH = "data/curated/jobs.duckdb"

def conectar():
    return duckdb.connect(DB_PATH, read_only=True)

def conectar_rw():
    return duckdb.connect(DB_PATH, read_only=False)

def carregar_vagas():
    con = conectar()
    df = con.execute("""
        SELECT
            v.id, v.titulo, v.nivel, v.modalidade, v.stacks,
            v.link, v.fonte, v.data_coleta, v.ativa, v.data_encerramento,
            e.nome AS empresa, e.ramo, e.cidade, e.url_linkedin
        FROM fact_vaga v
        JOIN dim_empresa e ON v.id_empresa = e.id
        ORDER BY v.data_coleta DESC
    """).df()
    con.close()
    return df

def carregar_logs():
    con = conectar()
    df = con.execute("""
        SELECT empresa, vagas_encontradas, vagas_novas, status, data_execucao
        FROM log_coleta
        ORDER BY data_execucao DESC
        LIMIT 10
    """).df()
    con.close()
    return df

def carregar_empresas():
    con = conectar()
    df = con.execute("""
        SELECT id, nome, ramo, cidade, estado, url_gupy,
               url_linkedin, url_site_vagas, ativa, data_cadastro
        FROM dim_empresa
        ORDER BY nome
    """).df()
    con.close()
    return df

def extrair_stacks_flat(df, categoria):
    todas = []
    for stacks_json in df["stacks"].dropna():
        try:
            stacks = json.loads(stacks_json) if isinstance(stacks_json, str) else stacks_json
            todas.extend(stacks.get(categoria, []))
        except:
            pass
    return pd.Series(todas).value_counts()

st.set_page_config(page_title="Job Tracker", layout="wide")
pagina = st.sidebar.radio("Navegação", ["Dashboard", "Empresas"])

# ─── PÁGINA DASHBOARD ───────────────────────────────────────────
if pagina == "Dashboard":
    st.title("Job Tracker — Data Engineering")

    df = carregar_vagas()

    st.sidebar.divider()
    st.sidebar.header("Filtros")
    empresas = ["Todas"] + sorted(df["empresa"].unique().tolist())
    empresa_sel = st.sidebar.selectbox("Empresa", empresas)
    niveis = ["Todos"] + sorted(df["nivel"].dropna().unique().tolist())
    nivel_sel = st.sidebar.selectbox("Nível", niveis)
    modalidades = ["Todas"] + sorted(df["modalidade"].dropna().unique().tolist())
    modalidade_sel = st.sidebar.selectbox("Modalidade", modalidades)
    status_sel = st.sidebar.radio("Status", ["Ativas", "Encerradas", "Todas"])

    df_filtrado = df.copy()
    if empresa_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["empresa"] == empresa_sel]
    if nivel_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["nivel"] == nivel_sel]
    if modalidade_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["modalidade"] == modalidade_sel]
    if status_sel == "Ativas":
        df_filtrado = df_filtrado[df_filtrado["ativa"] == True]
    elif status_sel == "Encerradas":
        df_filtrado = df_filtrado[df_filtrado["ativa"] == False]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de vagas", len(df_filtrado))
    col2.metric("Vagas ativas", df_filtrado[df_filtrado["ativa"] == True].shape[0])
    col3.metric("Vagas encerradas", df_filtrado[df_filtrado["ativa"] == False].shape[0])
    col4.metric("Empresas monitoradas", df_filtrado["empresa"].nunique())

    st.divider()
    st.subheader("Stacks mais exigidas")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.caption("Linguagens")
        s = extrair_stacks_flat(df_filtrado, "linguagens")
        if not s.empty:
            st.bar_chart(s)
    with col_b:
        st.caption("Cloud")
        s = extrair_stacks_flat(df_filtrado, "cloud")
        if not s.empty:
            st.bar_chart(s)
    with col_c:
        st.caption("Processamento")
        s = extrair_stacks_flat(df_filtrado, "processamento")
        if not s.empty:
            st.bar_chart(s)

    col_d, col_e = st.columns(2)
    with col_d:
        st.caption("Orquestração")
        s = extrair_stacks_flat(df_filtrado, "orquestracao")
        if not s.empty:
            st.bar_chart(s)
    with col_e:
        st.caption("Armazenamento")
        s = extrair_stacks_flat(df_filtrado, "armazenamento")
        if not s.empty:
            st.bar_chart(s)

    st.divider()
    st.subheader("Vagas")

    for _, vaga in df_filtrado.iterrows():
        status_icon = "🟢" if vaga["ativa"] else "🔴"
        with st.expander(f"{status_icon} {vaga['titulo']} — {vaga['empresa']}"):
            col1, col2, col3 = st.columns(3)
            col1.write(f"**Nível:** {vaga['nivel']}")
            col2.write(f"**Modalidade:** {vaga['modalidade']}")
            col3.write(f"**Coletada em:** {vaga['data_coleta']}")
            if not vaga["ativa"]:
                st.warning(f"Vaga encerrada em {vaga['data_encerramento']}")
            try:
                stacks = json.loads(vaga["stacks"]) if isinstance(vaga["stacks"], str) else vaga["stacks"]
                if stacks:
                    st.write("**Stacks:**")
                    for categoria, termos in stacks.items():
                        st.write(f"- {categoria}: {', '.join(termos)}")
            except:
                pass
            st.link_button("Ver vaga", vaga["link"])

    st.divider()
    st.subheader("Histórico de execuções")
    st.dataframe(carregar_logs(), use_container_width=True)

# ─── PÁGINA EMPRESAS ────────────────────────────────────────────
elif pagina == "Empresas":
    st.title("Empresas monitoradas")

    df_empresas = carregar_empresas()

    st.subheader("Cadastrar nova empresa")

    if "dados_buscados" not in st.session_state:
        st.session_state.dados_buscados = {}

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

    with st.form("form_empresa"):
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome da empresa *", value=d.get("nome", ""))
        ramo = col2.text_input("Ramo", value=d.get("ramo", ""))

        col3, col4, col5 = st.columns(3)
        cidade = col3.text_input("Cidade", value=d.get("cidade", ""))
        bairro = col4.text_input("Bairro", value=d.get("bairro", ""))
        estado = col5.text_input("Estado", value=d.get("estado", ""))

        url_gupy = st.text_input("URL Gupy *", placeholder="https://empresa.gupy.io/")
        url_linkedin = st.text_input("URL LinkedIn", value=d.get("url_linkedin", ""))
        url_site_vagas = st.text_input("URL site de vagas", value=d.get("url_site_vagas", ""))

        submitted = st.form_submit_button("Salvar empresa")

        if submitted:
            if not nome:
                st.error("Nome da empresa é obrigatório.")
            elif not url_gupy:
                st.error("URL Gupy é obrigatória.")
            else:
                try:
                    con = conectar_rw()
                    existente = con.execute(
                        "SELECT id FROM dim_empresa WHERE nome = ?", [nome]
                    ).fetchone()

                    if existente:
                        st.warning(f"{nome} já está cadastrada.")
                    else:
                        id_novo = con.execute(
                            "SELECT nextval('seq_empresa')"
                        ).fetchone()[0]
                        con.execute("""
                            INSERT INTO dim_empresa
                            (id, nome, ramo, cidade, estado, url_gupy, url_linkedin, url_site_vagas)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, [id_novo, nome, ramo, cidade, estado,
                              url_gupy, url_linkedin, url_site_vagas])
                        con.close()
                        st.session_state.dados_buscados = {}
                        st.success(f"{nome} cadastrada com sucesso!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cadastrar: {e}")

    st.divider()
    st.subheader("Empresas cadastradas")

    for _, emp in df_empresas.iterrows():
        status = "🟢 Ativa" if emp["ativa"] else "🔴 Pausada"
        with st.expander(f"{emp['nome']} — {status}"):

            col1, col2 = st.columns(2)
            col1.write(f"**Ramo:** {emp['ramo'] or '—'}")
            col2.write(f"**Cadastrada em:** {emp['data_cadastro']}")

            if emp["url_gupy"]:
                st.write(f"**Gupy:** {emp['url_gupy']}")
            if emp["url_linkedin"]:
                st.write(f"**LinkedIn:** {emp['url_linkedin']}")
            if emp["url_site_vagas"]:
                st.write(f"**Site vagas:** {emp['url_site_vagas']}")

            st.divider()
            with st.form(key=f"form_edit_{emp['id']}"):
                st.caption("Editar informações")
                col1, col2 = st.columns(2)
                edit_ramo = col1.text_input("Ramo", value=emp["ramo"] or "", key=f"edit_ramo_{emp['id']}")
                edit_estado = col2.text_input("Estado", value=emp["estado"] or "", key=f"edit_estado_{emp['id']}")
                edit_gupy = st.text_input("URL Gupy", value=emp["url_gupy"] or "", key=f"edit_gupy_{emp['id']}")
                edit_linkedin = st.text_input("URL LinkedIn", value=emp["url_linkedin"] or "", key=f"edit_linkedin_{emp['id']}")
                edit_site = st.text_input("URL site de vagas", value=emp["url_site_vagas"] or "", key=f"edit_site_{emp['id']}")

                if st.form_submit_button("Salvar alterações"):
                    con = conectar_rw()
                    con.execute("""
                        UPDATE dim_empresa
                        SET ramo = ?, estado = ?, url_gupy = ?, url_linkedin = ?, url_site_vagas = ?
                        WHERE id = ?
                    """, [edit_ramo, edit_estado, edit_gupy, edit_linkedin, edit_site, emp["id"]])
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
            if emp["ativa"]:
                if st.button("Pausar monitoramento", key=f"pausar_{emp['id']}"):
                    con = conectar_rw()
                    con.execute("UPDATE dim_empresa SET ativa = false WHERE id = ?", [emp["id"]])
                    con.close()
                    st.rerun()
            else:
                if st.button("Reativar monitoramento", key=f"reativar_{emp['id']}"):
                    con = conectar_rw()
                    con.execute("UPDATE dim_empresa SET ativa = true WHERE id = ?", [emp["id"]])
                    con.close()
                    st.rerun()