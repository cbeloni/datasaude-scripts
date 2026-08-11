SELECT
    pc.acuracia,
    pc.provider,
    COUNT(1) AS total_registros
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
GROUP BY
    pc.acuracia,
    pc.provider
ORDER BY
    pc.acuracia,
    pc.provider;
