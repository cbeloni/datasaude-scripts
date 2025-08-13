from dotenv import load_dotenv, dotenv_values

load_dotenv()
_config = dotenv_values(".env")

def get_config():
    global _config
    if not _config:
        raise ValueError("Configuração não carregada. Verifique o arquivo .env.")
    return _config