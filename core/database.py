import time

from dotenv import load_dotenv, dotenv_values
import mysql.connector

from config.log_config import Log
from sqlalchemy import create_engine

_log = Log("database")

load_dotenv()
_config = dotenv_values(".env")


# Função para criar a conexão com o banco de dados
def criar_conexao(config=None):
    global _config

    if not _config and not config:
        raise ValueError("É necessário fornecer um valor para o parâmetro 'config'")

    if not _config:
        _config = config

    tentativa = 1

    while True:
        try:
            _log.info(f"Tentativa {tentativa} de conectar ao banco")
            print(f"Tentativa {tentativa} de conectar ao banco")
            _log.info(f"Abrindo conexao para: {_config}")

            conexao = mysql.connector.connect(
                host=_config['host'],
                user=_config['user'],
                password=_config['password'],
                database=_config['database'],
                ssl_ca=_config['ssl_ca'] if 'ssl_ca' in _config else None
            )
            _log.info("Conexao com o banco estabelecida")
            print("Conexao com o banco estabelecida")
            return conexao
        except mysql.connector.Error as error:
            _log.error(f"Falha na tentativa {tentativa} de conexao: {error}")
            print(f"Falha na tentativa {tentativa} de conexao: {error}")
            print("Aguardando 1 segundo para tentar novamente")
            time.sleep(1)
            tentativa += 1

def criar_engine_sqlalchemy(config=None):
    global _config

    if not _config and not config:
        raise ValueError("É necessário fornecer um valor para o parâmetro 'config'")

    if not _config:
        _config = config

    user = _config['user']
    password = _config['password']
    host = _config['host']
    database = _config['database']

    # Monta a string de conexão para o MySQL
    connection_string = (
        f"mysql+mysqlconnector://{user}:{password}@{host}/{database}"
    )

    # Adiciona ssl_ca se existir
    connect_args = {}
    if 'ssl_ca' in _config and _config['ssl_ca']:
        connect_args['ssl_ca'] = _config['ssl_ca']

    engine = create_engine(connection_string, connect_args=connect_args)
    return engine

if __name__ == '__main__':
    _log.info("Criando conexão")
    conexao = criar_conexao()
    _log.info(f"conectado: {conexao.is_connected()}")

    # Criar o cursor para executar as consultas SQL
    cursor = conexao.cursor()

    sql = """
        SELECT COUNT(1) 
          FROM poluente
         WHERE nome = %s
        """

    nome = 'S.André-Capuava',

    cursor.execute(sql, nome)

    record = cursor.fetchone()[0]

    _log.info(f'record: {record}')
