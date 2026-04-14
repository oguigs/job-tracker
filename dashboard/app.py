import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from dashboard.views import (
    dashboard_page, vagas, cadastrar_vaga, empresas,
    pipeline, configuracoes, vagas_negadas,
    perfil_empresa, contatos, perfil_candidato, comparativo, tendencias
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
        "Dashboard", "Vagas", "Comparativo", "Tendências", "Cadastrar Vaga",
        "Empresas", "Indicadores", "Pipeline",
        "Configurações", "Vagas Negadas", "Meu Perfil"
    ])
    pages = {
        "Dashboard":        dashboard_page.render,
        "Vagas":            vagas.render,
        "Comparativo":      comparativo.render,
        "Cadastrar Vaga":   cadastrar_vaga.render,
        "Empresas":         empresas.render,
        "Tendências":       tendencias.render,
        "Indicadores":      contatos.render,
        "Pipeline":         pipeline.render,
        "Configurações":    configuracoes.render,
        "Vagas Negadas":    vagas_negadas.render,
        "Meu Perfil":       perfil_candidato.render,
    }
    pages[pagina]()