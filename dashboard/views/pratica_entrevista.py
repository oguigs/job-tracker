import streamlit as st
from database.connection import db_connect
from database.candidato import carregar_curriculo_estruturado

_COR_TIPO = {
    "Comportamental": "🟣",
    "Técnica": "🔵",
    "Situacional": "🟠",
    "Motivacional": "🟢",
}

_SCORE_LABEL = {1: "Fraca", 2: "Regular", 3: "Adequada", 4: "Boa", 5: "Excelente"}
_SCORE_COR = {1: "🔴", 2: "🟠", 3: "🟡", 4: "🟢", 5: "🟢"}


def _cv_para_texto(cv: dict) -> str:
    if not cv:
        return ""
    linhas = []
    dp = cv.get("dados_pessoais", {})
    if dp.get("nome"):
        linhas.append(dp["nome"])
    for exp in cv.get("experiencias", []):
        linhas += [f"{exp.get('cargo', '')} — {exp.get('empresa', '')}"]
        for b in exp.get("bullets", []):
            if b.strip():
                linhas.append(f"• {b}")
    if cv.get("habilidades"):
        linhas += ["Habilidades: " + ", ".join(cv["habilidades"])]
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


def _iniciar_sessao(id_vaga: int, titulo: str, empresa: str, descricao: str, texto_cv: str):
    st.session_state["ei_id_vaga"] = id_vaga
    st.session_state["ei_titulo"] = titulo
    st.session_state["ei_empresa"] = empresa
    st.session_state["ei_descricao"] = descricao
    st.session_state["ei_texto_cv"] = texto_cv
    st.session_state["ei_perguntas"] = []
    st.session_state["ei_idx"] = 0
    st.session_state["ei_historico"] = []
    st.session_state["ei_resposta"] = ""
    st.session_state["ei_feedback"] = None
    st.session_state["ei_fase"] = "gerando"


def _resetar():
    for k in list(st.session_state.keys()):
        if k.startswith("ei_"):
            del st.session_state[k]


def _exportar_relatorio() -> str:
    historico = st.session_state.get("ei_historico", [])
    titulo = st.session_state.get("ei_titulo", "")
    empresa = st.session_state.get("ei_empresa", "")
    sep = "─" * 55
    linhas = [
        "RELATÓRIO DE PRÁTICA DE ENTREVISTA",
        sep,
        f"Vaga: {titulo} — {empresa}",
        f"Perguntas respondidas: {len(historico)}",
    ]
    scores = [h["feedback"]["score"] for h in historico if h.get("feedback")]
    if scores:
        media = sum(scores) / len(scores)
        linhas.append(f"Score médio: {media:.1f}/5")
    linhas += ["", sep]

    for i, h in enumerate(historico, 1):
        fb = h.get("feedback", {})
        linhas += [
            "",
            f"Pergunta {i} [{h['tipo']}]",
            h["pergunta"],
            "",
            "Sua resposta:",
            h["resposta"],
            "",
            f"Score: {fb.get('score', '?')}/5 — {_SCORE_LABEL.get(fb.get('score', 3), '')}",
            f"Pontos fortes: {fb.get('pontos_fortes', '')}",
            f"Melhorar: {fb.get('melhorar', '')}",
            f"Dica: {fb.get('dica', '')}",
            sep,
        ]
    return "\n".join(linhas)


def _tela_selecao():
    from transformers.ats_agents import ollama_disponivel

    st.markdown(
        "Simule entrevistas reais com perguntas específicas para a vaga e receba **feedback instantâneo** por IA."
    )

    if not ollama_disponivel():
        st.warning("Ollama não está rodando. Inicie com `ollama serve` no terminal.")
        return

    vagas = _carregar_vagas()
    if not vagas:
        st.warning("Nenhuma vaga com descrição disponível. Importe vagas primeiro.")
        return

    opcoes = {f"{v[2]} — {v[1]}": v for v in vagas}
    sel = st.selectbox("Selecione a vaga para simular a entrevista", list(opcoes.keys()))
    vaga = opcoes[sel]

    col1, col2 = st.columns([3, 1])
    n_perguntas = col1.slider("Número de perguntas", min_value=4, max_value=12, value=8, step=2)

    cv = carregar_curriculo_estruturado()
    texto_cv = _cv_para_texto(cv)

    usar_cv = col2.checkbox(
        "Usar meu CV",
        value=bool(texto_cv),
        help="Personaliza as perguntas com base no seu currículo",
    )

    if st.button("▶ Iniciar entrevista", type="primary", use_container_width=True):
        _iniciar_sessao(
            id_vaga=vaga[0],
            titulo=vaga[1],
            empresa=vaga[2],
            descricao=vaga[3],
            texto_cv=texto_cv if usar_cv else "",
        )
        st.session_state["ei_n_perguntas"] = n_perguntas
        st.rerun()


def _tela_gerando():
    from transformers.ats_agents import gerar_perguntas_entrevista

    titulo = st.session_state["ei_titulo"]
    empresa = st.session_state["ei_empresa"]
    descricao = st.session_state["ei_descricao"]
    texto_cv = st.session_state["ei_texto_cv"]
    n = st.session_state.get("ei_n_perguntas", 8)

    with st.spinner(f"MIRROR preparando {n} perguntas para **{titulo}** — {empresa}..."):
        perguntas = gerar_perguntas_entrevista(
            titulo_vaga=titulo,
            descricao_vaga=descricao,
            texto_cv=texto_cv,
            n=n,
        )

    if not perguntas:
        st.error("Não foi possível gerar as perguntas. Tente novamente.")
        if st.button("Tentar novamente"):
            st.session_state["ei_fase"] = "gerando"
            st.rerun()
        return

    st.session_state["ei_perguntas"] = perguntas
    st.session_state["ei_fase"] = "pergunta"
    st.rerun()


def _tela_pergunta():
    from transformers.ats_agents import avaliar_resposta

    perguntas = st.session_state["ei_perguntas"]
    idx = st.session_state["ei_idx"]
    titulo = st.session_state["ei_titulo"]
    empresa = st.session_state["ei_empresa"]
    texto_cv = st.session_state["ei_texto_cv"]
    total = len(perguntas)

    # cabeçalho
    col_titulo, col_btn = st.columns([5, 1])
    col_titulo.markdown(f"**{titulo}** — {empresa}")
    if col_btn.button("✕ Encerrar", help="Encerrar sessão atual"):
        _resetar()
        st.rerun()

    progresso = (idx) / total
    st.progress(progresso, text=f"Pergunta {idx + 1} de {total}")
    st.divider()

    q = perguntas[idx]
    tipo_icon = _COR_TIPO.get(q["tipo"], "⚪")
    st.markdown(f"{tipo_icon} **{q['tipo']}**")
    st.markdown(f"### {q['pergunta']}")

    feedback = st.session_state.get("ei_feedback")

    if feedback is None:
        # fase de resposta
        resposta = st.text_area(
            "Sua resposta",
            value=st.session_state.get("ei_resposta", ""),
            height=180,
            placeholder="Estruture sua resposta com clareza. Para perguntas comportamentais, use o método STAR: Situação, Tarefa, Ação, Resultado.",
            label_visibility="collapsed",
        )
        st.session_state["ei_resposta"] = resposta

        col_dica, col_enviar = st.columns([4, 1])
        col_dica.caption(
            "💡 Dica: responda em 2-4 parágrafos. Seja específico e use métricas quando possível."
        )

        if col_enviar.button(
            "Enviar →",
            type="primary",
            use_container_width=True,
            disabled=len(resposta.strip()) < 20,
        ):
            with st.spinner("MIRROR avaliando sua resposta..."):
                fb = avaliar_resposta(
                    pergunta=q["pergunta"],
                    resposta=resposta,
                    titulo_vaga=titulo,
                    texto_cv=texto_cv,
                    tipo_pergunta=q.get("tipo_key", "tecnica"),
                )
            st.session_state["ei_feedback"] = fb
            st.rerun()

        if len(resposta.strip()) < 20 and resposta.strip():
            st.caption("Escreva pelo menos 20 caracteres para enviar.")

    else:
        # fase de feedback
        fb = feedback
        score = fb["score"]
        score_icon = _SCORE_COR.get(score, "⚪")
        score_label = _SCORE_LABEL.get(score, "")

        st.markdown(f"**Avaliação MIRROR** — {score_icon} {score}/5 {score_label}")

        with st.container(border=True):
            if fb.get("pontos_fortes"):
                st.markdown(f"✅ **Pontos fortes**\n\n{fb['pontos_fortes']}")
            if fb.get("melhorar"):
                st.markdown(f"⚠️ **O que melhorar**\n\n{fb['melhorar']}")
            if fb.get("dica"):
                st.info(f"💡 **Dica:** {fb['dica']}")

        # salva no histórico ao avançar
        col_ver, col_prox = st.columns([1, 1])

        with col_ver.expander("Ver minha resposta"):
            st.write(st.session_state.get("ei_resposta", ""))

        prox_label = "Próxima pergunta →" if idx + 1 < total else "Ver resultado final →"
        if col_prox.button(prox_label, type="primary", use_container_width=True):
            st.session_state["ei_historico"].append(
                {
                    "tipo": q["tipo"],
                    "pergunta": q["pergunta"],
                    "resposta": st.session_state.get("ei_resposta", ""),
                    "feedback": fb,
                }
            )
            st.session_state["ei_idx"] = idx + 1
            st.session_state["ei_feedback"] = None
            st.session_state["ei_resposta"] = ""

            if idx + 1 >= total:
                st.session_state["ei_fase"] = "resultado"
            st.rerun()


def _tela_resultado():
    historico = st.session_state.get("ei_historico", [])
    titulo = st.session_state.get("ei_titulo", "")
    empresa = st.session_state.get("ei_empresa", "")

    scores = [h["feedback"]["score"] for h in historico if h.get("feedback")]
    media = sum(scores) / len(scores) if scores else 0

    st.markdown(f"### Resultado da entrevista — {titulo}")
    st.caption(f"{empresa} · {len(historico)} perguntas respondidas")
    st.divider()

    # score geral
    estrelas = "⭐" * round(media) + "☆" * (5 - round(media))
    col_score, col_label = st.columns([1, 3])
    col_score.metric("Score médio", f"{media:.1f}/5")
    col_label.markdown(f"\n\n{estrelas}")

    if media >= 4:
        st.success("Ótimo desempenho! Você está bem preparado para esta entrevista.")
    elif media >= 3:
        st.info("Desempenho adequado. Revise os pontos de melhoria abaixo para afinar.")
    else:
        st.warning("Há espaço considerável para melhorar. Pratique mais as áreas fracas.")

    st.divider()

    # distribuição por tipo
    tipos_scores: dict[str, list[int]] = {}
    for h in historico:
        t = h["tipo"]
        s = h["feedback"]["score"]
        tipos_scores.setdefault(t, []).append(s)

    st.markdown("**Desempenho por categoria**")
    cols = st.columns(len(tipos_scores) or 1)
    for col, (tipo, ss) in zip(cols, tipos_scores.items()):
        m = sum(ss) / len(ss)
        icon = _COR_TIPO.get(tipo, "⚪")
        col.metric(f"{icon} {tipo}", f"{m:.1f}/5")

    st.divider()

    # detalhe pergunta a pergunta
    st.markdown("**Revisão das respostas**")
    for i, h in enumerate(historico, 1):
        fb = h.get("feedback", {})
        score = fb.get("score", 3)
        icon = _SCORE_COR.get(score, "⚪")
        with st.expander(f"Pergunta {i} [{h['tipo']}] — {icon} {score}/5"):
            st.markdown(f"**{h['pergunta']}**")
            st.caption("Sua resposta:")
            st.write(h["resposta"])
            st.divider()
            if fb.get("pontos_fortes"):
                st.markdown(f"✅ {fb['pontos_fortes']}")
            if fb.get("melhorar"):
                st.markdown(f"⚠️ {fb['melhorar']}")
            if fb.get("dica"):
                st.info(f"💡 {fb['dica']}")

    st.divider()

    col_dl, col_nova = st.columns(2)
    relatorio = _exportar_relatorio()
    nome_arq = f"entrevista_{titulo[:25].lower().replace(' ', '_')}.txt"
    col_dl.download_button(
        "📥 Baixar relatório (.txt)",
        data=relatorio.encode("utf-8"),
        file_name=nome_arq,
        mime="text/plain",
        use_container_width=True,
    )
    if col_nova.button("🔄 Nova entrevista", use_container_width=True):
        _resetar()
        st.rerun()


def render():
    st.title("🎤 Prática de Entrevista por IA")

    fase = st.session_state.get("ei_fase")

    if fase is None:
        _tela_selecao()
    elif fase == "gerando":
        _tela_gerando()
    elif fase == "pergunta":
        _tela_pergunta()
    elif fase == "resultado":
        _tela_resultado()
