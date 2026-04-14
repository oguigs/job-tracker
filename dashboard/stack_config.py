# Mapeamento de stack → (ícone devicons, link roadmap.sh)
STACK_CONFIG = {
    # Linguagens
    "python":       ("python",      "https://roadmap.sh/python"),
    "sql":          ("postgresql",  "https://roadmap.sh/sql"),
    "java":         ("java",        "https://roadmap.sh/java"),
    "scala":        ("scala",       "https://roadmap.sh/scala"),
    "r":            ("r",           None),
    "bash":         ("bash",        None),
    "go":           ("go",          "https://roadmap.sh/golang"),

    # Cloud
    "aws":          ("amazonwebservices", "https://roadmap.sh/aws"),
    "azure":        ("azure",       None),
    "gcp":          ("googlecloud", None),
    "databricks":   ("apachespark", None),
    "google cloud": ("googlecloud", None),

    # Processamento
    "spark":        ("apachespark", None),
    "pyspark":      ("apachespark", None),
    "kafka":        ("apachekafka", None),
    "dbt":          ("dbt",         "https://roadmap.sh/sql"),
    "glue":         ("amazonwebservices", None),
    "flink":        ("apacheflink", None),

    # Orquestração
    "airflow":      ("apacheairflow", None),
    "prefect":      ("python",      None),
    "step functions": ("amazonwebservices", None),
    "luigi":        ("python",      None),

    # Armazenamento
    "postgresql":   ("postgresql",  None),
    "mysql":        ("mysql",       None),
    "mongodb":      ("mongodb",     None),
    "redis":        ("redis",       None),
    "s3":           ("amazonwebservices", None),
    "bigquery":     ("googlecloud", None),
    "snowflake":    ("snowflake",   None),
    "redshift":     ("amazonwebservices", None),
    "delta lake":   ("apachespark", None),
    "iceberg":      ("apachespark", None),

    # Infraestrutura
    "docker":       ("docker",      "https://roadmap.sh/docker"),
    "kubernetes":   ("kubernetes",  "https://roadmap.sh/kubernetes"),
    "terraform":    ("terraform",   "https://roadmap.sh/terraform"),
    "git":          ("git",         "https://roadmap.sh/git-github"),
    "jenkins":      ("jenkins",     None),
    "github":       ("github",      "https://roadmap.sh/git-github"),
    "gitlab":       ("gitlab",      None),
    "ci/cd":        ("githubactions", None),
    "linux":        ("linux",       None),

    # Visualização
    "tableau":      ("tableau",     None),
    "power bi":     ("python",      None),
    "looker":       ("python",      None),
    "metabase":     ("python",      None),
    "superset":     ("python",      None),
    "grafana":      ("grafana",     None),

    # ML/IA
    "tensorflow":   ("tensorflow",  "https://roadmap.sh/ai-data-scientist"),
    "pytorch":      ("pytorch",     "https://roadmap.sh/ai-data-scientist"),
    "scikit-learn": ("python",      "https://roadmap.sh/ai-data-scientist"),
    "sklearn":      ("python",      "https://roadmap.sh/ai-data-scientist"),
    "mlflow":       ("python",      None),

    # Infraestrutura adicional
    "ansible":      ("ansible",     None),
    "helm":         ("helm",        None),
    "prometheus":   ("prometheus",  None),
    "grafana":      ("grafana",     None),
    "circleci":     ("circleci",    None),
    "pulumi":       ("python",      None),

    # Armazenamento adicional
    "cassandra":    ("apachecassandra", None),
    "elasticsearch":("elasticsearch",  None),
    "redis":        ("redis",           None),
    "firebase":     ("firebase",        None),

    # Processamento adicional
    "polars":       ("python",      None),
    "pandas":       ("pandas",      None),
    "numpy":        ("numpy",       None),
    "rabbitmq":     ("rabbitmq",    None),
    "trino":        ("python",      None),
    "airbyte":      ("python",      None),

    # Cloud adicional
    "lambda":       ("amazonwebservices", None),
    "kinesis":      ("amazonwebservices", None),
    "pubsub":       ("googlecloud",       None),
}

DEVICON_BASE = "https://cdn.jsdelivr.net/gh/devicons/devicon/icons"

def get_stack_icon_url(stack: str) -> str:
    """Retorna a URL do ícone SVG da stack."""
    key = stack.lower().strip()
    if key in STACK_CONFIG:
        devicon_name = STACK_CONFIG[key][0]
        return f"{DEVICON_BASE}/{devicon_name}/{devicon_name}-original.svg"
    return ""

def get_stack_roadmap_url(stack: str) -> str:
    """Retorna a URL do roadmap.sh da stack, ou None se não existir."""
    key = stack.lower().strip()
    if key in STACK_CONFIG:
        return STACK_CONFIG[key][1]
    return None

# Cores por categoria
CATEGORIA_CORES = {
    "linguagens":    {"bg": "#E8F5F0", "border": "#1D9E75", "text": "#157A5A"},
    "cloud":         {"bg": "#EBF3FB", "border": "#378ADD", "text": "#1A5FAD"},
    "processamento": {"bg": "#FBF0EB", "border": "#D85A30", "text": "#A83A18"},
    "orquestracao":  {"bg": "#F0EFF9", "border": "#7F77DD", "text": "#4B44AA"},
    "armazenamento": {"bg": "#FBF4E8", "border": "#BA7517", "text": "#8A5210"},
    "infraestrutura":{"bg": "#F2F2F1", "border": "#888780", "text": "#555450"},
    "visualizacao": {"bg": "#EBF3FB", "border": "#378ADD", "text": "#1A5FAD"},
    "ml_ia":        {"bg": "#F5EFF9", "border": "#9B59B6", "text": "#6C3483"},

}

def get_categoria_cor(categoria: str) -> dict:
    key = categoria.lower().replace("ç", "c").replace("ã", "a")
    return CATEGORIA_CORES.get(key, {"bg": "#f0f0f0", "border": "#ddd", "text": "#555"})
