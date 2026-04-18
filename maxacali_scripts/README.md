# Maxacali Scripts

## Objetivo
Este diretório contém scripts para criar a tabela e importar dados do CSV para o MySQL.

Arquivos:
- `maxacali.sql`: cria a tabela `maxacali`
- `import_maxacali_csv.py`: lê o CSV e insere/atualiza os registros

## 1. Pré-requisitos
- Python 3
- Dependência `mysql-connector-python`
- Banco MySQL acessível
- Arquivo `.env` na raiz do projeto `datasaude-scripts`

## 2. Configurar variáveis de banco
No arquivo `.env` (na raiz de `datasaude-scripts`), garanta:

```env
host=SEU_HOST
user=SEU_USUARIO
password=SUA_SENHA
database=SEU_BANCO
# ssl_ca=/caminho/certificado.pem  # opcional
```

## 3. Criar a tabela no MySQL
Execute o SQL:

```bash
mysql -h SEU_HOST -u SEU_USUARIO -p SEU_BANCO < /Users/cauebeloni/Documents/Projeto\ Pensi/datasaude-scripts/maxacali_scripts/maxacali.sql
```

## 4. Configurar caminho do CSV
No arquivo `import_maxacali_csv.py`, ajuste a constante:

```python
CSV_PATH = Path('/caminho/do/seu/arquivo.csv')
```

## 5. Executar importação

```bash
python3 /Users/cauebeloni/Documents/Projeto\ Pensi/datasaude-scripts/maxacali_scripts/import_maxacali_csv.py
```

## 6. Comportamento da carga
- Lê o CSV com autodetecção de delimitador (`;`, `,` ou tab)
- Converte `.` e vazio para `NULL`
- Converte vírgula decimal para ponto nos campos numéricos
- Insere em lote
- Se `cd_setor` já existir, atualiza os demais campos (`ON DUPLICATE KEY UPDATE`)

## 7. Erros comuns
- `Arquivo CSV nao encontrado`: ajuste `CSV_PATH`
- `Access denied`: valide `host/user/password`
- `Unknown database`: valide `database`
- `CSV nao contem as colunas esperadas`: confira cabeçalho do CSV
