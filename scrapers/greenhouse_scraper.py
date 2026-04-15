from playwright.sync_api import sync_playwright
import re

def buscar_vagas_greenhouse(empresa_slug: str) -> list:
    """
    Coleta vagas do Greenhouse para uma empresa.
    URL padrão: https://boards.greenhouse.io/{empresa_slug}
    """
    url_base = f"https://boards.greenhouse.io/{empresa_slug}"
    vagas = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(url_base, wait_until="networkidle", timeout=30000)

            links = page.query_selector_all(f'a[href*="/{empresa_slug}/jobs/"]')

            for link in links:
                titulo = link.inner_text().strip()
                href = link.get_attribute("href")

                if not titulo or not href:
                    continue

                if not href.startswith("http"):
                    href = f"https://boards.greenhouse.io{href}"

                # detecta modalidade pelo título
                modalidade = "não identificado"
                titulo_lower = titulo.lower()
                if "remote" in titulo_lower or "remoto" in titulo_lower:
                    modalidade = "remoto"
                elif "hybrid" in titulo_lower or "híbrido" in titulo_lower:
                    modalidade = "hibrido"
                elif "on-site" in titulo_lower or "presencial" in titulo_lower:
                    modalidade = "presencial"

                vagas.append({
                    "titulo": titulo,
                    "link": href,
                    "modalidade": modalidade,
                    "fonte": "greenhouse",
                    "empresa": empresa_slug,
                })

        except Exception as e:
            print(f"Erro ao coletar {empresa_slug}: {e}")
        finally:
            browser.close()

    return vagas


if __name__ == "__main__":
    vagas = buscar_vagas_greenhouse("nubank")
    print(f"{len(vagas)} vagas encontradas")
    for v in vagas[:5]:
        print(f"  - {v['titulo']}")