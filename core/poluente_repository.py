from dotenv import load_dotenv, dotenv_values

from core.database import criar_conexao
from core.log_config import Log

load_dotenv()
_config = dotenv_values("../.env")
_log = Log('poluente_repository')

def get_poluente_scrap_pendentes(data_inicial: str = '2022-01-01 00:00:00', status: str = 'FINALIZADO') -> list:
    _conexao = criar_conexao(_config)
    _log.info(f"conectado: {_conexao.is_connected()}")
    cursor = _conexao.cursor()
    query = """
        SELECT id, i_rede, data_inicial, data_final, i_tipo_dado, estacao, parametro, created_at, updated_at, file
        FROM poluente_scrap 
        WHERE data_inicial = %s and status = %s
    """
    cursor.execute(query, (data_inicial, status))

    resultados = cursor.fetchall()

    cursor.close()
    _conexao.close()
    return resultados

def update_poluente_scrap(id, message) -> bool:
    _log.info(f"Atualizando processamento id: {id}")
    _conexao = criar_conexao(_config)
    cursor = _conexao.cursor()
    query = "UPDATE poluente_scrap SET file = %s, status = %s, updated_at=now() WHERE id = %s"
    cursor.execute(query, (message, id))
    _conexao.commit()
    cursor.close()
    _conexao.close()

def update_poluente_scrap_finish(id, message, file) -> bool:
    _log.info(f"finalizando processamento id: {id}")
    _conexao = criar_conexao(_config)
    cursor = _conexao.cursor()
    query = "UPDATE poluente_scrap SET file = %s, status = %s, updated_at=now() WHERE id = %s"
    cursor.execute(query, (file, message, id))
    _conexao.commit()
    cursor.close()
    _conexao.close()

if __name__ == '__main__':
    resultados = get_poluente_scrap_pendentes('2022-01-01 00:00:00', 'PARSED')
    for resultado in resultados:
        id, i_rede, data_inicial, data_final, i_tipo_dado, estacao, parametro, created_at, updated_at, file = resultado
        _log.info(f'estacao: {estacao} - file: {file}')

