from datetime import timedelta
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.database import criar_conexao


def query_datas():
    return """
            select pb.id_paciente, pb.data_atendimento from  paciente_bronquiolite pb
            where not exists (select 1 from paciente_bronquiolite_datas pbd where pb.id_paciente  = pbd.id_paciente)
            """


def get_insert_query():
    return "INSERT INTO paciente_bronquiolite_datas (id_paciente, data_atendimento) VALUES (%s, %s)"


def main():
    conexao = criar_conexao()
    cursor = conexao.cursor()

    query_gerar_csv = query_datas()
    cursor.execute(query_gerar_csv)
    results = cursor.fetchall()
    for row in results:
        (id_paciente, data_atendimento) = row
        for i in range(1, 7):
            data_insert = data_atendimento + timedelta(days=i)
            cursor.execute(get_insert_query(), (id_paciente, data_insert))
            conexao.commit()
