"""
ats_agents.py — Análise de currículo vs vaga com 4 agentes especializados.

ANYA        — ATS: keywords, formatação, seções, impacto (pure Python)
VANELLOPE   — Carreira: compatibilidade e posicionamento (Ollama)
ARYA        — Estratégia: como hackear o processo seletivo (Ollama)
SINTETIZADOR — Score final + brief unificado (pure Python + Ollama)
NEXUS       — Otimizador: reescreve título, resumo e bullets (Ollama)

Suporte bilíngue: pt-BR e en-US. Detecção automática ou seleção manual.
"""

import re
import requests
import ollama

_OLLAMA_MODEL  = "llama3.2"
_OLLAMA_URL    = "http://localhost:11434"

# Seções esperadas num currículo bem estruturado (bilíngue)
_SECOES_ESPERADAS = [
    ["experiência", "experience", "histórico profissional", "work experience", "professional experience"],
    ["educação", "education", "formação", "formacao", "academic background"],
    ["habilidades", "skills", "competências", "competencias", "tecnologias", "technical skills"],
    ["resumo", "summary", "objetivo", "sobre mim", "perfil", "profile", "about me", "objective"],
]

# Padrões de impacto quantificado (PT + EN)
_PADRAO_IMPACTO = re.compile(
    r"(\d+[\.,]?\d*\s*(%|x|k|m|bi|mil|milhões|bilhões|million|billion|"
    r"reduz|aument|economiz|entreg|process|impacto|resultado|melhori|"
    r"reduc|increas|deliver|improv|sav|generat|achiev))",
    re.IGNORECASE,
)

# Stopwords PT-BR + EN
_STOPWORDS = {
    # PT
    "e", "de", "da", "do", "em", "para", "com", "que", "os", "as",
    "um", "uma", "por", "mais", "ser", "ter", "nos", "nas", "ao",
    "ou", "se", "na", "no", "a", "o", "é", "são", "seu", "sua",
    "foi", "ele", "ela", "eles", "elas", "isso", "esta", "este",
    "nós", "nos", "das", "dos", "aos", "pela", "pelo", "entre",
    # EN
    "the", "and", "or", "of", "to", "in", "for", "with", "an",
    "be", "is", "are", "will", "you", "we", "our", "your", "this",
    "that", "it", "as", "at", "by", "from", "not", "but", "have",
    "has", "their", "on", "all", "who", "can", "also", "about",
    "was", "were", "been", "being", "they", "them", "its", "into",
    "such", "when", "which", "while", "both", "each", "more",
}

# Marcadores PT para detecção de idioma
_PT_MARKERS = {
    "de", "da", "do", "em", "para", "com", "que", "uma", "dos",
    "das", "por", "mais", "ser", "ter", "são", "está", "como",
    "experiência", "formação", "habilidades", "anos", "empresa",
}
# Marcadores EN para detecção de idioma
_EN_MARKERS = {
    "the", "and", "with", "for", "are", "have", "this", "that",
    "experience", "skills", "company", "years", "team", "work",
    "responsible", "developed", "managed", "led", "built",
}


def detectar_idioma(texto: str) -> str:
    """Detecta o idioma dominante do texto. Retorna 'pt-BR' ou 'en-US'."""
    palavras = set(re.findall(r"[a-záéíóúâêîôûãõça-z]+", texto.lower()))
    pts = len(palavras & _PT_MARKERS)
    ens = len(palavras & _EN_MARKERS)
    return "pt-BR" if pts >= ens else "en-US"


def _instrucao_idioma(idioma: str) -> str:
    if idioma == "en-US":
        return "Write your response in English."
    return "Escreva sua resposta em português brasileiro."


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

def rodar_vanellope(texto_cv: str, descricao_vaga: str, titulo_vaga: str, analise_anya: dict, idioma: str = "pt-BR") -> str:
    """Parágrafo estratégico de compatibilidade de carreira."""
    ausentes  = ", ".join(analise_anya["keywords_ausentes"][:15]) or "none"
    presentes = ", ".join(analise_anya["keywords_presentes"][:10]) or "none"
    lang      = _instrucao_idioma(idioma)

    prompt = f"""You are VANELLOPE, a career and recruitment specialist.
Analyze the compatibility between the resume and the job below. Write ONE direct and honest paragraph.

Be specific: mention the job title, relevant candidate experience and what is missing.
Give ONE concrete and practical action the candidate can take now to improve the fit.
Maximum 5 sentences. {lang}

JOB: {titulo_vaga}
JOB DESCRIPTION: {descricao_vaga[:800]}
KEYWORDS FOUND IN RESUME: {presentes}
MISSING KEYWORDS: {ausentes}
RESUME: {texto_cv[:1000]}
"""
    return _ollama_chat(prompt)


# ──────────────────────────────────────────────
# ARYA — Módulo Estratégia (Ollama)
# ──────────────────────────────────────────────

def rodar_arya(texto_cv: str, descricao_vaga: str, titulo_vaga: str, analise_anya: dict, idioma: str = "pt-BR") -> str:
    """Estratégia anti-sistema para passar pelo filtro ATS e entrevista."""
    ausentes = ", ".join(analise_anya["keywords_ausentes"][:12]) or "none"
    lang     = _instrucao_idioma(idioma)

    prompt = f"""You are ARYA, a recruitment strategist specialized in helping candidates pass ATS filters.
Write ONE paragraph with bold and practical strategy.

Include:
1. How to rephrase the job title or experience bullets to align with the job WITHOUT lying
2. Which missing keywords to naturally insert in the resume
3. How to sell the candidate's differentiator in the interview

Maximum 5 sentences. {lang}

JOB: {titulo_vaga}
MISSING KEYWORDS: {ausentes}
JOB DESCRIPTION: {descricao_vaga[:600]}
RESUME: {texto_cv[:800]}
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
    idioma: str = "pt-BR",
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
        lang = _instrucao_idioma(idioma)
        prompt = f"""You are the SYNTHESIZER, a system that compiles analyses from 3 specialized agents.
Write 2 sentences summarizing the diagnosis and the most important action for the candidate.
Tone: objective, no repetition of details already covered by the agents. {lang}

SCORE: {score}/100 — {status}
CAREER ANALYSIS: {texto_vanellope[:300]}
STRATEGY: {texto_arya[:300]}
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

def rodar_nexus(texto_cv: str, descricao_vaga: str, titulo_vaga: str, analise_anya: dict, idioma: str = "pt-BR") -> dict:
    """Reescreve título, resumo e bullets do currículo com as keywords da vaga.

    Retorna dict com:
        titulo_sugerido   — título alinhado à vaga
        resumo_otimizado  — parágrafo de abertura com keywords
        bullets           — lista de {"antes": str, "depois": str}
    """
    ausentes = ", ".join(analise_anya["keywords_ausentes"][:15]) or "none"
    lang     = _instrucao_idioma(idioma)

    prompt = f"""You are NEXUS, a resume optimization specialist.

Your task is to rewrite parts of the resume to increase the match with the job.
CRITICAL RULE: do NOT invent experience. Rewrite what already exists using the right keywords.
{lang}

JOB: {titulo_vaga}
JOB DESCRIPTION: {descricao_vaga[:700]}
MISSING KEYWORDS: {ausentes}
CURRENT RESUME: {texto_cv[:2000]}

Reply EXACTLY in this format (no extra text outside the fields):

TÍTULO_SUGERIDO:
[write a professional title aligned with the job]

RESUMO_OTIMIZADO:
[write a 2-3 sentence opening paragraph with job keywords]

BULLET_ANTES_1:
[copy an existing bullet point from the resume that can be improved]
BULLET_DEPOIS_1:
[rewrite that bullet with job keywords and business impact focus]

BULLET_ANTES_2:
[copy another existing bullet]
BULLET_DEPOIS_2:
[rewrite it]

BULLET_ANTES_3:
[copy another existing bullet]
BULLET_DEPOIS_3:
[rewrite it]"""

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
# CARTA — Agente de Carta de Apresentação (Ollama)
# ──────────────────────────────────────────────

def rodar_carta(texto_cv: str, descricao_vaga: str, titulo_vaga: str,
                empresa: str = "", idioma: str = "pt-BR") -> str:
    """Gera carta de apresentação personalizada baseada no CV e na vaga.

    O que hunters realmente leem:
    - Linha 1: por que ESSA empresa (não genérico)
    - 2-3 conquistas quantificadas alinhadas à vaga
    - Fit técnico explícito (stacks/ferramentas mencionadas)
    - Fechamento com call-to-action direto
    Máximo 3 parágrafos, ~250 palavras.
    """
    lang = _instrucao_idioma(idioma)
    empresa_str = empresa or "a empresa"

    prompt = f"""You are CARTA, a specialist in writing cover letters that get responses from headhunters.

Rules that headhunters follow when reading cover letters:
1. They spend ~10 seconds on the first paragraph — if it's generic, they stop
2. They look for 2-3 specific and quantified achievements relevant to the role
3. They check if the candidate mentions the tools/skills listed in the job description
4. They want a direct closing — not "I hope to hear from you" but "I am available for a call this week"

Write a cover letter in exactly 3 paragraphs:

PARAGRAPH 1 — Hook (2-3 sentences):
Mention something specific about {empresa_str} that motivates the candidacy.
Connect the candidate's main differentiation to the job's main need.
NO "I am writing to apply for the position" opener.

PARAGRAPH 2 — Proof (3-4 sentences):
Extract 2-3 concrete and quantified achievements from the resume that are directly relevant to the job.
Naturally mention 2-3 technical keywords from the job description.

PARAGRAPH 3 — Closing (2 sentences):
Show confidence, not desperation.
Specific and direct call-to-action.

{lang}

JOB: {titulo_vaga} at {empresa_str}
JOB DESCRIPTION: {descricao_vaga[:800]}
RESUME: {texto_cv[:1500]}
"""
    return _ollama_chat(prompt)


# ──────────────────────────────────────────────
# Entrada principal — roda os 4 agentes em sequência
# ──────────────────────────────────────────────

def analisar_curriculo(texto_cv: str, descricao_vaga: str, titulo_vaga: str = "", idioma: str = "auto") -> dict:
    """Roda os 4 agentes e retorna o resultado completo.

    Args:
        idioma: 'pt-BR', 'en-US' ou 'auto' (detecta automaticamente).
    """
    if idioma == "auto":
        idioma = detectar_idioma(texto_cv + " " + descricao_vaga)

    anya      = rodar_anya(texto_cv, descricao_vaga, titulo_vaga)
    vanellope = rodar_vanellope(texto_cv, descricao_vaga, titulo_vaga, anya, idioma)
    arya      = rodar_arya(texto_cv, descricao_vaga, titulo_vaga, anya, idioma)
    sintese   = rodar_sintetizador(anya, vanellope, arya, texto_cv, descricao_vaga, titulo_vaga, idioma)

    return {
        "anya":        anya,
        "vanellope":   vanellope,
        "arya":        arya,
        "sintetizador": sintese,
        "idioma":      idioma,
    }
