import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
from database.schemas import criar_tabelas

@st.cache_resource
def _init_db():
    criar_tabelas()

_init_db()
from dashboard.views import (
    dashboard_page, vagas, cadastrar_vaga, empresas,
    pipeline, configuracoes, vagas_negadas,
    perfil_empresa, contatos, perfil_candidato,
    comparativo, tendencias, funil, qualidade, fila_inscricao, estudos,
    minha_performance, perguntas, comparar_ofertas, analise_curriculo
)

st.set_page_config(page_title="Job Tracker", layout="wide")

pages = {
    "Dashboard":            dashboard_page.render,
    "Vagas":                vagas.render,
    "Fila de Inscrição":    fila_inscricao.render,
    "Estudos":              estudos.render,
    "Comparativo":          comparativo.render,
    "Tendências":           tendencias.render,
    "Funil":                funil.render,
    "Cadastrar Vaga":       cadastrar_vaga.render,
    "Empresas":             empresas.render,
    "Indicadores":          contatos.render,
    "Meu Perfil":           perfil_candidato.render,
    "Análise de Currículo": analise_curriculo.render,
    "Pipeline":             pipeline.render,
    "Qualidade":            qualidade.render,
    "Configurações":        configuracoes.render,
    "Vagas Negadas":        vagas_negadas.render,
    "Minha Performance":    minha_performance.render,
    "Perguntas":            perguntas.render,
    "Comparar Ofertas":     comparar_ofertas.render,
}

GRUPOS = {
    "🎯 Trabalho diário": ["Dashboard", "Fila de Inscrição", "Vagas"],
    "📚 Estudo": ["Estudos", "Comparativo", "Tendências", "Minha Performance", "Perguntas"],
    "📋 Cadastros": ["Cadastrar Vaga", "Empresas", "Indicadores", "Meu Perfil", "Análise de Currículo", "Comparar Ofertas"],
    "⚙️ Operações":       ["Pipeline", "Qualidade", "Configurações", "Funil", "Vagas Negadas"],
}

empresa_perfil = st.query_params.get("empresa", None)
if empresa_perfil:
    if st.sidebar.button("← Voltar"):
        st.query_params.clear()
        st.rerun()
    perfil_empresa.render(empresa_perfil)
else:
    st.sidebar.markdown("### Job Tracker")
    st.sidebar.divider()

    if "pagina" not in st.session_state:
        st.session_state["pagina"] = "Dashboard"

    for grupo, itens in GRUPOS.items():
        expanded = any(st.session_state["pagina"] == item for item in itens)
        with st.sidebar.expander(grupo, expanded=expanded):
            for item in itens:
                ativo = st.session_state["pagina"] == item
                if st.button(
                    item,
                    key=f"nav_{item}",
                    use_container_width=True,
                    type="primary" if ativo else "secondary"
                ):
                    st.session_state["pagina"] = item
                    # reset dialogs ao trocar página
                    for key in list(st.session_state.keys()):
                        if key.startswith("dialog_"):
                            st.session_state[key] = False
                    st.rerun()

    pagina = st.session_state["pagina"]
    pages[pagina]()
