"""Catálogo territorial de referencia: provincias españolas con su comunidad
autónoma, centroide aproximado, si tienen costa y nº aproximado de municipios.

Es el único dato "real" del proyecto y solo sirve como esqueleto geográfico
para que los municipios sintéticos queden repartidos de forma verosímil.
"""

# (cod_provincia, provincia, ccaa, lat, lon, costa, n_municipios)
PROVINCIAS = [
    ("01", "Álava", "País Vasco", 42.85, -2.68, False, 51),
    ("02", "Albacete", "Castilla-La Mancha", 38.83, -1.98, False, 87),
    ("03", "Alicante", "Comunidad Valenciana", 38.48, -0.57, True, 141),
    ("04", "Almería", "Andalucía", 37.17, -2.33, True, 103),
    ("05", "Ávila", "Castilla y León", 40.58, -4.95, False, 248),
    ("06", "Badajoz", "Extremadura", 38.68, -6.17, False, 165),
    ("07", "Illes Balears", "Illes Balears", 39.57, 2.90, True, 67),
    ("08", "Barcelona", "Cataluña", 41.73, 1.98, True, 311),
    ("09", "Burgos", "Castilla y León", 42.35, -3.68, False, 371),
    ("10", "Cáceres", "Extremadura", 39.70, -6.15, False, 223),
    ("11", "Cádiz", "Andalucía", 36.52, -5.75, True, 45),
    ("12", "Castellón", "Comunidad Valenciana", 40.20, -0.20, True, 135),
    ("13", "Ciudad Real", "Castilla-La Mancha", 38.98, -3.93, False, 102),
    ("14", "Córdoba", "Andalucía", 37.88, -4.78, False, 77),
    ("15", "A Coruña", "Galicia", 43.12, -8.40, True, 93),
    ("16", "Cuenca", "Castilla-La Mancha", 40.07, -2.13, False, 238),
    ("17", "Girona", "Cataluña", 42.13, 2.67, True, 221),
    ("18", "Granada", "Andalucía", 37.30, -3.30, True, 174),
    ("19", "Guadalajara", "Castilla-La Mancha", 40.82, -2.62, False, 288),
    ("20", "Gipuzkoa", "País Vasco", 43.15, -2.17, True, 88),
    ("21", "Huelva", "Andalucía", 37.58, -6.83, True, 80),
    ("22", "Huesca", "Aragón", 42.13, -0.10, False, 202),
    ("23", "Jaén", "Andalucía", 37.95, -3.45, False, 97),
    ("24", "León", "Castilla y León", 42.60, -5.80, False, 211),
    ("25", "Lleida", "Cataluña", 42.03, 1.03, False, 231),
    ("26", "La Rioja", "La Rioja", 42.28, -2.52, False, 174),
    ("27", "Lugo", "Galicia", 43.00, -7.55, True, 67),
    ("28", "Madrid", "Comunidad de Madrid", 40.42, -3.70, False, 179),
    ("29", "Málaga", "Andalucía", 36.83, -4.70, True, 103),
    ("30", "Murcia", "Región de Murcia", 38.00, -1.50, True, 45),
    ("31", "Navarra", "Navarra", 42.67, -1.65, False, 272),
    ("32", "Ourense", "Galicia", 42.20, -7.60, False, 92),
    ("33", "Asturias", "Principado de Asturias", 43.30, -5.95, True, 78),
    ("34", "Palencia", "Castilla y León", 42.37, -4.53, False, 191),
    ("35", "Las Palmas", "Canarias", 28.30, -14.80, True, 34),
    ("36", "Pontevedra", "Galicia", 42.43, -8.63, True, 61),
    ("37", "Salamanca", "Castilla y León", 40.82, -6.00, False, 362),
    ("38", "Santa Cruz de Tenerife", "Canarias", 28.30, -16.60, True, 54),
    ("39", "Cantabria", "Cantabria", 43.20, -4.03, True, 102),
    ("40", "Segovia", "Castilla y León", 41.17, -4.07, False, 209),
    ("41", "Sevilla", "Andalucía", 37.43, -5.67, False, 106),
    ("42", "Soria", "Castilla y León", 41.67, -2.60, False, 183),
    ("43", "Tarragona", "Cataluña", 41.08, 0.85, True, 184),
    ("44", "Teruel", "Aragón", 40.65, -0.78, False, 236),
    ("45", "Toledo", "Castilla-La Mancha", 39.80, -4.17, False, 204),
    ("46", "Valencia", "Comunidad Valenciana", 39.37, -0.67, True, 266),
    ("47", "Valladolid", "Castilla y León", 41.63, -4.85, False, 225),
    ("48", "Bizkaia", "País Vasco", 43.22, -2.85, True, 112),
    ("49", "Zamora", "Castilla y León", 41.73, -6.03, False, 248),
    ("50", "Zaragoza", "Aragón", 41.62, -1.05, False, 293),
]

# Capitales con punto neutro de Internet / gran nodo (para distancia a nodos)
NODOS_PRINCIPALES = {
    "Madrid": (40.42, -3.70),
    "Barcelona": (41.39, 2.17),
    "Bilbao": (43.26, -2.93),
    "Valencia": (39.47, -0.38),
    "Sevilla": (37.39, -5.98),
    "Zaragoza": (41.65, -0.88),
    "Málaga": (36.72, -4.42),
}

CONFEDERACIONES = {
    "Galicia": "Miño-Sil", "Principado de Asturias": "Cantábrico", "Cantabria": "Cantábrico",
    "País Vasco": "Cantábrico", "Navarra": "Ebro", "La Rioja": "Ebro", "Aragón": "Ebro",
    "Cataluña": "Ebro", "Castilla y León": "Duero", "Comunidad de Madrid": "Tajo",
    "Extremadura": "Guadiana", "Castilla-La Mancha": "Guadiana", "Andalucía": "Guadalquivir",
    "Región de Murcia": "Segura", "Comunidad Valenciana": "Júcar", "Illes Balears": "Illes Balears",
    "Canarias": "Canarias",
}

# Estrés hídrico estructural de cada cuenca (0 = sin estrés, 1 = máximo)
ESTRES_CUENCA = {
    "Miño-Sil": 0.10, "Cantábrico": 0.12, "Ebro": 0.40, "Duero": 0.38, "Tajo": 0.50,
    "Guadiana": 0.60, "Guadalquivir": 0.72, "Segura": 0.92, "Júcar": 0.70,
    "Illes Balears": 0.75, "Canarias": 0.85,
}

PREFIJOS = ["Villa", "San", "Santa", "Torre", "Castil", "Fuente", "Puebla", "Valde", "Monte",
            "Navas", "Alba", "Quinta", "Casas", "Puerto", "Peña", "Rio", "Campo", "Sierra"]
NUCLEOS = ["nueva", "rrubia", "blanca", "real", "verde", "alta", "llana", "seca", "fría",
           "mayor", "hermosa", "del Valle", "de Arriba", "de Abajo", "del Monte", "del Río",
           "de la Sierra", "del Campo", "de los Olmos", "del Pinar"]
