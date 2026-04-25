from logger import get_logger
log = get_logger("gupy_detalhes")
import requests, re, json, html as html_lib, time, random


def _limpar_html(txt: str) -> str:
    return re.sub(r"<[^>]+>", " ", html_lib.unescape(txt or "")).strip()


def _extrair_descricao_gupy(link: str) -> dict:
    """
    Busca descrição completa de uma vaga Gupy via __NEXT_DATA__.
    Retorna dict com: descricao, modalidade, cidade (strings vazias se falhar).
    """
    try:
        r = requests.get(
            link,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
            timeout=15,
        )
        m = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            r.text, re.DOTALL
        )
        if not m:
            return {}

        job = json.loads(m.group(1)).get("props", {}).get("pageProps", {}).get("job", {})

        parts = [
            _limpar_html(job.get("description", "")),
            _limpar_html(job.get("responsibilities", "")),
            _limpar_html(job.get("prerequisites", "")),
        ]
        descricao = " ".join(p for p in parts if p and len(p) > 5)

        wp_type = (job.get("workplaceType") or "").lower()
        modalidade = ""
        if wp_type in ("remote", "remoto"):
            modalidade = "remoto"
        elif wp_type == "hybrid":
            modalidade = "hibrido"
        elif wp_type in ("presential", "on-site", "presencial"):
            modalidade = "presencial"

        return {
            "descricao":  descricao,
            "modalidade": modalidade,
            "cidade":     job.get("addressCity", ""),
        }
    except Exception as e:
        log.error(f"  Erro ao extrair descrição: {e}")
        return {}


def coletar_descricoes_lote(vagas: list) -> list:
    """
    Preenche campo 'descricao' de cada vaga via requests + __NEXT_DATA__.
    Sem Playwright. Também atualiza modalidade e cidade quando disponíveis.
    """
    from transformers.stack_extractor import extrair_stacks, detectar_urgencia

    if not vagas:
        return vagas

    log.info(f"  Coletando descrições de {len(vagas)} vagas (requests)...")

    for i, vaga in enumerate(vagas):
        link = vaga.get("link", "")
        if not link:
            continue

        info = _extrair_descricao_gupy(link)
        descricao = info.get("descricao", "")
        vaga["descricao"] = descricao

        if info.get("modalidade"):
            vaga["modalidade"] = info["modalidade"]
        if info.get("cidade"):
            vaga["cidade"] = info["cidade"]

        if descricao:
            stacks_desc = extrair_stacks(descricao)
            existing = vaga.get("stacks") or {}
            if isinstance(existing, str):
                try:
                    existing = json.loads(existing)
                except Exception:
                    existing = {}
            for cat, termos in stacks_desc.items():
                existing.setdefault(cat, [])
                existing[cat] = list(set(existing[cat] + termos))
            vaga["stacks"] = existing
            vaga["urgente"] = detectar_urgencia(descricao, vaga.get("titulo", ""))

        status = f"✓ {len(descricao)}ch" if descricao else "✗ sem desc"
        log.info(f"  [{i+1}/{len(vagas)}] {status} — {vaga['titulo'][:45]}")
        time.sleep(random.uniform(0.3, 0.8))

    log.info("  Descrições coletadas.")
    return vagas
