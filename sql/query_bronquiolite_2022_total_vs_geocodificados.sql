-- =============================================================================
-- BRONQUIOLITE 2022: TOTAL DE PACIENTES VS. PACIENTES GEOCODIFICADOS/VALIDADOS
-- =============================================================================
-- Critérios (conforme combinado):
--   * A tabela de coordenadas é `paciente_coordenadas`.
--   * O join correto é: pc.id_paciente = p.CD_ATENDIMENTO
--     (as queries antigas usavam pc.id_paciente = p.ID, que retorna 0 registros)
--   * `validado = 1` significa que o paciente é da Região Metropolitana de
--     São Paulo E está dentro do critério (escore) de acuracia esperado.
--   * "Geocodificado" aqui = validado = 1.
-- =============================================================================

SELECT
    COUNT(DISTINCT p.ID) AS total_pacientes_bronquiolite_2022,
    COUNT(DISTINCT CASE WHEN pc.tem_validado_1 = 1 THEN p.ID END) AS geocodificados_validados,
    COUNT(DISTINCT p.ID)
        - COUNT(DISTINCT CASE WHEN pc.tem_validado_1 = 1 THEN p.ID END) AS nao_geocodificados
FROM paciente p
LEFT JOIN (
    SELECT id_paciente,
           MAX(CASE WHEN validado = 1 THEN 1 ELSE 0 END) AS tem_validado_1
    FROM paciente_coordenadas
    GROUP BY id_paciente
) pc ON pc.id_paciente = p.CD_ATENDIMENTO
WHERE UPPER(TRIM(p.DS_CID)) IN (
      'BRONQUIOLITE AGUDA',
      'BRONQUIOLITE AGUDA DEVIDA A VIRUS SINCICIAL RESPIRATORIO',
      'BRONQUIOLITE AGUDA DEVIDA A OUTROS MICROORGANISMOS ESPECIFICADOS'
)
  AND p.DT_ATENDIMENTO BETWEEN '2022-01-01' AND '2022-12-31';
