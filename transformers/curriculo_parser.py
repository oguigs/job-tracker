"""
curriculo_parser.py — Extrai texto e stacks do currículo em PDF.
"""

import pdfplumber
from transformers.stack_extractor import extrair_stacks


def extrair_texto_pdf(caminho_pdf: str) -> str:
    """Extrai texto bruto de um PDF."""
    texto = ""
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                texto += pagina.extract_text() or ""
    except Exception as e:
        print(f"Erro ao ler PDF: {e}")
    return texto


def extrair_stacks_curriculo(caminho_pdf: str) -> dict:
    """Extrai stacks do currículo via PDF."""
    texto = extrair_texto_pdf(caminho_pdf)
    if not texto:
        return {}
    return extrair_stacks(texto)


def gerar_diff_curriculo_vaga(stacks_curriculo: dict, stacks_vaga: dict) -> dict:
    """
    Compara stacks do currículo com as da vaga.
    Retorna matches (você tem), gaps (faltam) e extras (você tem mas a vaga não pede).
    """
    # flatten curriculo
    curriculo_set = set()
    for termos in stacks_curriculo.values():
        curriculo_set.update(t.lower() for t in termos)

    matches = []
    gaps = []

    for categoria, termos in stacks_vaga.items():
        for termo in termos:
            t_lower = termo.lower()
            if t_lower in curriculo_set:
                matches.append({"stack": termo, "categoria": categoria})
            else:
                gaps.append({"stack": termo, "categoria": categoria})

    # extras — você tem mas a vaga não pede
    vaga_set = set()
    for termos in stacks_vaga.values():
        vaga_set.update(t.lower() for t in termos)

    extras = [s for s in curriculo_set if s not in vaga_set]

    pct = round(len(matches) / (len(matches) + len(gaps)) * 100) if (matches or gaps) else 0

    return {
        "matches": matches,
        "gaps": gaps,
        "extras": extras,
        "pct_cobertura": pct,
    }
