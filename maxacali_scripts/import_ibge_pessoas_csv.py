#!/usr/bin/env python3
"""Importa dados de pessoas (CSV) para tabela MySQL `ibge_pessoas`."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

import mysql.connector
from dotenv import dotenv_values, load_dotenv

load_dotenv()
_config = dotenv_values('.env')

# Ajuste aqui o caminho do CSV quando for executar.
CSV_PATH = Path('/Users/cauebeloni/Documents/Projeto Pensi/dados/ibge/Agregados_por_setores_pessoas_indigenas_BR_filtrado.csv')
TABLE_NAME = 'ibge_pessoas'
BATCH_SIZE = 1000
ENCODING_CANDIDATES = ('utf-8-sig', 'utf-8', 'latin-1', 'cp1252')

TABLE_COLUMNS = ['cd_setor'] + [f'v{i:05d}' for i in range(1690, 1697)]


def criar_conexao():
    return mysql.connector.connect(
        host=_config['host'],
        user=_config['user'],
        password=_config['password'],
        database=_config['database'],
        ssl_ca=_config['ssl_ca'] if 'ssl_ca' in _config else None,
        autocommit=False,
    )


def normalize_header(header: str) -> str:
    return header.strip().lower()


def as_none(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if cleaned in {'', '.'}:
        return None
    return cleaned


def detect_encoding(csv_path: Path) -> str:
    for encoding in ENCODING_CANDIDATES:
        try:
            with csv_path.open('r', encoding=encoding, newline='') as fp:
                fp.read(8192)
            return encoding
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError('csv', b'', 0, 1, 'Nao foi possivel decodificar o CSV com os encodings suportados')


def read_rows(csv_path: Path) -> Iterable[tuple]:
    encoding = detect_encoding(csv_path)
    print(f'Encoding detectado: {encoding}')

    with csv_path.open('r', encoding=encoding, newline='') as fp:
        sample = fp.read(4096)
        fp.seek(0)

        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
        except csv.Error:
            dialect = csv.excel
            dialect.delimiter = ';'

        reader = csv.DictReader(fp, dialect=dialect)
        if reader.fieldnames is None:
            raise ValueError('CSV sem cabecalho')

        field_map = {normalize_header(name): name for name in reader.fieldnames}
        missing = [col for col in TABLE_COLUMNS if col not in field_map]
        if missing:
            raise ValueError(f'CSV nao contem as colunas esperadas: {missing}')

        for row in reader:
            parsed = []
            for col in TABLE_COLUMNS:
                raw_value = row.get(field_map[col])
                parsed.append(as_none(raw_value))
            yield tuple(parsed)


def build_insert_sql(table_name: str) -> str:
    cols_csv = ', '.join(TABLE_COLUMNS)
    placeholders = ', '.join(['%s'] * len(TABLE_COLUMNS))
    update_clause = ', '.join([f"{col}=VALUES({col})" for col in TABLE_COLUMNS if col != 'cd_setor'])
    return (
        f'INSERT INTO {table_name} ({cols_csv}) VALUES ({placeholders}) '
        f'ON DUPLICATE KEY UPDATE {update_clause}'
    )


def chunked(rows: Iterable[tuple], size: int) -> Iterable[list[tuple]]:
    batch: list[tuple] = []
    for row in rows:
        batch.append(row)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def carregar_cd_setor_validos(cursor) -> set[str]:
    cursor.execute('SELECT cd_setor FROM ibge')
    return {row[0] for row in cursor.fetchall()}


def filtrar_lote_por_cd_setor_existente(batch: list[tuple], cd_setores_validos: set[str]) -> list[tuple]:
    return [row for row in batch if row[0] in cd_setores_validos]


def run() -> None:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f'Arquivo CSV nao encontrado: {CSV_PATH}')

    conexao = criar_conexao()
    insert_sql = build_insert_sql(TABLE_NAME)
    total_lidos = 0
    total_inseridos = 0
    total_ignorados = 0

    try:
        with conexao.cursor() as cursor:
            cd_setores_validos = carregar_cd_setor_validos(cursor)
            print(f'cd_setor validos carregados da ibge: {len(cd_setores_validos)}')

            for batch in chunked(read_rows(CSV_PATH), BATCH_SIZE):
                total_lidos += len(batch)
                batch_filtrado = filtrar_lote_por_cd_setor_existente(batch, cd_setores_validos)
                ignorados = len(batch) - len(batch_filtrado)
                total_ignorados += ignorados

                if batch_filtrado:
                    cursor.executemany(insert_sql, batch_filtrado)
                    conexao.commit()
                    total_inseridos += len(batch_filtrado)

                print(
                    f'Lote lido: {len(batch)} | Inseridos/atualizados: {len(batch_filtrado)} | '
                    f'Ignorados (cd_setor inexistente): {ignorados} | Total inseridos: {total_inseridos}'
                )
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()

    print(
        'Importacao concluida. '
        f'Total lidos: {total_lidos} | Total inseridos/atualizados: {total_inseridos} | '
        f'Total ignorados: {total_ignorados}'
    )


if __name__ == '__main__':
    run()
