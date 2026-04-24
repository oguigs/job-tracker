from logger import get_logger
log = get_logger("smartrecruiters_scraper")
import requests, html, re

def limpar_html(texto: str) -> str:
    return re.sub('<[^>]+>', ' ', html.unescape(texto or ''))


def buscar_vagas_smartrecruiters(company_slug: str, filtro_cidade: str = None, buscar_descricao: bool = True) -> list:
    vagas = []
    limit = 100
    offset = 0

    while True:
        try:
            r = requests.get(
                f"https://api.smartrecruiters.com/v1/companies/{company_slug}/postings",
                params={"limit": limit, "offset": offset},
                timeout=15
            )
            if r.status_code != 200:
                break

            data = r.json()
            items = data.get("content", [])
            if not items:
                break

            for v in items:
                cidade = v.get("location", {}).get("city", "")
                if filtro_cidade and filtro_cidade.lower() not in cidade.lower():
                    continue

                if buscar_descricao:
                    # busca descrição individual
                    descricao = ""
                    try:
                        rd = requests.get(
                            f"https://api.smartrecruiters.com/v1/companies/{company_slug}/postings/{v['id']}",
                            timeout=10
                        )
                        if rd.status_code == 200:
                            sections = rd.json().get('jobAd',{}).get('sections',{})
                            desc = limpar_html(sections.get('jobDescription',{}).get('text',''))
                            qual = limpar_html(sections.get('qualifications',{}).get('text',''))
                            descricao = f"{desc} {qual}"
                    except Exception:
                        pass
                else:
                    descricao = ""

                modalidade = "não identificado"
                tipo = str(v.get("typeOfEmployment", {}).get("label", "")).lower()
                if "remote" in tipo or "remoto" in tipo:
                    modalidade = "remoto"
                elif "hybrid" in tipo:
                    modalidade = "hibrido"

                vagas.append({
                    "titulo": v["name"],
                    "link": f"https://jobs.smartrecruiters.com/{company_slug}/{v['id']}",
                    "modalidade": modalidade,
                    "fonte": "smartrecruiters",
                    "empresa": company_slug,
                    "descricao": descricao,
                    "cidade": v.get("location", {}).get("city", ""),
                    "pais": v.get("location", {}).get("country", ""),
                })
            offset += limit
            if offset >= data.get("totalFound", 0):
                break

        except Exception as e:
            log.error(f"Erro SmartRecruiters: {e}")
            break

    return vagas

if __name__ == "__main__":
    vagas = buscar_vagas_smartrecruiters("Visa")
    log.info(f"{len(vagas)} vagas encontradas")
    for v in vagas[:5]:
        log.info(f"  - {v['titulo']}")
