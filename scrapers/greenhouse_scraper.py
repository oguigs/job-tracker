from logger import get_logger
log = get_logger("greenhouse_scraper")
from playwright.sync_api import sync_playwright
import re

import requests, html, re

def limpar_html(texto):
    return re.sub('<[^>]+>', ' ', html.unescape(texto or ''))

def buscar_vagas_greenhouse(empresa_slug: str) -> list:
    vagas = []
    try:
        r = requests.get(
            f"https://boards-api.greenhouse.io/v1/boards/{empresa_slug}/jobs?content=true",
            timeout=15
        )
        if r.status_code != 200:
            log.error(f"  Erro Greenhouse {empresa_slug}: {r.status_code}")
            return []

        for job in r.json().get("jobs", []):
            descricao = limpar_html(job.get("content", ""))
            location = job.get("location", {}).get("name", "")

            modalidade = "não identificado"
            texto_lower = (job["title"] + " " + location).lower()
            if "remote" in texto_lower or "remoto" in texto_lower:
                modalidade = "remoto"
            elif "hybrid" in texto_lower:
                modalidade = "hibrido"

            location_name = job.get("location", {}).get("name", "")
            
            pais_detectado = ""
            loc_lower = location_name.lower()
            paises_br = ["brasil","brazil","são paulo","rio","rio de janeiro","belo horizonte","curitiba","londrina","porto alegre","osasco","campinas","florianopolis","salvador","recife","fortaleza","manaus","brasilia"]
            paises_outros = ["united states","usa","us","india","china","uk","canada","mexico","argentina","colombia","singapore","germany","france","spain"]
            
            if any(p in loc_lower for p in paises_br):
                pais_detectado = "br"
            elif any(p in loc_lower for p in paises_outros):
                pais_detectado = "other"
            elif location_name and "remote" not in loc_lower:
                pais_detectado = "br"  # assume BR se tem localização mas não é estrangeiro
            
            vagas.append({
                "titulo": job["title"],
                "link": job["absolute_url"],
                "modalidade": modalidade,
                "fonte": "greenhouse",
                "empresa": empresa_slug,
                "descricao": descricao,
                "cidade": location_name,
                "pais": pais_detectado,
            })

    except Exception as e:
        log.error(f"  Erro Greenhouse {empresa_slug}: {e}")

    return vagas

if __name__ == "__main__":
    vagas = buscar_vagas_greenhouse("nubank")
    log.info(f"{len(vagas)} vagas encontradas")
    for v in vagas[:5]:
        log.info(f"  - {v['titulo']}")