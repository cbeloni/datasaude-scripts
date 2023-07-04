from core.log_config import Log
from core.database import criar_conexao



_log = Log("scrapping_cetesb")

if __name__ == '__main__':
    _log.info("Starting scrapping cetesb")
    print('main scrapping')
    # conexao = criar_conexao()
    # _log.info(f"conectado: {conexao.is_connected()}")