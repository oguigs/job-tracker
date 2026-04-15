from playwright.sync_api import sync_playwright

def buscar_vagas_inhire(url_base: str) -> list:
    """
    Coleta vagas do Inhire.
    url_base ex: https://alelo.inhire.app/veloe/vagas
    """
    vagas = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(url_base, wait_until="networkidle", timeout=30000)
            links = page.query_selector_all('a[href*="/vagas/"]')

            base = url_base.split("/vagas")[0]
            dominio = url_base.split("/")[2]

            for link in links:
                href = link.get_attribute("href")
                titulo = link.inner_text().strip()

                if not href or not titulo or href.endswith("/vagas"):
                    continue

                # filtra só vagas reais (com UUID)
                partes = href.split("/")
                if len(partes) < 4:
                    continue

                url_completa = f"https://{dominio}{href}"

                modalidade = "não identificado"
                titulo_lower = titulo.lower()
                if "remoto" in titulo_lower or "remote" in titulo_lower:
                    modalidade = "remoto"
                elif "híbrido" in titulo_lower or "hybrid" in titulo_lower:
                    modalidade = "hibrido"
                elif "presencial" in titulo_lower:
                    modalidade = "presencial"

                vagas.append({
                    "titulo": titulo.split(" -> ")[0].strip(),
                    "link": url_completa,
                    "modalidade": modalidade,
                    "fonte": "inhire",
                    "empresa": dominio.split(".")[0],
                })

        except Exception as e:
            print(f"Erro Inhire {url_base}: {e}")
        finally:
            browser.close()

    return vagas


if __name__ == "__main__":
    vagas = buscar_vagas_inhire("https://alelo.inhire.app/veloe/vagas")
    print(f"{len(vagas)} vagas encontradas")
    for v in vagas[:5]:
        print(f"  - {v['titulo']}")