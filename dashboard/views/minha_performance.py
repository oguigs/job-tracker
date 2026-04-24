import streamlit as st
import plotly.express as px
from database.connection import db_connect


def render():
    st.title("📈 Minha Performance")
    st.caption("Análise do seu processo seletivo baseada nos seus dados reais.")

    with db_connect(read_only=True) as con:
        # total geral
        totais = con.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN candidatura_status != 'nao_inscrito' THEN 1 END) as inscritas,
                COUNT(CASE WHEN candidatura_status IN ('chamado','recrutador','fase_1','fase_2','fase_3') THEN 1 END) as entrevistas,
                COUNT(CASE WHEN candidatura_status = 'aprovado' THEN 1 END) as aprovadas,
                COUNT(CASE WHEN negada = true THEN 1 END) as negadas
            FROM fact_vaga
        """).fetchone()

        # por empresa — onde avancei mais
        por_empresa = con.execute("""
            SELECT
                e.nome as empresa,
                COUNT(*) as candidaturas,
                COUNT(CASE WHEN v.candidatura_status IN ('chamado','recrutador','fase_1','fase_2','fase_3','aprovado') THEN 1 END) as entrevistas,
                MAX(v.candidatura_status) as melhor_fase
            FROM fact_vaga v
            JOIN dim_empresa e ON v.id_empresa = e.id
            WHERE v.candidatura_status != 'nao_inscrito'
            AND (v.negada = false OR v.negada IS NULL)
            GROUP BY e.nome
            HAVING COUNT(*) > 0
            ORDER BY entrevistas DESC, candidaturas DESC
        """).df()

        # score médio por fase
        score_fase = con.execute("""
            SELECT
                candidatura_status,
                COUNT(*) as total
            FROM fact_vaga
            WHERE candidatura_status IS NOT NULL
            AND candidatura_status != 'nao_inscrito'
            AND (negada = false OR negada IS NULL)
            GROUP BY candidatura_status
            ORDER BY total DESC
        """).df()

        # por nível
        por_nivel = con.execute("""
            SELECT nivel, COUNT(*) as total,
                COUNT(CASE WHEN candidatura_status IN ('chamado','recrutador','fase_1','fase_2','fase_3','aprovado') THEN 1 END) as entrevistas
            FROM fact_vaga
            WHERE candidatura_status != 'nao_inscrito'
            AND (negada = false OR negada IS NULL)
            GROUP BY nivel
            ORDER BY total DESC
        """).df()

        # por modalidade
        por_modalidade = con.execute("""
            SELECT modalidade, COUNT(*) as total,
                COUNT(CASE WHEN candidatura_status IN ('chamado','recrutador','fase_1','fase_2','fase_3','aprovado') THEN 1 END) as entrevistas
            FROM fact_vaga
            WHERE candidatura_status != 'nao_inscrito'
            AND (negada = false OR negada IS NULL)
            GROUP BY modalidade
            ORDER BY total DESC
        """).df()

    if not totais or totais[1] == 0:
        from dashboard.ui_components import render_empty_state
        render_empty_state(
            "Nenhuma candidatura ainda",
            "Candidate-se às vagas na Fila de Inscrição para ver sua performance aqui."
        )
        return

    # ── MÉTRICAS GERAIS ────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total vagas", totais[0])
    col2.metric("Inscritas", totais[1])
    col3.metric("Entrevistas", totais[2])
    col4.metric("Aprovadas", totais[3])
    col5.metric("Negadas", totais[4])

    if totais[1] > 0:
        taxa = round(totais[2] / totais[1] * 100)
        cor = "#1D9E75" if taxa >= 30 else "#BA7517" if taxa >= 15 else "#D85A30"
        st.markdown(
            f"<div style='background:#f8f8f8;border-radius:8px;padding:10px 16px;"
            f"border-left:4px solid {cor};margin:8px 0'>"
            f"<span style='font-size:13px;color:{cor};font-weight:600'>"
            f"Taxa de conversão inscrição → entrevista: {taxa}%</span></div>",
            unsafe_allow_html=True)

    st.divider()

    # ── EMPRESAS ───────────────────────────────────────────────
    if not por_empresa.empty:
        st.subheader("🏢 Por empresa")
        col_a, col_b = st.columns(2)
        with col_a:
            st.caption("Empresas onde você mais avançou")
            for _, row in por_empresa.head(8).iterrows():
                pct = round(row["entrevistas"] / row["candidaturas"] * 100) if row["candidaturas"] > 0 else 0
                cor = "#1D9E75" if row["entrevistas"] > 0 else "#888"
                st.markdown(
                    f"<div style='display:flex;align-items:center;padding:4px 0;"
                    f"border-bottom:1px solid #f0f0f0'>"
                    f"<span style='flex:3;font-size:13px'>{row['empresa']}</span>"
                    f"<span style='flex:1;text-align:center;font-size:12px;color:#888'>"
                    f"{int(row['candidaturas'])} candidatura(s)</span>"
                    f"<span style='flex:1;text-align:right;color:{cor};font-weight:600'>"
                    f"{int(row['entrevistas'])} entrevista(s)</span>"
                    f"</div>", unsafe_allow_html=True)

    st.divider()

    # ── NÍVEL E MODALIDADE ─────────────────────────────────────
    col_n, col_m = st.columns(2)
    with col_n:
        st.subheader("📊 Por nível")
        if not por_nivel.empty:
            fig = px.bar(por_nivel, x="nivel", y=["total","entrevistas"],
                barmode="group", template="plotly_white",
                color_discrete_sequence=["#378ADD","#1D9E75"],
                labels={"value":"Vagas","variable":"","nivel":"Nível"})
            fig.update_layout(height=280, margin=dict(l=0,r=0,t=20,b=0))
            st.plotly_chart(fig, use_container_width=True)

    with col_m:
        st.subheader("🏠 Por modalidade")
        if not por_modalidade.empty:
            fig = px.bar(por_modalidade, x="modalidade", y=["total","entrevistas"],
                barmode="group", template="plotly_white",
                color_discrete_sequence=["#378ADD","#1D9E75"],
                labels={"value":"Vagas","variable":"","modalidade":"Modalidade"})
            fig.update_layout(height=280, margin=dict(l=0,r=0,t=20,b=0))
            st.plotly_chart(fig, use_container_width=True)
