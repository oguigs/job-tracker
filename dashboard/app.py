import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from dashboard.views import (
    dashboard_page, vagas, cadastrar_vaga, empresas,
    pipeline, configuracoes, vagas_negadas,
    perfil_empresa, contatos, perfil_candidato, 
    comparativo, tendencias, funil, qualidade, fila_inscricao
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
        "Dashboard", "Vagas", "Fila de Inscrição", "Comparativo", "Tendências", 
        "Funil", "Cadastrar Vaga",
        "Empresas", "Indicadores", "Pipeline", "Qualidade",
        "Configurações", "Vagas Negadas", "Meu Perfil"
    ])
    pages = {
        "Dashboard":        dashboard_page.render,
        "Vagas":                vagas.render,
        "Fila de Inscrição":    fila_inscricao.render,
        "Comparativo":          comparativo.render,
        "Cadastrar Vaga":       cadastrar_vaga.render,
        "Empresas":             empresas.render,
        "Tendências":           tendencias.render,
        "Funil":                funil.render,
        "Indicadores":          contatos.render,
        "Pipeline":             pipeline.render,
        "Configurações":        configuracoes.render,
        "Vagas Negadas":        vagas_negadas.render,
        "Meu Perfil":           perfil_candidato.render,
        "Qualidade":            qualidade.render
    }
    pages[pagina]()