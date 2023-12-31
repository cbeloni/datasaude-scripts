import sqlite3
import pandas as pd
from config.log_config import Log
from interpolacao.interpolate import interpolar, gera_png, gera_transparencia

_log = Log('poluente_repository')


def criar_conexao_sqlite():
    return sqlite3.connect('/home/caue/Documentos/pensi_projeto/POLUENTES_PACIENTES.sqlite')


def update_poluente_plot(cursor, id, arquivo_csv, arquivo_geojson, arquivo_escala_fixa_png, arquivo_escala_movel_png,
                         status):
    _log.info(f"Atualizando poluente_plot id: {id}")
    query = """UPDATE poluente_plot 
                  SET arquivo_csv = ?, arquivo_geojson = ?, arquivo_escala_fixa_png = ?, 
                      arquivo_escala_movel_png = ? , status = ?, data_atual=DATE('now') 
                WHERE id = ?"""
    cursor.execute(query, (arquivo_csv, arquivo_geojson, arquivo_escala_fixa_png, arquivo_escala_movel_png, status, id))


def query_poluente_plot(status):
    return f"""
                SELECT id, data_coleta, poluente, vmin, vmax, arquivo_csv, arquivo_geojson, arquivo_escala_fixa_png, arquivo_escala_movel_png
                FROM poluente_plot
                WHERE status = '{status}';
            """


def query_poluente_historico():
    return """
    select  "'" || p.nome_estacao || "'" as nome_estacao, 
     codigo_estacao, 
     TRIM(SUBSTR(nome_parametro, 1, INSTR(nome_parametro, ' ') - 1)) poluente,  
     REPLACE(SUBSTR(data, 1, INSTR(data, ' ') - 1), '-', '') as data,  
     ROUND(avg(media_horaria)) as "media_diaria", 
     e.x as x, 
     e.y as y
    from poluente_historico p, estacao e
    where p.nome_estacao = e.nome
    and TRIM(SUBSTR(nome_parametro, 1, INSTR(nome_parametro, ' ') - 1)) in (?)
    and REPLACE(SUBSTR(data, 1, INSTR(data, ' ') - 1), '-', '') = ?
    group by p.nome_estacao, codigo_estacao, unidade_medida,  TRIM(SUBSTR(nome_parametro, 1, INSTR(nome_parametro, ' ') - 1)), data, e.x, e.y;
    """


def gerar_csv(arquivo, cursor):
    df = pd.DataFrame(cursor.fetchall(), columns=[i[0] for i in cursor.description])
    df.to_csv(arquivo, index=False)


def interpolar_massa(arquivo, campo, vmin, vmax, escala):
    df = interpolar(f'csv/AMOSTRA_{arquivo}.csv',
                    campo,
                    'contorno/hexgrid_v2.shp',
                    vmin,
                    vmax)

    geo_json_output_path = f"geojson/{arquivo}.geojson"
    df.to_file(geo_json_output_path, driver="GeoJSON")

    output_png_path = f'png_{escala}/{arquivo}_{vmin}_{vmax}_{escala}.png'
    gera_png(geo_json_output_path, output_png_path, campo, df, vmin, vmax)

    output_filename_transparente = f'png_{escala}/{arquivo}_{vmin}_{vmax}_{escala}.png'
    gera_transparencia(output_filename_transparente)

    return geo_json_output_path, output_filename_transparente


if __name__ == '__main__':
    conexao = criar_conexao_sqlite()
    cursor = conexao.cursor()

    query_gerar_csv = query_poluente_plot('gerar_csv')
    cursor.execute(query_gerar_csv)
    results = cursor.fetchall()
    for row in results:
        id, data, poluente, vmin, vmax, arquivo_csv, arquivo_geojson, arquivo_escala_fixa_png, arquivo_escala_movel_png = row
        path = 'csv/'
        arquivo = f'{path}AMOSTRA_{poluente}_{data}.csv'

        cursor.execute(query_poluente_historico(), (poluente, data))
        gerar_csv(arquivo, cursor)

        update_poluente_plot(cursor, id, arquivo, arquivo_geojson, arquivo_escala_fixa_png, arquivo_escala_movel_png,
                             'gerar_geojson')
        conexao.commit()

    query_geojson = query_poluente_plot('gerar_geojson')
    cursor.execute(query_geojson)
    results = cursor.fetchall()
    for row in results:
        id, data, poluente, vmin, vmax, arquivo_csv, arquivo_geojson, arquivo_escala_fixa_png, arquivo_escala_movel_png = row
        path = 'geojson/'
        arquivo = f'{poluente}_{data}'

        if arquivo_geojson != '':
            _log.info(f"Substituindo arquivo {arquivo_geojson}")
        if arquivo_escala_movel_png != '':
            _log.info(f"Substituindo arquivo {arquivo_escala_movel_png}")

        df = pd.read_csv(arquivo_csv)
        vmin_movel = df["media_diaria"].min()
        vmax_movel = df["media_diaria"].max()

        arquivo_geojson, arquivo_escala_movel_png = interpolar_massa(arquivo, 'media_diaria', vmin_movel, vmax_movel, 'movel')

        arquivo_geojson_fixo, arquivo_escala_fixa_png = interpolar_massa(arquivo, 'media_diaria', vmin, vmax, 'fixa')

        update_poluente_plot(cursor, id, arquivo_csv, arquivo_geojson,
                             arquivo_escala_fixa_png, arquivo_escala_movel_png, 'finalizado')
        conexao.commit()

    cursor.close()
    conexao.close()
