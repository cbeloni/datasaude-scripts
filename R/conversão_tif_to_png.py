from PIL import Image

imagem_tif = Image.open("2022-01-01 O3 (Ozônio) .tif")
imagem_tif.save("2022-01-01 O3 (Ozônio).png", "PNG")
imagem_tif.close()

imagem_png = Image.open("2022-01-01 O3 (Ozônio).png")

transparencia = 255  # # transparência restante em 100% 
mascara_transparencia = imagem_png.convert("L").point(lambda p: p < transparencia and 190) # transparência parte branca em 50%
imagem_png.putalpha(mascara_transparencia)

imagem_png.save("2022-01-01 O3 (Ozônio)_transparência.png")
imagem_png.close()