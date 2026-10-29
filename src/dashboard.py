"""Fase 7 · Cuadro de mandos (Streamlit).

Ejecutar:  streamlit run src/dashboard.py

Páginas previstas:
  1. Ranking de municipios y mapa de España por score de viabilidad
  2. Ficha de municipio (todas las dimensiones + comparativa con la media)
  3. Simulador: configurar el CPD y ver impacto, costes y ROI
  4. Previsiones a 10 años (demanda eléctrica, reservas de agua)
  5. Calidad de datos y linaje (fuentes, fechas de carga)
"""
import streamlit as st

st.set_page_config(page_title="Viabilidad CPD", layout="wide")
st.title("Sistema de predicción de viabilidad de un CPD")
st.info("Dashboard en construcción. Ejecuta primero `python run_pipeline.py`.")
