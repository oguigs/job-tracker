"""
ats_score.py — CRUD para scores ATS pré-computados por vaga.
"""
from database.connection import db_connect


def salvar_ats_score(id_vaga: int, scores: dict):
    """Salva ou atualiza o score ANYA de uma vaga."""
    with db_connect() as con:
        existente = con.execute(
            "SELECT id FROM fact_ats_score WHERE id_vaga = ?", [id_vaga]
        ).fetchone()

        if existente:
            con.execute("""
                UPDATE fact_ats_score SET
                    score_keywords   = ?,
                    score_formatacao = ?,
                    score_secoes     = ?,
                    score_impacto    = ?,
                    score_final      = ?,
                    keywords_ausentes = ?,
                    keywords_presentes = ?,
                    data_calculo     = current_date
                WHERE id_vaga = ?
            """, [
                scores.get("score_keywords", 0),
                scores.get("score_formatacao", 0),
                scores.get("score_secoes", 0),
                scores.get("score_impacto", 0),
                scores.get("score_final", 0),
                ",".join(scores.get("keywords_ausentes", [])[:30]),
                ",".join(scores.get("keywords_presentes", [])[:30]),
                id_vaga,
            ])
        else:
            id_score = con.execute("SELECT nextval('seq_ats_score')").fetchone()[0]
            con.execute("""
                INSERT INTO fact_ats_score
                (id, id_vaga, score_keywords, score_formatacao,
                 score_secoes, score_impacto, score_final,
                 keywords_ausentes, keywords_presentes, data_calculo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, current_date)
            """, [
                id_score, id_vaga,
                scores.get("score_keywords", 0),
                scores.get("score_formatacao", 0),
                scores.get("score_secoes", 0),
                scores.get("score_impacto", 0),
                scores.get("score_final", 0),
                ",".join(scores.get("keywords_ausentes", [])[:30]),
                ",".join(scores.get("keywords_presentes", [])[:30]),
            ])


def carregar_ats_score(id_vaga: int) -> dict | None:
    """Retorna o score ATS de uma vaga específica ou None se não calculado."""
    with db_connect(read_only=True) as con:
        row = con.execute("""
            SELECT score_keywords, score_formatacao, score_secoes,
                   score_impacto, score_final, keywords_ausentes, keywords_presentes,
                   data_calculo
            FROM fact_ats_score WHERE id_vaga = ?
        """, [id_vaga]).fetchone()

    if not row:
        return None

    return {
        "score_keywords":    row[0],
        "score_formatacao":  row[1],
        "score_secoes":      row[2],
        "score_impacto":     row[3],
        "score_final":       row[4],
        "keywords_ausentes":  [k for k in row[5].split(",") if k] if row[5] else [],
        "keywords_presentes": [k for k in row[6].split(",") if k] if row[6] else [],
        "data_calculo":      str(row[7])[:10] if row[7] else "N/A",
    }


def listar_ats_scores() -> dict[int, int]:
    """Retorna {id_vaga: score_final} para exibir badges na listagem."""
    with db_connect(read_only=True) as con:
        rows = con.execute(
            "SELECT id_vaga, score_final FROM fact_ats_score"
        ).fetchall()
    return {r[0]: r[1] for r in rows}


def recalcular_todos(texto_cv: str):
    """Recalcula ANYA para todas as vagas ativas com descrição."""
    from transformers.ats_agents import rodar_anya
    import json

    with db_connect(read_only=True) as con:
        vagas = con.execute("""
            SELECT id, titulo, descricao, stacks
            FROM fact_vaga
            WHERE ativa = true
              AND descricao IS NOT NULL
              AND descricao != ''
        """).fetchall()

    total = 0
    for id_vaga, titulo, descricao, stacks_json in vagas:
        try:
            anya = rodar_anya(texto_cv, descricao or "", titulo or "")
            score_final = round(
                anya["score_keywords"]   * 0.40 +
                anya["score_formatacao"] * 0.25 +
                anya["score_secoes"]     * 0.20 +
                anya["score_impacto"]    * 0.15
            )
            anya["score_final"] = score_final
            salvar_ats_score(id_vaga, anya)
            total += 1
        except Exception:
            continue

    return total
