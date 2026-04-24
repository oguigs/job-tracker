"""
pipeline_prefect.py — Pipeline orquestrado com Prefect 2.
Substitui o loop manual do main.py por @flow e @task com retry automático.

Uso:
    python pipeline_prefect.py          # roda uma vez
    python pipeline_prefect.py --serve  # agenda para rodar a cada 6h
"""
import sys
from prefect import flow, task, get_run_logger
from prefect.tasks import task_input_hash
from datetime import timedelta


@task(name="buscar-empresas", retries=2, retry_delay_seconds=30)
def buscar_empresas_task() -> list:
    from database.connection import db_connect
    with db_connect(read_only=True) as con:
        return con.execute("""
            SELECT nome, url_vagas FROM dim_empresa
            WHERE ativa = true AND url_vagas IS NOT NULL AND url_vagas != ''
        """).fetchall()


@task(name="verificar-cooldown")
def verificar_cooldown_task(nome: str, horas_minimas: int = 12) -> bool:
    from database.logs import ultima_execucao_sucesso
    horas = ultima_execucao_sucesso(nome)
    return horas >= horas_minimas


@task(name="processar-gupy", retries=1, retry_delay_seconds=60)
def processar_gupy_task(nome: str, url: str) -> tuple:
    from main import processar_empresa
    return processar_empresa(nome, url)


@task(name="processar-greenhouse", retries=2, retry_delay_seconds=30)
def processar_greenhouse_task(nome: str, url: str) -> tuple:
    from main import processar_empresa_greenhouse
    slug = url.split("greenhouse.io/")[-1].split("/")[0]
    return processar_empresa_greenhouse(nome, slug)


@task(name="processar-inhire", retries=2, retry_delay_seconds=30)
def processar_inhire_task(nome: str, url: str) -> tuple:
    from main import processar_empresa_inhire
    return processar_empresa_inhire(nome, url)


@task(name="processar-smartrecruiters", retries=2, retry_delay_seconds=30)
def processar_smartrecruiters_task(nome: str, url: str) -> tuple:
    from main import processar_empresa_smartrecruiters
    return processar_empresa_smartrecruiters(nome, url)


@task(name="salvar-snapshot")
def salvar_snapshot_task():
    from database.snapshots import salvar_snapshot
    salvar_snapshot()


@flow(name="job-tracker-pipeline", log_prints=True)
def rodar_pipeline():
    """Flow principal — coleta vagas de todas as empresas ativas."""
    logger = get_run_logger()

    empresas = buscar_empresas_task()
    if not empresas:
        logger.warning("Nenhuma empresa ativa no banco.")
        return

    logger.info(f"Iniciando pipeline para {len(empresas)} empresas")

    total_novas = 0
    erros = []

    for nome, url in empresas:
        # verifica cooldown
        pode_rodar = verificar_cooldown_task(nome)
        if not pode_rodar:
            logger.info(f"[{nome}] Pulando — cooldown ativo")
            continue

        logger.info(f"[{nome}] Processando...")
        try:
            url = url or ""
            if "greenhouse.io" in url:
                enc, nov, erro = processar_greenhouse_task(nome, url)
            elif "inhire.app" in url:
                enc, nov, erro = processar_inhire_task(nome, url)
            elif "smartrecruiters.com" in url:
                enc, nov, erro = processar_smartrecruiters_task(nome, url)
            else:
                enc, nov, erro = processar_gupy_task(nome, url)

            total_novas += nov
            if erro:
                erros.append(f"{nome}: {erro}")
                logger.warning(f"[{nome}] {erro}")
            else:
                logger.info(f"[{nome}] {enc} encontradas | {nov} novas")

        except Exception as e:
            erros.append(f"{nome}: {str(e)}")
            logger.error(f"[{nome}] Erro: {e}")

    salvar_snapshot_task()

    logger.info(f"Pipeline concluído — {total_novas} vagas novas")
    if erros:
        logger.warning(f"Erros: {erros}")

    return {"total_novas": total_novas, "erros": erros}


if __name__ == "__main__":
    if "--serve" in sys.argv:
        # agenda para rodar a cada 6 horas
        rodar_pipeline.serve(
            name="job-tracker-schedule",
            interval=timedelta(hours=6),
        )
    else:
        rodar_pipeline()
