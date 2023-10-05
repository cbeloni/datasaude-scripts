import sqlite3
import pandas as pd
from config.log_config import Log

_log = Log('poluente_repository')

_query_gerar_csv = """
    SELECT id, data_coleta, poluente, vmin, vmax
    FROM poluente_plot
    WHERE status = 'gerar_csv';
"""

def criar_conexao_sqlite():
    return sqlite3.connect('/home/caue/Documentos/pensi_projeto/POLUENTES_PACIENTES.sqlite')

def update_poluente_plot(cursor, id, arquivo, status):
    _log.info(f"Atualizando poluente_plot id: {id}")
    query = "UPDATE poluente_plot SET arquivo_csv = ?, status = ?, data_atual=DATE('now') WHERE id = ?"
    cursor.execute(query, (arquivo, status, id))

def query_csv():
    return """
    select p.nome_estacao, 
     codigo_estacao, 
     TRIM(SUBSTR(nome_parametro, 1, INSTR(nome_parametro, ' ') - 1)) poluente,  
     REPLACE(SUBSTR(data, 1, INSTR(data, ' ') - 1), '-', '') data, 
     ROUND(avg(media_horaria)) as "media_diaria", 
     e.x, 
     e.y
    from poluente_historico p, estacao e
    where p.nome_estacao = e.nome
    and TRIM(SUBSTR(nome_parametro, 1, INSTR(nome_parametro, ' ') - 1)) in (?)
    and REPLACE(SUBSTR(data, 1, INSTR(data, ' ') - 1), '-', '') = ?
    group by p.nome_estacao, codigo_estacao, unidade_medida,  TRIM(SUBSTR(nome_parametro, 1, INSTR(nome_parametro, ' ') - 1)), data, e.x, e.y;
    """


def gerar_csv(arquivo, cursor):
    df = pd.DataFrame(cursor.fetchall(), columns=[i[0] for i in cursor.description])
    df.to_csv(arquivo, index=False)


if __name__ == '__main__':
    conexao = criar_conexao_sqlite()
    cursor = conexao.cursor()

    cursor.execute(_query_gerar_csv)
    results = cursor.fetchall()

    for row in results:
        id, data, poluente, vmin, vmax = row
        path = 'csv/'
        arquivo = f'{path}AMOSTRA_{poluente}_{data}.csv'

        cursor.execute(query_csv(), (poluente, data))
        gerar_csv(arquivo, cursor)

        update_poluente_plot(cursor, id, arquivo, 'gerar_geojson')
        conexao.commit()

    cursor.close()
    conexao.close()
