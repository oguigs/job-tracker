import json
import re

STACKS = {
    "linguagens": [
        "python", "sql", "scala", "java", "bash", "shell", "linguagem r", "r studio", "rstudio"
    ],
    "cloud": [
        "aws", "azure", "gcp", "google cloud", "databricks", "snowflake"
    ],
    "orquestracao": [
        "airflow", "prefect", "dagster", "mage", "step functions"
    ],
    "processamento": [
        "spark", "pyspark", "flink", "kafka", "dbt", "dask", "glue"
    ],
    "armazenamento": [
        "s3", "redshift", "bigquery", "delta lake", "iceberg", "hudi",
        "dynamodb", "postgres", "postgresql", "mysql", "mongodb"
    ],
    "infraestrutura": [
        "docker", "kubernetes", "terraform", "ci/cd", "git", "github",
        "gitlab", "jenkins"
    ],
    "nivel": [
        "junior", "pleno", "senior", "especialista", "lead"
    ]
}

def extrair_stacks(descricao: str) -> dict:
    descricao_lower = descricao.lower()
    resultado = {}
    for categoria, termos in STACKS.items():
        encontrados = []
        for t in termos:
            # busca palavra inteira para evitar falsos positivos como "r"
            padrao = rf'\b{re.escape(t)}\b'
            if re.search(padrao, descricao_lower):
                encontrados.append(t)
        if encontrados:
            resultado[categoria] = encontrados
    return resultado

def detectar_nivel(titulo: str) -> str:
    titulo_lower = titulo.lower()
    if any(p in titulo_lower for p in ["junior", "jr", "júnior"]):
        return "junior"
    if any(p in titulo_lower for p in ["especialista", "specialist", "lead", "staff"]):
        return "especialista"
    if any(p in titulo_lower for p in ["senior", "sr", "sênior"]):
        return "senior"
    if "pleno" in titulo_lower:
        return "pleno"
    return "não identificado"

def detectar_modalidade(texto: str, modalidade_coletada: str = "não identificado") -> str:
    # se já veio preenchido do scraper, prioriza esse valor
    if modalidade_coletada and modalidade_coletada != "não identificado":
        return modalidade_coletada

    # senão tenta extrair da descrição
    texto_lower = texto.lower()
    if "híbrido" in texto_lower or "hibrido" in texto_lower:
        return "hibrido"
    if "remoto" in texto_lower or "remote" in texto_lower:
        return "remoto"
    if "presencial" in texto_lower:
        return "presencial"
    return "não identificado"

def processar_vagas(caminho_json: str):
    with open(caminho_json, "r", encoding="utf-8") as f:
        vagas = json.load(f)

    for vaga in vagas:
        descricao = vaga.get("descricao", "")
        titulo = vaga.get("titulo", "")
        vaga["stacks"] = extrair_stacks(descricao)
        vaga["nivel"] = detectar_nivel(titulo)
        vaga["modalidade"] = detectar_modalidade(
            descricao,
            modalidade_coletada=vaga.get("modalidade", "não identificado")
        )

    with open("data/raw/vagas_processadas.json", "w", encoding="utf-8") as f:
        json.dump(vagas, f, ensure_ascii=False, indent=2)

    print(f"{len(vagas)} vagas processadas")
    print("\nResumo das stacks encontradas:")
    for vaga in vagas:
        print(f"\n{vaga['titulo'][:50]}")
        print(f"  Nível: {vaga['nivel']} | Modalidade: {vaga['modalidade']}")
        for categoria, termos in vaga['stacks'].items():
            print(f"  {categoria}: {', '.join(termos)}")

    return vagas

TERMOS_URGENCIA = [
    "início imediato", "inicio imediato",
    "urgente", "urgência", "urgencia",
    "processo rápido", "processo rapido",
    "vaga urgente", "contratação imediata",
    "contratacao imediata", "imediato",
    "asap", "as soon as possible"
]

def detectar_urgencia(descricao: str, titulo: str = "") -> bool:
    texto = (descricao + " " + titulo).lower()
    return any(termo in texto for termo in TERMOS_URGENCIA)


if __name__ == "__main__":
    processar_vagas("data/raw/vagas_enriquecidas.json")