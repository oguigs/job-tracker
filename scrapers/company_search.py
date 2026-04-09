from ddgs import DDGS
import re

def buscar_empresa(nome_empresa: str) -> dict:
    resultado = {
        "ramo": "",
        "cidade": "",
        "bairro": "",
        "estado": "",
        "url_linkedin": "",
        "url_site_vagas": ""
    }

    queries = {
        "linkedin": f"{nome_empresa} site:linkedin.com/company",
        "info": f"{nome_empresa} empresa sede endereço setor brasil",
        "vagas": f"{nome_empresa} vagas emprego careers jobs"
    }

    setores = {
        "fintech": ["fintech", "financeiro", "banco", "pagamento", "crédito"],
        "tecnologia": ["tecnologia", "software", "ti ", "tech", "sistemas"],
        "consultoria": ["consultoria", "consulting", "serviços"],
        "varejo": ["varejo", "e-commerce", "retail", "loja"],
        "saúde": ["saúde", "health", "hospital", "médico", "farmácia"],
        "educação": ["educação", "ensino", "escola", "edtech", "cursos"],
        "logística": ["logística", "transporte", "frete", "entrega"],
        "telecomunicações": ["telecom", "telecomunicações", "internet", "fibra"]
    }

    cidades = [
        "são paulo", "rio de janeiro", "belo horizonte", "curitiba",
        "porto alegre", "brasília", "campinas", "florianópolis",
        "recife", "salvador", "fortaleza", "manaus", "goiânia"
    ]

    with DDGS() as ddgs:
        for tipo, query in queries.items():
            try:
                resultados = list(ddgs.text(query, max_results=5))

                for item in resultados:
                    link = item.get("href", "")
                    snippet = item.get("body", "").lower()
                    titulo = item.get("title", "").lower()
                    texto = snippet + " " + titulo

                    if tipo == "linkedin":
                        if "linkedin.com/company" in link:
                            resultado["url_linkedin"] = link
                            break

                    if tipo == "vagas":
                        if resultado["url_site_vagas"]:
                            break
                        if any(p in link for p in ["gupy.io", "inhire.io", "lever.co", "greenhouse.io"]):
                            resultado["url_site_vagas"] = link
                            break
                        if any(p in link for p in ["vagas", "careers", "jobs", "trabalhe"]):
                            resultado["url_site_vagas"] = link
                            break

                    if tipo == "info":
                        if not resultado["ramo"]:
                            for setor, palavras in setores.items():
                                if any(p in texto for p in palavras):
                                    resultado["ramo"] = setor
                                    break

                        if not resultado["cidade"]:
                            for cidade in cidades:
                                if cidade in texto:
                                    resultado["cidade"] = cidade.title()
                                    break

            except Exception as e:
                print(f"Erro na busca '{tipo}': {e}")

    return resultado


if __name__ == "__main__":
    print("Testando busca para Compass UOL...")
    resultado = buscar_empresa("Compass UOL")
    for chave, valor in resultado.items():
        print(f"  {chave}: {valor}")