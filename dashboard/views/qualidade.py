import streamlit as st


def render():
    st.title("Qualidade dos dados")
    st.caption("Validação automática com Great Expectations.")

    if st.button("▶ Rodar validação", type="primary"):
        with st.spinner("Validando..."):
            import sys

            sys.path.insert(0, ".")
            from database.quality import validar_vagas

            resultado = validar_vagas()

        if resultado["success"]:
            st.success(f"✅ Todos os {resultado['total']} testes passaram!")
        else:
            st.error(f"⚠️ {resultado['failed']} falha(s) encontradas")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total de testes", resultado["total"])
        col2.metric("Passaram", resultado["passed"])
        col3.metric("Falharam", resultado["failed"])

        if resultado["results"]:
            st.divider()
            st.subheader("Falhas encontradas")
            for d in resultado["results"]:
                st.warning(f"**{d['coluna']}** — {d['expectativa']}")
