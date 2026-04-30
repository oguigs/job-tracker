import streamlit as st
import plotly.express as px
import pandas as pd
from database.snapshots import carregar_historico, listar_stacks_snapshot, salvar_snapshot
from dashboard.ui_components import render_empty_state


CATEGORIAS = [
    "linguagens",
    "cloud",
    "processamento",
    "orquestracao",
    "armazenamento",
    "infraestrutura",
]

CATEGORIA_CORES = {
    "linguagens": "#1D9E75",
    "cloud": "#378ADD",
    "processamento": "#D85A30",
    "orquestracao": "#7F77DD",
    "armazenamento": "#BA7517",
    "infraestrutura": "#888780",
}


def render():
    st.title("Tendências do mercado")
    st.caption("Evolução das stacks mais pedidas ao longo do tempo.")

    col_snap, col_info = st.columns([2, 4])
    with col_snap:
        if st.button("📸 Salvar snapshot hoje", use_container_width=True):
            salvar_snapshot()
            st.success("Snapshot salvo!")
            st.rerun()

    stacks_disponiveis = listar_stacks_snapshot()
    if not stacks_disponiveis:
        render_empty_state(
            "Nenhum snapshot ainda",
            "Clique em 'Salvar snapshot hoje' e volte em alguns dias para ver a evolução das stacks no mercado.",
        )
        return

    st.divider()

    tab_categoria, tab_stack = st.tabs(["Por categoria", "Por stack específica"])

    with tab_categoria:
        st.subheader("Evolução por categoria")
        categoria_sel = st.selectbox("Categoria", CATEGORIAS, key="cat_sel")
        cor = CATEGORIA_CORES.get(categoria_sel, "#888")

        df = carregar_historico(categoria=categoria_sel)
        if df.empty:
            st.info("Sem dados para essa categoria ainda.")
        else:
            top_stacks = (
                df.groupby("stack")["quantidade"]
                .sum()
                .sort_values(ascending=False)
                .head(8)
                .index.tolist()
            )
            df_top = df[df["stack"].isin(top_stacks)].copy()

            if len(df_top["data_ref"].unique()) < 2:
                # só um snapshot — mostra barras em vez de linha
                df_total = (
                    df_top.groupby("stack")["quantidade"]
                    .sum()
                    .reset_index()
                    .sort_values("quantidade", ascending=True)
                )
                fig = px.bar(
                    df_total,
                    x="quantidade",
                    y="stack",
                    orientation="h",
                    title=f"Stacks — {categoria_sel} (snapshot único)",
                    color_discrete_sequence=[CATEGORIA_CORES.get(categoria_sel, "#888")],
                    template="plotly_white",
                )
                fig.update_layout(
                    height=400,
                    margin=dict(l=0, r=0, t=40, b=0),
                    yaxis_title="",
                    xaxis_title="Vagas",
                )
            else:
                df_top["data_ref"] = pd.to_datetime(df_top["data_ref"])
                fig = px.line(
                    df_top,
                    x="data_ref",
                    y="quantidade",
                    color="stack",
                    title=f"Top stacks — {categoria_sel}",
                    template="plotly_white",
                    color_discrete_sequence=px.colors.qualitative.Set2,
                )
                fig.update_layout(
                    height=400,
                    margin=dict(l=0, r=0, t=40, b=0),
                    xaxis_title="Data",
                    yaxis_title="Vagas",
                    legend_title="Stack",
                )
            st.plotly_chart(fig, use_container_width=True)

    with tab_stack:
        st.subheader("Evolução de uma stack específica")
        nomes_stacks = sorted(set([s[0] for s in stacks_disponiveis]))
        stack_sel = st.selectbox("Stack", nomes_stacks, key="stack_sel")

        df = carregar_historico(stack=stack_sel)
        if df.empty:
            st.info("Sem histórico para essa stack.")
        else:
            categoria = df["categoria"].iloc[0]
            cor = CATEGORIA_CORES.get(categoria, "#888")

            if len(df["data_ref"].unique()) < 2:
                # só um ponto — mostra métrica simples
                qtd = int(df["quantidade"].iloc[0])
                st.metric("Vagas hoje", qtd)
                st.caption(f"Categoria: {categoria}")
                st.info("Acumule mais snapshots ao longo dos dias para ver a evolução.")
            else:
                df["data_ref"] = pd.to_datetime(df["data_ref"])
                fig = px.line(
                    df,
                    x="data_ref",
                    y="quantidade",
                    title=f"Evolução de '{stack_sel}'",
                    template="plotly_white",
                    color_discrete_sequence=[cor],
                )
                fig.update_layout(
                    height=350,
                    margin=dict(l=0, r=0, t=40, b=0),
                    xaxis_title="Data",
                    yaxis_title="Vagas",
                )
                st.plotly_chart(fig, use_container_width=True)

                col1, col2 = st.columns(2)
                col1.metric("Categoria", categoria)
                col2.metric("Vagas hoje", int(df["quantidade"].iloc[-1]))
