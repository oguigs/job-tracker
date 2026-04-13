import streamlit as st
import plotly.express as px
from database.schemas import TIMELINE, TIMELINE_LABELS
from database.candidaturas import atualizar_candidatura, negar_vaga
from dashboard.components import (
    carregar_vagas, carregar_logs, extrair_stacks_flat,
    grafico_stacks, get_favicon, render_stacks
)

def render():
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

    df_f = df.copy()
    if empresa_sel != "Todas":
        df_f = df_f[df_f["empresa"] == empresa_sel]
    if nivel_sel != "Todos":
        df_f = df_f[df_f["nivel"] == nivel_sel]
    if modalidade_sel != "Todas":
        df_f = df_f[df_f["modalidade"] == modalidade_sel]
    if status_sel == "Ativas":
        df_f = df_f[df_f["ativa"] == True]
    elif status_sel == "Encerradas":
        df_f = df_f[df_f["ativa"] == False]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de vagas", len(df_f))
    col2.metric("Vagas ativas", df_f[df_f["ativa"] == True].shape[0])
    col3.metric("Vagas encerradas", df_f[df_f["ativa"] == False].shape[0])
    col4.metric("Empresas monitoradas", df_f["empresa"].nunique())

    st.divider()
    st.subheader("Stacks mais exigidas")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        fig = grafico_stacks(extrair_stacks_flat(df_f, "linguagens"), "Linguagens", "#1D9E75")
        if fig: st.plotly_chart(fig, use_container_width=True)
    with col_b:
        fig = grafico_stacks(extrair_stacks_flat(df_f, "cloud"), "Cloud", "#378ADD")
        if fig: st.plotly_chart(fig, use_container_width=True)
    with col_c:
        fig = grafico_stacks(extrair_stacks_flat(df_f, "processamento"), "Processamento", "#D85A30")
        if fig: st.plotly_chart(fig, use_container_width=True)

    col_d, col_e, col_f = st.columns(3)
    with col_d:
        fig = grafico_stacks(extrair_stacks_flat(df_f, "orquestracao"), "Orquestração", "#7F77DD")
        if fig: st.plotly_chart(fig, use_container_width=True)
    with col_e:
        fig = grafico_stacks(extrair_stacks_flat(df_f, "armazenamento"), "Armazenamento", "#BA7517")
        if fig: st.plotly_chart(fig, use_container_width=True)
    with col_f:
        fig = grafico_stacks(extrair_stacks_flat(df_f, "infraestrutura"), "Infraestrutura", "#888780")
        if fig: st.plotly_chart(fig, use_container_width=True)

    st.divider()
    col_nivel, col_modal = st.columns(2)
    with col_nivel:
        st.subheader("Distribuição por nível")
        df_nivel = df_f["nivel"].value_counts().reset_index()
        df_nivel.columns = ["nivel", "count"]
        fig = px.pie(df_nivel, values="count", names="nivel",
                     color_discrete_sequence=px.colors.qualitative.Set2,
                     template="plotly_white")
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
    with col_modal:
        st.subheader("Distribuição por modalidade")
        df_modal = df_f["modalidade"].value_counts().reset_index()
        df_modal.columns = ["modalidade", "count"]
        fig = px.pie(df_modal, values="count", names="modalidade",
                     color_discrete_sequence=["#1D9E75", "#378ADD", "#D85A30"],
                     template="plotly_white")
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Vagas")
    for _, vaga in df_f.iterrows():
        status_icon = "🟢" if vaga["ativa"] else "🔴"
        status_cand = vaga.get("candidatura_status") or "nao_inscrito"
        label_status = TIMELINE_LABELS.get(status_cand, "Não inscrito")
        favicon = get_favicon(vaga["empresa"], vaga.get("favicon_url") or "")

        with st.expander(f"{status_icon} {vaga['titulo']} — {vaga['empresa']} | {label_status}"):
            if st.button(f"Ver perfil de {vaga['empresa']}", key=f"perfil_d_{vaga['id']}"):
                st.query_params["empresa"] = vaga["empresa"]
                st.rerun()
            col_logo, col_info = st.columns([1, 5])
            if favicon:
                col_logo.image(favicon, width=40)
            data_fmt = str(vaga['data_coleta'])[:10]
            col_info.markdown(f"**{vaga['empresa']}** — {vaga['nivel']} | {vaga['modalidade']} | {data_fmt}")
            if not vaga["ativa"]:
                st.warning(f"Vaga encerrada em {vaga['data_encerramento']}")
            render_stacks(vaga["stacks"])
            st.link_button("Ver vaga", vaga["link"])
            st.divider()
            st.write("**Candidatura:**")
            fases = ["nao_inscrito", "inscrito", "chamado", "recrutador", "fase_1", "fase_2", "fase_3"]
            cols = st.columns(len(fases))
            for i, fase in enumerate(fases):
                ativo = fase == status_cand
                cols[i].markdown(
                    f"<div style='text-align:center; padding:4px; border-radius:6px; "
                    f"background:{'#1D9E75' if ativo else '#f0f0f0'}; "
                    f"color:{'white' if ativo else '#888'}; font-size:11px'>"
                    f"{TIMELINE_LABELS[fase]}</div>", unsafe_allow_html=True
                )
            st.write("")
            with st.form(key=f"form_d_{vaga['id']}"):
                col_s, col_o = st.columns([2, 3])
                novo_status = col_s.selectbox("Atualizar status", options=TIMELINE,
                    format_func=lambda x: TIMELINE_LABELS[x],
                    index=TIMELINE.index(status_cand) if status_cand in TIMELINE else 0,
                    key=f"sel_d_{vaga['id']}")
                observacao = col_o.text_input("Observação",
                    value=vaga.get("candidatura_observacao") or "",
                    key=f"obs_d_{vaga['id']}")
                col_s2, col_n2 = st.columns(2)
                with col_s2:
                    if st.form_submit_button("Salvar status", use_container_width=True):
                        atualizar_candidatura(vaga["id"], novo_status, novo_status, observacao)
                        st.success("Status atualizado!")
                        st.rerun()
                with col_n2:
                    if st.form_submit_button("Negar vaga", use_container_width=True, type="secondary"):
                        negar_vaga(vaga["id"], observacao or f"Negada em: {status_cand}")
                        st.warning("Vaga negada.")
                        st.rerun()

    st.divider()
    st.subheader("Histórico de execuções")
    st.dataframe(carregar_logs(), use_container_width=True)