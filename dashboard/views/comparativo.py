import streamlit as st
import plotly.express as px
from database.connection import db_connect
from dashboard.charts import extrair_stacks_flat, grafico_stacks
from dashboard.ui_components import render_empty_state

def render():
    st.title("Comparativo entre empresas")
    st.caption("Compare stacks, nível médio e modalidade de duas empresas lado a lado.")

    with db_connect() as con:
        nomes = [e[0] for e in con.execute("""
            SELECT DISTINCT e.nome FROM dim_empresa e
            JOIN fact_vaga v ON v.id_empresa = e.id
            WHERE v.negada = false OR v.negada IS NULL
            ORDER BY e.nome
        """).fetchall()]

    if len(nomes) < 2:
        render_empty_state(
            "Empresas insuficientes",
            "Cadastre pelo menos 2 empresas com vagas coletadas para usar o comparativo.",
            "Ir para Empresas", "Empresas"
        )
        return

    col1, col2 = st.columns(2)
    emp_a = col1.selectbox("Empresa A", nomes, index=0)
    emp_b = col2.selectbox("Empresa B", nomes, index=1)

    if emp_a == emp_b:
        st.warning("Selecione empresas diferentes.")
        return

    def carregar_vagas_empresa(nome):
        with db_connect() as con:
            return con.execute("""
                SELECT v.id, v.titulo, v.nivel, v.modalidade, v.stacks, v.data_coleta
                FROM fact_vaga v
                JOIN dim_empresa e ON v.id_empresa = e.id
                WHERE e.nome = ? AND (v.negada = false OR v.negada IS NULL)
            """, [nome]).df()

    df_a = carregar_vagas_empresa(emp_a)
    df_b = carregar_vagas_empresa(emp_b)

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader(emp_a)
        m1, m2, m3 = st.columns(3)
        m1.metric("Vagas", len(df_a))
        m2.metric("Nível", df_a["nivel"].mode()[0] if not df_a.empty else "—")
        m3.metric("Modalidade", df_a["modalidade"].mode()[0] if not df_a.empty else "—")
    with col_b:
        st.subheader(emp_b)
        m1, m2, m3 = st.columns(3)
        m1.metric("Vagas", len(df_b))
        m2.metric("Nível", df_b["nivel"].mode()[0] if not df_b.empty else "—")
        m3.metric("Modalidade", df_b["modalidade"].mode()[0] if not df_b.empty else "—")

    st.divider()
    st.subheader("Stacks mais pedidas")
    categorias = [
        ("linguagens", "#1D9E75"), ("cloud", "#378ADD"),
        ("processamento", "#D85A30"), ("orquestracao", "#7F77DD"),
        ("armazenamento", "#BA7517"), ("infraestrutura", "#888780"),
    ]
    for categoria, cor in categorias:
        s_a = extrair_stacks_flat(df_a, categoria)
        s_b = extrair_stacks_flat(df_b, categoria)
        if s_a.empty and s_b.empty:
            continue
        st.markdown(f"**{categoria.upper()}**")
        col_a, col_b = st.columns(2)
        with col_a:
            fig = grafico_stacks(s_a, emp_a, cor)
            if fig: st.plotly_chart(fig, use_container_width=True)
            else: st.caption("Sem dados")
        with col_b:
            fig = grafico_stacks(s_b, emp_b, cor)
            if fig: st.plotly_chart(fig, use_container_width=True)
            else: st.caption("Sem dados")

    st.divider()
    st.subheader("Distribuição por nível")
    col_a, col_b = st.columns(2)
    with col_a:
        if not df_a.empty:
            df_n = df_a["nivel"].value_counts().reset_index()
            df_n.columns = ["nivel", "count"]
            fig = px.pie(df_n, values="count", names="nivel", title=emp_a,
                color_discrete_sequence=px.colors.qualitative.Set2, template="plotly_white")
            fig.update_layout(height=280, margin=dict(l=0,r=0,t=40,b=0))
            st.plotly_chart(fig, use_container_width=True)
    with col_b:
        if not df_b.empty:
            df_n = df_b["nivel"].value_counts().reset_index()
            df_n.columns = ["nivel", "count"]
            fig = px.pie(df_n, values="count", names="nivel", title=emp_b,
                color_discrete_sequence=px.colors.qualitative.Set2, template="plotly_white")
            fig.update_layout(height=280, margin=dict(l=0,r=0,t=40,b=0))
            st.plotly_chart(fig, use_container_width=True)
