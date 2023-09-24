from config.log_config import Log
from csv_to_sql.poluente_historico_csv_to_sql import run_csv_to_sql
from scraping_cetesb.api import CestebConsuilta
from scraping_cetesb.parse_table_csv import parse_table_to_csv
from scraping_cetesb.popula_poluente_scrap_table import PopulaPoluenteScrap
import time

_log = Log("scrapping_cetesb")

def main():
    _log.info("Starting scrapping cetesb")
    populaPoluenteScrap = PopulaPoluenteScrap()
    cestebConsuilta = CestebConsuilta()
    cookie = cestebConsuilta.autenticacao()

    resultados = populaPoluenteScrap.get_poluente_scrap_pendentes()

    for resultado in resultados:
        id, i_rede, data_inicial, data_final, i_tipo_dado, estacao, parametro, created_at, updated_at = resultado

        try:
            payload = {'irede': i_rede,
                       'dataInicialStr': data_inicial.strftime('%d/%m/%Y'),
                       'dataFinalStr': data_final.strftime('%d/%m/%Y'),
                       'iTipoDado': i_tipo_dado,
                       'estacaoVO.nestcaMonto': estacao,
                       'parametroVO.nparmt': parametro}
            filtros = cestebConsuilta.filtrar(payload)
            nome_arquivo = f"{data_inicial.strftime('%d%m%Y')}_{data_final.strftime('%d%m%Y')}_{estacao}_{parametro}.html"
            cestebConsuilta.scrap(nome_arquivo)
            _log.info(f"Consulta realizada com sucesso!")

            populaPoluenteScrap.update_poluente_scrap_finish(id, 'FINALIZADO', nome_arquivo)

        except Exception as e:
            _log.error(f"Error id: {id} - tracer: {e}")
            message_error = f"error: {e.args[0]}"[:50]
            populaPoluenteScrap.update_poluente_scrap_finish(id, message_error, "")

if __name__ == '__main__':

    while True:
        try:
            main()
            parse_table_to_csv()
            run_csv_to_sql()
        except Exception as e:
            _log.error(f"Ocorreu um erro: {str(e)}")

        _log.error(f"Aguardando...")
        # Aguarda 1 minuto
        time.sleep(1 * 60)


