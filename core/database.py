from dotenv import load_dotenv, dotenv_values
import mysql.connector
from core.log_config import Log

_log = Log("database")

load_dotenv()
_config = dotenv_values(".env")


# Função para criar a conexão com o banco de dados
def criar_conexao():
    _log.info(f"Abrindo conexão para: {_config}")
    return mysql.connector.connect(
        host=_config['host'],
        user=_config['user'],
        password=_config['password'],
        database=_config['database'],
        ssl_ca=_config['ssl_ca'] if 'ssl_ca' in _config else None
    )


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
