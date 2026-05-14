import streamlit as st
import pandas as pd

# =====================================
# CONFIG
# =====================================

st.set_page_config(
    page_title="Sistema Predictivo",
    layout="wide"
)

# =====================================
# MENU LATERAL
# =====================================

pagina = st.sidebar.radio(
    "📂 Navegación",
    [
        "Inicio",
        "Dashboard",
        "Predicción",
        "Historial"
    ]
)

# =====================================
# INICIO
# =====================================

if pagina == "Inicio":

    st.title("📈 Sistema Predictivo de Ventas")

    st.write("""
    Bienvenido al sistema predictivo.
    """)

# =====================================
# DASHBOARD
# =====================================

elif pagina == "Dashboard":

    st.title("📊 Dashboard")

    st.metric(
        "Ventas Totales",
        "S/ 25,000"
    )

    st.metric(
        "Predicciones",
        "350"
    )

# =====================================
# PREDICCION
# =====================================

elif pagina == "Predicción":

    st.title("🤖 Predicción de Ventas")

    fecha = st.date_input("Fecha")

    hora = st.number_input(
        "Hora",
        min_value=0,
        max_value=23
    )

    producto = st.selectbox(
        "Producto",
        [
            "Coca Cola",
            "Red Bull",
            "Inca Kola"
        ]
    )

    precio = st.number_input(
        "Precio",
        min_value=0.0
    )

    clima = st.selectbox(
        "Clima",
        [
            "Soleado",
            "Lluvioso",
            "Nublado"
        ]
    )

    if st.button("Predecir"):

        prediccion_fake = 24

        st.success(
            f"Cantidad vendida estimada: {prediccion_fake}"
        )

# =====================================
# HISTORIAL
# =====================================

elif pagina == "Historial":

    st.title("📜 Historial")

    df = pd.DataFrame({
        "Producto": ["Coca Cola", "Red Bull"],
        "Predicción": [20, 35]
    })

    st.dataframe(df)