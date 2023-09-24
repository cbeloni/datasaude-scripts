 select p.nome_estacao, codigo_estacao, unidade_medida,  TRIM(SUBSTR(nome_parametro, 1, INSTR(nome_parametro, ' ') - 1)), data, ROUND(avg(media_horaria)) as "media_diaria", e.x, e.y
from poluente_historico p, estacao e
where p.nome_estacao = e.nome
and TRIM(SUBSTR(nome_parametro, 1, INSTR(nome_parametro, ' ') - 1)) in ('MP10','O3','TEMP','UR','NO','NO2')
group by p.nome_estacao, codigo_estacao, unidade_medida,  TRIM(SUBSTR(nome_parametro, 1, INSTR(nome_parametro, ' ') - 1)), data, e.x, e.y;