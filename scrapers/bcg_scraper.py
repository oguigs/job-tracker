from logger import get_logger
log = get_logger("bcg_scraper")
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import time
import random

_stealth = Stealth()

_BASE_URL = "https://careers.bcg.com/global/en/search-results?rk=l-brazil&sortBy=Most%20relevant"
_SITE_BASE = "https://careers.bcg.com"

_SEL_CARDS    = "li[data-ph-at-id='jobs-list-item']"
_SEL_LINK     = "a[href*='/job/']"
_SEL_LOCAL    = "[class*='location']"
_SEL_NEXT     = (
    "[data-ph-at-id='pagination-next-button'], "
    "a[aria-label*='Next'], button[aria-label*='Next'], "
    "a[class*='next'], button[class*='next']"
)
_SEL_DESCRICAO = (
    "[data-ph-at-id='job-description'], "
    "[class*='job-description'], [class*='jobDescription'], "
    "section[class*='description'], .description"
)


def _limpar_location(texto: str) -> str:
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    # remove a label "Location" se vier como primeira linha
    if linhas and linhas[0].lower() == "location":
        linhas = linhas[1:]
    return linhas[0] if linhas else ""


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
    termos_br = {
        "brazil", "brasil", "são paulo", "sao paulo", "rio de janeiro",
        "curitiba", "belo horizonte", "porto alegre", "campinas", "brasilia",
    }
    if any(t in loc for t in termos_br):
        return "br"
    return "br"  # URL já filtrada para Brazil


def _coletar_descricao(page, url: str) -> str:
    try:
        resp = page.goto(url, wait_until="load", timeout=45000)
        if resp and resp.status in (403, 429):
            log.warning(f"  Bloqueado ({resp.status})")
            return ""
        time.sleep(2)
        el = page.query_selector(_SEL_DESCRICAO)
        return el.inner_text().strip() if el else ""
    except Exception as e:
        log.error(f"  Erro descrição: {e}")
        return ""


def buscar_vagas_bcg(
    url_base: str = _BASE_URL,
    buscar_descricao: bool = True,
    headless: bool = True,
) -> list:
    """Coleta vagas do BCG Careers (Phenom People) via Playwright.

    Args:
        url_base: URL de busca já com filtros (ex: rk=l-brazil).
        buscar_descricao: Se True, visita cada vaga individualmente para descrição.
        headless: Se False, abre navegador visível (debug).
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
        _stealth.apply_stealth_sync(page)

        log.info("  Abrindo BCG Careers...")
        resp = page.goto(url_base, wait_until="load", timeout=90000)
        if not resp or resp.status not in (200, 304):
            log.error(f"  Erro HTTP {resp.status if resp else 'sem resposta'}")
            browser.close()
            return []

        time.sleep(5)

        try:
            page.wait_for_selector(_SEL_CARDS, timeout=30000)
        except Exception:
            log.warning("  Nenhum card encontrado após 30s")
            browser.close()
            return []

        pagina = 1
        while True:
            log.info(f"  Lendo página {pagina}...")
            cards = page.query_selector_all(_SEL_CARDS)

            for card in cards:
                link_el = card.query_selector(_SEL_LINK)
                if not link_el:
                    continue

                titulo = link_el.inner_text().strip()
                href = link_el.get_attribute("href") or ""
                link = href if href.startswith("http") else f"{_SITE_BASE}{href}"

                if not titulo or not link or link in links_vistos:
                    continue
                links_vistos.add(link)

                local_el = card.query_selector(_SEL_LOCAL)
                location_raw = local_el.inner_text() if local_el else ""
                location = _limpar_location(location_raw)

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

            # paginação: tenta botão "next"
            next_btn = page.query_selector(_SEL_NEXT)
            if next_btn and next_btn.is_visible() and not next_btn.is_disabled():
                try:
                    next_btn.scroll_into_view_if_needed()
                    next_btn.click()
                    page.wait_for_load_state("domcontentloaded")
                    time.sleep(random.uniform(2.0, 3.0))
                    pagina += 1
                    continue
                except Exception:
                    pass

            # fallback: scroll infinito
            total_antes = len(page.query_selector_all(_SEL_CARDS))
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(random.uniform(2.0, 3.0))
            total_depois = len(page.query_selector_all(_SEL_CARDS))
            if total_depois > total_antes:
                pagina += 1
            else:
                break

        log.info(f"  {len(vagas)} vagas na listagem")

        if buscar_descricao and vagas:
            log.info(f"  Coletando descrições ({len(vagas)} vagas)...")
            desc_page = context.new_page()
            _stealth.apply_stealth_sync(desc_page)

            for i, vaga in enumerate(vagas):
                log.info(f"  [{i+1}/{len(vagas)}] {vaga['titulo'][:55]}")
                desc = _coletar_descricao(desc_page, vaga["link"])
                vaga["descricao"] = desc
                if desc:
                    vaga["modalidade"] = _detectar_modalidade(
                        vaga["titulo"], vaga["cidade"], desc
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
