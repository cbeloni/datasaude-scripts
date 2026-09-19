"""E4 e E7 — Carga das tabelas `gestantes_uruguaiana` e `gestantes_exposicao_diaria`.

Ambas as cargas usam UPSERT sobre a chave única, portanto são idempotentes:
reexecutar o pipeline não duplica nem altera contagens.

Ver PLANEJAMENTO.md §E4 e §E7.
"""

import pandas as pd

from uruguaiana.config_uruguaiana import (
    CSV_03_GEOCODE,
    CSV_06_EXPOSICAO,
    CSV_02_DATAS,
    DIR_OUTPUT,
    XLSX_GESTANTES,
)
from uruguaiana.repositorio import (
    conectar,
    executar_em_lotes,
    mapa_ids,
)

CSV_GRADE = DIR_OUTPUT / "06b_gestantes_grade.csv"

# ---------------------------------------------------------- gestantes (E4)
COLUNAS_GESTANTES = [
    "id_externo",
    "grupo",
    "origem_arquivo",
    "carimbo_data_hora",
    "data_coleta_original",
    "data_coleta",
    "data_referencia",
    "data_status",
    "janela_inicio",
    "janela_fim",
    "dias_janela",
    "endereco_original",
    "endereco_ajustado",
    "endereco_ajuste",
    "endereco_hash",
    "latitude",
    "longitude",
    "geo_confianca",
    "geo_formatado",
    "geo_status",
    "geo_default",
    "geo_nivel",
    "geo_provider",
    "geo_city",
    "geo_state",
    "geo_country",
    "geo_postcode",
    "geo_suburb",
    "geo_data_hora",
    "grade_ar_latitude",
    "grade_ar_longitude",
    "grade_meteo_latitude",
    "grade_meteo_longitude",
    "exposicao_status",
    "dias_com_exposicao",
    "validado",
]

_ATUALIZAVEIS_G = [
    c
    for c in COLUNAS_GESTANTES
    # chave: nunca atualizar
    if c not in ("grupo", "id_externo")
    # colunas DERIVADAS, calculadas pelo E7 a partir da tabela de exposição.
    # Se o E4 as sobrescrevesse, reexecutar a carga de gestantes apagaria o
    # resultado do E7. São gravadas no INSERT (NULL) e mantidas no UPDATE.
    and c not in ("exposicao_status", "dias_com_exposicao")
]

SQL_UPSERT_GESTANTES = (
    f"INSERT INTO gestantes_uruguaiana ({', '.join(COLUNAS_GESTANTES)}) "
    f"VALUES ({', '.join(['%s'] * len(COLUNAS_GESTANTES))}) "
    "ON DUPLICATE KEY UPDATE "
    + ", ".join(f"{c} = VALUES({c})" for c in _ATUALIZAVEIS_G)
)

# --------------------------------------------------------- exposição (E7)
COLUNAS_EXPOSICAO = [
    "id_gestante",
    "grupo",
    "id_externo",
    "data",
    "dia_relativo",
    "mes_relativo",
    "pm10_media",
    "pm10_min",
    "pm10_max",
    "pm10_horas_validas",
    "pm2_5_media",
    "pm2_5_min",
    "pm2_5_max",
    "pm2_5_horas_validas",
    "temperatura_media",
    "temperatura_min",
    "temperatura_max",
    "temperatura_horas_validas",
    "valido",
]

_ATUALIZAVEIS_E = [
    c for c in COLUNAS_EXPOSICAO if c not in ("id_gestante", "grupo", "id_externo")
]

SQL_UPSERT_EXPOSICAO = (
    f"INSERT INTO gestantes_exposicao_diaria ({', '.join(COLUNAS_EXPOSICAO)}) "
    f"VALUES ({', '.join(['%s'] * len(COLUNAS_EXPOSICAO))}) "
    "ON DUPLICATE KEY UPDATE "
    + ", ".join(f"{c} = VALUES({c})" for c in _ATUALIZAVEIS_E)
)

SQL_ATUALIZA_STATUS = """
UPDATE gestantes_uruguaiana g
LEFT JOIN (
    SELECT id_gestante, COUNT(*) AS n
      FROM gestantes_exposicao_diaria
     GROUP BY id_gestante
) e ON e.id_gestante = g.id
   SET g.dias_com_exposicao = COALESCE(e.n, 0),
       g.exposicao_status   = CASE
           WHEN COALESCE(e.n, 0) = 0              THEN 'SEM_COBERTURA'
           WHEN COALESCE(e.n, 0) >= g.dias_janela THEN 'COMPLETA'
           ELSE 'PARCIAL'
       END
"""


# ------------------------------------------------------------------ helpers
def _preparar_gestantes() -> pd.DataFrame:
    # O CSV 03 (geocodificação) é derivado do CSV 02 (datas) pelo E3. Se o E2 for
    # reexecutado sem reexecutar o E3, o CSV 03 carrega as datas ANTIGAS. Para não
    # depender da ordem de execução, as colunas de data/janela são SEMPRE relidas
    # do CSV 02, que é a fonte autoritativa.
    datas = pd.read_csv(CSV_02_DATAS)
    df = pd.read_csv(CSV_03_GEOCODE)

    colunas_datas = [
        "carimbo_data_hora",
        "data_coleta_original",
        "data_coleta",
        "data_referencia",
        "data_status",
        "janela_inicio",
        "janela_fim",
        "dias_janela",
    ]
    df = df.drop(columns=[c for c in colunas_datas if c in df.columns]).merge(
        datas, on=["grupo", "id_externo"], how="left"
    )

    # ponto de grade efetivo (calculado no E6)
    if CSV_GRADE.exists():
        df = df.merge(pd.read_csv(CSV_GRADE), on=["grupo", "id_externo"], how="left")
    for coluna in (
        "grade_ar_latitude", "grade_ar_longitude",
        "grade_meteo_latitude", "grade_meteo_longitude",
    ):
        if coluna not in df.columns:
            df[coluna] = None

    df["origem_arquivo"] = str(XLSX_GESTANTES)
    df["geo_provider"] = "opencage"

    # normalização de nomes de coluna vindos dos CSVs
    renomear = {
        "confianca": "geo_confianca",
        "formatado": "geo_formatado",
        "nivel": "geo_nivel",
    }
    df = df.rename(columns={k: v for k, v in renomear.items() if k in df.columns})

    for coluna in COLUNAS_GESTANTES:
        if coluna not in df.columns:
            df[coluna] = None

    df["validado"] = 0
    df["exposicao_status"] = None
    df["dias_com_exposicao"] = None

    return df[COLUNAS_GESTANTES]


def carregar_gestantes() -> int:
    print("[E4] Carregando gestantes...")
    df = _preparar_gestantes()

    linhas = [list(registro.values()) for registro in df.to_dict("records")]

    conn = conectar()
    try:
        total = executar_em_lotes(
            conn, SQL_UPSERT_GESTANTES, linhas, 500, rotulo="gestantes_uruguaiana"
        )
    finally:
        conn.close()

    return total


def carregar_exposicao() -> int:
    print("[E7] Carregando exposição diária...")

    exposicao = pd.read_csv(CSV_06_EXPOSICAO)
    ids = mapa_ids()

    exposicao["id_gestante"] = [
        ids.get((g, e)) for g, e in zip(exposicao["grupo"], exposicao["id_externo"])
    ]

    orfaos = int(exposicao["id_gestante"].isna().sum())
    if orfaos:
        raise RuntimeError(
            f"{orfaos} linhas de exposição sem gestante correspondente. "
            "Rode a etapa 4 antes."
        )
    exposicao["id_gestante"] = exposicao["id_gestante"].astype(int)

    linhas = [
        [registro[c] for c in COLUNAS_EXPOSICAO]
        for registro in exposicao.to_dict("records")
    ]

    conn = conectar()
    try:
        total = executar_em_lotes(
            conn, SQL_UPSERT_EXPOSICAO, linhas, 5000, rotulo="gestantes_exposicao_diaria"
        )
        print("   Atualizando exposicao_status / dias_com_exposicao...")
        cursor = conn.cursor()
        cursor.execute(SQL_ATUALIZA_STATUS)
        conn.commit()
        cursor.close()
    finally:
        conn.close()

    return total


def resumo_banco() -> dict:
    conn = conectar()
    try:
        cursor = conn.cursor()
        resumo = {}
        cursor.execute("SELECT COUNT(*) FROM gestantes_uruguaiana")
        resumo["gestantes"] = cursor.fetchone()[0]
        cursor.execute("SELECT grupo, COUNT(*) FROM gestantes_uruguaiana GROUP BY grupo")
        resumo["por_grupo"] = dict(cursor.fetchall())
        cursor.execute("SELECT geo_status, COUNT(*) FROM gestantes_uruguaiana GROUP BY geo_status")
        resumo["geo_status"] = dict(cursor.fetchall())
        cursor.execute("SELECT data_status, COUNT(*) FROM gestantes_uruguaiana GROUP BY data_status")
        resumo["data_status"] = dict(cursor.fetchall())
        cursor.execute("SELECT geo_default, COUNT(*) FROM gestantes_uruguaiana GROUP BY geo_default")
        resumo["geo_default"] = dict(cursor.fetchall())
        cursor.execute("SELECT COUNT(*) FROM gestantes_exposicao_diaria")
        resumo["exposicao"] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT id_gestante) FROM gestantes_exposicao_diaria")
        resumo["gestantes_com_exposicao"] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM geocode_cache")
        resumo["geocode_cache"] = cursor.fetchone()[0]
        cursor.execute("SELECT MIN(dias_janela), MAX(dias_janela) FROM gestantes_uruguaiana")
        resumo["dias_janela"] = cursor.fetchone()
        cursor.execute(
            "SELECT COUNT(*) FROM gestantes_uruguaiana WHERE latitude IS NULL OR longitude IS NULL"
        )
        resumo["sem_coordenada"] = cursor.fetchone()[0]
        cursor.execute(
            "SELECT COUNT(*) FROM gestantes_uruguaiana WHERE exposicao_status IS NULL"
        )
        resumo["sem_exposicao_status"] = cursor.fetchone()[0]

        # --- contiguidade da série temporal (ver PLANEJAMENTO §13)
        cursor.execute(
            "SELECT COUNT(*) FROM ("
            "  SELECT mes_relativo - LAG(mes_relativo) OVER ("
            "           PARTITION BY id_gestante ORDER BY data) AS d"
            "    FROM gestantes_exposicao_diaria) t"
            " WHERE d IS NOT NULL AND (d < 0 OR d > 1)"
        )
        resumo["mes_nao_contiguo"] = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM ("
            "  SELECT id_gestante FROM gestantes_exposicao_diaria"
            "   GROUP BY id_gestante HAVING COUNT(DISTINCT mes_relativo) <> 9) t"
        )
        resumo["gestantes_sem_9_meses"] = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM ("
            "  SELECT dia_relativo - LAG(dia_relativo) OVER ("
            "           PARTITION BY id_gestante ORDER BY data) AS d"
            "    FROM gestantes_exposicao_diaria) t"
            " WHERE d IS NOT NULL AND d <> 1"
        )
        resumo["dias_nao_contiguos"] = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM gestantes_exposicao_diaria"
            " WHERE dia_relativo = 0 AND mes_relativo <> 9"
        )
        resumo["coleta_fora_do_mes_9"] = cursor.fetchone()[0]

        return resumo
    finally:
        conn.close()
