import requests
import time
from estacao_address import addresses
from dotenv import load_dotenv, dotenv_values

load_dotenv()
_config = dotenv_values("../.env")


def get_latitude_longetitude(address):
    global url, response, location
    url = "https://maps.googleapis.com/maps/api/geocode/json?address=%s&key=%s" % (address, _config['api_key'])
    response = requests.get(url)
    json_data = response.json()
    results = json_data['results']
    location = results[0]['geometry']['location']
    latitude = location['lat']
    longitude = location['lng']
    return (latitude, longitude)

if __name__ == '__main__':
    for estacao in addresses:
        latitude, longitude = get_latitude_longetitude(estacao)
        print(f'{estacao};{latitude};{longitude}')
        time.sleep(2)