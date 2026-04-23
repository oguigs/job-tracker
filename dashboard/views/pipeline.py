import streamlit as st
from database.connection import DB_PATH
import threading
import time
import duckdb
from database.logs import ultima_execucao_sucesso
from database.schemas import criar_tabelas
from main import processar_empresa, processar_empresa_greenhouse, processar_empresa_inhire, processar_empresa_smartrecruiters


def detectar_plataforma(url: str) -> str:
    if "gupy.io" in url: return "Gupy"
    if "greenhouse.io" in url: return "Greenhouse"
    if "inhire.app" in url: return "Inhire"
    if "smartrecruiters.com" in url: return "SmartRecruiters"
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


def render():
    st.title("🔄 Pipeline")
    st.caption("Coleta automática de vagas em background.")

    con = duckdb.connect(DB_PATH)
    empresas = con.execute("""
        SELECT nome, url_vagas FROM dim_empresa
        WHERE ativa = true AND url_vagas IS NOT NULL
        ORDER BY nome
    """).fetchall()
    con.close()

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

    if estado["rodando"]:
        time.sleep(2)
        st.rerun()