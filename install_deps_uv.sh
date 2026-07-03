#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
REQUIREMENTS_FILE="${ROOT_DIR}/requirements.txt"
ACTIVATE_SCRIPT="${VENV_DIR}/bin/activate"
PYTHON_BIN="${VENV_DIR}/bin/python"

if ! command -v uv >/dev/null 2>&1; then
  echo "Erro: 'uv' nao encontrado no PATH." >&2
  echo "Instale o uv e execute este script novamente." >&2
  exit 1
fi

cd "${ROOT_DIR}"

if [[ ! -d "${VENV_DIR}" ]]; then
  uv venv "${VENV_DIR}"
fi

if [[ -f "${ACTIVATE_SCRIPT}" ]]; then
  # shellcheck disable=SC1090
  source "${ACTIVATE_SCRIPT}"
  export PATH="${VENV_DIR}/bin:${PATH}"
  hash -r
else
  echo "Erro: nao foi possivel localizar o arquivo de ativacao do venv." >&2
  exit 1
fi

uv pip install --python "${PYTHON_BIN}" -r "${REQUIREMENTS_FILE}"

echo "Dependencias instaladas com sucesso em ${VENV_DIR}."

if [[ $# -gt 0 ]]; then
  "${PYTHON_BIN}" "$@"
fi
