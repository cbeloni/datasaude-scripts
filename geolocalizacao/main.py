import requests
import time
from estacao_address import addresses
from dotenv import load_dotenv, dotenv_values
import pyproj
from geopy.geocoders import Nominatim

load_dotenv()
_config = dotenv_values("../.env")

def obter_coordenadas_utm_do_endereco(endereco):
    try:
        # Inicialize o geocoder
        geolocator = Nominatim(user_agent="myGeocoder")

        # Obtenha as coordenadas geográficas (latitude e longitude) do endereço
        location = geolocator.geocode(endereco)

        if location:
            latitude = location.latitude
            longitude = location.longitude

            # Defina a projeção de coordenadas para UTM 29T (código 29193)
            utm = pyproj.Proj("+proj=utm +zone=23 +south +ellps=aust_SA + towgs84")

            # Converta as coordenadas geográficas em coordenadas UTM
            utm_x, utm_y = utm(longitude, latitude)

            return {
                "latitude": latitude,
                "longitude": longitude,
                "utm_29T": (utm_x, utm_y)
            }
        else:
            return {"error": "Endereço não encontrado ou geocodificação falhou."}
    except Exception as e:
        return {"error": str(e)}

def get_latitude_longetitude(address):
    url = "https://maps.googleapis.com/maps/api/geocode/json?address=%s&key=%s" % (address, _config['api_key'])
    response = requests.get(url)
    json_data = response.json()
    results = json_data['results']
    location = results[0]['geometry']['location']
    latitude = location['lat']
    longitude = location['lng']
    return (latitude, longitude)
def converte_coordenadas_UTM(latitude, longitude):
    input_crs = pyproj.CRS.from_epsg(4326)
    output_crs = pyproj.CRS.from_epsg(29193)

    transformer = pyproj.Transformer.from_crs(input_crs, output_crs, always_xy=True)

    # Converta de latitude e longitude para UTM
    return transformer.transform(longitude, latitude)


if __name__ == '__main__':
    for estacao in addresses:
        latitude, longitude = get_latitude_longetitude(f'{estacao["endereco"]},{estacao["municipio"]}')
        #coordenadas = obter_coordenadas_utm_do_endereco(f'{estacao["endereco"]},{estacao["municipio"]}')
        x, y = converte_coordenadas_UTM(latitude, longitude)
        print(f'{estacao["endereco"]};{estacao["municipio"]};{estacao["nome"]};{latitude};{longitude};{x};{y}')
        time.sleep(2)