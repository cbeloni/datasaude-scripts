-- =============================================================================
-- BRONQUIOLITE 2022: QUANTIDADE POR REGIÃO (COUNTY)
-- =============================================================================
-- Baseado em: query_bronquiolite_2022_quantidade_sem_join copy.sql
-- Adicionado: paciente_coordenadas (join correto: pc.id_paciente = p.CD_ATENDIMENTO)
-- Agrupado por county, destacando 'Região Metropolitana de São Paulo'
-- =============================================================================

SELECT
    p.DS_CID,
    CASE
        WHEN pc.county = 'Região Metropolitana de São Paulo' THEN 'regiao_metropolitana_sp'
        WHEN pc.county IS NULL OR pc.county = '' THEN 'sem_county'
        ELSE 'fora_rmsp'
    END AS situacao_regiao,
    pc.county,
    COUNT(DISTINCT p.ID) AS total_pacientes
FROM paciente p
LEFT JOIN paciente_coordenadas pc ON pc.id_paciente = p.CD_ATENDIMENTO
WHERE UPPER(TRIM(p.DS_CID)) IN (
    'BRONQUIOLITE AGUDA',
    'BRONQUIOLITE AGUDA DEVIDA A VIRUS SINCICIAL RESPIRATORIO',
    'BRONQUIOLITE AGUDA DEVIDA A OUTROS MICROORGANISMOS ESPECIFICADOS'
)
  AND p.DT_ATENDIMENTO BETWEEN '2022-01-01' AND '2022-12-31'
GROUP BY p.DS_CID, situacao_regiao, pc.county
ORDER BY p.DS_CID, situacao_regiao, pc.county;
