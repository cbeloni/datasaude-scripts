from config.log_config import Log

from shapely.geometry import Point
import geopandas as gpd

_log = Log("exposicao_poluente")

def indice_poluente_por_utm(x, y, arquivo_geojson):
    point_utm = Point(x, y)

    gdf = gpd.read_file(arquivo_geojson)
    result = gdf.contains(point_utm)

    if result.any():
        return gdf.loc[result, "yhat"].values[0]

    _log.error("O ponto UTM não está dentro do polígono.")
    return 0

if __name__ == '__main__':
    poluente = 'mp10'
    data = '20220101'
    nome_arquivo = f'poluente_{poluente}_{data}'
    arquivo_geojson = f'output/{nome_arquivo}.geojson'
    indice = indice_poluente_por_utm(319367, 7384421, arquivo_geojson)
    _log.info(f"O valor de exposição do poluente para o ponto UTM é: {indice}")
