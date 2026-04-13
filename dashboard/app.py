import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from dashboard.views import (
    dashboard_page, vagas, cadastrar_vaga,
    empresas, pipeline, configuracoes,
    vagas_negadas, perfil_empresa
)

st.set_page_config(page_title="Job Tracker", layout="wide")

empresa_perfil = st.query_params.get("empresa", None)

if empresa_perfil:
    if st.sidebar.button("← Voltar"):
        st.query_params.clear()
        st.rerun()
    perfil_empresa.render(empresa_perfil)
else:
    pagina = st.sidebar.radio("Navegação", [
        "Dashboard", "Vagas", "Cadastrar Vaga",
        "Empresas", "Pipeline", "Configurações", "Vagas Negadas"
    ])
    pages = {
        "Dashboard":      dashboard_page.render,
        "Vagas":          vagas.render,
        "Cadastrar Vaga": cadastrar_vaga.render,
        "Empresas":       empresas.render,
        "Pipeline":       pipeline.render,
        "Configurações":  configuracoes.render,
        "Vagas Negadas":  vagas_negadas.render,
    }
    pages[pagina]()