import streamlit as st

# =====================================
# CONFIG
# =====================================
st.set_page_config(
    page_title="Sistema Predictivo",
    layout="wide"
)

# =====================================
# IMPORTAR PÁGINAS
# =====================================
from pages.dashboard import show_dashboard
from pages.prediccion import show_prediccion

# =====================================
# SIDEBAR
# =====================================
st.sidebar.title("📂 Navegación")

pagina = st.sidebar.radio(
    "Ir a",
    [
        "Inicio",
        "Dashboard",
        "Predicción",
    ]
)

# =====================================
# PÁGINAS
# =====================================
if pagina == "Inicio":

    st.title("📈 Sistema Predictivo Retail")

    st.markdown("""
    ### Bienvenido al sistema inteligente de predicción

    Este sistema permite:

    - 📊 Analizar demanda de productos
    - 🤖 Realizar predicciones de ventas
    - 🌦️ Evaluar impacto del clima
    - 🏷️ Analizar promociones
    - ⏰ Detectar horas pico
    - 🏪 Comparar zonas y tiendas
    """)

elif pagina == "Dashboard":

    show_dashboard()

elif pagina == "Predicción":

    show_prediccion()

