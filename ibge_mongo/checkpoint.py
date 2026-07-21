"""Checkpoint tracking for long-running CSV imports.

Saves the last processed row number to a JSON file so that an import
can be interrupted and resumed without starting over.
"""

from __future__ import annotations

import json
from pathlib import Path

CHECKPOINT_DIR = Path(
    "/Users/cauebeloni/Documents/Projeto Pensi/dados/ibge/.checkpoints"
)


def _checkpoint_path(csv_name: str) -> Path:
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    return CHECKPOINT_DIR / f"{csv_name}.json"


def load_checkpoint(csv_name: str) -> int | None:
    """Return the number of data rows already processed, or *None*."""
    ckpt = _checkpoint_path(csv_name)
    if not ckpt.exists():
        return None
    try:
        data = json.loads(ckpt.read_text(encoding="utf-8"))
        return int(data["linha"])
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def save_checkpoint(csv_name: str, linha: int) -> None:
    """Persist *linha* as the last successfully processed data row."""
    ckpt = _checkpoint_path(csv_name)
    ckpt.write_text(json.dumps({"linha": linha}, indent=2, ensure_ascii=False))


def clear_checkpoint(csv_name: str) -> None:
    """Remove the checkpoint file (import finished successfully)."""
    ckpt = _checkpoint_path(csv_name)
    if ckpt.exists():
        ckpt.unlink()