import os
import json
import uuid
import streamlit as st
from dashboard.stack_config import get_stack_icon_url, get_stack_roadmap_url, get_categoria_cor
from database.score import calcular_score
from database.candidato import carregar_perfil
from utils import safe_str, nivel_fmt, modal_fmt
from dashboard.theme import status_badge, cor_score as get_cor_score
from database.diario import adicionar_nota, listar_notas, deletar_nota
from database.contatos import listar_contatos
from database.connection import db_connect
from database.candidaturas import salvar_remuneracao, atualizar_candidatura, negar_vaga
from database.schemas import TIMELINE, TIMELINE_LABELS


@st.cache_data
def get_favicon(nome: str, favicon_url: str = "") -> str:
    nome_arquivo = nome.lower().replace(" ", "_").replace("&", "e")
    caminho_local = f"dashboard/static/favicons/{nome_arquivo}.png"
    if os.path.exists(caminho_local):
        return caminho_local
    return favicon_url or ""


def render_stacks(stacks_json):
    try:
        stacks = json.loads(stacks_json) if isinstance(stacks_json, str) else stacks_json
        if not stacks:
            return
        st.write("**Stacks:**")
        for categoria, termos in stacks.items():
            if not termos:
                continue
            cor = get_categoria_cor(categoria)
            st.markdown(
                f"<span style='font-size:11px;font-weight:600;color:{cor['text']};"
                f"text-transform:uppercase;letter-spacing:0.5px'>{categoria}</span>",
                unsafe_allow_html=True)
            badges_html = "<div style='display:flex;flex-wrap:wrap;gap:4px;margin-bottom:8px'>"
            for termo in termos:
                icon_url = get_stack_icon_url(termo)
                roadmap_url = get_stack_roadmap_url(termo)
                icon_tag = f'<img src="{icon_url}" width="14" style="vertical-align:middle;margin-right:4px">' if icon_url else ""
                estilo = (f"display:inline-flex;align-items:center;padding:3px 10px;"
                         f"border-radius:12px;font-size:12px;font-weight:500;"
                         f"background:{cor['bg']};color:{cor['text']};"
                         f"border:1px solid {cor['border']};text-decoration:none;")
                if roadmap_url:
                    badges_html += f'<a href="{roadmap_url}" target="_blank" style="{estilo}">{icon_tag}{termo}</a>'
                else:
                    badges_html += f'<span style="{estilo}">{icon_tag}{termo}</span>'
            badges_html += "</div>"
            st.markdown(badges_html, unsafe_allow_html=True)
    except Exception:
        pass


def render_score_breakdown(id_vaga: int):
    df_perfil = carregar_perfil()
    if df_perfil.empty:
        return
    id_candidato = int(df_perfil.iloc[0]["id"])
    resultado = calcular_score(id_vaga, id_candidato)
    if not resultado["score"]:
        return
    score = resultado["score"]
    matches = resultado["matches"]
    gaps = resultado["gaps"]
    breakdown = resultado["breakdown"]
    cor = "#1D9E75" if score >= 70 else "#BA7517" if score >= 40 else "#D85A30"
    st.markdown(
        f"<div style='margin:4px 0 8px 0'>"
        f"<span style='font-size:12px;color:{cor};font-weight:700'>"
        f"Score de fit: {score}% ({resultado['total_match']}/{resultado['total_vaga']} stacks)</span>"
        f"<div style='background:#f0f0f0;border-radius:6px;height:8px;margin-top:4px'>"
        f"<div style='background:{cor};width:{score}%;height:8px;border-radius:6px'></div>"
        f"</div></div>", unsafe_allow_html=True)
    if breakdown:
        col_match, col_gap = st.columns(2)
        with col_match:
            if matches:
                st.markdown("**✅ Você tem:**")
                for m in matches:
                    st.markdown(
                        f"<span style='background:#E8F5F0;color:#157A5A;padding:2px 8px;"
                        f"border-radius:10px;font-size:11px;margin:2px;display:inline-block'>"
                        f"✓ {m['stack']} ({m['nivel']})</span>", unsafe_allow_html=True)
        with col_gap:
            if gaps:
                st.markdown("**❌ Faltam:**")
                for g in gaps:
                    st.markdown(
                        f"<span style='background:#FBF0EB;color:#A83A18;padding:2px 8px;"
                        f"border-radius:10px;font-size:11px;margin:2px;display:inline-block'>"
                        f"✗ {g['stack']}</span>", unsafe_allow_html=True)


def render_diario(id_vaga: int, prefix: str = "v"):
    st.divider()
    st.write("**Diário de candidatura:**")
    df_notas = listar_notas(id_vaga)
    if not df_notas.empty:
        for _, nota in df_notas.iterrows():
            impressao = nota.get("impressao") or ""
            icone = {"positivo": "😊", "neutro": "😐", "negativo": "😟"}.get(impressao, "")
            col_data, col_nota, col_del = st.columns([1.5, 6, 0.5])
            data_str = str(nota["data_nota"])[:10] if str(nota["data_nota"]) not in ["NaT","None","nan"] else "hoje"
            col_data.caption(data_str)
            col_nota.write(f"{icone} {nota['nota']}" if icone else nota["nota"])
            if col_del.button("✕", key=f"del_nota_{nota['id']}"):
                deletar_nota(nota["id"])
                st.session_state[f"dialog_{prefix}_atual"] = id_vaga
                st.rerun()
    else:
        st.caption("Nenhuma nota ainda.")
    nota_counter_key = f"nota_counter_{id_vaga}"
    if nota_counter_key not in st.session_state:
        st.session_state[nota_counter_key] = 0

    nova_nota_key = f"nova_nota_{id_vaga}_{st.session_state[nota_counter_key]}"
    impressao_key = f"nova_impressao_{id_vaga}_{st.session_state[nota_counter_key]}"

    nova_nota = st.text_area("Nova nota", placeholder="Ex: Ligaram do RH...",
                             height=80, label_visibility="collapsed",
                             key=nova_nota_key)
    impressao_sel = st.radio("Impressão", ["😊 Positivo", "😐 Neutro", "😟 Negativo"],
        horizontal=True, index=1, key=impressao_key)
    if st.button("Adicionar nota", use_container_width=True, key=f"btn_nota_{id_vaga}"):
        if nova_nota.strip():
            imp_map = {"😊 Positivo": "positivo", "😐 Neutro": "neutro", "😟 Negativo": "negativo"}
            adicionar_nota(id_vaga, nova_nota.strip(), imp_map[impressao_sel])
            st.session_state[nota_counter_key] += 1
            st.session_state[f"dialog_{prefix}_atual"] = id_vaga
            st.toast("✅ Nota adicionada!")
            st.rerun()


def render_preparacao_entrevista(id_vaga: int, id_empresa_nome: str, status_cand: str):
    fases_entrevista = ["chamado", "recrutador", "fase_1", "fase_2", "fase_3"]
    if status_cand not in fases_entrevista:
        return
    with db_connect() as con:
        id_empresa = con.execute("SELECT id FROM dim_empresa WHERE nome = ?", [id_empresa_nome]).fetchone()
    if not id_empresa:
        return
    id_empresa = id_empresa[0]
    st.divider()
    st.markdown(
        "<div style='background:#FFF8E1;border:1px solid #F0C040;border-radius:8px;"
        "padding:12px;margin-bottom:8px'>"
        "<span style='font-size:14px;font-weight:700;color:#8A5210'>"
        "🎯 Preparação para entrevista</span></div>", unsafe_allow_html=True)
    col_gaps, col_contatos = st.columns(2)
    with col_gaps:
        st.markdown("**📚 Estude antes da entrevista:**")
        df_perfil = carregar_perfil()
        if not df_perfil.empty:
            resultado = calcular_score(id_vaga, int(df_perfil.iloc[0]["id"]))
            gaps = resultado.get("gaps", [])
            if gaps:
                for g in gaps:
                    st.markdown(
                        f"<span style='background:#FBF0EB;color:#A83A18;padding:2px 8px;"
                        f"border-radius:10px;font-size:11px;margin:2px;display:inline-block'>"
                        f"✗ {g['stack']}</span>", unsafe_allow_html=True)
            else:
                st.success("Você tem todas as stacks!")
    with col_contatos:
        st.markdown("**👥 Seus contatos nessa empresa:**")
        df_contatos = listar_contatos(id_empresa)
        if not df_contatos.empty:
            for _, c in df_contatos.iterrows():
                email_tag = f" · `{c['email']}`" if c.get("email") else ""
                st.markdown(
                    f"<div style='background:#E8F5F0;border-radius:6px;padding:6px 10px;"
                    f"margin:3px 0;font-size:12px'>"
                    f"<b>{c['nome']}</b> — {c['grau']}{email_tag}</div>", unsafe_allow_html=True)
        else:
            st.caption("Nenhum contato cadastrado.")


def render_remuneracao(vaga: dict):
    def _si(val):
        try: return 0 if val is None or str(val) == 'nan' else int(val)
        except Exception: return 0

    def _sb(val):
        try: return False if val is None or str(val) == 'nan' else bool(val)
        except Exception: return False

    def _ss(val):
        try: return "" if val is None or str(val) == 'nan' else str(val)
        except Exception: return ""

    st.divider()
    st.write("**💰 Remuneração:**")
    with st.form(key=f"form_rem_{vaga['id']}"):
        col1, col2 = st.columns(2)
        regime = col1.selectbox("Regime", ["CLT","PJ","Exterior"],
            index=["CLT","PJ","Exterior"].index(_ss(vaga.get("regime")) or "CLT")
            if _ss(vaga.get("regime")) in ["CLT","PJ","Exterior"] else 0,
            key=f"regime_{vaga['id']}")
        moeda = col2.selectbox("Moeda", ["BRL","USD","EUR","GBP"],
            index=["BRL","USD","EUR","GBP"].index(_ss(vaga.get("moeda")) or "BRL")
            if _ss(vaga.get("moeda")) in ["BRL","USD","EUR","GBP"] else 0,
            key=f"moeda_{vaga['id']}")
        col3, col4 = st.columns(2)
        salario_mensal = col3.number_input("Salário mensal", min_value=0, step=500,
            value=_si(vaga.get("salario_mensal")), key=f"smensal_{vaga['id']}")
        salario_anual_total = col4.number_input("Total anual", min_value=0, step=1000,
            value=_si(vaga.get("salario_anual_total")), key=f"sanual_{vaga['id']}")
        st.caption("Benefícios")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            tem_vr = st.checkbox("VR", value=_sb(vaga.get("tem_vr")), key=f"tvr_{vaga['id']}")
            valor_vr = st.number_input("Valor VR", min_value=0, step=10, value=_si(vaga.get("valor_vr")), key=f"vvr_{vaga['id']}")
            tem_va = st.checkbox("VA", value=_sb(vaga.get("tem_va")), key=f"tva_{vaga['id']}")
            valor_va = st.number_input("Valor VA", min_value=0, step=10, value=_si(vaga.get("valor_va")), key=f"vva_{vaga['id']}")
            tem_vt = st.checkbox("VT", value=_sb(vaga.get("tem_vt")), key=f"tvt_{vaga['id']}")
            valor_vt = st.number_input("Valor VT", min_value=0, step=10, value=_si(vaga.get("valor_vt")), key=f"vvt_{vaga['id']}")
        with col_b:
            tem_plano_saude = st.checkbox("Plano de saúde", value=_sb(vaga.get("tem_plano_saude")), key=f"tps_{vaga['id']}")
            tem_gympass = st.checkbox("Gympass", value=_sb(vaga.get("tem_gympass")), key=f"tgym_{vaga['id']}")
            tem_convenio_medico = st.checkbox("Convênio médico", value=_sb(vaga.get("tem_convenio_medico")), key=f"tcm_{vaga['id']}")
            tem_sal13 = st.checkbox("13º salário", value=_sb(vaga.get("tem_sal13")), key=f"tsal13_{vaga['id']}")
        with col_c:
            tem_convenio_odonto = st.checkbox("Convênio odontológico", value=_sb(vaga.get("tem_convenio_odonto")), key=f"tco_{vaga['id']}")
            tem_prev_privada = st.checkbox("Previdência privada", value=_sb(vaga.get("tem_prev_privada")), key=f"tpp_{vaga['id']}")
            tem_plr = st.checkbox("PLR", value=_sb(vaga.get("tem_plr")), key=f"tplr_{vaga['id']}")
            valor_plr = st.number_input("Valor PLR", min_value=0, step=500, value=_si(vaga.get("valor_plr")), key=f"vplr_{vaga['id']}")
            tem_bonus = st.checkbox("Bônus", value=_sb(vaga.get("tem_bonus")), key=f"tbonus_{vaga['id']}")
            valor_bonus = st.number_input("Valor bônus", min_value=0, step=500, value=_si(vaga.get("valor_bonus")), key=f"vbonus_{vaga['id']}")
        outros = st.text_input("Outros benefícios", value=_ss(vaga.get("outros_beneficios")),
            placeholder="Ex: stock options, day off...", key=f"outros_{vaga['id']}")

        if salario_mensal > 0:
            sal_mensal_total = salario_mensal + (valor_vr if tem_vr else 0) + (valor_va if tem_va else 0) + (valor_vt if tem_vt else 0)
            sal_anual = (salario_mensal * 12) + (salario_mensal if tem_sal13 else 0) + (valor_plr if tem_plr else 0) + (valor_bonus if tem_bonus else 0)
            st.divider()
            col_t1, col_t2 = st.columns(2)
            col_t1.metric("💰 Mensal total", f"R$ {sal_mensal_total:,.0f}")
            col_t2.metric("📅 Anual total", f"R$ {sal_anual:,.0f}")

        if st.form_submit_button("Salvar remuneração", use_container_width=True):
            salvar_remuneracao(
                id_vaga=vaga["id"], regime=regime, moeda=moeda,
                salario_mensal=salario_mensal, 
                salario_anual_total=sal_anual,
                tem_vr=tem_vr, valor_vr=valor_vr, tem_va=tem_va, valor_va=valor_va,
                tem_vt=tem_vt, valor_vt=valor_vt, tem_plano_saude=tem_plano_saude,
                tem_gympass=tem_gympass, tem_convenio_medico=tem_convenio_medico,
                tem_convenio_odonto=tem_convenio_odonto, tem_prev_privada=tem_prev_privada,
                outros_beneficios=outros,
                tem_sal13=tem_sal13, tem_plr=tem_plr, valor_plr=valor_plr,
                tem_bonus=tem_bonus, valor_bonus=valor_bonus
            )
            st.success("Remuneração salva!")
            st.rerun()


def render_checklist_preparacao(id_vaga: int):
    df_perfil = carregar_perfil()
    if df_perfil.empty:
        return
    id_candidato = int(df_perfil.iloc[0]["id"])
    resultado = calcular_score(id_vaga, id_candidato)
    gaps = resultado.get("gaps", [])
    matches = resultado.get("matches", [])
    if not gaps and not matches:
        return
    st.divider()
    st.write("**📋 Checklist de preparação:**")
    if matches:
        st.caption("✅ Você já tem — reforce antes da entrevista:")
        for m in matches:
            st.checkbox(f"{m['stack']} ({m['nivel']})", value=True,
                key=f"cm_{id_vaga}_{m['stack']}_{m['categoria']}_{uuid.uuid4().hex[:6]}")
    if gaps:
        st.caption("📚 Estudar antes de se candidatar:")
        for g in gaps:
            st.checkbox(f"{g['stack']}", value=False,
                key=f"cg_{id_vaga}_{g['stack']}_{g['categoria']}_{uuid.uuid4().hex[:6]}")


def tempo_relativo(data_coleta) -> str:
    from datetime import date, datetime
    try:
        if isinstance(data_coleta, str):
            d = datetime.strptime(str(data_coleta)[:10], "%Y-%m-%d").date()
        elif hasattr(data_coleta, "date"):
            d = data_coleta.date()
        else:
            d = data_coleta
        delta = (date.today() - d).days
        if delta == 0:  return "hoje"
        if delta == 1:  return "ontem"
        if delta < 7:   return f"há {delta}d"
        if delta < 30:  return f"há {delta // 7}sem"
        if delta < 365: return f"há {delta // 30}m"
        return f"há {delta // 365}a"
    except Exception:
        return str(data_coleta)[:10]


_NIVEL_COR = {
    "junior":       ("#EBF3FB", "#1A5FAD"),
    "pleno":        ("#E8F5F0", "#157A5A"),
    "senior":       ("#FBF4E8", "#8A5210"),
    "sênior":       ("#FBF4E8", "#8A5210"),
    "especialista": ("#FBF0EB", "#A83A18"),
    "lead":         ("#F0EFF9", "#4B44AA"),
}
_MODAL_COR = {
    "remoto":    ("#E8F5F0", "#157A5A"),
    "híbrido":   ("#EBF3FB", "#1A5FAD"),
    "hibrido":   ("#EBF3FB", "#1A5FAD"),
    "presencial":("#FBF0EB", "#A83A18"),
}
_FONTE_ICON = {
    "gupy":            "🟣",
    "greenhouse":      "🟢",
    "inhire":          "🔵",
    "smartrecruiters": "🟡",
    "amazon":          "🟠",
    "bcg":             "⚫",
    "lever":           "🔴",
    "uber":            "⬛",
    "manual":          "✏️",
}

_TIMELINE_ICONS = {
    "nao_inscrito": "📝",
    "inscrito":     "📤",
    "chamado":      "📞",
    "recrutador":   "🎙️",
    "fase_1":       "1️⃣",
    "fase_2":       "2️⃣",
    "fase_3":       "3️⃣",
    "aprovado":     "✅",
    "reprovado":    "❌",
}

_FASES_ORDERED = [
    "nao_inscrito", "inscrito", "chamado", "recrutador",
    "fase_1", "fase_2", "fase_3", "aprovado", "reprovado",
]


def _mini_badge(txt: str, bg: str, fg: str) -> str:
    return (f"<span style='background:{bg};color:{fg};border:1px solid {bg};"
            f"border-radius:8px;padding:1px 8px;font-size:11px;"
            f"font-weight:500;white-space:nowrap'>{txt}</span>")


def render_vaga_card(vaga, score: int, is_nova: bool, key_prefix: str = "card", ats_score: int = 0):
    status_cand = vaga.get("candidatura_status") or "nao_inscrito"
    status_label, status_cor = status_badge(status_cand, is_nova)
    nivel_str = nivel_fmt(vaga["nivel"])
    score_cor = get_cor_score(score)
    favicon_url = safe_str(vaga.get("favicon_url"))
    urgente = vaga.get("urgente") is True

    with st.container(border=True):
        col_fav, col_emp, col_badge = st.columns([0.4, 4.5, 1.5])
        if favicon_url:
            col_fav.image(favicon_url, width=16)
        col_emp.markdown(
            f"<div style='font-size:12px;color:#888;padding-top:2px'>{vaga['empresa']}</div>",
            unsafe_allow_html=True)
        col_badge.markdown(
            f"<div style='text-align:right'>"
            f"<span style='background:{status_cor};color:white;font-size:10px;"
            f"padding:2px 6px;border-radius:10px;font-weight:600'>{status_label}</span>"
            f"</div>", unsafe_allow_html=True)

        st.markdown(
            f"<div style='min-height:44px;overflow:hidden;font-weight:600;margin:4px 0'>"
            f"{vaga['titulo'][:100].replace('*', '')}"
            f"</div>", unsafe_allow_html=True)

        nivel_lower = str(vaga["nivel"]).lower()
        modal_lower = str(vaga["modalidade"]).lower()
        fonte       = str(vaga.get("fonte", "")).lower()

        nivel_bg, nivel_fg = _NIVEL_COR.get(nivel_lower, ("#F2F2F1", "#555"))
        modal_bg, modal_fg = _MODAL_COR.get(modal_lower, ("#F2F2F1", "#555"))
        fonte_icon = _FONTE_ICON.get(fonte, "•")

        badges = ""
        if nivel_lower not in ("não identificado", "nao identificado", "nan", "none", ""):
            badges += _mini_badge(nivel_str, nivel_bg, nivel_fg) + " "
        if modal_lower not in ("não identificado", "nao identificado", "nan", "none", ""):
            badges += _mini_badge(modal_fmt(vaga["modalidade"]), modal_bg, modal_fg) + " "
        if fonte:
            badges += _mini_badge(f"{fonte_icon} {fonte}", "#F5F5F5", "#666") + " "
        if urgente:
            badges += _mini_badge("🔥 urgente", "#FFF0F0", "#C0392B") + " "
        if is_nova:
            badges += _mini_badge("🆕 nova", "#E8F5F0", "#1D9E75")

        st.markdown(
            f"<div style='margin-bottom:6px;display:flex;flex-wrap:wrap;gap:3px'>{badges}</div>",
            unsafe_allow_html=True)

        col_s, col_ats, col_data = st.columns([1, 1, 2])
        if score > 0:
            col_s.markdown(
                f"<div style='margin:2px 0'>"
                f"<span style='color:{score_cor};font-weight:700;font-size:11px'>🎯 {score}%</span>"
                f"<div style='background:#f0f0f0;border-radius:4px;height:4px;margin-top:2px'>"
                f"<div style='background:{score_cor};width:{score}%;height:4px;border-radius:4px'></div>"
                f"</div></div>",
                unsafe_allow_html=True)
        if ats_score > 0:
            ats_cor = get_cor_score(ats_score)
            col_ats.markdown(
                f"<div style='margin:2px 0'>"
                f"<span style='color:{ats_cor};font-weight:700;font-size:11px'>🤖 {ats_score}%</span>"
                f"<div style='background:#f0f0f0;border-radius:4px;height:4px;margin-top:2px'>"
                f"<div style='background:{ats_cor};width:{ats_score}%;height:4px;border-radius:4px'></div>"
                f"</div></div>",
                unsafe_allow_html=True)

        tempo = tempo_relativo(vaga["data_coleta"])
        col_data.markdown(
            f"<div style='text-align:right;color:#888;font-size:11px;padding-top:6px'>📅 {tempo}</div>",
            unsafe_allow_html=True)

        if st.button("▼ detalhes", key=f"{key_prefix}_{vaga['id']}", use_container_width=True):
            st.session_state[f"dialog_{key_prefix}_{int(vaga['id'])}"] = True
            st.session_state[f"dialog_{key_prefix}_atual"] = int(vaga["id"])


def _cor_ats(score: int) -> str:
    if score >= 75:
        return "#00ff88"
    if score >= 50:
        return "#ffd700"
    if score >= 25:
        return "#ff8c00"
    return "#ff4444"


def _barra_ats(score: int, label: str):
    cor = _cor_ats(score)
    preenchido = int(score / 10)
    vazio = 10 - preenchido
    barra = "█" * preenchido + "░" * vazio
    st.markdown(
        f"<div style='font-family:monospace; font-size:13px; margin:3px 0'>"
        f"<span style='color:#aaa'>{label:<14}</span>"
        f"<span style='color:{cor}'>{barra}</span> "
        f"<span style='color:{cor}; font-weight:bold'>{score}%</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _calcular_e_salvar_anya(id_vaga: int, texto_cv: str, descricao: str, titulo: str):
    from transformers.ats_agents import rodar_anya
    from database.ats_score import salvar_ats_score
    anya = rodar_anya(texto_cv, descricao, titulo)
    anya["score_final"] = round(
        anya["score_keywords"]   * 0.40 +
        anya["score_formatacao"] * 0.25 +
        anya["score_secoes"]     * 0.20 +
        anya["score_impacto"]    * 0.15
    )
    salvar_ats_score(id_vaga, anya)


def _render_ats_tab(id_vaga: int, descricao: str, titulo: str, prefix: str):
    from database.ats_score import carregar_ats_score, salvar_ats_score
    from database.candidato import carregar_curriculo_texto
    from database.vagas import atualizar_descricao_vaga

    texto_cv = carregar_curriculo_texto()

    # Reload descricao from DB so edits done earlier in this session are visible
    with db_connect() as _c:
        _row = _c.execute("SELECT descricao FROM fact_vaga WHERE id=?", [id_vaga]).fetchone()
    descricao = (_row[0] if _row and _row[0] else "") or ""

    scores = carregar_ats_score(id_vaga)

    if not texto_cv:
        st.info("Para ver a análise ATS, salve seu currículo em **Meu Perfil → Currículo**.")
        return

    sem_descricao = not descricao or not descricao.strip()

    # ── CAMPO DE DESCRIÇÃO MANUAL ─────────────────────────────
    with st.expander("✏️ Editar descrição da vaga", expanded=sem_descricao):
        desc_input = st.text_area(
            "Cole aqui o texto completo da vaga",
            value=descricao,
            height=200,
            key=f"desc_manual_{id_vaga}_{prefix}",
            label_visibility="collapsed",
            placeholder="Cole o texto da vaga aqui para calcular o score ATS...",
        )
        if st.button("💾 Salvar e calcular ATS", key=f"salvar_desc_{id_vaga}_{prefix}", type="primary", use_container_width=True):
            if desc_input.strip():
                from transformers.stack_extractor import extrair_stacks, detectar_modalidade
                import json as _json
                stacks = extrair_stacks(desc_input)
                modalidade = detectar_modalidade(desc_input)
                atualizar_descricao_vaga(id_vaga, desc_input.strip(), _json.dumps(stacks), modalidade)
                with st.spinner("Calculando ATS..."):
                    _calcular_e_salvar_anya(id_vaga, texto_cv, desc_input.strip(), titulo)
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("Cole uma descrição antes de salvar.")

    if not scores and sem_descricao:
        return

    if not scores:
        st.caption("Score ATS ainda não calculado para esta vaga.")
        if st.button("▶ Calcular agora", key=f"ats_calc_{id_vaga}_{prefix}", type="primary"):
            with st.spinner("Calculando..."):
                _calcular_e_salvar_anya(id_vaga, texto_cv, descricao, titulo)
            st.rerun()
        return

    sem_descricao = not descricao or not descricao.strip()
    sem_keywords  = not scores["keywords_ausentes"] and not scores["keywords_presentes"]

    score_final = scores["score_final"]
    cor = _cor_ats(score_final)

    st.markdown(
        f"<div style='text-align:center; font-family:monospace; padding:16px 0'>"
        f"<div style='font-size:52px; font-weight:bold; color:{cor}'>{score_final}</div>"
        f"<div style='font-size:14px; color:#aaa'>/100 — SCORE ATS ANYA</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if sem_descricao:
        st.warning("Esta vaga não tem descrição armazenada. Execute o pipeline para coletar a descrição completa e depois recalcule.")
    elif sem_keywords:
        st.warning("Nenhuma keyword técnica foi encontrada na descrição desta vaga. A dimensão KEYWORDS foi zerada — verifique se a descrição está completa.")
        with st.expander("Ver descrição analisada"):
            st.text(descricao[:1500] + ("\n[...]" if len(descricao) > 1500 else ""))

    st.markdown(
        "<div style='font-family:monospace; color:#555; font-size:11px; margin-bottom:4px'>DIMENSÕES</div>",
        unsafe_allow_html=True,
    )
    _barra_ats(scores["score_keywords"],   "KEYWORDS")
    _barra_ats(scores["score_formatacao"], "FORMATAÇÃO")
    _barra_ats(scores["score_secoes"],     "SEÇÕES")
    _barra_ats(scores["score_impacto"],    "IMPACTO")

    if not sem_keywords:
        col_neg, col_pos = st.columns(2)
        with col_neg:
            st.markdown("**✗ Ausentes**")
            for kw in scores["keywords_ausentes"][:15]:
                st.markdown(
                    f"<span style='font-family:monospace; color:#ff4444; font-size:12px'>✗ {kw.upper()}</span>",
                    unsafe_allow_html=True,
                )
        with col_pos:
            st.markdown("**✓ Presentes**")
            for kw in scores["keywords_presentes"][:15]:
                st.markdown(
                    f"<span style='font-family:monospace; color:#00ff88; font-size:12px'>✓ {kw.upper()}</span>",
                    unsafe_allow_html=True,
                )

    st.divider()
    if st.button("↻ Recalcular", key=f"ats_recalc_{id_vaga}_{prefix}"):
        from transformers.ats_agents import rodar_anya
        with st.spinner("Recalculando..."):
            anya = rodar_anya(texto_cv, descricao, titulo)
            anya["score_final"] = round(
                anya["score_keywords"]   * 0.40 +
                anya["score_formatacao"] * 0.25 +
                anya["score_secoes"]     * 0.20 +
                anya["score_impacto"]    * 0.15
            )
            salvar_ats_score(id_vaga, anya)
        st.rerun()

    st.caption(f"Calculado em: {scores.get('data_calculo', 'N/A')} · Para análise profunda com IA, use Análise de Currículo.")


def render_dialog_vaga(v, prefix: str = "v"):
    """Dialog de detalhes de vaga reutilizável."""
    import json as _json
    with db_connect() as _con:
        _row = _con.execute(
            "SELECT candidatura_status, candidatura_observacao, historico_fases FROM fact_vaga WHERE id=?",
            [int(v["id"])]
        ).fetchone()
    status_cand = (_row[0] if _row and _row[0] else None) or "nao_inscrito"
    _obs_atual  = _row[1] if _row and _row[1] else ""
    try:
        _historico = _json.loads(_row[2]) if _row and _row[2] else {}
    except Exception:
        _historico = {}

    label_status = TIMELINE_LABELS.get(status_cand, "Não inscrito")
    data_fmt_v = str(v['data_coleta'])[:10] if str(v['data_coleta']) not in ['NaT','None','nan'] else 'N/A'

    col_info, col_link, col_perfil = st.columns([4, 1, 1])
    col_info.caption(f"📅 {data_fmt_v} · {v['empresa']} · {label_status}")
    col_link.link_button("🔗 Ver vaga", v["link"], use_container_width=True)
    if col_perfil.button("🏢 Empresa", use_container_width=True, key=f"perfil_btn_{prefix}_{v['id']}"):
        st.query_params["empresa"] = v["empresa"]
        st.rerun()

    fases_entrevista = ["chamado","recrutador","fase_1","fase_2","fase_3"]
    mostrar_briefing = status_cand in fases_entrevista

    if mostrar_briefing:
        tab_score, tab_cand, tab_briefing, tab_ats, tab_cv, tab_rem, tab_diario = st.tabs([
            "📊 Score & Stacks", "📋 Candidatura", "🎯 Briefing", "🤖 ATS", "📄 Diff CV", "💰 Remuneração", "📓 Diário"
        ])
    else:
        tab_score, tab_cand, tab_ats, tab_cv, tab_rem, tab_diario = st.tabs([
            "📊 Score & Stacks", "📋 Candidatura", "🤖 ATS", "📄 Diff CV", "💰 Remuneração", "📓 Diário"
        ])

    with tab_score:
        render_score_breakdown(int(v["id"]))
        render_checklist_preparacao(int(v["id"]))
        render_stacks(v["stacks"])

    with tab_cand:
        fases = _FASES_ORDERED
        idx_atual = fases.index(status_cand) if status_cand in fases else 0
        pct = int(idx_atual / (len(fases) - 1) * 100) if len(fases) > 1 else 0
        cor_tl = "#1D9E75" if status_cand == "aprovado" else "#D85A30" if status_cand == "reprovado" else "#378ADD"
        st.markdown(
            f"<div style='margin-bottom:8px'>"
            f"<div style='background:#f0f0f0;border-radius:6px;height:6px'>"
            f"<div style='background:{cor_tl};width:{pct}%;height:6px;border-radius:6px'></div>"
            f"</div>"
            f"<div style='text-align:right;font-size:10px;color:#888;margin-top:2px'>"
            f"{TIMELINE_LABELS.get(status_cand, status_cand)}</div>"
            f"</div>",
            unsafe_allow_html=True)
        cols_f = st.columns(len(fases))
        for idx, fase in enumerate(fases):
            ativo = fase == status_cand
            icon  = _TIMELINE_ICONS.get(fase, "•")
            data_fase = _historico.get(fase, "")
            data_label = data_fase[5:] if data_fase else ""  # MM-DD
            btn_label = f"{icon}\n{data_label}" if data_label else icon
            if cols_f[idx].button(
                btn_label,
                key=f"fase_{prefix}_{fase}_{v['id']}",
                use_container_width=True,
                type="primary" if ativo else "secondary",
                help=f"{TIMELINE_LABELS[fase]}{' — ' + data_fase if data_fase else ''}",
            ):
                atualizar_candidatura(int(v["id"]), fase, fase, _obs_atual)
                st.cache_data.clear()
                st.session_state[f"dialog_{prefix}_atual"] = int(v["id"])
                st.toast(f"✅ {TIMELINE_LABELS[fase]}")
                st.rerun()
        st.write("")

        obs_key = f"obs_inline_{prefix}_{v['id']}"
        observacao = st.text_input("Observação", value=_obs_atual, key=obs_key)
        if st.button("💾 Salvar observação", key=f"salvar_obs_{prefix}_{v['id']}",
                    use_container_width=True):
            atualizar_candidatura(int(v["id"]), status_cand, status_cand, observacao)
            st.cache_data.clear()
            st.session_state[f"dialog_{prefix}_atual"] = int(v["id"])
            st.toast("✅ Observação salva!")
            st.rerun()

        st.divider()
        if st.button("❌ Negar vaga", key=f"negar_{prefix}_{v['id']}",
                    use_container_width=True, type="secondary"):
            negar_vaga(int(v["id"]), observacao or f"Negada em: {status_cand}")
            st.cache_data.clear()
            st.session_state[f"dialog_{prefix}_atual"] = None
            st.toast("❌ Vaga negada.")
            st.rerun()
        # retrospectiva — aparece quando processo encerrou
        if status_cand in ["aprovado", "reprovado"]:
            st.divider()
            from database.retrospectiva import carregar_retrospectiva, salvar_retrospectiva
            retro = carregar_retrospectiva(int(v["id"]))
            
            with st.expander("📝 Retrospectiva do processo", expanded=retro is None):
                if retro:
                    st.caption(f"Preenchida em {str(retro[4])[:10]}")
                    if retro[0]: st.markdown(f"**Não soube:** {retro[0]}")
                    if retro[1]: st.markdown(f"**Faria diferente:** {retro[1]}")
                    if retro[2]: st.markdown(f"**Impressão:** {retro[2]}")
                    if retro[3]: st.markdown(f"**Motivo:** {retro[3]}")
                    st.divider()

                with st.form(key=f"form_retro_{v['id']}"):
                    nao_soube = st.text_area("O que você não soube responder?",
                        value=retro[0] if retro else "",
                        placeholder="Ex: Perguntaram sobre otimização de queries no Spark...",
                        height=60)
                    faria_diferente = st.text_area("O que faria diferente na preparação?",
                        value=retro[1] if retro else "",
                        placeholder="Ex: Estudaria mais Delta Lake antes...",
                        height=60)
                    col_imp, col_mot = st.columns(2)
                    impressao = col_imp.selectbox("Impressão geral",
                        ["positiva", "neutra", "negativa"],
                        index=["positiva","neutra","negativa"].index(retro[2]) if retro and retro[2] in ["positiva","neutra","negativa"] else 1)
                    motivo = col_mot.selectbox("Motivo do encerramento",
                        ["técnico", "fit cultural", "concorrência", "freeze de headcount", "desisti", "outro"],
                        index=0)
                    if st.form_submit_button("💾 Salvar retrospectiva", use_container_width=True):
                        salvar_retrospectiva(int(v["id"]), nao_soube, faria_diferente, impressao, motivo)
                        st.toast("✅ Retrospectiva salva!")
                        st.rerun()    

    with tab_ats:
        _render_ats_tab(int(v["id"]), v.get("descricao", ""), v.get("titulo", ""), prefix)

    with tab_cv:
        st.caption("Faça upload do seu currículo em PDF para ver o diff com esta vaga.")
        curriculo_file = st.file_uploader("Currículo (PDF)", type=["pdf"], key=f"cv_{v['id']}")
        if curriculo_file:
            import tempfile, os, json
            from transformers.curriculo_parser import extrair_stacks_curriculo, gerar_diff_curriculo_vaga
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(curriculo_file.read())
                tmp_path = tmp.name
            try:
                stacks_cv = extrair_stacks_curriculo(tmp_path)
                stacks_vaga_dict = json.loads(v["stacks"]) if isinstance(v["stacks"], str) else v["stacks"]
                diff = gerar_diff_curriculo_vaga(stacks_cv, stacks_vaga_dict or {})

                st.metric("Cobertura do CV para esta vaga", f"{diff['pct_cobertura']}%")
                st.progress(diff["pct_cobertura"] / 100)

                col_m, col_g = st.columns(2)
                with col_m:
                    st.markdown("**✅ Você menciona no CV:**")
                    for m in diff["matches"]:
                        st.markdown(
                            f"<span style='background:#E8F5F0;color:#157A5A;padding:2px 8px;"
                            f"border-radius:10px;font-size:11px;margin:2px;display:inline-block'>"
                            f"✓ {m['stack']}</span>", unsafe_allow_html=True)
                with col_g:
                    st.markdown("**❌ Faltam no CV:**")
                    for g in diff["gaps"]:
                        st.markdown(
                            f"<span style='background:#FBF0EB;color:#A83A18;padding:2px 8px;"
                            f"border-radius:10px;font-size:11px;margin:2px;display:inline-block'>"
                            f"✗ {g['stack']}</span>", unsafe_allow_html=True)

                if diff["gaps"]:
                    st.divider()
                    st.caption("💡 Adicione essas stacks ao CV antes de candidatar — ou certifique-se de mencionar experiência relevante durante a entrevista.")
            # exportar diff como markdown
                st.divider()
                md = f"# Diff Currículo × {v['titulo'][:50]}\n"
                md += f"**Empresa:** {v['empresa']}  \n"
                md += f"**Cobertura:** {diff['pct_cobertura']}%\n\n"
                md += "## ✅ Você menciona no CV\n"
                for m in diff["matches"]:
                    md += f"- {m['stack']} ({m['categoria']})\n"
                md += "\n## ❌ Faltam no CV\n"
                for g in diff["gaps"]:
                    md += f"- {g['stack']} ({g['categoria']})\n"
                if diff["gaps"]:
                    md += "\n## 💡 Ações recomendadas\n"
                    for g in diff["gaps"]:
                        md += f"- Adicione **{g['stack']}** ao CV ou mencione durante a entrevista\n"

                st.download_button(
                    "📥 Exportar diff como Markdown",
                    data=md,
                    file_name=f"diff_{v['empresa'].lower().replace(' ','_')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
            finally:
                os.unlink(tmp_path)
        else:
            st.info("Upload o PDF do seu currículo para ver quais stacks aparecem e quais estão faltando para esta vaga.")

    with tab_rem:
        render_remuneracao(v)

    with tab_diario:
        render_diario(int(v["id"]), prefix=prefix)

    if mostrar_briefing:
        with tab_briefing:
            from database.empresas import gerar_briefing_empresa
            b = gerar_briefing_empresa(v["empresa"])
            st.markdown(f"### 🏢 {v['empresa']}")
            col1, col2, col3 = st.columns(3)
            col1.metric("Vagas históricas", b["total_vagas"])
            col2.metric("Vagas ativas", b["vagas_ativas"])
            col3.metric("Suas candidaturas", b["candidaturas"])
            if b["urgentes"] > 0:
                st.warning(f"🔥 {b['urgentes']} vaga(s) urgente(s) abertas agora")
            if b["niveis"]:
                st.caption("**Níveis mais contratados:**")
                for nivel, total in b["niveis"]:
                    st.markdown(f"- {nivel}: {total} vagas")
            if b["modalidades"]:
                st.caption("**Modalidades:**")
                for mod, total in b["modalidades"]:
                    st.markdown(f"- {mod}: {total} vagas")
            if b["top_stacks"]:
                st.divider()
                st.caption("**Stacks mais pedidas pela empresa:**")
                badges = " ".join([
                    f"<span style='background:#EBF3FB;color:#378ADD;padding:2px 8px;"
                    f"border-radius:10px;font-size:11px;margin:2px;display:inline-block'>"
                    f"{s} ({c})</span>"
                    for s, c in b["top_stacks"]
                ])
                st.markdown(badges, unsafe_allow_html=True)
            if b["contatos"]:
                st.divider()
                st.caption("**Seus contatos nessa empresa:**")
                for nome_c, grau, email in b["contatos"]:
                    email_str = f" · {email}" if email else ""
                    st.markdown(f"👤 **{nome_c}** — {grau}{email_str}")
            st.caption(f"Última coleta: {b['ultima_coleta']}")


def render_empty_state(titulo: str, descricao: str, acao_label: str = None, acao_pagina: str = None):
    st.markdown(
        f"<div style='text-align:center;padding:40px 20px;color:#767676'>"
        f"<div style='font-size:48px;margin-bottom:16px'>🔍</div>"
        f"<div style='font-size:18px;font-weight:600;color:#333;margin-bottom:8px'>{titulo}</div>"
        f"<div style='font-size:14px;max-width:400px;margin:0 auto'>{descricao}</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    if acao_label and acao_pagina:
        col = st.columns([1, 2, 1])[1]
        if col.button(acao_label, use_container_width=True, type="primary"):
            st.session_state["pagina"] = acao_pagina
            st.rerun()
