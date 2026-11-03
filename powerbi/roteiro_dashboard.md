# Roteiro do dashboard (Power BI Desktop)

O arquivo `.pbix` é montado no Power BI Desktop e salvo na pasta (`powerbi/controladoria_pncp.pbix`).
Este roteiro lista, página a página, o que montar. As fórmulas estão em [`medidas_dax.md`](medidas_dax.md).

## 1. Conexão
1. **Obter dados → Banco de dados PostgreSQL** → servidor `localhost`, banco `pncp_controladoria` (modo **Importar**).
2. Marque as 5 tabelas: `fato_item_contratado`, `dim_orgao`, `dim_fornecedor`, `dim_modalidade`, `dim_localidade`.
3. Desmarque **Incluir colunas de relacionamento**.
4. Em `fato_item_contratado`, remova `descricao_item` se o arquivo ficar pesado (ela só serve para auditoria).
5. As linhas `sk = -1` ("Não informado") existem nas dimensões mas nenhuma FK aponta para elas: não aparecem nos visuais.

## 2. Modelo
Crie o Calendário, os relacionamentos e as 15 medidas conforme `medidas_dax.md`. Desligue a hierarquia automática de data.

## 3. Páginas (cada uma: pergunta no título → números → conclusão em caixa de texto)

| Página | Pergunta (título) | Medidas | Visuais sugeridos |
| --- | --- | --- | --- |
| 1 Economia | Quanto o governo economizou? | 1, 2, 3, 4, 5 | 4 cartões (Volume, Economia R$, Economia %, % Comparáveis) + colunas de Economia % por mês (`Calendario[Ano-Mês]`) |
| 2 Fornecedores | Quem concentra o orçamento? É um risco? | 2, 6, 7, 8 | Barras horizontais Top 10 (filtro N superior por `Volume Homologado`), cartão `Concentração Top 10 %`, tabela com ranking e participação |
| 3 Modalidades | Qual economiza mais e qual movimenta mais dinheiro? | 2, 4, 5, 9, 10 | Barras de Economia % por modalidade, rosca/barras de `Participação no Volume %`, tabela com `Deságio vs Média Geral (p.p.)` |
| 4 Ciclo de Compras | Onde as compras demoram mais? | 11, 12, 13 | Barras de `Ciclo Médio` por `nome_orgao` (filtro: itens com ciclo >= 5), cartões Máximo e Itens sem Ciclo |
| 5 Regional | Onde se gasta mais e onde há mais desconto? | 2, 4, 9, 14 | Mapa ou barras por UF (Volume), barras por Região (Economia %), cartão Qtd Unidades Compradoras |
| 6 Perfil de Gastos | Em que o dinheiro é gasto? | 2, 4, 9, 15 | Rosca de `Participação no Volume %` por `perfil_gasto`, cartões de Ticket Médio e Economia % |

No filtro do visual de ciclo por órgão: arraste `nome_orgao` para o visual, adicione um filtro de visual sobre a medida
`COUNT(dias_ciclo)` (ou crie a medida extra `Itens com Ciclo = COUNT ( fato_item_contratado[dias_ciclo] )`) com valor **>= 5**.

**Conclusão de cada página:** escreva você mesmo uma frase dizendo o que os números significam para a Controladoria.
Pontos que os números do banco permitem destacar (para você confirmar na tela e reescrever com suas palavras):

- P1: a economia de 14,46% vale para a base comparável (89% dos itens). Sem o filtro de comparáveis o número seria enganoso.
- P2: os 10 maiores fornecedores concentram 41,43% do volume e o maior deles (um único item de R$ 1,06 bi) sozinho passa de 13%. Vale a conferência manual desse item.
- P3: Pregão Eletrônico tem o maior deságio (24,0%), mas a Concorrência Eletrônica movimenta 58% do dinheiro. Credenciamento (27% do volume) não tem economia calculável.
- P4: a média é de 48 dias, mas há órgãos acima de 100 dias e ciclos de até 611 dias.
- P5: o Centro-Oeste (DF) concentra 44% do volume; o Norte tem o maior desconto (21,4%).
- P6: Obras e engenharia ficam com 60,8% do volume, em apenas 967 itens.

## 4. Navegação (UX)
- **Botões das páginas:** Ação → **Navegação de página** → destino.
- Copie o menu para todas as páginas (mesma posição = Repetição e Alinhamento do CRAP).

## 5. Tooltip personalizado
1. Nova página `Tooltip`, **Formato da página → Tamanho da página: Dica de ferramenta**, e ative **Permitir uso como dica de ferramenta**.
2. Coloque `Título Dinâmico do Tooltip`, `Economia %`, `Ciclo Médio (dias)`, `Itens sem Ciclo` e `Ticket Médio por Item (R$)`.
3. Nos visuais principais: **Formato → Dica de ferramenta → Tipo: Página → Página: Tooltip**.

## 6. Design (CRAP)
Paleta com propósito: um tom neutro para o geral e **uma** cor de destaque para o que importa (ex.: a barra/valor que responde à pergunta);
vermelho só para risco (concentração, sobrepreço, ciclo longo). Mesma grade, mesma fonte e mesmo cabeçalho em todas as páginas.

## 7. Checagem final
Os números dos cartões têm de ser os da tabela "Números que o dashboard deve mostrar" no fim de `medidas_dax.md` (iguais ao SQL).
