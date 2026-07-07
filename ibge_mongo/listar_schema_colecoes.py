#!/usr/bin/env python3
"""Lista o validator/schema e a estrutura inferida de todas as collections."""

from __future__ import annotations

from collections import OrderedDict
from io import StringIO
from pprint import pprint
from typing import Any
from pathlib import Path

try:
    from .mongodb_import import get_mongo_database, get_mongo_uri
except ImportError:  # pragma: no cover - fallback for direct script execution
    from mongodb_import import get_mongo_database, get_mongo_uri  # type: ignore[no-redef]

OUTPUT_FILE = Path(__file__).with_name("schema.txt")


def describe_value(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int) and not isinstance(value, bool):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        if not value:
            return "list[empty]"
        inner_types = sorted({describe_value(item) for item in value})
        return f"list[{', '.join(inner_types)}]"
    if isinstance(value, dict):
        return "dict"
    return type(value).__name__


def infer_structure(document: dict[str, Any]) -> list[tuple[str, str]]:
    ordered = OrderedDict()
    for key, value in document.items():
        if key == "_id":
            continue
        ordered[key] = describe_value(value)
    return list(ordered.items())


def main() -> None:
    from pymongo import MongoClient

    uri = get_mongo_uri()
    database_name = get_mongo_database()

    client = MongoClient(uri)
    buffer = StringIO()
    try:
        database = client[database_name]
        for coll in database.list_collections():
            buffer.write("=============================================\n")
            buffer.write(f"COLEÇÃO: {coll['name']}\n")
            buffer.write("=============================================\n")

            options = coll.get("options") or {}
            validator = options.get("validator")
            if validator:
                buffer.write("SCHEMA DE VALIDAÇÃO:\n")
                pprint(validator, stream=buffer, sort_dicts=False)
            else:
                buffer.write("SCHEMA DE VALIDAÇÃO:\n")
                buffer.write("A coleção não possui validator definido.\n")

            sample = database[coll["name"]].find_one()
            if sample:
                buffer.write("ESTRUTURA INFERIDA A PARTIR DE UM DOCUMENTO AMOSTRAL:\n")
                pprint(infer_structure(sample), stream=buffer, sort_dicts=False)
            else:
                buffer.write("A coleção está vazia; não foi possível inferir a estrutura.\n")

            buffer.write("\n")
    finally:
        client.close()

    OUTPUT_FILE.write_text(buffer.getvalue(), encoding="utf-8")
    print(f"Schema salvo em {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
