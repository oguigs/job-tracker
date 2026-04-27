from logger import get_logger
log = get_logger("doordash_scraper")
import requests
import html
import re

_URL_SITE = "https://careersatdoordash.com/job-search/?location=&spage=1"
_GH_SLUG  = "doordashinternational"

_TERMOS_BR = {
    "brazil", "brasil", "são paulo", "sao paulo", "rio de janeiro",
    "curitiba", "belo horizonte", "porto alegre", "campinas", "brasilia",
    "brasília", "fortaleza", "recife", "salvador", "manaus",
}


def _limpar_html(texto: str) -> str:
    return re.sub(r"<[^>]+>", " ", html.unescape(texto or "")).strip()


def _detectar_pais(location: str) -> str:
    loc = location.lower()
    if any(t in loc for t in _TERMOS_BR):
        return "br"
    if "remote" in loc or "worldwide" in loc or "global" in loc:
        return "br"
    return "other"


def _detectar_modalidade(titulo: str, location: str, descricao: str = "") -> str:
    texto = (titulo + " " + location + " " + descricao).lower()
    if "remote" in texto or "remoto" in texto:
        return "remoto"
    if "hybrid" in texto or "híbrido" in texto or "hibrido" in texto:
        return "hibrido"
    if "on-site" in texto or "presencial" in texto:
        return "presencial"
    return "não identificado"


def buscar_vagas_doordash() -> list:
    """Coleta vagas do DoorDash via Greenhouse API (backend de careersatdoordash.com).

    Tenta o board 'doordashinternational' primeiro (vagas fora dos EUA)
    e inclui vagas com localização Brazil ou remotas globais.
    """
    vagas = []
    try:
        r = requests.get(
            f"https://boards-api.greenhouse.io/v1/boards/{_GH_SLUG}/jobs?content=true",
            timeout=20,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json",
                "Referer": _URL_SITE,
            },
        )
        if r.status_code != 200:
            log.error(f"  Greenhouse DoorDash retornou {r.status_code}")
            return []

        jobs = r.json().get("jobs", [])
        log.info(f"  {len(jobs)} vagas brutas no board")

        for job in jobs:
            titulo    = job.get("title", "")
            link      = job.get("absolute_url", "")
            loc_obj   = job.get("location", {})
            location  = loc_obj.get("name", "") if isinstance(loc_obj, dict) else str(loc_obj)
            descricao = _limpar_html(job.get("content", ""))

            pais = _detectar_pais(location)
            if pais == "other":
                continue

            vagas.append({
                "titulo"    : titulo,
                "link"      : link,
                "modalidade": _detectar_modalidade(titulo, location, descricao),
                "fonte"     : "greenhouse",
                "empresa"   : "Doordash",
                "descricao" : descricao,
                "cidade"    : location,
                "pais"      : pais,
            })

        log.info(f"  {len(vagas)} vagas após filtro Brazil/remote")

    except Exception as e:
        log.error(f"  Erro DoorDash: {e}")

    return vagas


if __name__ == "__main__":
    import json

    vagas = buscar_vagas_doordash()
    log.info(f"{len(vagas)} vagas encontradas")
    for v in vagas[:10]:
        log.info(f"  - {v['titulo']} | {v['cidade']} | {v['modalidade']}")

    with open("data/raw/vagas_doordash.json", "w", encoding="utf-8") as f:
        json.dump(vagas, f, ensure_ascii=False, indent=2)
    log.info("Salvo em data/raw/vagas_doordash.json")
