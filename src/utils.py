"""Utilidades comunes: rutas del proyecto, carga de configuración y logging."""
from __future__ import annotations

import logging
from pathlib import Path

import yaml

# Raíz del proyecto (carpeta que contiene config/, src/, data/...)
RAIZ = Path(__file__).resolve().parents[1]


def cargar_config(ruta: str | Path | None = None) -> dict:
    """Lee config/config.yaml y devuelve un diccionario."""
    ruta = Path(ruta) if ruta else RAIZ / "config" / "config.yaml"
    with open(ruta, encoding="utf-8") as f:
        return yaml.safe_load(f)


def ruta_datos(clave: str, config: dict | None = None) -> Path:
    """Devuelve la ruta absoluta de una capa (bronze, silver, gold, warehouse...)
    y crea la carpeta si no existe."""
    config = config or cargar_config()
    ruta = RAIZ / config["rutas"][clave]
    carpeta = ruta.parent if ruta.suffix else ruta
    carpeta.mkdir(parents=True, exist_ok=True)
    return ruta


def get_logger(nombre: str) -> logging.Logger:
    """Logger con formato homogéneo para todo el pipeline."""
    logger = logging.getLogger(nombre)
    if not logger.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s", "%H:%M:%S"))
        logger.addHandler(h)
        logger.setLevel(logging.INFO)
    return logger
