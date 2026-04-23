import os
import json
import uuid
import streamlit as st
from dashboard.stack_config import get_stack_icon_url, get_stack_roadmap_url, get_categoria_cor
from database.score import calcular_score
from database.candidato import carregar_perfil
from utils import safe_str, nivel_fmt, modal_fmt, status_badge, cor_score as get_cor_score


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


def render_diario(id_vaga: int):
    from database.diario import adicionar_nota, listar_notas, deletar_nota
    st.divider()
    st.write("**Diário de candidatura:**")
    df_notas = listar_notas(id_vaga)
    if not df_notas.empty:
        for _, nota in df_notas.iterrows():
            col_data, col_nota, col_del = st.columns([1.5, 6, 0.5])
            col_data.caption(str(nota["data_nota"])[:10])
            col_nota.write(nota["nota"])
            if col_del.button("✕", key=f"del_nota_{nota['id']}"):
                deletar_nota(nota["id"])
                st.rerun()
    else:
        st.caption("Nenhuma nota ainda.")
    with st.form(key=f"form_diario_{id_vaga}"):
        nova_nota = st.text_area("Nova nota", placeholder="Ex: Ligaram do RH...", height=80, label_visibility="collapsed")
        if st.form_submit_button("Adicionar nota", use_container_width=True):
            if nova_nota.strip():
                adicionar_nota(id_vaga, nova_nota.strip())
                st.success("Nota adicionada!")
                st.rerun()


def render_preparacao_entrevista(id_vaga: int, id_empresa_nome: str, status_cand: str):
    fases_entrevista = ["chamado", "recrutador", "fase_1", "fase_2", "fase_3"]
    if status_cand not in fases_entrevista:
        return
    from database.contatos import listar_contatos
    from database.connection import conectar
    con = conectar()
    id_empresa = con.execute("SELECT id FROM dim_empresa WHERE nome = ?", [id_empresa_nome]).fetchone()
    con.close()
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
    from database.candidaturas import salvar_remuneracao

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
            # cálculo automático
            sal_mensal_total = salario_mensal + (valor_vr if tem_vr else 0) + (valor_va if tem_va else 0) + (valor_vt if tem_vt else 0)
            sal_anual = (salario_mensal * 12) + (salario_mensal if tem_sal13 else 0) + (valor_plr if tem_plr else 0) + (valor_bonus if tem_bonus else 0)

        # totais calculados automaticamente
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
                salario_mensal=salario_mensal, salario_anual_total=salario_mensal,
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


def render_vaga_card(vaga, score: int, is_nova: bool, key_prefix: str = "card"):
    status_cand = vaga.get("candidatura_status") or "nao_inscrito"
    status_label, status_cor = status_badge(status_cand, is_nova)
    nivel_str = nivel_fmt(vaga['nivel'])
    modal_str = modal_fmt(vaga['modalidade'])
    score_cor = get_cor_score(score)
    favicon_url = safe_str(vaga.get("favicon_url"))
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
            f"<div style='min-height:48px;overflow:hidden'>"
            f"{vaga['titulo'][:100].replace('*','')}"
            f"</div>", unsafe_allow_html=True)
        col_n, col_m, col_s = st.columns([2, 2, 1])
        col_n.caption(nivel_str)
        col_m.caption(modal_str)
        if score > 0:
            col_s.markdown(
                f"<span style='color:{score_cor};font-weight:700;font-size:12px'>🎯{score}%</span>",
                unsafe_allow_html=True)
        if st.button("▼ detalhes", key=f"{key_prefix}_{vaga['id']}", use_container_width=True):
            st.session_state[f"dialog_{key_prefix}_{int(vaga['id'])}"] = True
            st.session_state[f"dialog_{key_prefix}_atual"] = int(vaga['id'])