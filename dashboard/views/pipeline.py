import streamlit as st
import threading
import time
import duckdb
from database.logs import ultima_execucao_sucesso
from database.schemas import criar_tabelas

def render():
    st.title("Pipeline")
    st.caption("Dispare a coleta de vagas em background e acompanhe o status.")

    con = duckdb.connect("data/curated/jobs.duckdb")
    empresas = con.execute("""
        SELECT nome, url_vagas FROM dim_empresa
        WHERE ativa = true AND url_vagas IS NOT NULL
    """).fetchall()
    con.close()

    st.metric("Empresas ativas", len(empresas))
    for nome, url in empresas:
        st.write(f"- {nome} — `{url}`")
    st.divider()

    if "pipeline_estado" not in st.session_state:
        st.session_state.pipeline_estado = {
            "rodando": False, "concluido": False,
            "log": [], "total_encontradas": 0, "total_novas": 0
        }

    estado = st.session_state.pipeline_estado

    def rodar_em_background(empresas, estado):
        from main import processar_empresa
        criar_tabelas()
        total_encontradas = 0
        total_novas = 0
        for nome, url_vagas in empresas:
            horas = ultima_execucao_sucesso(nome)
            if horas < 12:
                estado["log"].append(f"⏭ {nome} — pulada (última execução há {horas}h)")
                continue
            estado["log"].append(f"▶ Iniciando {nome}...")
            encontradas, novas, erro = processar_empresa(nome, url_vagas)
            if erro and "cooldown" not in erro:
                estado["log"].append(f"✗ {nome} — erro: {erro[:60]}")
            else:
                total_encontradas += encontradas
                total_novas += novas
                estado["log"].append(f"✓ {nome} — {encontradas} vagas | {novas} novas")
        estado["total_encontradas"] = total_encontradas
        estado["total_novas"] = total_novas
        estado["log"].append("✓ Pipeline concluído!")
        estado["rodando"] = False
        estado["concluido"] = True

    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("Rodar pipeline completo", type="primary",
                     use_container_width=True, disabled=estado["rodando"]):
            estado["rodando"] = True
            estado["concluido"] = False
            estado["log"] = []
            estado["total_encontradas"] = 0
            estado["total_novas"] = 0
            thread = threading.Thread(
                target=rodar_em_background, args=(empresas, estado), daemon=True)
            thread.start()
            st.rerun()

    with col_btn2:
        intervalo = st.number_input("Intervalo (min)", min_value=1, max_value=60, value=5, step=1)
        if st.button("Rodar espaçado", use_container_width=True, disabled=estado["rodando"]):
            estado["rodando"] = True
            estado["concluido"] = False
            estado["log"] = []
            estado["total_encontradas"] = 0
            estado["total_novas"] = 0
            def rodar_espacado(empresas, estado, intervalo_min):
                from main import processar_empresa
                criar_tabelas()
                for nome, url_vagas in empresas:
                    horas = ultima_execucao_sucesso(nome)
                    if horas < 12:
                        estado["log"].append(f"⏭ {nome} — pulada ({horas}h)")
                        continue
                    estado["log"].append(f"▶ Iniciando {nome}...")
                    encontradas, novas, erro = processar_empresa(nome, url_vagas)
                    if erro and "cooldown" not in erro and "bloqueado" not in erro:
                        estado["log"].append(f"✗ {nome} — {erro[:60]}")
                    else:
                        estado["total_encontradas"] += encontradas
                        estado["total_novas"] += novas
                        estado["log"].append(f"✓ {nome} — {encontradas} vagas | {novas} novas")
                    estado["log"].append(f"⏸ Aguardando {intervalo_min} min...")
                    import time
                    time.sleep(intervalo_min * 60)
                estado["log"].append("✓ Pipeline espaçado concluído!")
                estado["rodando"] = False
                estado["concluido"] = True
            thread = threading.Thread(
                target=rodar_espacado, args=(empresas, estado, intervalo), daemon=True)
            thread.start()
            st.rerun()

    with col_btn3:
        if st.button("Limpar log", use_container_width=True):
            estado["log"] = []
            estado["concluido"] = False
            estado["total_encontradas"] = 0
            estado["total_novas"] = 0
            st.rerun()

    if estado["rodando"]:
        st.info("Pipeline rodando em background — você pode navegar normalmente.")
    if estado["concluido"]:
        col1, col2 = st.columns(2)
        col1.metric("Vagas encontradas", estado["total_encontradas"])
        col2.metric("Vagas novas", estado["total_novas"])
        st.success("Pipeline concluído!")
    if estado["log"]:
        st.divider()
        st.write("**Log de execução:**")
        st.code("\n".join(estado["log"]), language=None)
    if estado["rodando"]:
        time.sleep(3)
        st.rerun()