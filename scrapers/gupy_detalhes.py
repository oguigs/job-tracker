from logger import get_logger
log = get_logger("gupy_detalhes")
from playwright.sync_api import sync_playwright
import json
import time

CARGOS_RELEVANTES = [
    "data engineer",
    "engenheiro de dados",
    "analytics engineer",
    "data analyst",
    "analista de dados",
    "data scientist",
    "engenheiro de dados",
]

def é_vaga_relevante(titulo: str) -> bool:
    titulo_lower = titulo.lower()
    return any(cargo in titulo_lower for cargo in CARGOS_RELEVANTES)

def coletar_descricao(page, url: str) -> str:
    try:
        page.goto(url, wait_until="networkidle")
        page.wait_for_selector("[class*='description'], [class*='jobDescription'], section", timeout=10000)
        descricao = page.query_selector("[class*='description'], [class*='jobDescription'], section")
        return descricao.inner_text().strip() if descricao else ""
    except Exception as e:
        log.error(f"Erro ao coletar descrição: {e}")
        return ""

def enriquecer_vagas(caminho_json: str):
    from database.filtros import carregar_filtros

    with open(caminho_json, "r", encoding="utf-8") as f:
        vagas = json.load(f)

    interesse, bloqueio = carregar_filtros()

    def titulo_relevante(titulo: str) -> bool:
        titulo_lower = titulo.lower()
        # se tem termo de bloqueio, descarta
        if any(b in titulo_lower for b in bloqueio):
            return False
        # se não tem nenhum termo de interesse, descarta
        if interesse and not any(i in titulo_lower for i in interesse):
            return False
        return True

    vagas_relevantes = [v for v in vagas if titulo_relevante(v["titulo"])]
    log.info(f"{len(vagas_relevantes)} vagas relevantes de {len(vagas)} coletadas")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for i, vaga in enumerate(vagas_relevantes):
            log.info(f"[{i+1}/{len(vagas_relevantes)}] Coletando: {vaga['titulo']}")
            vaga["descricao"] = coletar_descricao(page, vaga["link"])
            time.sleep(2)

        browser.close()

    with open("data/raw/vagas_enriquecidas.json", "w", encoding="utf-8") as f:
        json.dump(vagas_relevantes, f, ensure_ascii=False, indent=2)

    log.info(f"\nSalvo em data/raw/vagas_enriquecidas.json")
    return vagas_relevantes


if __name__ == "__main__":
    enriquecer_vagas("data/raw/vagas_gupy.json")

def coletar_descricoes_lote(vagas: list, headless: bool = True) -> list:
    """
    Coleta descrições de uma lista de vagas usando Playwright.
    Retorna a mesma lista com campo 'descricao' preenchido.
    Extrai stacks, nível e urgência de cada descrição.
    """
    from playwright.sync_api import sync_playwright
    from playwright_stealth import stealth as stealth_sync
    from transformers.stack_extractor import extrair_stacks, detectar_nivel, detectar_urgencia
    import random, time

    if not vagas:
        return vagas

    log.info(f"  Coletando descrições de {len(vagas)} vagas...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        stealth_sync(page)

        for i, vaga in enumerate(vagas):
            try:
                response = page.goto(vaga["link"], wait_until="networkidle", timeout=60000)
                if response and response.status in [403, 429]:
                    log.warning(f"  Bloqueado ({response.status}): {vaga['titulo'][:40]}")
                    continue

                content = page.content()
                if "cloudflare" in content.lower() and "checking your browser" in content.lower():
                    log.info(f"  Cloudflare detectado: {vaga['titulo'][:40]}")
                    continue

                page.wait_for_selector(
                    "[class*='description'], [class*='jobDescription'], section, .job-description",
                    timeout=8000
                )
                el = page.query_selector(
                    "[class*='description'], [class*='jobDescription'], section, .job-description"
                )
                descricao = el.inner_text().strip() if el else ""
                vaga["descricao"] = descricao

                if descricao:
                    stacks_desc = extrair_stacks(descricao)
                    for cat, termos in stacks_desc.items():
                        if cat in vaga.get("stacks", {}):
                            vaga["stacks"][cat] = list(set(vaga["stacks"][cat] + termos))
                        else:
                            if "stacks" not in vaga:
                                vaga["stacks"] = {}
                            vaga["stacks"][cat] = termos
                    vaga["urgente"] = detectar_urgencia(descricao, vaga.get("titulo", ""))

                time.sleep(random.uniform(1.5, 3.0))

            except Exception as e:
                log.error(f"  Erro descrição {vaga['titulo'][:40]}: {e}")
                continue

        browser.close()

    log.info(f"  Descrições coletadas.")
    return vagas
