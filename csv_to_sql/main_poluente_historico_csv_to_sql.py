from poluente_historico_csv_to_sql import csv_to_sql
from core.log_config import Log

_log = Log("main_poluente_historico_csv_to_sql")

path = "/home/caue/Documentos/FILES_CETESB/2022_csv"

if __name__ == '__main__':
    file = '01012022_01012023_63_63.html.csv'
    path_file = f"{path}/{file}"
    # csv_to_sql()
    _log.info(f'convertendo: {path_file}')

