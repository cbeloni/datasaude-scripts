from dotenv import load_dotenv, dotenv_values
from core.database import criar_conexao
from config.log_config import Log
from interpolacao.exposicao_poluente import indice_poluente_por_utm

load_dotenv()
_config = dotenv_values("../.env")
_log = Log("exposicao_poluente_massa")

def query_paciente_poluente():
    return """
        select p.ID, pc.id id_coordenada, replace(p.DT_ATENDIMENTO, '-','') dt_atendimento, pc.x, pc.y, pp.poluente, arquivo_geojson
          from paciente p,
               paciente_coordenadas pc,
               poluente_plot pp
         where p.ID = pc.id_paciente
           and replace(p.DT_ATENDIMENTO, '-','') =  pp.data_coleta
           and not exists (select 1 from paciente_interpolacao pi where pc.id = pi.id_coordenada and pp.poluente = pi.poluente)
           and pc.acuracia >= 8
           and pc.country = 'BRAZIL'
           and county in ('São Paulo', 'Região Metropolitana de São Paulo')
           order by DT_ATENDIMENTO, p.id, pp.poluente asc
           limit 100000;
    """

insert_paciente_interpolacao = """
    INSERT INTO paciente_interpolacao (id_coordenada, data, poluente, indice_interpolado)
    VALUES (%s, %s, %s, %s);
"""

if __name__ == '__main__':
    _log.info("Criando conexão")
    conexao = criar_conexao(_config)
    _log.info(f"conectado: {conexao.is_connected()}")

    cursor = conexao.cursor()
    cursor.execute(query_paciente_poluente())

    for row in cursor.fetchall():
        id, id_coordenada, dt_atendimento, x, y, poluente, arquivo_geojson = row
        indice_interpolado = indice_poluente_por_utm(x, y, arquivo_geojson, "media_diaria")
        params = (str(id_coordenada), dt_atendimento, poluente, str(indice_interpolado))
        cursor.execute(insert_paciente_interpolacao, params)
        conexao.commit()

    cursor.close()
    conexao.close()