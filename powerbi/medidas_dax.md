# Calendário e medidas DAX

Fórmulas de referência para o `.pbix`. Crie cada uma no Power BI Desktop em **Modelagem → Nova medida / Nova tabela**.
Todas as medidas ficam em uma tabela só para elas (`_Medidas`) e cada uma em uma **pasta de exibição** (uma por pergunta).

> Como criar a tabela `_Medidas`: **Inserir dados → Carregar** (tabela vazia chamada `_Medidas`). Depois apague a coluna que vier.
> Pasta de exibição: selecione a medida → painel **Propriedades → Geral → Pasta de exibição** (ex.: `P1 Economia`).

Nomes das tabelas no modelo: `fato_item_contratado`, `dim_orgao`, `dim_fornecedor`, `dim_modalidade`, `dim_localidade`, `Calendario`.

---

## Tabela Calendário (DAX, dinâmica)

Os limites vêm dos dados (nada digitado): começa em 1º de janeiro do ano da menor data e termina em 31 de dezembro do ano da maior data,
considerando publicação **e** homologação (a homologação chega a 2026).

```dax
Calendario =
VAR _MinData = MIN ( fato_item_contratado[data_publicacao] )
VAR _MaxData = MAX ( MAX ( fato_item_contratado[data_publicacao] ), MAX ( fato_item_contratado[data_homologacao] ) )
VAR _Base    = CALENDAR ( DATE ( YEAR ( _MinData ), 1, 1 ), DATE ( YEAR ( _MaxData ), 12, 31 ) )
RETURN
    SELECTCOLUMNS (
        _Base,
        "Data",       [Date],
        "Ano",        YEAR ( [Date] ),
        "Mês Núm",    MONTH ( [Date] ),
        "Mês",        FORMAT ( [Date], "mmm", "pt-BR" ),
        "Ano-Mês Núm", YEAR ( [Date] ) * 100 + MONTH ( [Date] ),
        "Ano-Mês",    FORMAT ( [Date], "yyyy-mm" )
    )
```

Configuração obrigatória (**Exibição de tabela → selecione a coluna → Classificar por coluna**):

| Coluna | Classificar por |
| --- | --- |
| `Mês` | `Mês Núm` |
| `Ano-Mês` | `Ano-Mês Núm` |

Depois: **Ferramentas de tabela → Marcar como tabela de datas → coluna `Data`**.

---

## Modelo e relacionamentos (visão de modelo)

| De (lado 1) | Para (lado N) | Estado |
| --- | --- | --- |
| `dim_orgao[sk_orgao]` | `fato_item_contratado[sk_orgao]` | ativo |
| `dim_fornecedor[sk_fornecedor]` | `fato_item_contratado[sk_fornecedor]` | ativo |
| `dim_modalidade[sk_modalidade]` | `fato_item_contratado[sk_modalidade]` | ativo |
| `dim_localidade[sk_localidade]` | `fato_item_contratado[sk_localidade]` | ativo |
| `Calendario[Data]` | `fato_item_contratado[data_publicacao]` | **ativo** |
| `Calendario[Data]` | `fato_item_contratado[data_homologacao]` | **inativo** (use `USERELATIONSHIP`) |

Direção do filtro: única (da dimensão para a fato). Esconda as colunas `sk_*` do modo de exibição de relatório.
Desligue a **hierarquia automática de data** (Arquivo → Opções → Arquivo atual → Carregamento de dados → Hora/data automática).

---

## As 15 medidas obrigatórias

### P1 Economia

```dax
Valor Estimado Comparável =
CALCULATE (
    SUM ( fato_item_contratado[valor_total_estimado] ),
    fato_item_contratado[comparavel] = 1
)
```

```dax
Volume Homologado =
SUM ( fato_item_contratado[valor_total_homologado] )
```

```dax
Economia (R$) =
VAR _Estimado   = [Valor Estimado Comparável]
VAR _Homologado =
    CALCULATE (
        SUM ( fato_item_contratado[valor_total_homologado] ),
        fato_item_contratado[comparavel] = 1
    )
RETURN
    _Estimado - _Homologado
```

```dax
Economia % =
VAR _Economia  = [Economia (R$)]
VAR _Estimado  = [Valor Estimado Comparável]
RETURN
    DIVIDE ( _Economia, _Estimado )
```

```dax
% de Itens Comparáveis =
VAR _Comparaveis = CALCULATE ( COUNTROWS ( fato_item_contratado ), fato_item_contratado[comparavel] = 1 )
VAR _Total       = COUNTROWS ( fato_item_contratado )
RETURN
    DIVIDE ( _Comparaveis, _Total )
```

### P2 Fornecedores

```dax
Participação do Fornecedor % =
VAR _Volume = [Volume Homologado]
VAR _Total  = CALCULATE ( [Volume Homologado], ALL ( dim_fornecedor ) )
RETURN
    DIVIDE ( _Volume, _Total )
```

```dax
Ranking do Fornecedor =
IF (
    ISINSCOPE ( dim_fornecedor[ni_fornecedor] ),
    RANKX ( ALL ( dim_fornecedor ), [Volume Homologado], , DESC, DENSE )
)
```

```dax
Concentração Top 10 % =
VAR _Total = CALCULATE ( [Volume Homologado], ALL ( dim_fornecedor ) )
VAR _Top10 = TOPN ( 10, ALL ( dim_fornecedor ), [Volume Homologado], DESC )
VAR _VolumeTop10 = CALCULATE ( [Volume Homologado], KEEPFILTERS ( _Top10 ) )
RETURN
    DIVIDE ( _VolumeTop10, _Total )
```

### P3 Modalidades

```dax
Participação no Volume % =
VAR _Volume = [Volume Homologado]
VAR _Total  = CALCULATE ( [Volume Homologado], ALLSELECTED () )
RETURN
    DIVIDE ( _Volume, _Total )
```

```dax
Deságio vs Média Geral (p.p.) =
VAR _Atual = [Economia %]
VAR _Geral = CALCULATE ( [Economia %], REMOVEFILTERS () )
RETURN
    IF ( NOT ISBLANK ( _Atual ), ( _Atual - _Geral ) * 100 )
```

Formate esta medida como **número decimal com 1 casa** (ex.: 2,5), nunca como %. O `IF` deixa Credenciamento em branco
(não tem item comparável) em vez de mostrar um falso desvio negativo.

### P4 Ciclo de Compras

```dax
Ciclo Médio (dias) =
VAR _Media = AVERAGE ( fato_item_contratado[dias_ciclo] )
RETURN
    _Media
```

```dax
Ciclo Máximo (dias) =
MAX ( fato_item_contratado[dias_ciclo] )
```

```dax
Itens sem Ciclo =
VAR _Total     = COUNTROWS ( fato_item_contratado )
VAR _ComCiclo  = COUNT ( fato_item_contratado[dias_ciclo] )
RETURN
    _Total - _ComCiclo
```

Os itens sem ciclo têm `dias_ciclo` vazio, por isso `AVERAGE` e `COUNT` já os ignoram.

### P5 Distribuição Regional

```dax
Qtd Unidades Compradoras =
DISTINCTCOUNT ( fato_item_contratado[sk_orgao] )
```

Contar `sk_orgao` **na fato** (e não na dimensão) faz a medida responder aos filtros de UF, modalidade e período.
Como cada `sk_orgao` corresponde a um `cnpj_orgao` único, o número é o mesmo de `DISTINCTCOUNT ( dim_orgao[cnpj_orgao] )` sem filtros (363).

### P6 Perfil de Gastos

```dax
Ticket Médio por Item (R$) =
VAR _Volume = [Volume Homologado]
VAR _Itens  = COUNTROWS ( fato_item_contratado )
RETURN
    DIVIDE ( _Volume, _Itens )
```

---

## Extras (opcionais)

```dax
Itens com Sobrepreço =
COUNTROWS (
    FILTER (
        fato_item_contratado,
        fato_item_contratado[comparavel] = 1
            && fato_item_contratado[valor_total_homologado] > fato_item_contratado[valor_total_estimado]
    )
)
```

```dax
Economia (R$) - Conferência SUMX =
SUMX ( fato_item_contratado, fato_item_contratado[economia_valor] )
```
Deve ser igual a `[Economia (R$)]` (prova de que a coluna `economia_valor` do banco e a medida DAX contam a mesma coisa).

```dax
Volume por Data de Homologação =
CALCULATE (
    [Volume Homologado],
    USERELATIONSHIP ( Calendario[Data], fato_item_contratado[data_homologacao] )
)
```

```dax
Variação Mensal % =
VAR _Atual    = [Volume Homologado]
VAR _Anterior = CALCULATE ( [Volume Homologado], DATEADD ( Calendario[Data], -1, MONTH ) )
RETURN
    DIVIDE ( _Atual - _Anterior, _Anterior )
```

```dax
Volume Acumulado no Ano =
CALCULATE ( [Volume Homologado], DATESYTD ( Calendario[Data] ) )
```

```dax
Título Dinâmico do Tooltip =
SELECTEDVALUE ( dim_orgao[nome_orgao], "Visão geral" )
```

---

## Números que o dashboard deve mostrar (iguais ao `sql/02_perguntas.sql`)

| Medida | Valor esperado |
| --- | --- |
| Volume Homologado | R$ 8.044.498.805,74 |
| Valor Estimado Comparável | R$ 6.867.663.469,91 |
| Economia (R$) | R$ 992.861.686,95 |
| Economia % | 14,46% |
| % de Itens Comparáveis | 89,08% (5.457 de 6.126) |
| Concentração Top 10 % | 41,43% |
| Ciclo Médio (dias) / Máximo | 48,1 / 611 |
| Itens sem Ciclo | 230 |
| Qtd Unidades Compradoras (total) | 363 |
| Ticket Médio por Item (R$) | R$ 1.313.173,16 (= 8.044.498.805,74 ÷ 6.126) |
