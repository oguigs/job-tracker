import streamlit as st
from database.candidato import (
    salvar_perfil, carregar_perfil,
    salvar_stack, carregar_stacks, deletar_stack,
    salvar_curriculo_texto, carregar_curriculo_texto,
)
from dashboard.ui_components import render_empty_state
NIVEIS = ["Junior", "Pleno", "Sênior", "Especialista"]
MODALIDADES = ["Remoto", "Híbrido", "Presencial", "Indiferente"]
NIVEIS_STACK = ["Básico", "Intermediário", "Avançado", "Especialista"]
CATEGORIAS = ["linguagens", "cloud", "processamento", "orquestracao",
              "armazenamento", "infraestrutura"]

def render():
    st.title("Meu Perfil")
    st.caption("Seus dados pessoais e stacks para cálculo de score de fit.")

    df_perfil = carregar_perfil()
    p = df_perfil.iloc[0].to_dict() if not df_perfil.empty else {}

    tab_dados, tab_stacks, tab_curriculo = st.tabs(["Dados pessoais", "Minhas stacks", "Currículo"])

    # ── ABA DADOS PESSOAIS ───────────────────────────────────────
    with tab_dados:
        with st.form("form_perfil"):
            col1, col2 = st.columns(2)
            nome    = col1.text_input("Nome completo", value=p.get("nome") or "")
            email   = col2.text_input("Email", value=p.get("email") or "")

            col3, col4 = st.columns(2)
            linkedin = col3.text_input("LinkedIn", value=p.get("linkedin") or "",
                                        placeholder="https://linkedin.com/in/seu-perfil")
            cidade   = col4.text_input("Cidade", value=p.get("cidade") or "")

            col5, col6 = st.columns(2)
            nivel = col5.selectbox("Nível atual", NIVEIS,
                index=NIVEIS.index(p["nivel"]) if p.get("nivel") in NIVEIS else 2)
            modalidade_pref = col6.selectbox("Modalidade preferida", MODALIDADES,
                index=MODALIDADES.index(p["modalidade_pref"])
                if p.get("modalidade_pref") in MODALIDADES else 0)

            col7, col8 = st.columns(2)
            pretensao_min = col7.number_input("Pretensão mínima (R$)",
                min_value=0, step=500, value=int(p.get("pretensao_min") or 0))
            pretensao_max = col8.number_input("Pretensão máxima (R$)",
                min_value=0, step=500, value=int(p.get("pretensao_max") or 0))

            resumo = st.text_area("Resumo profissional",
                value=p.get("resumo") or "",
                placeholder="Breve descrição da sua experiência e objetivos...",
                height=120)

            if st.form_submit_button("Salvar perfil", type="primary", use_container_width=True):
                salvar_perfil(
                    nome=nome, email=email, linkedin=linkedin, cidade=cidade,
                    nivel=nivel, modalidade_pref=modalidade_pref,
                    pretensao_min=pretensao_min, pretensao_max=pretensao_max,
                    resumo=resumo
                )
                st.success("Perfil salvo!")
                st.rerun()

    # ── ABA STACKS ───────────────────────────────────────────────
    with tab_stacks:
        if df_perfil.empty:
            st.warning("Salve seus dados pessoais primeiro.")
            return

        id_candidato = int(p["id"])
        df_stacks = carregar_stacks(id_candidato)

        st.subheader("Adicionar stack")
        with st.form("form_stack"):
            col1, col2, col3, col4 = st.columns(4)
            stack       = col1.text_input("Tecnologia *", placeholder="Ex: python")
            categoria   = col2.selectbox("Categoria", CATEGORIAS)
            nivel_stack = col3.selectbox("Nível", NIVEIS_STACK)
            anos_exp    = col4.number_input("Anos de exp.", min_value=0, max_value=20, step=1)

            if st.form_submit_button("Adicionar", type="primary", use_container_width=True):
                if not stack:
                    st.error("Nome da tecnologia é obrigatório.")
                else:
                    salvar_stack(id_candidato, stack.lower().strip(),
                                 categoria, nivel_stack, anos_exp)
                    st.success(f"{stack} adicionada!")
                    st.rerun()

        if df_stacks.empty:
            render_empty_state(
                "Nenhuma stack cadastrada",
                "Adicione suas stacks para calcular o score de fit com as vagas coletadas.",
                "Adicionar stacks", "Meu Perfil"
            )
            return

        st.divider()
        st.subheader("Minhas stacks")

        for categoria in CATEGORIAS:
            df_cat = df_stacks[df_stacks["categoria"] == categoria]
            if df_cat.empty:
                continue
            st.markdown(f"**{categoria.upper()}**")
            for _, s in df_cat.iterrows():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                col1.write(f"`{s['stack']}`")
                col2.write(s["nivel_stack"])
                col3.write(f"{s['anos_exp']} ano(s)")
                if col4.button("✕", key=f"del_stack_{s['id']}"):
                    deletar_stack(s["id"])
                    st.rerun()
            st.divider()

    # ── ABA CURRÍCULO ────────────────────────────────────────────
    with tab_curriculo:
        texto_atual = carregar_curriculo_texto()

        if texto_atual:
            st.success(f"Currículo armazenado — {len(texto_atual)} caracteres extraídos.")
            with st.expander("Visualizar texto extraído"):
                st.text(texto_atual[:3000] + ("\n[...]" if len(texto_atual) > 3000 else ""))
            st.divider()

        st.markdown("**Atualizar currículo (PDF)**")
        st.caption("O texto será salvo e usado automaticamente para calcular scores ATS nas vagas capturadas.")
        cv_file = st.file_uploader("Upload PDF", type=["pdf"], key="cv_perfil_upload")
        if cv_file:
            import tempfile, os
            from transformers.curriculo_parser import extrair_texto_pdf
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(cv_file.read())
                tmp_path = tmp.name
            try:
                texto = extrair_texto_pdf(tmp_path)
                if texto.strip():
                    salvar_curriculo_texto(texto)
                    st.success(f"Currículo salvo! {len(texto)} caracteres extraídos.")
                    st.rerun()
                else:
                    st.error("Não foi possível extrair texto do PDF. Use um PDF com texto selecionável.")
            finally:
                os.unlink(tmp_path)

        if texto_atual:
            st.divider()
            st.markdown("**Recalcular scores ATS para todas as vagas**")
            st.caption("Recalcula ANYA para todas as vagas ativas com descrição usando o currículo armazenado.")
            if st.button("↻ Recalcular todos os scores", type="secondary", use_container_width=True):
                from database.ats_score import recalcular_todos
                with st.spinner("Calculando..."):
                    total = recalcular_todos(texto_atual)
                st.success(f"{total} vagas recalculadas.")