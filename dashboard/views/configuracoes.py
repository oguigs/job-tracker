import streamlit as st
from database.connection import DB_PATH
import duckdb
from database.filtros import adicionar_filtro, remover_filtro, listar_filtros, carregar_filtros, carregar_filtros_localizacao
from main import titulo_relevante, localidade_relevante


def render():
    st.title("⚙️ Configurações")
    st.caption("Gerencie os filtros de coleta e qualidade da base.")

    df_filtros = listar_filtros()

    tab_titulo, tab_local, tab_limpeza = st.tabs([
        "🔤 Filtros de título", "🌍 Filtros de localização", "🧹 Limpeza da base"
    ])

    # ── FILTROS DE TÍTULO ──────────────────────────────────────
    with tab_titulo:
        col_interesse, col_bloqueio = st.columns(2)

        with col_interesse:
            st.subheader("✅ Interesse")
            st.caption("Vagas com esses termos serão coletadas.")
            df_i = df_filtros[df_filtros["tipo"] == "interesse"]

            # tags visuais
            tags_html = ""
            for _, row in df_i.iterrows():
                tags_html += (
                    f"<span style='background:#E8F5F0;color:#1D9E75;border:1px solid #1D9E75;"
                    f"border-radius:12px;padding:2px 10px;margin:2px;font-size:12px;display:inline-block'>"
                    f"{row['termo']}</span>"
                )
            if tags_html:
                st.markdown(tags_html, unsafe_allow_html=True)
            else:
                st.caption("Nenhum termo cadastrado.")

            st.write("")
            for _, row in df_i.iterrows():
                col_t, col_d = st.columns([4, 1])
                col_t.write(f"`{row['termo']}`")
                if col_d.button("🗑", key=f"rem_i_{row['id']}"):
                    remover_filtro(row["id"])
                    st.rerun()

            with st.form("form_interesse"):
                novo = st.text_input("Novo termo", placeholder="Ex: data engineer")
                if st.form_submit_button("➕ Adicionar", use_container_width=True):
                    if novo:
                        adicionar_filtro("interesse", novo.lower())
                        st.rerun()

        with col_bloqueio:
            st.subheader("🚫 Bloqueio")
            st.caption("Vagas com esses termos serão ignoradas.")
            df_b = df_filtros[df_filtros["tipo"] == "bloqueio"]

            tags_html = ""
            for _, row in df_b.iterrows():
                tags_html += (
                    f"<span style='background:#FFF0F0;color:#D85A30;border:1px solid #D85A30;"
                    f"border-radius:12px;padding:2px 10px;margin:2px;font-size:12px;display:inline-block'>"
                    f"{row['termo']}</span>"
                )
            if tags_html:
                st.markdown(tags_html, unsafe_allow_html=True)
            else:
                st.caption("Nenhum termo cadastrado.")

            st.write("")
            for _, row in df_b.iterrows():
                col_t, col_d = st.columns([4, 1])
                col_t.write(f"`{row['termo']}`")
                if col_d.button("🗑", key=f"rem_b_{row['id']}"):
                    remover_filtro(row["id"])
                    st.rerun()

            with st.form("form_bloqueio"):
                novo = st.text_input("Novo termo", placeholder="Ex: vendedor")
                if st.form_submit_button("➕ Adicionar", use_container_width=True):
                    if novo:
                        adicionar_filtro("bloqueio", novo.lower())
                        st.rerun()

    # ── FILTROS DE LOCALIZAÇÃO ─────────────────────────────────
    with tab_local:
        col_perm, col_bloq = st.columns(2)

        with col_perm:
            st.subheader("✅ Locais permitidos")
            st.caption("Só vagas dessas localidades serão coletadas.")
            df_perm = df_filtros[df_filtros["tipo"].isin(["pais_permitido","cidade_permitida"])]

            tags_html = ""
            for _, row in df_perm.iterrows():
                tags_html += (
                    f"<span style='background:#E8F5F0;color:#1D9E75;border:1px solid #1D9E75;"
                    f"border-radius:12px;padding:2px 10px;margin:2px;font-size:12px;display:inline-block'>"
                    f"{row['termo']}</span>"
                )
            if tags_html:
                st.markdown(tags_html, unsafe_allow_html=True)
            else:
                st.caption("Nenhum local cadastrado — aceita qualquer localização.")

            st.write("")
            for _, row in df_perm.iterrows():
                col_t, col_d = st.columns([4, 1])
                col_t.write(f"`{row['termo']}`")
                if col_d.button("🗑", key=f"rem_perm_{row['id']}"):
                    remover_filtro(row["id"])
                    st.rerun()

            with st.form("form_permitido"):
                novo = st.text_input("Adicionar", placeholder="Ex: brazil, são paulo")
                if st.form_submit_button("➕ Adicionar", use_container_width=True):
                    if novo:
                        adicionar_filtro("pais_permitido", novo.lower())
                        st.rerun()

        with col_bloq:
            st.subheader("🚫 Locais bloqueados")
            st.caption("Vagas dessas localidades serão ignoradas.")
            df_bloq = df_filtros[df_filtros["tipo"].isin(["pais_bloqueado","cidade_bloqueada"])]

            tags_html = ""
            for _, row in df_bloq.iterrows():
                tags_html += (
                    f"<span style='background:#FFF0F0;color:#D85A30;border:1px solid #D85A30;"
                    f"border-radius:12px;padding:2px 10px;margin:2px;font-size:12px;display:inline-block'>"
                    f"{row['termo']}</span>"
                )
            if tags_html:
                st.markdown(tags_html, unsafe_allow_html=True)
            else:
                st.caption("Nenhum local bloqueado.")

            st.write("")
            for _, row in df_bloq.iterrows():
                col_t, col_d = st.columns([4, 1])
                col_t.write(f"`{row['termo']}`")
                if col_d.button("🗑", key=f"rem_bloq_{row['id']}"):
                    remover_filtro(row["id"])
                    st.rerun()

            with st.form("form_bloqueado_loc"):
                novo = st.text_input("Adicionar", placeholder="Ex: india, singapore")
                if st.form_submit_button("➕ Adicionar", use_container_width=True):
                    if novo:
                        adicionar_filtro("pais_bloqueado", novo.lower())
                        st.rerun()

    # ── LIMPEZA DA BASE ────────────────────────────────────────
    with tab_limpeza:
        st.subheader("🧹 Limpeza da base")
        st.caption("Remove vagas que não passam pelos filtros atuais.")

        try:
            interesse, bloqueio = carregar_filtros()
            permitidos, bloqueados = carregar_filtros_localizacao()
            con = duckdb.connect(DB_PATH)
            vagas = con.execute("SELECT id, titulo FROM fact_vaga WHERE negada=false OR negada IS NULL").fetchall()
            con.close()

            irrelevantes = []
            for id_v, titulo in vagas:
                vaga_dict = {"titulo": titulo, "modalidade": "", "cidade": "", "pais": ""}
                if not titulo_relevante(titulo, interesse, bloqueio):
                    irrelevantes.append(id_v)
                elif not localidade_relevante(vaga_dict, permitidos, bloqueados):
                    irrelevantes.append(id_v)

            col1, col2, col3 = st.columns(3)
            col1.metric("Total de vagas", len(vagas))
            col2.metric("Seriam removidas", len(irrelevantes))
            col3.metric("Seriam mantidas", len(vagas) - len(irrelevantes))

            if len(irrelevantes) > 0:
                pct = round(len(irrelevantes) / len(vagas) * 100)
                st.warning(f"⚠️ {pct}% das vagas não passam pelos filtros atuais.")
                if st.button("🗑 Executar limpeza", type="secondary", use_container_width=False):
                    con = duckdb.connect(DB_PATH)
                    con.execute(f"DELETE FROM fact_vaga WHERE id IN ({','.join(map(str, irrelevantes))})")
                    con.close()
                    st.success(f"✅ {len(irrelevantes)} vagas removidas!")
                    st.rerun()
            else:
                st.success("✅ Todas as vagas passam pelos filtros atuais!")

        except Exception as e:
            st.error(f"Erro ao calcular impacto: {e}")