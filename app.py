import streamlit as st

# =====================================
# CONFIG
# =====================================

st.set_page_config(
    page_title="Sistema Predictivo",
    layout="wide"
)

# =====================================
# MENU
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

