import streamlit as st
from database.connection import DB_PATH, db_connect
import threading
import time
from database.logs import ultima_execucao_sucesso
from database.schemas import criar_tabelas
from main import (
    processar_empresa, processar_empresa_greenhouse,
    processar_empresa_inhire, processar_empresa_smartrecruiters,
    processar_empresa_amazon, processar_empresa_bcg,
)
from streamlit import cache_data

def detectar_plataforma(url: str) -> str:
    if "gupy.io" in url: return "Gupy"
    if "greenhouse.io" in url: return "Greenhouse"
    if "inhire.app" in url: return "Inhire"
    if "smartrecruiters.com" in url: return "SmartRecruiters"
    if "amazon.jobs" in url: return "Amazon Jobs"
    if "bcg.com" in url or "careers.bcg" in url: return "BCG"
    return "—"


def processar(nome, url):
    url = url or ""
    if "greenhouse.io" in url:
        slug = url.split("greenhouse.io/")[-1].split("/")[0]
        return processar_empresa_greenhouse(nome, slug)
    elif "inhire.app" in url:
        return processar_empresa_inhire(nome, url)
    elif "smartrecruiters.com" in url:
        return processar_empresa_smartrecruiters(nome, url)
    elif "amazon.jobs" in url:
        return processar_empresa_amazon(nome)
    elif "bcg.com" in url or "careers.bcg" in url:
        return processar_empresa_bcg(nome, url)
    else:
        return processar_empresa(nome, url)


def rodar_pipeline(empresas, estado, intervalo_min=0):
    criar_tabelas()
    total_enc = 0
    total_nov = 0
    total = len(empresas)

    for idx, (nome, url) in enumerate(empresas):
        estado["empresa_atual"] = nome
        estado["progresso"] = idx / total

        horas = ultima_execucao_sucesso(nome)
        if horas < 12:
            estado["log"].append(f"⏭ {nome} — pulada ({horas}h atrás)")
            continue

        estado["log"].append(f"▶ {nome}...")
        encontradas, novas, erro = processar(nome, url)

        if erro and "cooldown" not in erro and "bloqueado" not in erro:
            estado["log"].append(f"✗ {nome} — {erro[:60]}")
        else:
            total_enc += encontradas
            total_nov += novas
            estado["log"].append(f"✓ {nome} — {encontradas} vagas | {novas} novas")

        if intervalo_min > 0:
            estado["log"].append(f"⏸ Aguardando {intervalo_min} min...")
            time.sleep(intervalo_min * 60)

    estado["total_encontradas"] = total_enc
    estado["total_novas"] = total_nov
    estado["progresso"] = 1.0
    estado["empresa_atual"] = ""
    estado["log"].append("✅ Pipeline concluído!")
    estado["rodando"] = False
    estado["concluido"] = True
    # invalida cache do Streamlit para refletir novas vagas
    try:
        cache_data.clear()
    except Exception:
        pass


def render():
    st.title("🔄 Pipeline")
    st.caption("Coleta automática de vagas em background.")

    with db_connect() as con:
        empresas = con.execute("""
            SELECT nome, url_vagas FROM dim_empresa
            WHERE ativa = true AND url_vagas IS NOT NULL
            ORDER BY nome
        """).fetchall()

    if "pipeline_estado" not in st.session_state:
        st.session_state.pipeline_estado = {
            "rodando": False, "concluido": False, "log": [],
            "total_encontradas": 0, "total_novas": 0,
            "progresso": 0.0, "empresa_atual": ""
        }
    estado = st.session_state.pipeline_estado

    # ── EMPRESAS ativas ────────────────────────────────────────
    st.subheader(f"Empresas ativas ({len(empresas)})")
    if empresas:
        cols = st.columns(5)
        for i, (nome, url) in enumerate(empresas):
            plat = detectar_plataforma(url or "")
            horas = ultima_execucao_sucesso(nome)
            cor = "#1D9E75" if horas < 12 else "#378ADD" if horas < 48 else "#888"
            label = f"{horas}h atrás" if horas < 999 else "nunca"
            with cols[i % 5]:
                st.markdown(
                    f"<div style='border:1px solid #eee;border-radius:8px;padding:8px;margin:2px 0;"
                    f"border-left:3px solid {cor}'>"
                    f"<div style='font-size:12px;font-weight:600'>{nome}</div>"
                    f"<div style='font-size:10px;color:#888'>{plat} · {label}</div>"
                    f"</div>",
                    unsafe_allow_html=True)
    st.divider()

    # ── CONTROLES ──────────────────────────────────────────────
    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns([2, 1, 1, 1])

    with col_btn1:
        if st.button("🚀 Rodar pipeline", type="primary",
                     use_container_width=True, disabled=estado["rodando"]):
            estado.update({"rodando": True, "concluido": False, "log": [],
                          "total_encontradas": 0, "total_novas": 0,
                          "progresso": 0.0, "empresa_atual": ""})
            threading.Thread(target=rodar_pipeline, args=(empresas, estado), daemon=True).start()
            st.rerun()

    with col_btn2:
        intervalo = st.number_input("⏱ Intervalo (min)", min_value=0, max_value=60, value=0, step=1,
            label_visibility="collapsed", help="0 = sem intervalo")
        st.caption("⏱ intervalo (min)")

    with col_btn3:
        if st.button("⏰ Espaçado", use_container_width=True,
                     disabled=estado["rodando"] or intervalo == 0):
            estado.update({"rodando": True, "concluido": False, "log": [],
                          "total_encontradas": 0, "total_novas": 0,
                          "progresso": 0.0, "empresa_atual": ""})
            threading.Thread(target=rodar_pipeline, args=(empresas, estado, intervalo), daemon=True).start()
            st.rerun()

    with col_btn4:
        if st.button("🗑 Limpar", use_container_width=True, disabled=estado["rodando"]):
            estado.update({"log": [], "concluido": False,
                          "total_encontradas": 0, "total_novas": 0})
            st.rerun()

    # ── STATUS ─────────────────────────────────────────────────
    if estado["rodando"]:
        st.divider()
        emp_atual = estado.get("empresa_atual", "")
        prog = estado.get("progresso", 0.0)
        st.info(f"⚙️ Processando: **{emp_atual}**" if emp_atual else "⚙️ Iniciando...")
        st.progress(prog)
        st.caption(f"{round(prog * 100)}% concluído")

    if estado["concluido"]:
        st.divider()
        col1, col2 = st.columns(2)
        col1.metric("Vagas encontradas", estado["total_encontradas"])
        col2.metric("Vagas novas", estado["total_novas"])
        st.success("✅ Pipeline concluído!")

    # ── LOG ────────────────────────────────────────────────────
    if estado["log"]:
        st.divider()
        st.subheader("Log")
        log_html = ""
        for linha in estado["log"]:
            if linha.startswith("✓"):
                cor = "#1D9E75"
            elif linha.startswith("✗"):
                cor = "#D85A30"
            elif linha.startswith("⏭"):
                cor = "#888"
            elif linha.startswith("▶"):
                cor = "#378ADD"
            elif linha.startswith("⏸"):
                cor = "#BA7517"
            else:
                cor = "#1D9E75"
            log_html += f"<div style='font-size:12px;color:{cor};padding:1px 0'>{linha}</div>"

        st.markdown(
            f"<div style='background:#f8f8f8;border-radius:8px;padding:12px;max-height:300px;overflow-y:auto'>"
            f"{log_html}</div>",
            unsafe_allow_html=True)

    # ── SAÚDE DO PIPELINE ──────────────────────────────────────
    st.divider()
    st.subheader("📊 Saúde do pipeline")
    with db_connect() as con:
        df_saude = con.execute("""
            SELECT
                empresa,
                COUNT(*) as total_execucoes,
                SUM(CASE WHEN status = 'sucesso' THEN 1 ELSE 0 END) as sucessos,
                SUM(CASE WHEN status = 'erro' THEN 1 ELSE 0 END) as erros,
                SUM(CASE WHEN status = 'bloqueado' THEN 1 ELSE 0 END) as bloqueios,
                MAX(data_execucao) as ultima_execucao,
                ROUND(AVG(vagas_encontradas), 0) as media_vagas
            FROM log_coleta
            GROUP BY empresa
            ORDER BY erros DESC, ultima_execucao DESC
        """).df()

    if df_saude.empty:
        st.caption("Nenhuma execução registrada ainda.")
    else:
        col1, col2, col3 = st.columns(3)
        total_empresas = len(df_saude)
        com_erro = df_saude[df_saude["erros"] > 0].shape[0]
        bloqueadas = df_saude[df_saude["bloqueios"] > 0].shape[0]
        col1.metric("Empresas monitoradas", total_empresas)
        col2.metric("⚠️ Com erros recentes", com_erro)
        col3.metric("🚫 Bloqueadas", bloqueadas)
        st.divider()

        for _, row in df_saude.iterrows():
            taxa = round(row["sucessos"] / row["total_execucoes"] * 100) if row["total_execucoes"] > 0 else 0
            cor = "#1D9E75" if taxa >= 80 else "#BA7517" if taxa >= 50 else "#D85A30"
            ultima = str(row["ultima_execucao"])[:16] if row["ultima_execucao"] else "—"
            st.markdown(
                f"<div style='display:flex;align-items:center;padding:6px 0;border-bottom:1px solid #f0f0f0'>"
                f"<span style='flex:2;font-weight:600'>{row['empresa']}</span>"
                f"<span style='flex:1;text-align:center'>"
                f"<span style='color:{cor};font-weight:700'>{taxa}%</span> sucesso</span>"
                f"<span style='flex:1;text-align:center;color:#888;font-size:12px'>"
                f"✓{int(row['sucessos'])} ✗{int(row['erros'])} 🚫{int(row['bloqueios'])}</span>"
                f"<span style='flex:1;text-align:right;color:#888;font-size:11px'>{ultima}</span>"
                f"</div>",
                unsafe_allow_html=True
            )

    if estado["rodando"]:
        time.sleep(2)
        st.rerun()