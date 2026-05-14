import streamlit as st
import pandas as pd

from utils.predict import predict_sales
from utils.preprocess import preprocess_input

st.title("🤖 Predicción de Ventas")

fecha = st.date_input("Fecha")

hora = st.number_input(
    "Hora",
    min_value=0,
    max_value=23
)

ubicacion_tienda = st.selectbox(
    "Ubicación",
    [
        "Ayacucho Centro",
        "Lima Norte",
        "Cusco Plaza"
    ]
)

tipo_zona = st.selectbox(
    "Tipo Zona",
    [
        "Urbana",
        "Rural"
    ]
)

producto = st.selectbox(
    "Producto",
    [
        "Coca Cola",
        "Red Bull",
        "Inca Kola"
    ]
)

categoria_producto = st.selectbox(
    "Categoría",
    [
        "Bebidas",
        "Snacks"
    ]
)

precio_unitario = st.number_input(
    "Precio",
    min_value=0.0
)

tipo_promocion = st.selectbox(
    "Promoción",
    [
        "Ninguna",
        "2x1",
        "Descuento"
    ]
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

    data = pd.DataFrame([{
        "fecha": fecha,
        "hora": hora,
        "ubicacion_tienda": ubicacion_tienda,
        "tipo_zona": tipo_zona,
        "producto": producto,
        "categoria_producto": categoria_producto,
        "precio_unitario": precio_unitario,
        "tipo_promocion": tipo_promocion,
        "clima": clima
    }])

    data = preprocess_input(data)

    pred = predict_sales(data)

    st.success(
        f"Cantidad vendida estimada: {round(pred[0],2)}"
    )