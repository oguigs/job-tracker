from logger import get_logger
log = get_logger("gupy_scraper")
import requests, re, json

def buscar_vagas(url_empresa: str) -> list:
    """
    Coleta vagas via __NEXT_DATA__ do Gupy — sem Playwright.
    Retorna lista com titulo, link, modalidade, fonte, empresa, cidade, pais.
    Descrições são preenchidas por coletar_descricoes_lote depois da filtragem.
    """
    nome_empresa = url_empresa.replace("https://", "").split(".gupy.io")[0]
    url_base = f"https://{nome_empresa}.gupy.io"

    try:
        r = requests.get(
            url_base,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
            timeout=15,
        )
        if r.status_code != 200:
            log.error(f"Erro ao acessar {url_base}: {r.status_code}")
            return []

        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            r.text, re.DOTALL
        )
        if not match:
            log.error(f"__NEXT_DATA__ não encontrado em {url_base}")
            return []

        data = json.loads(match.group(1))
        jobs = data.get("props", {}).get("pageProps", {}).get("jobs", [])

    except Exception as e:
        log.error(f"Erro ao coletar listing {url_base}: {e}")
        return []

    vagas = []
    for job in jobs:
        workplace   = job.get("workplace", {})
        wp_type     = (workplace.get("workplaceType") or "").lower()
        address     = workplace.get("address", {})

        modalidade = "não identificado"
        if wp_type in ("remote", "remoto"):
            modalidade = "remoto"
        elif wp_type == "hybrid":
            modalidade = "hibrido"
        elif wp_type in ("presential", "on-site", "presencial"):
            modalidade = "presencial"

        job_id = job.get("id", "")
        vagas.append({
            "titulo":    job.get("title", ""),
            "empresa":   nome_empresa.capitalize(),
            "link":      f"{url_base}/jobs/{job_id}?jobBoardSource=gupy_public_page",
            "modalidade": modalidade,
            "fonte":     "gupy",
            "cidade":    address.get("city", ""),
            "pais":      "br",
        })

    log.info(f"  {len(vagas)} vagas encontradas em {nome_empresa}")
    return vagas


if __name__ == "__main__":
    empresas = [
        "https://compass.gupy.io/",
        "https://ambev.gupy.io/",
        "https://localiza.gupy.io/",
    ]
    for url in empresas:
        vagas = buscar_vagas(url)
        log.info(f"{url}: {len(vagas)} vagas")
        for v in vagas[:3]:
            log.info(f"  - {v['titulo']}")
