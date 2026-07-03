"""XLSX dictionary loading for IBGE sector imports."""

from __future__ import annotations

import os
import re
import zipfile
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path

try:
    from .csv_utils import clean_value, normalize_header, is_variable_header, slugify
except ImportError:  # pragma: no cover - fallback for direct script execution
    from csv_utils import clean_value, normalize_header, is_variable_header, slugify

DEFAULT_DATA_DIR = Path(
    os.getenv("IBGE_DATA_DIR", "/Users/cauebeloni/Documents/Projeto Pensi/dados/ibge")
)
DEFAULT_DICTIONARY_PATH = Path(
    os.getenv(
        "IBGE_DICTIONARY_PATH",
        str(DEFAULT_DATA_DIR / "dicionario_de_dados_agregados_por_setores_censitarios_20250417-2.xlsx"),
    )
)

XML_NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def sanitize_field_name(code: str, description: str) -> str:
    prefix = code.lower()
    desc = slugify(description)
    return f"{prefix}_{desc}" if desc else prefix


@lru_cache(maxsize=None)
def load_dictionary_mapping(
    workbook_path: str | Path,
    sheet_name: str,
) -> dict[str, str]:
    workbook_path = Path(workbook_path)
    with zipfile.ZipFile(workbook_path) as archive:
        shared_strings = _read_shared_strings(archive)
        sheet_target = _find_sheet_target(archive, sheet_name)
        rows = _read_sheet_rows(archive, sheet_target, shared_strings)

    if not rows:
        raise ValueError(f"Sheet '{sheet_name}' is empty")

    header = [normalize_header(col) for col in rows[0]]
    if "variável" in header:
        variable_idx = header.index("variável")
    elif "variavel" in header:
        variable_idx = header.index("variavel")
    else:
        raise ValueError(f"Sheet '{sheet_name}' does not contain a 'Variável' column")

    if "descrição" in header:
        description_idx = header.index("descrição")
    elif "descricao" in header:
        description_idx = header.index("descricao")
    else:
        raise ValueError(f"Sheet '{sheet_name}' does not contain a 'Descrição' column")

    mapping: dict[str, str] = {}
    for row in rows[1:]:
        if variable_idx >= len(row) or description_idx >= len(row):
            continue
        code = clean_value(row[variable_idx])
        description = clean_value(row[description_idx])
        if not code or not description:
            continue
        if not is_variable_header(code):
            continue
        mapping[code.lower()] = sanitize_field_name(code, description)
    return mapping


def _read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []

    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for si in root.findall("a:si", XML_NS):
        text = "".join(node.text or "" for node in si.iterfind(".//a:t", XML_NS))
        values.append(text)
    return values


def _find_sheet_target(archive: zipfile.ZipFile, sheet_name: str) -> str:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    rel_map = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels
        if rel.attrib.get("Target")
    }

    for sheet in workbook.find("a:sheets", XML_NS):
        if sheet.attrib.get("name") == sheet_name:
            rel_id = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
            target = rel_map[rel_id]
            if not target.startswith("xl/"):
                target = f"xl/{target}"
            return target

    available = [sheet.attrib.get("name") for sheet in workbook.find("a:sheets", XML_NS)]
    raise KeyError(f"Sheet '{sheet_name}' not found. Available sheets: {available}")


def _read_sheet_rows(
    archive: zipfile.ZipFile,
    sheet_target: str,
    shared_strings: list[str],
) -> list[list[str]]:
    root = ET.fromstring(archive.read(sheet_target))
    rows: list[list[str]] = []
    for row in root.findall(".//a:sheetData/a:row", XML_NS):
        values: list[str] = []
        for cell in row.findall("a:c", XML_NS):
            value = _read_cell_value(cell, shared_strings)
            values.append(value)
        rows.append(values)
    return rows


def _read_cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    raw_value = cell.findtext("a:v", default="", namespaces=XML_NS)
    if cell_type == "s" and raw_value:
        return shared_strings[int(raw_value)]
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.iterfind(".//a:t", XML_NS))
    return raw_value or ""
