-- =============================================================================
-- Tabela: gestantes_exposicao_diaria
-- Origem: Open-Meteo Air Quality (pm10, pm2_5) + Open-Meteo Archive (temperature_2m)
--         Agregacao diaria das series horarias da janela de 9 meses de cada gestante.
-- Destino: MySQL 8.0.37 / database `datasaude`
--
-- Uma linha por (gestante, dia). Janela = [data_referencia - 9 meses, data_referencia],
-- ou seja, dia_relativo vai de -274 (aprox.) ate 0.
-- Volume: 708 gestantes x ~274 dias = 194.169 linhas.
-- (TODAS as gestantes tem coordenada: quando o endereco nao existe ou nao e
--  resolvivel, usa-se o centroide do municipio -29.75472 / -57.08833,
--  sinalizado por gestantes_uruguaiana.geo_default = 1.)
-- A carga e feita por UPSERT sobre (id_gestante, data), portanto e idempotente.
-- =============================================================================

CREATE TABLE `gestantes_exposicao_diaria`
(
    -- ---------------------------------------------------------------- chaves
    `id`                        bigint           NOT NULL AUTO_INCREMENT,
    `id_gestante`               int              NOT NULL COMMENT 'FK -> gestantes_uruguaiana.id',

    -- ------------------------------------------- desnormalizacao p/ consulta
    `grupo`                     varchar(20)      NOT NULL COMMENT 'Grupo1 | Grupo_2 (copia de gestantes_uruguaiana)',
    `id_externo`                varchar(50)      NOT NULL COMMENT 'Form1_1, Form2_204, ... (copia)',

    -- ------------------------------------------------------------- tempo
    `data`                      date             NOT NULL COMMENT 'Dia calendario em America/Sao_Paulo',
    `dia_relativo`              smallint         NOT NULL COMMENT '(data - data_referencia) em dias - de -274 ate 0',
    `mes_relativo`              tinyint          NOT NULL COMMENT 'Mes da janela de 9 meses: 1 (mais antigo) a 9 (o da coleta)',

    -- ------------------------------------------------------- material particulado
    `pm10_media`                decimal(8, 3)             DEFAULT NULL COMMENT 'ug/m3 - media diaria',
    `pm10_min`                  decimal(8, 3)             DEFAULT NULL COMMENT 'ug/m3 - minimo horario do dia',
    `pm10_max`                  decimal(8, 3)             DEFAULT NULL COMMENT 'ug/m3 - maximo horario do dia',
    `pm10_horas_validas`        tinyint unsigned NOT NULL DEFAULT 0 COMMENT 'Horas com valor nao nulo (0-24)',

    `pm2_5_media`               decimal(8, 3)             DEFAULT NULL COMMENT 'ug/m3 - media diaria',
    `pm2_5_min`                 decimal(8, 3)             DEFAULT NULL COMMENT 'ug/m3 - minimo horario do dia',
    `pm2_5_max`                 decimal(8, 3)             DEFAULT NULL COMMENT 'ug/m3 - maximo horario do dia',
    `pm2_5_horas_validas`       tinyint unsigned NOT NULL DEFAULT 0 COMMENT 'Horas com valor nao nulo (0-24)',

    -- --------------------------------------------------------- temperatura
    `temperatura_media`         decimal(6, 2)             DEFAULT NULL COMMENT 'graus C - media diaria',
    `temperatura_min`           decimal(6, 2)             DEFAULT NULL COMMENT 'graus C - minimo horario do dia',
    `temperatura_max`           decimal(6, 2)             DEFAULT NULL COMMENT 'graus C - maximo horario do dia',
    `temperatura_horas_validas` tinyint unsigned NOT NULL DEFAULT 0 COMMENT 'Horas com valor nao nulo (0-24)',

    -- ---------------------------------------------------------- qualidade
    `valido`                    tinyint(1)       NOT NULL DEFAULT 0 COMMENT '1 se as 3 variaveis tem >= 18 horas validas - 75 por cento',

    -- ---------------------------------------------------------- auditoria
    `data_criacao`              timestamp                 DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `gestantes_exposicao_diaria_gestante_data_uindex` (`id_gestante`, `data`),
    KEY `gestantes_exposicao_diaria_data_index` (`data`),
    KEY `gestantes_exposicao_diaria_gestante_dia_index` (`id_gestante`, `dia_relativo`),
    KEY `gestantes_exposicao_diaria_valido_index` (`valido`),
    CONSTRAINT `gestantes_exposicao_diaria_gestantes_uruguaiana_id_fk`
        FOREIGN KEY (`id_gestante`) REFERENCES `gestantes_uruguaiana` (`id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci
    COMMENT = 'Exposicao ambiental diaria (PM10, PM2.5, temperatura) nos 9 meses anteriores a coleta';


-- -----------------------------------------------------------------------------
-- Carga (exemplo de UPSERT idempotente - Etapa 7, em lotes de 5.000)
-- -----------------------------------------------------------------------------
-- INSERT INTO gestantes_exposicao_diaria
--     (id_gestante, grupo, id_externo, data, dia_relativo, mes_relativo,
--      pm10_media, pm10_min, pm10_max, pm10_horas_validas,
--      pm2_5_media, pm2_5_min, pm2_5_max, pm2_5_horas_validas,
--      temperatura_media, temperatura_min, temperatura_max, temperatura_horas_validas,
--      valido)
-- VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
-- ON DUPLICATE KEY UPDATE
--     dia_relativo = VALUES(dia_relativo),
--     mes_relativo = VALUES(mes_relativo),
--     pm10_media = VALUES(pm10_media),
--     pm10_min = VALUES(pm10_min),
--     pm10_max = VALUES(pm10_max),
--     pm10_horas_validas = VALUES(pm10_horas_validas),
--     pm2_5_media = VALUES(pm2_5_media),
--     pm2_5_min = VALUES(pm2_5_min),
--     pm2_5_max = VALUES(pm2_5_max),
--     pm2_5_horas_validas = VALUES(pm2_5_horas_validas),
--     temperatura_media = VALUES(temperatura_media),
--     temperatura_min = VALUES(temperatura_min),
--     temperatura_max = VALUES(temperatura_max),
--     temperatura_horas_validas = VALUES(temperatura_horas_validas),
--     valido = VALUES(valido);


-- -----------------------------------------------------------------------------
-- Consultas de validacao (criterios de aceite do planejamento)
-- -----------------------------------------------------------------------------
-- SELECT COUNT(*) FROM gestantes_exposicao_diaria;                            -- 194.169
-- SELECT COUNT(DISTINCT id_gestante) FROM gestantes_exposicao_diaria;         -- 708
-- SELECT MIN(dia_relativo), MAX(dia_relativo) FROM gestantes_exposicao_diaria;-- -276 .. 0
-- SELECT MIN(pm10_horas_validas), MAX(pm10_horas_validas) FROM gestantes_exposicao_diaria; -- 0 .. 24
-- SELECT valido, COUNT(*) FROM gestantes_exposicao_diaria GROUP BY valido;


-- -----------------------------------------------------------------------------
-- Views auxiliares sugeridas para analise
-- -----------------------------------------------------------------------------
-- Resumo por gestante (media do periodo, contagem de dias validos):
--
-- CREATE OR REPLACE VIEW vw_gestantes_exposicao_resumo AS
-- SELECT g.id,
--        g.grupo,
--        g.id_externo,
--        g.data_referencia,
--        COUNT(e.id)                                   AS dias_gravados,
--        SUM(e.valido)                                 AS dias_validos,
--        AVG(NULLIF(e.valido, 0) * e.pm10_media)       AS pm10_media_periodo,
--        AVG(NULLIF(e.valido, 0) * e.pm2_5_media)      AS pm2_5_media_periodo,
--        AVG(NULLIF(e.valido, 0) * e.temperatura_media) AS temperatura_media_periodo
--   FROM gestantes_uruguaiana g
--   LEFT JOIN gestantes_exposicao_diaria e ON e.id_gestante = g.id
--  GROUP BY g.id, g.grupo, g.id_externo, g.data_referencia;
--
--
-- Exposicao por mes relativo da janela (mes 9 = mais proximo da coleta):
--
-- CREATE OR REPLACE VIEW vw_gestantes_exposicao_mensal AS
-- SELECT id_gestante, grupo, id_externo, mes_relativo,
--        AVG(NULLIF(valido, 0) * pm10_media)        AS pm10_media,
--        AVG(NULLIF(valido, 0) * pm2_5_media)       AS pm2_5_media,
--        AVG(NULLIF(valido, 0) * temperatura_media) AS temperatura_media,
--        SUM(valido)                                AS dias_validos
--   FROM gestantes_exposicao_diaria
--  GROUP BY id_gestante, grupo, id_externo, mes_relativo;
