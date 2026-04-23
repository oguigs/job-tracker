import json
import time as _time
import duckdb
from scrapers.gupy_scraper import buscar_vagas
from transformers.stack_extractor import extrair_stacks, detectar_nivel, detectar_modalidade
from database.schemas import criar_tabelas
from database.empresas import upsert_empresa, listar_empresas_ativas, gerar_hash
from database.vagas import inserir_vaga, verificar_vagas_encerradas
from database.logs import registrar_log, ultima_execucao_sucesso, empresa_bloqueada
from database.filtros import carregar_filtros, carregar_filtros_localizacao
from database.snapshots import salvar_snapshot
from scrapers.greenhouse_scraper import buscar_vagas_greenhouse
from scrapers.inhire_scraper import buscar_vagas_inhire
from scrapers.smartrecruiters_scraper import buscar_vagas_smartrecruiters
from database.connection import DB_PATH, conectar, db_connect
import requests, html, re
TIMEOUT_EMPRESA_SEGUNDOS = 300

def titulo_relevante(titulo: str, interesse: list, bloqueio: list) -> bool:
    titulo_lower = titulo.lower()
    if any(b in titulo_lower for b in bloqueio):
        return False
    if interesse and not any(i in titulo_lower for i in interesse):
        return False
    return True

def localidade_relevante(vaga: dict, permitidos: list, bloqueados: list) -> bool:
    if not permitidos and not bloqueados:
        return True
    
    local = (
        vaga.get("cidade", "") + " " + 
        vaga.get("pais", "") + " " +
        vaga.get("modalidade", "") + " " +
        vaga.get("titulo", "")
    ).lower()
    
    if bloqueados:
        bloqueados_iso = {"india": "in", "china": "cn", "pakistan": "pk"}
        for b in bloqueados:
            if b.lower() in local:
                return False
            if b.lower() in bloqueados_iso and bloqueados_iso[b.lower()] == vaga.get("pais","").lower():
                return False
    
    if permitidos:
        permitidos_iso = {"brazil": "br", "brasil": "br"}
        for p in permitidos:
            if p.lower() in local:
                return True
            if p.lower() in permitidos_iso and permitidos_iso[p.lower()] == vaga.get("pais","").lower():
                return True
        return "remoto" in local or "remote" in local
    
    return True

def processar_empresa(nome: str, url_vagas: str, cooldown_horas: int = 12) -> tuple[int, int, str]:
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
        vagas = buscar_vagas(url_vagas)
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

        id_empresa = upsert_empresa(nome=nome, url_vagas=url_vagas)

        for vaga in vagas_enriquecidas:
            descricao = vaga.get("descricao", "")
            titulo = vaga.get("titulo", "")

            vaga["stacks"]    = extrair_stacks(descricao)
            vaga["nivel"]     = detectar_nivel(titulo)
            vaga["modalidade"] = detectar_modalidade(
                descricao,
                modalidade_coletada=vaga.get("modalidade", "não identificado")
            )

            with db_connect(read_only=True) as con_check:
                negada = con_check.execute("""
                    SELECT id FROM fact_vaga WHERE hash = ? AND negada = true
                """, [gerar_hash(vaga["titulo"], vaga["empresa"], vaga["link"])]).fetchone()

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

def _processar_empresa_generica(nome: str, vagas_raw: list) -> tuple[int, int, str]:
    """Processa vagas já coletadas — filtra, enriquece e insere no banco."""
    vagas_novas = 0
    try:
        interesse, bloqueio = carregar_filtros()
        vagas = [v for v in vagas_raw if titulo_relevante(v["titulo"], interesse, bloqueio)]
        print(f"  {len(vagas)} vagas relevantes após filtro de título")

        permitidos, bloqueados = carregar_filtros_localizacao()
        vagas = [v for v in vagas if localidade_relevante(v, permitidos, bloqueados)]
        print(f"  {len(vagas)} vagas após filtro de localização")

        vagas_encontradas = len(vagas)
        id_empresa = upsert_empresa(nome=nome, url_vagas="")

        for vaga in vagas:
            vaga["stacks"] = extrair_stacks(vaga.get("descricao", "") or vaga["titulo"])
            vaga["nivel"] = detectar_nivel(vaga["titulo"])
            vaga["empresa"] = nome
            h = gerar_hash(vaga["titulo"], nome, vaga["link"])
            with db_connect(read_only=True) as con_check:
                existe = con_check.execute("SELECT id FROM fact_vaga WHERE hash=?", [h]).fetchone()
            if existe:
                continue
            if inserir_vaga(vaga, id_empresa):
                vagas_novas += 1

        registrar_log(nome, vagas_encontradas, vagas_novas, "sucesso")
        print(f"  {vagas_encontradas} encontradas | {vagas_novas} novas")
        return vagas_encontradas, vagas_novas, ""

    except Exception as e:
        registrar_log(nome, 0, 0, "erro", str(e))
        print(f"  Erro: {e}")
        return 0, 0, str(e)


def processar_empresa_greenhouse(nome: str, slug: str) -> tuple[int, int, str]:
    vagas_raw = buscar_vagas_greenhouse(slug)
    return _processar_empresa_generica(nome, vagas_raw)


def processar_empresa_inhire(nome: str, url_inhire: str) -> tuple[int, int, str]:
    from scrapers.inhire_scraper import buscar_vagas_inhire
    vagas_raw = buscar_vagas_inhire(url_inhire)
    return _processar_empresa_generica(nome, vagas_raw)


def processar_empresa_smartrecruiters(nome: str, url: str) -> tuple[int, int, str]:
    vagas_raw = buscar_vagas_smartrecruiters(url)
    return _processar_empresa_generica(nome, vagas_raw)

def rodar_pipeline() -> None:
    criar_tabelas()
    
    with db_connect(read_only=True) as con:
        empresas = con.execute("""
            SELECT nome, url_vagas FROM dim_empresa
            WHERE ativa = true AND url_vagas IS NOT NULL AND url_vagas != ''
        """).fetchall()
    con.close()

    if not empresas:
        print("Nenhuma empresa ativa no banco.")
        return

    print(f"\n{len(empresas)} empresa(s) ativa(s)")

    for nome, url_vagas in empresas:
        print(f"\nProcessando {nome}...")
        if "gupy.io" in url_vagas:
            processar_empresa(nome, url_vagas)
        elif "greenhouse.io" in url_vagas:
            slug = url_vagas.split("greenhouse.io/")[-1].split("/")[0]
            processar_empresa_greenhouse(nome, slug)
        elif "inhire.app" in url_vagas:
            processar_empresa_inhire(nome, url_vagas)
        elif "smartrecruiters.com" in url_vagas:
            processar_empresa_smartrecruiters(nome, url_vagas)    
        else:
            print(f"  Plataforma não reconhecida: {url_vagas}")

    print("\nSalvando snapshot...")
    salvar_snapshot()
    print("\nPipeline concluído.")


if __name__ == "__main__":
    rodar_pipeline()