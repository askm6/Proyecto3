"""ETL: limpia los datos de data/raw y guarda el resultado integrado en data/processed.

Pasos:
  1. Extraer cada fuente con su formato (CSV ; latin-1, JSON anidado, Excel, texto '|').
  2. Limpiar: decimales con coma, miles con punto, nulos, duplicados, valores imposibles.
  3. Validar: rangos, códigos INE únicos, % de nulos.
  4. Integrar: una fila por municipio con todas las variables.
"""


def ejecutar_etl(config: dict) -> None:
    raise NotImplementedError("Pendiente")
