-- =====================================================================================
-- 01_criar_banco.sql  -  ESQUEMA ESTRELA (1 fato + 4 dimensoes)  -  PostgreSQL
-- -------------------------------------------------------------------------------------
-- Executado por src/carregar.py (banco.executar_script), DEPOIS de banco.recriar_banco().
-- O banco em si e recriado pelo Python: aqui so ficam as tabelas.
--
-- ATENCAO: o executor de scripts do projeto separa os comandos por ponto e virgula e
-- remove comentarios iniciados por dois hifens. Por isso: nada de ponto e virgula dentro
-- de texto e nada de dois hifens dentro de literais.
--
-- Decisoes de modelagem
--   * Chave substituta (sk_) INTEGER em toda dimensao; a chave natural (cnpj, modalidade_id,
--     uf_sigla...) fica como UNIQUE, para a carga ser idempotente e rastreavel ate o PNCP.
--   * Linha "Nao informado" (sk = -1) em cada dimensao: valor fora da sequencia 1, 2, 3...
--     para nunca colidir. Hoje nenhuma FK cai nela, mas ela garante que um dado futuro
--     sem dimensao nao quebre a integridade nem seja descartado em silencio.
--   * Dinheiro em NUMERIC(18,2) e precos unitarios/quantidades em NUMERIC(18,4):
--     nunca FLOAT, para nao acumular erro de arredondamento nas somas.
--   * CHECKs: o banco e a segunda barreira depois do Python (regra 4 do enunciado).
-- =====================================================================================


-- ------------------------------------------------------------------ DIMENSAO: QUEM COMPROU
CREATE TABLE dim_orgao (
    sk_orgao    INTEGER      PRIMARY KEY,
    cnpj_orgao  VARCHAR(20)  NOT NULL UNIQUE,
    nome_orgao  VARCHAR(300) NOT NULL,
    poder       VARCHAR(20)  NOT NULL,
    CONSTRAINT ck_dim_orgao_poder CHECK (poder IN ('Executivo', 'Legislativo', 'Judiciário', 'Não informado'))
);

-- ------------------------------------------------------------------ DIMENSAO: QUEM VENDEU
CREATE TABLE dim_fornecedor (
    sk_fornecedor   INTEGER      PRIMARY KEY,
    ni_fornecedor   VARCHAR(30)  NOT NULL UNIQUE,
    nome_fornecedor VARCHAR(300),
    tipo_pessoa     VARCHAR(2),
    porte           VARCHAR(20),
    CONSTRAINT ck_dim_fornecedor_tipo CHECK (tipo_pessoa IS NULL OR tipo_pessoa IN ('PJ', 'PF', 'PE'))
);

-- ------------------------------------------------------------------ DIMENSAO: COMO COMPROU
CREATE TABLE dim_modalidade (
    sk_modalidade   INTEGER      PRIMARY KEY,
    modalidade_id   INTEGER      NOT NULL UNIQUE,
    nome_modalidade VARCHAR(60)  NOT NULL
);

-- ------------------------------------------------------------------ DIMENSAO: ONDE
CREATE TABLE dim_localidade (
    sk_localidade INTEGER      PRIMARY KEY,
    uf_sigla      VARCHAR(10)  NOT NULL UNIQUE,
    uf_nome       VARCHAR(40)  NOT NULL,
    regiao        VARCHAR(20)  NOT NULL
);

-- ------------------------------------------------------------------ FATO: O QUE FOI COMPRADO
-- Grao: um item de contratacao (numero_controle_pncp + numero_item), com o fornecedor vencedor.
CREATE TABLE fato_item_contratado (
    sk_fato                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    numero_controle_pncp      VARCHAR(40)    NOT NULL,
    numero_item               INTEGER        NOT NULL,

    sk_orgao                  INTEGER        NOT NULL REFERENCES dim_orgao (sk_orgao),
    sk_fornecedor             INTEGER        NOT NULL REFERENCES dim_fornecedor (sk_fornecedor),
    sk_modalidade             INTEGER        NOT NULL REFERENCES dim_modalidade (sk_modalidade),
    sk_localidade             INTEGER        NOT NULL REFERENCES dim_localidade (sk_localidade),

    data_publicacao           DATE           NOT NULL,
    data_homologacao          DATE,

    descricao_item            TEXT,
    perfil_gasto              VARCHAR(30)    NOT NULL,

    quantidade                NUMERIC(18,4)  NOT NULL,
    valor_unitario_estimado   NUMERIC(18,4)  NOT NULL,
    valor_total_estimado      NUMERIC(18,2)  NOT NULL,
    valor_unitario_homologado NUMERIC(18,4)  NOT NULL,
    valor_total_homologado    NUMERIC(18,2)  NOT NULL,

    comparavel                SMALLINT       NOT NULL,
    economia_valor            NUMERIC(18,2),
    dias_ciclo                INTEGER,

    -- regra 1: o grao e unico
    CONSTRAINT uq_fato_item UNIQUE (numero_controle_pncp, numero_item),

    -- regra 4: o banco e a segunda barreira
    CONSTRAINT ck_fato_quantidade      CHECK (quantidade > 0),
    CONSTRAINT ck_fato_valores         CHECK (valor_unitario_estimado >= 0 AND valor_total_estimado >= 0
                                              AND valor_unitario_homologado >= 0 AND valor_total_homologado >= 0),
    -- regra 6: comparavel e flag 0/1
    CONSTRAINT ck_fato_comparavel      CHECK (comparavel IN (0, 1)),
    -- economia so existe onde ha comparacao
    CONSTRAINT ck_fato_economia_nula   CHECK (comparavel = 1 OR economia_valor IS NULL),
    -- regra 8: tres perfis possiveis
    CONSTRAINT ck_fato_perfil          CHECK (perfil_gasto IN ('Bens', 'Serviços', 'Obras e engenharia')),
    -- regra 7: homologacao antes da publicacao nunca chega ao banco (vira NULL) e ciclo nunca e negativo
    CONSTRAINT ck_fato_cronologia      CHECK (data_homologacao IS NULL OR data_homologacao >= data_publicacao),
    CONSTRAINT ck_fato_ciclo           CHECK (dias_ciclo IS NULL OR dias_ciclo >= 0),
    -- ciclo e data de homologacao nascem juntos: ou os dois existem, ou os dois sao vazios
    CONSTRAINT ck_fato_ciclo_coerente  CHECK ((data_homologacao IS NULL) = (dias_ciclo IS NULL))
);

-- Indices nas FKs (o PostgreSQL nao cria sozinho): aceleram os JOINs das perguntas e do Power BI
CREATE INDEX ix_fato_orgao      ON fato_item_contratado (sk_orgao);
CREATE INDEX ix_fato_fornecedor ON fato_item_contratado (sk_fornecedor);
CREATE INDEX ix_fato_modalidade ON fato_item_contratado (sk_modalidade);
CREATE INDEX ix_fato_localidade ON fato_item_contratado (sk_localidade);
CREATE INDEX ix_fato_data_pub   ON fato_item_contratado (data_publicacao);

-- ------------------------------------------------------------------ LINHAS "NAO INFORMADO" (sk = -1)
-- A chave natural precisa ser um valor que NAO existe nas demais linhas (a coluna e UNIQUE e NOT NULL).
INSERT INTO dim_orgao       (sk_orgao, cnpj_orgao, nome_orgao, poder)            VALUES (-1, 'NAO-INFORMADO', 'NÃO INFORMADO', 'Não informado');
INSERT INTO dim_fornecedor  (sk_fornecedor, ni_fornecedor, nome_fornecedor, tipo_pessoa, porte) VALUES (-1, 'NAO-INFORMADO', 'NÃO INFORMADO', NULL, NULL);
INSERT INTO dim_modalidade  (sk_modalidade, modalidade_id, nome_modalidade)      VALUES (-1, -1, 'Não informado');
INSERT INTO dim_localidade  (sk_localidade, uf_sigla, uf_nome, regiao)           VALUES (-1, 'NI', 'Não informado', 'Não informado');
