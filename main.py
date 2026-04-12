import json
import time as _time
import duckdb
from scrapers.gupy_scraper import buscar_vagas
from transformers.stack_extractor import extrair_stacks, detectar_nivel, detectar_modalidade
from database.db_manager import (
    criar_tabelas,
    upsert_empresa,
    inserir_vaga,
    registrar_log,
    listar_empresas_ativas,
    verificar_vagas_encerradas,
    gerar_hash,
    carregar_filtros,
    ultima_execucao_sucesso
)

TIMEOUT_EMPRESA_SEGUNDOS = 300  # 5 minutos por empresa


def titulo_relevante(titulo: str, interesse: list, bloqueio: list) -> bool:
    titulo_lower = titulo.lower()
    if any(b in titulo_lower for b in bloqueio):
        return False
    if interesse and not any(i in titulo_lower for i in interesse):
        return False
    return True


def processar_empresa(nome: str, url_gupy: str, cooldown_horas: int = 12):
    vagas_encontradas = 0
    vagas_novas = 0
    erro = ""

    # verifica cooldown
    horas_desde_ultima = ultima_execucao_sucesso(nome)
    if horas_desde_ultima < cooldown_horas:
        print(f"  Pulando {nome} — última execução há {horas_desde_ultima}h (cooldown: {cooldown_horas}h)")
        return 0, 0, f"cooldown ({horas_desde_ultima}h)"

    print(f"  Última execução: {horas_desde_ultima}h atrás")

    try:
        vagas = buscar_vagas(url_gupy)
        vagas_encontradas = len(vagas)

        interesse, bloqueio = carregar_filtros()
        vagas_filtradas = [v for v in vagas if titulo_relevante(v["titulo"], interesse, bloqueio)]
        print(f"  {len(vagas_filtradas)} vagas relevantes de {vagas_encontradas} após filtro")

        vagas_enriquecidas = []
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            inicio_coleta = _time.time()

            for vaga in vagas_filtradas:
                # timeout por empresa
                if _time.time() - inicio_coleta > TIMEOUT_EMPRESA_SEGUNDOS:
                    print(f"  Timeout de {TIMEOUT_EMPRESA_SEGUNDOS}s atingido — parando coleta de descrições")
                    break

                try:
                    page.goto(vaga["link"], wait_until="networkidle", timeout=60000)
                    page.wait_for_selector(
                        "[class*='description'], [class*='jobDescription'], section",
                        timeout=10000
                    )
                    el = page.query_selector(
                        "[class*='description'], [class*='jobDescription'], section"
                    )
                    vaga["descricao"] = el.inner_text().strip() if el else ""
                except Exception as e:
                    print(f"  Erro na vaga {vaga['titulo'][:40]}: {str(e)[:60]}")
                    vaga["descricao"] = ""
                vagas_enriquecidas.append(vaga)

            browser.close()

        id_empresa = upsert_empresa(nome=nome, url_gupy=url_gupy)

        for vaga in vagas_enriquecidas:
            descricao = vaga.get("descricao", "")
            titulo = vaga.get("titulo", "")

            vaga["stacks"] = extrair_stacks(descricao)
            vaga["nivel"] = detectar_nivel(titulo)
            vaga["modalidade"] = detectar_modalidade(
                descricao,
                modalidade_coletada=vaga.get("modalidade", "não identificado")
            )

            con_check = duckdb.connect("data/curated/jobs.duckdb")
            negada = con_check.execute("""
                SELECT id FROM fact_vaga WHERE hash = ? AND negada = true
            """, [gerar_hash(vaga["titulo"], vaga["empresa"], vaga["link"])]).fetchone()
            con_check.close()

            if negada:
                print(f"  Vaga negada ignorada: {vaga['titulo']}")
                continue

            inserida = inserir_vaga(vaga, id_empresa)
            if inserida:
                vagas_novas += 1

        links_ativos = [v["link"] for v in vagas_enriquecidas]
        encerradas = verificar_vagas_encerradas(id_empresa, links_ativos)
        if encerradas:
            print(f"  {len(encerradas)} vaga(s) encerrada(s):")
            for titulo in encerradas:
                print(f"    - {titulo}")

        registrar_log(nome, vagas_encontradas, vagas_novas, "sucesso")
        print(f"  {vagas_encontradas} encontradas | {vagas_novas} novas")

    except Exception as e:
        erro = str(e)
        registrar_log(nome, vagas_encontradas, vagas_novas, "erro", erro)
        print(f"  Erro: {erro}")

    return vagas_encontradas, vagas_novas, erro


def rodar_pipeline():
    criar_tabelas()
    empresas = listar_empresas_ativas()

    if not empresas:
        print("Nenhuma empresa ativa no banco.")
        return

    print(f"\n{len(empresas)} empresa(s) ativa(s) para monitorar")

    for nome, url_gupy in empresas:
        print(f"\nProcessando {nome}...")
        processar_empresa(nome, url_gupy)

    print("\nPipeline concluído. Resumo no banco:")
    con = duckdb.connect("data/curated/jobs.duckdb")
    print(con.execute("""
        SELECT e.nome, COUNT(v.id) as total_vagas
        FROM fact_vaga v
        JOIN dim_empresa e ON v.id_empresa = e.id
        GROUP BY e.nome
    """).df())

    print("\nÚltimos logs:")
    print(con.execute("""
        SELECT empresa, vagas_encontradas, vagas_novas, status, data_execucao
        FROM log_coleta
        ORDER BY data_execucao DESC
        LIMIT 5
    """).df())
    con.close()


if __name__ == "__main__":
    rodar_pipeline()