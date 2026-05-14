import streamlit as st

st.set_page_config(
    page_title="Sistema Predictivo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================
# SIDEBAR
# =====================================

with st.sidebar:

    st.title("📂 Navegación")

    st.page_link(
        "app.py",
        label="🏠 Inicio"
    )

    st.page_link(
        "pages/dashboard.py",
        label="📊 Dashboard"
    )

    st.page_link(
        "pages/prediccion.py",
        label="🤖 Predicción"
    )

    st.page_link(
        "pages/historial.py",
        label="📜 Historial"
    )

# =====================================
# MAIN
# =====================================

st.title("📈 Sistema Predictivo de Ventas")

st.markdown("""
Bienvenido al sistema predictivo.

Usa el menú lateral para navegar.
""")