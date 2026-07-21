"""Compatibility facade for IBGE import helpers."""

from __future__ import annotations

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
        slugify,
    )
    from .mongodb_import import (
        DEFAULT_MONGO_DATABASE,
        DEFAULT_MONGO_URI,
        get_mongo_database,
        get_mongo_uri,
        import_csv_to_mongodb,
        iter_csv_rows,
        iter_documents,
        row_to_document,
    )
    from .xlsx_dictionary import DEFAULT_DICTIONARY_PATH, load_dictionary_mapping, sanitize_field_name
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
        slugify,
    )
    from mongodb_import import (  # type: ignore[no-redef]
        DEFAULT_MONGO_DATABASE,
        DEFAULT_MONGO_URI,
        get_mongo_database,
        get_mongo_uri,
        import_csv_to_mongodb,
        iter_csv_rows,
        iter_documents,
        row_to_document,
    )
    from xlsx_dictionary import DEFAULT_DICTIONARY_PATH, load_dictionary_mapping, sanitize_field_name  # type: ignore[no-redef]
