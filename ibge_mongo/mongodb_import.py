"""MongoDB import helpers for IBGE sector datasets."""

from __future__ import annotations

import csv
import os
import time
from pathlib import Path
from typing import Iterator

try:
    from .checkpoint import clear_checkpoint, load_checkpoint, save_checkpoint
    from .csv_utils import (
        clean_value,
        collection_name_from_csv_path,
        detect_csv_dialect,
        detect_csv_encoding,
        is_variable_header,
        normalize_header,
        parse_numeric_value,
    )
    from .xlsx_dictionary import DEFAULT_DICTIONARY_PATH, load_dictionary_mapping
except ImportError:  # pragma: no cover - fallback for direct script execution
    from checkpoint import clear_checkpoint, load_checkpoint, save_checkpoint  # type: ignore[no-redef]
    from csv_utils import (  # type: ignore[no-redef]
        clean_value,
        collection_name_from_csv_path,
        detect_csv_dialect,
        detect_csv_encoding,
        is_variable_header,
        normalize_header,
        parse_numeric_value,
    )
    from xlsx_dictionary import DEFAULT_DICTIONARY_PATH, load_dictionary_mapping  # type: ignore[no-redef]

DEFAULT_MONGO_URI = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")
DEFAULT_MONGO_DATABASE = os.getenv("MONGODB_DATABASE") or os.getenv("MONGO_DB")

SPECIAL_COLUMN_NAMES = {
    "setor": "cd_setor",
    "cd_setor": "cd_setor",
}

STRING_COLUMNS = {
    "cd_setor",
    "situacao",
    "cd_sit",
    "cd_tipo",
    "cd_regiao",
    "nm_regiao",
    "cd_uf",
    "nm_uf",
    "cd_mun",
    "nm_mun",
    "cd_dist",
    "nm_dist",
    "cd_subdist",
    "nm_subdist",
    "cd_bairro",
    "nm_bairro",
    "cd_nu",
    "nm_nu",
    "cd_fcu",
    "nm_fcu",
    "cd_aglom",
    "nm_aglom",
    "cd_rgint",
    "nm_rgint",
    "cd_rgi",
    "nm_rgi",
    "cd_concurb",
    "nm_concurb",
}


def get_mongo_uri(mongo_uri: str | None = None) -> str:
    uri = mongo_uri or DEFAULT_MONGO_URI
    if not uri:
        raise ValueError(
            "MongoDB URI not configured. Set MONGODB_URI or MONGO_URI in the environment."
        )
    return uri


def get_mongo_database(mongo_database: str | None = None) -> str:
    database = mongo_database or DEFAULT_MONGO_DATABASE
    if not database:
        raise ValueError(
            "MongoDB database not configured. Set MONGODB_DATABASE or MONGO_DB in the environment."
        )
    return database


def iter_csv_rows(csv_path: Path, skip_rows: int = 0) -> tuple[list[str], Iterator[dict[str, str]]]:
    encoding = detect_csv_encoding(csv_path)
    dialect = detect_csv_dialect(csv_path, encoding)
    fp = csv_path.open("r", encoding=encoding, newline="")
    reader = csv.reader(fp, dialect=dialect)
    headers = next(reader)
    normalized_headers = [normalize_header(header) for header in headers]

    def row_iterator() -> Iterator[dict[str, str]]:
        try:
            # Skip rows that were already processed in a previous run
            for _ in range(skip_rows):
                try:
                    next(reader)
                except StopIteration:
                    return

            for raw_row in reader:
                row: dict[str, str] = {}
                for idx, header in enumerate(normalized_headers):
                    row[header] = raw_row[idx] if idx < len(raw_row) else ""
                yield row
        finally:
            fp.close()

    return normalized_headers, row_iterator()


def row_to_document(row: dict[str, str], field_mapping: dict[str, str]) -> dict[str, object]:
    document: dict[str, object] = {}
    sector_value: str | None = None

    for header, raw_value in row.items():
        target_header = SPECIAL_COLUMN_NAMES.get(header, header)
        cleaned_value = clean_value(raw_value)

        if target_header == "cd_setor":
            sector_value = cleaned_value
            document[target_header] = cleaned_value
            continue

        if header == "area_km2":
            document[target_header] = parse_numeric_value(raw_value)
            continue

        if is_variable_header(header):
            mapped_key = field_mapping.get(header)
            if mapped_key is None:
                raise KeyError(f"Variable '{header}' is missing from the dictionary mapping")
            document[mapped_key] = parse_numeric_value(raw_value)
            continue

        if target_header in STRING_COLUMNS:
            document[target_header] = cleaned_value
            continue

        document[target_header] = cleaned_value if cleaned_value is not None else None

    if sector_value is not None:
        document["_id"] = sector_value
    return document


def iter_documents(
    csv_path: Path, field_mapping: dict[str, str], skip_rows: int = 0
) -> Iterator[dict[str, object]]:
    headers, rows = iter_csv_rows(csv_path, skip_rows=skip_rows)
    missing_variables = [
        header for header in headers if is_variable_header(header) and header not in field_mapping
    ]
    if missing_variables:
        raise KeyError(
            f"CSV '{csv_path.name}' has variables that are not present in the dictionary: {missing_variables[:20]}"
        )

    for row in rows:
        yield row_to_document(row, field_mapping)


def import_csv_to_mongodb(
    *,
    csv_path: str | Path,
    sheet_name: str,
    dictionary_path: str | Path = DEFAULT_DICTIONARY_PATH,
    mongo_uri: str | None = None,
    mongo_database: str | None = None,
    batch_size: int = 1000,
    collection_name: str | None = None,
    checkpoint_interval: int = 100,
) -> int:
    from pymongo import MongoClient, ReplaceOne
    from pymongo.errors import PyMongoError

    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    csv_name = csv_path.stem

    # Resume from checkpoint if available
    checkpoint = load_checkpoint(csv_name)
    skip_rows = checkpoint if checkpoint is not None else 0

    mapping = load_dictionary_mapping(dictionary_path, sheet_name)
    collection_name = collection_name or collection_name_from_csv_path(csv_path)
    uri = get_mongo_uri(mongo_uri)
    database_name = get_mongo_database(mongo_database)
    tentativa = 1
    total = checkpoint if checkpoint is not None else 0
    operations: list[ReplaceOne] = []
    documents = iter_documents(csv_path, mapping, skip_rows=skip_rows)
    client = None
    collection = None
    index_created = False

    if checkpoint:
        print(
            f"Checkpoint encontrado: {csv_name} ja havia processado {checkpoint} linhas. "
            f"Retomando da linha {checkpoint + 1}."
        )

    while True:
        try:
            if client is None:
                print(f"Tentativa {tentativa} de conectar ao MongoDB")
                client = MongoClient(
                    uri,
                    serverSelectionTimeoutMS=1000,
                    connectTimeoutMS=1000,
                    socketTimeoutMS=1000,
                )
                client.admin.command("ping")
                print("Conexao com o MongoDB estabelecida")
                collection = client[database_name][collection_name]
                index_created = False

            if not index_created:
                collection.create_index("cd_setor", unique=True)
                index_created = True

            if operations:
                collection.bulk_write(operations, ordered=False)
                operations.clear()
                continue

            try:
                document = next(documents)
            except StopIteration:
                # Import completed successfully — clear checkpoint
                clear_checkpoint(csv_name)
                if client is not None:
                    client.close()
                return total

            sector_id = document.get("_id")
            if not sector_id:
                raise ValueError(f"Row without cd_setor in '{csv_path.name}'")

            operations.append(ReplaceOne({"_id": sector_id}, document, upsert=True))
            total += 1

            # Save checkpoint periodically
            if total % checkpoint_interval == 0:
                save_checkpoint(csv_name, total)

            if total % 1000 == 0:
                print(f"{total} documentos processados em {csv_path.name}")

            if len(operations) >= batch_size:
                continue
        except PyMongoError as error:
            print(f"Falha na tentativa {tentativa} de conexao com o MongoDB: {error}")
            print("Aguardando 1 segundo para tentar novamente")
            if client is not None:
                client.close()
                client = None
                collection = None
                index_created = False
            time.sleep(1)
            tentativa += 1
