"""Testes para utils.py — helpers globais."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import safe_bool, safe_str, safe_int, nivel_fmt, modal_fmt, status_badge, cor_score


def test_safe_bool():
    assert safe_bool(True) is True
    assert safe_bool(False) is False
    assert safe_bool(None) is False
    assert safe_bool("nan") is False
    assert safe_bool("None") is False
    assert safe_bool(1) is True
    assert safe_bool(0) is False


def test_safe_str():
    assert safe_str("hello") == "hello"
    assert safe_str(None) == ""
    assert safe_str("nan") == ""
    assert safe_str("None") == ""
    assert safe_str("NaT") == ""
    assert safe_str("", default="—") == "—"
    assert safe_str(123) == "123"


def test_safe_int():
    assert safe_int(5) == 5
    assert safe_int("10") == 10
    assert safe_int(None) == 0
    assert safe_int("nan") == 0
    assert safe_int("abc") == 0
    assert safe_int(None, default=99) == 99


def test_nivel_fmt():
    assert nivel_fmt("senior") == "senior"
    assert nivel_fmt("não identificado") == "—"
    assert nivel_fmt("nao identificado") == "—"
    assert nivel_fmt(None) == "—"
    assert nivel_fmt("nan") == "—"


def test_modal_fmt():
    assert modal_fmt("remoto") == "remoto"
    assert modal_fmt("não identificado") == "—"
    assert modal_fmt(None) == "—"


def test_status_badge_nao_inscrito():
    label, cor = status_badge("nao_inscrito", False)
    assert label == "Não inscrito"
    assert cor == "#378ADD"


def test_status_badge_novo():
    label, cor = status_badge("nao_inscrito", True)
    assert label == "Novo"
    assert cor == "#E8A020"


def test_status_badge_inscrito():
    label, cor = status_badge("inscrito", False)
    assert label == "Inscrito"
    assert cor == "#1D9E75"


def test_status_badge_em_processo():
    label, cor = status_badge("fase_1", False)
    assert label == "Em processo"


def test_cor_score():
    assert cor_score(70) == "#1D9E75"
    assert cor_score(71) == "#1D9E75"
    assert cor_score(40) == "#BA7517"
    assert cor_score(69) == "#BA7517"
    assert cor_score(39) == "#767676"
    assert cor_score(0) == "#767676"
