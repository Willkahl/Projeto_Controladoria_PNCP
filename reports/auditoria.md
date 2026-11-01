# Auditoria dos dados brutos (data/raw)

Gerado por `python -m src.auditoria`. Tudo lido como texto (dtype=str).

## 1. Tamanho e chaves

| Arquivo | Linhas | Colunas |
| --- | ---: | ---: |
| compras.csv | 2.042 | 25 |
| itens.csv | 7.077 | 14 |
| resultados.csv | 15.896 | 13 |

- `numero_controle_pncp` repetido em compras: **0**
- Itens repetidos (numero_controle_pncp + numero_item): **0**
- Resultados cancelados (data_cancelamento preenchida): **62**
- Resultados com ordem_classificacao_srp vazia: **11976**
- Itens com tem_resultado = False: **852**

## 2. Documentos (CNPJ/CPF)

**compras.cnpj_orgao**

| Situação | Linhas |
| --- | ---: |
| com máscara (pontos, barra ou hífen) | 176 |
| sem máscara e com menos de 14 dígitos (zero à esquerda perdido) | 77 |
| vazio ou nulo disfarçado | 0 |

**resultados.ni_fornecedor**

| Situação | Linhas |
| --- | ---: |
| com máscara | 1.633 |
| PJ com menos de 14 dígitos (zero perdido) | 194 |
| PF com menos de 11 dígitos (zero perdido) | 159 |
| PJ/PF com dígitos demais (documento impossível) | 0 |
| vazio ou nulo disfarçado | 0 |
| tipo_pessoa = PE (estrangeiro, mantido como veio) | 21 |

## 3. Dinheiro e números em texto

**itens.quantidade**

| Situação | Linhas |
| --- | ---: |
| ponto decimal | 5.596 |
| com R$ | 1.148 |
| vírgula decimal | 269 |
| milhar e decimal juntos | 64 |

Com espaço invisível/sem quebra: **264**

**itens.valor_unitario_estimado**

| Situação | Linhas |
| --- | ---: |
| ponto decimal | 5.475 |
| com R$ | 1.188 |
| milhar e decimal juntos | 224 |
| vírgula decimal | 190 |

Com espaço invisível/sem quebra: **301**

**resultados.quantidade_homologada**

| Situação | Linhas |
| --- | ---: |
| ponto decimal | 12.472 |
| com R$ | 2.561 |
| vírgula decimal | 451 |
| milhar e decimal juntos | 412 |

Com espaço invisível/sem quebra: **622**

**resultados.valor_unitario_homologado**

| Situação | Linhas |
| --- | ---: |
| ponto decimal | 12.282 |
| com R$ | 2.650 |
| milhar e decimal juntos | 532 |
| vírgula decimal | 432 |

Com espaço invisível/sem quebra: **704**

## 4. Datas

**compras.data_publicacao**

| Situação | Linhas |
| --- | ---: |
| AAAA-MM-DD (com ou sem hora) | 1.319 |
| DD/MM/AAAA (com ou sem hora) | 243 |
| DD-MM-AAAA | 138 |
| DD.MM.AAAA | 120 |
| AAAA/MM/DD | 116 |
| AAAAMMDD | 106 |
| vazio / nulo disfarçado | 0 |
| não converte (data impossível ou ano fora de 2000-2030) | 0 |

**resultados.data_resultado**

| Situação | Linhas |
| --- | ---: |
| AAAA-MM-DD (com ou sem hora) | 10.301 |
| DD/MM/AAAA (com ou sem hora) | 1.863 |
| DD-MM-AAAA | 912 |
| DD.MM.AAAA | 937 |
| AAAA/MM/DD | 960 |
| AAAAMMDD | 923 |
| vazio / nulo disfarçado | 0 |
| não converte (data impossível ou ano fora de 2000-2030) | 0 |

- Linhas de resultados com **data_resultado anterior à data_publicacao**: **234** (na fato, o item fica sem data de homologação e sem ciclo)

## 5. Nulos disfarçados, encoding e invisíveis (colunas de texto)

| Arquivo.coluna | Nulos disfarçados | Acento quebrado (Ã§, Ã£...) | Caracteres invisíveis | Espaços repetidos/pontas |
| --- | ---: | ---: | ---: | ---: |
| compras.razao_social_orgao | 0 | 0 | 0 | 58 |
| compras.nome_unidade | 0 | 14 | 0 | 63 |
| compras.objeto_compra | 0 | 43 | 1 | 519 |
| compras.uf_sigla | 0 | 0 | 0 | 0 |
| compras.uf_nome | 0 | 0 | 0 | 0 |
| compras.modalidade_nome | 0 | 0 | 0 | 0 |
| itens.descricao | 0 | 116 | 0 | 606 |
| itens.material_ou_servico | 0 | 0 | 0 | 0 |
| itens.unidade_medida | 0 | 0 | 0 | 935 |
| resultados.nome_fornecedor | 0 | 1 | 0 | 501 |
| resultados.porte | 4893 | 0 | 0 | 0 |
| resultados.tipo_pessoa | 0 | 0 | 0 | 0 |

**Colunas com mais campos vazios (top 15)**

| Situação | Linhas |
| --- | ---: |
| resultados.data_cancelamento | 15.834 |
| resultados.ordem_classificacao_srp | 11.976 |
| itens.catalogo_codigo_item | 7.068 |
| compras.data_abertura_proposta | 617 |
| compras.data_encerramento_proposta | 617 |
| itens.unidade_medida | 9 |

## 6. Domínios

**compras.modalidade_id**

| Situação | Linhas |
| --- | ---: |
| 9 | 427 |
| 6 | 425 |
| 8 | 425 |
| 4 | 401 |
| 12 | 317 |
| 5 | 42 |
| 7 | 5 |

**compras.poder_id**

| Situação | Linhas |
| --- | ---: |
| E | 1.873 |
| J | 151 |
| L | 18 |

**itens.sigiloso**

| Situação | Linhas |
| --- | ---: |
| False | 7.023 |
| True | 54 |

**itens.material_ou_servico**

| Situação | Linhas |
| --- | ---: |
| Material | 4.147 |
| Serviço | 2.930 |
