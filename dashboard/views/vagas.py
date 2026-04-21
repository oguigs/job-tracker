import streamlit as st
from datetime import datetime, timedelta
from database.schemas import TIMELINE, TIMELINE_LABELS
from database.candidaturas import atualizar_candidatura, negar_vaga
from dashboard.components import (
    carregar_vagas, get_favicon, render_stacks,
    render_score_breakdown, render_diario, calcular_scores_vagas,
    render_preparacao_entrevista, render_remuneracao, render_checklist_preparacao,
    render_vaga_card
)

def render():
    st.title("Vagas salvas")
    df = carregar_vagas()
    scores = calcular_scores_vagas()
    df["score"] = df["id"].map(scores).fillna(0).astype(int)
    df = df.sort_values("score", ascending=False)

    # ── SIDEBAR ────────────────────────────────────────────────
    st.sidebar.divider()
    st.sidebar.subheader("⚡ Ação rápida")
    so_novas = st.sidebar.checkbox("Só vagas novas (24h)")
    so_nao_inscrito = st.sidebar.checkbox("Só não inscritas")
    modo_compacto = st.sidebar.checkbox("Modo compacto")
    num_colunas = st.sidebar.select_slider("Colunas", options=[2, 3, 4, 5, 6 ,8, 10], value=4)
    ordenar_por = st.sidebar.selectbox("Ordenar por", 
        ["Score ↓", "Score ↑", "Data ↓", "Data ↑", "Empresa A-Z"])
    sla_dias = st.sidebar.number_input("⏰ Alertar sem resposta (dias)", min_value=0, max_value=30, value=0, step=1)
    st.sidebar.divider()
    st.sidebar.header("Filtros")
    empresas = ["Todas"] + sorted(df["empresa"].unique().tolist())
    empresa_sel = st.sidebar.selectbox("Empresa", empresas)
    niveis = ["Todos"] + sorted(df["nivel"].dropna().unique().tolist())
    nivel_sel = st.sidebar.selectbox("Nível", niveis)
    modalidades = ["Todas"] + sorted(df["modalidade"].dropna().unique().tolist())
    modalidade_sel = st.sidebar.selectbox("Modalidade", modalidades)
    status_cand = ["Todos"] + list(TIMELINE_LABELS.values())
    status_cand_sel = st.sidebar.selectbox("Status candidatura", status_cand)
    status_vaga = st.sidebar.radio("Status da vaga", ["Ativas", "Encerradas", "Todas"])
    busca = st.sidebar.text_input("Buscar no título")

    # ── FILTROS ────────────────────────────────────────────────
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

    # ── MÉTRICAS ───────────────────────────────────────────────
    em_processo = df_f[df_f["candidatura_status"].isin(["chamado","recrutador","fase_1","fase_2","fase_3"])].shape[0]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", len(df_f))
    col2.metric("Não inscritas", df_f[df_f["candidatura_status"] == "nao_inscrito"].shape[0])
    col3.metric("Inscritas", df_f[df_f["candidatura_status"] == "inscrito"].shape[0])
    col4.metric("Em processo", em_processo)
    st.divider()

    total_novas = df_f[df_f["data_coleta"].astype(str) >= ontem].shape[0]
    if total_novas > 0:
        st.success(f"🆕 {total_novas} vaga(s) nova(s) nas últimas 24h!")

    # ── MODO COMPACTO ──────────────────────────────────────────
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
                    atualizar_candidatura(vaga["id"], "inscrito", "inscrito", "")
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

    # ── MODO CARDS (4 por linha) ───────────────────────────────
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
    for _, vaga in df_f.iterrows():
        if not st.session_state.get(f"dialog_v_{vaga['id']}"):
            continue

        @st.dialog(vaga['titulo'][:60], width="large")
        def mostrar_detalhe(v=vaga):
            status_cand_val = v.get("candidatura_status") or "nao_inscrito"
            label_status = TIMELINE_LABELS.get(status_cand_val, "Não inscrito")
            data_fmt = str(v['data_coleta'])[:10] if str(v['data_coleta']) not in ['NaT','None','nan'] else 'N/A'

            col_info, col_link = st.columns([5, 1])
            col_info.caption(f"📅 {data_fmt} · {v['empresa']} · {label_status}")
            col_link.link_button("🔗 Ver vaga", v["link"], use_container_width=True)

            render_score_breakdown(v["id"])
            render_checklist_preparacao(v["id"])
            render_stacks(v["stacks"])
            st.divider()

            fases = ["nao_inscrito","inscrito","chamado","recrutador","fase_1","fase_2","fase_3"]
            cols_f = st.columns(len(fases))
            for idx, fase in enumerate(fases):
                ativo = fase == status_cand_val
                cols_f[idx].markdown(
                    f"<div style='text-align:center;padding:4px;border-radius:6px;"
                    f"background:{'#1D9E75' if ativo else '#f0f0f0'};"
                    f"color:{'white' if ativo else '#888'};font-size:11px'>"
                    f"{TIMELINE_LABELS[fase]}</div>", unsafe_allow_html=True)
            st.write("")

            with st.form(key=f"form_d_{v['id']}"):
                col_s, col_o = st.columns([2, 3])
                novo_status = col_s.selectbox("Status", options=TIMELINE,
                    format_func=lambda x: TIMELINE_LABELS[x],
                    index=TIMELINE.index(status_cand_val) if status_cand_val in TIMELINE else 0,
                    key=f"sel_d_{v['id']}")
                observacao = col_o.text_input("Observação",
                    value="" if str(v.get("candidatura_observacao") or "nan") == "nan" else str(v.get("candidatura_observacao") or ""),
                    key=f"obs_d_{v['id']}")
                col_s2, col_n2 = st.columns(2)
                with col_s2:
                    if st.form_submit_button("Salvar", use_container_width=True):
                        atualizar_candidatura(v["id"], novo_status, novo_status, observacao)
                        st.session_state[f"dialog_{v['id']}"] = False
                        st.rerun()
                with col_n2:
                    if st.form_submit_button("Negar", use_container_width=True, type="secondary"):
                        negar_vaga(v["id"], observacao or f"Negada em: {status_cand_val}")
                        st.session_state[f"dialog_{v['id']}"] = False
                        st.rerun()

            render_remuneracao(v)
            render_diario(v["id"])

        mostrar_detalhe()
