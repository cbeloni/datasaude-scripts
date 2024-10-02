import requests

_url_carga = "https://datasaude-api-staging.beloni.dev.br/api/v1/paciente/carga_previsao"

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

def carga_lote(cids: list, tipo_analise: str):
    for cid in cids:
        fazer_carga(cid, tipo_analise)


if __name__ == "__main__":  
    caminho_arquivo = 'previsao/cids.txt'
    cids = list(ler_arquivo_cids(caminho_arquivo))
    carga_lote(cids,'ATENDIMENTO')
    carga_lote(cids,'INTERNACAO')