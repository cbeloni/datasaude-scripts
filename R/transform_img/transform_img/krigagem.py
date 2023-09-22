import numpy as np
from pyinterpolate.semivariance import calculate_semivariance
from pyinterpolate.kriging import Krige
import matplotlib.pyplot as plt

# Dados de exemplo
data = np.array([
    [0, 0, 10],
    [1, 0, 12],
    [2, 0, 8],
    [0, 1, 15],
    [1, 1, 18],
    [2, 1, 14],
    [0, 2, 5],
    [1, 2, 9],
    [2, 2, 6]
])

# Variograma experimental
lag = 1  # Distância de lag
azimuth = 0  # Ângulo de azimute (0 graus = leste)
semivariance = calculate_semivariance(data, lag, azimuth)

# Ajustar o modelo de variograma
model = "spherical"  # Modelo de variograma (outras opções incluem "exponential" e "gaussian")
nugget = 0  # Valor de nugget
sill = 20  # Valor de sill
range_a = 1.5  # Alcance do variograma

# Criar o objeto Krige
krige = Krige(data, model, sill, range_a, nugget)

# Fazer a krigagem em um ponto de grade
grid = np.array([[x, y] for x in np.arange(0, 3, 0.1) for y in np.arange(0, 3, 0.1)])
predictions = krige.ordinary_kriging(grid)

# Plotar os resultados
plt.scatter(data[:, 0], data[:, 1], c=data[:, 2], cmap='viridis', marker='o', label='Dados Observados')
plt.scatter(grid[:, 0], grid[:, 1], c=predictions, cmap='viridis', marker='.', label='Krigagem')
plt.xlabel('X')
plt.ylabel('Y')
plt.legend()
plt.colorbar(label='Valor')
plt.title('Krigagem com Pyinterpolate')
plt.show()
