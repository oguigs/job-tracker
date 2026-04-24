from logger import get_logger
log = get_logger("bcg_scraper")
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth as stealth_sync
import re
import time
import random

_BASE_URL = "https://careers.bcg.com/global/en/search-results?rk=l-brazil&sortBy=Most%20relevant"
_SITE_BASE = "https://careers.bcg.com"

# Seletores Phenom People com fallbacks
_SEL_CARDS = "[data-ph-at-id='job-item'], li[class*='job-section'], li[class*='job-item']"
_SEL_TITULO = "[data-ph-at-id='job-title-link'], a[class*='title'], h2 a, h3 a"
_SEL_LOCAL   = "[data-ph-at-id='job-location'], [class*='location'], [class*='city']"
_SEL_LOAD_MORE = (
    "[data-ph-at-id='search-load-more-button'], "
    "button[class*='load-more'], button[class*='loadMore'], "
    "a[class*='load-more']"
)
_SEL_DESCRICAO = (
    "[data-ph-at-id='job-description'], "
    "[class*='job-description'], [class*='jobDescription'], "
    "section[class*='description']"
)


def _detectar_modalidade(titulo: str, location: str, descricao: str = "") -> str:
    texto = (titulo + " " + location + " " + descricao).lower()
    if "remote" in texto or "remoto" in texto:
        return "remoto"
    if "hybrid" in texto or "híbrido" in texto or "hibrido" in texto:
        return "hibrido"
    if "on-site" in texto or "on site" in texto or "presencial" in texto:
        return "presencial"
    return "não identificado"


def _detectar_pais(location: str) -> str:
    loc = location.lower()
    termos_br = {"brazil", "brasil", "são paulo", "sao paulo", "rio de janeiro",
                 "curitiba", "belo horizonte", "porto alegre", "campinas", "brasilia"}
    if any(t in loc for t in termos_br):
        return "br"
    if loc:
        return "other"
    return "br"  # URL já filtrada para Brazil


def _coletar_descricao(page, url: str) -> str:
    try:
        resp = page.goto(url, wait_until="domcontentloaded", timeout=30000)
        if resp and resp.status in (403, 429):
            log.warning(f"  Bloqueado ({resp.status}) em {url}")
            return ""
        page.wait_for_selector(_SEL_DESCRICAO, timeout=10000)
        el = page.query_selector(_SEL_DESCRICAO)
        return el.inner_text().strip() if el else ""
    except Exception as e:
        log.error(f"  Erro ao coletar descrição: {e}")
        return ""


def buscar_vagas_bcg(
    url_base: str = _BASE_URL,
    buscar_descricao: bool = True,
    headless: bool = True,
) -> list:
    """Coleta vagas do portal BCG Careers (Phenom People) via Playwright.

    Args:
        url_base: URL de busca com filtros já aplicados.
        buscar_descricao: Se True, visita cada vaga para coletar descrição completa.
        headless: Se False, abre o navegador visível (útil para debug).
    """
    vagas = []
    links_vistos = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1440, "height": 900},
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
        )
        page = context.new_page()
        stealth_sync(page)

        log.info(f"  Abrindo BCG Careers...")
        resp = page.goto(url_base, wait_until="networkidle", timeout=60000)
        if not resp or resp.status not in (200, 304):
            log.error(f"  Erro ao acessar BCG Careers: status {resp.status if resp else 'sem resposta'}")
            browser.close()
            return []

        # aguarda primeiro lote de cards carregar
        try:
            page.wait_for_selector(_SEL_CARDS, timeout=20000)
        except Exception:
            log.warning("  Nenhum card de vaga encontrado no seletor primário")
            browser.close()
            return []

        rodada = 1
        while True:
            log.info(f"  Lendo página {rodada}...")
            cards = page.query_selector_all(_SEL_CARDS)

            for card in cards:
                # título e link
                titulo_el = card.query_selector(_SEL_TITULO)
                if not titulo_el:
                    continue
                titulo = titulo_el.inner_text().strip()
                href = titulo_el.get_attribute("href") or ""
                link = f"{_SITE_BASE}{href}" if href.startswith("/") else href

                if not titulo or not link or link in links_vistos:
                    continue
                links_vistos.add(link)

                # localização
                local_el = card.query_selector(_SEL_LOCAL)
                location = local_el.inner_text().strip() if local_el else ""

                vagas.append({
                    "titulo": titulo,
                    "link": link,
                    "modalidade": _detectar_modalidade(titulo, location),
                    "fonte": "bcg",
                    "empresa": "BCG",
                    "descricao": "",
                    "cidade": location,
                    "pais": _detectar_pais(location),
                })

            # tenta carregar mais vagas
            load_more = page.query_selector(_SEL_LOAD_MORE)
            if load_more and load_more.is_visible() and not load_more.is_disabled():
                try:
                    load_more.scroll_into_view_if_needed()
                    load_more.click()
                    page.wait_for_load_state("networkidle")
                    time.sleep(random.uniform(1.5, 2.5))
                    rodada += 1
                except Exception:
                    break
            else:
                # tenta scroll para carregamento infinito
                total_antes = len(page.query_selector_all(_SEL_CARDS))
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(random.uniform(1.5, 2.5))
                total_depois = len(page.query_selector_all(_SEL_CARDS))
                if total_depois > total_antes:
                    rodada += 1
                else:
                    break

        log.info(f"  {len(vagas)} vagas na listagem")

        # coleta descrições visitando cada vaga individualmente
        if buscar_descricao and vagas:
            log.info(f"  Coletando descrições ({len(vagas)} vagas)...")
            desc_page = context.new_page()
            stealth_sync(desc_page)

            for i, vaga in enumerate(vagas):
                log.info(f"  [{i+1}/{len(vagas)}] {vaga['titulo'][:50]}")
                descricao = _coletar_descricao(desc_page, vaga["link"])
                vaga["descricao"] = descricao
                if descricao:
                    vaga["modalidade"] = _detectar_modalidade(
                        vaga["titulo"], vaga["cidade"], descricao
                    )
                time.sleep(random.uniform(2.0, 3.5))

            desc_page.close()

        browser.close()

    log.info(f"  Total: {len(vagas)} vagas coletadas")
    return vagas


if __name__ == "__main__":
    import json

    vagas = buscar_vagas_bcg(buscar_descricao=False)
    log.info(f"{len(vagas)} vagas encontradas")
    for v in vagas[:10]:
        log.info(f"  - [{v['pais']}] {v['titulo']} | {v['cidade']} | {v['modalidade']}")

    with open("data/raw/vagas_bcg.json", "w", encoding="utf-8") as f:
        json.dump(vagas, f, ensure_ascii=False, indent=2)
    log.info("Salvo em data/raw/vagas_bcg.json")
