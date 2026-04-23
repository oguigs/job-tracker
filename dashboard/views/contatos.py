import streamlit as st
from database.contatos import inserir_contato, listar_contatos, deletar_contato
from database.connection import db_connect

GRAUS = ["Amigo", "Conhecido", "Família", "Amigo de amigo"]


def render():
    st.title("Indicadores")
    st.caption("Pessoas que podem te indicar nas empresas monitoradas.")

    with db_connect(read_only=True) as con:
        empresas_db = con.execute("SELECT id, nome FROM dim_empresa ORDER BY nome").fetchall()

    nomes_empresas = [e[1] for e in empresas_db]
    mapa_empresas  = {e[1]: e[0] for e in empresas_db}

    st.subheader("Cadastrar contato")
    with st.form("form_contato"):
        col1, col2 = st.columns(2)
        nome  = col1.text_input("Nome *", placeholder="João Silva")
        email = col2.text_input("Email corporativo", placeholder="joao@empresa.com")
        col3, col4 = st.columns(2)
        empresa_sel = col3.selectbox("Empresa *", ["— selecione —"] + nomes_empresas)
        grau        = col4.selectbox("Grau de intimidade", GRAUS)
        observacoes = st.text_area("Observações", height=80)
        if st.form_submit_button("Salvar contato", type="primary", use_container_width=True):
            if not nome:
                st.error("Nome é obrigatório.")
            elif empresa_sel == "— selecione —":
                st.error("Selecione uma empresa.")
            else:
                inserir_contato(nome=nome, email=email,
                               id_empresa=mapa_empresas[empresa_sel],
                               grau=grau, observacoes=observacoes)
                st.success(f"{nome} cadastrado!")
                st.rerun()

    st.divider()
    st.subheader("Contatos cadastrados")
    empresa_filtro = st.selectbox("Filtrar por empresa", ["Todas"] + nomes_empresas)
    df = listar_contatos() if empresa_filtro == "Todas" else listar_contatos(mapa_empresas[empresa_filtro])

    if df.empty:
        from dashboard.ui_components import render_empty_state
        render_empty_state(
            "Nenhum contato cadastrado",
            "Adicione pessoas que podem te indicar — aparecem automaticamente ao avançar em entrevistas."
        )
        return

    st.metric("Total de contatos", len(df))
    st.divider()
    for empresa_nome in df["empresa"].unique():
        df_emp = df[df["empresa"] == empresa_nome]
        st.markdown(f"#### 🏢 {empresa_nome}")
        for _, contato in df_emp.iterrows():
            with st.expander(f"{contato['nome']} — {contato['grau']}"):
                col1, col2 = st.columns(2)
                col1.write(f"**Email:** {contato['email'] or '—'}")
                col2.write(f"**Grau:** {contato['grau']}")
                if contato["observacoes"]:
                    st.write(f"**Observações:** {contato['observacoes']}")
                if st.button("Remover", key=f"del_{contato['id']}", type="secondary"):
                    deletar_contato(contato["id"])
                    st.rerun()
        st.divider()
