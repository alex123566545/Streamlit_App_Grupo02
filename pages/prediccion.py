import streamlit as st
import pandas as pd

def show_prediccion():

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

        pred = 24

        st.success(
            f"Cantidad estimada: {pred}"
        )