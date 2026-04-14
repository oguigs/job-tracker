import os
import json
import streamlit as st
import pandas as pd
import plotly.express as px
from dashboard.stack_config import get_stack_icon_url, get_stack_roadmap_url, get_categoria_cor
import duckdb

DB_PATH = "data/curated/jobs.duckdb"

def conectar():
    return duckdb.connect(DB_PATH, read_only=True)

def conectar_rw():
    return duckdb.connect(DB_PATH, read_only=False)

def get_favicon(nome: str, favicon_url: str = "") -> str:
    nome_arquivo = nome.lower().replace(" ", "_").replace("&", "e")
    caminho_local = f"dashboard/static/favicons/{nome_arquivo}.png"
    if os.path.exists(caminho_local):
        return caminho_local
    return favicon_url or ""

def render_stacks(stacks_json):
    try:
        stacks = json.loads(stacks_json) if isinstance(stacks_json, str) else stacks_json
        if not stacks:
            return
        st.write("**Stacks:**")
        for categoria, termos in stacks.items():
            if not termos:
                continue
            cor = get_categoria_cor(categoria)
            st.markdown(
                f"<span style='font-size:11px; font-weight:600; color:{cor['text']}; "
                f"text-transform:uppercase; letter-spacing:0.5px;'>{categoria}</span>",
                unsafe_allow_html=True
            )
            badges_html = "<div style='display:flex; flex-wrap:wrap; gap:4px; margin-bottom:8px;'>"
            for termo in termos:
                icon_url = get_stack_icon_url(termo)
                roadmap_url = get_stack_roadmap_url(termo)
                icon_tag = (
                    f'<img src="{icon_url}" width="14" '
                    f'style="vertical-align:middle; margin-right:4px;">'
                    if icon_url else ""
                )
                estilo_base = (
                    f"display:inline-flex; align-items:center; padding:3px 10px; "
                    f"border-radius:12px; font-size:12px; font-weight:500; "
                    f"background:{cor['bg']}; color:{cor['text']}; "
                    f"border:1px solid {cor['border']}; text-decoration:none;"
                )
                if roadmap_url:
                    badges_html += (
                        f'<a href="{roadmap_url}" target="_blank" '
                        f'style="{estilo_base}">{icon_tag}{termo}</a>'
                    )
                else:
                    badges_html += (
                        f'<span style="{estilo_base}">{icon_tag}{termo}</span>'
                    )
            badges_html += "</div>"
            st.markdown(badges_html, unsafe_allow_html=True)
    except:
        pass

def extrair_stacks_flat(df, categoria):
    todas = []
    for stacks_json in df["stacks"].dropna():
        try:
            stacks = json.loads(stacks_json) if isinstance(stacks_json, str) else stacks_json
            todas.extend(stacks.get(categoria, []))
        except:
            pass
    return pd.Series(todas).value_counts().reset_index().rename(
        columns={"index": "stack", 0: "count", "count": "count"}
    )

def grafico_stacks(df_counts, titulo: str, cor: str):
    if df_counts.empty:
        return None
    df_counts.columns = ["stack", "count"]
    fig = px.bar(
        df_counts, x="count", y="stack", orientation="h",
        title=titulo, color_discrete_sequence=[cor], template="plotly_white"
    )
    fig.update_layout(
        height=300, margin=dict(l=0, r=0, t=40, b=0),
        yaxis=dict(autorange="reversed", title=""),
        xaxis=dict(title="Vagas"), showlegend=False, title_font_size=14
    )
    fig.update_traces(hovertemplate="<b>%{y}</b><br>%{x} vagas<extra></extra>")
    return fig

def carregar_vagas():
    con = conectar()
    df = con.execute("""
        SELECT v.id, v.titulo, v.nivel, v.modalidade, v.stacks,
               v.link, v.fonte, v.data_coleta, v.ativa, v.data_encerramento,
               v.candidatura_status, v.candidatura_fase, v.candidatura_observacao,
               v.urgente,
               e.nome AS empresa, e.ramo, e.cidade, e.url_linkedin, e.favicon_url
        FROM fact_vaga v
        JOIN dim_empresa e ON v.id_empresa = e.id
        WHERE v.negada = false OR v.negada IS NULL
        ORDER BY v.data_coleta DESC
    """).df()
    con.close()
    return df

def carregar_empresas():
    con = conectar()
    df = con.execute("""
        SELECT id, nome, ramo, cidade, estado, url_gupy,
               url_linkedin, url_site_vagas, url_site_oficial,
               ativa, data_cadastro, favicon_url
        FROM dim_empresa ORDER BY nome
    """).df()
    con.close()
    return df

def carregar_logs():
    con = conectar()
    df = con.execute("""
        SELECT empresa, vagas_encontradas, vagas_novas, status, data_execucao
        FROM log_coleta ORDER BY data_execucao DESC LIMIT 10
    """).df()
    con.close()
    return df

def carregar_perfil_empresa(nome: str):
    con = conectar()
    empresa = con.execute("""
        SELECT id, nome, ramo, cidade, estado, url_gupy,
               url_linkedin, url_site_vagas, url_site_oficial,
               favicon_url, data_cadastro
        FROM dim_empresa WHERE nome = ?
    """, [nome]).df()
    vagas = con.execute("""
        SELECT id, titulo, nivel, modalidade, stacks, link,
               data_coleta, ativa, candidatura_status
        FROM fact_vaga
        WHERE id_empresa = (SELECT id FROM dim_empresa WHERE nome = ?)
        AND (negada = false OR negada IS NULL)
        ORDER BY data_coleta DESC
    """, [nome]).df()
    logs = con.execute("""
        SELECT vagas_encontradas, vagas_novas, status, data_execucao
        FROM log_coleta WHERE empresa = ?
        ORDER BY data_execucao DESC LIMIT 5
    """, [nome]).df()
    enderecos = con.execute("""
        SELECT cidade, bairro FROM dim_empresa_endereco
        WHERE id_empresa = (SELECT id FROM dim_empresa WHERE nome = ?)
    """, [nome]).fetchall()
    con.close()
    return empresa, vagas, logs, enderecos

def calcular_scores_vagas():
    """Retorna dict {id_vaga: score} para todas as vagas ativas."""
    from database.candidato import carregar_perfil
    from database.score import calcular_scores_todos

    df_perfil = carregar_perfil()
    if df_perfil.empty:
        return {}

    id_candidato = int(df_perfil.iloc[0]["id"])
    return calcular_scores_todos(id_candidato)    

def render_score_breakdown(id_vaga: int):
    """Renderiza breakdown detalhado do score de fit para uma vaga."""
    from database.candidato import carregar_perfil
    from database.score import calcular_score

    df_perfil = carregar_perfil()
    if df_perfil.empty:
        return

    id_candidato = int(df_perfil.iloc[0]["id"])
    resultado = calcular_score(id_vaga, id_candidato)

    if not resultado["score"]:
        return

    score = resultado["score"]
    matches = resultado["matches"]
    gaps = resultado["gaps"]
    breakdown = resultado["breakdown"]

    cor_score = "#1D9E75" if score >= 70 else "#BA7517" if score >= 40 else "#D85A30"

    st.markdown(
        f"<div style='margin:4px 0 8px 0;'>"
        f"<span style='font-size:12px; color:{cor_score}; font-weight:700;'>"
        f"Score de fit: {score}% ({resultado['total_match']}/{resultado['total_vaga']} stacks)</span>"
        f"<div style='background:#f0f0f0; border-radius:6px; height=8px; margin-top:4px;'>"
        f"<div style='background:{cor_score}; width:{score}%; height:8px; border-radius:6px;'></div>"
        f"</div></div>",
        unsafe_allow_html=True
    )

    if breakdown:
        col_match, col_gap = st.columns(2)

        with col_match:
            if matches:
                st.markdown("**✅ Você tem:**")
                for m in matches:
                    st.markdown(
                        f"<span style='background:#E8F5F0; color:#157A5A; padding:2px 8px; "
                        f"border-radius:10px; font-size:11px; margin:2px; display:inline-block;'>"
                        f"✓ {m['stack']} ({m['nivel']})</span>",
                        unsafe_allow_html=True
                    )

        with col_gap:
            if gaps:
                st.markdown("**❌ Faltam:**")
                for g in gaps:
                    st.markdown(
                        f"<span style='background:#FBF0EB; color:#A83A18; padding:2px 8px; "
                        f"border-radius:10px; font-size:11px; margin:2px; display:inline-block;'>"
                        f"✗ {g['stack']}</span>",
                        unsafe_allow_html=True
                    )

def render_diario(id_vaga: int):
    """Renderiza o diário de candidatura dentro do expander da vaga."""
    from database.diario import adicionar_nota, listar_notas, deletar_nota

    st.divider()
    st.write("**Diário de candidatura:**")

    df_notas = listar_notas(id_vaga)

    # exibe notas existentes
    if not df_notas.empty:
        for _, nota in df_notas.iterrows():
            col_data, col_nota, col_del = st.columns([1.5, 6, 0.5])
            col_data.caption(str(nota["data_nota"])[:10])
            col_nota.write(nota["nota"])
            if col_del.button("✕", key=f"del_nota_{nota['id']}"):
                deletar_nota(nota["id"])
                st.rerun()
    else:
        st.caption("Nenhuma nota ainda.")

    # formulário de nova nota
    with st.form(key=f"form_diario_{id_vaga}"):
        nova_nota = st.text_area("Nova nota", placeholder="Ex: Ligaram do RH, processo tem 3 etapas...", height=80, label_visibility="collapsed")
        if st.form_submit_button("Adicionar nota", use_container_width=True):
            if nova_nota.strip():
                adicionar_nota(id_vaga, nova_nota.strip())
                st.success("Nota adicionada!")
                st.rerun()

def render_preparacao_entrevista(id_vaga: int, id_empresa_nome: str, status_cand: str):
    """Exibe painel de preparação quando vaga está em fase de entrevista."""
    fases_entrevista = ["chamado", "recrutador", "fase_1", "fase_2", "fase_3"]
    if status_cand not in fases_entrevista:
        return

    from database.contatos import listar_contatos
    from database.score import calcular_score
    from database.candidato import carregar_perfil

    con = conectar()
    id_empresa = con.execute(
        "SELECT id FROM dim_empresa WHERE nome = ?", [id_empresa_nome]
    ).fetchone()
    con.close()

    if not id_empresa:
        return

    id_empresa = id_empresa[0]

    st.divider()
    st.markdown(
        "<div style='background:#FFF8E1; border:1px solid #F0C040; border-radius:8px; "
        "padding:12px; margin-bottom:8px;'>"
        "<span style='font-size:14px; font-weight:700; color:#8A5210;'>"
        "🎯 Preparação para entrevista</span></div>",
        unsafe_allow_html=True
    )

    col_gaps, col_contatos = st.columns(2)

    # gaps do score — o que estudar
    with col_gaps:
        st.markdown("**📚 Estude antes da entrevista:**")
        df_perfil = carregar_perfil()
        if not df_perfil.empty:
            resultado = calcular_score(id_vaga, int(df_perfil.iloc[0]["id"]))
            gaps = resultado.get("gaps", [])
            if gaps:
                for g in gaps:
                    st.markdown(
                        f"<span style='background:#FBF0EB; color:#A83A18; padding:2px 8px; "
                        f"border-radius:10px; font-size:11px; margin:2px; display:inline-block;'>"
                        f"✗ {g['stack']}</span>",
                        unsafe_allow_html=True
                    )
            else:
                st.success("Você tem todas as stacks!")
        else:
            st.caption("Cadastre seu perfil para ver os gaps.")

    # contatos na empresa
    with col_contatos:
        st.markdown("**👥 Seus contatos nessa empresa:**")
        df_contatos = listar_contatos(id_empresa)
        if not df_contatos.empty:
            for _, c in df_contatos.iterrows():
                email_tag = f" · `{c['email']}`" if c.get("email") else ""
                st.markdown(
                    f"<div style='background:#E8F5F0; border-radius:6px; padding:6px 10px; "
                    f"margin:3px 0; font-size:12px;'>"
                    f"<b>{c['nome']}</b> — {c['grau']}{email_tag}</div>",
                    unsafe_allow_html=True
                )
        else:
            st.caption("Nenhum contato cadastrado para essa empresa.")
