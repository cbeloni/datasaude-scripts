#!/usr/bin/env python3
"""Importa dados de setores (CSV) para tabela MySQL `maxacali`."""

from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

import mysql.connector
from dotenv import dotenv_values, load_dotenv

load_dotenv()
_config = dotenv_values('.env')

# Ajuste aqui o caminho do CSV quando for executar.
CSV_PATH = Path('/Users/cauebeloni/Documents/Projeto Pensi/dados/ibge/Agregados_por_setores_basico_BR_20250417.csv')
TABLE_NAME = 'maxacali'
BATCH_SIZE = 1000
ENCODING_CANDIDATES = ('utf-8-sig', 'utf-8', 'latin-1', 'cp1252')

TABLE_COLUMNS = [
    'cd_setor',
    'situacao',
    'cd_sit',
    'cd_tipo',
    'area_km2',
    'cd_regiao',
    'nm_regiao',
    'cd_uf',
    'nm_uf',
    'cd_mun',
    'nm_mun',
    'cd_dist',
    'nm_dist',
    'cd_subdist',
    'nm_subdist',
    'cd_bairro',
    'nm_bairro',
    'cd_nu',
    'nm_nu',
    'cd_fcu',
    'nm_fcu',
    'cd_aglom',
    'nm_aglom',
    'cd_rgint',
    'nm_rgint',
    'cd_rgi',
    'nm_rgi',
    'cd_concurb',
    'nm_concurb',
    'v0001',
    'v0002',
    'v0003',
    'v0004',
    'v0005',
    'v0006',
    'v0007',
]

INT_FIELDS = {
    'cd_sit',
    'cd_tipo',
    'cd_regiao',
    'cd_uf',
    'cd_dist',
    'cd_bairro',
    'cd_rgint',
    'cd_rgi',
    'v0001',
    'v0002',
    'v0003',
    'v0004',
    'v0007',
}

DECIMAL_FIELDS = {'area_km2', 'v0005', 'v0006'}


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


def parse_int(value: str | None) -> int | None:
    value = as_none(value)
    if value is None:
        return None
    return int(value)


def parse_decimal(value: str | None) -> Decimal | None:
    value = as_none(value)
    if value is None:
        return None
    normalized = value.replace('.', '').replace(',', '.') if ',' in value else value
    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError(f'Valor decimal invalido: {value}') from exc


def parse_value(column: str, value: str | None):
    if column in INT_FIELDS:
        return parse_int(value)
    if column in DECIMAL_FIELDS:
        return parse_decimal(value)
    return as_none(value)


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
                parsed.append(parse_value(col, raw_value))
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


def run() -> None:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f'Arquivo CSV nao encontrado: {CSV_PATH}')

    conexao = criar_conexao()
    insert_sql = build_insert_sql(TABLE_NAME)
    total = 0

    try:
        with conexao.cursor() as cursor:
            for batch in chunked(read_rows(CSV_PATH), BATCH_SIZE):
                cursor.executemany(insert_sql, batch)
                conexao.commit()
                total += len(batch)
                print(f'Lote inserido: {len(batch)} | Total: {total}')
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()

    print(f'Importacao concluida. Total de registros processados: {total}')


if __name__ == '__main__':
    run()
