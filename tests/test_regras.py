"""Testes de integridade das tabelas geradas por src.montar_tabelas (batem com a prova real, anexo 8)."""
import pandas as pd
import pytest

from src import config, montar_tabelas


@pytest.fixture(scope="module")
def tabelas():
    montar_tabelas.main()
    # dtype=str nos documentos: lidos como numero, o CNPJ perderia o zero da esquerda
    ler = lambda n: pd.read_csv(config.PASTA_PROCESSED / f"{n}.csv", keep_default_na=False, na_values=[""],
                                dtype={"cnpj_orgao": str, "ni_fornecedor": str})
    return {n: ler(n) for n in ["fato_item_contratado", "dim_orgao", "dim_fornecedor", "dim_modalidade", "dim_localidade"]}


def test_contagens(tabelas):
    assert len(tabelas["fato_item_contratado"]) == 6126
    assert len(tabelas["dim_orgao"]) == 363
    assert len(tabelas["dim_fornecedor"]) == 2652
    assert len(tabelas["dim_modalidade"]) == 7
    assert len(tabelas["dim_localidade"]) == 27


def test_grao_unico(tabelas):
    assert not tabelas["fato_item_contratado"].duplicated(["numero_controle_pncp", "numero_item"]).any()


def test_volume_e_economia(tabelas):
    f = tabelas["fato_item_contratado"]
    assert round(f["valor_total_homologado"].sum(), 2) == pytest.approx(8044498805.74, abs=0.05)
    comp = f[f["comparavel"] == 1]
    assert len(comp) == 5457
    assert round(100 * comp["economia_valor"].sum() / comp["valor_total_estimado"].sum(), 2) == 14.46


def test_credenciamento_nunca_e_comparavel(tabelas):
    f, m = tabelas["fato_item_contratado"], tabelas["dim_modalidade"]
    sk12 = int(m.loc[m["modalidade_id"] == 12, "sk_modalidade"].iloc[0])
    assert (f.loc[f["sk_modalidade"] == sk12, "comparavel"] == 0).all()


def test_cronologia(tabelas):
    f = tabelas["fato_item_contratado"]
    assert f["dias_ciclo"].isna().sum() == 230
    assert (f["dias_ciclo"].dropna() >= 0).all()
    assert (f["data_homologacao"].isna() == f["dias_ciclo"].isna()).all()


def test_nenhuma_fk_solta(tabelas):
    f = tabelas["fato_item_contratado"]
    for sk, dim in [("sk_orgao", "dim_orgao"), ("sk_fornecedor", "dim_fornecedor"),
                    ("sk_modalidade", "dim_modalidade"), ("sk_localidade", "dim_localidade")]:
        assert f[sk].isin(tabelas[dim][sk]).all()


def test_documentos_com_tamanho_certo(tabelas):
    assert (tabelas["dim_orgao"]["cnpj_orgao"].astype(str).str.len() == 14).all()
