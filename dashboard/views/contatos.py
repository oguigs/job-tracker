import streamlit as st
from database.contatos import inserir_contato, listar_contatos, deletar_contato
from dashboard.components import conectar

GRAUS = ["Amigo", "Conhecido", "Família", "Amigo de amigo"]

def render():
    st.title("Indicadores")
    st.caption("Pessoas que podem te indicar nas empresas monitoradas.")

    con = conectar()
    empresas_db = con.execute("""
        SELECT id, nome FROM dim_empresa ORDER BY nome
    """).fetchall()
    con.close()

    nomes_empresas = [e[1] for e in empresas_db]
    mapa_empresas  = {e[1]: e[0] for e in empresas_db}

    # ── Cadastro ────────────────────────────────────────────────
    st.subheader("Cadastrar contato")
    with st.form("form_contato"):
        col1, col2 = st.columns(2)
        nome    = col1.text_input("Nome *", placeholder="João Silva")
        email   = col2.text_input("Email corporativo", placeholder="joao@empresa.com")

        col3, col4 = st.columns(2)
        empresa_sel = col3.selectbox("Empresa *", ["— selecione —"] + nomes_empresas)
        grau        = col4.selectbox("Grau de intimidade", GRAUS)

        observacoes = st.text_area("Observações", placeholder="Ex: colega da XP, trabalhou no time de dados", height=80)

        if st.form_submit_button("Salvar contato", type="primary", use_container_width=True):
            if not nome:
                st.error("Nome é obrigatório.")
            elif empresa_sel == "— selecione —":
                st.error("Selecione uma empresa.")
            else:
                inserir_contato(
                    nome=nome,
                    email=email,
                    id_empresa=mapa_empresas[empresa_sel],
                    grau=grau,
                    observacoes=observacoes
                )
                st.success(f"{nome} cadastrado!")
                st.rerun()

    st.divider()

    # ── Lista por empresa ────────────────────────────────────────
    st.subheader("Contatos cadastrados")

    empresa_filtro = st.selectbox("Filtrar por empresa", ["Todas"] + nomes_empresas)

    if empresa_filtro == "Todas":
        df = listar_contatos()
    else:
        df = listar_contatos(mapa_empresas[empresa_filtro])

    if df.empty:
        st.info("Nenhum contato cadastrado ainda.")
        return

    st.metric("Total de contatos", len(df))
    st.divider()

    # agrupa por empresa
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
                if st.button("Remover", key=f"del_contato_{contato['id']}", type="secondary"):
                    deletar_contato(contato["id"])
                    st.success("Contato removido.")
                    st.rerun()
        st.divider()