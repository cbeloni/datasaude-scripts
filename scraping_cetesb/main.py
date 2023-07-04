from core.log_config import Log
from scraping_cetesb.api import CestebConsuilta

_log = Log("scrapping_cetesb")




if __name__ == '__main__':
    _log.info("Starting scrapping cetesb")
    cestebConsuilta = CestebConsuilta()
    cookie = cestebConsuilta.autenticacao()
    _log.info(f"autenticado: {cookie}")

    filtros = cestebConsuilta.filtrar()
    _log.info(f"realizado filtros com sucesso")

    cestebConsuilta.scrap()
    _log.info(f"Consulta realizada com sucesso!")

