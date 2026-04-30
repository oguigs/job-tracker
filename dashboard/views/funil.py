import streamlit as st
import plotly.express as px
from database.connection import db_connect
from database.schemas import TIMELINE_LABELS


def render():
    st.title("Funil de candidaturas")
    st.caption("Visualize em qual fase você mais trava e sua taxa de conversão.")

    with db_connect() as con:
        df = con.execute("""
            SELECT candidatura_status, COUNT(*) as total
            FROM fact_vaga
            WHERE candidatura_status IS NOT NULL
            AND candidatura_status != 'nao_inscrito'
            AND (negada = false OR negada IS NULL)
            GROUP BY candidatura_status ORDER BY total DESC
        """).df()
        df_neg = con.execute("SELECT COUNT(*) as total FROM fact_vaga WHERE negada = true").df()
        df_conv = con.execute("""
            SELECT
                COUNT(*) FILTER (WHERE candidatura_status = 'inscrito') as inscritas,
                COUNT(*) FILTER (WHERE candidatura_status IN ('chamado','recrutador','fase_1','fase_2','fase_3','aprovado')) as entrevistas,
                COUNT(*) FILTER (WHERE candidatura_status = 'aprovado') as aprovadas,
                COUNT(*) FILTER (WHERE candidatura_status = 'reprovado') as reprovadas
            FROM fact_vaga WHERE negada = false OR negada IS NULL
        """).df()

    if df.empty:
        from dashboard.ui_components import render_empty_state

        render_empty_state(
            "Nenhuma candidatura ainda",
            "Candidate-se às vagas na Fila de Inscrição e acompanhe seu progresso aqui.",
            "Ir para Fila de Inscrição",
            "Fila de Inscrição",
        )
        return

    conv = df_conv.iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Inscritas", int(conv["inscritas"]))
    col2.metric("Entrevistas", int(conv["entrevistas"]))
    col3.metric("Aprovadas", int(conv["aprovadas"]))
    col4.metric("Reprovadas", int(conv["reprovadas"]))

    if int(conv["inscritas"]) > 0:
        taxa = round(int(conv["entrevistas"]) / int(conv["inscritas"]) * 100)
        st.markdown(f"**Taxa de conversão inscrição → entrevista: {taxa}%**")

    st.divider()
    ordem = [
        "inscrito",
        "chamado",
        "recrutador",
        "fase_1",
        "fase_2",
        "fase_3",
        "aprovado",
        "reprovado",
    ]
    df["label"] = df["candidatura_status"].map(TIMELINE_LABELS)
    df["ordem"] = df["candidatura_status"].map(lambda x: ordem.index(x) if x in ordem else 99)
    df = df.sort_values("ordem")
    fig = px.bar(
        df,
        x="label",
        y="total",
        title="Distribuição por fase",
        color="total",
        color_continuous_scale=["#D85A30", "#BA7517", "#1D9E75"],
        template="plotly_white",
    )
    fig.update_layout(
        height=350,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis_title="",
        yaxis_title="Vagas",
        showlegend=False,
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.divider()
    st.subheader("Vagas negadas")
    st.metric("Total negadas", int(df_neg.iloc[0]["total"]))
