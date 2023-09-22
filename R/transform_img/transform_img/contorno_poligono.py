import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
from rasterio.transform import from_origin

# Carregue o GeoJSON
geojson_file = 'contorno_29193.geojson'
gdf = gpd.read_file(geojson_file)
polygon = gdf.geometry.iloc[0]

# Carregue a imagem TIFF
tiff_file = 'Ozônio_epsg29193.tif'
with rasterio.open(tiff_file) as src:
    image = src.read()
    transform = src.transform
    profile = src.profile

# Crie uma máscara com base no polígono
mask = geometry_mask([polygon], out_shape=image.shape[-2:], transform=transform, invert=True)

# Aplique a máscara à imagem
image_masked = image.copy()
image_masked[:, ~mask] = 255  # Define pixels fora do polígono como zero

# Salve a imagem resultante em um novo arquivo TIFF
output_tiff_file = 'imagem_com_contorno_v3.tif'
with rasterio.open(output_tiff_file, 'w', **profile) as dst:
    dst.write(image_masked)

print(f"Imagem com contorno salva em {output_tiff_file}")
