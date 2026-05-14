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

# =====================================
# PAGINAS
# =====================================

if pagina == "Inicio":

    st.title("📈 Sistema Predictivo")

    st.write("Bienvenido al sistema.")

elif pagina == "Dashboard":

    from pages.dashboard import show_dashboard

    show_dashboard()

elif pagina == "Predicción":

    from pages.prediccion import show_prediccion

    show_prediccion()

elif pagina == "Historial":

    from pages.historial import show_historial

    show_historial()