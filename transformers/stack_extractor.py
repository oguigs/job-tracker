import json
import re

STACKS = {
    "linguagens": [
        "python", "sql", "scala", "java", "bash", "shell", "linguagem r",
        "r studio", "rstudio", "go", "golang", "rust", "typescript",
        "javascript", "kotlin", "c++", "c#", "ruby", "php", "swift",
        "haskell", "lua", "perl", "matlab", "julia"
    ],
    "cloud": [
        "aws", "azure", "gcp", "google cloud", "databricks", "snowflake",
        "oracle cloud", "ibm cloud", "cloudflare", "heroku", "vercel",
        "lambda", "ec2", "ecs", "eks", "emr", "sagemaker",
        "azure data factory", "azure synapse", "azure databricks",
        "google dataflow", "google dataproc", "bigquery ml",
        "cloud functions", "cloud run", "cloud storage"
    ],
    "orquestracao": [
        "airflow", "prefect", "dagster", "mage", "step functions",
        "luigi", "argo", "kubeflow", "flyte", "metaflow",
        "azure data factory", "cloud composer", "aws glue workflow"
    ],
    "processamento": [
        "spark", "pyspark", "flink", "kafka", "dbt", "dask", "glue",
        "beam", "apache beam", "ray", "polars", "pandas", "numpy",
        "spark streaming", "kafka streams", "kinesis", "pubsub",
        "rabbitmq", "activemq", "nifi", "apache nifi",
        "trino", "presto", "hive", "pig", "sqoop",
        "debezium", "fivetran", "airbyte", "stitch", "informatica"
    ],
    "armazenamento": [
        "s3", "redshift", "bigquery", "delta lake", "iceberg", "hudi",
        "dynamodb", "postgres", "postgresql", "mysql", "mongodb",
        "cassandra", "redis", "elasticsearch", "opensearch",
        "neo4j", "couchdb", "firebase", "supabase",
        "azure blob", "azure sql", "azure cosmos",
        "clickhouse", "druid", "pinot", "dremio",
        "unity catalog", "glue catalog", "hive metastore",
        "parquet", "avro", "orc", "json", "csv"
    ],
    "infraestrutura": [
        "docker", "kubernetes", "terraform", "ci/cd", "git", "github",
        "gitlab", "jenkins", "ansible", "puppet", "chef",
        "helm", "istio", "prometheus", "grafana", "datadog",
        "github actions", "gitlab ci", "circleci", "travis",
        "linux", "unix", "bash scripting", "powershell",
        "nginx", "apache", "vault", "consul",
        "pulumi", "cloudformation", "cdk", "bicep"
    ],
    "visualizacao": [
        "tableau", "power bi", "looker", "metabase", "superset",
        "grafana", "qlik", "microstrategy", "thoughtspot",
        "plotly", "matplotlib", "seaborn", "d3", "streamlit"
    ],
    "ml_ia": [
        "machine learning", "deep learning", "mlflow", "mlops",
        "scikit-learn", "sklearn", "tensorflow", "pytorch", "keras",
        "hugging face", "openai", "langchain", "llm",
        "feature store", "vertex ai", "sagemaker", "azure ml",
        "databricks mlflow", "wandb", "dvc", "bentoml",
        "xgboost", "lightgbm", "catboost", "prophet"
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

def detectar_salario(descricao: str) -> tuple[int, int]:
    """
    Extrai faixa salarial da descrição da vaga.
    Retorna (salario_min, salario_max) em reais/mês.
    Retorna (0, 0) se não encontrar.
    """
    import re

    texto = descricao.lower().replace(".", "").replace(",", ".")

    # padrões: R$ 5.000 a R$ 8.000 / entre 5000 e 8000 / 5k a 8k
    padroes = [
        r"r\$\s*(\d+\.?\d*)\s*(?:a|até|–|-)\s*r\$\s*(\d+\.?\d*)",
        r"(?:entre|de)\s*r\$\s*(\d+\.?\d*)\s*(?:e|a|até)\s*r\$\s*(\d+\.?\d*)",
        r"salário[:\s]+r\$\s*(\d+\.?\d*)\s*(?:a|até|–|-)\s*r\$\s*(\d+\.?\d*)",
        r"(\d+)k\s*(?:a|até|–|-)\s*(\d+)k",
        r"(\d{4,6})\s*(?:a|até|–|-)\s*(\d{4,6})",
    ]

    for padrao in padroes:
        match = re.search(padrao, texto)
        if match:
            try:
                v1 = float(match.group(1).replace(".", ""))
                v2 = float(match.group(2).replace(".", ""))
                # converte k para reais
                if v1 < 100: v1 *= 1000
                if v2 < 100: v2 *= 1000
                # sanity check — salários entre R$1k e R$50k
                if 1000 <= v1 <= 50000 and 1000 <= v2 <= 50000:
                    return int(min(v1, v2)), int(max(v1, v2))
            except Exception:
                continue

    return 0, 0


def extrair_sinais_descricao(descricao: str) -> dict:
    """
    Extrai sinais qualitativos da descrição da vaga além de stacks.
    Retorna dict com tamanho de equipe, volume de dados, cultura e estágio.
    """
    import re
    texto = descricao.lower()
    sinais = {
        "tamanho_equipe": None,
        "volume_dados": None,
        "cultura": [],
        "estagio_empresa": None,
    }

    # tamanho da equipe
    match = re.search(r'time\s+de\s+(\d+)|equipe\s+de\s+(\d+)|squad\s+de\s+(\d+)|(\d+)\s+engenheiros', texto)
    if match:
        val = next(v for v in match.groups() if v)
        sinais["tamanho_equipe"] = int(val)

    # volume de dados
    if any(x in texto for x in ["petabyte", "pb de", "bilhões de"]):
        sinais["volume_dados"] = "muito alto"
    elif any(x in texto for x in ["terabyte", "tb de", "milhões de eventos", "centenas de milhões"]):
        sinais["volume_dados"] = "alto"
    elif any(x in texto for x in ["gigabyte", "milhares de", "dezenas de milhões"]):
        sinais["volume_dados"] = "médio"

    # cultura de engenharia
    termos_cultura = {
        "pair programming": "pair programming",
        "code review": "code review",
        "tdd": "TDD",
        "on-call": "on-call",
        "post-mortem": "post-mortem",
        "agile": "agile",
        "scrum": "scrum",
        "kanban": "kanban",
        "ci/cd": "CI/CD",
        "devops": "devops",
    }
    sinais["cultura"] = [label for termo, label in termos_cultura.items() if termo in texto]

    # estágio da empresa
    if any(x in texto for x in ["série a", "serie a", "series a", "seed", "startup em early"]):
        sinais["estagio_empresa"] = "early stage"
    elif any(x in texto for x in ["série b", "serie b", "series b", "série c", "scale-up"]):
        sinais["estagio_empresa"] = "growth stage"
    elif any(x in texto for x in ["empresa consolidada", "20 anos", "30 anos", "empresa de grande porte", "multinacional"]):
        sinais["estagio_empresa"] = "empresa consolidada"

    return sinais
