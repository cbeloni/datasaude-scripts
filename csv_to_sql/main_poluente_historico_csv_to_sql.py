from core.poluente_repository import get_poluente_scrap_pendentes
from poluente_historico_csv_to_sql import csv_to_sql
from core.log_config import Log

_log = Log("main_poluente_historico_csv_to_sql")

path = "/home/caue/Documentos/FILES_CETESB/2022_csv"

if __name__ == '__main__':
    # csv_to_sql()

    resultados = get_poluente_scrap_pendentes('2022-01-01 00:00:00', 'PARSED')
    for resultado in resultados:
        id, i_rede, data_inicial, data_final, i_tipo_dado, estacao, parametro, created_at, updated_at, file = resultado

        path_file = f"{path}/{file}.csv"
        _log.info(f'salvando: {path_file}')
        try:
            csv_to_sql(path_file)
        except Exception as ex:
            _log.error(f'{path_file} - Error: {ex}')

