import requests

def buscar_vagas_smartrecruiters(company_slug: str, filtro_cidade: str = None) -> list:
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
                })

            offset += limit
            if offset >= data.get("totalFound", 0):
                break

        except Exception as e:
            print(f"Erro SmartRecruiters: {e}")
            break

    return vagas

if __name__ == "__main__":
    vagas = buscar_vagas_smartrecruiters("Visa")
    print(f"{len(vagas)} vagas encontradas")
    for v in vagas[:5]:
        print(f"  - {v['titulo']}")
