import sqlite3
from datetime import date, timedelta, datetime
from csv_to_sql.poluente_escala import escala


def criar_conexao_sqlite():
    return sqlite3.connect('/home/caue/Documentos/pensi_projeto/POLUENTES_PACIENTES.sqlite')

def popula_poluente_plot(cursor, data_coleta, poluente, vmin, vmax, arquivo_csv, arquivo_geojson, arquivo_escala_fixa_png, arquivo_escala_movel_png, data_atual, status):
    cursor.execute("SELECT id FROM poluente_plot WHERE data_coleta = ? AND poluente = ?", (data_coleta, poluente))
    id = cursor.fetchone()

    if id is None:
        cursor.execute("INSERT INTO poluente_plot (data_coleta, poluente, vmin, vmax, arquivo_csv, arquivo_geojson, arquivo_escala_fixa_png, arquivo_escala_movel_png, data_atual, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (data_coleta, poluente, vmin, vmax, arquivo_csv, arquivo_geojson, arquivo_escala_fixa_png, arquivo_escala_movel_png, data_atual, status))
    else:
        cursor.execute("UPDATE poluente_plot SET vmin = ?, vmax = ?, arquivo_csv = ?, arquivo_geojson = ?, arquivo_escala_fixa_png = ?, arquivo_escala_movel_png = ?, data_atual = ?, status = ? WHERE id = ?", (vmin, vmax, arquivo_csv, arquivo_geojson, arquivo_escala_fixa_png, arquivo_escala_movel_png, data_atual, status, id[0]))

    cursor.connection.commit()




def grava_csv(poluente, data):
    query = """
    select p.nome_estacao, 
     codigo_estacao, 
     unidade_medida,  
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

    cursor.execute(query, (poluente, data))

if __name__ == '__main__':

    data_inicial = date(2022, 1, 1)
    data_final = date(2022, 12, 31)

    conexao = criar_conexao_sqlite()
    cursor = conexao.cursor()

    escala_filtrada = [item for item in escala if item['plot']]
    for item in escala_filtrada:
        print(f"Poluente: {item['poluente']}, vmin: {item['vmin']}, vmax: {item['vmax']}")
        data_atual = data_inicial
        while data_atual <= data_final:
            print(data_atual.strftime('%Y%m%d'))
            popula_poluente_plot(cursor, data_atual.strftime('%Y%m%d'), item['poluente'], item['vmin'], item['vmax'], '','','','', datetime.now(), 'gerar_csv')
            data_atual += timedelta(days=1)


    conexao.close()