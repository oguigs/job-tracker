import streamlit as st
from database.connection import db_connect
from database.candidato import carregar_curriculo_estruturado


def _cv_para_texto(cv: dict) -> str:
    if not cv:
        return ""
    linhas = []
    dp = cv.get("dados_pessoais", {})
    if dp.get("nome"):
        linhas.append(dp["nome"])
    if cv.get("resumo"):
        linhas += ["", cv["resumo"]]
    for exp in cv.get("experiencias", []):
        linhas += [
            "",
            f"{exp.get('cargo', '')} — {exp.get('empresa', '')} ({exp.get('periodo', '')})",
        ]
        for b in exp.get("bullets", []):
            if b.strip():
                linhas.append(f"• {b}")
    if cv.get("habilidades"):
        linhas += ["", "Habilidades: " + ", ".join(cv["habilidades"])]
    if cv.get("idiomas"):
        linhas += ["", "Idiomas: " + ", ".join(cv["idiomas"])]
    return "\n".join(linhas)


def _carregar_vagas():
    with db_connect() as con:
        return con.execute("""
            SELECT fv.id, fv.titulo, de.nome, fv.descricao
            FROM fact_vaga fv
            JOIN dim_empresa de ON fv.id_empresa = de.id
            WHERE fv.ativa = true AND fv.descricao IS NOT NULL AND fv.descricao != ''
            ORDER BY fv.data_coleta DESC
            LIMIT 200
        """).fetchall()


def _gerar_txt_exportacao(carta: str, titulo: str, empresa: str) -> str:
    sep = "─" * 55
    linhas = [
        "CARTA DE APRESENTAÇÃO",
        sep,
        f"Vaga: {titulo} — {empresa}",
        sep,
        "",
        carta,
    ]
    return "\n".join(linhas)


def render():
    from transformers.ats_agents import rodar_carta, humanizar_carta, ollama_disponivel

    st.title("✉️ Carta de Apresentação")
    st.caption(
        "Gere cartas personalizadas por vaga em segundos. Cada carta é adaptada ao que o recrutador quer ler."
    )

    if not ollama_disponivel():
        st.warning("Ollama não está rodando. Inicie com `ollama serve` no terminal.")
        return

    vagas = _carregar_vagas()
    if not vagas:
        st.warning("Nenhuma vaga com descrição disponível. Importe vagas primeiro.")
        return

    opcoes = {f"{v[2]} — {v[1]}": v for v in vagas}

    col_sel, col_idioma = st.columns([4, 1])
    sel = col_sel.selectbox("Vaga", list(opcoes.keys()), label_visibility="collapsed")
    idioma = col_idioma.selectbox("Idioma", ["PT-BR", "EN-US"], label_visibility="collapsed")
    vaga = opcoes[sel]

    id_vaga, titulo, empresa, descricao = vaga

    cv = carregar_curriculo_estruturado()
    texto_cv = _cv_para_texto(cv)

    with st.expander("⚙️ Personalizar contexto (opcional)", expanded=False):
        contexto_extra = st.text_area(
            "Por que você quer esta vaga / empresa?",
            height=80,
            placeholder="Ex: admiro o produto X da empresa, tenho interesse no setor Y, quero trabalhar com o stack Z que usam...",
            label_visibility="collapsed",
        )
        if not texto_cv:
            st.info(
                "Preencha seu currículo no **Construtor de Currículo** para cartas mais personalizadas."
            )

    key_carta = f"carta_{id_vaga}_{idioma}"

    if st.button("✦ Gerar carta", type="primary", use_container_width=True):
        cv_completo = texto_cv
        if contexto_extra.strip():
            cv_completo = f"{texto_cv}\n\nMOTIVAÇÃO EXTRA: {contexto_extra.strip()}"

        with st.spinner("Redigindo sua carta de apresentação..."):
            carta = rodar_carta(
                texto_cv=cv_completo,
                descricao_vaga=descricao,
                titulo_vaga=titulo,
                empresa=empresa,
                idioma=idioma.lower().replace("-", "-"),
            )
        st.session_state[key_carta] = carta

    if st.session_state.get(key_carta):
        carta = st.session_state[key_carta]
        st.divider()

        col_label, col_human, col_regen = st.columns([4, 1, 1])
        col_label.markdown("**Carta gerada — edite antes de enviar**")
        if col_human.button(
            "✦ Humanizar", use_container_width=True, help="Remove padrões de IA do texto"
        ):
            with st.spinner("Humanizando..."):
                st.session_state[key_carta] = humanizar_carta(st.session_state[key_carta])
            st.rerun()
        if col_regen.button("↻ Regerar", use_container_width=True):
            del st.session_state[key_carta]
            st.rerun()

        carta_editada = st.text_area(
            "Carta",
            value=carta,
            height=420,
            label_visibility="collapsed",
            key=f"edit_{key_carta}",
        )

        st.divider()

        col_tip, col_dl = st.columns([3, 2])

        with col_tip:
            with st.expander("📋 Dicas de uso"):
                st.markdown(
                    """
- Cole no **corpo do e-mail** — não como anexo
- **Assunto sugerido:** `Candidatura — {titulo}` + seu nome
- Revise nomes próprios e pronomes antes de enviar
- Ajuste o **parágrafo 1** com algo que você sabe sobre a empresa
- Mantenha em **menos de 300 palavras** sempre que possível
""".replace("{titulo}", titulo)
                )

        txt = _gerar_txt_exportacao(carta_editada, titulo, empresa)
        nome_arq = f"carta_{empresa[:20].lower().replace(' ', '_')}_{titulo[:20].lower().replace(' ', '_')}.txt"
        col_dl.download_button(
            "📥 Baixar carta (.txt)",
            data=txt.encode("utf-8"),
            file_name=nome_arq,
            mime="text/plain",
            use_container_width=True,
        )
        col_dl.caption("Cole no Google Docs para formatar antes de enviar.")
