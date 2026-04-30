import streamlit as st
from database.candidaturas import atualizar_candidatura, negar_vaga
from dashboard.components import (
    calcular_scores_vagas,
    carregar_vagas,
    render_score_breakdown,
    render_checklist_preparacao,
    render_stacks,
    render_remuneracao,
)
from utils import safe_str
from datetime import datetime, timedelta


def render():
    st.title("🎯 Fila de inscrição")
    st.caption("Vagas ordenadas por score — trabalhe uma por vez.")

    df = carregar_vagas()
    scores = calcular_scores_vagas()
    df["score"] = df["id"].map(scores).fillna(0).astype(int)

    # só vagas não inscritas e ativas
    ontem = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d")

    df_f = df[(df["candidatura_status"] == "nao_inscrito") & (df["ativa"] != False)].sort_values(
        ["data_coleta", "score"], ascending=[False, False]
    )

    if df_f.empty:
        st.success("🎉 Todas as vagas foram processadas!")
        return

    # métricas
    col1, col2, col3 = st.columns(3)
    col1.metric("Na fila", len(df_f))
    col2.metric("Score médio", f"{int(df_f['score'].mean())}%")
    col3.metric("Score máximo", f"{int(df_f['score'].max())}%")
    st.divider()

    col_luck, col_reset = st.columns([1, 1])
    if col_luck.button("🎲 Estou com sorte", use_container_width=True):
        import random

        st.session_state["fila_idx"] = random.randint(0, len(df_f) - 1)
        st.rerun()
    if col_reset.button("⏮ Voltar ao início", use_container_width=True):
        st.session_state["fila_idx"] = 0
        st.rerun()

    # vaga atual — sempre a primeira da fila
    idx = st.session_state.get("fila_idx", 0)
    if idx >= len(df_f):
        idx = 0
        st.session_state["fila_idx"] = 0

    vaga = df_f.iloc[idx]
    total = len(df_f)

    # progresso
    st.markdown(
        f"<div style='font-size:12px;color:#888'>Vaga {idx + 1} de {total}</div>",
        unsafe_allow_html=True,
    )
    st.progress((idx) / total if total > 0 else 0)
    st.write("")

    # card da vaga atual
    with st.container(border=True):
        col_titulo, col_score = st.columns([5, 1])
        col_titulo.markdown(f"### {vaga['titulo']}")
        score = int(vaga["score"])
        cor = "#1D9E75" if score >= 70 else "#BA7517" if score >= 40 else "#888"
        col_score.markdown(
            f"<div style='text-align:center;padding-top:8px'>"
            f"<span style='font-size:24px;font-weight:700;color:{cor}'>{score}%</span>"
            f"<div style='font-size:11px;color:#888'>fit</div></div>",
            unsafe_allow_html=True,
        )

        col_info1, col_info2, col_info3 = st.columns(3)
        col_info1.caption(f"🏢 {vaga['empresa']}")
        col_info2.caption(f"📊 {safe_str(vaga['nivel'], '—')}")
        col_info3.caption(f"💼 {safe_str(vaga['modalidade'], '—')}")

        st.divider()
        render_score_breakdown(int(vaga["id"]))
        render_checklist_preparacao(int(vaga["id"]))
        render_stacks(vaga["stacks"])
        st.divider()
        render_remuneracao(vaga)

    st.write("")

    # ações
    col_ver, col_inscrito, col_pular, col_negar = st.columns(4)

    col_ver.link_button("🔗 Abrir vaga", vaga["link"], use_container_width=True)

    if col_inscrito.button("✅ Inscrito", use_container_width=True, type="primary"):
        atualizar_candidatura(int(vaga["id"]), "inscrito", "inscrito", "")
        st.session_state["fila_idx"] = idx  # mantém posição, vaga some da fila
        st.toast(f"✅ Inscrito em {vaga['empresa']}! {len(df_f) - 1} vagas restantes.")
        st.rerun()

    if col_pular.button("⏭ Pular", use_container_width=True):
        st.session_state["fila_idx"] = (idx + 1) % total
        st.rerun()

    if col_negar.button("❌ Negar", use_container_width=True, type="secondary"):
        negar_vaga(int(vaga["id"]), "Negada pela fila de inscrição")
        st.session_state["fila_idx"] = idx
        st.toast("❌ Vaga negada.")
        st.rerun()

    st.divider()

    # lista das próximas
    st.subheader("Próximas na fila")
    proximas = df_f.iloc[idx + 1 : idx + 6]
    for _, prox in proximas.iterrows():
        sc = int(prox["score"])
        cor_p = "#1D9E75" if sc >= 70 else "#BA7517" if sc >= 40 else "#888"
        st.markdown(
            f"<div style='padding:6px 10px;margin:2px 0;border-radius:6px;border:1px solid #eee'>"
            f"<span style='font-size:13px'>{prox['titulo'][:50]}</span> "
            f"<span style='color:#888;font-size:11px'>— {prox['empresa']}</span> "
            f"<span style='color:{cor_p};font-weight:700;font-size:12px;float:right'>🎯{sc}%</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
