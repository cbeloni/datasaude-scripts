#!/usr/bin/env python3
"""Importa Agregados_por_setores_cor_ou_raca_BR.csv para MongoDB."""

from __future__ import annotations

from pathlib import Path

from mongodb_import import import_csv_to_mongodb

CSV_PATH = Path("/Users/cauebeloni/Documents/Projeto Pensi/dados/ibge/Agregados_por_setores_cor_ou_raca_BR.csv")
SHEET_NAME = "Dicionário não PCT"


def main() -> None:
    imported = import_csv_to_mongodb(csv_path=CSV_PATH, sheet_name=SHEET_NAME)
    print(f"Importacao concluida: {CSV_PATH.name} -> setores_cor_ou_raca_br")
    print(f"Total processado: {imported}")


if __name__ == "__main__":
    main()
