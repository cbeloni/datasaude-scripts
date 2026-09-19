"""E5 — Coleta das séries horárias na Open-Meteo (qualidade do ar e temperatura).

Entrada : output/03_gestantes_geocode.csv (para saber as células de grade)
Saída   : output/cache/openmeteo/*.json

Duas otimizações centrais:

1. DEDUPLICAÇÃO POR CÉLULA DE GRADE. A Open-Meteo devolve o dado do PONTO DE GRADE
   mais próximo, não do ponto pedido. Agrupando por célula de 0,1° e buscando o
   intervalo global uma única vez por célula, o consumo cai de 1.416 chamadas
   para algumas dezenas.

2. REQUISIÇÕES EM BLOCOS DE ~1 ANO. Períodos longos (2,6 anos horários) sofrem
   429 e timeout de forma transitória. Buscar em blocos menores reduz o impacto
   de cada falha e permite retomar sem refazer o que já foi baixado.

Ver PLANEJAMENTO.md §E5.
"""

import json
import time
from datetime import date, timedelta

import requests

from uruguaiana.config_uruguaiana import (
    DIR_CACHE_OPENMETEO,
    GRADE_CASAS,
    OPENMETEO_AIR_URL,
    OPENMETEO_ARCHIVE_URL,
    OPENMETEO_DIAS_POR_BLOCO,
    OPENMETEO_ESPERA_BASE,
    OPENMETEO_ESPERA_ENTRE_CHAMADAS,
    OPENMETEO_MAX_TENTATIVAS,
    OPENMETEO_TIMEOUT,
    OPENMETEO_TIMEZONE,
    OPENMETEO_UTC_OFFSET_ESPERADO,
    VARIAVEL_METEO,
    VARIAVEIS_AR,
)


class OpenMeteoIndisponivel(Exception):
    """A Open-Meteo não devolveu dado válido após todas as tentativas."""


def chave_grade(latitude: float, longitude: float) -> str:
    """Chave da célula de grade (deduplicação)."""
    return f"{round(latitude, GRADE_CASAS)}_{round(longitude, GRADE_CASAS)}"


def _blocos(inicio: str, fim: str, dias: int = OPENMETEO_DIAS_POR_BLOCO):
    """Divide [inicio, fim] em blocos de no máximo `dias`, sem sobreposição."""
    atual = date.fromisoformat(inicio)
    limite = date.fromisoformat(fim)
    while atual <= limite:
        fim_bloco = min(atual + timedelta(days=dias - 1), limite)
        yield atual.isoformat(), fim_bloco.isoformat()
        atual = fim_bloco + timedelta(days=1)


def contar_blocos(inicio: str, fim: str) -> int:
    """Quantos blocos um intervalo gera (para estimar o nº de requisições)."""
    return sum(1 for _ in _blocos(inicio, fim))


def _caminho_cache(prefixo: str, chave: str, inicio: str, fim: str):
    return DIR_CACHE_OPENMETEO / f"{prefixo}_{chave}_{inicio}_{fim}.json"


def _valido(corpo, variaveis: list) -> bool:
    """Confere que a resposta traz as variáveis pedidas, com tamanho coerente."""
    if not isinstance(corpo, dict):
        return False
    horario = corpo.get("hourly")
    if not isinstance(horario, dict):
        return False
    tempos = horario.get("time")
    if not tempos:
        return False
    for variavel in variaveis:
        valores = horario.get(variavel)
        if valores is None or len(valores) != len(tempos):
            return False
    return True


def _espera_para_retry(resposta, tentativa: int) -> float:
    """Backoff exponencial, respeitando o header Retry-After quando presente."""
    if resposta is not None:
        cabecalho = resposta.headers.get("Retry-After")
        if cabecalho:
            try:
                return max(float(cabecalho), 1.0)
            except (TypeError, ValueError):
                pass
    return float(OPENMETEO_ESPERA_BASE * (2 ** (tentativa - 1)))


def _buscar_bloco(url, parametros, caminho, variaveis, descricao) -> dict:
    """Busca um bloco, com cache em disco, validação de conteúdo e retry."""
    if caminho.exists():
        try:
            guardado = json.loads(caminho.read_text(encoding="utf-8"))
            if _valido(guardado, variaveis):
                return guardado
            print(f"      [cache] {descricao}: conteúdo inválido, refazendo")
        except Exception:
            print(f"      [cache] {descricao}: arquivo corrompido, refazendo")

    ultimo_erro = "sem tentativas"
    for tentativa in range(1, OPENMETEO_MAX_TENTATIVAS + 1):
        resposta = None
        try:
            resposta = requests.get(url, params=parametros, timeout=OPENMETEO_TIMEOUT)

            if resposta.status_code == 200:
                corpo = resposta.json()
                if _valido(corpo, variaveis):
                    DIR_CACHE_OPENMETEO.mkdir(parents=True, exist_ok=True)
                    caminho.write_text(
                        json.dumps(corpo, ensure_ascii=False), encoding="utf-8"
                    )
                    time.sleep(OPENMETEO_ESPERA_ENTRE_CHAMADAS)
                    return corpo
                ultimo_erro = f"resposta sem as variáveis {variaveis}"
            else:
                ultimo_erro = f"HTTP {resposta.status_code}: {resposta.text[:160]}"

        except Exception as erro:
            ultimo_erro = f"{type(erro).__name__}: {erro}"

        if tentativa < OPENMETEO_MAX_TENTATIVAS:
            espera = _espera_para_retry(resposta, tentativa)
            print(
                f"      [tentativa {tentativa}/{OPENMETEO_MAX_TENTATIVAS}] "
                f"{descricao} falhou ({ultimo_erro}). Aguardando {espera:.0f}s..."
            )
            time.sleep(espera)

    raise OpenMeteoIndisponivel(f"{descricao}: {ultimo_erro}")


def _mesclar(blocos: list, variaveis: list) -> dict:
    """Une as respostas dos blocos em uma estrutura única, no formato da API."""
    if len(blocos) == 1:
        return blocos[0]

    colunas = {variavel: [] for variavel in variaveis}
    tempos: list = []
    for corpo in blocos:
        tempos.extend(corpo["hourly"]["time"])
        for variavel in variaveis:
            colunas[variavel].extend(corpo["hourly"][variavel])

    # ordena cronologicamente (os blocos já vêm em ordem, mas garantimos)
    ordem = sorted(range(len(tempos)), key=lambda i: tempos[i])
    horario = {
        "time": [tempos[i] for i in ordem],
        **{v: [colunas[v][i] for i in ordem] for v in variaveis},
    }

    base = dict(blocos[0])
    base["hourly"] = horario
    return base


def _coletar(url, prefixo, variaveis, latitude, longitude, inicio, fim) -> dict:
    chave = chave_grade(latitude, longitude)
    baixados = []

    for inicio_bloco, fim_bloco in _blocos(inicio, fim):
        parametros = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": inicio_bloco,
            "end_date": fim_bloco,
            "hourly": ",".join(variaveis),
            "timezone": OPENMETEO_TIMEZONE,
        }
        baixados.append(
            _buscar_bloco(
                url,
                parametros,
                _caminho_cache(prefixo, chave, inicio_bloco, fim_bloco),
                variaveis,
                f"{prefixo} {chave} {inicio_bloco}..{fim_bloco}",
            )
        )

    corpo = _mesclar(baixados, variaveis)

    offset = corpo.get("utc_offset_seconds")
    if offset != OPENMETEO_UTC_OFFSET_ESPERADO:
        print(
            f"   [aviso] {chave}: utc_offset_seconds={offset} "
            f"(esperado {OPENMETEO_UTC_OFFSET_ESPERADO}) — horários podem estar "
            f"em outro fuso"
        )

    return corpo


def coletar_ar(latitude: float, longitude: float, inicio: str, fim: str) -> dict:
    """Série horária de pm10 e pm2_5 (Air Quality API)."""
    return _coletar(
        OPENMETEO_AIR_URL, "air", VARIAVEIS_AR, latitude, longitude, inicio, fim
    )


def coletar_temperatura(latitude: float, longitude: float, inicio: str, fim: str) -> dict:
    """Série horária de temperature_2m (Archive API)."""
    return _coletar(
        OPENMETEO_ARCHIVE_URL,
        "archive",
        [VARIAVEL_METEO],
        latitude,
        longitude,
        inicio,
        fim,
    )
