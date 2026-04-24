import streamlit as st
import tempfile
import os
from transformers.curriculo_parser import extrair_texto_pdf
from transformers.ats_agents import analisar_curriculo, rodar_anya, ollama_disponivel, rodar_nexus, detectar_idioma
from database.connection import db_connect


def _cor_score(score: int) -> str:
    if score >= 75:
        return "#00ff88"
    if score >= 50:
        return "#ffd700"
    if score >= 25:
        return "#ff8c00"
    return "#ff4444"


def _barra(score: int, label: str):
    cor = _cor_score(score)
    preenchido = int(score / 10)
    vazio = 10 - preenchido
    barra = "█" * preenchido + "░" * vazio
    st.markdown(
        f"<div style='font-family:monospace; font-size:14px; margin:4px 0'>"
        f"<span style='color:#aaa'>{label:<12}</span> "
        f"<span style='color:{cor}'>{barra}</span> "
        f"<span style='color:{cor}; font-weight:bold'>{score}%</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _linha_keyword(presente: bool, termo: str):
    icone = "✓" if presente else "✗"
    cor   = "#00ff88" if presente else "#ff4444"
    st.markdown(
        f"<span style='font-family:monospace; color:{cor}; font-size:13px'>"
        f"{icone} {termo.upper()}</span>",
        unsafe_allow_html=True,
    )


def _bloco_terminal(titulo: str, conteudo: str, cor_titulo: str = "#00ff88"):
    st.markdown(
        f"<div style='"
        f"background:#0d1117; border:1px solid #30363d; border-radius:6px;"
        f"padding:16px; margin:8px 0; font-family:monospace'>"
        f"<div style='color:{cor_titulo}; font-size:12px; margin-bottom:8px'>"
        f"░ ANALISADO POR: {titulo}</div>"
        f"<div style='color:#e6edf3; font-size:14px; line-height:1.6'>{conteudo}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def render():
    st.title("Análise de Currículo")
    st.caption("Cole a descrição da vaga ou selecione uma do banco. Faça upload do seu currículo em PDF.")

    col_upload, col_vaga = st.columns([1, 1])

    with col_upload:
        st.markdown("**Seu currículo (PDF)**")
        pdf_file = st.file_uploader("", type=["pdf"], label_visibility="collapsed")

    with col_vaga:
        st.markdown("**Vaga para comparar**")
        modo = st.radio("", ["Selecionar do banco", "Colar descrição manual"],
                        horizontal=True, label_visibility="collapsed")

    descricao_vaga = ""
    titulo_vaga = ""

    if modo == "Selecionar do banco":
        with db_connect(read_only=True) as con:
            vagas = con.execute("""
                SELECT fv.id, fv.titulo, de.nome
                FROM fact_vaga fv
                JOIN dim_empresa de ON fv.id_empresa = de.id
                WHERE (fv.negada = false OR fv.negada IS NULL)
                  AND fv.ativa = true
                  AND fv.descricao IS NOT NULL
                  AND fv.descricao != ''
                ORDER BY fv.data_coleta DESC
                LIMIT 200
            """).fetchall()

        if not vagas:
            st.warning("Nenhuma vaga com descrição no banco. Rode o pipeline primeiro ou cole a descrição manualmente.")
        else:
            opcoes = {f"{v[2]} — {v[1]}": (v[0], v[1]) for v in vagas}
            sel = st.selectbox("", list(opcoes.keys()), label_visibility="collapsed")
            id_vaga, titulo_vaga = opcoes[sel]
            with db_connect(read_only=True) as con:
                row = con.execute("SELECT descricao FROM fact_vaga WHERE id = ?", [id_vaga]).fetchone()
            descricao_vaga = row[0] if row else ""
    else:
        titulo_vaga = st.text_input("Título da vaga", placeholder="Ex: Analista Pleno de Dados")
        descricao_vaga = st.text_area("Descrição da vaga", height=200,
                                       placeholder="Cole aqui o texto completo da vaga...")

    st.divider()

    col_lang, _ = st.columns([1, 3])
    idioma_sel = col_lang.selectbox(
        "Idioma do currículo e sugestões",
        options=["Automático", "Português (pt-BR)", "English (en-US)"],
        index=0,
    )
    idioma = {"Automático": "auto", "Português (pt-BR)": "pt-BR", "English (en-US)": "en-US"}[idioma_sel]

    llm_ok = ollama_disponivel()
    if not llm_ok:
        st.warning(
            "**Ollama não está rodando.** "
            "Os scores serão calculados normalmente, mas os agentes VANELLOPE e ARYA (análise textual) "
            "ficarão desativados. Para ativar: abra o terminal e rode `ollama serve`."
        )

    rodar = st.button("▶ RODAR ANÁLISE", type="primary", use_container_width=True)

    if rodar:
        if not pdf_file:
            st.error("Faça upload do currículo em PDF.")
            return
        if not descricao_vaga:
            st.error("Informe a descrição da vaga.")
            return

        # salva PDF temporariamente para o pdfplumber ler
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_file.read())
            tmp_path = tmp.name

        try:
            with st.status("Processando...", expanded=True) as status:
                st.write("░ ANYA EXTRAINDO DADOS DO CURRÍCULO...")
                texto_cv = extrair_texto_pdf(tmp_path)
                if not texto_cv.strip():
                    st.error("Não foi possível extrair texto do PDF. Tente um PDF com texto selecionável.")
                    return

                st.write(f"░ PARSER ENCONTROU {len(texto_cv)} CARACTERES")
                st.write("░ ANYA ANALISANDO KEYWORDS...")
                anya = rodar_anya(texto_cv, descricao_vaga, titulo_vaga)

                idioma_final = idioma
                if idioma_final == "auto":
                    idioma_final = detectar_idioma(texto_cv + " " + descricao_vaga)
                st.write(f"░ IDIOMA DETECTADO: {'PORTUGUÊS' if idioma_final == 'pt-BR' else 'ENGLISH'}")

                if llm_ok:
                    st.write("░ VANELLOPE AVALIANDO COMPATIBILIDADE DE CARREIRA...")
                    st.write("░ ARYA CALCULANDO ESTRATÉGIA ANTI-ATS...")
                    st.write("░ SINTETIZADOR COMPILANDO DIAGNÓSTICO FINAL...")
                    resultado = analisar_curriculo(texto_cv, descricao_vaga, titulo_vaga, idioma_final)
                else:
                    from transformers.ats_agents import rodar_sintetizador
                    sintese = rodar_sintetizador(anya, "", "", texto_cv, descricao_vaga, titulo_vaga)
                    resultado = {"anya": anya, "vanellope": None, "arya": None, "sintetizador": sintese}

                status.update(label="Análise concluída", state="complete")

        finally:
            os.unlink(tmp_path)

        st.session_state["ats_resultado"]    = resultado
        st.session_state["ats_texto_cv"]     = texto_cv
        st.session_state["ats_descricao"]    = descricao_vaga
        st.session_state["ats_titulo_vaga"]  = titulo_vaga
        st.session_state["ats_nexus"]        = None

    if "ats_resultado" in st.session_state and st.session_state["ats_resultado"]:
        _exibir_resultado(st.session_state["ats_resultado"], llm_ok)

        if llm_ok:
            st.divider()
            if st.button("✦ OTIMIZAR CURRÍCULO COM NEXUS", type="primary", use_container_width=True):
                with st.status("░ NEXUS REESCREVENDO CURRÍCULO...", expanded=True) as status:
                    st.write("░ ANALISANDO GAPS E REESCREVENDO BULLETS...")
                    nexus = rodar_nexus(
                        st.session_state["ats_texto_cv"],
                        st.session_state["ats_descricao"],
                        st.session_state["ats_titulo_vaga"],
                        st.session_state["ats_resultado"]["anya"],
                        st.session_state["ats_resultado"].get("idioma", "pt-BR"),
                    )
                    st.session_state["ats_nexus"] = nexus
                    status.update(label="Otimização concluída", state="complete")

        if st.session_state.get("ats_nexus"):
            _exibir_nexus(st.session_state["ats_nexus"])


def _exibir_resultado(resultado: dict, llm_ok: bool):
    anya    = resultado["anya"]
    sintese = resultado["sintetizador"]

    st.divider()

    # ── SCORE GERAL ──────────────────────────────────────────────
    score  = sintese["score"]
    status = sintese["status"]
    cor    = _cor_score(score)

    st.markdown(
        f"<div style='text-align:center; font-family:monospace; padding:24px 0'>"
        f"<div style='font-size:64px; font-weight:bold; color:{cor}'>{score}</div>"
        f"<div style='font-size:18px; color:#aaa'>/100</div>"
        f"<div style='font-size:20px; color:{cor}; margin-top:8px; letter-spacing:3px'>"
        f"{status}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if sintese.get("brief"):
        st.markdown(
            f"<div style='background:#161b22; border-left:3px solid {cor}; "
            f"padding:12px 16px; margin:8px 0; font-family:monospace; color:#e6edf3; font-size:14px'>"
            f"{sintese['brief']}</div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── DIMENSÕES ────────────────────────────────────────────────
    st.markdown("<div style='font-family:monospace; color:#888; font-size:12px'>SCORE ATS DETALHADO</div>",
                unsafe_allow_html=True)
    for label, val in sintese["dimensoes"].items():
        _barra(val, label)

    st.divider()

    # ── ANYA ─────────────────────────────────────────────────────
    col_neg, col_pos = st.columns(2)

    with col_neg:
        st.markdown("**✗ Palavras-chave ausentes**")
        for kw in anya["keywords_ausentes"][:20]:
            _linha_keyword(False, kw)

    with col_pos:
        st.markdown("**✓ Palavras-chave presentes**")
        for kw in anya["keywords_presentes"][:20]:
            _linha_keyword(True, kw)

    st.divider()

    # formatação
    fmt = anya["formatacao"]
    st.markdown("<div style='font-family:monospace; color:#888; font-size:12px; margin-bottom:8px'>CHECKLIST DE FORMATAÇÃO</div>",
                unsafe_allow_html=True)
    checks = {
        "Bullet points":        fmt["tem_bullets"],
        "Datas de experiência": fmt["tem_datas"],
        "Email":                fmt["tem_email"],
        "LinkedIn":             fmt["tem_linkedin"],
        "Tamanho adequado":     fmt["tamanho_ok"],
    }
    cols = st.columns(len(checks))
    for col, (label, ok) in zip(cols, checks.items()):
        icone = "✓" if ok else "✗"
        cor   = "#00ff88" if ok else "#ff4444"
        col.markdown(
            f"<div style='text-align:center; font-family:monospace'>"
            f"<div style='font-size:20px; color:{cor}'>{icone}</div>"
            f"<div style='font-size:11px; color:#aaa'>{label}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # impacto
    imp = anya["impacto"]
    if imp["exemplos"]:
        st.markdown(
            f"<div style='font-family:monospace; font-size:13px; color:#aaa; margin-top:12px'>"
            f"▸ {imp['ocorrencias']} métricas quantificadas encontradas: "
            f"{' · '.join(imp['exemplos'])}</div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── VANELLOPE & ARYA ─────────────────────────────────────────
    if resultado.get("vanellope"):
        _bloco_terminal("VANELLOPE — MÓDULO CARREIRA", resultado["vanellope"], "#ffd700")
        _bloco_terminal("ARYA — MÓDULO ESTRATÉGIA", resultado["arya"], "#ff6b6b")
    else:
        st.info("Rode `ollama serve` no terminal para ativar os agentes VANELLOPE e ARYA.")

    # seções detectadas
    with st.expander("Seções detectadas no currículo"):
        for secao, presente in anya["secoes"].items():
            icone = "✓" if presente else "✗"
            cor   = "green" if presente else "red"
            st.markdown(f":{cor}[{icone} {secao.capitalize()}]")


def _exibir_nexus(nexus: dict):
    st.divider()
    st.markdown(
        "<div style='font-family:monospace; color:#a78bfa; font-size:13px; "
        "letter-spacing:2px; margin-bottom:16px'>✦ NEXUS — MÓDULO OTIMIZADOR</div>",
        unsafe_allow_html=True,
    )

    # título sugerido
    if nexus.get("titulo_sugerido"):
        st.markdown("**Título sugerido para esta vaga**")
        col_a, col_b = st.columns(2)
        col_a.markdown(
            "<div style='background:#1a1a2e; padding:12px; border-radius:4px; "
            "font-family:monospace; color:#ff6b6b; font-size:13px'>"
            "ANTES<br><br>" + (nexus.get("titulo_original", "Seu título atual") or "Seu título atual") +
            "</div>", unsafe_allow_html=True
        )
        col_b.markdown(
            "<div style='background:#0d2818; padding:12px; border-radius:4px; "
            "font-family:monospace; color:#00ff88; font-size:13px'>"
            "DEPOIS<br><br>" + nexus["titulo_sugerido"] +
            "</div>", unsafe_allow_html=True
        )

    st.divider()

    # resumo otimizado
    if nexus.get("resumo_otimizado"):
        st.markdown("**Resumo profissional otimizado**")
        st.markdown(
            "<div style='background:#0d2818; border-left:3px solid #a78bfa; "
            "padding:14px 16px; font-family:monospace; color:#e6edf3; font-size:14px; "
            "line-height:1.7'>" + nexus["resumo_otimizado"] + "</div>",
            unsafe_allow_html=True,
        )
        if st.button("Copiar resumo", key="copy_resumo"):
            st.write(nexus["resumo_otimizado"])

    st.divider()

    # bullets antes/depois
    if nexus.get("bullets"):
        st.markdown("**Bullets reescritos**")
        for i, bullet in enumerate(nexus["bullets"], 1):
            st.markdown(f"*Experiência {i}*")
            col_a, col_b = st.columns(2)
            col_a.markdown(
                "<div style='background:#1a1a2e; padding:12px; border-radius:4px; "
                "font-family:monospace; color:#ff6b6b; font-size:13px; line-height:1.6'>"
                "✗ ANTES<br><br>" + bullet["antes"] + "</div>",
                unsafe_allow_html=True,
            )
            col_b.markdown(
                "<div style='background:#0d2818; padding:12px; border-radius:4px; "
                "font-family:monospace; color:#00ff88; font-size:13px; line-height:1.6'>"
                "✓ DEPOIS<br><br>" + bullet["depois"] + "</div>",
                unsafe_allow_html=True,
            )
            st.markdown("")

    # fallback: se o parser não extraiu estrutura, mostra o raw
    if not nexus.get("bullets") and not nexus.get("resumo_otimizado") and nexus.get("raw"):
        st.markdown("**Sugestões do NEXUS**")
        st.markdown(
            "<div style='background:#0d1117; border:1px solid #30363d; border-radius:6px; "
            "padding:16px; font-family:monospace; color:#e6edf3; font-size:14px; "
            "white-space:pre-wrap'>" + nexus["raw"] + "</div>",
            unsafe_allow_html=True,
        )
