import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from pyinterpolate.idw import inverse_distance_weighting
from matplotlib.colors import ListedColormap
import rasterio
from rasterio import features
from rasterio.transform import from_origin
from matplotlib.colors import LinearSegmentedColormap


def ler_fontes(amostra_file, contorno_file):
    readings = pd.read_csv(amostra_file, index_col='id')
    canvas = gpd.read_file(contorno_file)
    canvas['points'] = canvas.centroid
    return readings, canvas

def plotar_amostra(garr,ax):
    garr.set_geometry = 'geometry'
    garr.plot(ax=ax, column=0, legend=False, vmin=10, vmax=50, cmap='coolwarm')
    plt.show()

def idw_apply(x, known, nn=-1, power=1):
    pred = inverse_distance_weighting(known, np.array([x.x, x.y]), nn, power)
    return pd.Series([x, pred])

def gera_png(geo_json_output_path, output_png_path):
    gdf = gpd.read_file(geo_json_output_path)
    colors = ['#008000', '#FFFF00', '#FFA500', '#FF0000', '#800080']
    #cmap = ListedColormap(colors)
    cmap = LinearSegmentedColormap.from_list('custom_colormap', colors, N=256)
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_axis_off()
    ax.set_xlim(df.geometry.total_bounds[0], df.geometry.total_bounds[2])
    ax.set_ylim(df.geometry.total_bounds[1], df.geometry.total_bounds[3])
    gdf.plot(column='yhat', ax=ax, legend=False, cmap=cmap, vmin=10, vmax=50)
    plt.tight_layout()
    plt.savefig(output_png_path, dpi=300, bbox_inches='tight', pad_inches=0.1)
    print(f'Imagem salva em {output_png_path}')

def gera_transparencia(output_filename_transparente):
    imagem_png = Image.open(output_png_path)

    transparencia = 255  # transparência parte branca em 100%
    mascara_transparencia = imagem_png.convert("L").point(
        lambda p: p < transparencia and 190)  # transparência restante em 50%
    imagem_png.putalpha(mascara_transparencia)

    imagem_png.save(output_filename_transparente)
    imagem_png.close()

def gera_geotif():
    # Lê o arquivo GeoJSON
    file_path = "output/mapa_poluentes.geojson"
    gdf = gpd.read_file(file_path)

    # Define as cores e o mapa de cores
    colors = ['#008000', '#FFFF00', '#FFA500', '#FF0000', '#800080']
    cmap = ListedColormap(colors)

    # Cria uma figura e eixos matplotlib
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_axis_off()

    # Plota o GeoDataFrame no eixo
    gdf.plot(column='yhat', ax=ax, legend=False, cmap=cmap, vmin=10, vmax=50)

    # Define o nome do arquivo de saída GeoTIFF
    output_filename = 'output/output_image.tif'

    # Obtém a extensão e resolução da imagem a partir do GeoDataFrame
    minx, miny, maxx, maxy = gdf.total_bounds
    width, height = 1000, 1000  # Especifique a resolução desejada em pixels

    # Calcula a transformação para a imagem raster
    transform = from_origin(minx, maxy, (maxx - minx) / width, (maxy - miny) / height)

    # Cria um arquivo GeoTIFF e escreve os dados do GeoDataFrame nele
    with rasterio.open(output_filename, 'w', driver='GTiff', width=width, height=height, count=1, dtype=rasterio.uint8,
                       crs=gdf.crs, transform=transform) as dst:
        for geom, val in zip(gdf.geometry, gdf['yhat']):
            shapes = [(geom, val)]
            rasterio.features.shapes(source=shapes, transform=transform, out=dst, fill=val)

    plt.show()

def interpolar(amostra_file, campo_amostra, contorno_file, vmin, vmax):
    readings, canvas = ler_fontes(amostra_file, contorno_file)

    POWER = 3
    READING = campo_amostra
    sample = readings[['x', 'y', READING]]
    arr = sample.dropna().values
    arr[:3]

    geometries = gpd.points_from_xy(x=arr[:, 0], y=arr[:, 1])
    garr = gpd.GeoDataFrame(arr[:, -1])
    garr['geometry'] = geometries
    garr.head()

    fig, ax = plt.subplots(figsize=(10, 10))

    # plotar_amostra(garr, ax)

    # Predict
    predicted = canvas['points'].apply(idw_apply, known=arr, power=POWER)
    predicted.columns = ['coordinates', 'yhat']

    colors = ['#008000', '#FFFF00', '#FFA500', '#FF0000', '#800080']
    #cmap = ListedColormap(colors)
    cmap = LinearSegmentedColormap.from_list('custom_colormap', colors, N=256)

    df = canvas.join(predicted)
    df = df[['geometry', 'yhat']]
    ax.set_axis_off()
    ax = df.plot(column='yhat', legend=False, vmin=vmin, vmax=vmax, figsize=(10, 10), cmap=cmap, ax=ax)

    plt.tight_layout()
    plt.show()
    return df


if __name__ == '__main__':
    vmin = 10
    vmax = 50
    poluente = 'mp10'
    data = '20220101'
    nome_arquivo = f'poluente_{poluente}_{data}'
    df = interpolar(f'amostra/amostra_{nome_arquivo}.csv',
                    poluente,
                    'contorno/hexgrid_v2.shp',
                    vmin,
                    vmax)

    # output_file = "output/shapefile"
    # df.to_file(output_file)

    geo_json_output_path = f"output/{nome_arquivo}.geojson"
    df.to_file(geo_json_output_path, driver="GeoJSON")

    output_png_path = f'output/{nome_arquivo}.png'
    gera_png(geo_json_output_path, output_png_path)

    output_filename_transparente = f'output/{nome_arquivo}.png'
    gera_transparencia(output_filename_transparente)
