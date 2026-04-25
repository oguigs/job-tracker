from logger import get_logger
log = get_logger("amazon_scraper")
import requests
import html
import re
import time

_BASE_URL = "https://www.amazon.jobs/en/search.json"
_JOB_BASE = "https://www.amazon.jobs"

_PAISES_BR = {
    "brazil", "brasil", "são paulo", "sao paulo", "rio de janeiro",
    "curitiba", "belo horizonte", "porto alegre", "campinas", "brasilia",
    "brasília", "fortaleza", "recife", "salvador", "manaus",
}

_PAISES_OUTROS = {
    "united states", "usa", "us", "india", "china", "uk", "canada",
    "mexico", "argentina", "colombia", "singapore", "germany", "france",
    "spain", "luxembourg", "ireland", "japan", "australia",
}


def _limpar_html(texto: str) -> str:
    return re.sub(r"<[^>]+>", " ", html.unescape(texto or "")).strip()


def _detectar_pais(location: str, country_code: str) -> str:
    loc = location.lower()
    code = (country_code or "").lower()

    if code == "br" or any(p in loc for p in _PAISES_BR):
        return "br"
    if any(p in loc for p in _PAISES_OUTROS):
        return "other"
    return ""


def _detectar_modalidade(titulo: str, descricao: str, location: str) -> str:
    texto = (titulo + " " + descricao + " " + location).lower()
    if "100% remote" in texto or "fully remote" in texto or "remoto" in texto:
        return "remoto"
    if "hybrid" in texto or "híbrido" in texto or "hibrido" in texto:
        return "hibrido"
    if "on-site" in texto or "on site" in texto or "presencial" in texto:
        return "presencial"
    return "não identificado"


def buscar_vagas_amazon(loc_query: str = "Brazil", base_query: str = "", result_limit: int = 100) -> list:
    """Busca vagas na Amazon Jobs via API JSON pública.

    Args:
        loc_query: Localização de busca (ex: "Brazil", "São Paulo").
        base_query: Termo de busca adicional (ex: "data engineer").
        result_limit: Vagas por página (máx. 100).
    """
    vagas = []
    offset = 0

    while True:
        try:
            params = {
                "base_query": base_query,
                "loc_query": loc_query,
                "result_limit": result_limit,
                "offset": offset,
            }
            resp = requests.get(_BASE_URL, params=params, timeout=20, headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Referer": "https://www.amazon.jobs/",
            })

            if resp.status_code != 200:
                log.error(f"  Amazon Jobs retornou status {resp.status_code}")
                break

            data = resp.json()
            jobs = data.get("jobs", [])
            if not jobs:
                break

            for job in jobs:
                titulo = job.get("title", "")
                job_path = job.get("job_path", "")
                link = f"{_JOB_BASE}{job_path}" if job_path else ""
                location = job.get("location", "")
                city = job.get("city", "")
                country_code = job.get("country_code", "")

                descricao_raw = job.get("description", "") or job.get("description_short", "")
                descricao = _limpar_html(descricao_raw)

                vagas.append({
                    "titulo": titulo,
                    "link": link,
                    "modalidade": _detectar_modalidade(titulo, descricao, location),
                    "fonte": "amazon",
                    "empresa": "Amazon",
                    "descricao": descricao,
                    "cidade": city or location,
                    "pais": _detectar_pais(location, country_code),
                })

            log.info(f"  Coletadas {len(vagas)} vagas (offset={offset})")

            total = data.get("hits", 0)
            offset += result_limit
            if offset >= total:
                break

            time.sleep(1.5)

        except Exception as e:
            log.error(f"  Erro Amazon Jobs: {e}")
            break

    log.info(f"  Total: {len(vagas)} vagas encontradas")
    return vagas


if __name__ == "__main__":
    import json

    vagas = buscar_vagas_amazon(loc_query="Brazil")
    log.info(f"{len(vagas)} vagas encontradas")
    for v in vagas[:10]:
        log.info(f"  - [{v['pais']}] {v['titulo']} | {v['cidade']} | {v['modalidade']}")

    with open("data/raw/vagas_amazon.json", "w", encoding="utf-8") as f:
        json.dump(vagas, f, ensure_ascii=False, indent=2)
    log.info("Salvo em data/raw/vagas_amazon.json")
