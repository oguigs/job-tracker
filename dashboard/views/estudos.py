import streamlit as st
import json
from database.connection import conectar

ESTUDOS = {
    "🔤 Fundamentos": {
        "SQL Avançado": {"desc": "Window functions, CTEs, otimização de queries", "prioridade": "alta"},
        "Python para Dados": {"desc": "Pandas, NumPy, tipagem, testes unitários", "prioridade": "alta"},
        "Git & GitHub": {"desc": "Branching, PRs, CI/CD básico", "prioridade": "alta"},
        "Linux & Terminal": {"desc": "Shell scripting, cron jobs, processos", "prioridade": "media"},
    },
    "☁️ Cloud": {
        "AWS S3": {"desc": "Storage, particionamento, lifecycle policies", "prioridade": "alta"},
        "AWS Glue": {"desc": "ETL serverless, crawlers, data catalog", "prioridade": "alta"},
        "AWS Athena": {"desc": "Queries em S3, particionamento, otimização", "prioridade": "alta"},
        "AWS Lambda": {"desc": "Funções serverless, triggers, integrações", "prioridade": "media"},
        "AWS EMR": {"desc": "Spark gerenciado na AWS", "prioridade": "media"},
        "Azure Data Factory": {"desc": "Pipelines ETL no Azure", "prioridade": "alta"},
        "Azure Databricks": {"desc": "Spark + Delta Lake no Azure", "prioridade": "alta"},
        "GCP BigQuery": {"desc": "Data warehouse serverless do Google", "prioridade": "media"},
        "Databricks": {"desc": "Plataforma unificada de dados e IA", "prioridade": "alta"},
        "Snowflake": {"desc": "Data warehouse cloud-native", "prioridade": "media"},
    },
    "⚙️ Processamento": {
        "Apache Spark": {"desc": "Processamento distribuído em larga escala", "prioridade": "alta"},
        "PySpark": {"desc": "Spark com Python — API DataFrame e SQL", "prioridade": "alta"},
        "Apache Kafka": {"desc": "Streaming de eventos em tempo real", "prioridade": "alta"},
        "dbt": {"desc": "Transformações SQL versionadas e testadas", "prioridade": "alta"},
        "Apache Flink": {"desc": "Stream processing de baixa latência", "prioridade": "media"},
        "Pandas": {"desc": "Manipulação de dados em Python", "prioridade": "alta"},
    },
    "🎼 Orquestração": {
        "Apache Airflow": {"desc": "DAGs, operators, hooks, XComs", "prioridade": "alta"},
        "Prefect": {"desc": "Orquestração moderna com Python nativo", "prioridade": "media"},
        "Dagster": {"desc": "Data assets, partições, observabilidade", "prioridade": "media"},
    },
    "🗄️ Armazenamento": {
        "Delta Lake": {"desc": "ACID transactions em data lakes", "prioridade": "alta"},
        "Apache Iceberg": {"desc": "Table format open source para lakes", "prioridade": "media"},
        "Data Lakehouse": {"desc": "Arquitetura unificando lake e warehouse", "prioridade": "alta"},
        "Redis": {"desc": "Cache em memória e estruturas de dados", "prioridade": "media"},
        "PostgreSQL Avançado": {"desc": "Indexing, particionamento, performance", "prioridade": "media"},
    },
    "📊 Qualidade de Dados": {
        "Great Expectations": {"desc": "Testes e validações de dados em Python", "prioridade": "alta"},
        "Soda.io": {"desc": "Monitoramento de qualidade de dados — perguntado em entrevista", "prioridade": "alta"},
        "Data Contracts": {"desc": "Esquemas acordados entre produtores e consumidores", "prioridade": "alta"},
        "Data Lineage": {"desc": "Rastreamento de origem e transformações dos dados", "prioridade": "media"},
        "SLAs de Pipeline": {"desc": "Alertas e monitoramento de qualidade dos pipelines", "prioridade": "alta"},
        "Anomaly Detection": {"desc": "Detecção automática de problemas nos dados", "prioridade": "media"},
        "dbt Tests": {"desc": "Testes de qualidade integrados ao dbt", "prioridade": "alta"},
    },
    "🏗️ Arquitetura": {
        "Medallion Architecture": {"desc": "Bronze/Silver/Gold — camadas de qualidade", "prioridade": "alta"},
        "Data Mesh": {"desc": "Domínios descentralizados de dados", "prioridade": "media"},
        "Lambda Architecture": {"desc": "Batch + streaming combinados", "prioridade": "media"},
        "Kappa Architecture": {"desc": "Tudo como streaming", "prioridade": "media"},
        "Data Vault": {"desc": "Modelagem para data warehouses auditáveis", "prioridade": "media"},
    },
    "🤖 ML/AI para DE": {
        "MLflow": {"desc": "Tracking de experimentos e registro de modelos", "prioridade": "media"},
        "Feature Store": {"desc": "Armazenamento e serving de features de ML", "prioridade": "media"},
        "MLOps Básico": {"desc": "CI/CD para modelos de ML", "prioridade": "media"},
        "LangChain": {"desc": "Framework para aplicações com LLMs", "prioridade": "media"},
        "Vector Databases": {"desc": "Armazenamento para embeddings de IA", "prioridade": "baixa"},
    },
    "🐳 Infraestrutura": {
        "Docker": {"desc": "Containerização de aplicações e pipelines", "prioridade": "alta"},
        "Kubernetes": {"desc": "Orquestração de containers em produção", "prioridade": "media"},
        "Terraform": {"desc": "Infraestrutura como código", "prioridade": "media"},
        "CI/CD": {"desc": "GitHub Actions, pipelines de deploy", "prioridade": "alta"},
    },
}

STATUS_OPTIONS = ["⬜ Para estudar", "📖 Estudando", "✅ Concluído"]
STATUS_CORES = {
    "⬜ Para estudar": "#888",
    "📖 Estudando": "#BA7517",
    "✅ Concluído": "#1D9E75",
}

def get_status_key(categoria, topico):
    return f"estudo_{categoria[:10]}_{topico[:15]}".replace(" ","_").replace("/","_")

def carregar_todos_status():
    con = conectar()
    try:
        rows = con.execute("SELECT termo FROM config_filtros WHERE tipo = 'estudo_status'").fetchall()
        con.close()
        result = {}
        for (termo,) in rows:
            if "=" in termo:
                k, v = termo.split("=", 1)
                result[k] = v
        return result
    except:
        con.close()
        return {}

def salvar_status_topico(key, novo_status):
    con = conectar()
    try:
        con.execute("DELETE FROM config_filtros WHERE tipo='estudo_status' AND termo LIKE ?", [f"{key}=%"])
        con.execute("INSERT INTO config_filtros (id, tipo, termo) VALUES (nextval('seq_filtro'), 'estudo_status', ?)", [f"{key}={novo_status}"])
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
    con.close()

def carregar_livros():
    con = conectar()
    try:
        rows = con.execute("SELECT termo FROM config_filtros WHERE tipo = 'livro'").fetchall()
        con.close()
        livros = []
        for (termo,) in rows:
            try:
                livros.append(json.loads(termo))
            except:
                pass
        return livros
    except:
        con.close()
        return []

def salvar_livro(livro: dict):
    con = conectar()
    try:
        con.execute("INSERT INTO config_filtros (id, tipo, termo) VALUES (nextval('seq_filtro'), 'livro', ?)", [json.dumps(livro)])
    except Exception as e:
        st.error(f"Erro ao salvar livro: {e}")
    con.close()

def atualizar_livro(livro_id: str, pagina_atual: int):
    con = conectar()
    try:
        rows = con.execute("SELECT id, termo FROM config_filtros WHERE tipo='livro'").fetchall()
        for row_id, termo in rows:
            try:
                l = json.loads(termo)
                if l.get("id") == livro_id:
                    l["pagina_atual"] = pagina_atual
                    con.execute("UPDATE config_filtros SET termo=? WHERE id=?", [json.dumps(l), row_id])
                    break
            except:
                pass
    except Exception as e:
        st.error(f"Erro: {e}")
    con.close()

def deletar_livro(livro_id: str):
    con = conectar()
    try:
        rows = con.execute("SELECT id, termo FROM config_filtros WHERE tipo='livro'").fetchall()
        for row_id, termo in rows:
            try:
                l = json.loads(termo)
                if l.get("id") == livro_id:
                    con.execute("DELETE FROM config_filtros WHERE id=?", [row_id])
                    break
            except:
                pass
    except:
        pass
    con.close()


def render():
    st.title("📚 Estudos — Data Engineering")
    st.caption("Roadmap personalizado baseado nas stacks mais exigidas nas vagas da sua base.")

    tab_roadmap, tab_livros = st.tabs(["🗺 Roadmap", "📖 Livros"])

    # ── TAB ROADMAP ────────────────────────────────────────────
    with tab_roadmap:
        todos_status = carregar_todos_status()
        total = sum(len(t) for t in ESTUDOS.values())
        concluidos = sum(1 for v in todos_status.values() if v == "✅ Concluído")
        estudando = sum(1 for v in todos_status.values() if v == "📖 Estudando")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total", total)
        col2.metric("✅ Concluídos", concluidos)
        col3.metric("📖 Estudando", estudando)
        col4.metric("⬜ Pendentes", total - concluidos - estudando)

        if total > 0:
            st.progress(concluidos / total)
            st.caption(f"Progresso geral: {round(concluidos/total*100)}%")

        st.divider()

        col_f1, col_f2 = st.columns(2)
        filtro_status = col_f1.selectbox("Filtrar por status", ["Todos"] + STATUS_OPTIONS)
        filtro_prio = col_f2.selectbox("Filtrar por prioridade", ["Todas", "Alta", "Média", "Baixa"])

        st.divider()

        for categoria, topicos in ESTUDOS.items():
            topicos_filtrados = {}
            for topico, info in topicos.items():
                key = get_status_key(categoria, topico)
                status_atual = todos_status.get(key, "⬜ Para estudar")
                prio = info["prioridade"]
                if filtro_status != "Todos" and status_atual != filtro_status:
                    continue
                if filtro_prio != "Todas" and prio != filtro_prio.lower():
                    continue
                topicos_filtrados[topico] = (info, key, status_atual)

            if not topicos_filtrados:
                continue

            with st.expander(f"{categoria} ({len(topicos_filtrados)})", expanded=False):
                for topico, (info, key, status_atual) in topicos_filtrados.items():
                    prio = info["prioridade"]
                    cor_prio = "#1D9E75" if prio == "alta" else "#BA7517" if prio == "media" else "#888"

                    col_t, col_p, col_s = st.columns([4, 1, 2])
                    col_t.markdown(f"**{topico}**")
                    col_t.caption(info["desc"])
                    col_p.markdown(
                        f"<div style='padding-top:8px'>"
                        f"<span style='background:{cor_prio};color:white;font-size:10px;"
                        f"padding:2px 6px;border-radius:8px'>{prio}</span></div>",
                        unsafe_allow_html=True)

                    novo_status = col_s.selectbox(
                        "", STATUS_OPTIONS,
                        index=STATUS_OPTIONS.index(status_atual) if status_atual in STATUS_OPTIONS else 0,
                        key=f"sel_{key}"
                    )
                    if novo_status != status_atual:
                        salvar_status_topico(key, novo_status)
                        st.rerun()

                    st.divider()

    # ── TAB LIVROS ─────────────────────────────────────────────
    with tab_livros:
        livros = carregar_livros()

        # métricas
        if livros:
            col1, col2 = st.columns(2)
            col1.metric("Livros cadastrados", len(livros))
            concluidos_l = sum(1 for l in livros if l.get("pagina_atual",0) >= l.get("total_paginas",1))
            col2.metric("✅ Concluídos", concluidos_l)
            st.divider()

        # lista de livros
        for livro in livros:
            lid = livro.get("id","")
            titulo = livro.get("titulo","")
            total_pag = int(livro.get("total_paginas", 0))
            pag_atual = int(livro.get("pagina_atual", 0))
            pct = round(pag_atual / total_pag * 100) if total_pag > 0 else 0
            faltam = total_pag - pag_atual

            with st.container(border=True):
                col_t, col_del = st.columns([6, 1])
                col_t.markdown(f"**{titulo}**")
                if col_del.button("🗑", key=f"del_livro_{lid}"):
                    deletar_livro(lid)
                    st.rerun()

                col_prog, col_info = st.columns([3, 2])
                with col_prog:
                    st.progress(pct / 100)
                    st.caption(f"{pct}% lido")
                with col_info:
                    st.caption(f"📄 {pag_atual} / {total_pag} páginas")
                    st.caption(f"📖 Faltam {faltam} páginas")

                nova_pag = st.number_input(
                    "Atualizar página atual",
                    min_value=0, max_value=total_pag,
                    value=pag_atual, step=1,
                    key=f"pag_{lid}"
                )
                if nova_pag != pag_atual:
                    if st.button("Salvar", key=f"save_pag_{lid}"):
                        atualizar_livro(lid, nova_pag)
                        st.rerun()

        st.divider()
        st.subheader("➕ Adicionar livro")
        with st.form("form_novo_livro"):
            titulo_novo = st.text_input("Título do livro")
            total_pag_novo = st.number_input("Total de páginas", min_value=1, value=300, step=1)
            pag_inicio = st.number_input("Página atual (opcional)", min_value=0, value=0, step=1)
            if st.form_submit_button("Adicionar", use_container_width=True):
                if titulo_novo:
                    import uuid
                    salvar_livro({
                        "id": uuid.uuid4().hex[:8],
                        "titulo": titulo_novo,
                        "total_paginas": int(total_pag_novo),
                        "pagina_atual": int(pag_inicio)
                    })
                    st.success(f"'{titulo_novo}' adicionado!")
                    st.rerun()
                else:
                    st.error("Título é obrigatório.")