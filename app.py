import streamlit as st

st.set_page_config(
    page_title="Sistema Predictivo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 Sistema Predictivo de Ventas")

st.markdown("""
Bienvenido al sistema predictivo.

Usa el menú lateral para navegar.
""")
st.markdown("""
<style>

section[data-testid="stSidebar"] {
    background-color: #1E1E1E;
}

</style>
""", unsafe_allow_html=True)