from datetime import datetime

import pandas as pd

from core import PoluenteHistorico
from core.database_sqlite import SessionSqlite, create_all
from core.log_config import Log

_log = Log("poluente_historico")

create_all()

def read_csv(arquivo: str):
    _log.info("Starting poluente historico")
    dados_csv = pd.read_csv(arquivo)

    sessionSqlite = SessionSqlite()

    for indice, linha in dados_csv.iterrows():
        _log.info(linha)
        tipo_rede = linha['Tipo de Rede '] if pd.notnull(linha['Tipo de Rede ']) else None
        tipo_monitoramento = linha['Tipo de Monitoramento '] if pd.notnull(linha['Tipo de Monitoramento ']) else None
        tipo = linha['Tipo '] if pd.notnull(linha['Tipo ']) else None
        data = linha['Data'] if pd.notnull(linha['Data']) else None
        hora = linha['Hora'] if pd.notnull(linha['Hora']) else None
        codigo_estacao = linha['Código Estação '] if pd.notnull(linha['Código Estação ']) else None
        nome_estacao = linha['Nome Estação '] if pd.notnull(linha['Nome Estação ']) else None
        nome_parametro = linha['Nome Parâmetro '] if pd.notnull(linha['Nome Parâmetro ']) else None
        unidade_medida = linha['Unidade de Medida '] if pd.notnull(linha['Unidade de Medida ']) else None
        media_horaria = linha['Média Horária '] if pd.notnull(linha['Média Horária ']) else None
        media_movel = linha['Média Móvel '] if pd.notnull(linha['Média Móvel ']) else None
        valido = linha['Válido'] if pd.notnull(linha['Válido']) else None
        dt_amostragem = linha['Dt. Amostragem'] if pd.notnull(linha['Dt. Amostragem']) else None
        dt_instalacao = linha['Dt. Instalação'] if pd.notnull(linha['Dt. Instalação']) else None
        dt_retirada = linha['Dt. Retirada '] if pd.notnull(linha['Dt. Retirada ']) else None
        concentracao = linha['Concentração'] if pd.notnull(linha['Concentração']) else None
        taxa = linha['Taxa'] if pd.notnull(linha['Taxa']) else None


        data_formatada = datetime.strptime(data, "%d/%m/%Y")

        registro = PoluenteHistorico(
            tipo_rede=tipo_rede,
            tipo_monitoramento=tipo_monitoramento,
            tipo=tipo,
            data=data_formatada,
            hora=hora,
            codigo_estacao=codigo_estacao,
            nome_estacao=nome_estacao,
            nome_parametro=nome_parametro,
            unidade_medida=unidade_medida,
            media_horaria=media_horaria,
            media_movel=media_movel,
            valido=valido,
            dt_amostragem=dt_amostragem,
            dt_instalacao=dt_instalacao,
            dt_retirada=dt_retirada,
            concentracao=concentracao,
            taxa=taxa
        )

        sessionSqlite.add(registro)
        sessionSqlite.commit()

    sessionSqlite.close()

if __name__ == '__main__':
    read_csv("FILES_CETESB/2022_csv/01012022_01012023_63_63.html.csv")