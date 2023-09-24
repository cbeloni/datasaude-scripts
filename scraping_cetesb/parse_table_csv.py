from bs4 import BeautifulSoup
import pandas as pd
from config.log_config import Log
from core.poluente_repository import get_poluente_scrap_pendentes, update_poluente_scrap_finish

_log = Log("parse_table_csv")

def html_to_csv(html_file, csv_file):
    with open(html_file, 'r') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    tables = soup.find_all('table')

    if len(tables) < 2:
        print('O arquivo HTML não contém duas tabelas.')
        return

    table = tables[1]

    first_row = table.find('tr')
    first_row.decompose()

    header = table.find("tr")
    list_header = []
    data = []

    for items in header:
        try:
            texto = items.get_text()
            if is_valid(texto):
                list_header.append(texto)
        except Exception as ex:
            _log.error(f"erro ao parsear header {ex}")
            continue

    HTML_data = table.find_all("tr")[1:]

    for element in HTML_data:
        sub_data = []
        for sub_element in element:
            try:
                texto = sub_element.get_text()
                if is_valid(texto):
                    sub_data.append(sanitizar_body(texto))
            except Exception as ex:
                _log.error(f"erro ao parsear body {ex}")
                continue
        data.append(sub_data)

    dataFrame = pd.DataFrame(data=data, columns=list_header)

    dataFrame.to_csv(csv_file)

    print(f'A segunda tabela HTML foi convertida com sucesso para {csv_file}.')

def is_valid(value):
    if value == '\n':
        return False
    elif value == '':
        return False
    else:
        return True

def sanitizar_body(value):
    return value.replace('\n', '').replace('\t', '')

def parse_table_to_csv():
    for i in get_poluente_scrap_pendentes():
        id, i_rede, data_inicial, data_final, i_tipo_dado, estacao, parametro, created_at, updated_at, file = i
        _log.info(f"Gerando: files/{ file }")
        html_file = f"files/{ file }"
        csv_file = f"files/{ file }.csv"
        try:
            html_to_csv(html_file, csv_file)
            update_poluente_scrap_finish(id, 'PARSED', file)
        except Exception as ex:
            _log.error(f"Error on parse: {ex}")

if __name__ == '__main__':
    # html_file = 'files/01012022_01012023_63_63.html'
    # csv_file = 'files/01012022_01012023_63_63.csv'
    # html_to_csv(html_file, csv_file)
    parse_table_to_csv()
