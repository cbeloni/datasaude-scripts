"""E1 — Extração e unificação das abas; E2 — Saneamento de datas.

Entrada : Dados_gestantes.xlsx (abas Grupo1 e Grupo_2)
Saída   : output/01_gestantes_normalizado.csv
          output/02_gestantes_datas.csv
          output/pendencias_datas.csv

Ver PLANEJAMENTO.md §E1 e §E2.
"""

import re
import warnings

import pandas as pd
from dateutil.relativedelta import relativedelta

from uruguaiana.config_uruguaiana import (
    ABAS,
    COLUNAS_CANONICAS,
    CSV_01_NORMALIZADO,
    CSV_02_DATAS,
    CSV_PEND_DATAS,
    DIR_OUTPUT,
    MESES_JANELA,
    TOLERANCIA_DIAS,
    XLSX_GESTANTES,
)


# ------------------------------------------------------------------- E1
def extrair() -> pd.DataFrame:
    """Lê as 2 abas e unifica, adicionando a coluna `grupo`."""
    if not XLSX_GESTANTES.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {XLSX_GESTANTES}")

    try:
        abas = pd.read_excel(XLSX_GESTANTES, sheet_name=None)
    except PermissionError as erro:
        raise RuntimeError(
            "Não foi possível ler o Excel. Feche o arquivo no Excel e tente de novo."
        ) from erro

    # validação 1: as abas esperadas existem
    faltando = [a for a in ABAS if a not in abas]
    if faltando:
        raise RuntimeError(f"Abas ausentes no Excel: {faltando}. Encontradas: {list(abas)}")

    partes = []
    for nome_aba in ABAS:
        bruto = abas[nome_aba]

        # validação 2: número de colunas
        if bruto.shape[1] != len(COLUNAS_CANONICAS):
            raise RuntimeError(
                f"Aba '{nome_aba}' tem {bruto.shape[1]} colunas; "
                f"esperado {len(COLUNAS_CANONICAS)}."
            )

        # Renomear POR POSIÇÃO — os cabeçalhos divergem entre as abas.
        df = bruto.copy()
        df.columns = COLUNAS_CANONICAS
        df["grupo"] = nome_aba
        partes.append(df)

    dados = pd.concat(partes, ignore_index=True)

    # validação 3: id_externo
    if dados["id_externo"].isna().any():
        raise RuntimeError("Existem registros sem id_externo.")
    duplicados = dados.duplicated(subset=["grupo", "id_externo"]).sum()
    if duplicados:
        raise RuntimeError(f"{duplicados} registros duplicados em (grupo, id_externo).")

    return dados


# ------------------------------------------------------------------- E2
def _parse_data(valor):
    """Parse tolerante: devolve Timestamp ou NaT, sem warnings."""
    if valor is None:
        return pd.NaT
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            return pd.to_datetime(str(valor).strip(), errors="coerce")
        except Exception:
            return pd.NaT


def _reparar_ano(valor_cru):
    """Tenta consertar um ano de 4 dígitos absurdo (3024 -> 2024, 1024 -> 2024)."""
    texto = str(valor_cru)
    achado = re.search(r"\b(\d{4})\b", texto)
    if not achado:
        return pd.NaT

    ano = int(achado.group(1))
    if ano > 2100:
        ano_correto = ano - 1000
    elif ano < 1950:
        ano_correto = ano + 1000
    else:
        return pd.NaT

    return _parse_data(texto.replace(achado.group(1), str(ano_correto)))


def sanear_data(valor_cru, carimbo):
    """Aplica as regras de §E2.

    Retorna ``(data_coleta, data_referencia, data_status)``.
    """
    carimbo_dia = carimbo.normalize()

    # 1. tentativa direta
    dt = _parse_data(valor_cru)
    status = "OK"

    # 2. reparo do ano
    if pd.isna(dt):
        dt = _reparar_ano(valor_cru)
        if not pd.isna(dt):
            status = "CORRIGIDA"

    # 3. não foi possível reparar
    if pd.isna(dt):
        return None, carimbo_dia, "INVALIDA"

    # 4. desvio grande em relação ao carimbo -> usa o carimbo
    if abs((dt - carimbo_dia).days) > TOLERANCIA_DIAS:
        return dt, carimbo_dia, "FALLBACK_CARIMBO"

    return dt, dt.normalize(), status


def sanear_datas(dados: pd.DataFrame) -> pd.DataFrame:
    """Aplica o saneamento e calcula a janela de exposição de 9 meses."""
    df = dados.copy()

    df["carimbo_data_hora"] = pd.to_datetime(df["carimbo_data_hora"], errors="coerce")
    if df["carimbo_data_hora"].isna().any():
        n = int(df["carimbo_data_hora"].isna().sum())
        raise RuntimeError(f"{n} registros sem carimbo de data/hora — âncora indisponível.")

    resultados = [
        sanear_data(coleta, carimbo)
        for coleta, carimbo in zip(df["data_coleta_original"], df["carimbo_data_hora"])
    ]
    df["data_coleta"] = [r[0] for r in resultados]
    df["data_referencia"] = [r[1] for r in resultados]
    df["data_status"] = [r[2] for r in resultados]

    # janela de 9 meses (calendário, não 9x30 dias)
    df["janela_inicio"] = df["data_referencia"] - pd.DateOffset(months=MESES_JANELA)
    df["janela_fim"] = df["data_referencia"]
    # +1 porque a janela é INCLUSIVA nas duas pontas: dias_janela é exatamente o
    # número de linhas diárias que a exposição deve ter (ver PLANEJAMENTO §E6).
    df["dias_janela"] = (df["janela_fim"] - df["janela_inicio"]).dt.days + 1

    # coerções para tipos limpos
    df["data_coleta"] = pd.to_datetime(df["data_coleta"]).dt.date
    df["data_referencia"] = pd.to_datetime(df["data_referencia"]).dt.date
    df["janela_inicio"] = pd.to_datetime(df["janela_inicio"]).dt.date
    df["janela_fim"] = pd.to_datetime(df["janela_fim"]).dt.date

    return df


# ------------------------------------------------------------------ main
def executar():
    DIR_OUTPUT.mkdir(parents=True, exist_ok=True)

    print("[E1] Extraindo e unificando as abas...")
    dados = extrair()
    dados.to_csv(CSV_01_NORMALIZADO, index=False)
    print(f"   {len(dados)} registros | {dados['grupo'].value_counts().to_dict()}")
    print(f"   -> {CSV_01_NORMALIZADO.relative_to(DIR_OUTPUT.parent)}")

    print("[E2] Saneando datas e calculando a janela de 9 meses...")
    limpo = sanear_datas(dados)
    limpo.to_csv(CSV_02_DATAS, index=False)

    print(f"   data_status: {limpo['data_status'].value_counts().to_dict()}")
    print(
        f"   data_referencia: {limpo['data_referencia'].min()} -> "
        f"{limpo['data_referencia'].max()}"
    )
    print(
        f"   janela_inicio mais antiga: {limpo['janela_inicio'].min()} | "
        f"janela_fim mais recente: {limpo['janela_fim'].max()}"
    )
    print(f"   dias_janela: {limpo['dias_janela'].min()}..{limpo['dias_janela'].max()}")
    print(f"   -> {CSV_02_DATAS.relative_to(DIR_OUTPUT.parent)}")

    pendencias = limpo[limpo["data_status"] != "OK"]
    if len(pendencias):
        pendencias[
            ["grupo", "id_externo", "data_coleta_original", "carimbo_data_hora",
             "data_coleta", "data_referencia", "data_status"]
        ].to_csv(CSV_PEND_DATAS, index=False)
        print(f"   {len(pendencias)} pendências -> {CSV_PEND_DATAS.name}")

    return limpo


if __name__ == "__main__":
    executar()
