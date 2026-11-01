"""
carregar.py  -  CARGA NO POSTGRESQL   (voce completa os trechos com ____)
=========================================================================
Passos:  1) recria o banco e as tabelas (banco.recriar_banco + sql/01_criar_banco.sql)
         2) carrega as 4 DIMENSOES   3) carrega a FATO (as dimensoes vem primeiro!)   4) confere as contagens
Usa so o que o kit ja traz: src/config.py e src/banco.py (recriar_banco, conectar, executar_script, inserir_em_lote, consultar).
O sql/01_criar_banco.sql e o SEU script (veja a secao 4.3 do enunciado): crie esse arquivo antes de rodar a carga.
Ele so cria as tabelas: o banco em si e recriado por banco.recriar_banco().
Dica: veja a carga em lote do 1_extrair.py do Desafio Transparencia (banco.inserir_em_lote).

COMO RODAR (depois do montar_tabelas):   python -m src.carregar
"""

import pandas as pd

from src import banco, config


def ler(nome, **opcoes):
    """PRONTA. Le um CSV de data/processed. Campo vazio vira NaN (que mais abaixo vira None = NULL no banco)."""
    return pd.read_csv(config.PASTA_PROCESSED / f"{nome}.csv", keep_default_na=False, na_values=[""], **opcoes)


def tuplas(tabela, colunas):
    """PRONTA. Transforma o DataFrame em uma lista de tuplas simples, que e o que o banco entende.
    Valor vazio (NaN) vira None, que o banco grava como NULL."""
    dados = tabela[colunas].astype(object)
    dados = dados.where(dados.notna(), None)
    return [tuple(linha) for linha in dados.itertuples(index=False, name=None)]


def inserir(con, tabela, colunas, dados):
    """Monta o INSERT INTO ... VALUES (%s, %s, ...) e envia todas as linhas de uma vez."""
    # Um %s para cada coluna. COMPLETE: monte uma lista com "%s" repetido len(colunas) vezes:  ["%s"] * len(colunas)
    marcadores = ", ".join(["%s"] * len(colunas))
    sql = f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES ({marcadores})"
    # COMPLETE: envie em lote com banco.inserir_em_lote(conexao, sql, linhas)
    banco.inserir_em_lote(con, sql, tuplas(dados, colunas))
    print(f"   {tabela}: {len(dados)} linhas")


DIMENSOES = [("dim_orgao", ["sk_orgao", "cnpj_orgao", "nome_orgao", "poder"]),
             ("dim_fornecedor", ["sk_fornecedor", "ni_fornecedor", "nome_fornecedor", "tipo_pessoa", "porte"]),
             ("dim_modalidade", ["sk_modalidade", "modalidade_id", "nome_modalidade"]),
             ("dim_localidade", ["sk_localidade", "uf_sigla", "uf_nome", "regiao"])]

COLUNAS_FATO = ["numero_controle_pncp", "numero_item", "sk_orgao", "sk_fornecedor", "sk_modalidade", "sk_localidade",
                "data_publicacao", "data_homologacao", "descricao_item", "perfil_gasto", "quantidade",
                "valor_unitario_estimado", "valor_total_estimado", "valor_unitario_homologado", "valor_total_homologado",
                "comparavel", "economia_valor", "dias_ciclo"]


def validar_antes_de_carregar(fato, dimensoes):
    """VALIDACAO PREVIA (antes de tocar no banco): falha cedo e com mensagem clara, em vez de deixar o PostgreSQL
    recusar o lote no meio da carga. Levanta ValueError se achar FK sem destino, grao duplicado ou valor impossivel."""
    problemas = []
    for nome, colunas in DIMENSOES:
        sk, natural = colunas[0], colunas[1]
        tabela = dimensoes[nome]
        if tabela[sk].duplicated().any():
            problemas.append(f"{nome}: {sk} repetida")
        if tabela[natural].duplicated().any():
            problemas.append(f"{nome}: chave natural {natural} repetida")
        orfas = ~fato[sk].isin(set(tabela[sk].astype(int)) | {-1})
        if orfas.any():
            problemas.append(f"fato: {int(orfas.sum())} linha(s) com {sk} sem destino em {nome}")
    if fato.duplicated(["numero_controle_pncp", "numero_item"]).any():
        problemas.append("fato: grao (numero_controle_pncp + numero_item) duplicado")
    if not (fato["quantidade"] > 0).all():
        problemas.append("fato: quantidade <= 0")
    if (fato[["valor_total_estimado", "valor_total_homologado"]] < 0).any().any():
        problemas.append("fato: valor negativo")
    if (fato["valor_total_estimado"].abs().max() >= 1e16) or (fato["valor_total_homologado"].abs().max() >= 1e16):
        problemas.append("fato: valor estoura o DECIMAL(18,2)")
    if problemas:
        raise ValueError("Validacao previa falhou:\n   - " + "\n   - ".join(problemas))
    print("Validacao previa: OK (sem FK solta, sem grao duplicado, sem valor impossivel)")


def conferir_integridade(con):
    """CONFERENCIA NO BANCO: as FKs ja impedem orfas, mas a consulta prova isso com numero (esperado: 0 em todas)."""
    print("Integridade referencial (esperado 0 FK solta):")
    ok = True
    for sk, dim in [("sk_orgao", "dim_orgao"), ("sk_fornecedor", "dim_fornecedor"),
                    ("sk_modalidade", "dim_modalidade"), ("sk_localidade", "dim_localidade")]:
        n = banco.consultar(con, f"SELECT COUNT(*) FROM fato_item_contratado f "
                                 f"LEFT JOIN {dim} d ON d.{sk} = f.{sk} WHERE d.{sk} IS NULL")[0][0]
        print(f"   fato.{sk} sem destino em {dim}: {n} -> {'OK' if n == 0 else 'DIVERGENTE'}")
        ok &= n == 0
    n = banco.consultar(con, "SELECT COUNT(*) FROM fato_item_contratado WHERE sk_orgao = -1 OR sk_fornecedor = -1 "
                             "OR sk_modalidade = -1 OR sk_localidade = -1")[0][0]
    print(f"   fato apontando para a linha 'Nao informado' (sk = -1): {n}")
    return ok


def main():
    # 0) Le e valida TUDO antes de mexer no banco
    dimensoes = {nome: ler(nome, dtype=str) for nome, _ in DIMENSOES}
    for nome, colunas in DIMENSOES:
        dimensoes[nome][colunas[0]] = dimensoes[nome][colunas[0]].astype(int)
    fato = ler("fato_item_contratado")
    # dias_ciclo vem como 48.0 (decimal) porque tem vazios; o banco quer inteiro. COMPLETE: converta para o tipo "Int64"
    fato["dias_ciclo"] = fato["dias_ciclo"].astype("Int64")
    try:
        validar_antes_de_carregar(fato, dimensoes)
    except ValueError as erro:
        print(erro)
        raise SystemExit(1)

    # 1) Banco (o recriar_banco apaga e cria de novo) e tabelas
    banco.recriar_banco()
    con = banco.conectar()
    try:
        # COMPLETE: execute o arquivo SQL de criacao: banco.executar_script(conexao, caminho_do_arquivo)
        banco.executar_script(con, config.PASTA_SQL / "01_criar_banco.sql")

        # 2) Dimensoes PRIMEIRO: a fato tem chave estrangeira para elas, entao elas precisam existir antes.
        print("Carga:")
        for nome, colunas in DIMENSOES:
            inserir(con, nome, colunas, dimensoes[nome])

        # 3) Fato (depois das dimensoes)
        inserir(con, "fato_item_contratado", COLUNAS_FATO, fato)

        # 4) Conferencia: o que esta no banco tem que bater com a prova real (anexo 8 do enunciado)
        #    As dimensoes tem tambem a linha 'Nao informado' (sk = -1): ela nao conta nas linhas esperadas.
        print("Conferencia:")
        tudo_ok = True
        for tabela, esperado in [("fato_item_contratado", 6126), ("dim_orgao", 363), ("dim_fornecedor", 2652),
                                 ("dim_modalidade", 7), ("dim_localidade", 27)]:
            filtro = "" if tabela.startswith("fato") else f" WHERE sk_{tabela[4:]} > 0"
            n = banco.consultar(con, f"SELECT COUNT(*) FROM {tabela}{filtro}")[0][0]
            print(f"   {tabela}: {n} (esperado {esperado}) -> {'OK' if n == esperado else 'DIVERGENTE'}")
            tudo_ok &= n == esperado
        volume = banco.consultar(con, "SELECT SUM(valor_total_homologado) FROM fato_item_contratado")[0][0]
        print(f"   volume homologado no banco: R$ {volume:,.2f} (esperado R$ 8,044,498,805.74)")
        tudo_ok &= conferir_integridade(con)
        print("\nCarga concluida." if tudo_ok else "\nCarga concluida COM DIVERGENCIAS: investigue antes de seguir.")
    except Exception as erro:                       # falha no meio: desfaz o que estava pendente e avisa
        con.rollback()
        print(f"ERRO na carga: {erro}")
        raise SystemExit(1)
    finally:
        con.close()


if __name__ == "__main__":
    main()
