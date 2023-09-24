 select p.nome_estacao, codigo_estacao, unidade_medida,  TRIM(SUBSTR(nome_parametro, 1, INSTR(nome_parametro, ' ') - 1)) poluente, data, ROUND(avg(media_horaria)) as "media_diaria", e.x, e.y
from poluente_historico p, estacao e
where p.nome_estacao = e.nome
and TRIM(SUBSTR(nome_parametro, 1, INSTR(nome_parametro, ' ') - 1)) in ('MP10')
and data = '2022-01-01 00:00:00.000000'
group by p.nome_estacao, codigo_estacao, unidade_medida,  TRIM(SUBSTR(nome_parametro, 1, INSTR(nome_parametro, ' ') - 1)), data, e.x, e.y;