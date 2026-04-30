import streamlit as st
import plotly.graph_objects as go
import json
from database.connection import db_connect


@st.cache_data(ttl=300)
def _load_metrics():
    with db_connect() as con:
        total_vagas = con.execute("SELECT COUNT(*) FROM fact_vaga").fetchone()[0]
        empresas_ativas = con.execute(
            "SELECT COUNT(*) FROM dim_empresa WHERE ativa=true"
        ).fetchone()[0]
        fontes = con.execute(
            "SELECT fonte, COUNT(*) as n FROM fact_vaga GROUP BY fonte ORDER BY n DESC"
        ).fetchall()
        modalidade_raw = con.execute(
            "SELECT modalidade, COUNT(*) as n FROM fact_vaga GROUP BY modalidade ORDER BY n DESC"
        ).fetchall()
        nivel_raw = con.execute(
            "SELECT nivel, COUNT(*) as n FROM fact_vaga GROUP BY nivel ORDER BY n DESC LIMIT 6"
        ).fetchall()
        vagas_por_dia = con.execute("""
            SELECT CAST(data_coleta AS DATE) as dia, COUNT(*) as n
            FROM fact_vaga
            WHERE data_coleta IS NOT NULL
            GROUP BY dia ORDER BY dia
        """).fetchall()
        ultima = con.execute(
            "SELECT MAX(data_execucao) FROM log_coleta WHERE status='sucesso'"
        ).fetchone()[0]
        total_exec = con.execute("SELECT COUNT(*) FROM log_coleta").fetchone()[0]
        stacks_raw = con.execute(
            "SELECT stacks FROM fact_vaga WHERE stacks IS NOT NULL AND stacks != ''"
        ).fetchall()

    stack_count = {}
    for (stacks_json,) in stacks_raw:
        try:
            data = json.loads(stacks_json)
            for cat, items in data.items():
                if cat == "nivel":
                    continue
                for s in items or []:
                    stack_count[s] = stack_count.get(s, 0) + 1
        except Exception:
            pass
    top_stacks = sorted(stack_count.items(), key=lambda x: -x[1])[:15]

    modal_merged = {}
    for m, n in modalidade_raw:
        key = (m or "não identificado").replace("híbrido", "hibrido")
        modal_merged[key] = modal_merged.get(key, 0) + n
    modalidade = sorted(modal_merged.items(), key=lambda x: -x[1])

    return {
        "total_vagas": total_vagas,
        "empresas_ativas": empresas_ativas,
        "fontes": fontes,
        "modalidade": modalidade,
        "nivel": list(nivel_raw),
        "vagas_por_dia": vagas_por_dia,
        "ultima": ultima,
        "total_exec": total_exec,
        "top_stacks": top_stacks,
    }


def _diagram_html() -> str:
    ss = "flex:1;min-width:145px;border-radius:10px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.09)"
    hs = "padding:11px 14px;font-size:10px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:white"
    bs = "padding:10px 12px;background:white;border:1px solid #ebebeb;border-top:none;border-radius:0 0 10px 10px;min-height:180px"
    arrow = "<div style='display:flex;align-items:center;justify-content:center;padding:0 5px;font-size:22px;color:#c8c8c8;flex-shrink:0;margin-top:40px'>→</div>"

    def item(txt, bg, fg):
        return (
            f"<div style='padding:5px 9px;margin:3px 0;border-radius:6px;"
            f"font-size:12px;font-weight:500;background:{bg};color:{fg}'>{txt}</div>"
        )

    def stage(title, color, bg, fg, items):
        body = "".join(item(i, bg, fg) for i in items)
        return (
            f"<div style='{ss}'>"
            f"<div style='{hs};background:{color}'>{title}</div>"
            f"<div style='{bs}'>{body}</div></div>"
        )

    s1 = stage(
        "📥 Fontes",
        "#1A5FAD",
        "#EBF3FB",
        "#1A5FAD",
        [
            "🟣 Gupy API",
            "🟠 Amazon Jobs API",
            "🟢 Greenhouse API",
            "⚫ BCG Careers",
            "🔵 InHire",
            "🟡 SmartRecruiters",
            "✏️ Cadastro manual",
        ],
    )
    s2 = stage(
        "⚡ Extração",
        "#157A5A",
        "#E8F5F0",
        "#157A5A",
        [
            "requests HTTP",
            "JSON REST API",
            "Playwright headless",
            "playwright-stealth",
            "Paginação automática",
            "Timeout 5 min",
        ],
    )
    s3 = stage(
        "🔧 Transformação",
        "#8A5210",
        "#FBF4E8",
        "#8A5210",
        [
            "Normalização de campos",
            "Dedup via MD5 hash",
            "Stack Extractor NLP",
            "Detector de nível",
            "Detector de modalidade",
            "ATS Score (ANYA)",
            "Cooldown 12 h / empresa",
        ],
    )
    s4 = stage(
        "💾 Armazenamento",
        "#7F77DD",
        "#F0EFF9",
        "#4B44AA",
        [
            "DuckDB (local)",
            "fact_vaga",
            "dim_empresa",
            "log_coleta",
            "7 backups automáticos",
        ],
    )
    s5 = stage(
        "📊 Analytics",
        "#1D9E75",
        "#E8F5F0",
        "#157A5A",
        [
            "Streamlit dashboard",
            "Plotly interativo",
            "Score de Fit",
            "Funil de candidatura",
            "Tendências de stacks",
            "Análise ATS",
        ],
    )

    return (
        "<div style='display:flex;align-items:flex-start;gap:0;width:100%;"
        "overflow-x:auto;padding:20px 0 8px'>"
        f"{s1}{arrow}{s2}{arrow}{s3}{arrow}{s4}{arrow}{s5}"
        "</div>"
    )


def _tech_stack_html() -> str:
    techs = [
        ("Python 3.11", "#3776AB", "#fff"),
        ("DuckDB", "#FFF000", "#000"),
        ("Streamlit", "#FF4B4B", "#fff"),
        ("Playwright", "#2EAD33", "#fff"),
        ("playwright-stealth", "#1D9E75", "#fff"),
        ("Plotly", "#3F4F75", "#fff"),
        ("requests", "#378ADD", "#fff"),
        ("Claude API (ATS)", "#7F77DD", "#fff"),
    ]
    badges = "".join(
        f"<span style='background:{bg};color:{fg};border-radius:16px;"
        f"padding:5px 14px;font-size:12px;font-weight:600;margin:4px 3px;"
        f"display:inline-block'>{name}</span>"
        for name, bg, fg in techs
    )
    return f"<div style='padding:8px 0'>{badges}</div>"


_FONTE_CORES = {
    "gupy": "#7F77DD",
    "greenhouse": "#1D9E75",
    "amazon": "#D85A30",
    "smartrecruiters": "#BA7517",
    "inhire": "#378ADD",
    "bcg": "#444",
    "manual": "#888",
}

_MODAL_CORES = {
    "remoto": "#1D9E75",
    "hibrido": "#378ADD",
    "presencial": "#D85A30",
    "não identificado": "#ccc",
}

_NIVEL_CORES = {
    "senior": "#8A5210",
    "pleno": "#1D9E75",
    "junior": "#1A5FAD",
    "especialista": "#D85A30",
    "lead": "#7F77DD",
    "não identificado": "#ccc",
}


def render():
    st.title("🏗️ Arquitetura ETL")
    st.caption(
        "Pipeline end-to-end de coleta, transformação e análise de vagas — "
        "visão técnica para portfólio."
    )

    # ── DIAGRAMA ──────────────────────────────────────────────────────────────
    st.subheader("Fluxo do Pipeline")
    st.markdown(_diagram_html(), unsafe_allow_html=True)

    # ── STACK DO PROJETO ─────────────────────────────────────────────────────
    with st.expander("🔩 Stack técnico do projeto"):
        st.markdown(_tech_stack_html(), unsafe_allow_html=True)

    st.divider()

    # ── MÉTRICAS AO VIVO ─────────────────────────────────────────────────────
    st.subheader("📈 Métricas ao vivo")

    m = _load_metrics()
    ultima_str = str(m["ultima"])[:16].replace("T", " ") if m["ultima"] else "—"
    hora = ultima_str.split(" ")[-1][:5] if m["ultima"] else "—"
    data_str = ultima_str.split(" ")[0] if m["ultima"] else ""

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Vagas coletadas", m["total_vagas"])
    c2.metric("Empresas ativas", m["empresas_ativas"])
    c3.metric("Fontes conectadas", len(m["fontes"]))
    c4.metric("Última coleta", hora, data_str)

    st.divider()

    # ── ROW 1: fontes + vagas por dia ─────────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Vagas por fonte**")
        if m["fontes"]:
            labels = [f[0].capitalize() for f in m["fontes"]]
            values = [f[1] for f in m["fontes"]]
            cores = [_FONTE_CORES.get(f[0], "#888") for f in m["fontes"]]
            fig = go.Figure(
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.55,
                    marker=dict(colors=cores),
                    textinfo="label+percent",
                    textfont_size=12,
                )
            )
            fig.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                showlegend=False,
                height=280,
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("**Vagas coletadas por dia**")
        if m["vagas_por_dia"]:
            dias = [str(r[0]) for r in m["vagas_por_dia"]]
            qtd = [r[1] for r in m["vagas_por_dia"]]
            fig2 = go.Figure(
                go.Scatter(
                    x=dias,
                    y=qtd,
                    mode="lines+markers",
                    line=dict(color="#1A5FAD", width=2),
                    marker=dict(size=8, color="#1A5FAD"),
                    fill="tozeroy",
                    fillcolor="rgba(26,95,173,0.08)",
                )
            )
            fig2.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(showgrid=False, tickangle=-30),
                yaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
                height=280,
                plot_bgcolor="white",
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.caption("Sem dados de data de coleta registrados.")

    st.divider()

    # ── ROW 2: modalidade + nível ─────────────────────────────────────────────
    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown("**Modalidade de trabalho**")
        if m["modalidade"]:
            labels_m = [r[0].capitalize() for r in m["modalidade"]]
            vals_m = [r[1] for r in m["modalidade"]]
            cores_m = [_MODAL_CORES.get(r[0], "#888") for r in m["modalidade"]]
            fig3 = go.Figure(
                go.Bar(
                    x=vals_m,
                    y=labels_m,
                    orientation="h",
                    marker_color=cores_m,
                    text=vals_m,
                    textposition="auto",
                )
            )
            fig3.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(showgrid=False),
                yaxis=dict(autorange="reversed"),
                height=230,
                plot_bgcolor="white",
            )
            st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        st.markdown("**Nível de senioridade**")
        if m["nivel"]:
            labels_n = [r[0].capitalize() for r in m["nivel"]]
            vals_n = [r[1] for r in m["nivel"]]
            cores_n = [_NIVEL_CORES.get(r[0], "#888") for r in m["nivel"]]
            fig4 = go.Figure(
                go.Bar(
                    x=vals_n,
                    y=labels_n,
                    orientation="h",
                    marker_color=cores_n,
                    text=vals_n,
                    textposition="auto",
                )
            )
            fig4.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(showgrid=False),
                yaxis=dict(autorange="reversed"),
                height=230,
                plot_bgcolor="white",
            )
            st.plotly_chart(fig4, use_container_width=True)

    st.divider()

    # ── TOP STACKS ─────────────────────────────────────────────────────────────
    st.markdown("**🔧 Tecnologias mais demandadas**")
    if m["top_stacks"]:
        stacks = [s[0].upper() for s in m["top_stacks"]]
        counts = [s[1] for s in m["top_stacks"]]
        fig5 = go.Figure(
            go.Bar(
                x=counts,
                y=stacks,
                orientation="h",
                marker_color="#1A5FAD",
                text=counts,
                textposition="outside",
            )
        )
        fig5.update_layout(
            margin=dict(t=10, b=10, l=10, r=50),
            xaxis=dict(showgrid=False),
            yaxis=dict(autorange="reversed"),
            height=440,
            plot_bgcolor="white",
        )
        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.caption("Nenhuma stack registrada ainda.")

    st.divider()

    # ── TOTAIS DO LOG ─────────────────────────────────────────────────────────
    st.markdown("**📋 Execuções do pipeline**")
    with db_connect() as con:
        df_log = con.execute("""
            SELECT
                SUM(CASE WHEN status='sucesso' THEN 1 ELSE 0 END) as sucessos,
                SUM(CASE WHEN status='erro' THEN 1 ELSE 0 END) as erros,
                SUM(CASE WHEN status='bloqueado' THEN 1 ELSE 0 END) as bloqueios,
                SUM(vagas_encontradas) as total_enc,
                SUM(vagas_novas) as total_novas,
                COUNT(DISTINCT empresa) as empresas_logadas
            FROM log_coleta
        """).fetchone()

    if df_log and df_log[0] is not None:
        lc1, lc2, lc3, lc4, lc5 = st.columns(5)
        lc1.metric("Execuções OK", int(df_log[0] or 0))
        lc2.metric("Erros", int(df_log[1] or 0))
        lc3.metric("Bloqueios", int(df_log[2] or 0))
        lc4.metric("Vagas encontradas (total log)", int(df_log[3] or 0))
        lc5.metric("Empresas no log", int(df_log[5] or 0))
