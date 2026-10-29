"""Fase 1 · Generación de fuentes de datos sintéticas.

Crea un "territorio latente" de municipios (posición, altitud, población...) y
a partir de él genera ficheros que imitan a cada fuente real, cada uno con su
propio formato, codificación y defectos de calidad. El ETL (fase 2) tendrá que
integrarlos.

    Fuente            Fichero (data/raw/...)          Formato
    INE               ine/padron_municipal.csv                CSV ; latin-1, miles con '.'
    INE               ine/indicadores_socioeconomicos.csv     CSV ; latin-1, decimales con ','
    REE               ree/demanda_mensual_provincia.json      JSON plano
    REE               ree/red_electrica_municipal.json        JSON anidado con metadatos
    AEMET             aemet/clima_anual.json                  JSON, números como texto "14,3"
    MITECO / CCHH     miteco/agua_municipal.csv               CSV , utf-8
    MITECO / CCHH     miteco/reserva_embalses_mensual.csv     CSV , utf-8 (serie temporal)
    CNMC / SETID      cnmc/cobertura_telecom.xlsx             Excel, hoja "Cobertura"
    Catastro / IGN    catastro/suelo_transporte.txt           Texto separado por '|'

Los valores no son aleatorios sin más: siguen relaciones físicas y económicas
plausibles (más latitud y altitud → menos temperatura; cuencas del sureste →
más estrés hídrico; cerca de grandes nodos → mejor conectividad...).
"""
from __future__ import annotations

import json
from datetime import datetime

import numpy as np
import pandas as pd

from src.catalogo import (CONFEDERACIONES, ESTRES_CUENCA, NODOS_PRINCIPALES,
                                     NUCLEOS, PREFIJOS, PROVINCIAS)
from src.utils import cargar_config, get_logger, ruta_datos

log = get_logger("generadores")


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def haversine_km(lat1, lon1, lat2, lon2):
    """Distancia en km entre puntos (admite arrays de numpy)."""
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(a))


def ensuciar(df: pd.DataFrame, rng: np.random.Generator, columnas: list[str],
             pct_nulos: float = 0.02, pct_duplicados: float = 0.005) -> pd.DataFrame:
    """Introduce defectos típicos de datos reales: nulos y filas duplicadas."""
    df = df.copy()
    for c in columnas:
        mascara = rng.random(len(df)) < pct_nulos
        df[c] = df[c].astype(object)
        df.loc[mascara, c] = None
    dup = df.sample(frac=pct_duplicados, random_state=int(rng.integers(1e9)))
    return pd.concat([df, dup], ignore_index=True)


# ---------------------------------------------------------------------------
# 1. Territorio latente (no se guarda tal cual: es la "verdad" de la que salen las fuentes)
# ---------------------------------------------------------------------------
def generar_territorio(rng: np.random.Generator, escala: float = 1.0) -> pd.DataFrame:
    filas = []
    for cod_p, prov, ccaa, lat, lon, costa, n in PROVINCIAS:
        n = max(3, int(round(n * escala)))
        nombres = set()
        for i in range(1, n + 1):
            # Nombre único dentro de la provincia ("Villanueva", "Torre del Pinar"...)
            pre, nuc = rng.choice(PREFIJOS), rng.choice(NUCLEOS)
            nombre = f"{pre} {nuc}" if nuc.startswith("de") else f"{pre}{nuc}"
            base, k = nombre, 2
            while nombre in nombres:
                nombre, k = f"{base} {['', '', 'II', 'III', 'IV', 'V'][k] if k < 6 else k}", k + 1
            nombres.add(nombre)
            es_capital = i == 1
            filas.append({
                "cod_ine": f"{cod_p}{i:03d}",
                "municipio": f"{prov} (capital)" if es_capital else nombre,
                "cod_provincia": cod_p, "provincia": prov, "ccaa": ccaa,
                "lat": lat + (0 if es_capital else rng.normal(0, 0.35)),
                "lon": lon + (0 if es_capital else rng.normal(0, 0.45)),
                "provincia_costera": costa, "es_capital": es_capital,
            })
    t = pd.DataFrame(filas)
    n = len(t)

    # Altitud: más baja en provincias costeras, la Meseta ~700 m
    base_alt = np.where(t.provincia_costera, 250, 750)
    t["altitud_m"] = np.clip(base_alt + rng.gamma(2.0, 180, n) - 200, 0, 2100).round()
    t["dist_costa_km"] = np.where(t.provincia_costera, rng.gamma(1.5, 25, n), rng.gamma(4, 50, n)).round(1)

    # Población: log-normal (muchos pueblos pequeños, pocas ciudades grandes)
    pob = rng.lognormal(mean=6.6, sigma=1.5, size=n)
    pob = np.where(t.es_capital, rng.lognormal(12.0, 0.8, n), pob)
    t["poblacion_2024"] = np.clip(pob, 15, 3_400_000).round().astype(int)
    t["superficie_km2"] = np.clip(rng.lognormal(3.6, 0.8, n), 1, 1700).round(2)

    # Distancia al nodo principal de Internet más cercano
    dist = np.column_stack([haversine_km(t.lat, t.lon, la, lo) for la, lo in NODOS_PRINCIPALES.values()])
    t["dist_nodo_km"] = dist.min(axis=1).round(1)
    t["confederacion"] = t.ccaa.map(CONFEDERACIONES)
    return t


# ---------------------------------------------------------------------------
# 2. Fuentes
# ---------------------------------------------------------------------------
def fuente_ine(t, rng, anios, carpeta):
    """Padrón por año + indicadores socioeconómicos."""
    # Tendencia: los municipios pequeños pierden población, los grandes ganan
    tendencia = np.where(t.poblacion_2024 < 1000, -0.012, np.where(t.poblacion_2024 > 20000, 0.008, -0.002))
    tendencia = tendencia + rng.normal(0, 0.006, len(t))
    filas = []
    for anio in anios:
        factor = (1 + tendencia) ** (anios[-1] - anio)
        pob = (t.poblacion_2024 / factor * rng.normal(1, 0.004, len(t))).round().astype(int)
        filas.append(pd.DataFrame({"Codigo": t.cod_ine, "Municipio": t.municipio, "Periodo": anio,
                                   "Total": pob}))
    padron = pd.concat(filas, ignore_index=True)
    # Formato INE: miles con punto y nombres con mayúsculas/espacios irregulares
    padron["Total"] = padron["Total"].map(lambda v: f"{v:,}".replace(",", "."))
    idx = rng.random(len(padron)) < 0.03
    padron.loc[idx, "Municipio"] = padron.loc[idx, "Municipio"].str.upper() + "  "
    padron = ensuciar(padron, rng, ["Total"], pct_nulos=0.01)
    padron.to_csv(carpeta / "padron_municipal.csv", sep=";", index=False, encoding="latin-1")

    log_pob = np.log10(t.poblacion_2024)
    ind = pd.DataFrame({
        "Codigo": t.cod_ine,
        "Tasa envejecimiento (%)": np.clip(32 - 3.2 * log_pob + rng.normal(0, 4, len(t)), 8, 60),
        "Tasa paro (%)": np.clip(np.where(t.ccaa.isin(["Andalucía", "Extremadura", "Canarias"]), 17, 10)
                                 + rng.normal(0, 3, len(t)), 2, 40),
        "Poblacion con estudios superiores (%)": np.clip(10 + 5 * log_pob + rng.normal(0, 4, len(t)), 3, 65),
        "PIB municipal (miles EUR)": (t.poblacion_2024 * rng.normal(26, 5, len(t))).clip(100),
        "Empresas activas": (t.poblacion_2024 * rng.uniform(0.04, 0.09, len(t))).round().astype(int),
    })
    for c in ind.columns[1:4]:
        ind[c] = ind[c].round(2).map(lambda v: str(v).replace(".", ","))
    ind = ensuciar(ind, rng, ["Tasa paro (%)", "Poblacion con estudios superiores (%)"])
    ind.to_csv(carpeta / "indicadores_socioeconomicos.csv", sep=";", index=False, encoding="latin-1")


def fuente_ree(t, rng, anios, carpeta):
    """Demanda mensual por provincia (serie temporal) + red eléctrica municipal."""
    prov = t.groupby(["provincia", "provincia_costera"], as_index=False).agg(pob=("poblacion_2024", "sum"), lat=("lat", "mean"))
    registros = []
    for _, p in prov.iterrows():
        base = p.pob * 5.3 / 12  # ~5,3 MWh por habitante y año
        for anio in anios:
            for mes in range(1, 13):
                t_idx = (anio - anios[0]) * 12 + mes
                estacional = 1 + 0.12 * np.cos(2 * np.pi * (mes - 1) / 12) + 0.08 * np.cos(2 * np.pi * (mes - 7) / 12) * (p.lat < 39)
                tendencia = 1 + 0.011 * t_idx / 12 - (0.10 if anio == 2020 and 3 <= mes <= 6 else 0)
                renov = np.clip(35 + 2.1 * (anio - anios[0]) + 10 * np.sin(2 * np.pi * (mes - 3) / 12) + rng.normal(0, 4), 10, 90)
                registros.append({"provincia": p.provincia, "fecha": f"{anio}-{mes:02d}",
                                  "demanda_mwh": round(float(base * estacional * tendencia * rng.normal(1, 0.02)), 1),
                                  "pct_renovable": round(float(renov), 1)})
    with open(carpeta / "demanda_mensual_provincia.json", "w", encoding="utf-8") as f:
        json.dump(registros, f, ensure_ascii=False)

    n = len(t)
    cerca_nodo = np.exp(-t.dist_nodo_km / 150)
    datos = []
    for i, r in t.iterrows():
        dist_sub = float(np.clip(rng.gamma(2, 6) * (1.4 - cerca_nodo[i]), 0.3, 90))
        datos.append({
            "municipio": {"codigo": r.cod_ine, "nombre": r.municipio},
            "red": {
                "subestacion_cercana_km": round(dist_sub, 2),
                "tension_subestacion_kv": int(rng.choice([66, 132, 220, 400], p=[0.35, 0.3, 0.2, 0.15])),
                "capacidad_acceso_disponible_mw": round(float(np.clip(rng.gamma(2, 25) * (0.5 + cerca_nodo[i]), 0, 400)), 1),
                "capacidad_transporte_mva": round(float(rng.gamma(3, 120)), 0),
            },
            "balance": {
                "consumo_municipal_mwh": round(float(r.poblacion_2024 * rng.normal(5.3, 0.8)), 1),
                "produccion_local_mwh": round(float(rng.gamma(0.6, 20000) * (1 + (not r.provincia_costera))), 1),
            },
        })
    payload = {"metadata": {"fuente": "REE (sintético)", "generado": datetime.now().isoformat(timespec="seconds"),
                            "unidades": {"capacidad": "MW", "consumo": "MWh/año"}},
               "datos": datos}
    with open(carpeta / "red_electrica_municipal.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)


def fuente_aemet(t, rng, anios, carpeta):
    """Clima anual por municipio, con números como texto y coma decimal (estilo AEMET)."""
    n = len(t)
    # Temperatura: baja con la latitud y la altitud; Canarias templada
    tmed_base = 19.5 - 0.75 * (t.lat - 36).clip(lower=0) - 0.0062 * t.altitud_m
    tmed_base = np.where(t.ccaa == "Canarias", 21 - 0.006 * t.altitud_m, tmed_base)
    hr_base = np.clip(75 - t.dist_costa_km * 0.08 + (t.lat - 40) * 2, 40, 85)
    viento_base = rng.gamma(4, 1.0, n) + np.where(t.provincia_costera, 1.0, 0)
    registros = []
    for anio in anios:
        calentamiento = 0.04 * (anio - anios[0])
        tmed = tmed_base + calentamiento + rng.normal(0, 0.4, n)
        tmax = tmed + 18 + rng.normal(0, 1.5, n) - np.where(t.provincia_costera, 3, 0)
        dias35 = np.clip((tmax - 34) * 6 + rng.normal(0, 3, n), 0, 110)
        for i in range(n):
            registros.append({"indicativo": t.cod_ine.iat[i], "anio": str(anio),
                              "tm_mes": f"{tmed[i]:.1f}".replace(".", ","),
                              "ta_max": f"{tmax[i]:.1f}".replace(".", ","),
                              "hr": f"{hr_base[i] + rng.normal(0, 2):.0f}",
                              "nt_35": f"{dias35[i]:.0f}",
                              "w_med": f"{viento_base[i] * rng.normal(1, 0.05):.1f}".replace(".", ",")})
    # Huecos típicos de estaciones: algunos valores "" o "-"
    for r in rng.choice(registros, size=len(registros) // 60, replace=False):
        r[rng.choice(["tm_mes", "hr", "w_med"])] = rng.choice(["", "-"])
    with open(carpeta / "clima_anual.json", "w", encoding="utf-8") as f:
        json.dump(registros, f, ensure_ascii=False)


def fuente_miteco(t, rng, anios, carpeta):
    """Agua por municipio + reserva mensual de embalses por confederación."""
    n = len(t)
    estres = t.confederacion.map(ESTRES_CUENCA).to_numpy()
    agua = pd.DataFrame({
        "cod_ine": t.cod_ine,
        "confederacion": t.confederacion,
        "disponibilidad_hidrica_hm3": np.clip(rng.gamma(2, 6, n) * (1.3 - estres), 0.05, None).round(2),
        "consumo_hidrico_m3_hab_anio": np.clip(rng.normal(55, 10, n) + 25 * estres, 25, 130).round(1),
        "dist_embalse_km": np.clip(rng.gamma(2, 12, n), 0.5, 150).round(1),
        "indice_estres_hidrico": np.clip(estres + rng.normal(0, 0.08, n), 0, 1).round(3),
        "sequias_ultimos_20_anios": rng.poisson(1 + 5 * estres),
        "calidad_agua": rng.choice(["Buena", "Aceptable", "Deficiente"], n, p=[0.7, 0.24, 0.06]),
    })
    # Errores de captura: algunos negativos y calidades con distinta grafía
    idx = rng.random(n) < 0.005
    agua.loc[idx, "disponibilidad_hidrica_hm3"] *= -1
    idx = rng.random(n) < 0.05
    agua.loc[idx, "calidad_agua"] = agua.loc[idx, "calidad_agua"].str.lower()
    ensuciar(agua, rng, ["dist_embalse_km", "indice_estres_hidrico"]).to_csv(
        carpeta / "agua_municipal.csv", index=False, encoding="utf-8")

    filas = []
    for conf, e in ESTRES_CUENCA.items():
        nivel = 70 - 30 * e
        for anio in anios:
            sequia = -15 if anio in (2017, 2022, 2023) else 0
            for mes in range(1, 13):
                nivel_mes = nivel + sequia + 12 * np.cos(2 * np.pi * (mes - 4) / 12) + rng.normal(0, 3)
                filas.append({"confederacion": conf, "fecha": f"{anio}-{mes:02d}-01",
                              "reserva_pct": round(float(np.clip(nivel_mes, 5, 98)), 1)})
    pd.DataFrame(filas).to_csv(carpeta / "reserva_embalses_mensual.csv", index=False, encoding="utf-8")


def fuente_cnmc(t, rng, carpeta):
    """Cobertura de telecomunicaciones (Excel)."""
    n = len(t)
    urbano = np.clip((np.log10(t.poblacion_2024) - 2) / 3, 0, 1)
    cerca = np.exp(-t.dist_nodo_km / 200)
    df = pd.DataFrame({
        "Código INE": t.cod_ine,
        "Cobertura FTTH (%)": np.clip(30 + 65 * urbano + rng.normal(0, 10, n), 0, 100).round(1),
        "Cobertura 5G (%)": np.clip(10 + 80 * urbano * cerca + rng.normal(0, 10, n), 0, 100).round(1),
        "Operadores con red propia": np.clip(np.round(1 + 4 * urbano + rng.normal(0, 0.7, n)), 0, 6).astype(int),
        "Troncal de fibra": np.where(rng.random(n) < 0.15 + 0.6 * cerca, "Sí", "No"),
        "Distancia nodo principal (km)": t.dist_nodo_km,
        "Punto neutro en provincia": t.provincia.isin(["Madrid", "Barcelona", "Bizkaia", "Valencia", "Sevilla",
                                                        "Zaragoza", "Málaga"]),
    })
    with pd.ExcelWriter(carpeta / "cobertura_telecom.xlsx") as xls:
        pd.DataFrame({"Nota": ["Datos sintéticos generados para el Proyecto 3", "Fuente simulada: CNMC / SETID"]}
                     ).to_excel(xls, sheet_name="Leeme", index=False)
        df.to_excel(xls, sheet_name="Cobertura", index=False)


def fuente_catastro(t, rng, carpeta):
    """Suelo industrial, riesgos y transporte (texto separado por '|')."""
    n = len(t)
    urbano = np.clip((np.log10(t.poblacion_2024) - 2) / 3, 0, 1)
    sur_este = np.clip((40 - t.lat) / 4, 0, 1) * np.clip((t.lon + 4) / 4, 0, 1)
    df = pd.DataFrame({
        "COD_INE": t.cod_ine,
        "PRECIO_SUELO_IND_EUR_M2": np.clip(rng.lognormal(3.4, 0.4, n) * (1 + 3 * urbano), 8, 900).round(2),
        "PARCELAS_IND_DISPONIBLES": rng.poisson(1 + 12 * urbano),
        "SUP_IND_DISPONIBLE_HA": np.clip(rng.gamma(1.5, 8, n) * (0.3 + urbano), 0, 400).round(1),
        "CALIFICACION": rng.choice(["INDUSTRIAL", "TECNOLOGICO", "MIXTO", "RUSTICO"], n, p=[0.35, 0.08, 0.2, 0.37]),
        "RIESGO_INUNDACION": rng.choice(["BAJO", "MEDIO", "ALTO"], n, p=[0.65, 0.25, 0.10]),
        "PGA_SISMICA_G": np.clip(0.03 + 0.18 * sur_este + rng.normal(0, 0.02, n), 0.02, 0.30).round(3),
        "PCT_RED_NATURA": np.clip(rng.beta(1.2, 4, n) * 100, 0, 100).round(1),
        "DIST_AUTOPISTA_KM": np.clip(rng.gamma(1.6, 12, n) * (1.2 - urbano), 0.2, 150).round(1),
        "DIST_PUERTO_KM": np.clip(t.dist_costa_km * rng.uniform(1, 2.5, n), 1, 600).round(1),
        "DIST_AEROPUERTO_KM": np.clip(rng.gamma(3, 25, n) * (1.2 - urbano), 2, 300).round(1),
    })
    df.to_csv(carpeta / "suelo_transporte.txt", sep="|", index=False, encoding="utf-8")


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------
def generar_todo(config: dict | None = None) -> dict:
    """Genera todas las fuentes en data/raw. Devuelve un resumen."""
    config = config or cargar_config()
    rng = np.random.default_rng(config["semilla"])
    g = config["generacion"]
    anios = list(range(g["anio_inicio"], g["anio_fin"] + 1))
    raw = ruta_datos("raw", config)

    t = generar_territorio(rng, g["escala_municipios"])
    log.info("Territorio sintético: %d municipios en %d provincias", len(t), t.provincia.nunique())

    pasos = {"ine": lambda c: fuente_ine(t, rng, anios, c),
             "ree": lambda c: fuente_ree(t, rng, anios, c),
             "aemet": lambda c: fuente_aemet(t, rng, anios, c),
             "miteco": lambda c: fuente_miteco(t, rng, anios, c),
             "cnmc": lambda c: fuente_cnmc(t, rng, c),
             "catastro": lambda c: fuente_catastro(t, rng, c)}
    resumen = {}
    for nombre, fn in pasos.items():
        carpeta = raw / nombre
        carpeta.mkdir(parents=True, exist_ok=True)
        fn(carpeta)
        ficheros = sorted(p.name for p in carpeta.iterdir())
        resumen[nombre] = ficheros
        log.info("Fuente %-8s -> %s", nombre, ", ".join(ficheros))

    # Maestro de municipios (equivale al nomenclátor oficial del INE)
    t[["cod_ine", "municipio", "cod_provincia", "provincia", "ccaa", "lat", "lon", "altitud_m",
       "superficie_km2"]].to_csv(raw / "ine" / "nomenclator_municipios.csv", sep=";", index=False,
                                encoding="latin-1")
    return resumen


if __name__ == "__main__":
    generar_todo()
