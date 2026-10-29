"""Punto de entrada del pipeline completo.

Uso:
    python run_pipeline.py                 # todas las fases implementadas
    python run_pipeline.py --fase generar  # solo una fase
"""
import argparse
import sys
import time

from src.utils import cargar_config, get_logger

log = get_logger("pipeline")


def fase_generar(cfg):
    from src.generar_datos import generar_todo
    generar_todo(cfg)


def fase_etl(cfg):
    from src.etl import ejecutar_etl
    ejecutar_etl(cfg)


def fase_warehouse(cfg):
    from src.warehouse import construir_dw
    construir_dw(cfg)


def fase_modelos(cfg):
    from src.modelos import entrenar_todo
    entrenar_todo(cfg)


FASES = {"generar": fase_generar, "etl": fase_etl, "warehouse": fase_warehouse, "modelos": fase_modelos}


def main():
    parser = argparse.ArgumentParser(description="Pipeline Proyecto 3 · Viabilidad CPD")
    parser.add_argument("--fase", choices=list(FASES), help="Ejecuta solo esta fase")
    args = parser.parse_args()
    cfg = cargar_config()

    for nombre, fn in FASES.items():
        if args.fase and nombre != args.fase:
            continue
        inicio = time.time()
        log.info("=== Fase: %s ===", nombre)
        try:
            fn(cfg)
        except NotImplementedError as e:
            log.warning("Fase '%s' aún no implementada: %s", nombre, e)
            continue
        log.info("Fase '%s' completada en %.1f s", nombre, time.time() - inicio)


if __name__ == "__main__":
    sys.exit(main())
