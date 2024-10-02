import requests
from dotenv import load_dotenv, dotenv_values
import mysql.connector

load_dotenv()

_config = dotenv_values(".env")
_url_carga = "https://datasaude-api-staging.beloni.dev.br/api/v1/paciente/carga_previsao"
_url_previsao = "https://datasaude-api-ml-staging.beloni.dev.br/api/temporal/treinar"


def criar_conexao():
    return mysql.connector.connect(
        host= _config['host'],
        user= _config['user'],
        password= _config['password'],
        database= _config['database'],
        ssl_ca= _config['ssl_ca'] if 'ssl_ca' in _config else None
    )

def ler_arquivo_cids(caminho_arquivo):
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            linhas = arquivo.readlines()
            for linha in linhas:
                yield linha.strip()
    except FileNotFoundError:
        print(f"Arquivo {caminho_arquivo} não encontrado.")
    except Exception as e:
        print(f"Ocorreu um erro ao ler o arquivo: {e}")

def fazer_carga(cid: str, tipo_analise: str):    
    params = {
        "qtd_dias_corte": 1,
        "cid": cid,
        "tipo_analise": tipo_analise
    }
    response = requests.post(_url_carga, params=params)
    if response.status_code == 200:
        print(f"Requisição para CID {cid} enviada com sucesso.")
    else:
        print(f"Falha ao enviar requisição para CID {cid}. Status code: {response.status_code}")

def fazer_previsao(cid: str, tipo_analise: str):
    params = {
        "qtd_dias_previsao": 30,
        "qtd_dias_sazonalidade": 90,
        "cid": cid,
        "tipo_analise": tipo_analise
    }
    response = requests.post(_url_previsao, params=params)
    if response.status_code == 200:
        print(f"Previsão para CID {cid} enviada com sucesso.")
    else:
        print(f"Falha ao enviar previsão para CID {cid}. Status code: {response.status_code}")

def carga_previsao_lote(cids: list, tipo_analise: str):
    for cid in cids:
        fazer_carga(cid, tipo_analise)
        fazer_previsao(cid, tipo_analise)

def loop_paciente():
    conexao = criar_conexao()
    cursor = conexao.cursor()
    query = """
    SELECT CAST(CONCAT(YEAR(DT_ATENDIMENTO), LPAD(MONTH(DT_ATENDIMENTO), 2, '0')) AS UNSIGNED) AS registros
    FROM paciente_import
    GROUP BY registros
    ORDER BY registros
    """
    cursor.execute(query)
    resultados = cursor.fetchall()
    
    for (registro,) in resultados:
        yield registro

    cursor.close()
    conexao.close()

def insert_paciente(registro):
    conexao = criar_conexao()
    cursor = conexao.cursor()
    
    select_query = """
    insert into paciente (CD_ATENDIMENTO,NM_PACIENTE,DT_ATENDIMENTO,TP_ATENDIMENTO,DS_ORI_ATE,DS_LEITO,DT_PREVISTA_ALTA,DT_ALTA,CD_SGRU_CID,CD_CID,DS_CID,SN_INTERNADO,DT_NASC,IDADE,TP_SEXO,DS_ENDERECO,NR_ENDERECO,NM_BAIRRO,NR_CEP)
    (
    SELECT truncate(id*3.14,0),NM_PACIENTE,DT_ATENDIMENTO,TP_ATENDIMENTO,DS_ORI_ATE,DS_LEITO,DT_PREVISTA_ALTA,DT_ALTA,CD_SGRU_CID,CD_CID,DS_CID,SN_INTERNADO,DT_NASC,IDADE,TP_SEXO,DS_ENDERECO,NR_ENDERECO,NM_BAIRRO,NR_CEP
    FROM paciente_import
    WHERE CAST(CONCAT(YEAR(DT_ATENDIMENTO), LPAD(MONTH(DT_ATENDIMENTO), 2, '0')) AS UNSIGNED) = '%s');
    """
    cursor.execute(select_query, (registro,))
    
    delete_query = """
    DELETE FROM paciente_import
    WHERE CAST(CONCAT(YEAR(DT_ATENDIMENTO), LPAD(MONTH(DT_ATENDIMENTO), 2, '0')) AS UNSIGNED) = '%s'
    """
    cursor.execute(delete_query, (registro,))
    conexao.commit()
    
    cursor.close()
    conexao.close()

if __name__ == "__main__":  
    caminho_arquivo = 'previsao/cids.txt'
    cids = list(ler_arquivo_cids(caminho_arquivo))
    for ano_mes in loop_paciente():
        print(f"Processando registros do mês {ano_mes}")
        insert_paciente(ano_mes)
        print(f"Registros do mês {ano_mes} inseridos e deletados com sucesso.")
        carga_previsao_lote(cids,'ATENDIMENTO')
        carga_previsao_lote(cids,'INTERNACAO')
        print(f"Finalizado registros do mês {ano_mes}")