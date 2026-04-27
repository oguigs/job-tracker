from logger import get_logger
log = get_logger("uber_scraper")
import requests
import time

_API_URL  = "https://www.uber.com/api/loadSearchJobsResults?localeCode=pt-BR"
_JOB_BASE = "https://www.uber.com/br/pt-br/careers/list"
_HEADERS  = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer"     : "https://www.uber.com/br/pt-br/careers/list/",
    "x-csrf-token": "x",
    "Content-Type": "application/json",
    "Accept"      : "application/json",
}

_PAYLOAD_BASE = {
    "limit" : 100,
    "page"  : 0,
    "params": {
        "department"        : [],
        "lineOfBusinessName": [],
        "location"          : [],
        "programAndPlatform": [],
        "team"              : [],
    },
}


def _detectar_modalidade(titulo: str, descricao: str) -> str:
    texto = (titulo + " " + descricao).lower()
    if "remote" in texto or "remoto" in texto or "100% remote" in texto:
        return "remoto"
    if "hybrid" in texto or "híbrido" in texto or "hibrido" in texto:
        return "hibrido"
    if "on-site" in texto or "on site" in texto or "presencial" in texto:
        return "presencial"
    return "não identificado"


def _e_brasil(job: dict) -> bool:
    """Retorna True se a vaga tem localização Brasil (primária ou alternativa)."""
    loc = job.get("location", {})
    if isinstance(loc, dict) and loc.get("country") == "BRA":
        return True
    for alt in job.get("allLocations", []):
        if isinstance(alt, dict) and alt.get("country") == "BRA":
            return True
    return False


def buscar_vagas_uber(url_base: str = _JOB_BASE, max_paginas: int = 30) -> list:
    """Coleta vagas do Uber para o Brasil via API JSON.

    Pagina todas as vagas globais e filtra as com localização BRA
    (primária ou entre as localizações alternativas).
    """
    vagas = []
    ids_vistos: set = set()

    for page in range(max_paginas):
        payload = {**_PAYLOAD_BASE, "page": page}
        try:
            r = requests.post(_API_URL, json=payload, headers=_HEADERS, timeout=20)
            if r.status_code != 200:
                log.error(f"  Uber API retornou {r.status_code} na página {page}")
                break

            data   = r.json().get("data", {})
            jobs   = data.get("results", [])
            total  = data.get("totalResults", {})
            total  = total.get("low", 0) if isinstance(total, dict) else int(total or 0)

            if not jobs:
                break

            log.info(f"  Página {page}: {len(jobs)} vagas brutas (total global: {total})")

            for job in jobs:
                job_id = job.get("id")
                if not job_id or job_id in ids_vistos:
                    continue
                if not _e_brasil(job):
                    continue

                ids_vistos.add(job_id)
                titulo    = job.get("title", "")
                descricao = job.get("description", "")
                loc       = job.get("location", {})
                cidade    = f"{loc.get('city', '')} - {loc.get('region', '')}".strip(" -")

                vagas.append({
                    "titulo"    : titulo,
                    "link"      : f"{_JOB_BASE}/{job_id}",
                    "modalidade": _detectar_modalidade(titulo, descricao),
                    "fonte"     : "desconhecida",
                    "empresa"   : "Uber",
                    "descricao" : descricao,
                    "cidade"    : cidade,
                    "pais"      : "br",
                })

            # Para se já vimos todas as vagas globais
            if len(ids_vistos) >= total or len(jobs) < 100:
                break

            time.sleep(0.5)

        except Exception as e:
            log.error(f"  Erro Uber página {page}: {e}")
            break

    log.info(f"  Total: {len(vagas)} vagas Brazil coletadas")
    return vagas


if __name__ == "__main__":
    import json

    vagas = buscar_vagas_uber()
    log.info(f"{len(vagas)} vagas encontradas")
    for v in vagas[:10]:
        log.info(f"  - {v['titulo']} | {v['cidade']} | {v['modalidade']}")

    with open("data/raw/vagas_uber.json", "w", encoding="utf-8") as f:
        json.dump(vagas, f, ensure_ascii=False, indent=2)
    log.info("Salvo em data/raw/vagas_uber.json")
