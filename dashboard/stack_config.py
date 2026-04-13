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