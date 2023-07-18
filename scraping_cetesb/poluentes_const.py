estacoes = {
    'Americana': 290,
    'Americana-Vila Sta Maria': 105,
    'Araçatuba': 107,
    'Araraquara': 106,
    'Bauru': 108,
    'Cambuci': 90,
    'Campinas-Centro': 89,
    'Campinas-Taquaral': 276,
    'Campinas-V.União': 275,
    'Capão Redondo': 269,
    'Carapicuíba': 263,
    'Catanduva': 248,
    'Centro': 94,
    'Cerqueira César': 91,
    'Cid.Universitária-USP-Ipen': 95,
    'Congonhas': 73,
    'Cubatão-Centro': 87,
    'Cubatão-V.Parisi': 66,
    'Cubatão-Vale do Mogi': 119,
    'Diadema': 92,
    'Grajaú-Parelheiros': 98,
    'Guaratinguetá': 289,
    'Guarulhos': 118,
    'Guarulhos-Paço Municipal': 264,
    'Guarulhos-Pimentas': 279,
    'Ibirapuera': 83,
    'Interlagos': 262,
    'Itaim Paulista': 266,
    'Itaquera': 97,
    'Jacareí': 259,
    'Jaú': 110,
    'Jundiaí': 109,
    'Lapa': 84,
    'Limeira': 281,
    'Marg.Tietê-Pte Remédios': 270,
    'Marília': 111,
    'Mauá': 65,
    'Mogi das Cruzes': 287,
    'Mooca': 85,
    'N.Senhora do Ó': 96,
    'Osasco': 120,
    'Parque D.Pedro II': 72,
    'Paulínia': 117,
    'Paulínia-Sta Terezinha': 291,
    'Paulínia-Sul': 112,
    'Perus': 293,
    'Pico do Jaraguá': 284,
    'Pinheiros': 99,
    'Piracicaba': 113,
    'Pirassununga': 268,
    'Presidente Prudente': 114,
    'Ribeirão Preto': 288,
    'Ribeirão Preto-Ipiranga': 115,
    'Rio Claro-Jd.Guanabara': 292,
    'S.André-Capuava': 100,
    'S.André-Centro': 101,
    'S.André-Paço Municipal': 254,
    'S.Bernardo-Centro': 272,
    'S.Bernardo-Paulicéia': 102,
    'S.José Campos': 88,
    'S.José Campos-Jd.Satelite': 277,
    'S.José Campos-Vista Verde': 278,
    'S.Miguel Paulista': 236,
    'Santa Gertrudes': 273,
    'Santana': 63,
    'Santo Amaro': 64,
    'Santos': 258,
    'Santos-Ponta da Praia': 260,
    'São Caetano do Sul': 86,
    'São José do Rio Preto': 116,
    'São Sebastião': 294,
    'Sorocaba': 67,
    'Taboão da Serra': 103,
    'Tatuí': 256,
    'Taubaté': 280
}

estacoes_grande_sp = [
    'Santana',
    'Santo Amaro',
    'Parque D.Pedro II',
    'Congonhas',
    'Ibirapuera',
    'Mooca',
    'Cerqueira César',
    'Cid.Universitária-USP-Ipen',
    'N.Senhora do Ó',
    'Itaquera',
    'Interlagos',
    'Itaim Paulista',
    'Capão Redondo',
    'Marg.Tietê-Pte Remédios',
    'Pico do Jaraguá',
    'Diadema',
    'Guarulhos-Paço Municipal',
    'Guarulhos-Pimentas',
    'Mauá',
    'S.André-Capuava',
    'S.Bernardo-Paulicéia',
    'S.Bernardo-Centro',
    'São Caetano do Sul',
    'Taboão da Serra',
    'Santo Amaro',
    'Carapicuíba',
    'Cubatão-Centro',
    'Grajaú-Parelheiros',
    'Osasco',
    'Perus',
    'Pinheiros',
]

estacoes_pendentes = [
    'Santo Amaro',
    'Carapicuíba',
    'Cubatão-Centro',
    'Grajaú-Parelheiros',
    'Osasco',
    'Perus',
    'Pinheiros',
]

poluentes = {
    'MP10': 12,
    'NO':17,
    'NO2': 15,
    'O3':63,
    'TEMP':25,
    'UR': 28
}
poluentes_analisados = [
    'MP10',
    'NO',
    'NO2',
    'O3',
    'TEMP',
    'UR',
]

if __name__ == '__main__':
    # for i in estacoes_grande_sp:
    #     print(estacoes[i])

    for poluente in poluentes:
        print(poluentes)

