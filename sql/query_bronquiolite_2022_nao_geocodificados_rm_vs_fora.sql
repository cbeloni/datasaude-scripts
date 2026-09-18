-- =============================================================================
-- BRONQUIOLITE 2022: SEPARAÇÃO DOS NÃO GEOCODIFICADOS
-- =============================================================================
-- Dos pacientes que NÃO foram geocodificados (validado != 1), separar entre:
--   * Na Região Metropolitana mas abaixo do escore de corte
--     -> county = 'Região Metropolitana de São Paulo' e validado != 1
--   * Fora da Região Metropolitana
--     -> validado = -1 (Localização fora da grande SP) ou
--        county != 'Região Metropolitana de São Paulo' ou sem coordenada
-- =============================================================================

SELECT situacao, COUNT(*) AS total_pacientes
FROM (
    SELECT
        p.ID,
        CASE
            WHEN MAX(CASE WHEN pc.county = 'Região Metropolitana de São Paulo' THEN 1 ELSE 0 END) = 1
                THEN 'na_RM_mas_abaixo_do_escore'
            WHEN MAX(CASE WHEN pc.validado = -1 THEN 1 ELSE 0 END) = 1
                THEN 'fora_da_RM'
            WHEN MAX(CASE WHEN pc.id IS NOT NULL THEN 1 ELSE 0 END) = 1
                THEN 'fora_da_RM_com_coordenada'
            ELSE 'sem_coordenada'
        END AS situacao
    FROM paciente p
    LEFT JOIN paciente_coordenadas pc ON pc.id_paciente = p.CD_ATENDIMENTO
    WHERE UPPER(TRIM(p.DS_CID)) IN (
          'BRONQUIOLITE AGUDA',
          'BRONQUIOLITE AGUDA DEVIDA A VIRUS SINCICIAL RESPIRATORIO',
          'BRONQUIOLITE AGUDA DEVIDA A OUTROS MICROORGANISMOS ESPECIFICADOS'
    )
      AND p.DT_ATENDIMENTO BETWEEN '2022-01-01' AND '2022-12-31'
    GROUP BY p.ID
    HAVING MAX(CASE WHEN pc.validado = 1 THEN 1 ELSE 0 END) = 0
) sub
GROUP BY situacao
ORDER BY situacao;
