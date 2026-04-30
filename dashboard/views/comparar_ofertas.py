import streamlit as st
from database.connection import db_connect
from database.score import calcular_score
from database.candidato import carregar_perfil
import json


def render():
    st.title("⚖️ Comparador de Ofertas")
    st.caption("Compare duas vagas em fase avançada lado a lado para tomar a melhor decisão.")

    with db_connect() as con:
        vagas = con.execute("""
            SELECT v.id, v.titulo, v.nivel, v.modalidade, v.regime,
                   v.salario_mensal, v.salario_anual_total, v.stacks,
                   v.candidatura_status, e.nome as empresa
            FROM fact_vaga v
            JOIN dim_empresa e ON v.id_empresa = e.id
            WHERE v.candidatura_status IN ('chamado','recrutador','fase_1','fase_2','fase_3','aprovado','inscrito')
            AND (v.negada = false OR v.negada IS NULL)
            ORDER BY v.candidatura_status DESC, e.nome
        """).fetchall()

    if len(vagas) < 2:
        from dashboard.ui_components import render_empty_state

        render_empty_state(
            "Poucas vagas em processo",
            "Você precisa de pelo menos 2 vagas em fase de candidatura/entrevista para comparar.",
        )
        return

    opcoes = {f"{v[9]} — {v[1][:45]} ({v[8]})": v for v in vagas}
    nomes = list(opcoes.keys())

    col1, col2 = st.columns(2)
    sel_a = col1.selectbox("Oferta A", nomes, index=0)
    sel_b = col2.selectbox("Oferta B", nomes, index=min(1, len(nomes) - 1))

    if sel_a == sel_b:
        st.warning("Selecione ofertas diferentes.")
        return

    va = opcoes[sel_a]
    vb = opcoes[sel_b]

    # scores de fit
    df_perfil = carregar_perfil()
    score_a = score_b = 0
    if not df_perfil.empty:
        id_cand = int(df_perfil.iloc[0]["id"])
        score_a = calcular_score(va[0], id_cand)["score"]
        score_b = calcular_score(vb[0], id_cand)["score"]

    st.divider()

    # tabela comparativa
    campos = [
        ("Empresa", va[9], vb[9]),
        ("Nível", va[2] or "—", vb[2] or "—"),
        ("Modalidade", va[3] or "—", vb[3] or "—"),
        ("Regime", va[4] or "—", vb[4] or "—"),
        (
            "Salário mensal",
            f"R$ {int(va[5]):,.0f}" if va[5] else "—",
            f"R$ {int(vb[5]):,.0f}" if vb[5] else "—",
        ),
        (
            "Total anual",
            f"R$ {int(va[6]):,.0f}" if va[6] else "—",
            f"R$ {int(vb[6]):,.0f}" if vb[6] else "—",
        ),
        ("Score de fit", f"🎯 {score_a}%", f"🎯 {score_b}%"),
        ("Status", va[8], vb[8]),
    ]

    col_campo, col_a, col_b = st.columns([2, 3, 3])
    col_campo.markdown("**Campo**")
    col_a.markdown(f"**{va[9]}**")
    col_b.markdown(f"**{vb[9]}**")
    st.divider()

    for campo, val_a, val_b in campos:
        col_campo, col_a, col_b = st.columns([2, 3, 3])
        col_campo.caption(campo)
        col_a.write(str(val_a))
        col_b.write(str(val_b))

    st.divider()

    # stacks exclusivas de cada uma
    try:
        stacks_a = set()
        stacks_b = set()
        for cat, termos in (json.loads(va[7]) if isinstance(va[7], str) else va[7] or {}).items():
            stacks_a.update(t.lower() for t in termos)
        for cat, termos in (json.loads(vb[7]) if isinstance(vb[7], str) else vb[7] or {}).items():
            stacks_b.update(t.lower() for t in termos)

        so_a = stacks_a - stacks_b
        so_b = stacks_b - stacks_a
        comuns = stacks_a & stacks_b

        if so_a or so_b or comuns:
            st.subheader("Stacks")
            col_a, col_com, col_b = st.columns(3)
            with col_a:
                st.caption(f"Só em {va[9]}")
                for s in sorted(so_a):
                    st.markdown(
                        f"<span style='background:#EBF3FB;color:#378ADD;padding:2px 6px;border-radius:8px;font-size:11px;margin:2px;display:inline-block'>{s}</span>",
                        unsafe_allow_html=True,
                    )
            with col_com:
                st.caption("Ambas pedem")
                for s in sorted(comuns):
                    st.markdown(
                        f"<span style='background:#E8F5F0;color:#1D9E75;padding:2px 6px;border-radius:8px;font-size:11px;margin:2px;display:inline-block'>{s}</span>",
                        unsafe_allow_html=True,
                    )
            with col_b:
                st.caption(f"Só em {vb[9]}")
                for s in sorted(so_b):
                    st.markdown(
                        f"<span style='background:#FBF0EB;color:#D85A30;padding:2px 6px;border-radius:8px;font-size:11px;margin:2px;display:inline-block'>{s}</span>",
                        unsafe_allow_html=True,
                    )
    except Exception:
        pass

    st.divider()

    # campo de afinidade pessoal
    st.subheader("Sua avaliação")
    col_af_a, col_af_b = st.columns(2)
    af_a = col_af_a.slider(f"Afinidade com {va[9]}", 1, 5, 3, key="af_a")
    af_b = col_af_b.slider(f"Afinidade com {vb[9]}", 1, 5, 3, key="af_b")

    # score final ponderado
    st.divider()
    peso_score = 0.4
    peso_salario = 0.3
    peso_afinidade = 0.3

    sal_max = max(va[5] or 0, vb[5] or 0)
    sal_norm_a = (va[5] or 0) / sal_max if sal_max > 0 else 0
    sal_norm_b = (vb[5] or 0) / sal_max if sal_max > 0 else 0

    final_a = round(
        (score_a / 100 * peso_score + sal_norm_a * peso_salario + af_a / 5 * peso_afinidade) * 100
    )
    final_b = round(
        (score_b / 100 * peso_score + sal_norm_b * peso_salario + af_b / 5 * peso_afinidade) * 100
    )

    col_fa, col_fb = st.columns(2)
    cor_a = "#1D9E75" if final_a >= final_b else "#888"
    cor_b = "#1D9E75" if final_b >= final_a else "#888"
    col_fa.markdown(
        f"<div style='text-align:center;padding:16px;background:#f8f8f8;border-radius:8px;border-left:4px solid {cor_a}'><div style='font-size:32px;font-weight:700;color:{cor_a}'>{final_a}</div><div style='font-size:12px;color:#888'>Score final {va[9]}</div></div>",
        unsafe_allow_html=True,
    )
    col_fb.markdown(
        f"<div style='text-align:center;padding:16px;background:#f8f8f8;border-radius:8px;border-left:4px solid {cor_b}'><div style='font-size:32px;font-weight:700;color:{cor_b}'>{final_b}</div><div style='font-size:12px;color:#888'>Score final {vb[9]}</div></div>",
        unsafe_allow_html=True,
    )
    st.caption("Score final = 40% fit técnico + 30% salário + 30% afinidade pessoal")
