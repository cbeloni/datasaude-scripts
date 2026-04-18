import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.poluente_repository import get_poluente_scrap_pendentes
from poluente_historico_csv_to_sql import csv_to_sql
from config.log_config import Log

_log = Log("main_poluente_historico_csv_to_sql")

path = "files"

if __name__ == '__main__':
    # csv_to_sql()

    resultados = get_poluente_scrap_pendentes(None, 'PARSED')
    for resultado in resultados:
        id, i_rede, data_inicial, data_final, i_tipo_dado, estacao, parametro, created_at, updated_at, file = resultado

        path_file = f"{path}/{file}.csv"
        _log.info(f'salvando: {path_file}')
        try:
            csv_to_sql(path_file)
        except Exception as ex:
            _log.error(f'{path_file} - Error: {ex}')

