import streamlit as st

st.set_page_config(
    page_title="Sistema Predictivo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================
# FORZAR VISIBILIDAD DEL SIDEBAR
# =====================================

st.markdown("""
<style>

[data-testid="stSidebar"] {
    min-width: 250px;
    max-width: 250px;
}

</style>
""", unsafe_allow_html=True)

# =====================================
# MAIN
# =====================================

st.title("📈 Sistema Predictivo de Ventas")

st.write("Bienvenido al sistema predictivo.")

st.info("⬅️ Usa el menú lateral izquierdo para navegar.")