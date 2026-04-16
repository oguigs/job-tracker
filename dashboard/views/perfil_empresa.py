import streamlit as st
from database.schemas import TIMELINE, TIMELINE_LABELS
from database.candidaturas import atualizar_candidatura, negar_vaga
from dashboard.components import (
    carregar_perfil_empresa, extrair_stacks_flat,
    grafico_stacks, get_favicon, render_stacks
)

def render(empresa_perfil: str):
    empresa_df, vagas_df, logs_df, enderecos = carregar_perfil_empresa(empresa_perfil)

    if empresa_df.empty:
        st.error(f"Empresa '{empresa_perfil}' não encontrada.")
        return

    emp = empresa_df.iloc[0]
    favicon = get_favicon(emp["nome"], emp.get("favicon_url") or "")

    col_logo, col_titulo = st.columns([1, 6])
    if favicon:
        col_logo.image(favicon, width=64)
    col_titulo.title(emp["nome"])
    col_titulo.caption(f"{emp['ramo'] or '—'} · {emp['cidade'] or '—'}/{emp['estado'] or '—'} · Cadastrada em {emp['data_cadastro']}")

    cols_links = st.columns(3)
    url_v = str(emp.get("url_vagas") or "")
    if url_v and url_v not in ["None","nan"]:
        cols_links[0].link_button("Portal de vagas", url_v, use_container_width=True)
    url_of = str(emp.get("url_site_oficial") or "")
    if url_of and url_of not in ["None","nan"]:
        cols_links[1].link_button("Site oficial", url_of, use_container_width=True)
    if enderecos:
        st.write("**Polos:**")
        for cidade, bairro in enderecos:
            st.write(f"- {cidade} / {bairro or '—'}")

    st.divider()
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Total de vagas", len(vagas_df))
    col_m2.metric("Vagas ativas", vagas_df[vagas_df["ativa"] == True].shape[0])
    col_m3.metric("Inscritas", vagas_df[vagas_df["candidatura_status"] == "inscrito"].shape[0])

    st.divider()
    st.subheader("Stacks mais pedidas")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        fig = grafico_stacks(extrair_stacks_flat(vagas_df, "linguagens"), "Linguagens", "#1D9E75")
        if fig: st.plotly_chart(fig, use_container_width=True)
    with col_b:
        fig = grafico_stacks(extrair_stacks_flat(vagas_df, "cloud"), "Cloud", "#378ADD")
        if fig: st.plotly_chart(fig, use_container_width=True)
    with col_c:
        fig = grafico_stacks(extrair_stacks_flat(vagas_df, "processamento"), "Processamento", "#D85A30")
        if fig: st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Vagas")
    for _, vaga in vagas_df.iterrows():
        status_icon = "🟢" if str(vaga["ativa"]) == "True" else "🔴"
        status_cand_val = vaga.get("candidatura_status") or "nao_inscrito"
        label_status = TIMELINE_LABELS.get(status_cand_val, "Não inscrito")
        with st.expander(f"{status_icon} {vaga['titulo']} | {label_status}"):
            col1, col2, col3 = st.columns(3)
            col1.write(f"**Nível:** {vaga['nivel']}")
            col2.write(f"**Modalidade:** {vaga['modalidade']}")
            col3.write(f"**Coletada em:** {str(vaga['data_coleta'])[:10]}")
            render_stacks(vaga["stacks"])
            st.link_button("Ver vaga", vaga["link"])

    st.divider()
    st.subheader("Histórico do pipeline")
    if not logs_df.empty:
        st.dataframe(logs_df, use_container_width=True)
    else:
        st.caption("Nenhuma execução registrada ainda.")