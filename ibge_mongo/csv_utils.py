"""CSV utilities for IBGE sector imports."""

from __future__ import annotations

import csv
import os
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path

DEFAULT_DATA_DIR = Path(
    os.getenv("IBGE_DATA_DIR", "/Users/cauebeloni/Documents/Projeto Pensi/dados/ibge")
)

CSV_ENCODING_CANDIDATES = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
CSV_DELIMITER_CANDIDATES = (",", ";", "\t")

VARIABLE_CODE_RE = re.compile(r"^v\d+$", re.IGNORECASE)
INTEGER_RE = re.compile(r"^[+-]?\d+$")
DECIMAL_RE = re.compile(r"^[+-]?\d+[.,]\d+$")


def normalize_header(header: str) -> str:
    return header.strip().strip('"').strip("'").lower()


def collection_name_from_csv_path(csv_path: Path) -> str:
    name = csv_path.stem
    if name.startswith("Agregados_por_"):
        name = name.removeprefix("Agregados_por_")
    return name.lower()


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^a-z0-9]+", "_", ascii_text)
    ascii_text = re.sub(r"_+", "_", ascii_text).strip("_")
    return ascii_text


def clean_value(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if cleaned in {"", "."}:
        return None
    return cleaned


def parse_numeric_value(value: str | None):
    cleaned = clean_value(value)
    if cleaned is None:
        return None
    if INTEGER_RE.match(cleaned):
        try:
            return int(cleaned)
        except ValueError:
            return cleaned
    if DECIMAL_RE.match(cleaned):
        normalized = cleaned.replace(".", "").replace(",", ".") if "," in cleaned else cleaned
        try:
            return float(Decimal(normalized))
        except (InvalidOperation, ValueError):
            return cleaned
    return cleaned


def is_variable_header(header: str) -> bool:
    return bool(VARIABLE_CODE_RE.match(header))


def detect_csv_encoding(csv_path: Path) -> str:
    for encoding in CSV_ENCODING_CANDIDATES:
        try:
            with csv_path.open("r", encoding=encoding, newline="") as fp:
                fp.read(8192)
            return encoding
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("csv", b"", 0, 1, "Could not decode CSV with supported encodings")


def detect_csv_dialect(csv_path: Path, encoding: str) -> csv.Dialect:
    with csv_path.open("r", encoding=encoding, newline="") as fp:
        sample = fp.read(8192)

    try:
        return csv.Sniffer().sniff(sample, delimiters="".join(CSV_DELIMITER_CANDIDATES))
    except csv.Error:
        class FallbackDialect(csv.excel):
            delimiter = ";"

        return FallbackDialect

