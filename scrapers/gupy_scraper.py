from playwright.sync_api import sync_playwright
import json

def buscar_vagas(url_empresa: str):
    """
    Funciona para qualquer empresa no Gupy.
    Exemplos:
        buscar_vagas("https://compass.gupy.io/")
        buscar_vagas("https://nubank.gupy.io/")
        buscar_vagas("https://ifood.gupy.io/")
    """
    vagas = []
    nome_empresa = url_empresa.replace("https://", "").split(".gupy.io")[0].capitalize()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"Abrindo página de {nome_empresa}...")
        response = page.goto(url_empresa, wait_until="networkidle")

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

        cards = page.query_selector_all("a[href*='/job']")
        print(f"{len(cards)} vagas encontradas")

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
            link = f"{dominio}{href}" if href.startswith("/") else href

            if titulo:
                vagas.append({
                    "titulo": titulo,
                    "empresa": nome_empresa,
                    "link": link,
                    "modalidade": modalidade,
                    "fonte": "gupy"
                })

        browser.close()

    return vagas


if __name__ == "__main__":
    empresas = [
        "https://compass.gupy.io/",
        "https://nubank.gupy.io/",
        "https://ifood.gupy.io/",
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