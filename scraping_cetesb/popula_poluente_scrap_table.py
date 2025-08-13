from poluentes_const import estacoes_grande_sp, estacoes, poluentes, poluentes_analisados
from core.database import criar_conexao
from config.log_config import Log
from datetime import datetime

_log = Log("popula_poluente_scrap_table")

from dotenv import load_dotenv, dotenv_values
load_dotenv()
_config = dotenv_values("../.env")

class PopulaPoluenteScrap:
    _dados = []

    def __init__(self,ano_incial = 2018):
        self._ano_inicial = ano_incial

    def gerar(self):
        for estacao_grande_sp in estacoes_grande_sp:
            for p in poluentes_analisados:
                linha = {'i_rede': 'A',
                         'data_inicial': f'{self._ano_inicial}/01/01',
                         'data_final': f'{self._ano_inicial + 1}/01/01',
                         'i_tipo_dado': 'P',
                         'estacao':  estacoes[estacao_grande_sp],
                         'parametro': poluentes[p]}
                self._dados.append(linha)

        return self._dados

    def grava(self, registro):
        _log.info("Criando conexão")
        conexao = criar_conexao(_config)
        _log.info(f"conectado: {conexao.is_connected()}")

        # Criar o cursor para executar as consultas SQL
        cursor = conexao.cursor()

        sql = """
            INSERT INTO datasaude.poluente_scrap (i_rede, data_inicial, data_final, i_tipo_dado, estacao, parametro, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        valores = (registro['i_rede'], registro['data_inicial'], registro['data_final'],
                   registro['i_tipo_dado'], registro['estacao'], registro['parametro'],
                   data_atual, data_atual)

        try:
            cursor.execute(sql, valores)
            conexao.commit()
            _log.info(f"{cursor.rowcount} linhas inseridas.")
        except Exception as e:
            _log.error(f"Erro ao executar a consulta: {e}")
        finally:
            cursor.close()
            conexao.close()
    def update_poluente_scrap_finish(self, id, message, file) -> bool:
        _log.info(f"finalizando processamento id: {id}")
        _conexao = criar_conexao(_config)
        cursor = _conexao.cursor()
        query = "UPDATE poluente_scrap SET file = %s, status = %s, updated_at=now() WHERE id = %s"
        cursor.execute(query, (file, message, id))
        _conexao.commit()
        cursor.close()
        _conexao.close()

    def get_poluente_scrap_pendentes(self) -> list:
        _conexao = criar_conexao(_config)
        _log.info(f"conectado: {_conexao.is_connected()}")
        cursor = _conexao.cursor()
        query = """
            SELECT id, i_rede, data_inicial, data_final, i_tipo_dado, estacao, parametro, created_at, updated_at
            FROM poluente_scrap 
            WHERE status is null
        """
        cursor.execute(query)

        resultados = cursor.fetchall()

        cursor.close()
        _conexao.close()
        return resultados


if __name__ == '__main__':
    from dotenv import load_dotenv, dotenv_values
    load_dotenv()
    _config = dotenv_values("../.env")

    ano_inicial=2018
    populaPoluentes = PopulaPoluenteScrap(ano_inicial)
    dados = populaPoluentes.gerar()
    for d in dados:
        populaPoluentes.grava(d)
