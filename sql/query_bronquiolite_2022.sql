SELECT
    p.CD_ATENDIMENTO AS Atendimento,
    p.DS_CID,
    pc.x,
    pc.y,
    pc.acuracia,
    pc.provider,
    MP10.indice_interpolado AS MP10,
    NO.indice_interpolado AS NO,
    NO2.indice_interpolado AS NO2,
    O3.indice_interpolado AS O3,
    TEMP.indice_interpolado AS TEMP,
    UR.indice_interpolado AS UR,
    CASE
        WHEN DT_ATENDIMENTO BETWEEN '2022-03-20' AND '2022-06-20' THEN 1
        ELSE 0
    END AS outono,
    CASE
        WHEN DT_ATENDIMENTO BETWEEN '2022-06-21' AND '2022-09-22' THEN 1
        ELSE 0
    END AS inverno,
    CASE
        WHEN DT_ATENDIMENTO BETWEEN '2022-09-23' AND '2022-12-20' THEN 1
        ELSE 0
    END AS primavera,
    CASE
        WHEN DT_ATENDIMENTO BETWEEN '2022-12-21' AND '2022-12-31' THEN 1
        WHEN DT_ATENDIMENTO BETWEEN '2022-01-01' AND '2022-03-19' THEN 1
        ELSE 0
    END AS verao
FROM paciente_interpolacao MP10
JOIN paciente_interpolacao NO
    ON MP10.id_coordenada = NO.id_coordenada
JOIN paciente_interpolacao NO2
    ON MP10.id_coordenada = NO2.id_coordenada
JOIN paciente_interpolacao O3
    ON MP10.id_coordenada = O3.id_coordenada
JOIN paciente_interpolacao TEMP
    ON MP10.id_coordenada = TEMP.id_coordenada
JOIN paciente_interpolacao UR
    ON MP10.id_coordenada = UR.id_coordenada
JOIN paciente_coordenadas pc
    ON MP10.id_coordenada = pc.id
JOIN paciente p
    ON pc.id_paciente = p.ID
WHERE MP10.poluente = 'MP10'
  AND NO.poluente = 'NO'
  AND NO2.poluente = 'NO2'
  AND O3.poluente = 'O3'
  AND TEMP.poluente = 'TEMP'
  AND UR.poluente = 'UR'
  AND UPPER(TRIM(p.DS_CID)) IN (
      'BRONQUIOLITE AGUDA',
      'BRONQUIOLITE AGUDA DEVIDA A VIRUS SINCICIAL RESPIRATORIO',
      'BRONQUIOLITE AGUDA DEVIDA A OUTROS MICROORGANISMOS ESPECIFICADOS'
  )
  AND STR_TO_DATE(MP10.data, '%Y%m%d')
      BETWEEN STR_TO_DATE('20220101', '%Y%m%d')
          AND STR_TO_DATE('20221231', '%Y%m%d')
ORDER BY p.CD_ATENDIMENTO, MP10.id ASC;
