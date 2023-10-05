
import requests
import time
from estacao_address import addresses
from dotenv import load_dotenv, dotenv_values
import pyproj
from geopy.geocoders import Nominatim

load_dotenv()
_config = dotenv_values("../.env")

def get_free_coordenadas_utm_do_endereco(endereco):
    try:
        geolocator = Nominatim(user_agent="myGeocoder")
        location = geolocator.geocode(endereco)

        if location:
            latitude = location.latitude
            longitude = location.longitude
            place_rank = location.raw["place_rank"]

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
            raise {"Endereço não encontrado ou geocodificação falhou."}
    except Exception as e:
        raise {"error": str(e)}

def get_latitude_longitude_gmaps(address):
    url = "https://maps.googleapis.com/maps/api/geocode/json?address=%s&key=%s" % (address, _config['api_key'])
    response = requests.get(url)
    json_data = response.json()
    results = json_data['results']
    location = results[0]['geometry']['location']
    location_type = results[0]['geometry']['location_type']
    latitude = location['lat']
    longitude = location['lng']
    return (latitude, longitude, location_type)

def get_latitude_longitude_opencage(address):
    url = "https://api.opencagedata.com/geocode/v1/json?key=%s&q=%s" % (_config['open_cage_api_key'], address)
    response = requests.get(url)
    json_data = response.json()
    results = json_data['results']
    latitude = results[0]['geometry']['lat']
    longitude = results[0]['geometry']['lng']
    confidence = results[0]['confidence']
    return (latitude, longitude, confidence)

def converte_coordenadas_UTM(latitude, longitude):
    input_crs = pyproj.CRS.from_epsg(4326)
    output_crs = pyproj.CRS.from_epsg(29193)

    transformer = pyproj.Transformer.from_crs(input_crs, output_crs, always_xy=True)

    # Converta de latitude e longitude para UTM
    return transformer.transform(longitude, latitude)


if __name__ == '__main__':
    coordenadas = get_free_coordenadas_utm_do_endereco(f'AVENIDA DOUTOR GUILHERME DUMONT VILARES DE 1171 A 1402, SP')

    # for estacao in addresses:

        #API Google Maps
        # latitude, longitude, location_type = get_latitude_longitude_gmaps(f'{estacao["endereco"]},{estacao["municipio"]}')
        # x, y = converte_coordenadas_UTM(latitude, longitude)
        # print(f'{estacao["endereco"]};{estacao["municipio"]};{estacao["nome"]};{latitude};{longitude};{x};{y};{location_type}')

        #API FREE
        # try:
        #     coordenadas = get_free_coordenadas_utm_do_endereco(f'{estacao["endereco"]}, {estacao["municipio"]} - SP')
        #     print(f'{estacao["endereco"]};{estacao["municipio"]};{estacao["nome"]};"{coordenadas["latitude"]}";"{coordenadas["longitude"]}";"{coordenadas["x"]}";"{coordenadas["y"]}";{coordenadas["place_rank"]}')
        # except Exception as e:
        #     print(f'{estacao["endereco"]};{estacao["municipio"]}; endereço não encontrado')
        # try:
        #     latitude, longitude, location_type = get_latitude_longitude_opencage(f'{estacao["endereco"]},{estacao["municipio"]}')
        #     x, y = converte_coordenadas_UTM(latitude, longitude)
        #     print(f'{estacao["endereco"]};{estacao["municipio"]};{estacao["nome"]};{latitude};{longitude};{x};{y};{location_type}')
        # except Exception as e:
        #     print(f'{estacao["endereco"]};{estacao["municipio"]}; endereço não encontrado')

