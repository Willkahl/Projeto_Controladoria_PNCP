"""
auditoria.py  -  SPRINT 1: CONTAR OS PROBLEMAS DOS DADOS BRUTOS
===============================================================
Le os 3 CSVs de data/raw (tudo como texto) e conta, coluna a coluna, cada inconsistencia que a limpeza trata.
Gera reports/auditoria.md: e daqui que saem os numeros do "dicionario das inconsistencias" do README.

COMO RODAR:   python -m src.auditoria
"""

import re

import pandas as pd

from src import config, limpeza

ZERO_WIDTH = ["\u200b", "\u200c", "\u200d", "\ufeff"]
RE_DATA = {
    "AAAA-MM-DD (com ou sem hora)": r"^\d{4}-\d{2}-\d{2}([T ].*)?$",
    "DD/MM/AAAA (com ou sem hora)": r"^\d{2}/\d{2}/\d{4}( .*)?$",
    "DD-MM-AAAA": r"^\d{2}-\d{2}-\d{4}$",
    "DD.MM.AAAA": r"^\d{2}\.\d{2}\.\d{4}$",
    "AAAA/MM/DD": r"^\d{4}/\d{2}/\d{2}$",
    "AAAAMMDD": r"^\d{8}$",
}


def ler(nome):
    return pd.read_csv(config.PASTA_RAW / f"{nome}.csv", dtype=str, keep_default_na=False)


def formato_dinheiro(v):
    """Classifica a grafia de um numero em texto (so para contar; a conversao real e limpeza.converter_numero)."""
    v = v.strip()
    if v == "":
        return "vazio"
    if v.upper() in limpeza.NULOS and v != "0":
        return "nulo disfarçado"
    if "R$" in v:
        return "com R$"
    if v.startswith("(") or v.endswith("-") or v.startswith("-"):
        return "negativo (parênteses/sinal)"
    if "." in v and "," in v:
        return "milhar e decimal juntos"
    if v.count(",") == 1:
        return "vírgula decimal"
    if v.count(".") > 1 or v.count(",") > 1:
        return "separador de milhar repetido"
    if v.count(".") == 1:
        return "ponto decimal"
    return "inteiro puro"


def tabela_md(serie, titulo):
    linhas = [f"**{titulo}**", "", "| Situação | Linhas |", "| --- | ---: |"]
    linhas += [f"| {k} | {format(v, ',').replace(',', '.')} |" for k, v in serie.items()]
    return "\n".join(linhas) + "\n"


def main():
    compras, itens, resultados = ler("compras"), ler("itens"), ler("resultados")
    out = ["# Auditoria dos dados brutos (data/raw)", "",
           "Gerado por `python -m src.auditoria`. Tudo lido como texto (dtype=str).", ""]

    # ---- 1) tamanho e chaves -------------------------------------------------------------------------------
    out += ["## 1. Tamanho e chaves", "", "| Arquivo | Linhas | Colunas |", "| --- | ---: | ---: |"]
    for nome, df in [("compras.csv", compras), ("itens.csv", itens), ("resultados.csv", resultados)]:
        out.append(f"| {nome} | {format(len(df), ',').replace(',', '.')} | {df.shape[1]} |")
    out += ["", f"- `numero_controle_pncp` repetido em compras: **{int(compras['numero_controle_pncp'].duplicated().sum())}**",
            f"- Itens repetidos (numero_controle_pncp + numero_item): **{int(itens.duplicated(['numero_controle_pncp', 'numero_item']).sum())}**",
            f"- Resultados cancelados (data_cancelamento preenchida): **{int((resultados['data_cancelamento'].str.strip() != '').sum())}**",
            f"- Resultados com ordem_classificacao_srp vazia: **{int((resultados['ordem_classificacao_srp'].str.strip() == '').sum())}**",
            f"- Itens com tem_resultado = False: **{int((itens['tem_resultado'].str.lower() != 'true').sum())}**", ""]

    # ---- 2) documentos -------------------------------------------------------------------------------------
    out += ["## 2. Documentos (CNPJ/CPF)", ""]
    cn = compras["cnpj_orgao"]
    dig = cn.map(lambda v: re.sub(r"\D", "", v))
    out.append(tabela_md(pd.Series({
        "com máscara (pontos, barra ou hífen)": int(cn.str.contains(r"[./-]").sum()),
        "sem máscara e com menos de 14 dígitos (zero à esquerda perdido)": int(((~cn.str.contains(r"[./-]")) & (dig.str.len() < 14)).sum()),
        "vazio ou nulo disfarçado": int(cn.map(lambda v: limpeza.eh_nulo(v.strip())).sum()),
    }), "compras.cnpj_orgao"))
    ni = resultados["ni_fornecedor"]
    dig = ni.map(lambda v: re.sub(r"\D", "", v))
    pj = resultados["tipo_pessoa"] == "PJ"
    pf = resultados["tipo_pessoa"] == "PF"
    out.append(tabela_md(pd.Series({
        "com máscara": int(ni.str.contains(r"[./-]").sum()),
        "PJ com menos de 14 dígitos (zero perdido)": int((pj & (dig.str.len() < 14) & (dig.str.len() > 0)).sum()),
        "PF com menos de 11 dígitos (zero perdido)": int((pf & (dig.str.len() < 11) & (dig.str.len() > 0)).sum()),
        "PJ/PF com dígitos demais (documento impossível)": int(((pj & (dig.str.len() > 14)) | (pf & (dig.str.len() > 11))).sum()),
        "vazio ou nulo disfarçado": int(ni.map(lambda v: limpeza.eh_nulo(v.strip())).sum()),
        "tipo_pessoa = PE (estrangeiro, mantido como veio)": int((resultados["tipo_pessoa"] == "PE").sum()),
    }), "resultados.ni_fornecedor"))

    # ---- 3) dinheiro e numeros -----------------------------------------------------------------------------
    out += ["## 3. Dinheiro e números em texto", ""]
    for arq, df, colunas in [("itens", itens, ["quantidade", "valor_unitario_estimado"]),
                             ("resultados", resultados, ["quantidade_homologada", "valor_unitario_homologado"])]:
        for col in colunas:
            out.append(tabela_md(df[col].map(formato_dinheiro).value_counts(), f"{arq}.{col}"))
            nbsp = int(df[col].str.contains("\u00a0|\u200b|\ufeff", regex=True).sum())
            out.append(f"Com espaço invisível/sem quebra: **{nbsp}**\n")

    # ---- 4) datas -------------------------------------------------------------------------------------------
    out += ["## 4. Datas", ""]
    for arq, df, col in [("compras", compras, "data_publicacao"), ("resultados", resultados, "data_resultado")]:
        v = df[col].str.strip()
        conta = {}
        for nome, rx in RE_DATA.items():
            conta[nome] = int(v.str.match(rx).sum())
        conta["vazio / nulo disfarçado"] = int(v.map(limpeza.eh_nulo).sum())
        invalidas = int(((v != "") & v.map(lambda x: limpeza.converter_data(x) is None) & ~v.map(limpeza.eh_nulo)).sum())
        conta["não converte (data impossível ou ano fora de 2000-2030)"] = invalidas
        out.append(tabela_md(pd.Series(conta), f"{arq}.{col}"))

    pub = compras.set_index("numero_controle_pncp")["data_publicacao"].map(limpeza.converter_data)
    r = resultados.copy()
    r["pub"] = r["numero_controle_pncp"].map(pub)
    r["res"] = r["data_resultado"].map(limpeza.converter_data)
    antes = r["res"].notna() & r["pub"].notna() & (r["res"] < r["pub"])
    out += [f"- Linhas de resultados com **data_resultado anterior à data_publicacao**: **{int(antes.sum())}** "
            f"(na fato, o item fica sem data de homologação e sem ciclo)", ""]

    # ---- 5) nulos disfarçados e texto ----------------------------------------------------------------------
    out += ["## 5. Nulos disfarçados, encoding e invisíveis (colunas de texto)", "",
            "| Arquivo.coluna | Nulos disfarçados | Acento quebrado (Ã§, Ã£...) | Caracteres invisíveis | Espaços repetidos/pontas |",
            "| --- | ---: | ---: | ---: | ---: |"]
    textos = {"compras": ["razao_social_orgao", "nome_unidade", "objeto_compra", "uf_sigla", "uf_nome", "modalidade_nome"],
              "itens": ["descricao", "material_ou_servico", "unidade_medida"],
              "resultados": ["nome_fornecedor", "porte", "tipo_pessoa"]}
    for arq, df in [("compras", compras), ("itens", itens), ("resultados", resultados)]:
        for col in textos[arq]:
            s = df[col]
            nulos = int(s.map(lambda v: v.strip() != "" and limpeza.eh_nulo(v.strip())).sum())
            mojibake = int(s.map(lambda v: limpeza.consertar_acento(v) != v).sum())
            invis = int(s.map(lambda v: any(c in v for c in ZERO_WIDTH)).sum())
            espacos = int(s.map(lambda v: v != " ".join(v.split()) and not any(c in v for c in ZERO_WIDTH)).sum())
            out.append(f"| {arq}.{col} | {nulos} | {mojibake} | {invis} | {espacos} |")
    out.append("")
    vazios = {f"{a}.{c}": int((df[c].str.strip() == "").sum())
              for a, df in [("compras", compras), ("itens", itens), ("resultados", resultados)] for c in df.columns}
    vazios = pd.Series(vazios)
    vazios = vazios[vazios > 0].sort_values(ascending=False).head(15)
    out.append(tabela_md(vazios, "Colunas com mais campos vazios (top 15)"))

    # ---- 6) modalidade, poder, sigilo ----------------------------------------------------------------------
    out += ["## 6. Domínios", "",
            tabela_md(compras["modalidade_id"].value_counts(), "compras.modalidade_id"),
            tabela_md(compras["poder_id"].value_counts(), "compras.poder_id"),
            tabela_md(itens["sigiloso"].value_counts(), "itens.sigiloso"),
            tabela_md(itens["material_ou_servico"].map(limpeza.limpar_texto).fillna("(nulo)").value_counts(), "itens.material_ou_servico")]

    config.PASTA_REPORTS.mkdir(parents=True, exist_ok=True)
    caminho = config.PASTA_REPORTS / "auditoria.md"
    caminho.write_text("\n".join(out), encoding="utf-8")
    print(f"Auditoria gravada em {caminho}")


if __name__ == "__main__":
    main()
