"""Testes para transformers/stack_extractor.py"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from transformers.stack_extractor import (
    extrair_stacks, detectar_nivel, detectar_modalidade,
    detectar_urgencia, detectar_salario, extrair_sinais_descricao
)


def test_extrair_stacks_python():
    stacks = extrair_stacks("Precisamos de alguém com Python e SQL avançado")
    assert "linguagens" in stacks
    assert any("python" in t.lower() for t in stacks["linguagens"])


def test_extrair_stacks_cloud():
    stacks = extrair_stacks("Experiência com AWS S3, Glue e Athena é necessária")
    assert "cloud" in stacks
    assert any("aws" in t.lower() for t in stacks["cloud"])


def test_extrair_stacks_vazio():
    stacks = extrair_stacks("")
    assert isinstance(stacks, dict)


def test_detectar_nivel_senior():
    assert detectar_nivel("Engenheiro de Dados Sênior") == "senior"
    assert detectar_nivel("Senior Data Engineer") == "senior"


def test_detectar_nivel_pleno():
    assert detectar_nivel("Analista de Dados Pleno") == "pleno"


def test_detectar_nivel_junior():
    assert detectar_nivel("Data Engineer Junior") == "junior"


def test_detectar_nivel_nao_identificado():
    assert detectar_nivel("Engenheiro de Dados") == "não identificado"


def test_detectar_modalidade_remoto():
    assert detectar_modalidade("Vaga 100% remota") == "remoto"
    assert detectar_modalidade("Trabalho home office") == "remoto"


def test_detectar_modalidade_hibrido():
    assert detectar_modalidade("Modelo híbrido 3x por semana") == "híbrido"


def test_detectar_modalidade_presencial():
    assert detectar_modalidade("Trabalho presencial em São Paulo") == "presencial"


def test_detectar_urgencia_true():
    assert detectar_urgencia("URGENTE: vaga com início imediato") is True
    assert detectar_urgencia("início imediato necessário") is True


def test_detectar_urgencia_false():
    assert detectar_urgencia("Vaga para engenheiro de dados sênior") is False


def test_detectar_salario():
    min_s, max_s = detectar_salario("Salário: R$ 8.000 a R$ 12.000 mensais")
    assert min_s == 8000
    assert max_s == 12000


def test_detectar_salario_k():
    min_s, max_s = detectar_salario("faixa de 10k a 15k")
    assert min_s == 10000
    assert max_s == 15000


def test_detectar_salario_sem_info():
    min_s, max_s = detectar_salario("Salário a combinar")
    assert min_s == 0
    assert max_s == 0


def test_extrair_sinais_equipe():
    sinais = extrair_sinais_descricao("Você vai trabalhar num time de 5 engenheiros")
    assert sinais["tamanho_equipe"] == 5


def test_extrair_sinais_cultura():
    sinais = extrair_sinais_descricao("Praticamos code review e TDD")
    assert "code review" in sinais["cultura"]
    assert "TDD" in sinais["cultura"]


def test_extrair_sinais_estagio():
    sinais = extrair_sinais_descricao("Startup série B em crescimento acelerado")
    assert sinais["estagio_empresa"] == "growth stage"
