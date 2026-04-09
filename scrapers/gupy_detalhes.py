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
        print(f"Erro ao coletar descrição: {e}")
        return ""

def enriquecer_vagas(caminho_json: str):
    with open(caminho_json, "r", encoding="utf-8") as f:
        vagas = json.load(f)

    vagas_relevantes = [v for v in vagas if é_vaga_relevante(v["titulo"])]
    print(f"{len(vagas_relevantes)} vagas relevantes de {len(vagas)} coletadas")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for i, vaga in enumerate(vagas_relevantes):
            print(f"[{i+1}/{len(vagas_relevantes)}] Coletando: {vaga['titulo']}")
            vaga["descricao"] = coletar_descricao(page, vaga["link"])
            time.sleep(2)

        browser.close()

    with open("data/raw/vagas_enriquecidas.json", "w", encoding="utf-8") as f:
        json.dump(vagas_relevantes, f, ensure_ascii=False, indent=2)

    print(f"\nSalvo em data/raw/vagas_enriquecidas.json")
    return vagas_relevantes


if __name__ == "__main__":
    enriquecer_vagas("data/raw/vagas_gupy.json")