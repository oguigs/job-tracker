import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta
from database.schemas import TIMELINE_LABELS
from database.candidaturas import atualizar_candidatura
from dashboard.components import (
    carregar_vagas,
    extrair_stacks_flat,
    grafico_stacks,
    calcular_scores_vagas,
)
from dashboard.ui_components import render_dialog_vaga, tempo_relativo
from database.ats_score import listar_ats_scores


def _dialog_dash(v):
    render_dialog_vaga(v, prefix="dash")


def render():
    for key in list(st.session_state.keys()):
        if key.startswith("dialog_"):
            st.session_state[key] = False

    st.title("Job Tracker — Data Engineering")

    df = carregar_vagas()
    scores = calcular_scores_vagas()
    ats_scores = listar_ats_scores()
    df["score"] = df["id"].map(scores).fillna(0).astype(int)
    df["ats"] = df["id"].map(lambda x: ats_scores.get(int(x), 0))

    ontem = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d")
    df_ativas = df[df["ativa"] == True]

    # ── MÉTRICAS PRINCIPAIS ────────────────────────────────────
    total = len(df_ativas)
    novas_hoje = df_ativas[df_ativas["data_coleta"].astype(str) >= ontem].shape[0]
    inscritas = df_ativas[df_ativas["candidatura_status"] == "inscrito"].shape[0]
    em_processo = df_ativas[
        df_ativas["candidatura_status"].isin(
            ["chamado", "recrutador", "fase_1", "fase_2", "fase_3"]
        )
    ].shape[0]
    score_medio = (
        int(df_ativas[df_ativas["score"] > 0]["score"].mean())
        if (df_ativas["score"] > 0).any()
        else 0
    )
    urgentes_nao_candidatadas = df_ativas[
        (df_ativas["urgente"] == True) & (df_ativas["candidatura_status"] == "nao_inscrito")
    ].shape[0]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Vagas ativas", total)
    c2.metric("Novas hoje", novas_hoje, delta=f"+{novas_hoje}" if novas_hoje > 0 else None)
    c3.metric("Inscritas", inscritas)
    c4.metric("Em processo", em_processo)
    c5.metric("Score médio", f"{score_medio}%")

    # ── BANNER DE AÇÃO ─────────────────────────────────────────
    msgs = []
    if novas_hoje > 0:
        msgs.append(f"🆕 **{novas_hoje} vaga(s) nova(s)** nas últimas 24h")
    if urgentes_nao_candidatadas > 0:
        msgs.append(f"🔥 **{urgentes_nao_candidatadas} urgente(s)** sem candidatura")

    if msgs:
        st.info("  ·  ".join(msgs) + " — acesse **Vagas** para agir")

    # ── TERMÔMETRO DE EMPREGABILIDADE ─────────────────────────
    if scores:
        vagas_70 = sum(1 for s in scores.values() if s >= 70)
        vagas_40 = sum(1 for s in scores.values() if 40 <= s < 70)
        total_scores = len(scores)
        pct_70 = round(vagas_70 / total_scores * 100) if total_scores > 0 else 0
        cor = "#1D9E75" if pct_70 >= 20 else "#BA7517" if pct_70 >= 10 else "#D85A30"
        st.markdown(
            f"<div style='background:#f8f8f8;border-radius:8px;padding:12px 16px;"
            f"border-left:4px solid {cor};margin:8px 0'>"
            f"<span style='font-size:13px;font-weight:600;color:{cor}'>"
            f"🎯 Empregabilidade: {vagas_70} vaga(s) com 70%+ de fit"
            f"</span>"
            f"<span style='font-size:12px;color:#888;margin-left:12px'>"
            f"{vagas_40} com 40–69% · {pct_70}% do total acima do limiar"
            f"</span></div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── TOP VAGAS PARA CANDIDATAR ──────────────────────────────
    top_vagas = (
        df_ativas[df_ativas["candidatura_status"] == "nao_inscrito"]
        .sort_values("score", ascending=False)
        .head(5)
    )

    if not top_vagas.empty:
        st.subheader("Top vagas para candidatar agora")
        for _, v in top_vagas.iterrows():
            score = int(v["score"])
            ats = int(v["ats"])
            urgente = v.get("urgente") is True
            cor_score = "#1D9E75" if score >= 70 else "#BA7517" if score >= 40 else "#888"
            urgente_tag = " 🔥" if urgente else ""

            col_info, col_score, col_ats, col_link, col_btn = st.columns([5, 1.5, 1.5, 0.8, 1])
            with col_info:
                tempo = tempo_relativo(v["data_coleta"])
                st.markdown(
                    f"**{v['titulo'][:55]}{urgente_tag}**  \n"
                    f"<span style='color:#888;font-size:12px'>{v['empresa']} · {v['nivel']} · {v['modalidade']} · {tempo}</span>",
                    unsafe_allow_html=True,
                )
            with col_score:
                st.markdown(
                    f"<div style='font-size:12px;font-weight:700;color:{cor_score}'>🎯 {score}%</div>"
                    f"<div style='background:#f0f0f0;border-radius:3px;height:4px'>"
                    f"<div style='background:{cor_score};width:{score}%;height:4px;border-radius:3px'></div></div>",
                    unsafe_allow_html=True,
                )
            with col_ats:
                if ats > 0:
                    st.markdown(
                        f"<div style='font-size:12px;font-weight:700;color:#7F77DD'>🤖 {ats}%</div>"
                        f"<div style='background:#f0f0f0;border-radius:3px;height:4px'>"
                        f"<div style='background:#7F77DD;width:{ats}%;height:4px;border-radius:3px'></div></div>",
                        unsafe_allow_html=True,
                    )
            with col_link:
                st.link_button("🔗", v["link"])
            with col_btn:
                if st.button("✅ Inscrito", key=f"dash_inscrito_{v['id']}"):
                    atualizar_candidatura(int(v["id"]), "inscrito", "inscrito", "")
                    st.rerun()

        st.divider()

    # ── STACKS MAIS EXIGIDAS ───────────────────────────────────
    st.subheader("Stacks mais exigidas")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        fig = grafico_stacks(extrair_stacks_flat(df_ativas, "linguagens"), "Linguagens", "#1D9E75")
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col_b:
        fig = grafico_stacks(extrair_stacks_flat(df_ativas, "cloud"), "Cloud", "#378ADD")
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col_c:
        fig = grafico_stacks(
            extrair_stacks_flat(df_ativas, "processamento"), "Processamento", "#D85A30"
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    col_d, col_e, col_f = st.columns(3)
    with col_d:
        fig = grafico_stacks(
            extrair_stacks_flat(df_ativas, "orquestracao"), "Orquestração", "#7F77DD"
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col_e:
        fig = grafico_stacks(
            extrair_stacks_flat(df_ativas, "armazenamento"), "Armazenamento", "#BA7517"
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col_f:
        fig = grafico_stacks(
            extrair_stacks_flat(df_ativas, "infraestrutura"), "Infraestrutura", "#888780"
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── DISTRIBUIÇÃO ───────────────────────────────────────────
    col_nivel, col_modal, col_status = st.columns(3)
    with col_nivel:
        st.subheader("Por nível")
        df_nivel = df_ativas["nivel"].value_counts().reset_index()
        df_nivel.columns = ["nivel", "count"]
        fig = px.pie(
            df_nivel,
            values="count",
            names="nivel",
            color_discrete_sequence=px.colors.qualitative.Set2,
            template="plotly_white",
        )
        fig.update_layout(height=260, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
    with col_modal:
        st.subheader("Por modalidade")
        df_modal = df_ativas["modalidade"].value_counts().reset_index()
        df_modal.columns = ["modalidade", "count"]
        fig = px.pie(
            df_modal,
            values="count",
            names="modalidade",
            color_discrete_sequence=["#1D9E75", "#378ADD", "#D85A30"],
            template="plotly_white",
        )
        fig.update_layout(height=260, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
    with col_status:
        st.subheader("Por status")
        df_status = (
            df_ativas["candidatura_status"].map(TIMELINE_LABELS).value_counts().reset_index()
        )
        df_status.columns = ["status", "count"]
        fig = px.bar(
            df_status,
            x="count",
            y="status",
            orientation="h",
            color_discrete_sequence=["#1A5FAD"],
            template="plotly_white",
        )
        fig.update_layout(
            height=260, margin=dict(l=0, r=0, t=0, b=0), xaxis_title="", yaxis_title=""
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── DIALOGS ────────────────────────────────────────────────
    vaga_id_atual = st.session_state.get("dialog_dash_atual")
    if vaga_id_atual:
        rows = df[df["id"] == vaga_id_atual]
        if not rows.empty:
            vaga = rows.iloc[0]
            dialog_fn = st.dialog(vaga["titulo"][:60], width="large")(_dialog_dash)
            dialog_fn(vaga)
