import json
import time as _time
import duckdb
from scrapers.gupy_scraper import buscar_vagas
from transformers.stack_extractor import extrair_stacks, detectar_nivel, detectar_modalidade
from database.schemas import criar_tabelas
from database.empresas import upsert_empresa, listar_empresas_ativas, gerar_hash
from database.vagas import inserir_vaga, verificar_vagas_encerradas
from database.logs import registrar_log, ultima_execucao_sucesso, empresa_bloqueada
from database.filtros import carregar_filtros
from database.snapshots import salvar_snapshot

TIMEOUT_EMPRESA_SEGUNDOS = 300

def titulo_relevante(titulo: str, interesse: list, bloqueio: list) -> bool:
    titulo_lower = titulo.lower()
    if any(b in titulo_lower for b in bloqueio):
        return False
    if interesse and not any(i in titulo_lower for i in interesse):
        return False
    return True

def processar_empresa(nome: str, url_gupy: str, cooldown_horas: int = 12):
    if empresa_bloqueada(nome):
        print(f"  {nome} bloqueada — aguardando 48h")
        return 0, 0, "bloqueada (48h)"

    vagas_encontradas = 0
    vagas_novas = 0
    erro = ""

    horas_desde_ultima = ultima_execucao_sucesso(nome)
    if horas_desde_ultima < cooldown_horas:
        print(f"  Pulando {nome} — última execução há {horas_desde_ultima}h")
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
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                locale="pt-BR",
                timezone_id="America/Sao_Paulo",
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            try:
                from playwright_stealth import stealth_sync
                stealth_sync(page)
            except ImportError:
                pass

            inicio_coleta = _time.time()
            for vaga in vagas_filtradas:
                if _time.time() - inicio_coleta > TIMEOUT_EMPRESA_SEGUNDOS:
                    print(f"  Timeout de {TIMEOUT_EMPRESA_SEGUNDOS}s atingido")
                    break 
                try:
                    response = page.goto(vaga["link"], wait_until="networkidle", timeout=60000)
                    
                    # detecção de bloqueio
                    if response and response.status in [403, 429]:
                        print(f"  Bloqueado ({response.status}) — parando coleta de {nome}")
                        registrar_log(nome, vagas_encontradas, vagas_novas, "bloqueado", f"HTTP {response.status}")
                        break

                    # detecção Cloudflare
                    content = page.content()
                    if "cloudflare" in content.lower() and "checking your browser" in content.lower():
                        print(f"  Cloudflare detectado — parando coleta de {nome}")
                        registrar_log(nome, vagas_encontradas, vagas_novas, "bloqueado", "Cloudflare")
                        break

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

                import random, time as _t
                _t.sleep(random.uniform(1.5, 3.5))

                vagas_enriquecidas.append(vaga)

            context.close()
            browser.close() 

        id_empresa = upsert_empresa(nome=nome, url_gupy=url_gupy)

        for vaga in vagas_enriquecidas:
            descricao = vaga.get("descricao", "")
            titulo = vaga.get("titulo", "")

            vaga["stacks"]    = extrair_stacks(descricao)
            vaga["nivel"]     = detectar_nivel(titulo)
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
                continue

            inserida = inserir_vaga(vaga, id_empresa)
            if inserida:
                vagas_novas += 1

        links_ativos = [v["link"] for v in vagas_enriquecidas]
        encerradas = verificar_vagas_encerradas(id_empresa, links_ativos)
        if encerradas:
            print(f"  {len(encerradas)} vaga(s) encerrada(s)")

        registrar_log(nome, vagas_encontradas, vagas_novas, "sucesso")
        print(f"  {vagas_encontradas} encontradas | {vagas_novas} novas")

    except Exception as e:
        erro = str(e)
        registrar_log(nome, vagas_encontradas, vagas_novas, "erro", erro)
        print(f"  Erro: {erro}")

    return vagas_encontradas, vagas_novas, erro

def processar_empresa_greenhouse(nome: str, slug: str):
    from scrapers.greenhouse_scraper import buscar_vagas_greenhouse
    from transformers.stack_extractor import extrair_stacks, detectar_nivel

    vagas_encontradas = 0
    vagas_novas = 0

    try:
        vagas = buscar_vagas_greenhouse(slug)
        vagas_encontradas = len(vagas)
        id_empresa = upsert_empresa(nome=nome, url_gupy="")

        for vaga in vagas:
            vaga["stacks"] = extrair_stacks(vaga["titulo"])
            vaga["nivel"] = detectar_nivel(vaga["titulo"])
            vaga["empresa"] = nome

            from database.vagas import gerar_hash
            h = gerar_hash(vaga["titulo"], nome, vaga["link"])
            con_check = duckdb.connect("data/curated/jobs.duckdb")
            existe = con_check.execute("SELECT id FROM fact_vaga WHERE hash=?", [h]).fetchone()
            con_check.close()
            if existe:
                continue

            inserida = inserir_vaga(vaga, id_empresa)
            if inserida:
                vagas_novas += 1

        registrar_log(nome, vagas_encontradas, vagas_novas, "sucesso")
        print(f"  {vagas_encontradas} encontradas | {vagas_novas} novas")

    except Exception as e:
        registrar_log(nome, 0, 0, "erro", str(e))
        print(f"  Erro: {e}")

    return vagas_encontradas, vagas_novas, ""

def processar_empresa_inhire(nome: str, url_inhire: str):
    from scrapers.inhire_scraper import buscar_vagas_inhire
    from transformers.stack_extractor import extrair_stacks, detectar_nivel

    vagas_encontradas = 0
    vagas_novas = 0

    try:
        vagas = buscar_vagas_inhire(url_inhire)
        vagas_encontradas = len(vagas)
        id_empresa = upsert_empresa(nome=nome, url_gupy="")

        for vaga in vagas:
            vaga["stacks"] = extrair_stacks(vaga["titulo"])
            vaga["nivel"] = detectar_nivel(vaga["titulo"])
            vaga["empresa"] = nome

            from database.vagas import gerar_hash
            h = gerar_hash(vaga["titulo"], nome, vaga["link"])
            con_check = duckdb.connect("data/curated/jobs.duckdb")
            existe = con_check.execute("SELECT id FROM fact_vaga WHERE hash=?", [h]).fetchone()
            con_check.close()
            if existe:
                continue

            inserida = inserir_vaga(vaga, id_empresa)
            if inserida:
                vagas_novas += 1

        registrar_log(nome, vagas_encontradas, vagas_novas, "sucesso")
        print(f"  {vagas_encontradas} encontradas | {vagas_novas} novas")

    except Exception as e:
        registrar_log(nome, 0, 0, "erro", str(e))
        print(f"  Erro: {e}")

    return vagas_encontradas, vagas_novas, ""


def rodar_pipeline():
    criar_tabelas()
    empresas = listar_empresas_ativas()

    if not empresas:
        print("Nenhuma empresa ativa no banco.")
        return

    print(f"\n{len(empresas)} empresa(s) ativa(s)")

    for nome, url_gupy in empresas:
        print(f"\nProcessando {nome}...")
        processar_empresa(nome, url_gupy)

    # empresas Greenhouse
    con_gh = duckdb.connect("data/curated/jobs.duckdb")
    empresas_gh = con_gh.execute("""
        SELECT nome, url_greenhouse FROM dim_empresa
        WHERE ativa = true AND url_greenhouse IS NOT NULL
    """).fetchall()
    con_gh.close()

    for nome, slug in empresas_gh:
        print(f"\nProcessando {nome} (Greenhouse)...")
        processar_empresa_greenhouse(nome, slug)

    # empresas Inhire
    con_inh = duckdb.connect("data/curated/jobs.duckdb")
    empresas_inh = con_inh.execute("""
        SELECT nome, url_inhire FROM dim_empresa
        WHERE ativa = true AND url_inhire IS NOT NULL
    """).fetchall()
    con_inh.close()

    for nome, url_inhire in empresas_inh:
        print(f"\nProcessando {nome} (Inhire)...")
        processar_empresa_inhire(nome, url_inhire)

    # snapshot automático ao final do pipeline
    print("\nSalvando snapshot do mercado...")
    salvar_snapshot()

    print("\nPipeline concluído.")


if __name__ == "__main__":
    rodar_pipeline()