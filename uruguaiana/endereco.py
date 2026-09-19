"""Construção da nova coluna de endereço (`endereco_ajustado`).

Premissa de projeto: TODOS os endereços são do município de Uruguaiana/RS.
O objetivo é entregar à OpenCage um texto limpo e com o município sempre presente.

Ver PLANEJAMENTO.md §E3.1.
"""

import hashlib
import re

from uruguaiana.config_uruguaiana import (
    MUNICIPIO_PADRAO,
    MUNICIPIOS_REMOVER,
    STOP_ADDRESS,
    TYPO_MUNICIPIO,
)

# Logradouros cuja duplicação deve ser colapsada (ex.: "RUA RUA MARECHAL")
_PREFIXOS = r"(RUA|AVENIDA|AV|TRAVESSA|RODOVIA|ESTRADA|BECO|ALAMEDA|PRAÇA|PRACA|LARGO|VIELA)"


def sem_endereco(endereco) -> bool:
    """True quando o valor representa 'sem endereço'."""
    if endereco is None:
        return True
    try:
        if endereco != endereco:  # NaN
            return True
    except Exception:
        pass
    return str(endereco).strip().upper() in STOP_ADDRESS


def ajustar_endereco(bruto) -> tuple[str | None, str | None]:
    """Ajusta o endereço bruto.

    Retorna ``(endereco_ajustado, ajustes)``.
    ``endereco_ajustado`` é ``None`` quando o valor é de 'sem endereço'.
    ``ajustes`` é uma string com as regras disparadas, separadas por ', '.
    """
    if sem_endereco(bruto):
        return None, None

    ajustes: list[str] = []
    s = str(bruto)

    # 1. espaços
    s_norm = re.sub(r"\s+", " ", s).strip()
    if s_norm != s:
        ajustes.append("espacos normalizados")
    s = s_norm

    # 2. separadores . ; -> ,
    if re.search(r"[.;]", s):
        s = re.sub(r"\s*[.;]+\s*", ", ", s)
        ajustes.append("separador")

    # 2b. hífen como separador de número/bairro  ("28 -TABAJARA")
    if re.search(r"\d\s*-\s*[A-Za-zÀ-ÿ]", s):
        s = re.sub(r"\s*-\s*", ", ", s)
        ajustes.append("hifen separador")

    # 3. logradouro duplicado  ("RUA RUA MARECHAL")
    s2 = re.sub(rf"\b{_PREFIXOS}\s+\1\b", r"\1", s, flags=re.IGNORECASE)
    if s2 != s:
        ajustes.append("logradouro duplicado")
    s = s2

    # 4. typos de município
    for errado, certo in TYPO_MUNICIPIO.items():
        if re.search(rf"\b{errado}\b", s, flags=re.IGNORECASE):
            s = re.sub(rf"\b{errado}\b", certo, s, flags=re.IGNORECASE)
            ajustes.append("typo municipio")

    # 5. remover menções a OUTROS municípios (todos são de Uruguaiana)
    for mun in MUNICIPIOS_REMOVER:
        if re.search(re.escape(mun), s, flags=re.IGNORECASE):
            s = re.sub(
                re.escape(mun) + r"\s*(,|-|–)?\s*(RS)?",
                "",
                s,
                flags=re.IGNORECASE,
            )
            ajustes.append("municipio vizinho removido")

    # 6. remover URUGUAIANA / RS / BRASIL residuais (serão reanexados padronizados)
    s2 = re.sub(r"[, ]*\bURUGUAIANA\b\s*(-\s*RS)?[, ]*", ", ", s, flags=re.IGNORECASE)
    if s2 != s:
        ajustes.append("municipio reanexado")
    s = s2
    s2 = re.sub(r"[, ]*\bRS\b[, ]*", ", ", s, flags=re.IGNORECASE)
    if s2 != s:
        ajustes.append("municipio reanexado")
    s = s2
    s = re.sub(r"[, ]*\bBRASIL\b[, ]*", ", ", s, flags=re.IGNORECASE)

    # 7. colapsar vírgulas repetidas e limpar as pontas
    antes = s
    s = re.sub(r"(\s*,\s*)+", ", ", s)
    s = s.strip(" ,-–")
    if s != antes:
        ajustes.append("pontuacao normalizada")

    if not s:
        return None, None

    # 8. anexar SEMPRE o município padronizado
    ajustado = f"{s}, {MUNICIPIO_PADRAO}"

    return ajustado, ", ".join(dict.fromkeys(ajustes)) if ajustes else "sem ajustes"


def hash_endereco(endereco_ajustado: str) -> str:
    """SHA1 do endereço ajustado — chave do cache de geocodificação."""
    return hashlib.sha1(endereco_ajustado.encode("utf-8")).hexdigest()
