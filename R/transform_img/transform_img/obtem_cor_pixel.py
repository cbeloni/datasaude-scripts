import rasterio

# Carrega a imagem TIFF
tiff_file = 'mp10_discreto_sem_transparencia.tif'
with rasterio.open(tiff_file) as src:
    transform = src.transform
    profile = src.profile

# Coordenadas UTM
utm_x = 333274
utm_y = 7365201

# Converta as coordenadas UTM para coordenadas de pixel na imagem
pixel_x, pixel_y = ~transform * (utm_x, utm_y)

# Leia a imagem como uma matriz numpy
with rasterio.open(tiff_file) as src:
    image = src.read()

# Obtenha a cor do pixel nas coordenadas de pixel
if 0 <= pixel_x < image.shape[2] and 0 <= pixel_y < image.shape[1]:
    color = image[:3, int(pixel_y), int(pixel_x)]  # Obtém a cor do pixel
else:
    color = None  # Coordenadas UTM fora da imagem

print("Cor do pixel (bandas RGB):", ', '.join(map(str, color)))
