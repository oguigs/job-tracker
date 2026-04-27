from logger import get_logger
log = get_logger("lever_scraper")
import requests
import re

_API_BASE = "https://api.lever.co/v0/postings"
_SITE_BASE = "https://jobs.lever.co"
_HEADERS   = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

_TERMOS_BR = {
    "brazil", "brasil", "são paulo", "sao paulo", "rio de janeiro",
    "curitiba", "belo horizonte", "porto alegre", "campinas", "brasilia",
    "brasília", "fortaleza", "recife", "salvador",
}


def _limpar_html(texto: str) -> str:
    return re.sub(r"<[^>]+>", " ", texto or "").strip()


def _e_brasil(job: dict) -> bool:
    """Retorna True se a vaga é para o Brasil (primária ou alternativa)."""
    if job.get("country", "").upper() == "BR":
        return True
    loc = str(job.get("categories", {}).get("location", "")).lower()
    if any(t in loc for t in _TERMOS_BR):
        return True
    for alt in job.get("categories", {}).get("allLocations", []):
        if any(t in str(alt).lower() for t in _TERMOS_BR):
            return True
    return False


def _cidade_brasil(job: dict) -> str:
    """Retorna a localização Brasil mais específica disponível no job."""
    loc_primary = job.get("categories", {}).get("location", "")
    if any(t in loc_primary.lower() for t in _TERMOS_BR):
        return loc_primary
    for alt in job.get("categories", {}).get("allLocations", []):
        if any(t in str(alt).lower() for t in _TERMOS_BR):
            # Limpar sufixos como "(Hybrid)"
            return str(alt).replace("(Hybrid)", "").replace("(hybrid)", "").strip()
    return loc_primary


def _detectar_modalidade(job: dict) -> str:
    workplace = job.get("workplaceType", "").lower()
    if workplace == "remote":
        return "remoto"
    if workplace == "hybrid":
        return "hibrido"
    if workplace == "on-site":
        return "presencial"
    # fallback via texto
    texto = (
        job.get("text", "") + " " +
        str(job.get("categories", {}).get("location", "")) + " " +
        str(job.get("descriptionPlain", ""))[:300]
    ).lower()
    if "remote" in texto or "remoto" in texto:
        return "remoto"
    if "hybrid" in texto or "híbrido" in texto:
        return "hibrido"
    return "não identificado"


def buscar_vagas_lever(slug: str, empresa: str, filtrar_brasil: bool = True) -> list:
    """Coleta vagas de uma empresa no Lever via API pública.

    Args:
        slug: Identificador da empresa no Lever (ex: "cloudwalk", "dlocal").
        empresa: Nome da empresa para preencher o campo `empresa` nas vagas.
        filtrar_brasil: Se True, retorna apenas vagas com localização Brasil.
    """
    vagas = []
    try:
        r = requests.get(
            f"{_API_BASE}/{slug}",
            params={"mode": "json"},
            headers=_HEADERS,
            timeout=15,
        )
        if r.status_code == 404:
            log.error(f"  Lever slug não encontrado: {slug!r}")
            return []
        if r.status_code != 200:
            log.error(f"  Lever {slug}: HTTP {r.status_code}")
            return []

        jobs = r.json()
        log.info(f"  {len(jobs)} vagas brutas no board {slug!r}")

        for job in jobs:
            if filtrar_brasil and not _e_brasil(job):
                continue

            titulo   = job.get("text", "")
            location = _cidade_brasil(job) if filtrar_brasil else job.get("categories", {}).get("location", "")
            link     = job.get("hostedUrl", "") or f"{_SITE_BASE}/{slug}/{job.get('id', '')}"
            descricao = job.get("descriptionPlain", "") or _limpar_html(job.get("description", ""))

            vagas.append({
                "titulo"    : titulo,
                "link"      : link,
                "modalidade": _detectar_modalidade(job),
                "fonte"     : "desconhecida",
                "empresa"   : empresa,
                "descricao" : descricao,
                "cidade"    : location,
                "pais"      : "br",
            })

        log.info(f"  {len(vagas)} vagas após filtro{'  Brasil' if filtrar_brasil else ''}")

    except Exception as e:
        log.error(f"  Erro Lever {slug}: {e}")

    return vagas


if __name__ == "__main__":
    import json

    for slug, nome in [("cloudwalk", "CloudWalk"), ("dlocal", "dLocal")]:
        vagas = buscar_vagas_lever(slug, nome)
        log.info(f"\n{nome}: {len(vagas)} vagas")
        for v in vagas[:5]:
            log.info(f"  - {v['titulo']} | {v['cidade']} | {v['modalidade']}")

    with open("data/raw/vagas_lever.json", "w", encoding="utf-8") as f:
        json.dump(vagas, f, ensure_ascii=False, indent=2)
    log.info("\nSalvo em data/raw/vagas_lever.json")
