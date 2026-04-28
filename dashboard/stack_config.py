# stack → (devicon_name | None, roadmap_url | None)
# None em devicon_name = sem ícone (badge só texto)
STACK_CONFIG = {
    # Linguagens
    "python":          ("python",            "https://roadmap.sh/python"),
    "sql":             ("postgresql",        "https://roadmap.sh/sql"),
    "java":            ("java",              "https://roadmap.sh/java"),
    "scala":           ("scala",             None),
    "go":              ("go",                "https://roadmap.sh/golang"),
    "golang":          ("go",                "https://roadmap.sh/golang"),
    "bash":            ("bash",              "https://roadmap.sh/linux"),
    "shell":           ("bash",              "https://roadmap.sh/linux"),
    "r studio":        ("rstudio",           None),
    "rstudio":         ("rstudio",           None),
    "typescript":      ("typescript",        None),
    "javascript":      ("javascript",        None),
    "kotlin":          ("kotlin",            None),
    "rust":            ("rust",              None),

    # Cloud
    "aws":             ("amazonwebservices", "https://roadmap.sh/aws"),
    "azure":           ("azure",             None),
    "gcp":             ("googlecloud",       None),
    "google cloud":    ("googlecloud",       None),
    "databricks":      ("apachespark",       None),
    "lambda":          ("amazonwebservices", "https://roadmap.sh/aws"),
    "ec2":             ("amazonwebservices", "https://roadmap.sh/aws"),
    "ecs":             ("amazonwebservices", "https://roadmap.sh/aws"),
    "eks":             ("amazonwebservices", "https://roadmap.sh/aws"),
    "emr":             ("amazonwebservices", "https://roadmap.sh/aws"),
    "sagemaker":       ("amazonwebservices", "https://roadmap.sh/aws"),
    "kinesis":         ("amazonwebservices", "https://roadmap.sh/aws"),
    "pubsub":          ("googlecloud",       None),
    "cloud run":       ("googlecloud",       None),
    "bigquery":        ("googlecloud",       None),

    # Processamento
    "spark":           ("apachespark",       None),
    "pyspark":         ("apachespark",       None),
    "kafka":           ("apachekafka",       None),
    "flink":           ("apacheflink",       None),
    "dbt":             (None,                "https://roadmap.sh/sql"),
    "glue":            ("amazonwebservices", "https://roadmap.sh/aws"),
    "beam":            ("apachebeam",        None),
    "apache beam":     ("apachebeam",        None),
    "polars":          ("python",            "https://roadmap.sh/python"),
    "pandas":          ("pandas",            "https://roadmap.sh/python"),
    "numpy":           ("numpy",             "https://roadmap.sh/python"),
    "trino":           (None,                None),
    "presto":          (None,                None),
    "hive":            ("apachehive",        None),
    "airbyte":         (None,                None),
    "fivetran":        (None,                None),
    "rabbitmq":        ("rabbitmq",          None),

    # Orquestração
    "airflow":         ("apacheairflow",     None),
    "prefect":         (None,                None),
    "dagster":         (None,                None),
    "step functions":  ("amazonwebservices", "https://roadmap.sh/aws"),
    "luigi":           (None,                None),

    # Armazenamento
    "postgresql":      ("postgresql",        "https://roadmap.sh/postgresql-dba"),
    "postgres":        ("postgresql",        "https://roadmap.sh/postgresql-dba"),
    "mysql":           ("mysql",             None),
    "mongodb":         ("mongodb",           "https://roadmap.sh/mongodb"),
    "redis":           ("redis",             None),
    "s3":              ("amazonwebservices", "https://roadmap.sh/aws"),
    "redshift":        ("amazonwebservices", "https://roadmap.sh/aws"),
    "snowflake":       (None,                None),
    "delta lake":      ("apachespark",       None),
    "iceberg":         (None,                None),
    "cassandra":       ("apachecassandra",   None),
    "elasticsearch":   ("elasticsearch",     None),
    "opensearch":      ("elasticsearch",     None),
    "firebase":        ("firebase",          None),
    "dynamodb":        ("amazonwebservices", "https://roadmap.sh/aws"),
    "clickhouse":      (None,                None),

    # Infraestrutura
    "docker":          ("docker",            "https://roadmap.sh/docker"),
    "kubernetes":      ("kubernetes",        "https://roadmap.sh/kubernetes"),
    "terraform":       ("terraform",         "https://roadmap.sh/terraform"),
    "git":             ("git",               "https://roadmap.sh/git-github"),
    "github":          ("github",            "https://roadmap.sh/git-github"),
    "gitlab":          ("gitlab",            None),
    "jenkins":         ("jenkins",           None),
    "ansible":         ("ansible",           "https://roadmap.sh/devops"),
    "helm":            ("helm",              "https://roadmap.sh/kubernetes"),
    "prometheus":      ("prometheus",        None),
    "grafana":         ("grafana",           None),
    "datadog":         (None,                None),
    "circleci":        ("circleci",          None),
    "github actions":  ("githubactions",     "https://roadmap.sh/devops"),
    "ci/cd":           ("githubactions",     "https://roadmap.sh/devops"),
    "linux":           ("linux",             "https://roadmap.sh/linux"),
    "pulumi":          (None,                "https://roadmap.sh/devops"),

    # Visualização
    "tableau":         ("tableau",           None),
    "power bi":        (None,                None),
    "looker":          (None,                None),
    "metabase":        (None,                None),
    "superset":        (None,                None),
    "grafana":         ("grafana",           None),
    "plotly":          ("plotly",            None),
    "streamlit":       ("streamlit",         None),

    # ML/IA
    "machine learning": (None,              "https://roadmap.sh/ai-data-scientist"),
    "deep learning":   (None,               "https://roadmap.sh/ai-data-scientist"),
    "tensorflow":      ("tensorflow",        "https://roadmap.sh/ai-data-scientist"),
    "pytorch":         ("pytorch",           "https://roadmap.sh/ai-data-scientist"),
    "scikit-learn":    (None,               "https://roadmap.sh/ai-data-scientist"),
    "sklearn":         (None,               "https://roadmap.sh/ai-data-scientist"),
    "mlflow":          (None,                None),
    "langchain":       (None,                None),
    "llm":             (None,                "https://roadmap.sh/ai-data-scientist"),
    "openai":          (None,                "https://roadmap.sh/ai-data-scientist"),
    "hugging face":    (None,                "https://roadmap.sh/ai-data-scientist"),
    "xgboost":         (None,               "https://roadmap.sh/ai-data-scientist"),
}

DEVICON_BASE = "https://cdn.jsdelivr.net/gh/devicons/devicon/icons"


def get_stack_icon_url(stack: str) -> str:
    key = stack.lower().strip()
    cfg = STACK_CONFIG.get(key)
    if cfg and cfg[0]:
        devicon_name = cfg[0]
        return f"{DEVICON_BASE}/{devicon_name}/{devicon_name}-original.svg"
    return ""


def get_stack_roadmap_url(stack: str) -> str:
    key = stack.lower().strip()
    cfg = STACK_CONFIG.get(key)
    return cfg[1] if cfg else None


# Cores por categoria
CATEGORIA_CORES = {
    "linguagens":     {"bg": "#E8F5F0", "border": "#1D9E75", "text": "#157A5A"},
    "cloud":          {"bg": "#EBF3FB", "border": "#378ADD", "text": "#1A5FAD"},
    "processamento":  {"bg": "#FBF0EB", "border": "#D85A30", "text": "#A83A18"},
    "orquestracao":   {"bg": "#F0EFF9", "border": "#7F77DD", "text": "#4B44AA"},
    "armazenamento":  {"bg": "#FBF4E8", "border": "#BA7517", "text": "#8A5210"},
    "infraestrutura": {"bg": "#F2F2F1", "border": "#888780", "text": "#555450"},
    "integracao":     {"bg": "#E8F5F0", "border": "#1D9E75", "text": "#157A5A"},
    "visualizacao":   {"bg": "#EBF3FB", "border": "#378ADD", "text": "#1A5FAD"},
    "ml_ia":          {"bg": "#F5EFF9", "border": "#9B59B6", "text": "#6C3483"},
}


def get_categoria_cor(categoria: str) -> dict:
    key = categoria.lower().replace("ç", "c").replace("ã", "a")
    return CATEGORIA_CORES.get(key, {"bg": "#f0f0f0", "border": "#ddd", "text": "#555"})
