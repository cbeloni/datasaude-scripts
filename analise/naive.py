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
    p.DT_ALTA,
    CASE
        WHEN DS_LEITO IS NULL THEN 0
        ELSE 1
    END AS internacao,
    CASE
        when upper(DS_LEITO) like '%UTI%' THEN 'GRAVE'
        WHEN DS_LEITO IS NULL THEN 'LEVE'
        ELSE 'MODERADO'
    END AS gravidade,
    concat(ds_cid, CASE
        when upper(DS_LEITO) like '%UTI%' THEN '_GRAVE'
        WHEN DS_LEITO IS NULL THEN '_LEVE'
        ELSE '_MODERADO'
    END) as DS_CID_GRAVIDADE,
    CASE 
    	WHEN DT_ATENDIMENTO  BETWEEN '2022-03-20' AND '2022-06-20' THEN 1
    ELSE 0
  	END AS outono,
  	CASE 
    	WHEN DT_ATENDIMENTO  BETWEEN '2022-06-21' AND '2022-09-22' THEN 1
    ELSE 0
  	END AS inverno,
  	CASE 
    	WHEN DT_ATENDIMENTO  BETWEEN '2022-09-23' AND '2022-12-20' THEN 1
    ELSE 0
  	END AS primavera,
  	CASE 
    	WHEN DT_ATENDIMENTO  BETWEEN '2022-12-21' AND '2022-12-31' THEN 1
    	WHEN DT_ATENDIMENTO  BETWEEN '2022-01-01' AND '2022-03-19' THEN 1
    ELSE 0
  	END AS verao
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
        arquivo_txt.write(linha + "\n")

def campos(resultado):
    indices_desejados = [4, 5, 11]
    campos = [float(resultado[i]) if resultado[i] is not None else None for i in indices_desejados]
    return campos

if __name__ == '__main__':
    _log.info("Criando conexão")
    conexao = criar_conexao(_config)
    _log.info(f"conectado: {conexao.is_connected()}")

    cursor = conexao.cursor()
    cursor.execute(query_dados_treino(), ("20220101", "20221030"))

    poluentes = []
    cid = []
    internacao = []
    gravidade = []
    cid_gravidade = []
    for resultado in cursor.fetchall():
        indices_desejados = [0, 1, 2, 3, 4, 5, 14, 15, 16, 17]
        campos = [float(resultado[i]) if resultado[i] is not None else None for i in indices_desejados]
        poluentes.append(campos)
        cid.append(resultado[6])
        internacao.append(resultado[11])
        gravidade.append(resultado[12])
        cid_gravidade.append(resultado[13])

    # Treinar o modelo
    modelo = treinar_modelo(np.array(poluentes), np.array(internacao))

    # Fazer previsões
    cursor.execute(query_dados_treino(), ("20221201", "20221231"))
    poluentes_prev = []
    for resultado in cursor.fetchall():
        indices_desejados = [0, 1, 2, 3, 4, 5, 14, 15, 16, 17]
        campos = [float(resultado[i]) if resultado[i] is not None else None for i in indices_desejados]
        poluentes_prev.append(campos)

    previsoes = fazer_previsao(modelo, np.array(poluentes_prev))

    # Salvar resultado
    cursor.execute(query_dados_treino(), ("20221201", "20221231"))
    index = 0
    for row in cursor.fetchall():
        MP10, NO, NO2, O3, TEMP, UR, DS_CID, data_poluente, DT_ATENDIMENTO, DS_LEITO, DT_ALTA, INTERNACAO, gravidade, cid_gravidade, *campos = row
        previsao = previsoes[index]
        campos_concatenados = f"{MP10}|{NO}|{NO2}|{O3}|{TEMP}|{UR}|{data_poluente}|{DT_ATENDIMENTO}|{DS_LEITO}|{DT_ALTA}|{DS_CID}|{INTERNACAO}|{previsao}"
        print(campos_concatenados)
        salvar_csv('resultado_naive_bayes.csv', campos_concatenados)
        index += 1
