import json
import time as _time
import duckdb
from scrapers.gupy_detalhes import coletar_descricoes_lote
from transformers.stack_extractor import extrair_stacks, detectar_nivel, detectar_modalidade, detectar_urgencia, detectar_salario, extrair_sinais_descricao
from database.schemas import criar_tabelas
from database.empresas import upsert_empresa, listar_empresas_ativas, gerar_hash
from database.vagas import inserir_vaga, verificar_vagas_encerradas
from database.logs import registrar_log, ultima_execucao_sucesso, empresa_bloqueada
from database.filtros import carregar_filtros, carregar_filtros_localizacao
from database.snapshots import salvar_snapshot
from database.candidato import carregar_curriculo_texto
from database.ats_score import salvar_ats_score
from scrapers.greenhouse_scraper import buscar_vagas_greenhouse
from scrapers.inhire_scraper import buscar_vagas_inhire
from scrapers.smartrecruiters_scraper import buscar_vagas_smartrecruiters
from database.connection import DB_PATH, conectar, db_connect
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth as stealth_sync
import requests, html, re
from transformers.stack_extractor import extrair_sinais_descricao

from logger import get_logger
log = get_logger("pipeline")

TIMEOUT_EMPRESA_SEGUNDOS = 300

def titulo_relevante(titulo: str, interesse: list, bloqueio: list) -> bool:
    titulo_lower = titulo.lower()
    if any(b in titulo_lower for b in bloqueio):
        return False
    if interesse and not any(i in titulo_lower for i in interesse):
        return False
    return True

def localidade_relevante(vaga: dict, permitidos: list, bloqueados: list) -> bool:
    if not permitidos and not bloqueados:
        return True
    
    local = (
        vaga.get("cidade", "") + " " + 
        vaga.get("pais", "") + " " +
        vaga.get("modalidade", "") + " " +
        vaga.get("titulo", "")
    ).lower()
    
    if bloqueados:
        bloqueados_iso = {"india": "in", "china": "cn", "pakistan": "pk"}
        for b in bloqueados:
            if b.lower() in local:
                return False
            if b.lower() in bloqueados_iso and bloqueados_iso[b.lower()] == vaga.get("pais","").lower():
                return False
    
    if permitidos:
        permitidos_iso = {"brazil": "br", "brasil": "br"}
        for p in permitidos:
            if p.lower() in local:
                return True
            if p.lower() in permitidos_iso and permitidos_iso[p.lower()] == vaga.get("pais","").lower():
                return True
        return "remoto" in local or "remote" in local
    
    return True

def processar_empresa(nome: str, url_vagas: str, cooldown_horas: int = 12) -> tuple[int, int, str]:
    if empresa_bloqueada(nome):
        log.info(f"  {nome} bloqueada — aguardando 48h")
        return 0, 0, "bloqueada (48h)"

    vagas_encontradas = 0
    vagas_novas = 0
    erro = ""

    horas_desde_ultima = ultima_execucao_sucesso(nome)
    if horas_desde_ultima < cooldown_horas:
        log.info(f"  Pulando {nome} — última execução há {horas_desde_ultima}h")
        return 0, 0, f"cooldown ({horas_desde_ultima}h)"

    log.info(f"  Última execução: {horas_desde_ultima}h atrás")

    try:
        texto_cv = carregar_curriculo_texto()
        vagas = buscar_vagas(url_vagas)
        vagas_encontradas = len(vagas)

        interesse, bloqueio = carregar_filtros()
        vagas_filtradas = [v for v in vagas if titulo_relevante(v["titulo"], interesse, bloqueio)]
        log.info(f"  {len(vagas_filtradas)} vagas relevantes de {vagas_encontradas} após filtro")

        vagas_enriquecidas = coletar_descricoes_lote(vagas_filtradas)

        id_empresa = upsert_empresa(nome=nome, url_vagas=url_vagas)
        for vaga in vagas_enriquecidas:
            descricao = vaga.get("descricao", "")
            titulo = vaga.get("titulo", "")

            vaga["stacks"]    = extrair_stacks(descricao)
            vaga["nivel"]     = detectar_nivel(titulo)
            vaga["modalidade"] = detectar_modalidade(
                descricao,
                modalidade_coletada=vaga.get("modalidade", "não identificado")
            )

            with db_connect(read_only=True) as con_check:
                negada = con_check.execute("""
                    SELECT id FROM fact_vaga WHERE hash = ? AND negada = true
                """, [gerar_hash(vaga["titulo"], vaga["empresa"], vaga["link"])]).fetchone()

            if negada:
                continue

            id_nova = inserir_vaga(vaga, id_empresa)
            if id_nova:
                vagas_novas += 1
                _auto_anya(id_nova, descricao, titulo, texto_cv)

        links_ativos = [v["link"] for v in vagas_enriquecidas]
        encerradas = verificar_vagas_encerradas(id_empresa, links_ativos)
        if encerradas:
            log.info(f"  {len(encerradas)} vaga(s) encerrada(s)")

        registrar_log(nome, vagas_encontradas, vagas_novas, "sucesso")
        log.info(f"  {vagas_encontradas} encontradas | {vagas_novas} novas")

    except Exception as e:
        erro = str(e)
        registrar_log(nome, vagas_encontradas, vagas_novas, "erro", erro)
        log.error(f"  Erro: {erro}")

    return vagas_encontradas, vagas_novas, erro

def _auto_anya(id_vaga: int, descricao: str, titulo: str, texto_cv: str):
    """Runs ANYA score computation silently — never raises."""
    if not texto_cv or not descricao:
        return
    try:
        from transformers.ats_agents import rodar_anya
        anya = rodar_anya(texto_cv, descricao, titulo)
        anya["score_final"] = round(
            anya["score_keywords"]   * 0.40 +
            anya["score_formatacao"] * 0.25 +
            anya["score_secoes"]     * 0.20 +
            anya["score_impacto"]    * 0.15
        )
        salvar_ats_score(id_vaga, anya)
    except Exception:
        pass


def _processar_empresa_generica(nome: str, vagas_raw: list) -> tuple[int, int, str]:
    """Processa vagas já coletadas — filtra, enriquece e insere no banco."""
    vagas_novas = 0
    try:
        texto_cv = carregar_curriculo_texto()

        interesse, bloqueio = carregar_filtros()
        vagas = [v for v in vagas_raw if titulo_relevante(v["titulo"], interesse, bloqueio)]
        log.info(f"  {len(vagas)} vagas relevantes após filtro de título")

        permitidos, bloqueados = carregar_filtros_localizacao()
        vagas = [v for v in vagas if localidade_relevante(v, permitidos, bloqueados)]
        log.info(f"  {len(vagas)} vagas após filtro de localização")

        vagas_encontradas = len(vagas)
        id_empresa = upsert_empresa(nome=nome, url_vagas="")

        for vaga in vagas:
            vaga["stacks"] = extrair_stacks(vaga.get("descricao", "") or vaga["titulo"])
            vaga["nivel"] = detectar_nivel(vaga["titulo"])
            vaga["urgente"] = detectar_urgencia(vaga.get("descricao", ""), vaga["titulo"])

            sinais = extrair_sinais_descricao(vaga.get("descricao", ""))
            if sinais["tamanho_equipe"]:
                vaga["tamanho_equipe"] = sinais["tamanho_equipe"]
            if sinais["volume_dados"]:
                vaga["volume_dados"] = sinais["volume_dados"]
            if sinais["estagio_empresa"]:
                vaga["estagio_empresa"] = sinais["estagio_empresa"]
            sal_min, sal_max = detectar_salario(vaga.get("descricao", ""))
            if sal_min > 0:
                vaga["salario_min"] = sal_min
                vaga["salario_max"] = sal_max
            vaga["empresa"] = nome
            h = gerar_hash(vaga["titulo"], nome, vaga["link"])
            with db_connect(read_only=True) as con_check:
                existe = con_check.execute("SELECT id FROM fact_vaga WHERE hash=?", [h]).fetchone()
            if existe:
                continue
            id_nova = inserir_vaga(vaga, id_empresa)
            if id_nova:
                vagas_novas += 1
                _auto_anya(id_nova, vaga.get("descricao", ""), vaga["titulo"], texto_cv)

        registrar_log(nome, vagas_encontradas, vagas_novas, "sucesso")
        log.info(f"  {vagas_encontradas} encontradas | {vagas_novas} novas")
        return vagas_encontradas, vagas_novas, ""

    except Exception as e:
        registrar_log(nome, 0, 0, "erro", str(e))
        log.error(f"  Erro: {e}")
        return 0, 0, str(e)


def processar_empresa_greenhouse(nome: str, slug: str) -> tuple[int, int, str]:
    vagas_raw = buscar_vagas_greenhouse(slug)
    return _processar_empresa_generica(nome, vagas_raw)


def processar_empresa_inhire(nome: str, url_inhire: str) -> tuple[int, int, str]:
    vagas_raw = buscar_vagas_inhire(url_inhire)
    return _processar_empresa_generica(nome, vagas_raw)


def processar_empresa_smartrecruiters(nome: str, url: str) -> tuple[int, int, str]:
    # URL stored as https://careers.smartrecruiters.com/CompanySlug — extract slug
    slug = url.rstrip("/").split("/")[-1]
    vagas_raw = buscar_vagas_smartrecruiters(slug)
    return _processar_empresa_generica(nome, vagas_raw)

def rodar_pipeline() -> None:
    criar_tabelas()
    
    with db_connect(read_only=True) as con:
        empresas = con.execute("""
            SELECT nome, url_vagas FROM dim_empresa
            WHERE ativa = true AND url_vagas IS NOT NULL AND url_vagas != ''
        """).fetchall()

    if not empresas:
        log.warning("Nenhuma empresa ativa no banco.")
        return

    log.info(f"\n{len(empresas)} empresa(s) ativa(s)")

    for nome, url_vagas in empresas:
        log.info(f"\nProcessando {nome}...")
        if "gupy.io" in url_vagas:
            processar_empresa(nome, url_vagas)
        elif "greenhouse.io" in url_vagas:
            slug = url_vagas.split("greenhouse.io/")[-1].split("/")[0]
            processar_empresa_greenhouse(nome, slug)
        elif "inhire.app" in url_vagas:
            processar_empresa_inhire(nome, url_vagas)
        elif "smartrecruiters.com" in url_vagas:
            processar_empresa_smartrecruiters(nome, url_vagas)    
        else:
            log.info(f"  Plataforma não reconhecida: {url_vagas}")

    log.info("\nSalvando snapshot...")
    salvar_snapshot()
    log.info("\nPipeline concluído.")


if __name__ == "__main__":
    rodar_pipeline()