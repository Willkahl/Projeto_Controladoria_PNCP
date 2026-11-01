"""Testes das funcoes de limpeza (pytest).  Rode:  python -m pytest -q"""
import pytest

from src import limpeza


@pytest.mark.parametrize("nome, args, esperado", limpeza.CASOS)
def test_exemplos_do_enunciado(nome, args, esperado):
    """Os mesmos 54 exemplos do autoteste do kit (casos_de_teste.docx)."""
    assert getattr(limpeza, nome)(*args) == esperado


def test_converter_numero_zero_e_valor():
    assert limpeza.converter_numero("0") == 0.0


def test_converter_numero_nbsp_e_rs():
    assert limpeza.converter_numero("R$\u00a01.234,56") == 1234.56


def test_documento_estrangeiro_nao_e_alterado():
    assert limpeza.limpar_documento("abc123", "PE") == "ABC123"


def test_data_hora_e_descartada():
    assert str(limpeza.converter_data("2025-03-10T23:59:59")) == "2025-03-10"
