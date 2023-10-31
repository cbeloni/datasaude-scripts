from dotenv import load_dotenv, dotenv_values
from core.database import criar_conexao
from config.log_config import Log
import requests

load_dotenv()
_config = dotenv_values("../.env")
_log = Log("gestor_arquivos")
_PATH_VOLUME = _config['PATH_VOLUME']
def enviar(arquivo: str):
    # URL da API
    url = 'http://datasaude-api.beloni.dev.br/api/v1/poluentes/file-upload'

    # Dados do formulário
    data = {
        'bucket_name': 'maps-pub',
        'object_key': arquivo,
        'content_type': 'image/png',
    }

    # Nome do arquivo a ser enviado
    files = {'arquivo': (arquivo, open(f'{_PATH_VOLUME}{arquivo}', 'rb'), 'image/png')}

    # Realize a requisição POST
    response = requests.post(url, data=data, files=files, headers={'accept': 'application/json'})

    # Verifique a resposta
    if response.status_code == 201:
        print(f"Arquivo {arquivo} enviado com sucesso!")
    else:
        print(f"Falha ao enviar o arquivo {arquivo}. Código de status:", response.status_code)
        print("Resposta do servidor:", response.text)

def query_poluente_plot():
    return """
        select arquivo_escala_fixa_png, arquivo_escala_movel_png 
         from poluente_plot;
    """


if __name__ == '__main__':
    _log.info("Criando conexão")
    conexao = criar_conexao(_config)
    _log.info(f"conectado: {conexao.is_connected()}")

    cursor = conexao.cursor()
    cursor.execute(query_poluente_plot())

    for row in cursor.fetchall():
        arquivo_escala_fixa_png, arquivo_escala_movel_png = row
        enviar(arquivo_escala_fixa_png)

        enviar(arquivo_escala_movel_png)
