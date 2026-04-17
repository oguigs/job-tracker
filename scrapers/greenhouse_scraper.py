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
            print(f"  Erro Greenhouse {empresa_slug}: {r.status_code}")
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

            vagas.append({
                "titulo": job["title"],
                "link": job["absolute_url"],
                "modalidade": modalidade,
                "fonte": "greenhouse",
                "empresa": empresa_slug,
                "descricao": descricao,
            })

    except Exception as e:
        print(f"  Erro Greenhouse {empresa_slug}: {e}")

    return vagas

if __name__ == "__main__":
    vagas = buscar_vagas_greenhouse("nubank")
    print(f"{len(vagas)} vagas encontradas")
    for v in vagas[:5]:
        print(f"  - {v['titulo']}")