"""
ats_agents.py — Análise de currículo vs vaga com 4 agentes especializados.

ANYA        — ATS: keywords, formatação, seções, impacto (pure Python)
VANELLOPE   — Carreira: compatibilidade e posicionamento (Ollama)
ARYA        — Estratégia: como hackear o processo seletivo (Ollama)
SINTETIZADOR — Score final + brief unificado (pure Python + Ollama)
"""

import re
import requests
import ollama

_OLLAMA_MODEL  = "llama3.2"
_OLLAMA_URL    = "http://localhost:11434"

# Seções esperadas num currículo bem estruturado
_SECOES_ESPERADAS = [
    ["experiência", "experience", "histórico profissional"],
    ["educação", "education", "formação", "formacao"],
    ["habilidades", "skills", "competências", "competencias", "tecnologias"],
    ["resumo", "summary", "objetivo", "sobre mim", "perfil"],
]

# Padrões que indicam impacto quantificado
_PADRAO_IMPACTO = re.compile(
    r"(\d+[\.,]?\d*\s*(%|x|k|m|bi|mil|milhões|bilhões|reduz|aument|economiz|entreg|process|impacto|resultado|melhori))",
    re.IGNORECASE,
)

# Stopwords para extração de keywords da vaga
_STOPWORDS = {
    "e", "de", "da", "do", "em", "para", "com", "que", "os", "as",
    "um", "uma", "por", "mais", "ser", "ter", "nos", "nas", "ao",
    "ou", "se", "na", "no", "a", "o", "é", "são", "seu", "sua",
    "the", "and", "or", "of", "to", "in", "for", "with", "a", "an",
    "be", "is", "are", "will", "you", "we", "our", "your", "this",
    "that", "it", "as", "at", "by", "from", "not", "but", "have",
    "has", "their", "on", "all", "who", "can", "also", "about",
}


def ollama_disponivel() -> bool:
    """Verifica se o serviço Ollama está rodando."""
    try:
        r = requests.get(_OLLAMA_URL, timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def _ollama_chat(prompt: str) -> str:
    """Envia prompt para o Ollama e retorna o texto gerado."""
    resp = ollama.chat(
        model=_OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.4, "num_predict": 350},
    )
    return resp["message"]["content"].strip()


def _extrair_keywords(texto: str, min_len: int = 4) -> set[str]:
    """Extrai keywords relevantes de um texto removendo stopwords."""
    palavras = re.findall(r"[a-záéíóúâêîôûãõçà\w]+", texto.lower())
    return {p for p in palavras if len(p) >= min_len and p not in _STOPWORDS}


def _checar_secoes(texto_cv: str) -> dict:
    """Verifica quais seções esperadas existem no currículo."""
    texto_lower = texto_cv.lower()
    resultado = {}
    for grupo in _SECOES_ESPERADAS:
        nome_secao = grupo[0]
        encontrada = any(termo in texto_lower for termo in grupo)
        resultado[nome_secao] = encontrada
    return resultado


def _checar_impacto(texto_cv: str) -> dict:
    """Detecta bullet points com métricas quantificadas."""
    ocorrencias = _PADRAO_IMPACTO.findall(texto_cv)
    total_bullets = len(re.findall(r"^[\-•▸▶*]\s", texto_cv, re.MULTILINE))
    return {
        "ocorrencias": len(ocorrencias),
        "total_bullets": total_bullets,
        "exemplos": [m[0] for m in ocorrencias[:3]],
    }


# ──────────────────────────────────────────────
# ANYA — Módulo ATS (pure Python)
# ──────────────────────────────────────────────

def rodar_anya(texto_cv: str, descricao_vaga: str, titulo_vaga: str = "") -> dict:
    """Analisa match de keywords, formatação, seções e impacto."""

    kw_vaga = _extrair_keywords(descricao_vaga)
    kw_cv   = _extrair_keywords(texto_cv)

    presentes = sorted(kw_vaga & kw_cv)
    ausentes  = sorted(kw_vaga - kw_cv)

    score_keywords = round(len(presentes) / len(kw_vaga) * 100) if kw_vaga else 0

    # formatação: penaliza CVs com pouco texto ou sem estrutura
    tem_bullets   = bool(re.search(r"^[\-•▸▶*]\s", texto_cv, re.MULTILINE))
    tem_datas     = bool(re.search(r"\b(20\d\d|19\d\d)\b", texto_cv))
    tem_email     = bool(re.search(r"[\w.]+@[\w.]+\.\w+", texto_cv))
    tem_linkedin  = "linkedin" in texto_cv.lower()
    tamanho_ok    = len(texto_cv) > 500

    pontos_fmt = sum([tem_bullets, tem_datas, tem_email, tem_linkedin, tamanho_ok])
    score_formatacao = round(pontos_fmt / 5 * 100)

    # seções
    secoes = _checar_secoes(texto_cv)
    secoes_ok = sum(secoes.values())
    score_secoes = round(secoes_ok / len(secoes) * 100)

    # impacto
    impacto = _checar_impacto(texto_cv)
    if impacto["ocorrencias"] >= 5:
        score_impacto = 100
    elif impacto["ocorrencias"] >= 3:
        score_impacto = 70
    elif impacto["ocorrencias"] >= 1:
        score_impacto = 40
    else:
        score_impacto = 0

    return {
        "score_keywords":   score_keywords,
        "score_formatacao": score_formatacao,
        "score_secoes":     score_secoes,
        "score_impacto":    score_impacto,
        "keywords_presentes": presentes,
        "keywords_ausentes":  ausentes,
        "secoes":             secoes,
        "impacto":            impacto,
        "formatacao": {
            "tem_bullets":  tem_bullets,
            "tem_datas":    tem_datas,
            "tem_email":    tem_email,
            "tem_linkedin": tem_linkedin,
            "tamanho_ok":   tamanho_ok,
        },
    }


# ──────────────────────────────────────────────
# VANELLOPE — Módulo Carreira (Groq)
# ──────────────────────────────────────────────

def rodar_vanellope(texto_cv: str, descricao_vaga: str, titulo_vaga: str, analise_anya: dict) -> str:
    """Parágrafo estratégico de compatibilidade de carreira."""
    ausentes = ", ".join(analise_anya["keywords_ausentes"][:15]) or "nenhuma"
    presentes = ", ".join(analise_anya["keywords_presentes"][:10]) or "nenhuma"

    prompt = f"""Você é uma especialista em carreira e recrutamento no Brasil chamada VANELLOPE.
Analise a compatibilidade entre o currículo e a vaga abaixo e escreva UM parágrafo direto e honesto.

Seja específica: mencione o cargo da vaga, experiências relevantes do candidato e o que falta.
Dê UMA ação concreta e prática que o candidato pode fazer agora para melhorar o fit.
Escreva em português, tom direto, sem rodeios. Máximo 5 frases.

VAGA: {titulo_vaga}
DESCRIÇÃO DA VAGA (resumo): {descricao_vaga[:800]}

KEYWORDS PRESENTES NO CURRÍCULO: {presentes}
KEYWORDS AUSENTES: {ausentes}

CURRÍCULO (resumo): {texto_cv[:1000]}
"""
    return _ollama_chat(prompt)


# ──────────────────────────────────────────────
# ARYA — Módulo Estratégia (Ollama)
# ──────────────────────────────────────────────

def rodar_arya(texto_cv: str, descricao_vaga: str, titulo_vaga: str, analise_anya: dict) -> str:
    """Estratégia anti-sistema para passar pelo filtro ATS e entrevista."""
    ausentes = ", ".join(analise_anya["keywords_ausentes"][:12]) or "nenhuma"

    prompt = f"""Você é uma estrategista de recrutamento chamada ARYA, especialista em ajudar candidatos a passarem por filtros ATS.
Escreva UM parágrafo com estratégia prática e ousada.

Inclua:
1. Como refraseiar o título ou experiências para alinhar com a vaga SEM mentir
2. Quais keywords ausentes inserir naturalmente no currículo
3. Como vender o diferencial na entrevista

Escreva em português, tom direto e estratégico. Máximo 5 frases.

VAGA: {titulo_vaga}
KEYWORDS QUE FALTAM NO CURRÍCULO: {ausentes}
DESCRIÇÃO DA VAGA (resumo): {descricao_vaga[:600]}
CURRÍCULO (resumo): {texto_cv[:800]}
"""
    return _ollama_chat(prompt)


# ──────────────────────────────────────────────
# SINTETIZADOR — Score final + brief (pure Python + Ollama)
# ──────────────────────────────────────────────

def rodar_sintetizador(
    analise_anya: dict,
    texto_vanellope: str,
    texto_arya: str,
    texto_cv: str,
    descricao_vaga: str,
    titulo_vaga: str,
) -> dict:
    """Compila os 3 agentes num score final e um brief unificado."""

    # score final ponderado
    score = round(
        analise_anya["score_keywords"]   * 0.40 +
        analise_anya["score_formatacao"] * 0.25 +
        analise_anya["score_secoes"]     * 0.20 +
        analise_anya["score_impacto"]    * 0.15
    )

    if score >= 75:
        status = "COMPATÍVEL"
    elif score >= 50:
        status = "PARCIALMENTE COMPATÍVEL"
    elif score >= 25:
        status = "REQUER AJUSTES"
    else:
        status = "INCOMPATÍVEL"

    # brief unificado via Ollama (opcional — só roda se os agentes LLM rodaram)
    brief = ""
    if texto_vanellope and texto_arya:
        prompt = f"""Você é o SINTETIZADOR, um sistema que compila análises de 3 agentes especializados.
Escreva 2 frases resumindo o diagnóstico e a ação mais importante para o candidato.
Tom: objetivo, sem repetir o que os agentes já disseram em detalhes.

SCORE: {score}/100 — {status}
ANÁLISE DE CARREIRA: {texto_vanellope[:300]}
ESTRATÉGIA: {texto_arya[:300]}
"""
        try:
            brief = _ollama_chat(prompt)
        except Exception:
            brief = ""

    return {
        "score":  score,
        "status": status,
        "brief":  brief,
        "dimensoes": {
            "KEYWORDS":   analise_anya["score_keywords"],
            "FORMATAÇÃO": analise_anya["score_formatacao"],
            "SEÇÕES":     analise_anya["score_secoes"],
            "IMPACTO":    analise_anya["score_impacto"],
        },
    }


# ──────────────────────────────────────────────
# NEXUS — Agente Otimizador (Ollama)
# ──────────────────────────────────────────────

def rodar_nexus(texto_cv: str, descricao_vaga: str, titulo_vaga: str, analise_anya: dict) -> dict:
    """Reescreve título, resumo e bullets do currículo com as keywords da vaga.

    Retorna dict com:
        titulo_sugerido   — título alinhado à vaga
        resumo_otimizado  — parágrafo de abertura com keywords
        bullets           — lista de {"antes": str, "depois": str}
    """
    ausentes = ", ".join(analise_anya["keywords_ausentes"][:15]) or "nenhuma"

    prompt = f"""Você é NEXUS, especialista em otimização de currículos para o mercado brasileiro.

Sua tarefa é reescrever partes do currículo para aumentar o match com a vaga.
REGRA CRÍTICA: não invente experiências. Reescreva o que já existe usando as keywords certas.

VAGA: {titulo_vaga}
DESCRIÇÃO DA VAGA: {descricao_vaga[:700]}
KEYWORDS AUSENTES NO CURRÍCULO: {ausentes}
CURRÍCULO ATUAL: {texto_cv[:2000]}

Responda EXATAMENTE neste formato (sem texto extra fora dos campos):

TÍTULO_SUGERIDO:
[escreva aqui um título profissional alinhado à vaga]

RESUMO_OTIMIZADO:
[escreva aqui um parágrafo de 2-3 frases para o topo do currículo com as keywords da vaga]

BULLET_ANTES_1:
[copie aqui um bullet point existente do currículo que pode ser melhorado]
BULLET_DEPOIS_1:
[reescreva esse bullet com as keywords da vaga e foco em resultado de negócio]

BULLET_ANTES_2:
[copie aqui outro bullet point existente]
BULLET_DEPOIS_2:
[reescreva esse bullet]

BULLET_ANTES_3:
[copie aqui outro bullet point existente]
BULLET_DEPOIS_3:
[reescreva esse bullet]"""

    raw = _ollama_chat(prompt)
    return _parsear_nexus(raw)


def _parsear_nexus(raw: str) -> dict:
    """Extrai campos estruturados da resposta do NEXUS."""

    def _extrair(chave: str) -> str:
        pattern = rf"{re.escape(chave)}:\s*\n?(.*?)(?=\n[A-Z_]+:|$)"
        m = re.search(pattern, raw, re.DOTALL | re.IGNORECASE)
        return m.group(1).strip() if m else ""

    titulo    = _extrair("TÍTULO_SUGERIDO")
    resumo    = _extrair("RESUMO_OTIMIZADO")

    bullets = []
    for i in range(1, 4):
        antes  = _extrair(f"BULLET_ANTES_{i}")
        depois = _extrair(f"BULLET_DEPOIS_{i}")
        if antes and depois:
            bullets.append({"antes": antes, "depois": depois})

    return {
        "titulo_sugerido":  titulo,
        "resumo_otimizado": resumo,
        "bullets":          bullets,
        "raw":              raw,
    }


# ──────────────────────────────────────────────
# Entrada principal — roda os 4 agentes em sequência
# ──────────────────────────────────────────────

def analisar_curriculo(texto_cv: str, descricao_vaga: str, titulo_vaga: str = "") -> dict:
    """Roda os 4 agentes e retorna o resultado completo."""
    anya      = rodar_anya(texto_cv, descricao_vaga, titulo_vaga)
    vanellope = rodar_vanellope(texto_cv, descricao_vaga, titulo_vaga, anya)
    arya      = rodar_arya(texto_cv, descricao_vaga, titulo_vaga, anya)
    sintese   = rodar_sintetizador(anya, vanellope, arya, texto_cv, descricao_vaga, titulo_vaga)

    return {
        "anya":        anya,
        "vanellope":   vanellope,
        "arya":        arya,
        "sintetizador": sintese,
    }
