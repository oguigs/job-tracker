import streamlit as st
from datetime import datetime, timedelta
from database.schemas import TIMELINE, TIMELINE_LABELS
from database.candidaturas import atualizar_candidatura, negar_vaga
from dashboard.components import (
    carregar_vagas, render_stacks,
    render_score_breakdown, render_diario, calcular_scores_vagas,
    render_remuneracao, render_checklist_preparacao,
    render_vaga_card
)
from dashboard.ui_components import render_dialog_vaga


def _dialog_vaga(v):
    render_dialog_vaga(v, prefix="v")


def render():
    st.title("Vagas salvas")
    df = carregar_vagas()
    scores = calcular_scores_vagas()
    df["score"] = df["id"].map(scores).fillna(0).astype(int)
    df = df.sort_values("score", ascending=False)

# ── SIDEBAR ────────────────────────────────────────────────
    st.sidebar.divider()
    st.sidebar.subheader("⚡ Ação rápida")
    so_novas = st.sidebar.checkbox("Só vagas novas (24h)", key="f_so_novas")
    so_nao_inscrito = st.sidebar.checkbox("Só não inscritas", key="f_so_nao_inscrito")
    modo_compacto = st.sidebar.checkbox("Modo compacto", key="f_modo_compacto")
    num_colunas = st.sidebar.select_slider("Colunas", options=[2, 3, 4, 5, 6, 8], value=4, key="f_num_colunas")
    ordenar_por = st.sidebar.selectbox("Ordenar por",
        ["Score ↓", "Score ↑", "Data ↓", "Data ↑", "Empresa A-Z"], key="f_ordenar_por")
    sla_dias = st.sidebar.number_input("⏰ Alertar sem resposta (dias)", min_value=0, max_value=30, value=0, step=1, key="f_sla_dias")
    st.sidebar.divider()
    st.sidebar.header("Filtros")
    empresas = ["Todas"] + sorted(df["empresa"].unique().tolist())
    empresa_sel = st.sidebar.selectbox("Empresa", empresas, key="f_empresa")
    niveis = ["Todos"] + sorted(df["nivel"].dropna().unique().tolist())
    nivel_sel = st.sidebar.selectbox("Nível", niveis, key="f_nivel")
    modalidades = ["Todas"] + sorted(df["modalidade"].dropna().unique().tolist())
    modalidade_sel = st.sidebar.selectbox("Modalidade", modalidades, key="f_modalidade")
    status_cand = ["Todos"] + list(TIMELINE_LABELS.values())
    status_cand_sel = st.sidebar.selectbox("Status candidatura", status_cand, key="f_status_cand")
    status_vaga = st.sidebar.radio("Status da vaga", ["Ativas", "Encerradas", "Todas"], key="f_status_vaga")
    busca = st.sidebar.text_input("Buscar no título", key="f_busca")

    df_f = df.copy()
    ontem = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d")

    if sla_dias > 0:
        limite = (datetime.now() - timedelta(days=sla_dias)).strftime("%Y-%m-%d")
        df_f = df_f[(df_f["candidatura_status"] == "inscrito") & (df_f["candidatura_data"].astype(str) <= limite)]
    if empresa_sel != "Todas":
        df_f = df_f[df_f["empresa"] == empresa_sel]
    if nivel_sel != "Todos":
        df_f = df_f[df_f["nivel"] == nivel_sel]
    if modalidade_sel != "Todas":
        df_f = df_f[df_f["modalidade"] == modalidade_sel]
    if status_vaga == "Ativas":
        df_f = df_f[df_f["ativa"] == True]
    elif status_vaga == "Encerradas":
        df_f = df_f[df_f["ativa"] == False]
    if status_cand_sel != "Todos":
        chave = next((k for k, v in TIMELINE_LABELS.items() if v == status_cand_sel), None)
        if chave:
            df_f = df_f[df_f["candidatura_status"] == chave]
    if busca:
        df_f = df_f[df_f["titulo"].str.contains(busca, case=False, na=False)]
    if so_novas:
        df_f = df_f[df_f["data_coleta"].astype(str) >= ontem]
    if so_nao_inscrito:
        df_f = df_f[df_f["candidatura_status"] == "nao_inscrito"]

    em_processo = df_f[df_f["candidatura_status"].isin(["chamado","recrutador","fase_1","fase_2","fase_3"])].shape[0]

    if "filtro_rapido_vagas" not in st.session_state:
        st.session_state["filtro_rapido_vagas"] = None

    filtro_rapido = st.session_state.get("filtro_rapido_vagas")
    col1, col2, col3, col4 = st.columns(4)
    if col1.button(f"**Total**\n\n{len(df_f)}", use_container_width=True,
                   type="primary" if filtro_rapido is None else "secondary"):
        st.session_state["filtro_rapido_vagas"] = None
        st.rerun()
    if col2.button(f"**Não inscritas**\n\n{df_f[df_f['candidatura_status'] == 'nao_inscrito'].shape[0]}",
                   use_container_width=True,
                   type="primary" if filtro_rapido == "nao_inscrito" else "secondary"):
        st.session_state["filtro_rapido_vagas"] = "nao_inscrito"
        st.rerun()
    if col3.button(f"**Inscritas**\n\n{df_f[df_f['candidatura_status'] == 'inscrito'].shape[0]}",
                   use_container_width=True,
                   type="primary" if filtro_rapido == "inscrito" else "secondary"):
        st.session_state["filtro_rapido_vagas"] = "inscrito"
        st.rerun()
    if col4.button(f"**Em processo**\n\n{em_processo}", use_container_width=True,
                   type="primary" if filtro_rapido == "em_processo" else "secondary"):
        st.session_state["filtro_rapido_vagas"] = "em_processo"
        st.rerun()

    filtro_rapido = st.session_state.get("filtro_rapido_vagas")
    if filtro_rapido == "nao_inscrito":
        df_f = df_f[df_f["candidatura_status"] == "nao_inscrito"]
    elif filtro_rapido == "inscrito":
        df_f = df_f[df_f["candidatura_status"] == "inscrito"]
    elif filtro_rapido == "em_processo":
        df_f = df_f[df_f["candidatura_status"].isin(["chamado","recrutador","fase_1","fase_2","fase_3"])]
    st.divider()

    total_novas = df_f[df_f["data_coleta"].astype(str) >= ontem].shape[0]
    if total_novas > 0:
        st.success(f"🆕 {total_novas} vaga(s) nova(s) nas últimas 24h!")

    if modo_compacto:
        for _, vaga in df_f.iterrows():
            status_icon = "🟢" if str(vaga["ativa"]) == "True" else "🔴"
            status_cand_val = vaga.get("candidatura_status") or "nao_inscrito"
            label_status = TIMELINE_LABELS.get(status_cand_val, "Não inscrito")
            score = int(scores.get(vaga["id"], 0))
            is_nova = str(vaga["data_coleta"])[:10] >= ontem
            nova_label = "🆕 " if is_nova else ""
            cor_bg = "#E8F5F0" if is_nova else "white"
            st.markdown(
                f"<div style='padding:8px 12px;margin:2px 0;border-radius:6px;"
                f"border:1px solid #ddd;background:{cor_bg};'>"
                f"<span style='font-weight:600'>{nova_label}{status_icon} {vaga['titulo'][:55]}</span> "
                f"<span style='color:#888;font-size:12px'>— {vaga['empresa']} | {vaga['nivel']} | {vaga['modalidade']}</span>"
                f"</div>", unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns([4, 1, 1, 1])
            c1.caption(str(vaga['data_coleta'])[:10])
            c2.markdown(f"🎯 **{score}%**" if score > 0 else "")
            c3.link_button("🔗 Ver", vaga["link"])
            if status_cand_val == "nao_inscrito":
                if c4.button("✅", key=f"inscrito_{vaga['id']}", help="Marcar como inscrito"):
                    atualizar_candidatura(int(vaga["id"]), "inscrito", "inscrito", "")
                    st.rerun()
            else:
                c4.markdown(f"<span style='color:#1D9E75;font-size:11px'>{label_status}</span>", unsafe_allow_html=True)
        return

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

    vagas_list = list(df_f.iterrows())
    for i in range(0, len(vagas_list), num_colunas):
        grupo = vagas_list[i:i+num_colunas]
        cols = st.columns(num_colunas)
        for j in range(num_colunas):
            with cols[j]:
                if j >= len(grupo):
                    st.empty()
                    continue
                _, vaga = grupo[j]
                score = int(scores.get(vaga["id"], 0))
                is_nova = str(vaga["data_coleta"])[:10] >= ontem
                render_vaga_card(vaga, score, is_nova, key_prefix="v")

# ── DIALOGS ────────────────────────────────────────────────
    vaga_id_atual = st.session_state.get("dialog_v_atual")
    if vaga_id_atual:
        rows = df_f[df_f["id"] == vaga_id_atual]
        if not rows.empty:
            vaga = rows.iloc[0]
            dialog_fn = st.dialog(vaga['titulo'][:60], width="large")(_dialog_vaga)
            dialog_fn(vaga)