import boto3
from dotenv import load_dotenv, dotenv_values
from core.database import criar_conexao
from config.log_config import Log

load_dotenv()
_config = dotenv_values("../.env")
_log = Log("gestor_arquivos")
_PATH_VOLUME = _config['PATH_VOLUME']

_s3_client = boto3.client('s3',
                          aws_access_key_id=_config['aws_access_key_id'],
                          aws_secret_access_key=_config['aws_secret_access_key'],
                          endpoint_url=_config['endpoint_url'])

def enviar(bucket_name: str, file_path: str, object_name: str, content_type: str, ):
    extra_args = {'ContentType': content_type}
    _s3_client.upload_file(file_path, bucket_name, object_name, ExtraArgs=extra_args)

def listar(bucket_name: str):
    response = _s3_client.list_objects_v2(Bucket=bucket_name)

    if 'Contents' in response:
        for obj in response['Contents']:
            print(obj['Key'])
            if "1_Krig_media_mp10_2_1" == obj['Key'] or "1_Krig_media_mp10_2_1.png" == obj['Key']:
                continue
            remover('maps-pub', obj['Key'])
    else:
        print('O bucket está vazio.')
        
def remover(bucket_name: str, key: str):
    bucket_name = bucket_name
    object_key = key

    return _s3_client.delete_object(Bucket=bucket_name, Key=object_key)

def query_poluente_plot():
    return """
        select id, arquivo_escala_fixa_png, arquivo_escala_movel_png 
         from poluente_plot
         where bucket_movel is null or bucket_fixa is null;
    """

update_poluente_plot = """
    UPDATE poluente_plot 
    set bucket_fixa = %s, bucket_movel = %s  
    where id = %s;
"""

def encurta_nome(file_name):
    path, file_name = file_name.rsplit('/', 1)
    file_parts = file_name.split("_")
    new_file_name = "_".join(file_parts[:2]) + "." + file_name.split(".")[-1]
    new_file_path = path + "/" + new_file_name
    return new_file_path

if __name__ == '__main__':
    _log.info("Criando conexão")
    conexao = criar_conexao(_config)
    _log.info(f"conectado: {conexao.is_connected()}")

    cursor = conexao.cursor()
    cursor.execute(query_poluente_plot())

    for row in cursor.fetchall():
        id, arquivo_escala_fixa_png, arquivo_escala_movel_png = row
        arquivo_escala_fixa_png_short = encurta_nome(arquivo_escala_fixa_png)
        arquivo_escala_movel_png_short = encurta_nome(arquivo_escala_movel_png)
        enviar('maps-pub',
               f'{_PATH_VOLUME}{arquivo_escala_fixa_png}',
               arquivo_escala_fixa_png_short,
               'image/png')

        enviar('maps-pub',
               f'{_PATH_VOLUME}{arquivo_escala_movel_png}',
               arquivo_escala_movel_png_short,
               'image/png')

        params = (str(arquivo_escala_fixa_png_short), str(arquivo_escala_movel_png_short), str(id))
        cursor.execute(update_poluente_plot, params)
        conexao.commit()

    cursor.close()
    conexao.close()
    # enviar('maps-pub',
    #        '/home/caue/Imagens/mapa/arquivo_com_transparencia.png',
    #        '2022_mp10_2_1.png',
    #        'image/png')
    # print('Arquivo enviado com sucesso!')

    # listar('maps-pub')
    
    # resultado = remover('maps-pub', "2022_mp10_2_1.png")
    # print("Remoção com sucesso")

