from playwright.sync_api import sync_playwright
import json
import time

def buscar_vagas(url_empresa: str):
    vagas = []
    nome_empresa = url_empresa.replace("https://", "").split(".gupy.io")[0].capitalize()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"Abrindo página de {nome_empresa}...")
        response = page.goto(url_empresa, wait_until="networkidle", timeout=60000)

        if response.status == 404:
            print(f"Página não encontrada: {url_empresa}")
            browser.close()
            return []

        if response.status != 200:
            print(f"Erro ao acessar {url_empresa}: status {response.status}")
            browser.close()
            return []

        print("Aguardando vagas carregarem...")
        page.wait_for_selector("a[href*='/job']", timeout=15000)

        pagina_atual = 1

        while True:
            print(f"  Coletando página {pagina_atual}...")

            cards = page.query_selector_all("a[href*='/job']")
            dominio = url_empresa.rstrip("/")

            for card in cards:
                titulo_elemento = card.query_selector("h3, h2, [class*='title'], [class*='name']")
                texto_completo = titulo_elemento.inner_text().strip() if titulo_elemento else card.inner_text().strip()

                linhas = [l.strip() for l in texto_completo.split("\n") if l.strip()]
                titulo = linhas[0] if linhas else ""

                modalidade = "não identificado"
                for linha in linhas[1:]:
                    linha_lower = linha.lower()
                    if "remoto" in linha_lower or "remote" in linha_lower:
                        modalidade = "remoto"
                        break
                    if "híbrido" in linha_lower or "hibrido" in linha_lower:
                        modalidade = "hibrido"
                        break
                    if "presencial" in linha_lower:
                        modalidade = "presencial"
                        break

                href = card.get_attribute("href")
                link = f"{dominio}{href}" if href and href.startswith("/") else href

                if titulo and link not in [v["link"] for v in vagas]:
                    vagas.append({
                        "titulo": titulo,
                        "empresa": nome_empresa,
                        "link": link,
                        "modalidade": modalidade,
                        "fonte": "gupy"
                    })

            # tenta ir para próxima página
            proxima = page.query_selector(
                "button[data-testid='pagination-next-button']:not([disabled]):not([aria-disabled='true'])"
            )
      

            if proxima:
                try:
                    proxima.click()
                    page.wait_for_load_state("networkidle")
                    time.sleep(2)
                    pagina_atual += 1
                except:
                    break
            else:
                # tenta scroll para sites com carregamento infinito
                total_antes = len(page.query_selector_all("a[href*='/job']"))
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                total_depois = len(page.query_selector_all("a[href*='/job']"))

                if total_depois > total_antes:
                    pagina_atual += 1
                else:
                    break

        print(f"{len(vagas)} vagas encontradas no total")
        browser.close()

    return vagas


if __name__ == "__main__":
    empresas = [
        "https://compass.gupy.io/",
        "https://ambev.gupy.io/",
        "https://globo.gupy.io/",
    ]

    todas_vagas = []

    for url in empresas:
        try:
            vagas = buscar_vagas(url)
            todas_vagas.extend(vagas)
        except Exception as e:
            print(f"Erro em {url}: {e}")

    print(f"\nTotal: {len(todas_vagas)} vagas coletadas")

    with open("data/raw/vagas_gupy.json", "w", encoding="utf-8") as f:
        json.dump(todas_vagas, f, ensure_ascii=False, indent=2)
    print("Salvo em data/raw/vagas_gupy.json")