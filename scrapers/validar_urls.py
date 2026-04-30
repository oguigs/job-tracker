import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

EMPRESAS = [
    # Financeiro / Bancário
    ("Itaú Unibanco", "https://itau.gupy.io/"),
    ("Bradesco", "https://bradesco.gupy.io/"),
    ("Santander", "https://santander.gupy.io/"),
    ("Banco do Brasil", "https://bb.gupy.io/"),
    ("Caixa Econômica Federal", "https://caixa.gupy.io/"),
    ("BTG Pactual", "https://btgpactual.gupy.io/"),
    ("XP Inc", "https://xp.gupy.io/"),
    ("Inter", "https://inter.gupy.io/"),
    ("C6 Bank", "https://c6bank.gupy.io/"),
    ("Neon", "https://neon.gupy.io/"),
    ("Modalmais", "https://modalmais.gupy.io/"),
    ("Warren", "https://warren.gupy.io/"),
    ("Órama", "https://orama.gupy.io/"),
    ("Daycoval", "https://daycoval.gupy.io/"),
    # Fintech / Pagamentos
    ("PicPay", "https://picpay.gupy.io/"),
    ("PagSeguro", "https://pagseguro.gupy.io/"),
    ("Stone", "https://stone.gupy.io/"),
    ("Cielo", "https://cielo.gupy.io/"),
    ("Dock", "https://dock.gupy.io/"),
    ("Pismo", "https://pismo.gupy.io/"),
    ("Conductor", "https://conductor.gupy.io/"),
    # Tecnologia
    ("Totvs", "https://totvs.gupy.io/"),
    ("CI&T", "https://ciandt.gupy.io/"),
    ("Stefanini", "https://stefanini.gupy.io/"),
    ("Compass UOL", "https://compass.gupy.io/"),
    ("Accenture", "https://accenture.gupy.io/"),
    ("Capgemini", "https://capgemini.gupy.io/"),
    ("Thoughtworks", "https://thoughtworks.gupy.io/"),
    ("Spread", "https://spread.gupy.io/"),
    # E-commerce / Varejo
    ("Mercado Livre", "https://mercadolivre.gupy.io/"),
    ("Magazine Luiza", "https://magazineluiza.gupy.io/"),
    ("Americanas", "https://americanas.gupy.io/"),
    ("VTEX", "https://vtex.gupy.io/"),
    ("Shopee", "https://shopee.gupy.io/"),
    ("Leroy Merlin", "https://leroymerlin.gupy.io/"),
    ("Riachuelo", "https://riachuelo.gupy.io/"),
    ("Grupo Boticário", "https://grupoboticario.gupy.io/"),
    # Logística / Mobilidade
    ("Loggi", "https://loggi.gupy.io/"),
    ("Movile", "https://movile.gupy.io/"),
    ("99", "https://99app.gupy.io/"),
    ("Sequoia Logística", "https://sequoia.gupy.io/"),
    ("Jadlog", "https://jadlog.gupy.io/"),
    # Saúde
    ("Hapvida", "https://hapvida.gupy.io/"),
    ("Dasa", "https://dasa.gupy.io/"),
    ("Fleury", "https://fleury.gupy.io/"),
    ("Einstein", "https://einstein.gupy.io/"),
    ("Rede D'Or", "https://redor.gupy.io/"),
    ("Alice Saúde", "https://alice.gupy.io/"),
    ("Pebmed", "https://pebmed.gupy.io/"),
    ("Prevent Senior", "https://preventsenior.gupy.io/"),
    ("Unimed", "https://unimed.gupy.io/"),
    # Educação
    ("Descomplica", "https://descomplica.gupy.io/"),
    ("Cogna", "https://cogna.gupy.io/"),
    ("Estácio", "https://estacio.gupy.io/"),
    ("Anima Educação", "https://animaeducacao.gupy.io/"),
    ("Hotmart", "https://hotmart.gupy.io/"),
    ("Alura", "https://alura.gupy.io/"),
    ("Rock Content", "https://rockcontent.gupy.io/"),
    ("EBAC", "https://ebac.gupy.io/"),
    # Telecom / Mídia
    ("Vivo", "https://vivo.gupy.io/"),
    ("Claro", "https://claro.gupy.io/"),
    ("TIM", "https://tim.gupy.io/"),
    ("Globo", "https://globo.gupy.io/"),
    ("UOL", "https://uol.gupy.io/"),
    # Agro / Energia / Indústria
    ("Raízen", "https://raizen.gupy.io/"),
    ("JBS", "https://jbs.gupy.io/"),
    ("BRF", "https://brf.gupy.io/"),
    ("Suzano", "https://suzano.gupy.io/"),
    ("Petrobras", "https://petrobras.gupy.io/"),
    ("Vale", "https://vale.gupy.io/"),
    ("Embraer", "https://embraer.gupy.io/"),
    ("Natura", "https://natura.gupy.io/"),
    ("Ambev", "https://ambev.gupy.io/"),
    # Esporte / Entretenimento
    ("Decathlon", "https://decathlon.gupy.io/"),
    ("Centauro", "https://centauro.gupy.io/"),
    ("Playkids", "https://playkids.gupy.io/"),
]


async def testar_url(page, nome, url):
    try:
        response = await page.goto(url, wait_until="networkidle", timeout=15000)
        status = response.status if response else 0

        if status == 404:
            return {"nome": nome, "url": url, "status": "inválida", "codigo": 404}
        if status != 200:
            return {"nome": nome, "url": url, "status": "erro", "codigo": status}

        # verifica se tem vagas listadas
        try:
            await page.wait_for_selector("a[href*='/job']", timeout=8000)
            total = len(await page.query_selector_all("a[href*='/job']"))
            return {"nome": nome, "url": url, "status": "válida", "codigo": 200, "vagas": total}
        except Exception:
            return {
                "nome": nome,
                "url": url,
                "status": "válida_sem_vagas",
                "codigo": 200,
                "vagas": 0,
            }

    except Exception as e:
        return {"nome": nome, "url": url, "status": "erro", "codigo": 0, "erro": str(e)[:80]}


async def validar_todas():
    resultados = []
    total = len(EMPRESAS)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for i, (nome, url) in enumerate(EMPRESAS):
            print(f"[{i + 1}/{total}] Testando {nome}...", end=" ")
            resultado = await testar_url(page, nome, url)
            resultados.append(resultado)
            status = resultado["status"]
            vagas = resultado.get("vagas", "—")
            print(f"{status} | vagas: {vagas}")

        await browser.close()

    validas = [r for r in resultados if r["status"] in ("válida", "válida_sem_vagas")]
    invalidas = [r for r in resultados if r["status"] == "inválida"]
    erros = [r for r in resultados if r["status"] == "erro"]

    print(f"\n{'=' * 50}")
    print(f"Válidas: {len(validas)} | Inválidas: {len(invalidas)} | Erros: {len(erros)}")
    print(f"{'=' * 50}")

    print("\nVálidas com vagas:")
    for r in sorted(validas, key=lambda x: x.get("vagas", 0), reverse=True):
        if r.get("vagas", 0) > 0:
            print(f"  {r['nome']} — {r['vagas']} vagas — {r['url']}")

    print("\nInválidas (URL não existe):")
    for r in invalidas:
        print(f"  {r['nome']} — {r['url']}")

    print("\nErros (site instável ou timeout):")
    for r in erros:
        print(f"  {r['nome']} — {r.get('erro', '')}")

    with open("data/raw/urls_validadas.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "data": datetime.now().isoformat(),
                "validas": validas,
                "invalidas": invalidas,
                "erros": erros,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print("\nResultado salvo em data/raw/urls_validadas.json")
    return validas


if __name__ == "__main__":
    asyncio.run(validar_todas())
