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
from dashboard.ui_components import render_dialog_vaga
from database.ats_score import listar_ats_scores

def _dialog_dash(v):
    render_dialog_vaga(v, prefix="dash")


def render():
    # limpa dialogs abertos ao entrar na página
    for key in list(st.session_state.keys()):
        if key.startswith("dialog_"):
            st.session_state[key] = False

    st.title("Job Tracker — Data Engineering")
    df = carregar_vagas()
    scores = calcular_scores_vagas()
    ats_scores = listar_ats_scores()
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

     # ── TERMÔMETRO DE EMPREGABILIDADE ─────────────────────────
    scores_todos = calcular_scores_vagas()
    if scores_todos:
        vagas_70 = sum(1 for s in scores_todos.values() if s >= 70)
        vagas_40 = sum(1 for s in scores_todos.values() if 40 <= s < 70)
        total_scores = len(scores_todos)
        pct_70 = round(vagas_70 / total_scores * 100) if total_scores > 0 else 0
        cor_term = "#1D9E75" if pct_70 >= 20 else "#BA7517" if pct_70 >= 10 else "#D85A30"
        st.markdown(
            f"<div style='background:#f8f8f8;border-radius:8px;padding:12px 16px;"
            f"border-left:4px solid {cor_term};margin:8px 0'>"
            f"<span style='font-size:13px;font-weight:600;color:{cor_term}'>"
            f"🎯 Empregabilidade atual: {vagas_70} vaga(s) com 70%+ de fit"
            f"</span>"
            f"<span style='font-size:12px;color:#888;margin-left:12px'>"
            f"{vagas_40} com 40-69% · {pct_70}% do total acima do limiar"
            f"</span></div>",
            unsafe_allow_html=True
        )

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
                ats = ats_scores.get(int(vaga["id"]), 0)
                render_vaga_card(vaga, score, is_nova, key_prefix="dash", ats_score=ats)

 # ── DIALOGS ────────────────────────────────────────────────
    vaga_id_atual = st.session_state.get("dialog_dash_atual")
    if vaga_id_atual:
        rows = df_f[df_f["id"] == vaga_id_atual]
        if not rows.empty:
            vaga = rows.iloc[0]
            dialog_fn = st.dialog(vaga['titulo'][:60], width="large")(_dialog_dash)
            dialog_fn(vaga)

    st.divider()
    st.subheader("Histórico de execuções")
    st.dataframe(carregar_logs(), use_container_width=True)