"""E3 — Geocodificação dos endereços via OpenCage.

Entrada : output/02_gestantes_datas.csv
Saída   : output/03_gestantes_geocode.csv
          output/pendencias_geocode.csv
          tabela `geocode_cache` (cache permanente)

Ver PLANEJAMENTO.md §E3.
"""

import json
import time
from datetime import date, datetime
from decimal import Decimal

import pandas as pd
import requests

from uruguaiana.config_uruguaiana import (
    BBOX_URUGUAIANA,
    CONFIANCA_MIN_OK,
    COORD_DEFAULT,
    CSV_02_DATAS,
    CSV_03_GEOCODE,
    CSV_PEND_GEOCODE,
    DIR_CACHE_GEOCODE,
    DIR_OUTPUT,
    MAX_TENTATIVAS,
    NIVEIS_LOGRADOURO,
    NIVEIS_LUGAR,
    OPENCAGE_URL,
    PROVIDER,
    QUOTA_MINIMA,
    THROTTLE_SEGUNDOS,
    TOL_CENTROIDE,
    api_key_opencage,
)
from uruguaiana.endereco import ajustar_endereco, hash_endereco, sem_endereco
from uruguaiana.repositorio import conectar, executar_em_lotes

ARQUIVO_CACHE_LOCAL = DIR_CACHE_GEOCODE / "cache_opencage.json"

CAMPOS_CACHE = [
    "endereco_hash",
    "provider",
    "endereco_original",
    "endereco_consultado",
    "status",
    "latitude",
    "longitude",
    "confianca",
    "nivel",
    "formatado",
    "componentes",
    "resposta_bruta",
    "tentativas",
]

SQL_UPSERT_CACHE = """
INSERT INTO geocode_cache
    (endereco_hash, provider, endereco_original, endereco_consultado, status,
     latitude, longitude, confianca, nivel, formatado, componentes, resposta_bruta,
     tentativas)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    endereco_original   = COALESCE(VALUES(endereco_original), endereco_original),
    endereco_consultado = COALESCE(VALUES(endereco_consultado), endereco_consultado),
    status              = VALUES(status),
    latitude            = VALUES(latitude),
    longitude           = VALUES(longitude),
    confianca           = VALUES(confianca),
    nivel               = VALUES(nivel),
    formatado           = VALUES(formatado),
    componentes         = VALUES(componentes),
    resposta_bruta      = COALESCE(VALUES(resposta_bruta), resposta_bruta),
    tentativas          = GREATEST(tentativas, VALUES(tentativas))
"""

# Colunas obrigatórias (NOT NULL) na tabela geocode_cache. Itens do cache que
# não as tenham não podem ser gravados — ver `persistir_cache`.
CAMPOS_OBRIGATORIOS = ("endereco_hash", "endereco_original", "endereco_consultado")


def _valor_json_mysql(valor):
    """Converte estruturas JSON para texto aceito pelo conector MySQL."""
    if valor is None or isinstance(valor, (str, bytes)):
        return valor
    if isinstance(valor, (dict, list, tuple)):
        return json.dumps(valor, ensure_ascii=False)
    return valor


def _json_nativo(valor):
    """Converte o valor para algo serializável por json.dumps.

    Necessário porque latitude/longitude vêm do MySQL como Decimal e porque o
    espelho local precisa sobreviver a releituras sem perder o tipo original.
    """
    if valor is None or isinstance(valor, (str, bool, int, float)):
        return valor
    if isinstance(valor, dict):
        return {k: _json_nativo(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_json_nativo(v) for v in valor]
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    return str(valor)


class QuotaExcedida(Exception):
    """Levantada quando a quota diária da OpenCage está no limite."""


# ------------------------------------------------------------ classificação
def _dentro_bbox(lat: float, lng: float) -> bool:
    return (
        BBOX_URUGUAIANA["lat_min"] <= lat <= BBOX_URUGUAIANA["lat_max"]
        and BBOX_URUGUAIANA["lng_min"] <= lng <= BBOX_URUGUAIANA["lng_max"]
    )


def _eh_centroide(lat: float, lng: float) -> bool:
    return (
        abs(lat - COORD_DEFAULT[0]) <= TOL_CENTROIDE
        and abs(lng - COORD_DEFAULT[1]) <= TOL_CENTROIDE
    )


def classificar(resposta: dict | None, erro: bool = False) -> dict:
    """Classifica o retorno da API. Sempre devolve coordenada utilizável.

    Ordem das verificações (ver PLANEJAMENTO §E3.3): o bbox vem ANTES da confiança.
    """
    falha = {
        "latitude": COORD_DEFAULT[0],
        "longitude": COORD_DEFAULT[1],
        "confianca": None,
        "nivel": None,
        "formatado": None,
        "componentes": None,
        "geo_default": 1,
    }

    if erro:
        return {**falha, "status": "ERRO_API"}

    resultados = (resposta or {}).get("results") or []
    if not resultados:
        return {**falha, "status": "NAO_ENCONTRADO"}

    melhor = resultados[0]
    geo = melhor.get("geometry") or {}
    lat, lng = geo.get("lat"), geo.get("lng")
    componentes = melhor.get("components") or {}
    nivel = str(componentes.get("_type") or "").lower() or None
    confianca = melhor.get("confidence")
    formatado = melhor.get("formatted")

    # 1) coordenada ausente
    if lat is None or lng is None:
        return {**falha, "status": "NAO_ENCONTRADO"}

    # 2) fora do município (só o bbox detecta — ver §2.7 Descoberta 2)
    if not _dentro_bbox(lat, lng):
        return {
            **falha,
            "nivel": nivel,
            "confianca": confianca,
            "formatado": formatado,
            "componentes": componentes,
            "status": "FORA_DO_MUNICIPIO",
        }

    # 3) fallback para o centroide do município (§2.7 Descoberta 1)
    if _eh_centroide(lat, lng) or (nivel in NIVEIS_LUGAR):
        return {
            **falha,
            "nivel": nivel,
            "confianca": confianca,
            "formatado": formatado,
            "componentes": componentes,
            "status": "CENTROIDE_MUNICIPIO",
        }

    # 4) resolvido no logradouro
    if nivel in NIVEIS_LOGRADOURO and (confianca or 0) >= CONFIANCA_MIN_OK:
        return {
            "latitude": lat,
            "longitude": lng,
            "confianca": confianca,
            "nivel": nivel,
            "formatado": formatado,
            "componentes": componentes,
            "geo_default": 0,
            "status": "OK",
        }

    # 5) dentro do bbox, mas fraco — mantém a coordenada real
    return {
        "latitude": lat,
        "longitude": lng,
        "confianca": confianca,
        "nivel": nivel,
        "formatado": formatado,
        "componentes": componentes,
        "geo_default": 0,
        "status": "BAIXA_CONFIANCA",
    }


# ------------------------------------------------------------------- cliente
class ClienteGeocode:
    def __init__(self, chave: str, cache: dict | None = None):
        self.chave = chave
        self.cache = cache or {}
        self.sessao = requests.Session()
        self.ultima_resposta = None
        self.chamadas = 0
        # hashes efetivamente consultados na API nesta execução
        self.novos: set[str] = set()

    # ---------------------------------------------------------- API
    def _chamar(self, endereco_ajustado: str) -> tuple[dict | None, bool]:
        parametros = {
            "key": self.chave,
            "q": endereco_ajustado,
            "language": "pt-BR",
            "countrycode": "br",
            "limit": 1,
            "no_annotations": 1,
            "abbrv": 1,
        }

        for tentativa in range(1, MAX_TENTATIVAS + 1):
            try:
                resposta = self.sessao.get(OPENCAGE_URL, params=parametros, timeout=30)
                corpo = resposta.json()
            except Exception as erro:
                if tentativa == MAX_TENTATIVAS:
                    print(f"      [api] falha de rede: {erro}")
                    return None, True
                time.sleep(2 ** tentativa)
                continue

            self.ultima_resposta = corpo
            codigo = (corpo.get("status") or {}).get("code")

            if codigo == 200 and resposta.status_code == 200:
                self.chamadas += 1
                return corpo, False

            if codigo == 402:
                raise QuotaExcedida("OpenCage: quota diária esgotada (402).")

            # 429 (rate limit) e 5xx -> backoff e tenta de novo
            if codigo in (429, 500, 502, 503) or resposta.status_code >= 500:
                if tentativa == MAX_TENTATIVAS:
                    return None, True
                time.sleep(2 ** tentativa)
                continue

            # 401/403/400 etc -> erro definitivo desta chamada
            print(
                f"      [api] status.code={codigo} "
                f"http={resposta.status_code} msg={(corpo.get('status') or {}).get('message')}"
            )
            return None, True

        return None, True

    # ------------------------------------------------------- resolução
    def resolver(self, endereco_original):
        """Resolve um endereço bruto. Devolve o dicionário de resultado."""
        ajustado, ajustes = ajustar_endereco(endereco_original)

        if ajustado is None:
            return {
                "endereco_ajustado": None,
                "endereco_ajuste": None,
                "endereco_hash": None,
                "latitude": COORD_DEFAULT[0],
                "longitude": COORD_DEFAULT[1],
                "confianca": None,
                "nivel": None,
                "formatado": None,
                "componentes": None,
                "geo_default": 1,
                "geo_status": "SEM_ENDERECO",
                "do_cache": False,
            }

        chave = hash_endereco(ajustado)

        # cache hit
        if chave in self.cache:
            item = self.cache[chave]
            return {
                "endereco_ajustado": ajustado,
                "endereco_ajuste": ajustes,
                "endereco_hash": chave,
                "latitude": item["latitude"],
                "longitude": item["longitude"],
                "confianca": item.get("confianca"),
                "nivel": item.get("nivel"),
                "formatado": item.get("formatado"),
                "componentes": item.get("componentes"),
                "geo_default": int(item.get("geo_default", 0)),
                "geo_status": item["status"],
                "do_cache": True,
            }

        corpo, erro = self._chamar(ajustado)
        resultado = classificar(corpo, erro=erro)

        item_cache = {
            "endereco_hash": chave,
            "provider": PROVIDER,
            "endereco_original": str(endereco_original),
            "endereco_consultado": ajustado,
            "status": resultado["status"],
            "latitude": resultado["latitude"],
            "longitude": resultado["longitude"],
            "confianca": resultado["confianca"],
            "nivel": resultado["nivel"],
            "formatado": resultado["formatado"],
            "componentes": json.dumps(resultado["componentes"], ensure_ascii=False)
            if resultado["componentes"]
            else None,
            "resposta_bruta": json.dumps(corpo, ensure_ascii=False) if corpo else None,
            "tentativas": 1,
            "geo_default": resultado["geo_default"],
        }
        self.cache[chave] = item_cache
        self.novos.add(chave)

        return {
            "endereco_ajustado": ajustado,
            "endereco_ajuste": ajustes,
            "endereco_hash": chave,
            "latitude": resultado["latitude"],
            "longitude": resultado["longitude"],
            "confianca": resultado["confianca"],
            "nivel": resultado["nivel"],
            "formatado": resultado["formatado"],
            "componentes": resultado["componentes"],
            "geo_default": resultado["geo_default"],
            "geo_status": resultado["status"],
            "do_cache": False,
        }

    # ----------------------------------------------------------- quota
    def restante(self):
        if not self.ultima_resposta:
            return None
        return (self.ultima_resposta.get("rate") or {}).get("remaining")

    def salvar_cache_local(self):
        """Espelho local do cache (agilidade e uso offline).

        Os valores são sanitizados para tipos nativos de JSON — Decimals e numpy
        não são serializáveis e corromperiam o arquivo.
        """
        DIR_CACHE_GEOCODE.mkdir(parents=True, exist_ok=True)
        limpo = {chave: _json_nativo(item) for chave, item in self.cache.items()}
        ARQUIVO_CACHE_LOCAL.write_text(
            json.dumps(limpo, ensure_ascii=False), encoding="utf-8"
        )

    def novos_itens(self) -> dict:
        """Somente os endereços efetivamente consultados NESTA execução.

        É isso que deve ir para o banco: itens já existentes não precisam ser
        reescritos (e alguns podem ter vindo de um espelho local incompleto).
        """
        return {
            chave: self.cache[chave]
            for chave in self.novos
            if chave in self.cache
        }


# ------------------------------------------------------------- persistência
def carregar_cache() -> dict:
    """Carrega o cache da tabela MySQL (se existir) e do espelho local.

    IMPORTANTE: todas as colunas obrigatórias do upsert são lidas, senão o cache
    deixa de poder ser regravado (ver `persistir_cache`). `resposta_bruta` NÃO é
    lida — é um JSON pesado que o `COALESCE` do upsert preserva no banco.
    """
    cache: dict = {}

    # espelho local primeiro — usado apenas para recuperar `resposta_bruta`,
    # que é pesado e por isso não é lido do banco.
    espelho: dict = {}
    if ARQUIVO_CACHE_LOCAL.exists():
        try:
            espelho = json.loads(ARQUIVO_CACHE_LOCAL.read_text(encoding="utf-8"))
        except Exception:
            espelho = {}

    try:
        conn = conectar()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT endereco_hash, endereco_original, endereco_consultado, status, "
                "       latitude, longitude, confianca, nivel, formatado, componentes, "
                "       tentativas "
                "  FROM geocode_cache"
            )
            for linha in cursor.fetchall():
                componentes = linha.get("componentes")
                if isinstance(componentes, (str, bytes)):
                    try:
                        componentes = json.loads(componentes)
                    except Exception:
                        componentes = None

                bruto = espelho.get(linha["endereco_hash"]) or {}

                cache[linha["endereco_hash"]] = {
                    "endereco_hash": linha["endereco_hash"],
                    "provider": PROVIDER,
                    "endereco_original": linha["endereco_original"],
                    "endereco_consultado": linha["endereco_consultado"],
                    "status": linha["status"],
                    "latitude": float(linha["latitude"])
                    if linha["latitude"] is not None
                    else None,
                    "longitude": float(linha["longitude"])
                    if linha["longitude"] is not None
                    else None,
                    "confianca": linha["confianca"],
                    "nivel": linha["nivel"],
                    "formatado": linha["formatado"],
                    "componentes": componentes,
                    "resposta_bruta": bruto.get("resposta_bruta"),
                    "tentativas": linha.get("tentativas") or 1,
                    "geo_default": 1
                    if linha["status"]
                    in (
                        "SEM_ENDERECO",
                        "NAO_ENCONTRADO",
                        "ERRO_API",
                        "CENTROIDE_MUNICIPIO",
                        "FORA_DO_MUNICIPIO",
                    )
                    else 0,
                }
        finally:
            conn.close()
    except Exception as erro:
        print(f"   [cache] tabela geocode_cache indisponível ({erro}); usando só o local")
        # sem banco, o espelho local é a única fonte — usa o que for utilizável
        for chave, item in espelho.items():
            if item.get("endereco_hash") and item.get("endereco_original"):
                cache.setdefault(chave, item)

    return cache


def persistir_cache(cache: dict):
    """Grava o cache na tabela `geocode_cache` (upsert idempotente)."""
    linhas = []
    ignorados = 0

    for item in cache.values():
        # Rede de segurança: itens sem os campos NOT NULL não podem ser gravados.
        # Isso só acontece se algo foi carregado de forma incompleta.
        if any(not item.get(c) for c in CAMPOS_OBRIGATORIOS):
            ignorados += 1
            continue

        linha = [item.get(c) for c in CAMPOS_CACHE]
        # Colunas JSON precisam receber texto serializado pelo conector MySQL.
        for coluna in ("componentes", "resposta_bruta"):
            indice = CAMPOS_CACHE.index(coluna)
            linha[indice] = _valor_json_mysql(linha[indice])
        linhas.append(linha)

    if ignorados:
        print(f"   [cache] {ignorados} itens incompletos ignorados (já estão no banco)")
    if not linhas:
        print("   [cache] nada novo para persistir")
        return 0

    conn = conectar()
    try:
        return executar_em_lotes(
            conn, SQL_UPSERT_CACHE, linhas, 500, rotulo="geocode_cache"
        )
    finally:
        conn.close()


# ------------------------------------------------------------------ main
# Referência ao cliente da última execução, para que o CLI possa persistir
# exatamente os endereços consultados naquela rodada.
_ULTIMO_CLIENTE: "ClienteGeocode | None" = None


def executar(force: bool = False) -> pd.DataFrame:
    global _ULTIMO_CLIENTE

    DIR_OUTPUT.mkdir(parents=True, exist_ok=True)

    dados = pd.read_csv(CSV_02_DATAS)
    print(f"[E3] {len(dados)} registros | "
          f"{dados['endereco_original'].nunique()} endereços distintos brutos")

    cache = {} if force else carregar_cache()
    cliente = ClienteGeocode(api_key_opencage(), cache)
    print(f"   cache carregado: {len(cliente.cache)} endereços")

    resultados: list[dict] = []
    novas = reaproveitados = sem_end = 0
    abortado = False

    for registro in dados.to_dict("records"):
        try:
            res = cliente.resolver(registro["endereco_original"])
        except QuotaExcedida as erro:
            print(f"   !!! ABORTANDO: {erro}")
            abortado = True
            break

        fez_chamada = (not res["do_cache"]) and res["geo_status"] != "SEM_ENDERECO"

        if res["geo_status"] == "SEM_ENDERECO":
            sem_end += 1
        elif res["do_cache"]:
            reaproveitados += 1
        elif fez_chamada:
            novas += 1
            restante = cliente.restante()
            if restante is not None and restante < QUOTA_MINIMA:
                print(f"   !!! ABORTANDO: quota restante baixa ({restante})")
                resultados.append({**registro, **res})
                abortado = True
                break
            if novas % 25 == 0:
                cliente.salvar_cache_local()
                print(f"   {novas} novas consultas | quota restante: {restante}")
            time.sleep(THROTTLE_SEGUNDOS)

        resultados.append({**registro, **res})

    saida = pd.DataFrame(resultados)
    saida.to_csv(CSV_03_GEOCODE, index=False)
    cliente.salvar_cache_local()
    _ULTIMO_CLIENTE = cliente

    print(
        f"   novas consultas: {novas} | do cache: {reaproveitados} | "
        f"sem endereço: {sem_end}" + ("  [LOTE INCOMPLETO]" if abortado else "")
    )
    print(f"   geo_status: {saida['geo_status'].value_counts().to_dict()}")
    print(f"   geo_default=1: {int(saida['geo_default'].sum())} de {len(saida)}")
    print(f"   -> {CSV_03_GEOCODE.relative_to(DIR_OUTPUT.parent)}")

    pend = saida[(saida["geo_default"] == 1) & (saida["endereco_ajustado"].notna())]
    if len(pend):
        colunas = [
            "grupo", "id_externo", "endereco_original", "endereco_ajustado",
            "geo_status", "nivel", "confianca", "formatado",
        ]
        pend[[c for c in colunas if c in pend.columns]].to_csv(
            CSV_PEND_GEOCODE, index=False
        )
        print(f"   {len(pend)} pendências -> {CSV_PEND_GEOCODE.name}")

    return saida


def persistir(cache: dict):
    print("[E3] Persistindo o cache na tabela geocode_cache...")
    return persistir_cache(cache)


def persistir_cache_da_execucao():
    """Persiste os endereços consultados na última chamada de `executar()`.

    É o caminho correto: usa o cache em memória da própria execução, com os
    campos obrigatórios garantidos, em vez de reler o espelho local (que pode
    estar ausente, desatualizado ou editado por outra ferramenta).
    """
    if _ULTIMO_CLIENTE is None:
        print("   [cache] nenhuma execução do E3 nesta sessão — nada a persistir")
        return 0

    novos = _ULTIMO_CLIENTE.novos_itens()
    if not novos:
        print("   [cache] nenhuma consulta nova nesta execução — banco já está atualizado")
        return 0

    print(f"[E3] Persistindo {len(novos)} novos endereços no geocode_cache...")
    return persistir_cache(novos)
