import streamlit as st
from datetime import datetime, timedelta
from database.schemas import TIMELINE_LABELS
from database.candidaturas import atualizar_candidatura
from dashboard.components import (
    carregar_vagas,
    calcular_scores_vagas,
    render_vaga_card,
)
from dashboard.ui_components import render_dialog_vaga, tempo_relativo, render_empty_state
from database.ats_score import listar_ats_scores


def _dialog_vaga(v):
    render_dialog_vaga(v, prefix="v")


def _limpar_filtros():
    for k in [
        "f_empresa",
        "f_nivel",
        "f_modalidade",
        "f_status_cand",
        "f_status_vaga",
        "f_sla_dias",
        "f_busca",
        "f_ordenar_por",
        "f_num_colunas",
        "f_modo_compacto",
        "filtro_rapido_vagas",
    ]:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()


def render():
    st.title("Vagas salvas")
    df = carregar_vagas()
    scores = calcular_scores_vagas()
    ats_scores = listar_ats_scores()
    df["score"] = df["id"].map(scores).fillna(0).astype(int)
    ontem = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d")

    # ── SIDEBAR — filtros estruturais ──────────────────────────
    st.sidebar.divider()
    st.sidebar.header("Filtros")

    empresas = ["Todas"] + sorted(df["empresa"].unique().tolist())
    empresa_sel = st.sidebar.selectbox("Empresa", empresas, key="f_empresa")

    niveis = ["Todos"] + sorted(df["nivel"].dropna().unique().tolist())
    nivel_sel = st.sidebar.selectbox("Nível", niveis, key="f_nivel")

    modalidades = ["Todas"] + sorted(df["modalidade"].dropna().unique().tolist())
    modalidade_sel = st.sidebar.selectbox("Modalidade", modalidades, key="f_modalidade")

    status_vaga = st.sidebar.radio(
        "Status da vaga", ["Ativas", "Encerradas", "Todas"], key="f_status_vaga"
    )

    sla_dias = st.sidebar.number_input(
        "Sem resposta há (dias)",
        min_value=0,
        max_value=30,
        value=0,
        step=1,
        key="f_sla_dias",
        help="Alerta vagas inscritas sem retorno há X dias",
    )

    st.sidebar.divider()
    if st.sidebar.button("🗑 Limpar filtros", use_container_width=True):
        _limpar_filtros()

    # ── BARRA DE CONTROLES (busca + view) ──────────────────────
    col_busca, col_ord, col_agrup, col_cols, col_modo = st.columns([3, 2, 2, 1.5, 1.5])
    busca = col_busca.text_input(
        "🔍 Buscar no título",
        key="f_busca",
        label_visibility="collapsed",
        placeholder="Buscar no título...",
    )
    ordenar_por = col_ord.selectbox(
        "Ordenar",
        ["Score ↓", "Score ↑", "Data ↓", "Data ↑", "Empresa A-Z"],
        key="f_ordenar_por",
        label_visibility="collapsed",
    )
    agrupar_por = col_agrup.selectbox(
        "Agrupar", ["Nenhum", "Empresa", "Fase"], key="f_agrupar_por", label_visibility="collapsed"
    )
    num_colunas = col_cols.select_slider(
        "Colunas",
        options=[2, 3, 4, 5, 6, 8],
        value=4,
        key="f_num_colunas",
        label_visibility="collapsed",
    )
    modo_compacto = col_modo.checkbox("Compacto", key="f_modo_compacto")

    # ── FILTRO RÁPIDO POR STATUS ───────────────────────────────
    if "filtro_rapido_vagas" not in st.session_state:
        st.session_state["filtro_rapido_vagas"] = None

    df_base = df.copy()
    if empresa_sel != "Todas":
        df_base = df_base[df_base["empresa"] == empresa_sel]
    if nivel_sel != "Todos":
        df_base = df_base[df_base["nivel"] == nivel_sel]
    if modalidade_sel != "Todas":
        df_base = df_base[df_base["modalidade"] == modalidade_sel]
    if status_vaga == "Ativas":
        df_base = df_base[df_base["ativa"] == True]
    elif status_vaga == "Encerradas":
        df_base = df_base[df_base["ativa"] == False]
    if busca:
        df_base = df_base[df_base["titulo"].str.contains(busca, case=False, na=False)]
    if sla_dias > 0:
        limite = (datetime.now() - timedelta(days=sla_dias)).strftime("%Y-%m-%d")
        df_base = df_base[
            (df_base["candidatura_status"] == "inscrito")
            & (df_base["candidatura_data"].astype(str) <= limite)
        ]

    n_total = len(df_base)
    n_nao_inscrito = df_base[df_base["candidatura_status"] == "nao_inscrito"].shape[0]
    n_inscrito = df_base[df_base["candidatura_status"] == "inscrito"].shape[0]
    n_processo = df_base[
        df_base["candidatura_status"].isin(["chamado", "recrutador", "fase_1", "fase_2", "fase_3"])
    ].shape[0]

    filtro_rapido = st.session_state["filtro_rapido_vagas"]
    col1, col2, col3, col4 = st.columns(4)
    if col1.button(
        f"**Todas**  \n{n_total}",
        use_container_width=True,
        type="primary" if filtro_rapido is None else "secondary",
    ):
        st.session_state["filtro_rapido_vagas"] = None
        st.rerun()
    if col2.button(
        f"**Não inscritas**  \n{n_nao_inscrito}",
        use_container_width=True,
        type="primary" if filtro_rapido == "nao_inscrito" else "secondary",
    ):
        st.session_state["filtro_rapido_vagas"] = "nao_inscrito"
        st.rerun()
    if col3.button(
        f"**Inscritas**  \n{n_inscrito}",
        use_container_width=True,
        type="primary" if filtro_rapido == "inscrito" else "secondary",
    ):
        st.session_state["filtro_rapido_vagas"] = "inscrito"
        st.rerun()
    if col4.button(
        f"**Em processo**  \n{n_processo}",
        use_container_width=True,
        type="primary" if filtro_rapido == "em_processo" else "secondary",
    ):
        st.session_state["filtro_rapido_vagas"] = "em_processo"
        st.rerun()

    # aplica filtro rápido
    df_f = df_base.copy()
    filtro_rapido = st.session_state["filtro_rapido_vagas"]
    if filtro_rapido == "nao_inscrito":
        df_f = df_f[df_f["candidatura_status"] == "nao_inscrito"]
    elif filtro_rapido == "inscrito":
        df_f = df_f[df_f["candidatura_status"] == "inscrito"]
    elif filtro_rapido == "em_processo":
        df_f = df_f[
            df_f["candidatura_status"].isin(["chamado", "recrutador", "fase_1", "fase_2", "fase_3"])
        ]

    st.divider()

    # banner vagas novas
    total_novas = df_f[df_f["data_coleta"].astype(str) >= ontem].shape[0]
    if total_novas > 0:
        st.success(f"🆕 {total_novas} vaga(s) nova(s) nas últimas 24h")

    # ── ESTADO VAZIO ───────────────────────────────────────────
    if df_f.empty:
        filtros_ativos = any(
            [
                empresa_sel != "Todas",
                nivel_sel != "Todos",
                modalidade_sel != "Todas",
                status_vaga != "Ativas",
                busca,
                sla_dias > 0,
                filtro_rapido is not None,
            ]
        )
        if filtros_ativos:
            render_empty_state(
                "Nenhuma vaga encontrada",
                "Nenhuma vaga bate com os filtros aplicados.",
                acao_label="Limpar filtros",
                acao_pagina=None,
            )
            if st.button("Limpar filtros", type="primary"):
                _limpar_filtros()
        else:
            render_empty_state(
                "Nenhuma vaga ainda",
                "Execute o pipeline para coletar vagas das empresas cadastradas.",
                acao_label="Ir para Pipeline",
                acao_pagina="Pipeline",
            )
        return

    # ── ORDENAÇÃO ──────────────────────────────────────────────
    if ordenar_por == "Score ↓":
        df_f = df_f.sort_values("score", ascending=False)
    elif ordenar_por == "Score ↑":
        df_f = df_f.sort_values("score", ascending=True)
    elif ordenar_por == "Data ↓":
        df_f = df_f.sort_values("data_coleta", ascending=False)
    elif ordenar_por == "Data ↑":
        df_f = df_f.sort_values("data_coleta", ascending=True)
    elif ordenar_por == "Empresa A-Z":
        df_f = df_f.sort_values("empresa", ascending=True)

    # ── MODO COMPACTO ──────────────────────────────────────────
    if modo_compacto:
        for _, vaga in df_f.iterrows():
            status_cand_val = vaga.get("candidatura_status") or "nao_inscrito"
            label_status = TIMELINE_LABELS.get(status_cand_val, "Não inscrito")
            score = int(scores.get(vaga["id"], 0))
            ats = ats_scores.get(int(vaga["id"]), 0)
            is_nova = str(vaga["data_coleta"])[:10] >= ontem
            urgente = vaga.get("urgente") is True
            cor_left = "#1D9E75" if is_nova else "#D85A30" if urgente else "#e0e0e0"
            tempo = tempo_relativo(vaga["data_coleta"])
            tags = ""
            if urgente:
                tags += " 🔥"
            if is_nova:
                tags += " 🆕"
            st.markdown(
                f"<div style='padding:8px 12px;margin:2px 0;border-radius:6px;"
                f"border:1px solid #ddd;border-left:3px solid {cor_left};background:white;'>"
                f"<span style='font-weight:600'>{tags} {vaga['titulo'][:55]}</span> "
                f"<span style='color:#888;font-size:12px'>— {vaga['empresa']} · {vaga['nivel']} · {vaga['modalidade']}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
            c1.caption(f"📅 {tempo}")
            c2.markdown(
                f"<div style='font-size:11px;font-weight:700;color:#1A5FAD'>🎯 {score}%</div>"
                f"<div style='background:#f0f0f0;border-radius:3px;height:3px'>"
                f"<div style='background:#1A5FAD;width:{score}%;height:3px;border-radius:3px'></div></div>"
                if score > 0
                else "",
                unsafe_allow_html=True,
            )
            c3.markdown(
                f"<div style='font-size:11px;font-weight:700;color:#7F77DD'>🤖 {ats}%</div>"
                f"<div style='background:#f0f0f0;border-radius:3px;height:3px'>"
                f"<div style='background:#7F77DD;width:{ats}%;height:3px;border-radius:3px'></div></div>"
                if ats > 0
                else "",
                unsafe_allow_html=True,
            )
            c4.link_button("🔗", vaga["link"])
            if status_cand_val == "nao_inscrito":
                if c5.button("✅", key=f"inscrito_{vaga['id']}", help="Marcar como inscrito"):
                    atualizar_candidatura(int(vaga["id"]), "inscrito", "inscrito", "")
                    st.rerun()
            else:
                c5.markdown(
                    f"<span style='color:#1D9E75;font-size:11px'>{label_status}</span>",
                    unsafe_allow_html=True,
                )
        return

    # ── CARDS ──────────────────────────────────────────────────
    def _render_grupo(df_grupo, key_prefix="v"):
        vagas_list = list(df_grupo.iterrows())
        for i in range(0, len(vagas_list), num_colunas):
            bloco = vagas_list[i : i + num_colunas]
            cols = st.columns(num_colunas)
            for j in range(num_colunas):
                with cols[j]:
                    if j >= len(bloco):
                        st.empty()
                        continue
                    _, vaga = bloco[j]
                    score = int(scores.get(vaga["id"], 0))
                    is_nova = str(vaga["data_coleta"])[:10] >= ontem
                    ats = ats_scores.get(int(vaga["id"]), 0)
                    render_vaga_card(vaga, score, is_nova, key_prefix=key_prefix, ats_score=ats)

    if agrupar_por == "Empresa":
        for empresa in sorted(df_f["empresa"].unique()):
            df_emp = df_f[df_f["empresa"] == empresa]
            st.markdown(f"#### 🏢 {empresa} ({len(df_emp)})")
            _render_grupo(df_emp, key_prefix=f"v_emp_{empresa[:8]}")
            st.divider()
    elif agrupar_por == "Fase":
        ordem_fases = [
            "nao_inscrito",
            "inscrito",
            "chamado",
            "recrutador",
            "fase_1",
            "fase_2",
            "fase_3",
            "aprovado",
            "reprovado",
        ]
        for fase in ordem_fases:
            df_fase = df_f[df_f["candidatura_status"] == fase]
            if df_fase.empty:
                continue
            label = TIMELINE_LABELS.get(fase, fase)
            st.markdown(f"#### {label} ({len(df_fase)})")
            _render_grupo(df_fase, key_prefix=f"v_fase_{fase}")
            st.divider()
    else:
        _render_grupo(df_f)

    # ── DIALOGS ────────────────────────────────────────────────
    vaga_id_atual = st.session_state.get("dialog_v_atual")
    if vaga_id_atual:
        rows = df_f[df_f["id"] == vaga_id_atual]
        if not rows.empty:
            vaga = rows.iloc[0]
            dialog_fn = st.dialog(vaga["titulo"][:60], width="large")(_dialog_vaga)
            dialog_fn(vaga)
