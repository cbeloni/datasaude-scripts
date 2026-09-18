from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point


SETORES = {
    "355030874000128": (-23.490073, -46.448788),
    "355030874000129": (-23.489588, -46.446908),
    "355030874000130": (-23.489589, -46.445558),
    "355030874000141": (-23.489409, -46.446869),
    "355030874000167": (-23.489014, -46.448352),
    "355030874000176": (-23.490741, -46.451299),
    "355030874000185": (-23.489720, -46.444727),
    "355030874000168": (-23.489018, -46.449844),
    "355030874000169": (-23.489704, -46.450225),
    "355030874000173": (-23.488620, -46.451515),
    "355030874000175": (-23.488465, -46.449107),
    "355030874000177": (-23.489589, -46.452267),
    "355030874000146": (-23.488686, -46.446473),
    "355030874000147": (-23.488453, -46.445619),
    "355030874000148": (-23.488088, -46.447047),
    "355030874000174": (-23.487689, -46.449774),
    "355030874000186": (-23.488829, -46.444497),
}


PASTA = Path("/Users/cauebeloni/Documents/Projeto Pensi/datasaude-scripts/geojson")
SAIDA = Path("/Users/cauebeloni/Documents/Projeto Pensi/datasaude-scripts/lapenna/setores_media_diaria.csv")


def carregar_processados():
    if not SAIDA.exists():
        return set()

    df = pd.read_csv(
        SAIDA,
        usecols=["data", "setor"],
        dtype={"setor": str},
    )

    return set(
        zip(
            df["data"],
            df["setor"],
        )
    )


def extrair_data(arquivo):
    """
    TEMP_20221018.geojson
             ↓
         2022-10-18
    """

    data_str = arquivo.stem.replace(
        "TEMP_",
        "",
    )

    return pd.to_datetime(
        data_str,
        format="%Y%m%d",
    ).date()


def processar_arquivo(arquivo):
    data = extrair_data(arquivo)

    # Lê os polígonos
    gdf = gpd.read_file(
        arquivo,
        engine="pyogrio",
    )

    # Garante WGS84
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")

    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs("EPSG:4326")

    # Cria GeoDataFrame dos setores
    setores = gpd.GeoDataFrame(
        {
            "setor": list(SETORES.keys()),
            "latitude": [
                coordenadas[0]
                for coordenadas in SETORES.values()
            ],
            "longitude": [
                coordenadas[1]
                for coordenadas in SETORES.values()
            ],
        },
        geometry=[
            Point(longitude, latitude)
            for latitude, longitude in SETORES.values()
        ],
        crs="EPSG:4326",
    )

    # Encontra o polígono que contém cada ponto
    resultado = gpd.sjoin(
        setores,
        gdf,
        how="left",
        predicate="within",
    )

    # Mantém somente as colunas necessárias
    resultado = resultado[
        [
            "setor",
            "latitude",
            "longitude",
            "media_diaria",
        ]
    ].copy()

    resultado.insert(
        0,
        "data",
        data,
    )

    return resultado


def main():

    processados = carregar_processados()

    print(
        f"Registros já processados: "
        f"{len(processados)}"
    )

    arquivos = sorted(
        PASTA.glob("TEMP_*.geojson")
    )

    print(
        f"Arquivos encontrados: "
        f"{len(arquivos)}"
    )

    for numero, arquivo in enumerate(
        arquivos,
        start=1,
    ):

        data = extrair_data(arquivo)

        # Verifica se todos os setores dessa data
        # já foram processados
        todos_processados = all(
            (data, setor) in processados
            for setor in SETORES
        )

        if todos_processados:

            print(
                f"[{numero}/{len(arquivos)}] "
                f"{arquivo.name} -> já processado"
            )

            continue

        print(
            f"[{numero}/{len(arquivos)}] "
            f"{arquivo.name}"
        )

        try:

            resultado = processar_arquivo(
                arquivo
            )

            # Remove setores que eventualmente
            # já existam no CSV
            resultado = resultado[
                ~resultado.apply(
                    lambda row: (
                        row["data"],
                        row["setor"],
                    ) in processados,
                    axis=1,
                )
            ]

            if resultado.empty:
                continue

            # Primeiro arquivo
            if SAIDA.exists():

                resultado.to_csv(
                    SAIDA,
                    mode="a",
                    header=False,
                    index=False,
                )

            else:

                resultado.to_csv(
                    SAIDA,
                    index=False,
                )

            # Atualiza checkpoint
            for _, row in resultado.iterrows():

                processados.add(
                    (
                        row["data"],
                        row["setor"],
                    )
                )

            print(
                f"    {len(resultado)} registros gravados"
            )

        except Exception as e:

            print(
                f"    ERRO: {e}"
            )


if __name__ == "__main__":
    main()