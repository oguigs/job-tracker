from logger import get_logger
log = get_logger("inhire_scraper")
from playwright.sync_api import sync_playwright
import re, time, random


def _limpar_html(txt: str) -> str:
    import html as html_lib
    return re.sub(r"<[^>]+>", " ", html_lib.unescape(txt or "")).strip()


def _coletar_descricao_inhire(page, url: str) -> str:
    """Extrai descrição de uma vaga InHire via Playwright."""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(2000)
        # InHire renders description in a div with common class patterns
        for sel in [
            "[class*='description']",
            "[class*='vacancy-body']",
            "[class*='job-description']",
            "main article",
            "main section",
        ]:
            el = page.query_selector(sel)
            if el:
                txt = el.inner_text().strip()
                if len(txt) > 50:
                    return txt
        # Fallback: grab all visible text from main
        main = page.query_selector("main")
        return main.inner_text().strip() if main else ""
    except Exception as e:
        log.error(f"  Erro descrição InHire: {e}")
        return ""


def buscar_vagas_inhire(url_base: str) -> list:
    vagas = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url_base, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)
            links = page.query_selector_all('a[href*="/vagas/"]')
            dominio = url_base.split("/")[2]

            for link in links:
                href = link.get_attribute("href")
                titulo = link.inner_text().strip()
                if not href or not titulo or href.rstrip("/") == url_base.rstrip("/"):
                    continue
                url_completa = f"https://{dominio}{href}" if href.startswith("/") else href

                modalidade = "não identificado"
                titulo_lower = titulo.lower()
                if "remoto" in titulo_lower or "remote" in titulo_lower:
                    modalidade = "remoto"
                elif "híbrido" in titulo_lower or "hybrid" in titulo_lower:
                    modalidade = "hibrido"
                elif "presencial" in titulo_lower:
                    modalidade = "presencial"

                vagas.append({
                    "titulo":    titulo.split(" -> ")[0].strip(),
                    "link":      url_completa,
                    "modalidade": modalidade,
                    "fonte":     "inhire",
                    "empresa":   dominio.split(".")[0],
                    "cidade":    "",
                    "pais":      "br",
                })

            log.info(f"  {len(vagas)} vagas encontradas — coletando descrições...")

            for i, vaga in enumerate(vagas):
                desc = _coletar_descricao_inhire(page, vaga["link"])
                vaga["descricao"] = desc
                status = f"✓ {len(desc)}ch" if desc else "✗ sem desc"
                log.info(f"  [{i+1}/{len(vagas)}] {status} — {vaga['titulo'][:45]}")
                time.sleep(random.uniform(0.5, 1.2))

        except Exception as e:
            log.error(f"Erro InHire {url_base}: {e}")
        finally:
            browser.close()
    return vagas


if __name__ == "__main__":
    vagas = buscar_vagas_inhire("https://pravaler.inhire.app/vagas")
    log.info(f"{len(vagas)} vagas encontradas")
    for v in vagas[:5]:
        log.info(f"  - {v['titulo']} | {len(v.get('descricao',''))} chars")
