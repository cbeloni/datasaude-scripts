-- =============================================================================
-- Tabela: geocode_cache
-- Origem: respostas da API OpenCage Geocoding
-- Destino: MySQL 8.0.37 / database `datasaude`
--
-- Cache permanente da geocodificacao. Objetivos:
--   1. Nao repetir chamadas para os 547 enderecos unicos (economia de quota).
--   2. Permitir reexecucao do pipeline sem custo adicional.
--   3. Atender ao requisito de armazenamento permanente de resultados da OpenCage.
--
-- A chave do cache e o SHA1 do endereco normalizado (endereco_hash) + provider.
-- Volumetria esperada: ~547 linhas.
-- =============================================================================

CREATE TABLE `geocode_cache`
(
    `id`                   int          NOT NULL AUTO_INCREMENT,

    -- ------------------------------------------------------------- chave
    `endereco_hash`        char(40)     NOT NULL COMMENT 'SHA1 do endereco normalizado',
    `provider`             varchar(50)  NOT NULL DEFAULT 'opencage',

    -- --------------------------------------------------------- enderecos
    `endereco_original`    varchar(1000) NOT NULL COMMENT 'Texto cru vindo do Excel',
    `endereco_consultado`  varchar(1000) NOT NULL COMMENT 'Texto efetivamente enviado na query string',

    -- ----------------------------------------------------------- resultado
    `status`               varchar(30)  NOT NULL COMMENT 'OK | BAIXA_CONFIANCA | NAO_CONFIRMADO | NAO_ENCONTRADO | ERRO_API | SEM_ENDERECO',
    `latitude`             decimal(10, 7)        DEFAULT NULL COMMENT 'results[0].geometry.lat',
    `longitude`            decimal(10, 7)        DEFAULT NULL COMMENT 'results[0].geometry.lng',
    `confianca`            tinyint               DEFAULT NULL COMMENT 'results[0].confidence (0-10)',
    `formatado`            varchar(500)          DEFAULT NULL COMMENT 'results[0].formatted',
    `componentes`          json                  DEFAULT NULL COMMENT 'results[0].components',
    `resposta_bruta`       json                  DEFAULT NULL COMMENT 'JSON integral da resposta (auditoria)',

    -- ---------------------------------------------------------- controle
    `tentativas`           tinyint unsigned NOT NULL DEFAULT 1 COMMENT 'Numero de tentativas ate obter resposta definitiva',
    `data_criacao`         timestamp             DEFAULT CURRENT_TIMESTAMP,
    `data_alteracao`       timestamp             DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `geocode_cache_endereco_hash_provider_uindex` (`endereco_hash`, `provider`),
    KEY `geocode_cache_status_index` (`status`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci
    COMMENT = 'Cache permanente de geocodificacao (OpenCage) - evita repetir chamadas a API';


-- -----------------------------------------------------------------------------
-- Carga (exemplo de UPSERT idempotente - Etapa 3)
-- -----------------------------------------------------------------------------
-- INSERT INTO geocode_cache
--     (endereco_hash, provider, endereco_original, endereco_consultado, status,
--      latitude, longitude, confianca, formatado, componentes, resposta_bruta, tentativas)
-- VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
-- ON DUPLICATE KEY UPDATE
--     endereco_consultado = VALUES(endereco_consultado),
--     status = VALUES(status),
--     latitude = VALUES(latitude),
--     longitude = VALUES(longitude),
--     confianca = VALUES(confianca),
--     formatado = VALUES(formatado),
--     componentes = VALUES(componentes),
--     resposta_bruta = VALUES(resposta_bruta),
--     tentativas = tentativas + 1;


-- -----------------------------------------------------------------------------
-- Consultas uteis
-- -----------------------------------------------------------------------------
-- Distribuicao de status:
-- SELECT status, COUNT(*) FROM geocode_cache GROUP BY status;
--
-- Taxa de sucesso por confianca:
-- SELECT confianca, COUNT(*) FROM geocode_cache GROUP BY confianca ORDER BY confianca;
--
-- Enderecos que consumiram mais de uma chamada (deveria ser sempre 1):
-- SELECT endereco_consultado, tentativas FROM geocode_cache WHERE tentativas > 1;
--
-- Pendencias para revisao manual (exportar para CSV):
-- SELECT endereco_original, endereco_consultado, status, formatado
--   FROM geocode_cache
--  WHERE status IN ('NAO_ENCONTRADO', 'BAIXA_CONFIANCA', 'NAO_CONFIRMADO', 'ERRO_API')
--  ORDER BY status, endereco_original;
