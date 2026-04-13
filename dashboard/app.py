import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import duckdb
import pandas as pd
import json
import threading
import time
from scrapers.company_search import buscar_empresa
from database.db_manager import (
    inserir_endereco, listar_enderecos, deletar_endereco,
    atualizar_candidatura, negar_vaga, listar_vagas_negadas,
    TIMELINE, TIMELINE_LABELS
)
from dashboard.stack_config import get_stack_icon_url, get_stack_roadmap_url

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
            v.candidatura_status, v.candidatura_fase, v.candidatura_observacao,
            e.nome AS empresa, e.ramo, e.cidade, e.url_linkedin, e.favicon_url
        FROM fact_vaga v
        JOIN dim_empresa e ON v.id_empresa = e.id
        WHERE v.negada = false OR v.negada IS NULL
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
               url_linkedin, url_site_vagas, url_site_oficial,
               ativa, data_cadastro, favicon_url
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
    return pd.Series(todas).value_counts().reset_index().rename(
        columns={"index": "stack", 0: "count", "count": "count"}
    )

def grafico_stacks(df_counts, titulo: str, cor: str):
    if df_counts.empty:
        return None
    df_counts.columns = ["stack", "count"]
    fig = px.bar(
        df_counts,
        x="count",
        y="stack",
        orientation="h",
        title=titulo,
        color_discrete_sequence=[cor],
        template="plotly_white"
    )
    fig.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=40, b=0),
        yaxis=dict(autorange="reversed", title=""),
        xaxis=dict(title="Vagas"),
        showlegend=False,
        title_font_size=14
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>%{x} vagas<extra></extra>"
    )
    return fig

def carregar_perfil_empresa(nome: str):
    con = conectar()
    empresa = con.execute("""
        SELECT id, nome, ramo, cidade, estado, url_gupy,
               url_linkedin, url_site_vagas, url_site_oficial,
               favicon_url, data_cadastro
        FROM dim_empresa WHERE nome = ?
    """, [nome]).df()

    vagas = con.execute("""
        SELECT id, titulo, nivel, modalidade, stacks, link,
               data_coleta, ativa, candidatura_status
        FROM fact_vaga
        WHERE id_empresa = (SELECT id FROM dim_empresa WHERE nome = ?)
        AND (negada = false OR negada IS NULL)
        ORDER BY data_coleta DESC
    """, [nome]).df()

    logs = con.execute("""
        SELECT vagas_encontradas, vagas_novas, status, data_execucao
        FROM log_coleta
        WHERE empresa = ?
        ORDER BY data_execucao DESC
        LIMIT 5
    """, [nome]).df()

    enderecos = con.execute("""
        SELECT cidade, bairro FROM dim_empresa_endereco
        WHERE id_empresa = (SELECT id FROM dim_empresa WHERE nome = ?)
    """, [nome]).fetchall()

    con.close()
    return empresa, vagas, logs, enderecos

def get_favicon(nome: str, favicon_url: str = "") -> str:
    nome_arquivo = nome.lower().replace(" ", "_").replace("&", "e")
    caminho_local = f"dashboard/static/favicons/{nome_arquivo}.png"
    if os.path.exists(caminho_local):
        return caminho_local
    return favicon_url or ""

def render_stacks(stacks_json):
    """Renderiza stacks como badges com ícone e link para roadmap.sh."""
    try:
        stacks = json.loads(stacks_json) if isinstance(stacks_json, str) else stacks_json
        if not stacks:
            return
        st.write("**Stacks:**")
        for categoria, termos in stacks.items():
            if not termos:
                continue
            st.caption(categoria)
            badges_html = ""
            for termo in termos:
                icon_url = get_stack_icon_url(termo)
                roadmap_url = get_stack_roadmap_url(termo)
                icon_tag = (
                    f'<img src="{icon_url}" width="16" '
                    f'style="vertical-align:middle; margin-right:4px;">'
                    if icon_url else ""
                )
                estilo_base = (
                    "display:inline-flex; align-items:center; margin:2px; "
                    "padding:3px 10px; border-radius:12px; font-size:12px; "
                    "border:1px solid #ddd; text-decoration:none;"
                )
                if roadmap_url:
                    badges_html += (
                        f'<a href="{roadmap_url}" target="_blank" '
                        f'style="{estilo_base} background:#e8f5f0; color:#157A5A;">'
                        f'{icon_tag}{termo}</a>'
                    )
                else:
                    badges_html += (
                        f'<span style="{estilo_base} background:#f0f0f0; color:#555;">'
                        f'{icon_tag}{termo}</span>'
                    )
            st.markdown(badges_html, unsafe_allow_html=True)
            st.write("")
    except:
        pass

st.set_page_config(page_title="Job Tracker", layout="wide")

empresa_perfil = st.query_params.get("empresa", None)

if not empresa_perfil:
    pagina = st.sidebar.radio("Navegação", ["Dashboard", "Vagas", "Empresas", "Pipeline", "Configurações", "Vagas Negadas"])
else:
    pagina = "Perfil Empresa"
    if st.sidebar.button("← Voltar"):
        st.query_params.clear()
        st.rerun()

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
        s = extrair_stacks_flat(df_filtrado, "linguagens")
        fig = grafico_stacks(s, "Linguagens", "#1D9E75")
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col_b:
        s = extrair_stacks_flat(df_filtrado, "cloud")
        fig = grafico_stacks(s, "Cloud", "#378ADD")
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col_c:
        s = extrair_stacks_flat(df_filtrado, "processamento")
        fig = grafico_stacks(s, "Processamento", "#D85A30")
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    col_d, col_e, col_f = st.columns(3)
    with col_d:
        s = extrair_stacks_flat(df_filtrado, "orquestracao")
        fig = grafico_stacks(s, "Orquestração", "#7F77DD")
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col_e:
        s = extrair_stacks_flat(df_filtrado, "armazenamento")
        fig = grafico_stacks(s, "Armazenamento", "#BA7517")
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col_f:
        s = extrair_stacks_flat(df_filtrado, "infraestrutura")
        fig = grafico_stacks(s, "Infraestrutura", "#888780")
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    col_nivel, col_modal = st.columns(2)

    with col_nivel:
        st.subheader("Distribuição por nível")
        df_nivel = df_filtrado["nivel"].value_counts().reset_index()
        df_nivel.columns = ["nivel", "count"]
        fig = px.pie(
            df_nivel, values="count", names="nivel",
            color_discrete_sequence=px.colors.qualitative.Set2,
            template="plotly_white"
        )
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
        fig.update_traces(hovertemplate="<b>%{label}</b><br>%{value} vagas<extra></extra>")
        st.plotly_chart(fig, use_container_width=True)

    with col_modal:
        st.subheader("Distribuição por modalidade")
        df_modal = df_filtrado["modalidade"].value_counts().reset_index()
        df_modal.columns = ["modalidade", "count"]
        fig = px.pie(
            df_modal, values="count", names="modalidade",
            color_discrete_sequence=["#1D9E75", "#378ADD", "#D85A30"],
            template="plotly_white"
        )
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
        fig.update_traces(hovertemplate="<b>%{label}</b><br>%{value} vagas<extra></extra>")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Vagas")

    for _, vaga in df_filtrado.iterrows():
        status_icon = "🟢" if vaga["ativa"] else "🔴"
        status_cand = vaga.get("candidatura_status") or "nao_inscrito"
        label_status = TIMELINE_LABELS.get(status_cand, "Não inscrito")
        favicon = get_favicon(vaga["empresa"], vaga.get("favicon_url") or "")

        with st.expander(f"{status_icon} {vaga['titulo']} — {vaga['empresa']} | {label_status}"):
            if st.button(f"Ver perfil de {vaga['empresa']}", key=f"perfil_{vaga['id']}"):
                st.query_params["empresa"] = vaga["empresa"]
                st.rerun()
            col_logo, col_info = st.columns([1, 5])
            if favicon:
                col_logo.image(favicon, width=40)
            col_info.markdown(f"**{vaga['empresa']}** — {vaga['nivel']} | {vaga['modalidade']} | {vaga['data_coleta']}")

            if not vaga["ativa"]:
                st.warning(f"Vaga encerrada em {vaga['data_encerramento']}")

            render_stacks(vaga["stacks"])

            st.link_button("Ver vaga", vaga["link"])

            st.divider()
            st.write("**Candidatura:**")

            fases_ativas = ["nao_inscrito", "inscrito", "chamado", "recrutador",
                            "fase_1", "fase_2", "fase_3"]

            cols = st.columns(len(fases_ativas))
            for i, fase in enumerate(fases_ativas):
                ativo = fase == status_cand
                cols[i].markdown(
                    f"<div style='text-align:center; padding:4px; border-radius:6px; "
                    f"background:{'#1D9E75' if ativo else '#f0f0f0'}; "
                    f"color:{'white' if ativo else '#888'}; font-size:11px'>"
                    f"{TIMELINE_LABELS[fase]}</div>",
                    unsafe_allow_html=True
                )

            st.write("")

            with st.form(key=f"form_status_{vaga['id']}"):
                col_s, col_o = st.columns([2, 3])
                novo_status = col_s.selectbox(
                    "Atualizar status",
                    options=TIMELINE,
                    format_func=lambda x: TIMELINE_LABELS[x],
                    index=TIMELINE.index(status_cand) if status_cand in TIMELINE else 0,
                    key=f"sel_status_{vaga['id']}"
                )
                observacao = col_o.text_input(
                    "Observação",
                    value=vaga.get("candidatura_observacao") or "",
                    key=f"obs_{vaga['id']}"
                )

                col_salvar, col_negar = st.columns([1, 1])
                with col_salvar:
                    if st.form_submit_button("Salvar status", use_container_width=True):
                        atualizar_candidatura(
                            id_vaga=vaga["id"],
                            status=novo_status,
                            fase=novo_status,
                            observacao=observacao
                        )
                        st.success("Status atualizado!")
                        st.rerun()
                with col_negar:
                    if st.form_submit_button("Negar vaga", use_container_width=True, type="secondary"):
                        negar_vaga(
                            id_vaga=vaga["id"],
                            observacao=observacao or f"Negada em: {status_cand}"
                        )
                        st.warning("Vaga negada e removida da lista.")
                        st.rerun()

    st.divider()
    st.subheader("Histórico de execuções")
    st.dataframe(carregar_logs(), use_container_width=True)

# ─── PÁGINA VAGAS ───────────────────────────────────────────────
elif pagina == "Vagas":
    st.title("Vagas salvas")

    df = carregar_vagas()

    st.sidebar.divider()
    st.sidebar.header("Filtros")

    empresas = ["Todas"] + sorted(df["empresa"].unique().tolist())
    empresa_sel = st.sidebar.selectbox("Empresa", empresas)
    niveis = ["Todos"] + sorted(df["nivel"].dropna().unique().tolist())
    nivel_sel = st.sidebar.selectbox("Nível", niveis)
    modalidades = ["Todas"] + sorted(df["modalidade"].dropna().unique().tolist())
    modalidade_sel = st.sidebar.selectbox("Modalidade", modalidades)
    status_cand = ["Todos"] + list(TIMELINE_LABELS.values())
    status_cand_sel = st.sidebar.selectbox("Status candidatura", status_cand)
    status_vaga = st.sidebar.radio("Status da vaga", ["Ativas", "Encerradas", "Todas"])
    busca = st.sidebar.text_input("Buscar no título")

    df_filtrado = df.copy()
    if empresa_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["empresa"] == empresa_sel]
    if nivel_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["nivel"] == nivel_sel]
    if modalidade_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["modalidade"] == modalidade_sel]
    if status_vaga == "Ativas":
        df_filtrado = df_filtrado[df_filtrado["ativa"] == True]
    elif status_vaga == "Encerradas":
        df_filtrado = df_filtrado[df_filtrado["ativa"] == False]
    if status_cand_sel != "Todos":
        chave = next((k for k, v in TIMELINE_LABELS.items() if v == status_cand_sel), None)
        if chave:
            df_filtrado = df_filtrado[df_filtrado["candidatura_status"] == chave]
    if busca:
        df_filtrado = df_filtrado[df_filtrado["titulo"].str.contains(busca, case=False, na=False)]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", len(df_filtrado))
    col2.metric("Ativas", df_filtrado[df_filtrado["ativa"] == True].shape[0])
    col3.metric("Encerradas", df_filtrado[df_filtrado["ativa"] == False].shape[0])
    col4.metric("Inscritas", df_filtrado[df_filtrado["candidatura_status"] == "inscrito"].shape[0])

    st.divider()

    for _, vaga in df_filtrado.iterrows():
        status_icon = "🟢" if vaga["ativa"] else "🔴"
        status_cand_val = vaga.get("candidatura_status") or "nao_inscrito"
        label_status = TIMELINE_LABELS.get(status_cand_val, "Não inscrito")
        favicon = get_favicon(vaga["empresa"], vaga.get("favicon_url") or "")

        with st.expander(f"{status_icon} {vaga['titulo']} — {vaga['empresa']} | {label_status}"):
            if st.button(f"Ver perfil de {vaga['empresa']}", key=f"perfil_v_{vaga['id']}"):
                st.query_params["empresa"] = vaga["empresa"]
                st.rerun()
            col_logo, col_info = st.columns([1, 5])
            if favicon:
                col_logo.image(favicon, width=40)
            col_info.markdown(f"**{vaga['empresa']}** — {vaga['nivel']} | {vaga['modalidade']} | {vaga['data_coleta']}")

            if not vaga["ativa"]:
                st.warning(f"Vaga encerrada em {vaga['data_encerramento']}")

            render_stacks(vaga["stacks"])

            st.link_button("Ver vaga", vaga["link"])

            st.divider()
            st.write("**Candidatura:**")

            fases_ativas = ["nao_inscrito", "inscrito", "chamado", "recrutador",
                            "fase_1", "fase_2", "fase_3"]

            cols = st.columns(len(fases_ativas))
            for i, fase in enumerate(fases_ativas):
                ativo = fase == status_cand_val
                cols[i].markdown(
                    f"<div style='text-align:center; padding:4px; border-radius:6px; "
                    f"background:{'#1D9E75' if ativo else '#f0f0f0'}; "
                    f"color:{'white' if ativo else '#888'}; font-size:11px'>"
                    f"{TIMELINE_LABELS[fase]}</div>",
                    unsafe_allow_html=True
                )

            st.write("")

            with st.form(key=f"form_vaga_{vaga['id']}"):
                col_s, col_o = st.columns([2, 3])
                novo_status = col_s.selectbox(
                    "Atualizar status",
                    options=TIMELINE,
                    format_func=lambda x: TIMELINE_LABELS[x],
                    index=TIMELINE.index(status_cand_val) if status_cand_val in TIMELINE else 0,
                    key=f"sel_{vaga['id']}"
                )
                observacao = col_o.text_input(
                    "Observação",
                    value=vaga.get("candidatura_observacao") or "",
                    key=f"obs_{vaga['id']}"
                )

                col_salvar, col_negar = st.columns(2)
                with col_salvar:
                    if st.form_submit_button("Salvar status", use_container_width=True):
                        atualizar_candidatura(
                            id_vaga=vaga["id"],
                            status=novo_status,
                            fase=novo_status,
                            observacao=observacao
                        )
                        st.success("Status atualizado!")
                        st.rerun()
                with col_negar:
                    if st.form_submit_button("Negar vaga", use_container_width=True, type="secondary"):
                        negar_vaga(
                            id_vaga=vaga["id"],
                            observacao=observacao or f"Negada em: {status_cand_val}"
                        )
                        st.warning("Vaga negada!")
                        st.rerun()

# ─── PÁGINA EMPRESAS ────────────────────────────────────────────
elif pagina == "Empresas":
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

        url_gupy = st.text_input("URL Gupy *", placeholder="https://empresa.gupy.io/")
        url_linkedin = st.text_input("URL LinkedIn", value=d.get("url_linkedin", ""))
        url_site_vagas = st.text_input("URL site de vagas", value=d.get("url_site_vagas", ""))
        url_site_oficial = st.text_input(
            "Site oficial da empresa",
            placeholder="https://www.empresa.com.br",
            help="Usado para buscar o logo da empresa automaticamente"
        )

        submitted = st.form_submit_button("Salvar empresa")

        if submitted:
            if not nome:
                st.error("Nome da empresa é obrigatório.")
            elif not url_gupy:
                st.error("URL Gupy é obrigatória.")
            else:
                try:
                    if url_site_oficial:
                        dominio = url_site_oficial.replace("https://www.", "").replace("https://", "").split("/")[0]
                        favicon_url = f"https://www.google.com/s2/favicons?domain={dominio}&sz=64"
                    else:
                        favicon_url = ""

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
                            (id, nome, ramo, cidade, estado, url_gupy, url_linkedin,
                             url_site_vagas, url_site_oficial, favicon_url)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, [id_novo, nome, ramo, cidade, estado,
                              url_gupy, url_linkedin, url_site_vagas,
                              url_site_oficial, favicon_url])
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

            if emp["url_gupy"]:
                st.write(f"**Gupy:** {emp['url_gupy']}")
            if emp["url_linkedin"]:
                st.write(f"**LinkedIn:** {emp['url_linkedin']}")
            if emp["url_site_vagas"]:
                st.write(f"**Site vagas:** {emp['url_site_vagas']}")
            if emp.get("url_site_oficial"):
                st.write(f"**Site oficial:** {emp['url_site_oficial']}")

            st.divider()
            with st.form(key=f"form_edit_{emp['id']}"):
                st.caption("Editar informações")
                col1, col2 = st.columns(2)
                edit_ramo = col1.text_input("Ramo", value=emp["ramo"] or "", key=f"edit_ramo_{emp['id']}")
                edit_estado = col2.text_input("Estado", value=emp["estado"] or "", key=f"edit_estado_{emp['id']}")
                edit_gupy = st.text_input("URL Gupy", value=emp["url_gupy"] or "", key=f"edit_gupy_{emp['id']}")
                edit_linkedin = st.text_input("URL LinkedIn", value=emp["url_linkedin"] or "", key=f"edit_linkedin_{emp['id']}")
                edit_site = st.text_input("URL site de vagas", value=emp["url_site_vagas"] or "", key=f"edit_site_{emp['id']}")
                edit_site_oficial = st.text_input(
                    "Site oficial da empresa",
                    value=emp.get("url_site_oficial") or "",
                    placeholder="https://www.empresa.com.br",
                    key=f"edit_site_oficial_{emp['id']}"
                )

                if st.form_submit_button("Salvar alterações"):
                    if edit_site_oficial:
                        dominio = edit_site_oficial.replace("https://www.", "").replace("https://", "").split("/")[0]
                        novo_favicon = f"https://www.google.com/s2/favicons?domain={dominio}&sz=64"
                    else:
                        novo_favicon = get_favicon(emp["nome"], emp.get("favicon_url") or "")
                    con = conectar_rw()
                    con.execute("""
                        UPDATE dim_empresa
                        SET ramo = ?, estado = ?, url_gupy = ?, url_linkedin = ?,
                            url_site_vagas = ?, url_site_oficial = ?, favicon_url = ?
                        WHERE id = ?
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

# ─── PÁGINA PIPELINE ────────────────────────────────────────────
elif pagina == "Pipeline":
    st.title("Pipeline")
    st.caption("Dispare a coleta de vagas em background e acompanhe o status.")

    con = duckdb.connect("data/curated/jobs.duckdb")
    empresas = con.execute("""
        SELECT nome, url_gupy FROM dim_empresa
        WHERE ativa = true AND url_gupy IS NOT NULL
    """).fetchall()
    con.close()

    st.metric("Empresas ativas", len(empresas))
    for nome, url in empresas:
        st.write(f"- {nome} — `{url}`")

    st.divider()

    if "pipeline_estado" not in st.session_state:
        st.session_state.pipeline_estado = {
            "rodando": False,
            "concluido": False,
            "log": [],
            "total_encontradas": 0,
            "total_novas": 0
        }

    estado = st.session_state.pipeline_estado

    def rodar_em_background(empresas, estado):
        from main import processar_empresa
        from database.db_manager import criar_tabelas, ultima_execucao_sucesso

        criar_tabelas()
        total_encontradas = 0
        total_novas = 0

        for nome, url_gupy in empresas:
            horas = ultima_execucao_sucesso(nome)
            if horas < 12:
                estado["log"].append(f"⏭ {nome} — pulada (última execução há {horas}h)")
                continue
            estado["log"].append(f"▶ Iniciando {nome}...")
            encontradas, novas, erro = processar_empresa(nome, url_gupy)
            if erro and "cooldown" not in erro:
                estado["log"].append(f"✗ {nome} — erro: {erro[:60]}")
            else:
                total_encontradas += encontradas
                total_novas += novas
                estado["log"].append(f"✓ {nome} — {encontradas} vagas | {novas} novas")

        estado["total_encontradas"] = total_encontradas
        estado["total_novas"] = total_novas
        estado["log"].append("✓ Pipeline concluído!")
        estado["rodando"] = False
        estado["concluido"] = True

    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button(
            "Rodar pipeline",
            type="primary",
            use_container_width=True,
            disabled=estado["rodando"]
        ):
            estado["rodando"] = True
            estado["concluido"] = False
            estado["log"] = []
            estado["total_encontradas"] = 0
            estado["total_novas"] = 0
            thread = threading.Thread(
                target=rodar_em_background,
                args=(empresas, estado),
                daemon=True
            )
            thread.start()
            st.rerun()

    with col_btn2:
        if st.button("Limpar log", use_container_width=True):
            estado["log"] = []
            estado["concluido"] = False
            estado["total_encontradas"] = 0
            estado["total_novas"] = 0
            st.rerun()

    if estado["rodando"]:
        st.info("Pipeline rodando em background — você pode navegar normalmente.")

    if estado["concluido"]:
        col1, col2 = st.columns(2)
        col1.metric("Vagas encontradas", estado["total_encontradas"])
        col2.metric("Vagas novas", estado["total_novas"])
        st.success("Pipeline concluído!")

    if estado["log"]:
        st.divider()
        st.write("**Log de execução:**")
        st.code("\n".join(estado["log"]), language=None)

    if estado["rodando"]:
        time.sleep(3)
        st.rerun()

# ─── PÁGINA CONFIGURAÇÕES ───────────────────────────────────────
elif pagina == "Configurações":
    st.title("Configurações")
    st.caption("Gerencie os filtros de coleta de vagas.")

    from database.db_manager import adicionar_filtro, remover_filtro, listar_filtros

    df_filtros = listar_filtros()

    col_interesse, col_bloqueio = st.columns(2)

    with col_interesse:
        st.subheader("Palavras de interesse")
        st.caption("Vagas com esses termos no título serão coletadas.")
        df_i = df_filtros[df_filtros["tipo"] == "interesse"]
        for _, row in df_i.iterrows():
            col_t, col_d = st.columns([4, 1])
            col_t.write(f"`{row['termo']}`")
            if col_d.button("Remover", key=f"rem_i_{row['id']}"):
                remover_filtro(row["id"])
                st.rerun()

        with st.form("form_interesse"):
            novo_interesse = st.text_input("Adicionar termo de interesse")
            if st.form_submit_button("Adicionar"):
                if novo_interesse:
                    adicionar_filtro("interesse", novo_interesse.lower())
                    st.success(f"'{novo_interesse}' adicionado!")
                    st.rerun()

    with col_bloqueio:
        st.subheader("Palavras bloqueadas")
        st.caption("Vagas com esses termos no título serão ignoradas.")
        df_b = df_filtros[df_filtros["tipo"] == "bloqueio"]
        for _, row in df_b.iterrows():
            col_t, col_d = st.columns([4, 1])
            col_t.write(f"`{row['termo']}`")
            if col_d.button("Remover", key=f"rem_b_{row['id']}"):
                remover_filtro(row["id"])
                st.rerun()

        with st.form("form_bloqueio"):
            novo_bloqueio = st.text_input("Adicionar termo bloqueado")
            if st.form_submit_button("Adicionar"):
                if novo_bloqueio:
                    adicionar_filtro("bloqueio", novo_bloqueio.lower())
                    st.success(f"'{novo_bloqueio}' bloqueado!")
                    st.rerun()

# ─── PÁGINA VAGAS NEGADAS ───────────────────────────────────────
elif pagina == "Vagas Negadas":
    st.title("Vagas Negadas")
    st.caption("Vagas que você optou por não seguir.")

    df_negadas = listar_vagas_negadas()

    if df_negadas.empty:
        st.info("Nenhuma vaga negada ainda.")
    else:
        st.metric("Total de vagas negadas", len(df_negadas))
        st.divider()

        for _, vaga in df_negadas.iterrows():
            with st.expander(f"{vaga['titulo']} — {vaga['empresa']}"):
                col1, col2 = st.columns(2)
                col1.write(f"**Negada em:** {vaga['candidatura_data']}")
                col2.write(f"**Fase ao negar:** {TIMELINE_LABELS.get(vaga['candidatura_fase'], '—')}")

                if vaga["candidatura_observacao"]:
                    st.write(f"**Observação:** {vaga['candidatura_observacao']}")

                if st.button("Reativar vaga", key=f"reativar_negada_{vaga['id']}"):
                    con = conectar_rw()
                    con.execute("""
                        UPDATE fact_vaga
                        SET negada = false,
                            candidatura_status = 'nao_inscrito',
                            candidatura_fase = null,
                            candidatura_observacao = null,
                            candidatura_data = null
                        WHERE id = ?
                    """, [vaga["id"]])
                    con.close()
                    st.success("Vaga reativada!")
                    st.rerun()

# ─── PÁGINA PERFIL EMPRESA ──────────────────────────────────────
elif pagina == "Perfil Empresa":
    empresa_df, vagas_df, logs_df, enderecos = carregar_perfil_empresa(empresa_perfil)

    if empresa_df.empty:
        st.error(f"Empresa '{empresa_perfil}' não encontrada.")
    else:
        emp = empresa_df.iloc[0]
        favicon = get_favicon(emp["nome"], emp.get("favicon_url") or "")

        col_logo, col_titulo = st.columns([1, 6])
        if favicon:
            col_logo.image(favicon, width=64)
        col_titulo.title(emp["nome"])
        col_titulo.caption(f"{emp['ramo'] or '—'} · {emp['cidade'] or '—'}/{emp['estado'] or '—'} · Cadastrada em {emp['data_cadastro']}")

        cols_links = st.columns(4)
        if emp["url_gupy"]:
            cols_links[0].link_button("Portal Gupy", emp["url_gupy"], use_container_width=True)
        if emp["url_linkedin"]:
            cols_links[1].link_button("LinkedIn", emp["url_linkedin"], use_container_width=True)
        if emp["url_site_vagas"]:
            cols_links[2].link_button("Site de vagas", emp["url_site_vagas"], use_container_width=True)
        if emp.get("url_site_oficial"):
            cols_links[3].link_button("Site oficial", emp["url_site_oficial"], use_container_width=True)

        if enderecos:
            st.write("**Polos:**")
            for cidade, bairro in enderecos:
                st.write(f"- {cidade} / {bairro or '—'}")

        st.divider()

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Total de vagas", len(vagas_df))
        col_m2.metric("Vagas ativas", vagas_df[vagas_df["ativa"] == True].shape[0])
        col_m3.metric("Inscritas", vagas_df[vagas_df["candidatura_status"] == "inscrito"].shape[0])

        st.divider()
        st.subheader("Stacks mais pedidas")

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            s = extrair_stacks_flat(vagas_df, "linguagens")
            fig = grafico_stacks(s, "Linguagens", "#1D9E75")
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        with col_b:
            s = extrair_stacks_flat(vagas_df, "cloud")
            fig = grafico_stacks(s, "Cloud", "#378ADD")
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        with col_c:
            s = extrair_stacks_flat(vagas_df, "processamento")
            fig = grafico_stacks(s, "Processamento", "#D85A30")
            if fig:
                st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("Vagas")

        for _, vaga in vagas_df.iterrows():
            status_icon = "🟢" if vaga["ativa"] else "🔴"
            status_cand_val = vaga.get("candidatura_status") or "nao_inscrito"
            label_status = TIMELINE_LABELS.get(status_cand_val, "Não inscrito")

            with st.expander(f"{status_icon} {vaga['titulo']} | {label_status}"):
                col1, col2, col3 = st.columns(3)
                col1.write(f"**Nível:** {vaga['nivel']}")
                col2.write(f"**Modalidade:** {vaga['modalidade']}")
                col3.write(f"**Coletada em:** {vaga['data_coleta']}")

                render_stacks(vaga["stacks"])

                st.link_button("Ver vaga", vaga["link"])

        st.divider()
        st.subheader("Histórico do pipeline")
        if not logs_df.empty:
            st.dataframe(logs_df, use_container_width=True)
        else:
            st.caption("Nenhuma execução registrada ainda.")