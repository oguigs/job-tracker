import uuid
import json
import streamlit as st
from database.candidato import carregar_curriculo_estruturado, salvar_curriculo_estruturado
from database.connection import db_connect

_CV_VAZIO = {
    "dados_pessoais": {
        "nome": "",
        "email": "",
        "telefone": "",
        "linkedin": "",
        "github": "",
        "localizacao": "",
    },
    "resumo": "",
    "experiencias": [],
    "educacao": [],
    "habilidades": [],
    "certificacoes": [],
    "idiomas": [],
}


def _cv_para_texto(cv: dict) -> str:
    """Converte o currículo estruturado em texto plano para os agentes de IA."""
    linhas = []
    dp = cv.get("dados_pessoais", {})
    if dp.get("nome"):
        linhas.append(dp["nome"])
    contato = " | ".join(
        v for v in [dp.get("email"), dp.get("linkedin"), dp.get("localizacao")] if v
    )
    if contato:
        linhas.append(contato)
    if cv.get("resumo"):
        linhas += ["", "RESUMO", cv["resumo"]]
    for exp in cv.get("experiencias", []):
        linhas += [
            "",
            f"{exp.get('cargo', '')} — {exp.get('empresa', '')} ({exp.get('periodo', '')})",
        ]
        for b in exp.get("bullets", []):
            if b.strip():
                linhas.append(f"• {b}")
    for edu in cv.get("educacao", []):
        linhas += [
            "",
            f"{edu.get('curso', '')} — {edu.get('instituicao', '')} ({edu.get('periodo', '')})",
        ]
    if cv.get("habilidades"):
        linhas += ["", "HABILIDADES", ", ".join(cv["habilidades"])]
    if cv.get("idiomas"):
        linhas += ["", "IDIOMAS"] + cv["idiomas"]
    return "\n".join(linhas)


def _gerar_txt_exportacao(cv: dict, titulo_otimizado: str = "", resumo_otimizado: str = "") -> str:
    dp = cv.get("dados_pessoais", {})
    sep = "━" * 55
    linhas = []

    if dp.get("nome"):
        linhas.append(dp["nome"].upper())
    contato = " | ".join(
        v
        for v in [
            dp.get("email"),
            dp.get("telefone"),
            dp.get("linkedin"),
            dp.get("github"),
            dp.get("localizacao"),
        ]
        if v
    )
    if contato:
        linhas.append(contato)
    linhas.append("")

    if titulo_otimizado:
        linhas += [titulo_otimizado, ""]

    resumo = resumo_otimizado or cv.get("resumo", "")
    if resumo:
        linhas += ["RESUMO PROFISSIONAL", sep, resumo, ""]

    if cv.get("experiencias"):
        linhas += ["EXPERIÊNCIA PROFISSIONAL", sep]
        for exp in cv["experiencias"]:
            cargo = exp.get("cargo", "")
            empresa = exp.get("empresa", "")
            periodo = exp.get("periodo", "")
            header = f"{cargo} — {empresa}"
            if periodo:
                header += f"  |  {periodo}"
            linhas.append(header)
            for b in exp.get("bullets", []):
                if b.strip():
                    linhas.append(f"• {b}")
            linhas.append("")

    if cv.get("educacao"):
        linhas += ["EDUCAÇÃO", sep]
        for edu in cv["educacao"]:
            linha = f"{edu.get('curso', '')} — {edu.get('instituicao', '')}"
            if edu.get("periodo"):
                linha += f"  |  {edu['periodo']}"
            linhas.append(linha)
            if edu.get("descricao"):
                linhas.append(f"  {edu['descricao']}")
        linhas.append("")

    if cv.get("habilidades"):
        linhas += ["HABILIDADES TÉCNICAS", sep, ", ".join(cv["habilidades"]), ""]

    if cv.get("certificacoes"):
        linhas += ["CERTIFICAÇÕES", sep] + cv["certificacoes"] + [""]

    if cv.get("idiomas"):
        linhas += ["IDIOMAS", sep] + cv["idiomas"] + [""]

    return "\n".join(linhas)


def _importar_arquivo(cv: dict) -> dict:
    """Seção de upload PDF/DOCX — retorna CV atualizado se importação feita."""
    from transformers.cv_extractor import extrair_texto
    from transformers.ats_agents import parsear_curriculo_para_estrutura, ollama_disponivel

    with st.expander("📂 Importar currículo (PDF ou DOCX)", expanded=False):
        st.caption(
            "O arquivo é lido localmente. A IA extrai os dados e pré-preenche o editor — você revisa antes de salvar."
        )

        arquivo = st.file_uploader(
            "Selecione o arquivo",
            type=["pdf", "docx"],
            label_visibility="collapsed",
            key="cv_upload",
        )

        if arquivo is not None:
            if not ollama_disponivel():
                st.warning(
                    "Ollama não está rodando. Inicie com `ollama serve` para usar a extração por IA."
                )
                return cv

            col_parse, col_info = st.columns([2, 3])
            col_info.caption(f"📄 {arquivo.name}  ·  {arquivo.size // 1024} KB")

            if col_parse.button(
                "⚡ Extrair e preencher",
                type="primary",
                use_container_width=True,
                key="btn_importar",
            ):
                with st.spinner("Lendo arquivo e extraindo dados com IA..."):
                    try:
                        texto = extrair_texto(arquivo, arquivo.name)
                        if len(texto.strip()) < 50:
                            st.error(
                                "Não foi possível extrair texto do arquivo. Verifique se o PDF não é uma imagem escaneada."
                            )
                            return cv
                        cv_importado = parsear_curriculo_para_estrutura(texto)
                        st.session_state["cv_importado"] = cv_importado
                    except Exception as e:
                        st.error(f"Erro ao processar arquivo: {e}")
                        return cv
                st.rerun()

        cv_importado = st.session_state.get("cv_importado")
        if cv_importado:
            dp = cv_importado.get("dados_pessoais", {})
            nome = dp.get("nome") or "(sem nome)"
            n_exp = len(cv_importado.get("experiencias", []))
            n_edu = len(cv_importado.get("educacao", []))
            n_hab = len(cv_importado.get("habilidades", []))

            st.success(
                f"**{nome}** extraído — {n_exp} experiência(s), {n_edu} formação(ões), {n_hab} habilidade(s)"
            )
            st.caption(
                "Clique em **Aplicar** para preencher o editor com os dados extraídos. O currículo atual será substituído."
            )

            col_aplicar, col_descartar = st.columns(2)
            if col_aplicar.button(
                "✓ Aplicar ao editor",
                type="primary",
                use_container_width=True,
                key="btn_aplicar_import",
            ):
                del st.session_state["cv_importado"]
                st.session_state.pop("cv_upload", None)
                salvar_curriculo_estruturado(cv_importado)
                st.rerun()
                return cv_importado
            if col_descartar.button(
                "✕ Descartar", use_container_width=True, key="btn_descartar_import"
            ):
                del st.session_state["cv_importado"]
                st.rerun()

    return cv


def _tab_editor(cv: dict) -> dict:
    cv = _importar_arquivo(cv)
    st.subheader("Dados pessoais")
    dp = cv.get("dados_pessoais", {})
    col1, col2 = st.columns(2)
    dp["nome"] = col1.text_input("Nome completo", value=dp.get("nome", ""))
    dp["email"] = col2.text_input("E-mail", value=dp.get("email", ""))
    col3, col4 = st.columns(2)
    dp["telefone"] = col3.text_input("Telefone", value=dp.get("telefone", ""))
    dp["localizacao"] = col4.text_input(
        "Localização", value=dp.get("localizacao", ""), placeholder="São Paulo, SP"
    )
    col5, col6 = st.columns(2)
    dp["linkedin"] = col5.text_input(
        "LinkedIn", value=dp.get("linkedin", ""), placeholder="linkedin.com/in/..."
    )
    dp["github"] = col6.text_input(
        "GitHub", value=dp.get("github", ""), placeholder="github.com/..."
    )
    cv["dados_pessoais"] = dp

    st.divider()
    st.subheader("Resumo profissional")
    cv["resumo"] = st.text_area(
        "Resumo",
        value=cv.get("resumo", ""),
        height=100,
        label_visibility="collapsed",
        placeholder="2-3 frases destacando sua experiência, especialidade e diferencial...",
    )

    st.divider()
    st.subheader("Experiência profissional")

    experiencias = cv.get("experiencias", [])
    for i, exp in enumerate(experiencias):
        with st.container(border=True):
            col_h, col_del = st.columns([6, 1])
            col_h.markdown(f"**{exp.get('cargo', 'Nova experiência')} — {exp.get('empresa', '')}**")
            if col_del.button("🗑", key=f"del_exp_{exp['id']}"):
                experiencias.pop(i)
                cv["experiencias"] = experiencias
                salvar_curriculo_estruturado(cv)
                st.rerun()

            c1, c2, c3 = st.columns([2, 2, 1])
            exp["cargo"] = c1.text_input(
                "Cargo", value=exp.get("cargo", ""), key=f"cargo_{exp['id']}"
            )
            exp["empresa"] = c2.text_input(
                "Empresa", value=exp.get("empresa", ""), key=f"emp_{exp['id']}"
            )
            exp["periodo"] = c3.text_input(
                "Período",
                value=exp.get("periodo", ""),
                key=f"per_{exp['id']}",
                placeholder="Jan/2022 – hoje",
            )

            bullets = exp.get("bullets", [""])
            novos_bullets = []
            st.caption("Bullets (uma conquista por linha — use métricas quando possível)")
            for j, b in enumerate(bullets):
                cb1, cb2 = st.columns([8, 1])
                novo = cb1.text_input(
                    "•", value=b, key=f"bullet_{exp['id']}_{j}", label_visibility="collapsed"
                )
                novos_bullets.append(novo)
                if cb2.button("✕", key=f"del_b_{exp['id']}_{j}"):
                    bullets.pop(j)
                    exp["bullets"] = bullets
                    st.rerun()
            if st.button("+ Bullet", key=f"add_b_{exp['id']}", use_container_width=False):
                novos_bullets.append("")
            exp["bullets"] = [
                b for b in novos_bullets if b.strip() != "" or len(novos_bullets) == 1
            ]

    if st.button("➕ Adicionar experiência", use_container_width=True):
        experiencias.append(
            {"id": uuid.uuid4().hex[:8], "cargo": "", "empresa": "", "periodo": "", "bullets": [""]}
        )
        cv["experiencias"] = experiencias
        salvar_curriculo_estruturado(cv)
        st.rerun()
    cv["experiencias"] = experiencias

    st.divider()
    st.subheader("Educação")
    educacao = cv.get("educacao", [])
    for i, edu in enumerate(educacao):
        with st.container(border=True):
            col_h, col_del = st.columns([6, 1])
            col_h.markdown(f"**{edu.get('curso', '')} — {edu.get('instituicao', '')}**")
            if col_del.button("🗑", key=f"del_edu_{edu['id']}"):
                educacao.pop(i)
                cv["educacao"] = educacao
                salvar_curriculo_estruturado(cv)
                st.rerun()
            c1, c2, c3 = st.columns([3, 3, 1])
            edu["curso"] = c1.text_input(
                "Curso", value=edu.get("curso", ""), key=f"curso_{edu['id']}"
            )
            edu["instituicao"] = c2.text_input(
                "Instituição", value=edu.get("instituicao", ""), key=f"inst_{edu['id']}"
            )
            edu["periodo"] = c3.text_input(
                "Período",
                value=edu.get("periodo", ""),
                key=f"edup_{edu['id']}",
                placeholder="2018–2022",
            )
            edu["descricao"] = st.text_input(
                "Detalhe (opcional)",
                value=edu.get("descricao", ""),
                key=f"edud_{edu['id']}",
                placeholder="Ex: TCC em machine learning aplicado a finanças",
            )

    if st.button("➕ Adicionar educação", use_container_width=True):
        educacao.append(
            {
                "id": uuid.uuid4().hex[:8],
                "curso": "",
                "instituicao": "",
                "periodo": "",
                "descricao": "",
            }
        )
        cv["educacao"] = educacao
        salvar_curriculo_estruturado(cv)
        st.rerun()
    cv["educacao"] = educacao

    st.divider()
    col_hab, col_cert, col_idi = st.columns(3)

    with col_hab:
        st.subheader("Habilidades")
        habs_txt = st.text_area(
            "Uma por linha",
            value="\n".join(cv.get("habilidades", [])),
            height=120,
            label_visibility="collapsed",
            placeholder="Python\nSQL\nApache Spark\n...",
        )
        cv["habilidades"] = [h.strip() for h in habs_txt.splitlines() if h.strip()]

    with col_cert:
        st.subheader("Certificações")
        certs_txt = st.text_area(
            "Uma por linha",
            value="\n".join(cv.get("certificacoes", [])),
            height=120,
            label_visibility="collapsed",
            placeholder="AWS Certified Data Engineer\ndbt Fundamentals\n...",
        )
        cv["certificacoes"] = [c.strip() for c in certs_txt.splitlines() if c.strip()]

    with col_idi:
        st.subheader("Idiomas")
        idis_txt = st.text_area(
            "Uma por linha",
            value="\n".join(cv.get("idiomas", [])),
            height=120,
            label_visibility="collapsed",
            placeholder="Inglês — Avançado\nEspanhol — Básico\n...",
        )
        cv["idiomas"] = [i.strip() for i in idis_txt.splitlines() if i.strip()]

    return cv


def _tab_otimizar(cv: dict):
    from transformers.ats_agents import rodar_anya, rodar_nexus, ollama_disponivel

    if not ollama_disponivel():
        st.warning("Ollama não está rodando. Inicie com `ollama serve` no terminal.")
        return

    texto_cv = _cv_para_texto(cv)
    if not texto_cv.strip():
        st.info("Preencha o currículo na aba **✏️ Editor** antes de otimizar.")
        return

    st.markdown("**Selecione a vaga para otimizar o currículo:**")
    with db_connect() as con:
        vagas = con.execute("""
            SELECT fv.id, fv.titulo, de.nome, fv.descricao
            FROM fact_vaga fv
            JOIN dim_empresa de ON fv.id_empresa = de.id
            WHERE fv.ativa = true AND fv.descricao IS NOT NULL AND fv.descricao != ''
            ORDER BY fv.data_coleta DESC LIMIT 200
        """).fetchall()

    if not vagas:
        st.warning(
            "Nenhuma vaga com descrição disponível. Rode o pipeline ou cole uma descrição manualmente."
        )
        return

    opcoes = {f"{v[2]} — {v[1]}": (v[0], v[1], v[3]) for v in vagas}
    sel = st.selectbox("Vaga", list(opcoes.keys()), label_visibility="collapsed")
    id_vaga, titulo_vaga, descricao_vaga = opcoes[sel]

    key_nexus = f"builder_nexus_{id_vaga}"

    if st.button("✦ Otimizar currículo para esta vaga", type="primary", use_container_width=True):
        with st.spinner("NEXUS analisando e reescrevendo..."):
            anya = rodar_anya(texto_cv, descricao_vaga, titulo_vaga)
            nexus = rodar_nexus(texto_cv, descricao_vaga, titulo_vaga, anya)
            st.session_state[key_nexus] = nexus

    if st.session_state.get(key_nexus):
        nexus = st.session_state[key_nexus]
        st.divider()

        col_antes, col_depois = st.columns(2)
        col_antes.markdown("**Score ATS antes**")
        col_depois.markdown("**Score ATS depois (estimado)**")

        if nexus.get("titulo_sugerido"):
            st.markdown("**Título sugerido**")
            st.success(nexus["titulo_sugerido"])

        if nexus.get("resumo_otimizado"):
            st.markdown("**Resumo otimizado**")
            st.info(nexus["resumo_otimizado"])

        if nexus.get("bullets"):
            st.markdown("**Bullets reescritos**")
            for i, b in enumerate(nexus["bullets"], 1):
                with st.expander(f"Experiência {i}"):
                    ca, cd = st.columns(2)
                    ca.markdown(f"**Antes**\n\n{b['antes']}")
                    cd.markdown(f"**Depois**\n\n{b['depois']}")

        # aplicar otimizações e exportar
        cv_otimizado = json.loads(json.dumps(cv))  # deep copy
        if nexus.get("resumo_otimizado"):
            cv_otimizado["resumo"] = nexus["resumo_otimizado"]
        for b in nexus.get("bullets", []):
            antes = b["antes"].strip().lstrip("-•▸▶* ").strip()
            depois = b["depois"].strip()
            for exp in cv_otimizado.get("experiencias", []):
                bullets_novos = []
                for bul in exp.get("bullets", []):
                    if antes in bul or bul.lstrip("-•▸▶* ").strip() in antes[:80]:
                        bullets_novos.append(depois)
                    else:
                        bullets_novos.append(bul)
                exp["bullets"] = bullets_novos

        txt = _gerar_txt_exportacao(
            cv_otimizado,
            titulo_otimizado=nexus.get("titulo_sugerido", ""),
        )
        nome_arquivo = f"cv_{titulo_vaga[:30].lower().replace(' ', '_')}.txt"
        st.download_button(
            "📥 Baixar CV otimizado (.txt)",
            data=txt.encode("utf-8"),
            file_name=nome_arquivo,
            mime="text/plain",
            use_container_width=True,
            key=f"dl_builder_{id_vaga}",
        )
        st.caption(
            "O CV já vem com as otimizações aplicadas — cole no Google Docs e formate antes de enviar."
        )


def _tab_exportar(cv: dict):
    texto_cv = _cv_para_texto(cv)
    if not texto_cv.strip():
        st.info("Preencha o currículo na aba **✏️ Editor** para exportar.")
        return

    st.markdown("**Pré-visualização do currículo**")
    txt = _gerar_txt_exportacao(cv)
    st.text(txt[:3000] + ("\n[...]" if len(txt) > 3000 else ""))

    st.download_button(
        "📥 Baixar currículo base (.txt)",
        data=txt.encode("utf-8"),
        file_name="curriculo.txt",
        mime="text/plain",
        use_container_width=True,
    )
    st.caption("Use a aba **🤖 Otimizar** para gerar uma versão personalizada por vaga.")


def render():
    st.title("📄 Construtor de Currículo")
    st.caption(
        "Monte seu currículo base, otimize para cada vaga com IA e exporte pronto para enviar."
    )

    cv = carregar_curriculo_estruturado()
    if not cv:
        cv = json.loads(json.dumps(_CV_VAZIO))

    tab_editor, tab_otimizar, tab_exportar = st.tabs(
        ["✏️ Editor", "🤖 Otimizar por vaga", "📥 Exportar"]
    )

    with tab_editor:
        cv = _tab_editor(cv)
        st.divider()
        if st.button("💾 Salvar currículo", type="primary", use_container_width=True):
            salvar_curriculo_estruturado(cv)
            st.success("Currículo salvo!")

    with tab_otimizar:
        _tab_otimizar(cv)

    with tab_exportar:
        _tab_exportar(cv)
