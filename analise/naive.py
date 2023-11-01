from sklearn.naive_bayes import GaussianNB
import numpy as np
from dotenv import load_dotenv, dotenv_values
from core.database import criar_conexao
from config.log_config import Log

load_dotenv()
_config = dotenv_values("../.env")
_log = Log("naive")

def query_dados_treino():
    return """
    SELECT
    MP10.indice_interpolado AS MP10,
    NO.indice_interpolado AS NO,
    NO2.indice_interpolado AS NO2,
    O3.indice_interpolado AS O3,
    TEMP.indice_interpolado AS TEMP,
    UR.indice_interpolado AS UR,
    p.DS_CID,
    MP10.data AS data_poluente,
    p.DT_ATENDIMENTO,
    p.DS_LEITO,
    p.DT_ALTA
FROM paciente_interpolacao MP10
JOIN paciente_interpolacao NO ON MP10.id_coordenada = NO.id_coordenada
JOIN paciente_interpolacao NO2 ON MP10.id_coordenada = NO2.id_coordenada
JOIN paciente_interpolacao O3 ON MP10.id_coordenada = O3.id_coordenada
JOIN paciente_interpolacao TEMP ON MP10.id_coordenada = TEMP.id_coordenada
JOIN paciente_interpolacao UR ON MP10.id_coordenada = UR.id_coordenada
JOIN paciente_coordenadas PC ON MP10.id_coordenada = PC.id
JOIN paciente p on PC.id_paciente = p.ID
WHERE
    MP10.poluente = 'MP10'
    AND NO.poluente = 'NO'
    AND NO2.poluente = 'NO2'
    AND O3.poluente = 'O3'
    AND TEMP.poluente = 'TEMP'
    AND UR.poluente = 'UR'
    AND STR_TO_DATE(MP10.data, '%Y%m%d') BETWEEN STR_TO_DATE(%s, '%Y%m%d')  AND STR_TO_DATE(%s, '%Y%m%d')
order by MP10.id asc;
    """

def treinar_modelo(temperatura_treino, tempo_treino):
    model = GaussianNB()
    model.fit(temperatura_treino, tempo_treino)
    return model

def fazer_previsao(modelo, temperatura_previsao):
    previsao = modelo.predict(temperatura_previsao)
    return previsao

def salvar_csv(arquivo, linha):
    # Abra o arquivo de texto no modo de escrita e adicione a linha
    with open(arquivo, mode='a', newline='') as arquivo_txt:
        arquivo_txt.write(linha)

if __name__ == '__main__':
    _log.info("Criando conexão")
    conexao = criar_conexao(_config)
    _log.info(f"conectado: {conexao.is_connected()}")

    cursor = conexao.cursor()
    cursor.execute(query_dados_treino(), ("20220101", "20220630"))

    poluentes = []
    cid = []
    for resultado in cursor.fetchall():
        campos = [float(valor) if valor is not None else None for valor in resultado[0:6]]
        poluentes.append(campos)
        cid.append(resultado[6])

    # Treinar o modelo
    modelo = treinar_modelo(np.array(poluentes), np.array(cid))

    # Fazer previsões
    cursor.execute(query_dados_treino(), ("20220801", "20220830"))
    poluentes = []
    for resultado in cursor.fetchall():
        campos = [float(valor) if valor is not None else None for valor in resultado[0:6]]
        poluentes.append(campos)

    previsoes = fazer_previsao(modelo, np.array(poluentes))

    # Salvar resultado
    cursor.execute(query_dados_treino(), ("20220801", "20220830"))
    campos = [float(valor) if valor is not None else None for valor in resultado[0:6]]
    poluentes.append(campos)
    index = 0
    for row in cursor.fetchall():
        MP10, NO, NO2, O3, TEMP, UR, DS_CID, data_poluente, DT_ATENDIMENTO, DS_LEITO, DT_ALTA = row
        previsao = previsoes[index]
        dados_poluentes = [float(valor) if valor is not None else None for valor in resultado[0:6]]
        campos_concatenados = f"{MP10}|{NO}|{NO2}|{O3}|{TEMP}|{UR}|{data_poluente}|{DT_ATENDIMENTO}|{DS_LEITO}|{DT_ALTA}|{DS_CID}|{previsao}"
        print(campos_concatenados)
        salvar_csv('output.csv', campos_concatenados)
        index += 1
