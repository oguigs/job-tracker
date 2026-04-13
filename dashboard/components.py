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