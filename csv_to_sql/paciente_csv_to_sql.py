import pandas as pd
import mysql.connector
import sqlite3
from faker import Faker
from dotenv import load_dotenv, dotenv_values

load_dotenv()

_config = dotenv_values(".env")

_fake = Faker()

# Função para criar a conexão com o banco de dados
def criar_conexao():
    return mysql.connector.connect(
        host= _config['host'],
        user= _config['user'],
        password= _config['password'],
        database= _config['database'],
        ssl_ca= _config['ssl_ca'] if 'ssl_ca' in _config else None
    )

def criar_conexao_sqlite():
    return sqlite3.connect('/home/caue/Documentos/pensi_projeto/POLUENTES_PACIENTES.sqlite')

def run():
    print('executando')
    # Ler o arquivo CSV
    dados_csv = pd.read_csv('/home/caue/Documentos/pensi_projeto/Select2_PESQUISA_J00_ao_J99.csv',
                            encoding='iso-8859-1', on_bad_lines='skip')

    # Criar a conexão com o banco de dados
    conexao = criar_conexao_sqlite()

    # Criar o cursor para executar as consultas SQL
    cursor = conexao.cursor()    

    # Iterar sobre cada linha do CSV e inserir os dados na tabela 'paciente'
    for indice, linha in dados_csv.iterrows():
        cd_atendimento = linha['CD_ATENDIMENTO'] if pd.notnull(linha['CD_ATENDIMENTO']) else None
        dt_atendimento = linha['DT_ATENDIMENTO'] if pd.notnull(linha['DT_ATENDIMENTO']) else None
        tp_atendimento = linha['TP_ATENDIMENTO'] if pd.notnull(linha['TP_ATENDIMENTO']) else None
        ds_ori_ate = linha['DS_ORI_ATE'] if pd.notnull(linha['DS_ORI_ATE']) else None
        ds_leito = linha['DS_LEITO'] if pd.notnull(linha['DS_LEITO']) else None
        dt_prevista_alta = linha['DT_PREVISTA_ALTA'] if pd.notnull(linha['DT_PREVISTA_ALTA']) else None
        dt_alta = linha['DT_ALTA'] if pd.notnull(linha['DT_ALTA']) else None
        cd_sgru_cid = linha['CD_SGRU_CID'] if pd.notnull(linha['CD_SGRU_CID']) else None
        cd_cid = linha['CD_CID'] if pd.notnull(linha['CD_CID']) else None
        ds_cid = linha['DS_CID'] if pd.notnull(linha['DS_CID']) else None
        sn_internado = linha['SN_INTERNADO'] if pd.notnull(linha['SN_INTERNADO']) else None
        ds_endereco = linha['DS_ENDERECO'] if pd.notnull(linha['DS_ENDERECO']) else None
        nr_endereco = linha['NR_ENDERECO'] if pd.notnull(linha['NR_ENDERECO']) else None
        nm_bairro = linha['NM_BAIRRO'] if pd.notnull(linha['NM_BAIRRO']) else None
        nr_cep = linha['NR_CEP'] if pd.notnull(linha['NR_CEP']) else None
        dt_nasc = linha['DT_NASC'] if pd.notnull(linha['DT_NASC']) else None
        idade = linha['IDADE'] if pd.notnull(linha['IDADE']) else None
        tp_sexo = linha['TP_SEXO'] if pd.notnull(linha['TP_SEXO']) else None

        sql = """
            INSERT INTO paciente (CD_ATENDIMENTO, DT_ATENDIMENTO, TP_ATENDIMENTO, DS_ORI_ATE, DS_LEITO, DT_PREVISTA_ALTA, DT_ALTA,
            CD_SGRU_CID, CD_CID, DS_CID, SN_INTERNADO, DS_ENDERECO, NR_ENDERECO, NM_BAIRRO, NR_CEP, NM_PACIENTE, DT_NASC, IDADE, TP_SEXO)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            # Executar a consulta SQL
            cursor.execute(sql, (cd_atendimento, dt_atendimento, tp_atendimento,
                                 ds_ori_ate, ds_leito, dt_prevista_alta, dt_alta,
                                 cd_sgru_cid, cd_cid, ds_cid, sn_internado, ds_endereco,
                                 nr_endereco, nm_bairro, nr_cep, _fake.name(), dt_nasc, idade, tp_sexo))
            conexao.commit()
        except Exception as exception:
            print('error o except: {}', exception)
    conexao.close()

if __name__ == '__main__':
    run()
    