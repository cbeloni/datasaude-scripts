import cv2
import numpy as np

# Carregue a imagem TIFF
imagem_tif = cv2.imread('2022-01-01 O3 (Ozônio) .tif')

# Converta a imagem para escala de cinza (se já não estiver em escala de cinza)
imagem_cinza = cv2.cvtColor(imagem_tif, cv2.COLOR_BGR2GRAY)

# Aplique um limiar (threshold) para binarizar a imagem, se necessário
# Isso ajudará na detecção de contornos em imagens com fundo claro ou escuro
ret, imagem_binaria = cv2.threshold(imagem_cinza, 127, 255, cv2.THRESH_BINARY)

# Encontre os contornos na imagem binarizada
contornos, _ = cv2.findContours(imagem_binaria, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Selecione o contorno desejado (pode ser o maior, por exemplo)
maior_contorno = max(contornos, key=cv2.contourArea)

# Crie uma cópia da imagem original para desenhar o polígono
imagem_com_contorno = imagem_tif.copy()

# Desenhe o polígono de contorno na imagem
cv2.drawContours(imagem_com_contorno, [maior_contorno], -1, (0, 255, 0), 2)

# Salve a imagem com o polígono de contorno
cv2.imwrite('imagem_com_contorno.tif', imagem_com_contorno)

# Exiba a imagem com o polígono de contorno (opcional)
cv2.imshow('Imagem com Contorno', imagem_com_contorno)
cv2.waitKey(0)
cv2.destroyAllWindows()