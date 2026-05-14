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
    if st.button("📊 Dashboard"):
        st.switch_page("pages/dashboard.py")

with col2:
    if st.button("🤖 Predicción"):
        st.switch_page("pages/prediccion.py")

with col3:
    if st.button("📜 Historial"):
        st.switch_page("pages/historial.py")