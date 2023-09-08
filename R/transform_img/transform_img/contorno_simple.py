import rasterio
from rasterio.features import geometry_mask
from shapely.geometry import Polygon

# Suponha que temos uma imagem raster chamada "imagem.tif" e uma geometria no formato de um polígono.
# Vamos criar uma geometria de exemplo para demonstração.
polygon = Polygon([(0, 0), (0, 2), (2, 2), (2, 0)])

# Carregue a imagem raster usando rasterio.
with rasterio.open("Ozônio_epsg29193.tif") as src:
    # Use a função geometry_mask para criar uma máscara a partir da geometria e dos metadados da imagem.
    image = src.read()
    mask = geometry_mask([polygon], out_shape=src.shape, transform=src.transform, invert=True)
    profile = src.profile

# Agora, a variável "mask" contém uma máscara booleana onde os pixels dentro da geometria são True e os pixels fora são False.

image_masked = image.copy()
#image_masked[:, ~mask] = 255  # Define pixels fora do polígono como zero

# Salve a imagem resultante em um novo arquivo TIFF
output_tiff_file = 'imagem_com_contorno_v3.tif'
with rasterio.open(output_tiff_file, 'w', **profile) as dst:
    dst.write(image_masked)

