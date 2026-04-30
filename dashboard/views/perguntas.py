import streamlit as st
from database.perguntas import (
    adicionar_pergunta,
    listar_perguntas,
    deletar_pergunta,
    stats_perguntas,
)
from database.connection import db_connect


def render():
    st.title("🧠 Banco de Perguntas")
    st.caption("Registre perguntas de entrevistas técnicas. Quanto mais você usa, mais rico fica.")

    tab_banco, tab_adicionar, tab_stats = st.tabs(["📚 Banco", "➕ Adicionar", "📊 Estatísticas"])

    # ── BANCO ──────────────────────────────────────────────────
    with tab_banco:
        with db_connect() as con:
            stacks_disponiveis = con.execute("""
                SELECT DISTINCT stack FROM log_perguntas_entrevista ORDER BY stack
            """).fetchall()

        stacks_list = ["Todas"] + [s[0] for s in stacks_disponiveis]
        col_f1, col_f2 = st.columns(2)
        filtro_stack = col_f1.selectbox("Filtrar por stack", stacks_list)
        filtro_dif = col_f2.selectbox(
            "Filtrar por dificuldade", ["Todas", "fácil", "média", "difícil"]
        )

        df = listar_perguntas(stack=filtro_stack if filtro_stack != "Todas" else None)

        if df.empty:
            from dashboard.ui_components import render_empty_state

            render_empty_state(
                "Nenhuma pergunta ainda",
                "Após cada entrevista, registre as perguntas técnicas que fizeram. O banco cresce com o uso!",
            )
        else:
            if filtro_dif != "Todas":
                df = df[df["dificuldade"] == filtro_dif]

            st.metric("Total de perguntas", len(df))
            st.divider()

            for _, row in df.iterrows():
                dif_cor = {"fácil": "#1D9E75", "média": "#BA7517", "difícil": "#D85A30"}.get(
                    row["dificuldade"], "#888"
                )
                acertou_icon = "✅" if row.get("acertou") else "❌"
                with st.expander(f"{acertou_icon} [{row['stack']}] {row['pergunta'][:80]}"):
                    col1, col2, col3 = st.columns(3)
                    col1.markdown(f"**Stack:** {row['stack']}")
                    col2.markdown(
                        f"**Dificuldade:** <span style='color:{dif_cor};font-weight:700'>{row['dificuldade']}</span>",
                        unsafe_allow_html=True,
                    )
                    col3.markdown(f"**Empresa:** {row['empresa']}")
                    st.markdown(f"**Pergunta completa:** {row['pergunta']}")
                    if row.get("resposta_ideal"):
                        st.markdown(f"**Resposta ideal:** {row['resposta_ideal']}")
                    st.caption(f"Data: {str(row['data'])[:10]}")
                    if st.button("🗑 Remover", key=f"del_perg_{row['id']}"):
                        deletar_pergunta(int(row["id"]))
                        st.rerun()

    # ── ADICIONAR ──────────────────────────────────────────────
    with tab_adicionar:
        with db_connect() as con:
            vagas_entrevista = con.execute("""
                SELECT v.id, v.titulo, e.nome as empresa
                FROM fact_vaga v
                JOIN dim_empresa e ON v.id_empresa = e.id
                WHERE v.candidatura_status IN ('chamado','recrutador','fase_1','fase_2','fase_3','aprovado','reprovado')
                AND (v.negada = false OR v.negada IS NULL)
                ORDER BY v.candidatura_data DESC
            """).fetchall()

        if not vagas_entrevista:
            st.info("Avance para a fase de entrevista em alguma vaga para registrar perguntas.")
        else:
            opcoes = {f"{v[2]} — {v[1][:50]}": v[0] for v in vagas_entrevista}
            vaga_sel = st.selectbox("Vaga da entrevista", list(opcoes.keys()))
            id_vaga_sel = opcoes[vaga_sel]

            with st.form("form_pergunta"):
                col1, col2 = st.columns(2)
                stack = col1.text_input("Stack *", placeholder="Ex: Apache Spark")
                dificuldade = col2.selectbox("Dificuldade", ["fácil", "média", "difícil"])
                pergunta = st.text_area(
                    "Pergunta *",
                    placeholder="Ex: Como funciona o mecanismo de particionamento no Spark?",
                    height=80,
                )
                acertou = st.checkbox("Acertei / soube responder")
                resposta_ideal = st.text_area(
                    "Resposta ideal (opcional)",
                    placeholder="Anote a resposta correta para estudar depois",
                    height=80,
                )

                if st.form_submit_button("💾 Salvar pergunta", use_container_width=True):
                    if not stack or not pergunta:
                        st.error("Stack e pergunta são obrigatórios.")
                    else:
                        adicionar_pergunta(
                            id_vaga_sel,
                            stack.strip(),
                            pergunta.strip(),
                            dificuldade,
                            acertou,
                            resposta_ideal.strip(),
                        )
                        st.success("✅ Pergunta salva!")
                        st.rerun()

    # ── ESTATÍSTICAS ───────────────────────────────────────────
    with tab_stats:
        df_stats = stats_perguntas()
        if df_stats.empty:
            st.info("Nenhuma pergunta registrada ainda.")
        else:
            st.subheader("Stacks onde você mais erra")
            st.caption("Use isso para priorizar seus estudos.")
            for _, row in df_stats.iterrows():
                taxa_erro = round(row["erros"] / row["total"] * 100) if row["total"] > 0 else 0
                cor = "#D85A30" if taxa_erro >= 50 else "#BA7517" if taxa_erro >= 25 else "#1D9E75"
                st.markdown(
                    f"<div style='display:flex;align-items:center;padding:6px 0;"
                    f"border-bottom:1px solid #f0f0f0'>"
                    f"<span style='flex:2;font-weight:600'>{row['stack']}</span>"
                    f"<span style='flex:1;text-align:center;color:#888;font-size:12px'>"
                    f"{int(row['total'])} pergunta(s)</span>"
                    f"<span style='flex:1;text-align:center;font-size:12px'>"
                    f"{int(row['dificeis'])} difíceis</span>"
                    f"<span style='flex:1;text-align:right;color:{cor};font-weight:700'>"
                    f"{taxa_erro}% erro</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
