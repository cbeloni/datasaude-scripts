-- =============================================================================
-- Tabela: gestantes_uruguaiana
-- Origem: /Users/cauebeloni/Documents/Projeto Pensi/dados/uruguaiana-rs/Dados_gestantes.xlsx
--         Abas: "Grupo1" (504 registros) e "Grupo_2" (204 registros) = 708 total
-- Destino: MySQL 8.0.37 / database `datasaude`
--
-- Uma linha por gestante. A coluna `grupo` identifica a aba de origem do registro.
-- A carga e feita por UPSERT sobre (grupo, id_externo), portanto e idempotente.
-- =============================================================================

CREATE TABLE `gestantes_uruguaiana`
(
    -- ---------------------------------------------------------------- chaves
    `id`                          int          NOT NULL AUTO_INCREMENT,

    -- ------------------------------------------------ identificacao / origem
    `id_externo`                  varchar(50)  NOT NULL COMMENT 'ID original da planilha: Form1_1, Form2_204, ...',
    `grupo`                       varchar(20)  NOT NULL COMMENT 'NOVA COLUNA - aba de origem: Grupo1 | Grupo_2',
    `origem_arquivo`              varchar(255)          DEFAULT NULL COMMENT 'Caminho do arquivo xlsx de origem',

    -- ------------------------------------------------------------- datas
    `carimbo_data_hora`           datetime     NOT NULL COMMENT 'Timestamp de submissao do formulario',
    `data_coleta_original`        varchar(50)           DEFAULT NULL COMMENT 'Valor cru de "Data da Coleta" (auditoria)',
    `data_coleta`                 date                  DEFAULT NULL COMMENT 'Data de coleta saneada',
    `data_referencia`             date         NOT NULL COMMENT 'Data-ancora da janela de exposicao',
    `data_status`                 varchar(30)  NOT NULL DEFAULT 'OK' COMMENT 'OK | CORRIGIDA | FALLBACK_CARIMBO | INVALIDA',

    -- ------------------------------------------------ janela de exposicao
    `janela_inicio`               date         NOT NULL COMMENT 'data_referencia - 9 meses',
    `janela_fim`                  date         NOT NULL COMMENT '= data_referencia',
    `dias_janela`                 smallint     NOT NULL COMMENT 'Numero de dias INCLUSIVOS da janela (274-277) = linhas esperadas na exposicao',

    -- --------------------------------------------------------- endereco
    `endereco_original`           varchar(1000)         DEFAULT NULL COMMENT 'Texto cru do Excel (auditoria)',
    `endereco_ajustado`           varchar(1000)         DEFAULT NULL COMMENT 'NOVA COLUNA - endereco corrigido e padronizado, com o municipio anexado',
    `endereco_ajuste`             varchar(200)          DEFAULT NULL COMMENT 'Quais correcoes foram aplicadas (ex: separador, logradouro duplicado, municipio anexado)',
    `endereco_hash`               char(40)              DEFAULT NULL COMMENT 'SHA1 do endereco ajustado (chave do cache)',

    -- --------------------------------------------------- geocodificacao
    -- ATENCAO: latitude/longitude NUNCA ficam nulas. Quando o endereco nao existe ou
    -- nao e resolvivel, recebem o centroide do municipio (-29.75472 / -57.08833)
    -- e a linha e sinalizada com geo_default = 1.
    `latitude`                    decimal(10, 7)        DEFAULT NULL COMMENT 'geometry.lat do OpenCage, ou centroide do municipio quando geo_default = 1',
    `longitude`                   decimal(10, 7)        DEFAULT NULL COMMENT 'geometry.lng do OpenCage, ou centroide do municipio quando geo_default = 1',
    `geo_confianca`               tinyint               DEFAULT NULL COMMENT 'Campo confidence (0-10)',
    `geo_formatado`               varchar(500)          DEFAULT NULL COMMENT 'Campo formatted',
    `geo_status`                  varchar(30)  NOT NULL DEFAULT 'PENDENTE' COMMENT 'OK | BAIXA_CONFIANCA | CENTROIDE_MUNICIPIO | FORA_DO_MUNICIPIO | NAO_ENCONTRADO | SEM_ENDERECO | ERRO_API | PENDENTE',
    `geo_default`                 tinyint(1)   NOT NULL DEFAULT 0 COMMENT '1 = lat/lng sao o centroide do municipio, nao o endereco real',
    `geo_nivel`                   varchar(30)           DEFAULT NULL COMMENT 'components._type devolvido: road | house | city | municipality | ...',
    `geo_provider`                varchar(50)           DEFAULT NULL COMMENT 'Ex.: opencage',
    `geo_city`                    varchar(100)          DEFAULT NULL COMMENT 'components.city',
    `geo_state`                   varchar(50)           DEFAULT NULL COMMENT 'components.state_code',
    `geo_country`                 varchar(50)           DEFAULT NULL COMMENT 'components.country_code',
    `geo_postcode`                varchar(20)           DEFAULT NULL COMMENT 'components.postcode',
    `geo_suburb`                  varchar(100)          DEFAULT NULL COMMENT 'components.suburb',
    `geo_data_hora`               datetime              DEFAULT NULL COMMENT 'Momento da geocodificacao',

    -- ------------------------------------- pontos de grade das APIs de clima
    `grade_ar_latitude`           decimal(10, 7)        DEFAULT NULL COMMENT 'Latitude do ponto de grade da Air Quality API',
    `grade_ar_longitude`          decimal(10, 7)        DEFAULT NULL COMMENT 'Longitude do ponto de grade da Air Quality API',
    `grade_meteo_latitude`        decimal(10, 7)        DEFAULT NULL COMMENT 'Latitude do ponto de grade da Archive API',
    `grade_meteo_longitude`       decimal(10, 7)        DEFAULT NULL COMMENT 'Longitude do ponto de grade da Archive API',

    -- ----------------------------------------------------- exposicao
    `exposicao_status`            varchar(30)           DEFAULT NULL COMMENT 'COMPLETA | PARCIAL | SEM_COBERTURA | NAO_COLETADA',
    `dias_com_exposicao`          smallint              DEFAULT NULL COMMENT 'Dias gravados em gestantes_exposicao_diaria',

    -- -------------------------------------------------------- auditoria
    `validado`                    tinyint(1)   NOT NULL DEFAULT 0 COMMENT 'Revisado manualmente',
    `data_criacao`                timestamp             DEFAULT CURRENT_TIMESTAMP,
    `data_alteracao`              timestamp             DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `gestantes_uruguaiana_grupo_id_externo_uindex` (`grupo`, `id_externo`),
    KEY `gestantes_uruguaiana_data_referencia_index` (`data_referencia`),
    KEY `gestantes_uruguaiana_geo_status_index` (`geo_status`),
    KEY `gestantes_uruguaiana_geo_default_index` (`geo_default`),
    KEY `gestantes_uruguaiana_endereco_hash_index` (`endereco_hash`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci
    COMMENT = 'Gestantes de Uruguaiana/RS - Grupo1 (504) + Grupo_2 (204) = 708 registros';


-- -----------------------------------------------------------------------------
-- Carga (exemplo de UPSERT idempotente - Etapa 4)
-- -----------------------------------------------------------------------------
-- INSERT INTO gestantes_uruguaiana
--     (id_externo, grupo, carimbo_data_hora, data_coleta_original, data_coleta,
--      data_referencia, data_status, janela_inicio, janela_fim, dias_janela,
--      endereco_original, endereco_ajustado, endereco_ajuste, endereco_hash,
--      latitude, longitude, geo_confianca, geo_formatado, geo_status, geo_default,
--      geo_nivel, geo_provider, geo_city, geo_state, geo_country, geo_postcode,
--      geo_suburb, geo_data_hora)
-- VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
-- ON DUPLICATE KEY UPDATE
--     carimbo_data_hora = VALUES(carimbo_data_hora),
--     data_coleta = VALUES(data_coleta),
--     data_referencia = VALUES(data_referencia),
--     data_status = VALUES(data_status),
--     janela_inicio = VALUES(janela_inicio),
--     janela_fim = VALUES(janela_fim),
--     dias_janela = VALUES(dias_janela),
--     endereco_original = VALUES(endereco_original),
--     endereco_ajustado = VALUES(endereco_ajustado),
--     endereco_ajuste = VALUES(endereco_ajuste),
--     endereco_hash = VALUES(endereco_hash),
--     latitude = VALUES(latitude),
--     longitude = VALUES(longitude),
--     geo_confianca = VALUES(geo_confianca),
--     geo_formatado = VALUES(geo_formatado),
--     geo_status = VALUES(geo_status),
--     geo_default = VALUES(geo_default),
--     geo_nivel = VALUES(geo_nivel),
--     geo_city = VALUES(geo_city),
--     geo_state = VALUES(geo_state),
--     geo_country = VALUES(geo_country),
--     geo_postcode = VALUES(geo_postcode),
--     geo_suburb = VALUES(geo_suburb),
--     geo_data_hora = VALUES(geo_data_hora);


-- -----------------------------------------------------------------------------
-- Consultas de validacao (criterios de aceite do planejamento)
-- -----------------------------------------------------------------------------
-- SELECT COUNT(*) FROM gestantes_uruguaiana;                                  -- 708
-- SELECT grupo, COUNT(*) FROM gestantes_uruguaiana GROUP BY grupo;            -- Grupo1=504, Grupo_2=204
-- SELECT geo_status, COUNT(*) FROM gestantes_uruguaiana GROUP BY geo_status;
-- SELECT geo_default, COUNT(*) FROM gestantes_uruguaiana GROUP BY geo_default;-- 0 = resolvido no endereco
-- SELECT data_status, COUNT(*) FROM gestantes_uruguaiana GROUP BY data_status;-- <> OK = 22
-- SELECT MIN(dias_janela), MAX(dias_janela) FROM gestantes_uruguaiana;        -- 274 .. 277
--
-- INVARIANTE: latitude/longitude nunca sao nulas e todo geo_default = 1 aponta
--             para exatamente o centroide do municipio.
-- SELECT COUNT(*) FROM gestantes_uruguaiana
--  WHERE latitude IS NULL OR longitude IS NULL;                              -- 0
-- SELECT COUNT(*) FROM gestantes_uruguaiana
--  WHERE geo_default = 1
--    AND (latitude <> -29.754720 OR longitude <> -57.088330);                -- 0
-- SELECT COUNT(*) FROM gestantes_uruguaiana
--  WHERE geo_default = 0
--    AND (latitude BETWEEN -29.7547 AND -29.7548
--         OR latitude NOT BETWEEN -30.21 AND -29.40);                        -- 0
