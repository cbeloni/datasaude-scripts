import requests

from dotenv import load_dotenv, dotenv_values

load_dotenv()
_config = dotenv_values("../.env")

class CestebConsuilta:

    _url_base: str = "https://qualar.cetesb.sp.gov.br/qualar"
    _cookie: str = "JSESSIONID=3DDE77F1D8CF84639CA10F80BB4A746C"

    _ATUALIZANDO: str = "Atualizando base de dados! Por favor, tente novamente em 5 minutos"
    _NENHUM_REGISTRO_ENCONTRADO: str = "Nenhum Registro Encontrado para o Filtro de Pesquisa"

    def autenticacao(self):
        if self._cookie is not None:
            return self._cookie

        url = self._url_base + f'/autenticador?cetesb_login={_config["login"]}'
        response = requests.request("POST", url, headers={}, data={}, files={})

        # Obter os cookies da resposta
        cookies = response.cookies

        for self._cookie in cookies:
            return f"{self._cookie.name}={self._cookie.value}"

        return "Erro ao autenticar"

    def filtrar(self):
        url = "https://qualar.cetesb.sp.gov.br/qualar/exportaDados.do?method=filtrarParametros"

        payload = {'irede': 'A',
                   'dataInicialStr': '01/01/2022',
                   'dataFinalStr': '01/01/2023',
                   'iTipoDado': 'P',
                   'estacaoVO.nestcaMonto': '73',
                   'parametroVO.nparmt': '16'}
        files = []
        headers = {
            'Cookie': f'{self._cookie}'
        }

        response = requests.request("POST", url, headers=headers, data=payload, files=files)

        return response.text

    def scrap(self):
        url = "https://qualar.cetesb.sp.gov.br/qualar/exportaDados.do?method=pesquisar"

        payload = {}
        headers = {
            'Cookie': f'{self._cookie}'
        }

        response = requests.request("GET", url, headers=headers, data=payload)


        if self._ATUALIZANDO in response.text:
            raise Exception(f"{self._ATUALIZANDO}")

        if self._NENHUM_REGISTRO_ENCONTRADO in response.text:
            raise Exception(self._NENHUM_REGISTRO_ENCONTRADO)


        with open("arquivo2.html", "w") as arquivo:
            # Grava o texto no arquivo
            arquivo.write(response.text)