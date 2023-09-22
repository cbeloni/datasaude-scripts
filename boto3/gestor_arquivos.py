import boto3
from dotenv import load_dotenv, dotenv_values

load_dotenv()
_config = dotenv_values(".env")

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
            remover('maps-pub', obj['Key'])
    else:
        print('O bucket está vazio.')
        
def remover(bucket_name: str, key: str):
    bucket_name = bucket_name
    object_key = key

    return _s3_client.delete_object(Bucket=bucket_name, Key=object_key)

if __name__ == '__main__':
    enviar('maps-pub',
           '/home/caue/Imagens/mapa/arquivo_com_transparencia.png',
           '2022_mp10_2_1.png',
           'image/png')
    print('Arquivo enviado com sucesso!')

    # listar('maps-pub')
    
    # resultado = remover('maps-pub', "2022_mp10_2_1.png")
    # print("Remoção com sucesso")

