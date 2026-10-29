# Proyecto 3 · Sistema de Predicción de Viabilidad de un CPD

Plataforma en Python que puntúa (0–100) la viabilidad de instalar un Centro de
Procesamiento de Datos en cada municipio español y proyecta su sostenibilidad a 10 años.
Los datos son sintéticos y reproducibles.

## Estructura

```
config/
  config.yaml       parámetros del proyecto
data/
  raw/              datos de origen (generados)
  processed/        datos limpios e integrados
docs/               informes y manuales
src/
  catalogo.py       provincias y referencias territoriales
  generar_datos.py  genera las fuentes sintéticas
  etl.py            limpieza e integración
  warehouse.py      Data Warehouse (DuckDB)
  modelos.py        score, Machine Learning y series temporales
  simulador.py      simulador de escenarios
  dashboard.py      cuadro de mandos (Streamlit)
  utils.py          configuración y rutas
run_pipeline.py     ejecuta todo el proceso
```

## Uso

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run_pipeline.py
streamlit run src/dashboard.py
```
