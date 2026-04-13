import streamlit as st
from database.vagas import listar_vagas_negadas
from database.schemas import TIMELINE_LABELS
from dashboard.components import conectar_rw

def render():
    st.title("Vagas Negadas")
    st.caption("Vagas que você optou por não seguir.")

    df_negadas = listar_vagas_negadas()

    if df_negadas.empty:
        st.info("Nenhuma vaga negada ainda.")
        return

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
                    SET negada = false, candidatura_status = 'nao_inscrito',
                        candidatura_fase = null, candidatura_observacao = null,
                        candidatura_data = null
                    WHERE id = ?
                """, [vaga["id"]])
                con.close()
                st.success("Vaga reativada!")
                st.rerun()