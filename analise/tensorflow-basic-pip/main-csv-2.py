import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

def salvar_csv(arquivo, linha):
    # Abra o arquivo de texto no modo de escrita e adicione a linha
    with open(arquivo, mode='a', newline='') as arquivo_txt:
        arquivo_txt.write(linha + "\n")

# Carregando o CSV
data = pd.read_csv('dados_treino_01122023.csv', delimiter=',')

# Selecionando os campos
#X = data.iloc[:, [0, 1, 2, 3, 4, 5, 17,18,	19,	20]].values
X = data.iloc[:, [0, 1, 2, 3, 4, 5, 17, 18,	19,	20]].values
y = data.iloc[:, [15]].values

# Dividindo os dados em conjuntos de treinamento e teste
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Normalizando os dados
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Criando o modelo de rede neural
model = Sequential()
model.add(Dense(units=20, activation='relu', input_dim=10))
model.add(Dense(units=1, activation='linear'))

# Compilando o modelo
model.compile(optimizer='adam', loss='mean_squared_error')

# Treinando o modelo
model.fit(X_train, y_train, epochs=50, batch_size=32, validation_data=(X_test, y_test))

# Avaliando o modelo
loss = model.evaluate(X_test, y_test)
print(f'\nTest Loss: {loss}')


dados_teste = pd.read_csv('dados_teste_01122023.csv', delimiter=',')
x_dados_teste = data.iloc[:, [0, 1, 2, 3, 4, 5, 17, 18,	19,	20]].values
y_dados_teste = data.iloc[:, [15]].values
# Fazendo previsões
predictions = model.predict(x_dados_teste)
cabeçalho = 'MP10 | NO | NO2 | O3 | TEMP | UR | outono	| inverno | primavera | verao |  gravidade | internacao | previsao'
salvar_csv('resultado_redes_neurais.csv', cabeçalho)
for index, row  in dados_teste.iterrows():
        previsao = predictions[index][0]
        campos_concatenados = f"{row[0]}|{row[1]}|{row[2]}|{row[3]}|{row[4]}|{row[5]} | {row[17]} | {row[18]} | {row[19]} | {row[20]} | {row[16]} |  {y_dados_teste[index]} |{previsao}"
        #campos_concatenados = f"{row['MP10']}|{row['NO']}|{row['NO2']}|{row['O3']}|{row['TEMP']}|{row['UR']}|{row['gravidade']}|{row['internacao']}|{previsao}"
        salvar_csv('resultado_redes_neurais.csv', campos_concatenados)
        index += 1

