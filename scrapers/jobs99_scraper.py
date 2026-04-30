import re
import html as _html
import requests
from logger import get_logger

log = get_logger("jobs99_scraper")

_API_BASE = "https://api-oportunidades.99jobs.com"
_TOKEN = "BrLyO1PEhykcq3N1PlQM0EdYkDI3"
_HEADERS = {"Authorization": f"Token token={_TOKEN}"}
_UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def _strip_html(texto: str) -> str:
    texto = _html.unescape(texto or "")
    return re.sub(r"<[^>]+>", " ", texto).strip()


def _get_company_id(url: str) -> int | None:
    """Descobre o company_id lendo o bundle JS da página de carreiras."""
    m = re.match(r"https?://([^.]+)\.99jobs\.com", url)
    if not m:
        return None
    subdomain = m.group(1)
    base = f"https://{subdomain}.99jobs.com"
    try:
        r = requests.get(base + "/", timeout=10, headers=_UA)
        js_paths = re.findall(r'href=["\']?(/js/app\.[^\s"\'<>]+\.js)', r.text)
        if not js_paths:
            log.warning(f"  Bundle JS não encontrado em {base}")
            return None
        js_url = base + js_paths[0]
        log.info(f"  Lendo bundle: {js_url}")
        js_r = requests.get(js_url, timeout=20, headers=_UA)
        m_id = re.search(r'companyId[:\s"]+(\d+)', js_r.text)
        if m_id:
            return int(m_id.group(1))
        log.warning(f"  companyId não encontrado no bundle de {subdomain}")
    except Exception as e:
        log.error(f"  Erro ao obter company_id de {url}: {e}")
    return None


def _map_nivel(level: str) -> str:
    s = (level or "").lower()
    if any(x in s for x in ("júnior", "junior", "estágio", "estagio", "trainee")):
        return "junior"
    if "pleno" in s:
        return "pleno"
    if any(x in s for x in ("sênior", "senior", "especialista")):
        return "senior"
    if any(x in s for x in ("lead", "líder", "lider", "coordenador", "gerente")):
        return "lead"
    return "não identificado"


def _map_modalidade(acting_mode: str) -> str:
    s = (acting_mode or "").lower()
    if "remoto" in s or "remote" in s:
        return "remoto"
    if "híbrido" in s or "hibrido" in s or "hybrid" in s:
        return "hibrido"
    if "presencial" in s or "on-site" in s:
        return "presencial"
    return "não identificado"


def buscar_vagas_99jobs(url: str, empresa: str) -> list[dict]:
    """Coleta vagas de uma empresa no 99jobs via API REST.

    Args:
        url: URL da página de carreiras (ex: https://gruposmartfit.99jobs.com/vagas/grupo/smart-fit).
        empresa: Nome da empresa.
    """
    company_id = _get_company_id(url)
    if not company_id:
        log.error(f"  Não foi possível identificar company_id para {empresa}")
        return []

    log.info(f"  company_id={company_id} | {empresa}")

    vagas: list[dict] = []
    page = 1
    while True:
        try:
            r = requests.get(
                f"{_API_BASE}/v1/opportunities",
                params={"company_id": company_id, "page": page},
                headers=_HEADERS,
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            log.error(f"  Erro na página {page}: {e}")
            break

        oportunidades = data.get("opportunities", [])
        total_pages = data.get("links", {}).get("total_pages", 1)
        log.info(f"  Página {page}/{total_pages} — {len(oportunidades)} vagas")

        for op in oportunidades:
            link = (
                op.get("links", {}).get("subscription")
                or op.get("links", {}).get("opportunity_99jobs")
                or ""
            )
            descricao = _strip_html(
                (op.get("responsability") or "") + " " + (op.get("requirement") or "")
            )
            address = op.get("address") or {}
            cidade = address.get("city", "")
            estado = (address.get("state") or {}).get("abbr", "")
            cidade_full = f"{cidade}/{estado}" if cidade and estado else cidade or estado

            vagas.append(
                {
                    "titulo": op.get("title", ""),
                    "link": link,
                    "fonte": "99jobs",
                    "empresa": empresa,
                    "descricao": descricao,
                    "modalidade": _map_modalidade(op.get("acting_mode", "")),
                    "nivel": _map_nivel(op.get("level", "")),
                    "cidade": cidade_full,
                    "pais": "br",
                    "urgente": False,
                }
            )

        if page >= total_pages:
            break
        page += 1

    log.info(f"  Total: {len(vagas)} vagas")
    return vagas


if __name__ == "__main__":
    import json

    vagas = buscar_vagas_99jobs(
        "https://gruposmartfit.99jobs.com/vagas/grupo/smart-fit",
        "Smart Fit",
    )
    log.info(f"\nSmart Fit: {len(vagas)} vagas")
    for v in vagas[:5]:
        log.info(f"  - {v['titulo']} | {v['cidade']} | {v['modalidade']}")
    with open("data/raw/vagas_99jobs.json", "w", encoding="utf-8") as f:
        json.dump(vagas, f, ensure_ascii=False, indent=2)
