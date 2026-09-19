"""Constantes e configuração do pipeline Gestantes Uruguaiana/RS."""

from pathlib import Path

from dotenv import dotenv_values

# --------------------------------------------------------------------- caminhos
DIR_URUGUAIANA = Path(__file__).resolve().parent
RAIZ_PROJETO = DIR_URUGUAIANA.parent

DIR_OUTPUT = DIR_URUGUAIANA / "output"
DIR_CACHE = DIR_OUTPUT / "cache"
DIR_CACHE_OPENMETEO = DIR_CACHE / "openmeteo"
DIR_CACHE_GEOCODE = DIR_CACHE / "geocode"

SQL_TABELA_GESTANTES = DIR_URUGUAIANA / "create_table_gestantes_uruguaiana.sql"
SQL_TABELA_EXPOSICAO = DIR_URUGUAIANA / "create_table_gestantes_exposicao_diaria.sql"
SQL_TABELA_CACHE = DIR_URUGUAIANA / "create_table_geocode_cache.sql"

XLSX_GESTANTES = Path(
    "/Users/cauebeloni/Documents/Projeto Pensi/dados/uruguaiana-rs/Dados_gestantes.xlsx"
)

# CSVs intermediários
CSV_01_NORMALIZADO = DIR_OUTPUT / "01_gestantes_normalizado.csv"
CSV_02_DATAS = DIR_OUTPUT / "02_gestantes_datas.csv"
CSV_03_GEOCODE = DIR_OUTPUT / "03_gestantes_geocode.csv"
CSV_06_EXPOSICAO = DIR_OUTPUT / "06_exposicao_diaria.csv"
CSV_PEND_GEOCODE = DIR_OUTPUT / "pendencias_geocode.csv"
CSV_PEND_DATAS = DIR_OUTPUT / "pendencias_datas.csv"

# ------------------------------------------------------------------- entrada
ABAS = ["Grupo1", "Grupo_2"]
COLUNAS_CANONICAS = [
    "id_externo",
    "carimbo_data_hora",
    "data_coleta_original",
    "endereco_original",
]

# Valores da coluna de endereço que significam "sem endereço".
# Comparação sempre em MAIÚSCULAS e com strip().
STOP_ADDRESS = {
    "NAN",
    "",
    "SEM ENDEREÇO",
    "SEM ENDERECO",
    "NÃO APARECE NO CELK",
    "NAO APARECE NO CELK",
    "SEM DADOS RECENTES",
}

# --------------------------------------------------------------------- datas
TOLERANCIA_DIAS = 30  # desvio máximo entre Data da Coleta e Carimbo
MESES_JANELA = 9  # janela de exposição: [data_ref - 9 meses, data_ref]

# ---------------------------------------------------------------- endereços
MUNICIPIO_PADRAO = "URUGUAIANA, RS, BRASIL"

# Municípios vizinhos que devem ser REMOVIDOS do endereço.
# Premissa de projeto: todo endereço é do município de Uruguaiana/RS.
MUNICIPIOS_REMOVER = [
    "BARRA DO QUARAÍ",
    "BARRA DO QUARAI",
    "ITAQUI",
    "ALEGRETE",
    "SÃO BORJA",
    "SAO BORJA",
    "SANTANA DO LIVRAMENTO",
]

# Typos conhecidos de município
TYPO_MUNICIPIO = {"URGUAIANA": "URUGUAIANA"}

# ------------------------------------------------------------ geocodificação
OPENCAGE_URL = "https://api.opencagedata.com/geocode/v1/json"

# Centroide do município de Uruguaiana (devolvido pela própria OpenCage).
# Usado SEMPRE que não houver coordenada válida.
COORD_DEFAULT = (-29.75472, -57.08833)
TOL_CENTROIDE = 0.001  # ~110 m

# Bounding box do município de Uruguaiana (obtido da OpenCage).
# Resultados fora daqui são considerados erro (ex.: Rio Grande/RS, a 250 km).
BBOX_URUGUAIANA = {
    "lat_min": -30.2050473,
    "lat_max": -29.4001025,
    "lng_min": -57.3290000,
    "lng_max": -56.1502443,
}

# `components._type` que indicam resultado no nível de logradouro (confiável)
NIVEIS_LOGRADOURO = {
    "road",
    "house",
    "street",
    "neighbourhood",
    "village",
    "hamlet",
    "building",
    "address",
}

# `components._type` que indicam fallback para a cidade/município (centroide)
NIVEIS_LUGAR = {
    "city",
    "municipality",
    "state",
    "country",
    "administrative",
    "place",
    "county",
    "region",
}

CONFIANCA_MIN_OK = 8  # abaixo disso, cai em BAIXA_CONFIANCA

PROVIDER = "opencage"
THROTTLE_SEGUNDOS = 1.1  # OpenCage: 1 req/s
MAX_TENTATIVAS = 3
QUOTA_MINIMA = 50  # aborta o lote se rate.remaining < isso

# --------------------------------------------------------------- Open-Meteo
OPENMETEO_AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
OPENMETEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
OPENMETEO_TIMEZONE = "America/Sao_Paulo"  # OBRIGATÓRIO (ver PLANEJAMENTO §2.5)
OPENMETEO_UTC_OFFSET_ESPERADO = -10800

# Resiliência. A Open-Meteo devolve 429/timeout de forma transitória em
# requisições muito longas; por isso o período é buscado em blocos e com retry.
OPENMETEO_DIAS_POR_BLOCO = 365  # ~1 ano por requisição
OPENMETEO_TIMEOUT = 180  # segundos de leitura
OPENMETEO_MAX_TENTATIVAS = 5
OPENMETEO_ESPERA_BASE = 5  # backoff exponencial: 5, 10, 20, 40 s
OPENMETEO_ESPERA_ENTRE_CHAMADAS = 1.0  # cortesia entre requisições

VARIAVEIS_AR = ["pm10", "pm2_5"]
VARIAVEL_METEO = "temperature_2m"
VAR_MAP = {"pm10": "pm10", "pm2_5": "pm2_5", "temperature_2m": "temperatura"}
HORAS_MINIMAS_VALIDAS = 18  # 75% de 24h

GRADE_CASAS = 1  # arredondamento para deduplicar por célula de grade (0,1°)

# ---------------------------------------------------------------------- banco
_ENV = dotenv_values(RAIZ_PROJETO / ".env")


def _env(chave: str, obrigatorio: bool = True):
    valor = _ENV.get(chave)
    if valor is None:
        if obrigatorio:
            raise RuntimeError(
                f"Variável '{chave}' não encontrada em {RAIZ_PROJETO / '.env'}"
            )
        return None
    return valor.strip().strip('"').strip("'")


def config_banco() -> dict:
    """Credenciais do MySQL lidas do .env do projeto."""
    return {
        "host": _env("host"),
        "user": _env("user"),
        "password": _env("password"),
        "database": _env("database"),
    }


def api_key_opencage() -> str:
    return _env("OPENCAGE_API_KEY")


# Tabelas criadas NESTE contexto. O pipeline só pode tocar nestas três.
TABELAS_DO_CONTEXTO = (
    "gestantes_uruguaiana",
    "gestantes_exposicao_diaria",
    "geocode_cache",
)
