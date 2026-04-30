"""
backfill.py — preenche descrições para vagas existentes sem descrição.
"""

from logger import get_logger

log = get_logger("backfill")

import re
import json as _json
import time
import random


def _limpar_html(txt: str) -> str:
    import html as html_lib

    return re.sub(r"<[^>]+>", " ", html_lib.unescape(txt or "")).strip()


def _fetch_gupy(link: str) -> str:
    import requests

    try:
        r = requests.get(
            link,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            },
            timeout=15,
        )
        m = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            r.text,
            re.DOTALL,
        )
        if not m:
            return ""
        job = _json.loads(m.group(1)).get("props", {}).get("pageProps", {}).get("job", {})
        parts = [
            _limpar_html(job.get("description", "")),
            _limpar_html(job.get("responsibilities", "")),
            _limpar_html(job.get("prerequisites", "")),
        ]
        return " ".join(p for p in parts if p and len(p) > 5)
    except Exception as e:
        log.error(f"  Gupy backfill erro: {e}")
        return ""


def _fetch_greenhouse(link: str) -> str:
    """Extract job ID from URL and call Greenhouse API."""
    import requests

    try:
        # URL: https://boards.greenhouse.io/company/jobs/12345678
        m = re.search(r"/jobs/(\d+)", link)
        if not m:
            return ""
        job_id = m.group(1)
        slug_m = re.search(r"greenhouse\.io/([^/]+)/jobs", link)
        if not slug_m:
            return ""
        slug = slug_m.group(1)
        r = requests.get(
            f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{job_id}",
            timeout=10,
        )
        if r.status_code != 200:
            return ""
        content = r.json().get("content", "")
        return _limpar_html(content)
    except Exception as e:
        log.error(f"  Greenhouse backfill erro: {e}")
        return ""


def _fetch_smartrecruiters(link: str) -> str:
    """Extract company slug and job ID from URL and call SmartRecruiters API."""
    import requests

    try:
        # URL: https://jobs.smartrecruiters.com/CompanySlug/744000123456
        parts = link.rstrip("/").split("/")
        job_id = parts[-1]
        slug = parts[-2]
        r = requests.get(
            f"https://api.smartrecruiters.com/v1/companies/{slug}/postings/{job_id}",
            timeout=10,
        )
        if r.status_code != 200:
            return ""
        sections = r.json().get("jobAd", {}).get("sections", {})
        desc = _limpar_html(sections.get("jobDescription", {}).get("text", ""))
        qual = _limpar_html(sections.get("qualifications", {}).get("text", ""))
        return f"{desc} {qual}".strip()
    except Exception as e:
        log.error(f"  SmartRecruiters backfill erro: {e}")
        return ""


def preencher_descricoes_faltantes(callback=None) -> dict:
    """
    Fetches descriptions for all active vagas without one.
    callback(current, total, titulo) — optional progress hook for UI.
    Returns {"total": N, "preenchidas": K, "erros": E}.
    """
    from database.vagas import listar_vagas_sem_descricao, atualizar_descricao_vaga
    from database.candidato import carregar_curriculo_texto
    from database.ats_score import salvar_ats_score
    from transformers.stack_extractor import extrair_stacks, detectar_modalidade

    vagas = listar_vagas_sem_descricao()
    total = len(vagas)
    preenchidas = 0
    erros = 0

    texto_cv = carregar_curriculo_texto()

    log.info(f"Backfill: {total} vagas sem descrição")

    for i, (id_vaga, titulo, link, fonte) in enumerate(vagas):
        if callback:
            callback(i + 1, total, titulo)

        descricao = ""
        try:
            if fonte == "gupy":
                descricao = _fetch_gupy(link)
            elif fonte == "greenhouse":
                descricao = _fetch_greenhouse(link)
            elif fonte == "smartrecruiters":
                descricao = _fetch_smartrecruiters(link)
            # inhire: skip (SPA, needs Playwright — run pipeline normally)
        except Exception as e:
            log.error(f"  [{fonte}] {titulo[:40]}: {e}")
            erros += 1
            continue

        if not descricao:
            erros += 1
            log.info(f"  [{i + 1}/{total}] ✗ {fonte} — {titulo[:40]}")
            time.sleep(0.2)
            continue

        stacks = extrair_stacks(descricao)
        modalidade = detectar_modalidade(descricao)
        atualizar_descricao_vaga(id_vaga, descricao, _json.dumps(stacks), modalidade)
        preenchidas += 1
        log.info(f"  [{i + 1}/{total}] ✓ {len(descricao)}ch — {titulo[:40]}")

        # re-run ANYA if CV available
        if texto_cv:
            try:
                from transformers.ats_agents import rodar_anya

                anya = rodar_anya(texto_cv, descricao, titulo)
                anya["score_final"] = round(
                    anya["score_keywords"] * 0.40
                    + anya["score_formatacao"] * 0.25
                    + anya["score_secoes"] * 0.20
                    + anya["score_impacto"] * 0.15
                )
                salvar_ats_score(id_vaga, anya)
            except Exception:
                pass

        time.sleep(random.uniform(0.3, 0.7))

    log.info(f"Backfill concluído: {preenchidas}/{total} preenchidas, {erros} erros")
    return {"total": total, "preenchidas": preenchidas, "erros": erros}
