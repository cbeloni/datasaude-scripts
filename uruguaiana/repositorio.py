"""Acesso ao MySQL: conexão, criação das tabelas do contexto e upserts.

REGRAS DE SEGURANÇA DESTE MÓDULO
--------------------------------
1. Só são criadas as 3 tabelas de `TABELAS_DO_CONTEXTO` — nenhuma outra é tocada.
2. Nunca há DROP/TRUNCATE/DELETE. Se a tabela já existir, a criação é apenas ignorada.
3. Qualquer outra tabela referenciada fora de `TABELAS_DO_CONTEXTO` levanta erro.

Decisão de implementação: a conexão é aberta localmente (com número LIMITADO de
tentativas) em vez de usar `core.database.criar_conexao()`, que faz ``while True`` e
travaria o pipeline para sempre em caso de host inacessível.
"""

import re
import time
from pathlib import Path

import mysql.connector
from mysql.connector import Error as MySQLError

from uruguaiana.config_uruguaiana import (
    SQL_TABELA_CACHE,
    SQL_TABELA_EXPOSICAO,
    SQL_TABELA_GESTANTES,
    TABELAS_DO_CONTEXTO,
    config_banco,
)

MAX_TENTATIVAS_CONEXAO = 3
ESPERA_ENTRE_TENTATIVAS = 2  # segundos


# --------------------------------------------------------------- conexão
def conectar(tentativas: int = MAX_TENTATIVAS_CONEXAO):
    """Abre a conexão com o MySQL usando as credenciais do .env."""
    cfg = config_banco()
    ultimo_erro = None
    for n in range(1, tentativas + 1):
        try:
            return mysql.connector.connect(
                host=cfg["host"],
                user=cfg["user"],
                password=cfg["password"],
                database=cfg["database"],
                connection_timeout=15,
            )
        except MySQLError as erro:
            ultimo_erro = erro
            print(f"   [db] tentativa {n}/{tentativas} falhou: {erro}")
            if n < tentativas:
                time.sleep(ESPERA_ENTRE_TENTATIVAS)
    raise RuntimeError(
        f"Não foi possível conectar ao MySQL em {cfg['host']} "
        f"após {tentativas} tentativas: {ultimo_erro}"
    )


def _validar_tabela(nome: str) -> str:
    """Garante que só operamos sobre as tabelas deste contexto."""
    if nome not in TABELAS_DO_CONTEXTO:
        raise ValueError(
            f"Tabela '{nome}' está fora do contexto deste pipeline. "
            f"Permitidas: {TABELAS_DO_CONTEXTO}"
        )
    return nome


# --------------------------------------------------- criação das tabelas
def _extrair_create(caminho: Path) -> tuple[str, str]:
    """Lê o DDL e devolve (nome_tabela, sql) do primeiro CREATE TABLE."""
    linhas = [
        linha
        for linha in caminho.read_text(encoding="utf-8").splitlines()
        if not linha.strip().startswith("--")
    ]
    texto = "\n".join(linhas)

    # divide respeitando literais entre aspas simples
    partes, buffer, dentro = [], "", False
    for char in texto:
        if char == "'":
            dentro = not dentro
        if char == ";" and not dentro:
            if buffer.strip():
                partes.append(buffer.strip())
            buffer = ""
        else:
            buffer += char
    if buffer.strip():
        partes.append(buffer.strip())

    for instrucao in partes:
        if "CREATE TABLE" in instrucao:
            nome = re.search(r"CREATE TABLE `(\w+)`", instrucao).group(1)
            return nome, instrucao
    raise RuntimeError(f"Nenhum CREATE TABLE encontrado em {caminho}")


def criar_tabelas():
    """Cria as 3 tabelas do contexto, na ordem correta (FK depende da 1ª).

    Tabelas que já existem são IGNORADAS — nada é alterado ou removido.
    """
    arquivos = [SQL_TABELA_GESTANTES, SQL_TABELA_EXPOSICAO, SQL_TABELA_CACHE]

    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        existentes = {linha[0] for linha in cursor.fetchall()}

        for caminho in arquivos:
            nome, sql = _extrair_create(caminho)
            _validar_tabela(nome)

            if nome in existentes:
                print(f"   [db] {nome}: já existe — ignorada (nada foi alterado)")
                continue

            cursor.execute(sql)
            conn.commit()
            print(f"   [db] {nome}: criada")
    finally:
        conn.close()


def tabelas_existentes() -> set[str]:
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        return {linha[0] for linha in cursor.fetchall()}
    finally:
        conn.close()


def exigir_tabelas():
    """Falha cedo se as tabelas do contexto não existirem."""
    existentes = tabelas_existentes()
    faltando = [t for t in TABELAS_DO_CONTEXTO if t not in existentes]
    if faltando:
        raise RuntimeError(
            f"Tabelas ausentes: {faltando}. Execute a etapa 0 (--etapa 0) primeiro."
        )


# ------------------------------------------------------------- utilidades
def _limpar(valor):
    """Converte NaN/NaT/numpy para tipos aceitos pelo driver MySQL."""
    if valor is None:
        return None
    if isinstance(valor, float) and valor != valor:  # NaN
        return None
    if valor is not valor:  # NaT
        return None
    if hasattr(valor, "to_pydatetime"):  # pandas.Timestamp
        return valor.to_pydatetime()
    if hasattr(valor, "item"):  # numpy scalar
        return _limpar(valor.item())
    return valor


def executar_em_lotes(conn, sql, linhas, tamanho_lote, rotulo=""):
    """Executa `executemany` em lotes, com commit por lote. Devolve o total."""
    cursor = conn.cursor()
    total = 0
    inicio = time.time()
    for i in range(0, len(linhas), tamanho_lote):
        lote = [[_limpar(v) for v in linha] for linha in linhas[i: i + tamanho_lote]]
        cursor.executemany(sql, lote)
        conn.commit()
        total += len(lote)
        if rotulo:
            print(f"   [db] {rotulo}: {total}/{len(linhas)} linhas")
    cursor.close()
    decorrido = time.time() - inicio
    if rotulo:
        print(f"   [db] {rotulo}: {total} linhas em {decorrido:.1f}s")
    return total


# ---------------------------------------------- SELECT id por id_externo
def mapa_ids() -> dict[tuple[str, str], int]:
    """Mapa (grupo, id_externo) -> id, para alimentar a tabela de exposição."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT grupo, id_externo, id FROM gestantes_uruguaiana")
        return {(g, e): i for g, e, i in cursor.fetchall()}
    finally:
        conn.close()
