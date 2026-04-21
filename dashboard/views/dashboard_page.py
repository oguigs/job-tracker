import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta
from database.schemas import TIMELINE, TIMELINE_LABELS
from database.candidaturas import atualizar_candidatura, negar_vaga
from dashboard.components import (
    carregar_vagas, carregar_logs, extrair_stacks_flat,
    grafico_stacks, get_favicon, render_stacks, calcular_scores_vagas,
    render_score_breakdown, render_diario, render_remuneracao,
    render_checklist_preparacao, render_vaga_card
)


def _dialog_dash(v):
    status_cand = v.get("candidatura_status") or "nao_inscrito"
    label_status = TIMELINE_LABELS.get(status_cand, "Não inscrito")
    data_fmt_v = str(v['data_coleta'])[:10] if str(v['data_coleta']) not in ['NaT','None','nan'] else 'N/A'
    col_info, col_link = st.columns([5, 1])
    col_info.caption(f"📅 {data_fmt_v} · {v['empresa']} · {label_status}")
    col_link.link_button("🔗 Ver vaga", v["link"], use_container_width=True)
    render_score_breakdown(int(v["id"]))
    render_checklist_preparacao(int(v["id"]))
    render_stacks(v["stacks"])
    st.divider()
    fases = ["nao_inscrito","inscrito","chamado","recrutador","fase_1","fase_2","fase_3"]
    cols_f = st.columns(len(fases))
    for idx, fase in enumerate(fases):
        ativo = fase == status_cand
        cols_f[idx].markdown(
            f"<div style='text-align:center;padding:4px;border-radius:6px;"
            f"background:{'#1D9E75' if ativo else '#f0f0f0'};"
            f"color:{'white' if ativo else '#888'};font-size:11px'>"
            f"{TIMELINE_LABELS[fase]}</div>", unsafe_allow_html=True)
    st.write("")
    with st.form(key=f"form_dash_{v['id']}"):
        col_s, col_o = st.columns([2, 3])
        novo_status = col_s.selectbox("Status", options=TIMELINE,
            format_func=lambda x: TIMELINE_LABELS[x],
            index=TIMELINE.index(status_cand) if status_cand in TIMELINE else 0,
            key=f"sel_dash_{v['id']}")
        observacao = col_o.text_input("Observação",
            value="" if str(v.get("candidatura_observacao") or "nan") == "nan" else str(v.get("candidatura_observacao") or ""),
            key=f"obs_dash_{v['id']}")
        col_s2, col_n2 = st.columns(2)
        with col_s2:
            if st.form_submit_button("Salvar", use_container_width=True):
                atualizar_candidatura(int(v["id"]), novo_status, novo_status, observacao)
                st.session_state[f"dialog_dash_{v['id']}"] = False
                st.rerun()
        with col_n2:
            if st.form_submit_button("Negar", use_container_width=True, type="secondary"):
                negar_vaga(int(v["id"]), observacao or f"Negada em: {status_cand}")
                st.session_state[f"dialog_dash_{v['id']}"] = False
                st.rerun()
    render_remuneracao(v)
    render_diario(int(v["id"]))


def render():
    # limpa dialogs abertos ao entrar na página
    for key in list(st.session_state.keys()):
        if key.startswith("dialog_"):
            st.session_state[key] = False

    st.title("Job Tracker — Data Engineering")
    df = carregar_vagas()
    scores = calcular_scores_vagas()
    df["score"] = df["id"].map(scores).fillna(0).astype(int)
    df = df.sort_values("score", ascending=False)

    # ── SIDEBAR ────────────────────────────────────────────────
    st.sidebar.divider()
    st.sidebar.header("Filtros")
    empresas = ["Todas"] + sorted(df["empresa"].unique().tolist())
    empresa_sel = st.sidebar.selectbox("Empresa", empresas)
    niveis = ["Todos"] + sorted(df["nivel"].dropna().unique().tolist())
    nivel_sel = st.sidebar.selectbox("Nível", niveis)
    modalidades = ["Todas"] + sorted(df["modalidade"].dropna().unique().tolist())
    modalidade_sel = st.sidebar.selectbox("Modalidade", modalidades)
    status_sel = st.sidebar.radio("Status", ["Ativas", "Encerradas", "Todas"])

    # ── FILTROS ────────────────────────────────────────────────
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

    # ── MÉTRICAS ───────────────────────────────────────────────
    em_processo = df_f[df_f["candidatura_status"].isin(
        ["chamado","recrutador","fase_1","fase_2","fase_3"]
    )].shape[0]
    col1, col2, col3, col4 = st.columns(4)
    if col1.button(f"**Total**\n\n{len(df_f)}", use_container_width=True):
        st.session_state["filtro_rapido_dash"] = None
    if col2.button(f"**Inscritas**\n\n{df_f[df_f['candidatura_status'] == 'inscrito'].shape[0]}", use_container_width=True):
        st.session_state["filtro_rapido_dash"] = "inscrito"
    if col3.button(f"**Não inscritas**\n\n{df_f[df_f['candidatura_status'] == 'nao_inscrito'].shape[0]}", use_container_width=True):
        st.session_state["filtro_rapido_dash"] = "nao_inscrito"
    if col4.button(f"**Em processo**\n\n{em_processo}", use_container_width=True):
        st.session_state["filtro_rapido_dash"] = "em_processo"

    filtro_dash = st.session_state.get("filtro_rapido_dash")
    if filtro_dash == "inscrito":
        df_f = df_f[df_f["candidatura_status"] == "inscrito"]
    elif filtro_dash == "nao_inscrito":
        df_f = df_f[df_f["candidatura_status"] == "nao_inscrito"]
    elif filtro_dash == "em_processo":
        df_f = df_f[df_f["candidatura_status"].isin(["chamado","recrutador","fase_1","fase_2","fase_3"])]

    st.divider()

    # ── STACKS ─────────────────────────────────────────────────
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

    # ── DISTRIBUIÇÃO ───────────────────────────────────────────
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

    # ── VAGAS (cards) ──────────────────────────────────────────
    st.subheader("Vagas")
    ontem = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d")
    vagas_list = list(df_f.iterrows())
    num_colunas = 4
    for i in range(0, len(vagas_list), num_colunas):
        grupo = vagas_list[i:i+num_colunas]
        cols = st.columns(num_colunas)
        for j in range(num_colunas):
            with cols[j]:
                if j >= len(grupo):
                    st.empty()
                    continue
                _, vaga = grupo[j]
                score = int(vaga.get("score", 0))
                is_nova = str(vaga["data_coleta"])[:10] >= ontem
                render_vaga_card(vaga, score, is_nova, key_prefix="dash")

    # ── DIALOGS ────────────────────────────────────────────────
    for _, vaga in df_f.iterrows():
        if not st.session_state.get(f"dialog_dash_{vaga['id']}"):
            continue
        dialog_fn = st.dialog(vaga['titulo'][:60], width="large")(_dialog_dash)
        dialog_fn(vaga)
        break

    st.divider()
    st.subheader("Histórico de execuções")
    st.dataframe(carregar_logs(), use_container_width=True)