-- =====================================================================================
-- 02_perguntas.sql  -  AS 6 PERGUNTAS DE NEGOCIO DA CONTROLADORIA  (PostgreSQL)
-- -------------------------------------------------------------------------------------
-- Rode no pgAdmin (ou: psql -d pncp_controladoria -f sql/02_perguntas.sql) depois de python -m src.carregar.
--
-- Regras que valem para TODAS as consultas
--   * Percentual = SOMA / SOMA, nunca media de percentuais.
--   * Economia so conta itens COMPARAVEIS (comparavel = 1):
--         economia   = SUM(estimado - homologado) nos comparaveis
--         economia % = economia / SUM(estimado dos comparaveis)
--   * Volume = soma do valor_total_homologado de TODOS os itens da fato (comparaveis ou nao).
--   * NULLIF(denominador, 0): modalidades sem item comparavel (Credenciamento) ficam com % vazio.
--   * Fornecedor = ni_fornecedor (CNPJ/CPF limpo): o mesmo nome com CNPJ diferente e outro fornecedor.
-- Estas consultas sao a contraparte em SQL das medidas DAX do Power BI: os numeros devem ser iguais.
-- =====================================================================================


-- =====================================================================================
-- P1. ECONOMIA GLOBAL DO PODER PUBLICO
--     Qual o percentual e o valor nominal economizado (estimado x homologado)?
-- =====================================================================================
SELECT
    COUNT(*)                                                                    AS itens_na_fato,
    COUNT(*) FILTER (WHERE comparavel = 1)                                      AS itens_comparaveis,
    ROUND(100.0 * COUNT(*) FILTER (WHERE comparavel = 1) / COUNT(*), 2)         AS pct_itens_comparaveis,
    SUM(valor_total_homologado)                                                 AS volume_homologado,
    SUM(CASE WHEN comparavel = 1 THEN valor_total_estimado ELSE 0 END)          AS estimado_comparavel,
    SUM(CASE WHEN comparavel = 1 THEN valor_total_homologado ELSE 0 END)        AS homologado_comparavel,
    SUM(economia_valor)                                                         AS economia_reais,
    ROUND(100.0 * SUM(economia_valor)
          / NULLIF(SUM(CASE WHEN comparavel = 1 THEN valor_total_estimado ELSE 0 END), 0), 2) AS economia_pct,
    COUNT(*) FILTER (WHERE comparavel = 1 AND valor_total_homologado > valor_total_estimado) AS itens_com_sobrepreco
FROM fato_item_contratado;


-- =====================================================================================
-- P2. CONCENTRACAO E RISCO DE FORNECEDORES
--     Quem sao os 10 maiores em volume e que % do total esta concentrado neles?
-- =====================================================================================
-- P2a) Ranking dos 10 maiores, com participacao individual e acumulada
WITH volume_por_fornecedor AS (
    SELECT d.ni_fornecedor,
           d.nome_fornecedor,
           COUNT(*)                         AS itens,
           SUM(f.valor_total_homologado)    AS volume
    FROM fato_item_contratado f
    JOIN dim_fornecedor d ON d.sk_fornecedor = f.sk_fornecedor
    GROUP BY d.ni_fornecedor, d.nome_fornecedor
),
total AS (
    SELECT SUM(valor_total_homologado) AS volume_total FROM fato_item_contratado
)
SELECT
    ROW_NUMBER() OVER (ORDER BY v.volume DESC)                                          AS posicao,
    v.ni_fornecedor,
    v.nome_fornecedor,
    v.itens,
    v.volume,
    ROUND(100.0 * v.volume / t.volume_total, 2)                                         AS pct_do_total,
    ROUND(100.0 * SUM(v.volume) OVER (ORDER BY v.volume DESC) / t.volume_total, 2)      AS pct_acumulado
FROM volume_por_fornecedor v
CROSS JOIN total t
ORDER BY v.volume DESC
LIMIT 10;

-- P2b) Concentracao dos 10 maiores (uma linha so) e total de fornecedores
WITH volume_por_fornecedor AS (
    SELECT sk_fornecedor, SUM(valor_total_homologado) AS volume
    FROM fato_item_contratado
    GROUP BY sk_fornecedor
),
top10 AS (
    SELECT volume FROM volume_por_fornecedor ORDER BY volume DESC LIMIT 10
)
SELECT
    (SELECT COUNT(*) FROM volume_por_fornecedor)                                        AS fornecedores_distintos,
    (SELECT SUM(volume) FROM top10)                                                     AS volume_top10,
    (SELECT SUM(volume) FROM volume_por_fornecedor)                                     AS volume_total,
    ROUND(100.0 * (SELECT SUM(volume) FROM top10)
          / (SELECT SUM(volume) FROM volume_por_fornecedor), 2)                         AS concentracao_top10_pct;


-- =====================================================================================
-- P3. EFICACIA POR MODALIDADE
--     Quais modalidades dao maior desagio e quais concentram mais recursos?
-- =====================================================================================
SELECT
    m.modalidade_id,
    m.nome_modalidade,
    COUNT(*)                                                                    AS itens,
    COUNT(*) FILTER (WHERE f.comparavel = 1)                                    AS itens_comparaveis,
    SUM(f.valor_total_homologado)                                               AS volume_homologado,
    ROUND(100.0 * SUM(f.valor_total_homologado)
          / SUM(SUM(f.valor_total_homologado)) OVER (), 2)                      AS pct_do_volume,
    SUM(f.economia_valor)                                                       AS economia_reais,
    ROUND(100.0 * SUM(f.economia_valor)
          / NULLIF(SUM(CASE WHEN f.comparavel = 1 THEN f.valor_total_estimado ELSE 0 END), 0), 2) AS economia_pct
FROM fato_item_contratado f
JOIN dim_modalidade m ON m.sk_modalidade = f.sk_modalidade
GROUP BY m.modalidade_id, m.nome_modalidade
ORDER BY economia_pct DESC NULLS LAST;


-- =====================================================================================
-- P4. TEMPO DO CICLO DE COMPRAS
--     Duracao media (dias) entre publicacao e homologacao, por orgao.
--     Agrupa pelo NOME padronizado (o mesmo orgao tem varias unidades/CNPJ) e so mostra
--     orgaos com 5 ou mais itens COM ciclo (COUNT(dias_ciclo) ignora os vazios).
-- =====================================================================================
-- P4a) Ranking por orgao (do mais lento para o mais rapido)
SELECT
    o.nome_orgao,
    COUNT(DISTINCT o.cnpj_orgao)        AS unidades_compradoras,
    COUNT(f.dias_ciclo)                 AS itens_com_ciclo,
    ROUND(AVG(f.dias_ciclo), 1)         AS ciclo_medio_dias,
    MAX(f.dias_ciclo)                   AS ciclo_maximo_dias
FROM fato_item_contratado f
JOIN dim_orgao o ON o.sk_orgao = f.sk_orgao
GROUP BY o.nome_orgao
HAVING COUNT(f.dias_ciclo) >= 5
ORDER BY ciclo_medio_dias DESC;

-- P4b) Visao geral do ciclo (a media ignora os itens sem homologacao valida)
SELECT
    COUNT(dias_ciclo)                   AS itens_com_ciclo,
    COUNT(*) - COUNT(dias_ciclo)        AS itens_sem_ciclo,
    ROUND(AVG(dias_ciclo), 1)           AS ciclo_medio_dias,
    MAX(dias_ciclo)                     AS ciclo_maximo_dias
FROM fato_item_contratado;


-- =====================================================================================
-- P5. DISTRIBUICAO REGIONAL
--     Quais estados e regioes concentram a maior despesa e quais tem melhor desconto?
-- =====================================================================================
-- P5a) Por regiao
SELECT
    l.regiao,
    COUNT(DISTINCT f.sk_orgao)                                                  AS unidades_compradoras,
    COUNT(*)                                                                    AS itens,
    SUM(f.valor_total_homologado)                                               AS volume_homologado,
    ROUND(100.0 * SUM(f.valor_total_homologado)
          / SUM(SUM(f.valor_total_homologado)) OVER (), 2)                      AS pct_do_volume,
    ROUND(100.0 * SUM(f.economia_valor)
          / NULLIF(SUM(CASE WHEN f.comparavel = 1 THEN f.valor_total_estimado ELSE 0 END), 0), 2) AS economia_pct
FROM fato_item_contratado f
JOIN dim_localidade l ON l.sk_localidade = f.sk_localidade
GROUP BY l.regiao
ORDER BY volume_homologado DESC;

-- P5b) Por estado (UF)
SELECT
    l.uf_sigla,
    l.uf_nome,
    l.regiao,
    COUNT(DISTINCT f.sk_orgao)                                                  AS unidades_compradoras,
    COUNT(*)                                                                    AS itens,
    SUM(f.valor_total_homologado)                                               AS volume_homologado,
    ROUND(100.0 * SUM(f.valor_total_homologado)
          / SUM(SUM(f.valor_total_homologado)) OVER (), 2)                      AS pct_do_volume,
    ROUND(100.0 * SUM(f.economia_valor)
          / NULLIF(SUM(CASE WHEN f.comparavel = 1 THEN f.valor_total_estimado ELSE 0 END), 0), 2) AS economia_pct
FROM fato_item_contratado f
JOIN dim_localidade l ON l.sk_localidade = f.sk_localidade
GROUP BY l.uf_sigla, l.uf_nome, l.regiao
ORDER BY volume_homologado DESC;


-- =====================================================================================
-- P6. PERFIL DOS GASTOS
--     Como os recursos se distribuem entre bens, servicos e obras e engenharia?
--     perfil_gasto e coluna da propria fato: nao precisa de JOIN.
-- =====================================================================================
SELECT
    perfil_gasto,
    COUNT(*)                                                                    AS itens,
    SUM(valor_total_homologado)                                                 AS volume_homologado,
    ROUND(100.0 * SUM(valor_total_homologado)
          / SUM(SUM(valor_total_homologado)) OVER (), 1)                        AS pct_do_volume,
    ROUND(SUM(valor_total_homologado) / COUNT(*), 2)                            AS ticket_medio_por_item,
    ROUND(100.0 * SUM(economia_valor)
          / NULLIF(SUM(CASE WHEN comparavel = 1 THEN valor_total_estimado ELSE 0 END), 0), 2) AS economia_pct
FROM fato_item_contratado
GROUP BY perfil_gasto
ORDER BY volume_homologado DESC;
