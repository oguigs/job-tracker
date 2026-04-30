from logger import get_logger

log = get_logger("amaris_scraper")
import html
import re
import requests

_MEILI_URL = "https://meilisearch.7circles.com/indexes/prod_amaca_job_offers_index/search"
_MEILI_KEY = "s5o3zahr43aee3f0db2872e64015ce872f2c523910b11cf67b997f3b49473905581ec71e"
_JOB_BASE = "https://careers.amaris.com/jobs"
_PAGE_SIZE = 100
_HEADERS = {"Authorization": f"Bearer {_MEILI_KEY}", "Content-Type": "application/json"}

# Localização que representa "qualquer cidade do Brasil" no índice
_BRASIL_LOCATION = "Brazil > Brazil"


def _limpar_html(texto: str) -> str:
    sem_tags = re.sub(r"<[^>]+>", " ", texto or "")
    return re.sub(r"\s+", " ", html.unescape(sem_tags)).strip()


def _detectar_modalidade(titulo: str, descricao: str, locations: list) -> str:
    texto = " ".join([titulo, descricao[:500]] + locations).lower()
    if "remote" in texto or "remoto" in texto or "100% remote" in texto:
        return "remoto"
    if "hybrid" in texto or "híbrido" in texto or "hibrido" in texto:
        return "hibrido"
    return "não identificado"


def _extrair_cidade(locations: list) -> str:
    """Retorna a cidade mais específica, ignorando o marcador 'Brazil > Brazil'."""
    for loc in locations:
        if loc != _BRASIL_LOCATION and loc.startswith("Brazil > "):
            return loc.replace("Brazil > ", "").strip()
    return "Brasil"


def _buscar_pagina(offset: int) -> dict:
    payload = {
        "q": "",
        "limit": _PAGE_SIZE,
        "offset": offset,
        "filter": f'locations = "{_BRASIL_LOCATION}"',
    }
    r = requests.post(_MEILI_URL, json=payload, headers=_HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


def buscar_vagas_amaris() -> list:
    vagas = []
    offset = 0

    try:
        primeira = _buscar_pagina(0)
        total = primeira.get("nbHits") or primeira.get("estimatedTotalHits") or 0
        log.info(f"  Amaris: {total} vagas no Brasil")

        paginas = [primeira] + [_buscar_pagina(off) for off in range(_PAGE_SIZE, total, _PAGE_SIZE)]

        for pagina in paginas:
            for job in pagina.get("hits", []):
                titulo = job.get("title", "")
                descricao = _limpar_html(job.get("description", ""))
                locations = job.get("locations", [])
                cidade = _extrair_cidade(locations)
                link = f"{_JOB_BASE}/{job['id']}"
                modalidade = _detectar_modalidade(titulo, descricao, locations)

                vagas.append(
                    {
                        "titulo": titulo,
                        "link": link,
                        "modalidade": modalidade,
                        "fonte": "amaris",
                        "empresa": "Amaris Consulting",
                        "descricao": descricao,
                        "cidade": cidade,
                        "pais": "br",
                    }
                )

    except Exception as e:
        log.error(f"  Erro Amaris: {e}")

    log.info(f"  {len(vagas)} vagas coletadas")
    return vagas


if __name__ == "__main__":
    vagas = buscar_vagas_amaris()
    for v in vagas:
        log.info(f"  - {v['titulo']} | {v['cidade']} | {v['modalidade']}")
