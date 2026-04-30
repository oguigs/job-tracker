import streamlit as st
from database.connection import db_connect
from database.candidato import carregar_curriculo_estruturado

_COR_TIPO = {
    "Comportamental": ("🟣", "#7c3aed"),
    "Técnica": ("🔵", "#2563eb"),
    "Situacional": ("🟠", "#d97706"),
    "Motivacional": ("🟢", "#16a34a"),
    "Negociação": ("🟡", "#ca8a04"),
}


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
            SELECT fv.id, fv.titulo, de.nome, fv.descricao, fv.stacks
            FROM fact_vaga fv
            JOIN dim_empresa de ON fv.id_empresa = de.id
            WHERE fv.ativa = true AND fv.descricao IS NOT NULL AND fv.descricao != ''
            ORDER BY fv.data_coleta DESC
            LIMIT 200
        """).fetchall()


def _extrair_keywords_vaga(descricao: str, stacks: str) -> list[str]:
    """Extrai keywords técnicas relevantes da vaga para o painel lateral."""
    import re

    _STOP = {
        "de",
        "da",
        "do",
        "em",
        "para",
        "com",
        "que",
        "uma",
        "dos",
        "das",
        "por",
        "ser",
        "ter",
        "são",
        "como",
        "anos",
        "the",
        "and",
        "with",
        "for",
        "are",
        "have",
        "this",
        "that",
        "experience",
        "you",
        "will",
        "not",
        "our",
        "your",
        "team",
        "work",
        "also",
        "mais",
        "deve",
        "muito",
    }
    texto = f"{stacks or ''} {descricao or ''}"
    palavras = re.findall(r"[A-Za-zÀ-ú][A-Za-zÀ-ú0-9\+\#\.]{2,}", texto)
    vistos: set[str] = set()
    resultado = []
    for p in palavras:
        chave = p.lower()
        if chave not in _STOP and chave not in vistos:
            vistos.add(chave)
            resultado.append(p)
        if len(resultado) >= 20:
            break
    return resultado


def _resetar():
    for k in list(st.session_state.keys()):
        if k.startswith("buddy_"):
            del st.session_state[k]


def _tela_setup():
    from transformers.ats_agents import ollama_disponivel

    st.markdown(
        "Cole a pergunta que o entrevistador fizer e receba **pontos-chave para responder** em segundos — direto no fone ou na tela."
    )

    if not ollama_disponivel():
        st.warning("Ollama não está rodando. Inicie com `ollama serve` no terminal.")
        return

    vagas = _carregar_vagas()
    if not vagas:
        st.warning("Nenhuma vaga com descrição disponível. Importe vagas primeiro.")
        return

    opcoes = {f"{v[2]} — {v[1]}": v for v in vagas}
    sel = st.selectbox("Para qual vaga é a entrevista?", list(opcoes.keys()))
    vaga = opcoes[sel]

    cv = carregar_curriculo_estruturado()
    texto_cv = _cv_para_texto(cv)
    if not texto_cv:
        st.caption("💡 Preencha o **Construtor de Currículo** para coaching mais personalizado.")

    if st.button("▶ Iniciar sessão ao vivo", type="primary", use_container_width=True):
        st.session_state["buddy_id_vaga"] = vaga[0]
        st.session_state["buddy_titulo"] = vaga[1]
        st.session_state["buddy_empresa"] = vaga[2]
        st.session_state["buddy_descricao"] = vaga[3]
        st.session_state["buddy_stacks"] = vaga[4] or ""
        st.session_state["buddy_texto_cv"] = texto_cv
        st.session_state["buddy_historico"] = []
        st.session_state["buddy_ativo"] = True
        st.rerun()


def _tela_live():
    from transformers.ats_agents import rodar_buddy

    titulo = st.session_state["buddy_titulo"]
    empresa = st.session_state["buddy_empresa"]
    descricao = st.session_state["buddy_descricao"]
    stacks = st.session_state["buddy_stacks"]
    texto_cv = st.session_state["buddy_texto_cv"]
    historico = st.session_state.get("buddy_historico", [])

    keywords_vaga = _extrair_keywords_vaga(descricao, stacks)

    # ── layout principal ──────────────────────────────────
    col_arsenal, col_main = st.columns([1, 2], gap="large")

    # ── COLUNA ESQUERDA — Arsenal ─────────────────────────
    with col_arsenal:
        st.markdown(f"**{titulo}**")
        st.caption(empresa)
        st.divider()

        st.markdown("**🎯 Keywords da vaga**")
        st.caption("Mencione no mínimo 3 destas na entrevista")
        kw_html = " ".join(
            f'<span style="background:#1e3a5f;color:#93c5fd;padding:2px 8px;border-radius:12px;font-size:0.78rem;margin:2px;display:inline-block">{k}</span>'
            for k in keywords_vaga
        )
        st.markdown(kw_html, unsafe_allow_html=True)

        st.divider()

        cv = carregar_curriculo_estruturado()
        experiencias = cv.get("experiencias", []) if cv else []
        if experiencias:
            st.markdown("**💼 Suas experiências**")
            for exp in experiencias[:3]:
                st.caption(f"• {exp.get('cargo', '')} @ {exp.get('empresa', '')}")

        habilidades = cv.get("habilidades", []) if cv else []
        if habilidades:
            st.markdown("**⚡ Suas habilidades**")
            st.caption(", ".join(habilidades[:10]))

        st.divider()
        if st.button("✕ Encerrar sessão", use_container_width=True):
            _resetar()
            st.rerun()

    # ── COLUNA DIREITA — Coaching ao vivo ────────────────
    with col_main:
        n = len(historico)
        st.markdown(
            f"**Sessão ao vivo** · {n} pergunta{'s' if n != 1 else ''} respondida{'s' if n != 1 else ''}"
        )

        pergunta_input = st.text_area(
            "Cole a pergunta do entrevistador aqui",
            height=90,
            placeholder="Ex: Me fale sobre uma situação em que você teve que lidar com um prazo apertado...",
            label_visibility="visible",
            key="buddy_input",
        )

        col_btn, col_clear = st.columns([3, 1])
        gerar = col_btn.button(
            "⚡ Coaching agora",
            type="primary",
            use_container_width=True,
            disabled=len(pergunta_input.strip()) < 10,
        )
        if col_clear.button("Limpar", use_container_width=True):
            st.session_state["buddy_coaching"] = None
            st.rerun()

        if gerar and pergunta_input.strip():
            with st.spinner("BUDDY analisando..."):
                coaching = rodar_buddy(
                    pergunta=pergunta_input.strip(),
                    titulo_vaga=titulo,
                    descricao_vaga=descricao,
                    texto_cv=texto_cv,
                )
            st.session_state["buddy_coaching"] = coaching
            st.session_state["buddy_pergunta_atual"] = pergunta_input.strip()

        coaching = st.session_state.get("buddy_coaching")

        if coaching:
            tipo = coaching.get("tipo", "Técnica")
            icon, _ = _COR_TIPO.get(tipo, ("⚪", "#666"))

            st.markdown(f"{icon} **{tipo}**")
            st.divider()

            # Pontos principais — destaque máximo
            pontos = coaching.get("pontos", [])
            if pontos:
                st.markdown("**Fale sobre:**")
                for p in pontos:
                    if p.strip():
                        st.markdown(
                            f'<div style="background:#0f2942;border-left:3px solid #3b82f6;padding:8px 12px;margin:4px 0;border-radius:4px;font-size:0.95rem">{p}</div>',
                            unsafe_allow_html=True,
                        )

            # Keywords para mencionar
            kws = coaching.get("keywords", [])
            if kws:
                st.markdown("**Mencione:**")
                kw_badges = " ".join(
                    f'<span style="background:#064e3b;color:#6ee7b7;padding:2px 10px;border-radius:12px;font-size:0.8rem;margin:2px;display:inline-block">{k}</span>'
                    for k in kws
                )
                st.markdown(kw_badges, unsafe_allow_html=True)

            # Lembrete
            if coaching.get("lembrete"):
                st.info(f"💡 {coaching['lembrete']}")

            # salvar no histórico
            pergunta_atual = st.session_state.get("buddy_pergunta_atual", "")
            if st.button("✓ Salvar e limpar para próxima pergunta", use_container_width=True):
                historico.append(
                    {
                        "pergunta": pergunta_atual,
                        "coaching": coaching,
                    }
                )
                st.session_state["buddy_historico"] = historico
                st.session_state["buddy_coaching"] = None
                st.rerun()

        # Histórico da sessão
        if historico:
            st.divider()
            st.markdown(f"**Histórico da sessão ({len(historico)})**")
            for i, h in enumerate(reversed(historico), 1):
                c = h["coaching"]
                tipo_h = c.get("tipo", "")
                icon_h, _ = _COR_TIPO.get(tipo_h, ("⚪", "#666"))
                with st.expander(f"{icon_h} P{len(historico) - i + 1}: {h['pergunta'][:60]}..."):
                    for p in c.get("pontos", []):
                        st.caption(f"• {p}")


def render():
    st.title("🎧 Interview Buddy")

    if not st.session_state.get("buddy_ativo"):
        _tela_setup()
    else:
        _tela_live()
