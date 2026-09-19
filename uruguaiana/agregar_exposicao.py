"""E6 — Agregação diária da exposição de cada gestante.

Entrada : output/03_gestantes_geocode.csv + cache Open-Meteo
Saída   : output/06_exposicao_diaria.csv   (194.169 linhas)
          output/06b_gestantes_grade.csv   (ponto de grade efetivo por gestante)

Estratégia: como a Open-Meteo entrega o dado por célula de grade, o `resample`
diário é feito UMA VEZ POR CÉLULA (~10 no total) e depois fatiado por gestante,
em vez de 708 vezes.

Ver PLANEJAMENTO.md §E6.
"""

import pandas as pd

from uruguaiana.config_uruguaiana import (
    CSV_03_GEOCODE,
    CSV_06_EXPOSICAO,
    DIR_OUTPUT,
    HORAS_MINIMAS_VALIDAS,
    VARIAVEL_METEO,
)
from uruguaiana.openmeteo_client import (
    chave_grade,
    coletar_ar,
    coletar_temperatura,
)

CSV_GRADE = DIR_OUTPUT / "06b_gestantes_grade.csv"


def _diario(corpo: dict) -> pd.DataFrame:
    """Converte a resposta horária da Open-Meteo em um DataFrame diário."""
    horario = pd.DataFrame(corpo["hourly"])
    horario["time"] = pd.to_datetime(horario["time"])
    horario = horario.set_index("time").sort_index()

    diario = pd.DataFrame(index=horario.resample("D").size().index)
    for coluna in horario.columns:
        serie = horario[coluna]
        diario[f"{coluna}_media"] = serie.resample("D").mean()
        diario[f"{coluna}_min"] = serie.resample("D").min()
        diario[f"{coluna}_max"] = serie.resample("D").max()
        diario[f"{coluna}_horas_validas"] = serie.resample("D").count()

    return diario


def _mes_relativo(datas: pd.Series, referencia: pd.Timestamp) -> pd.Series:
    """Mês da janela de 9 meses: 1 = mais antigo, 9 = o da coleta.

    As fronteiras caem no **dia do mês da data de referência**, de modo que cada
    mês é o intervalo [dia_ref de M, dia_ref−1 de M+1]:

        mes 9 = [ref − 1 mês + 1 dia, ref]
        mes 8 = [ref − 2 meses + 1 dia, ref − 1 mês]
        ...
        mes 1 = [janela_inicio, ref − 8 meses]

    `meses_antes` é o número de aniversários mensais já completados. A correção
    do dia do mês precisa ser `>=`: no próprio dia da fronteira já se completou
    um mês. Com `<` (condição invertida) as fronteiras ficavam erradas e o mês
    pulava de 1 para 3 no dia 1, voltando para 2 no dia 2 — não monotônico.
    """
    meses_antes = (
        (referencia.year - datas.dt.year) * 12 + (referencia.month - datas.dt.month)
    )
    meses_antes = meses_antes - (datas.dt.day >= referencia.day).astype(int)
    return (9 - meses_antes).clip(lower=1, upper=9).astype(int)


def executar() -> pd.DataFrame:
    DIR_OUTPUT.mkdir(parents=True, exist_ok=True)

    gestantes = pd.read_csv(CSV_03_GEOCODE)
    gestantes["janela_inicio"] = pd.to_datetime(gestantes["janela_inicio"])
    gestantes["data_referencia"] = pd.to_datetime(gestantes["data_referencia"])

    inicio_global = gestantes["janela_inicio"].min().date().isoformat()
    fim_global = gestantes["data_referencia"].max().date().isoformat()
    print(f"[E6] {len(gestantes)} gestantes")
    print(f"   intervalo global a coletar: {inicio_global} -> {fim_global}")

    gestantes["grade"] = [
        chave_grade(lat, lng)
        for lat, lng in zip(gestantes["latitude"], gestantes["longitude"])
    ]

    celulas = sorted(gestantes["grade"].unique())
    print(f"   células de grade distintas: {len(celulas)} "
          f"(economia de {len(gestantes) * 2} -> {len(celulas) * 2} requisições)")

    blocos: list[pd.DataFrame] = []
    registros_grade: list[dict] = []

    for i, celula in enumerate(celulas, start=1):
        grupo_celula = gestantes[gestantes["grade"] == celula]
        linha_exemplo = grupo_celula.iloc[0]
        lat, lng = float(linha_exemplo["latitude"]), float(linha_exemplo["longitude"])

        print(f"   [{i}/{len(celulas)}] célula {celula} "
              f"({len(grupo_celula)} gestantes)")

        corpo_ar = coletar_ar(lat, lng, inicio_global, fim_global)
        corpo_temp = coletar_temperatura(lat, lng, inicio_global, fim_global)

        grade_ar = (corpo_ar.get("latitude"), corpo_ar.get("longitude"))
        grade_meteo = (corpo_temp.get("latitude"), corpo_temp.get("longitude"))

        diario = _diario(corpo_ar).join(_diario(corpo_temp), how="outer").sort_index()

        for registro in grupo_celula.to_dict("records"):
            referencia = pd.Timestamp(registro["data_referencia"])
            inicio = pd.Timestamp(registro["janela_inicio"])

            recorte = diario.loc[inicio:referencia]
            if recorte.empty:
                print(f"      [aviso] sem dados para {registro['id_externo']} "
                      f"({inicio.date()} .. {referencia.date()})")
                continue

            bloco = recorte.copy()
            bloco["id_externo"] = registro["id_externo"]
            bloco["grupo"] = registro["grupo"]
            bloco["data"] = bloco.index.date
            bloco["dia_relativo"] = (bloco.index - referencia).days
            bloco["mes_relativo"] = _mes_relativo(
                pd.Series(bloco.index), referencia
            ).to_numpy()
            blocos.append(bloco)

            registros_grade.append(
                {
                    "grupo": registro["grupo"],
                    "id_externo": registro["id_externo"],
                    "grade_ar_latitude": grade_ar[0],
                    "grade_ar_longitude": grade_ar[1],
                    "grade_meteo_latitude": grade_meteo[0],
                    "grade_meteo_longitude": grade_meteo[1],
                }
            )

    exposicao = pd.concat(blocos, ignore_index=True)

    # ---- montagem final das colunas
    saida = pd.DataFrame(
        {
            "id_externo": exposicao["id_externo"],
            "grupo": exposicao["grupo"],
            "data": exposicao["data"],
            "dia_relativo": exposicao["dia_relativo"].astype(int),
            "mes_relativo": exposicao["mes_relativo"].astype(int),
            "pm10_media": exposicao["pm10_media"],
            "pm10_min": exposicao["pm10_min"],
            "pm10_max": exposicao["pm10_max"],
            "pm10_horas_validas": exposicao["pm10_horas_validas"].fillna(0).astype(int),
            "pm2_5_media": exposicao["pm2_5_media"],
            "pm2_5_min": exposicao["pm2_5_min"],
            "pm2_5_max": exposicao["pm2_5_max"],
            "pm2_5_horas_validas": exposicao["pm2_5_horas_validas"].fillna(0).astype(int),
            "temperatura_media": exposicao[f"{VARIAVEL_METEO}_media"],
            "temperatura_min": exposicao[f"{VARIAVEL_METEO}_min"],
            "temperatura_max": exposicao[f"{VARIAVEL_METEO}_max"],
            "temperatura_horas_validas": exposicao[
                f"{VARIAVEL_METEO}_horas_validas"
            ].fillna(0).astype(int),
        }
    )

    saida["valido"] = (
        (saida["pm10_horas_validas"] >= HORAS_MINIMAS_VALIDAS)
        & (saida["pm2_5_horas_validas"] >= HORAS_MINIMAS_VALIDAS)
        & (saida["temperatura_horas_validas"] >= HORAS_MINIMAS_VALIDAS)
    ).astype(int)

    saida = saida.sort_values(["grupo", "id_externo", "data"], ignore_index=True)
    saida.to_csv(CSV_06_EXPOSICAO, index=False)
    pd.DataFrame(registros_grade).to_csv(CSV_GRADE, index=False)

    print(f"   linhas geradas: {len(saida)}")
    print(f"   gestantes com exposição: {saida['id_externo'].nunique()}")
    print(f"   dias válidos (valido=1): {int(saida['valido'].sum())} "
          f"({saida['valido'].mean():.1%})")
    print(f"   dia_relativo: {saida['dia_relativo'].min()} a {saida['dia_relativo'].max()}")
    print(f"   -> {CSV_06_EXPOSICAO.relative_to(DIR_OUTPUT.parent)}")
    print(f"   -> {CSV_GRADE.relative_to(DIR_OUTPUT.parent)}")

    return saida
