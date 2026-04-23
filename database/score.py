import json
from database.connection import conectar

def calcular_score(id_vaga: int, id_candidato: int) -> dict:
    """
    Calcula o score de fit entre o candidato e a vaga.
    Retorna um dict com score geral e breakdown por categoria.
    """
    con = conectar()

    # stacks do candidato
    stacks_candidato = con.execute("""
        SELECT stack, categoria, nivel_stack
        FROM dim_candidato_stack
        WHERE id_candidato = ?
    """, [id_candidato]).fetchall()

    # stacks da vaga
    stacks_vaga_raw = con.execute("""
        SELECT stacks FROM fact_vaga WHERE id = ?
    """, [id_vaga]).fetchone()

    con.close()

    if not stacks_candidato or not stacks_vaga_raw:
        return {"score": 0, "breakdown": {}, "matches": [], "gaps": []}

    # monta set de stacks do candidato
    candidato_set = {s[0].lower(): {"categoria": s[1], "nivel": s[2]}
                     for s in stacks_candidato}

    # monta lista de stacks da vaga
    try:
        stacks_vaga = json.loads(stacks_vaga_raw[0]) if isinstance(stacks_vaga_raw[0], str) else stacks_vaga_raw[0]
    except Exception:
        return {"score": 0, "breakdown": {}, "matches": [], "gaps": []}

    vaga_lista = []
    for categoria, termos in stacks_vaga.items():
        for termo in termos:
            vaga_lista.append({"stack": termo.lower(), "categoria": categoria})

    if not vaga_lista:
        return {"score": 0, "breakdown": {}, "matches": [], "gaps": []}

    # calcula matches e gaps
    matches = []
    gaps = []
    breakdown = {}

    for item in vaga_lista:
        stack = item["stack"]
        categoria = item["categoria"]

        if categoria not in breakdown:
            breakdown[categoria] = {"total": 0, "match": 0}
        breakdown[categoria]["total"] += 1

        if stack in candidato_set:
            matches.append({
                "stack": stack,
                "categoria": categoria,
                "nivel": candidato_set[stack]["nivel"]
            })
            breakdown[categoria]["match"] += 1
        else:
            gaps.append({"stack": stack, "categoria": categoria})

    # score geral
    score = round(len(matches) / len(vaga_lista) * 100) if vaga_lista else 0

    # score por categoria
    for cat in breakdown:
        total = breakdown[cat]["total"]
        match = breakdown[cat]["match"]
        breakdown[cat]["score"] = round(match / total * 100) if total > 0 else 0

    return {
        "score": score,
        "matches": matches,
        "gaps": gaps,
        "breakdown": breakdown,
        "total_vaga": len(vaga_lista),
        "total_match": len(matches)
    }

def calcular_scores_todos(id_candidato: int) -> dict:
    """Calcula score para todas as vagas ativas."""
    con = conectar()
    vagas = con.execute("""
        SELECT id FROM fact_vaga
        WHERE (negada = false OR negada IS NULL) AND ativa = true
    """).fetchall()
    con.close()

    scores = {}
    for (id_vaga,) in vagas:
        resultado = calcular_score(id_vaga, id_candidato)
        scores[id_vaga] = resultado["score"]

    return scores