"""
link_parser.py — Busca dados de uma vaga individual a partir do link.

Plataformas suportadas: Gupy, Greenhouse, Lever, 99jobs.
Retorna dict com: titulo, empresa, descricao, modalidade, link, fonte.
"""

import re
import json
import html as _html
import requests

_UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def _strip_html(texto: str) -> str:
    return re.sub(r"<[^>]+>", " ", _html.unescape(texto or "")).strip()


def _detectar_plataforma(url: str) -> str:
    if "gupy.io" in url:
        return "gupy"
    if "greenhouse.io" in url:
        return "greenhouse"
    if "lever.co" in url:
        return "lever"
    if "99jobs.com" in url:
        return "99jobs"
    return "desconhecida"


def _buscar_gupy(url: str) -> dict | None:
    try:
        r = requests.get(url, headers=_UA, timeout=15)
        m = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text, re.DOTALL
        )
        if not m:
            return None
        job = json.loads(m.group(1)).get("props", {}).get("pageProps", {}).get("job", {})
        if not job:
            return None

        empresa = job.get("companyName", "")
        if not empresa:
            sub = re.match(r"https?://([^.]+)\.gupy\.io", url)
            empresa = sub.group(1).replace("-", " ").title() if sub else ""

        descricao = " ".join(
            p
            for p in [
                _strip_html(job.get("description", "")),
                _strip_html(job.get("responsibilities", "")),
                _strip_html(job.get("prerequisites", "")),
            ]
            if p
        )
        wp = (job.get("workplaceType") or "").lower()
        modalidade = {
            "remote": "remoto",
            "remoto": "remoto",
            "hybrid": "hibrido",
            "presential": "presencial",
            "on-site": "presencial",
        }.get(wp, "não identificado")

        return {
            "titulo": job.get("name", ""),
            "empresa": empresa,
            "descricao": descricao,
            "modalidade": modalidade,
            "link": url,
            "fonte": "gupy",
        }
    except Exception:
        return None


def _buscar_greenhouse(url: str) -> dict | None:
    m = re.search(r"greenhouse\.io/([^/]+)/jobs/(\d+)", url)
    if not m:
        return None
    slug, job_id = m.group(1), m.group(2)
    try:
        r = requests.get(
            f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{job_id}?content=true",
            timeout=15,
        )
        if r.status_code != 200:
            return None
        job = r.json()
        location = job.get("location", {}).get("name", "")
        texto = (job.get("title", "") + " " + location).lower()
        modalidade = (
            "remoto"
            if "remote" in texto or "remoto" in texto
            else "hibrido"
            if "hybrid" in texto
            else "presencial"
            if location
            else "não identificado"
        )
        return {
            "titulo": job.get("title", ""),
            "empresa": slug.replace("-", " ").title(),
            "descricao": _strip_html(job.get("content", "")),
            "modalidade": modalidade,
            "link": url,
            "fonte": "greenhouse",
        }
    except Exception:
        return None


def _buscar_lever(url: str) -> dict | None:
    m = re.search(r"lever\.co/([^/?#]+)/([a-f0-9-]{36})", url)
    if not m:
        return None
    slug, job_id = m.group(1), m.group(2)
    try:
        r = requests.get(
            f"https://api.lever.co/v0/postings/{slug}/{job_id}?mode=json",
            headers={**_UA, "Accept": "application/json"},
            timeout=15,
        )
        if r.status_code != 200:
            return None
        job = r.json()
        wp = job.get("workplaceType", "").lower()
        modalidade = {"remote": "remoto", "hybrid": "hibrido", "on-site": "presencial"}.get(
            wp, "não identificado"
        )
        descricao = job.get("descriptionPlain", "") or _strip_html(job.get("description", ""))
        return {
            "titulo": job.get("text", ""),
            "empresa": slug.replace("-", " ").title(),
            "descricao": descricao,
            "modalidade": modalidade,
            "link": url,
            "fonte": "lever",
        }
    except Exception:
        return None


def _buscar_99jobs(url: str) -> dict | None:
    m = re.search(r"/vagas/(\d+)", url)
    if not m:
        return None
    job_id = m.group(1)
    try:
        from scrapers.jobs99_scraper import _TOKEN, _map_modalidade

        r = requests.get(
            f"https://api-oportunidades.99jobs.com/v1/opportunities/{job_id}",
            headers={"Authorization": f"Token token={_TOKEN}"},
            timeout=15,
        )
        if r.status_code != 200:
            return None
        raw = r.json().get("opportunity", {})
        op = raw[0] if isinstance(raw, list) and raw else raw if isinstance(raw, dict) else {}
        descricao = _strip_html(
            (op.get("responsability") or "") + " " + (op.get("requirement") or "")
        )
        return {
            "titulo": op.get("title", ""),
            "empresa": op.get("company_name", ""),
            "descricao": descricao,
            "modalidade": _map_modalidade(op.get("acting_mode", "")),
            "link": url,
            "fonte": "99jobs",
        }
    except Exception:
        return None


_BUSCADORES = {
    "gupy": _buscar_gupy,
    "greenhouse": _buscar_greenhouse,
    "lever": _buscar_lever,
    "99jobs": _buscar_99jobs,
}


def buscar_vaga_por_link(url: str) -> dict | None:
    """Detecta a plataforma e busca os dados da vaga pelo link.

    Retorna dict com titulo, empresa, descricao, modalidade, link, fonte.
    Retorna None se a plataforma não for suportada ou a busca falhar.
    """
    fn = _BUSCADORES.get(_detectar_plataforma(url))
    if not fn:
        return None
    return fn(url.strip())
