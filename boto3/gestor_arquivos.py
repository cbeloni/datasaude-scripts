import boto3
from dotenv import load_dotenv, dotenv_values
load_dotenv()
_config = dotenv_values(".env")


def enviar():
    s3_client = boto3.client('s3',
                             aws_access_key_id=_config['aws_access_key_id'],
                             aws_secret_access_key=_config['aws_secret_access_key'],
                             endpoint_url=_config['endpoint_url'])
    bucket_name = 'maps-pub'
    file_path = '/home/caue/Documentos/pensi_projeto/datasaude-app/public/2022_mp10_2_1.png'
    object_name = '2022_mp10_2_1.png'
    extra_args = {'ContentType': 'image/png'}
    s3_client.upload_file(file_path, bucket_name, object_name, ExtraArgs=extra_args)


enviar()

if __name__ == '__main__':
    print('Arquivo enviado com sucesso!')