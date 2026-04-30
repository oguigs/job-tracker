import streamlit as st
from database.connection import db_connect
from database.candidato import carregar_curriculo_estruturado
from database.candidaturas import atualizar_candidatura

_SCORE_COR = {
    "alta": ("#166534", "#dcfce7", "✅"),  # bg, text, icon
    "media": ("#854d0e", "#fef9c3", "⚠️"),
    "baixa": ("#991b1b", "#fee2e2", "🔴"),
}

_MODAL_ICON = {"Remoto": "🏠", "Híbrido": "🔀", "Presencial": "🏢"}


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
        linhas += [f"{exp.get('cargo', '')} — {exp.get('empresa', '')} ({exp.get('periodo', '')})"]
        for b in exp.get("bullets", []):
            if b.strip():
                linhas.append(f"• {b}")
    if cv.get("habilidades"):
        linhas += ["Habilidades: " + ", ".join(cv["habilidades"])]
    if cv.get("idiomas"):
        linhas += ["Idiomas: " + ", ".join(cv["idiomas"])]
    return "\n".join(linhas)


def _carregar_vagas_ativas(modalidade_filter: str, excluir_aplicadas: bool):
    filtros = [
        "fv.ativa = true",
        "fv.negada = false",
        "fv.descricao IS NOT NULL",
        "fv.descricao != ''",
    ]
    if modalidade_filter != "Todas":
        filtros.append(f"fv.modalidade = '{modalidade_filter}'")
    if excluir_aplicadas:
        filtros.append("(fv.candidatura_status = 'nao_inscrito' OR fv.candidatura_status IS NULL)")
    where = " AND ".join(filtros)
    with db_connect() as con:
        return con.execute(f"""
            SELECT fv.id, fv.titulo, de.nome AS empresa, fv.modalidade,
                   fv.descricao, fv.link, fv.stacks, fv.data_coleta,
                   fv.candidatura_status
            FROM fact_vaga fv
            JOIN dim_empresa de ON fv.id_empresa = de.id
            WHERE {where}
            ORDER BY fv.data_coleta DESC
            LIMIT 500
        """).fetchall()


def _candidaturas_hoje() -> int:
    with db_connect() as con:
        row = con.execute("""
            SELECT COUNT(*) FROM fact_vaga
            WHERE candidatura_status NOT IN ('nao_inscrito', 'negado')
            AND candidatura_data = current_date
        """).fetchone()
    return row[0] if row else 0


def _score_badge(score: int) -> str:
    if score >= 70:
        cat = "alta"
    elif score >= 45:
        cat = "media"
    else:
        cat = "baixa"
    bg, fg, icon = _SCORE_COR[cat]
    return f'<span style="background:{bg};color:{fg};padding:2px 10px;border-radius:12px;font-size:0.85rem;font-weight:600">{icon} {score}</span>'


def _computar_scores(vagas: list, texto_cv: str) -> dict:
    """Roda ANYA (puro Python) para cada vaga. Retorna {id_vaga: score}."""
    from transformers.ats_agents import rodar_anya

    cache_key = "aa_scores"
    if cache_key not in st.session_state:
        st.session_state[cache_key] = {}

    cached = st.session_state[cache_key]
    for v in vagas:
        id_vaga = v[0]
        if id_vaga not in cached:
            anya = rodar_anya(texto_cv, v[4] or "", v[1])
            score = round(
                anya["score_keywords"] * 0.45
                + anya["score_formatacao"] * 0.20
                + anya["score_secoes"] * 0.20
                + anya["score_impacto"] * 0.15
            )
            cached[id_vaga] = {"score": score, "anya": anya}

    return cached


def _gerar_carta_vaga(id_vaga: int, titulo: str, empresa: str, descricao: str, texto_cv: str):
    from transformers.ats_agents import rodar_carta, ollama_disponivel

    key = f"aa_carta_{id_vaga}"
    if key not in st.session_state:
        if not ollama_disponivel():
            st.warning("Ollama não está rodando para gerar a carta.")
            return
        with st.spinner("Gerando carta personalizada..."):
            carta = rodar_carta(texto_cv, descricao, titulo, empresa)
        st.session_state[key] = carta

    carta = st.session_state.get(key, "")
    if carta:
        carta_editada = st.text_area(
            "Carta de apresentação",
            value=carta,
            height=260,
            key=f"aa_carta_txt_{id_vaga}",
            label_visibility="collapsed",
        )
        txt = f"Carta — {titulo} @ {empresa}\n{'─' * 50}\n\n{carta_editada}"
        st.download_button(
            "📥 Baixar carta",
            data=txt.encode("utf-8"),
            file_name=f"carta_{empresa[:15].lower().replace(' ', '_')}.txt",
            mime="text/plain",
            key=f"aa_dl_carta_{id_vaga}",
            use_container_width=True,
        )


def _card_vaga(v: tuple, score_data: dict, texto_cv: str, meta: int, hoje: int):
    id_vaga, titulo, empresa, modalidade, descricao, link, stacks, data_coleta, status = v
    score = score_data.get("score", 0)
    anya = score_data.get("anya", {})

    modal_icon = _MODAL_ICON.get(modalidade or "", "")
    badge_html = _score_badge(score)

    col_badge, col_info, col_actions = st.columns([1, 5, 2])

    with col_badge:
        st.markdown(badge_html, unsafe_allow_html=True)
        st.caption("/100")

    with col_info:
        st.markdown(f"**{titulo}**")
        st.caption(f"{empresa}  {modal_icon} {modalidade or ''}  ·  {str(data_coleta)[:10]}")
        if stacks:
            st.caption(f"🔧 {stacks[:80]}")

        ausentes = anya.get("keywords_ausentes", [])[:5]
        if ausentes:
            badges = " ".join(
                f'<span style="background:#1e293b;color:#94a3b8;padding:1px 7px;border-radius:10px;font-size:0.72rem">{k}</span>'
                for k in ausentes
            )
            st.markdown(f"Faltam: {badges}", unsafe_allow_html=True)

    with col_actions:
        if link:
            st.link_button("Abrir vaga ↗", link, use_container_width=True)

        ja_aplicou = status not in (None, "nao_inscrito")
        if ja_aplicou:
            st.success("✓ Aplicado")
        else:
            if st.button(
                "✓ Candidatar",
                key=f"aa_apply_{id_vaga}",
                use_container_width=True,
                type="primary",
                disabled=(hoje >= meta),
            ):
                atualizar_candidatura(id_vaga, "inscrito")
                st.session_state[f"aa_aplicado_{id_vaga}"] = True
                st.rerun()

    # expander de conteúdo
    with st.expander("📄 Carta de apresentação personalizada"):
        _gerar_carta_vaga(id_vaga, titulo, empresa, descricao, texto_cv)

    st.divider()


def render():
    st.title("⚡ Auto Apply")
    st.caption(
        "Ranqueamento automático das suas melhores vagas por score de match. Gere carta + CV e candidate com um clique."
    )

    cv = carregar_curriculo_estruturado()
    texto_cv = _cv_para_texto(cv)

    if not texto_cv.strip():
        st.warning(
            "Preencha seu currículo no **Construtor de Currículo** para ativar o ranqueamento automático por match."
        )
        st.stop()

    # ── Configurações ─────────────────────────────────────────────
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        score_min = col1.slider(
            "Score mínimo", 0, 100, 50, 5, help="Só mostra vagas acima deste match"
        )
        meta_diaria = col2.number_input("Meta diária de candidaturas", 1, 50, 10)
        modalidade = col3.selectbox("Modalidade", ["Todas", "Remoto", "Híbrido", "Presencial"])
        excluir = col4.checkbox("Ocultar já aplicadas", value=True)

    # ── Progresso do dia ──────────────────────────────────────────
    hoje = _candidaturas_hoje()
    progresso = min(hoje / meta_diaria, 1.0)
    status_txt = f"**{hoje}** de **{meta_diaria}** candidaturas hoje"
    if hoje >= meta_diaria:
        status_txt += " — 🎉 Meta atingida!"
    st.progress(progresso, text=status_txt)
    st.divider()

    # ── Carregar e ranquear vagas ─────────────────────────────────
    vagas = _carregar_vagas_ativas(modalidade, excluir)
    if not vagas:
        st.info("Nenhuma vaga disponível com os filtros atuais.")
        return

    col_spin, col_info = st.columns([1, 4])
    with col_spin:
        calcular = st.button(
            "🔄 Calcular scores",
            use_container_width=True,
            help="Recalcula o match de todas as vagas com seu CV",
        )
    with col_info:
        st.caption(
            f"{len(vagas)} vagas encontradas · Score calculado com ANYA (keywords, formatação, seções, impacto)"
        )

    if calcular:
        st.session_state.pop("aa_scores", None)

    if "aa_scores" not in st.session_state or calcular:
        with st.spinner(f"Ranqueando {len(vagas)} vagas..."):
            _computar_scores(vagas, texto_cv)
        st.rerun()

    scores = st.session_state.get("aa_scores", {})

    # ordena por score desc
    vagas_rankeadas = sorted(
        [(v, scores.get(v[0], {"score": 0, "anya": {}})) for v in vagas],
        key=lambda x: x[1]["score"],
        reverse=True,
    )

    # filtra por score mínimo
    vagas_filtradas = [(v, s) for v, s in vagas_rankeadas if s["score"] >= score_min]

    if not vagas_filtradas:
        st.info(
            f"Nenhuma vaga com score ≥ {score_min}. Reduza o score mínimo ou atualize seu currículo."
        )
        return

    st.markdown(f"**{len(vagas_filtradas)} vagas com score ≥ {score_min}** — ordenadas por match")
    st.divider()

    for vaga, score_data in vagas_filtradas:
        _card_vaga(vaga, score_data, texto_cv, meta_diaria, hoje)
