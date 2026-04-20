import streamlit as st
from database.filtros import adicionar_filtro, remover_filtro, listar_filtros

def render():
    st.title("Configurações")
    st.caption("Gerencie os filtros de coleta de vagas.")

    df_filtros = listar_filtros()
    col_interesse, col_bloqueio = st.columns(2)

    with col_interesse:
        st.subheader("Palavras de interesse")
        st.caption("Vagas com esses termos no título serão coletadas.")
        df_i = df_filtros[df_filtros["tipo"] == "interesse"]
        for _, row in df_i.iterrows():
            col_t, col_d = st.columns([4, 1])
            col_t.write(f"`{row['termo']}`")
            if col_d.button("Remover", key=f"rem_i_{row['id']}"):
                remover_filtro(row["id"])
                st.rerun()
        with st.form("form_interesse"):
            novo = st.text_input("Adicionar termo de interesse")
            if st.form_submit_button("Adicionar"):
                if novo:
                    adicionar_filtro("interesse", novo.lower())
                    st.success(f"'{novo}' adicionado!")
                    st.rerun()

    with col_bloqueio:
        st.subheader("Palavras bloqueadas")
        st.caption("Vagas com esses termos no título serão ignoradas.")
        df_b = df_filtros[df_filtros["tipo"] == "bloqueio"]
        for _, row in df_b.iterrows():
            col_t, col_d = st.columns([4, 1])
            col_t.write(f"`{row['termo']}`")
            if col_d.button("Remover", key=f"rem_b_{row['id']}"):
                remover_filtro(row["id"])
                st.rerun()
        with st.form("form_bloqueio"):
            novo = st.text_input("Adicionar termo bloqueado")
            if st.form_submit_button("Adicionar"):
                if novo:
                    adicionar_filtro("bloqueio", novo.lower())
                    st.success(f"'{novo}' bloqueado!")
                    st.rerun()

    st.divider()
    st.subheader("Filtros de localização")
    st.caption("Deixe vazio para aceitar qualquer localização.")

    col_perm, col_bloq = st.columns(2)

    with col_perm:
        st.markdown("**Países/cidades permitidos**")
        st.caption("Só vagas dessas localidades serão coletadas.")
        df_perm = df_filtros[df_filtros["tipo"].isin(["pais_permitido","cidade_permitida"])]
        for _, row in df_perm.iterrows():
            col_t, col_d = st.columns([4, 1])
            col_t.write(f"`{row['termo']}`")
            if col_d.button("Remover", key=f"rem_perm_{row['id']}"):
                remover_filtro(row["id"])
                st.rerun()
        with st.form("form_permitido"):
            novo = st.text_input("Adicionar local permitido", placeholder="Ex: brazil, remote")
            if st.form_submit_button("Adicionar"):
                if novo:
                    adicionar_filtro("pais_permitido", novo.lower())
                    st.success(f"'{novo}' adicionado!")
                    st.rerun()

    with col_bloq:
        st.markdown("**Países/cidades bloqueados**")
        st.caption("Vagas dessas localidades serão ignoradas.")
        df_bloq = df_filtros[df_filtros["tipo"].isin(["pais_bloqueado","cidade_bloqueada"])]
        for _, row in df_bloq.iterrows():
            col_t, col_d = st.columns([4, 1])
            col_t.write(f"`{row['termo']}`")
            if col_d.button("Remover", key=f"rem_bloq_{row['id']}"):
                remover_filtro(row["id"])
                st.rerun()
        with st.form("form_bloqueado_loc"):
            novo = st.text_input("Adicionar local bloqueado", placeholder="Ex: india, singapore")
            if st.form_submit_button("Adicionar"):
                if novo:
                    adicionar_filtro("pais_bloqueado", novo.lower())
                    st.success(f"'{novo}' bloqueado!")
                    st.rerun()

        st.divider()
        st.subheader("🧹 Limpeza da base")
        st.caption("Remove vagas que não passam pelos filtros atuais de título e localização.")
        
        col_prev, col_btn = st.columns([3, 1])
        
        # preview de quantas seriam removidas
        try:
            from main import titulo_relevante, localidade_relevante
            from database.filtros import carregar_filtros, carregar_filtros_localizacao
            import duckdb
            
            interesse, bloqueio = carregar_filtros()
            con = duckdb.connect("data/curated/jobs.duckdb")
            vagas = con.execute("SELECT id, titulo FROM fact_vaga WHERE negada=false OR negada IS NULL").fetchall()
            con.close()
            
            permitidos, bloqueados = carregar_filtros_localizacao()
            
            irrelevantes = []
            for id_v, titulo in vagas:
                vaga_dict = {"titulo": titulo, "modalidade": "", "cidade": "", "pais": ""}
                if not titulo_relevante(titulo, interesse, bloqueio):
                    irrelevantes.append(id_v)
                elif not localidade_relevante(vaga_dict, permitidos, bloqueados):
                    irrelevantes.append(id_v)
                    
            col_prev.info(f"**{len(irrelevantes)}** vagas seriam removidas de um total de **{len(vagas)}**.")
        except:
            irrelevantes = []
            col_prev.info("Clique em reprocessar para ver o impacto.")
        
        if col_btn.button("🗑 Reprocessar", type="secondary", use_container_width=True):
            if irrelevantes:
                con = duckdb.connect("data/curated/jobs.duckdb")
                con.execute(f"DELETE FROM fact_vaga WHERE id IN ({','.join(map(str, irrelevantes))})")
                con.close()
                st.success(f"✅ {len(irrelevantes)} vagas removidas!")
                st.rerun()
            else:
                st.info("Nenhuma vaga para remover.")                    