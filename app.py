import streamlit as st

st.set_page_config(
    page_title="Sistema Predictivo",
    page_icon="📊",
    layout="wide"
)

st.title("📈 Sistema Predictivo de Ventas")

st.write("Selecciona una sección:")

col1, col2, col3 = st.columns(3)

with col1:
    st.page_link(
        "pages/dashboard.py",
        label="📊 Dashboard",
        icon="📊"
    )

with col2:
    st.page_link(
        "pages/prediccion.py",
        label="🤖 Predicción",
        icon="🤖"
    )

with col3:
    st.page_link(
        "pages/historial.py",
        label="📜 Historial",
        icon="📜"
    )