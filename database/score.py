import json
from database.connection import db_connect


def calcular_score(id_vaga: int, id_candidato: int) -> dict:
    with db_connect() as con:
        stacks_candidato = con.execute(
            """
            SELECT stack, categoria, nivel_stack
            FROM dim_candidato_stack WHERE id_candidato = ?
        """,
            [id_candidato],
        ).fetchall()
        stacks_vaga_raw = con.execute(
            "SELECT stacks FROM fact_vaga WHERE id = ?", [id_vaga]
        ).fetchone()

    if not stacks_candidato or not stacks_vaga_raw:
        return {
            "score": 0,
            "breakdown": {},
            "matches": [],
            "gaps": [],
            "total_vaga": 0,
            "total_match": 0,
        }

    candidato_set = {s[0].lower(): {"categoria": s[1], "nivel": s[2]} for s in stacks_candidato}
    try:
        stacks_vaga = (
            json.loads(stacks_vaga_raw[0])
            if isinstance(stacks_vaga_raw[0], str)
            else stacks_vaga_raw[0]
        )
    except Exception:
        return {
            "score": 0,
            "breakdown": {},
            "matches": [],
            "gaps": [],
            "total_vaga": 0,
            "total_match": 0,
        }

    vaga_lista = [
        {"stack": t.lower(), "categoria": cat}
        for cat, termos in stacks_vaga.items()
        for t in termos
    ]
    if not vaga_lista:
        return {
            "score": 0,
            "breakdown": {},
            "matches": [],
            "gaps": [],
            "total_vaga": 0,
            "total_match": 0,
        }

    matches, gaps, breakdown = [], [], {}
    for item in vaga_lista:
        stack, categoria = item["stack"], item["categoria"]
        if categoria not in breakdown:
            breakdown[categoria] = {"total": 0, "match": 0}
        breakdown[categoria]["total"] += 1
        if stack in candidato_set:
            matches.append(
                {"stack": stack, "categoria": categoria, "nivel": candidato_set[stack]["nivel"]}
            )
            breakdown[categoria]["match"] += 1
        else:
            gaps.append({"stack": stack, "categoria": categoria})

    score = round(len(matches) / len(vaga_lista) * 100) if vaga_lista else 0
    for cat in breakdown:
        t = breakdown[cat]["total"]
        breakdown[cat]["score"] = round(breakdown[cat]["match"] / t * 100) if t > 0 else 0

    return {
        "score": score,
        "matches": matches,
        "gaps": gaps,
        "breakdown": breakdown,
        "total_vaga": len(vaga_lista),
        "total_match": len(matches),
    }


def calcular_scores_todos(id_candidato: int) -> dict:
    with db_connect() as con:
        vagas = con.execute("""
            SELECT id FROM fact_vaga
            WHERE (negada = false OR negada IS NULL) AND ativa = true
        """).fetchall()
    return {id_vaga: calcular_score(id_vaga, id_candidato)["score"] for (id_vaga,) in vagas}
