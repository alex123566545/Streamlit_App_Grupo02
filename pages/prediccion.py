import streamlit as st
import pandas as pd
import requests
import pickle
from datetime import datetime


# =============================
# DESCARGA DESDE SUPABASE
# =============================
def load_file(url):

    response = requests.get(url)
    response.raise_for_status()

    return pickle.loads(response.content)


# =============================
# CARGAR MODELO + ENCODERS
# =============================
@st.cache_resource
def load_assets():

    MODEL_URL = "https://klbmaoqxfvjsczwrrwkj.supabase.co/storage/v1/object/public/models/model.pkl"

    ENCODERS_URL = "https://klbmaoqxfvjsczwrrwkj.supabase.co/storage/v1/object/public/models/encoders.pkl"

    model = load_file(MODEL_URL)
    encoders = load_file(ENCODERS_URL)

    return model, encoders


# =============================
# CREAR FEATURES
# =============================
def build_features(
    fecha,
    hora,
    producto,
    categoria_producto,
    precio,
    tipo_promocion,
    tipo_zona,
    ubicacion_tienda,
    clima
):

    dia_semana = fecha.strftime("%A")

    df = pd.DataFrame([{

        # =============================
        # VARIABLES BASE
        # =============================
        "mes": fecha.month,
        "hora": hora,
        "precio_unitario": precio,

        "producto": producto,
        "categoria_producto": categoria_producto,
        "tipo_promocion": tipo_promocion,
        "tipo_zona": tipo_zona,
        "ubicacion_tienda": ubicacion_tienda,
        "clima": clima,

        # =============================
        # VARIABLES DERIVADAS
        # =============================
        "es_fin_semana": 1 if fecha.weekday() >= 5 else 0,

        "hora_pico": 1 if (
            12 <= hora <= 14 or
            18 <= hora <= 21
        ) else 0,

        "producto_promocion":
            f"{producto}_{tipo_promocion}",

        "temporada": (
            "Q1" if fecha.month <= 3 else
            "Q2" if fecha.month <= 6 else
            "Q3" if fecha.month <= 9 else
            "Q4"
        )
    }])

    return df, dia_semana


# =============================
# UI
# =============================
def show_prediccion():

    st.title("🤖 Predicción de Ventas")

    model, encoders = load_assets()

    # =============================
    # INPUTS
    # =============================
    fecha = st.date_input("Fecha")

    hora = st.number_input(
        "Hora",
        min_value=0,
        max_value=23,
        value=12
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
            "Gaseosa",
            "Energética"
        ]
    )

    precio = st.number_input(
        "Precio Unitario",
        min_value=0.0,
        value=3.50
    )

    tipo_promocion = st.selectbox(
        "Tipo de Promoción",
        [
            "normal",
            "descuento",
            "2x1",
            "combo"
        ]
    )

    tipo_zona = st.selectbox(
        "Tipo de Zona",
        [
            "urbana",
            "residencial",
            "comercial"
        ]
    )

    ubicacion_tienda = st.selectbox(
        "Ubicación de Tienda",
        [
            "Centro",
            "Mall",
            "Aeropuerto"
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

    # =============================
    # BOTÓN
    # =============================
    if st.button("Predecir"):

        # =============================
        # FEATURE ENGINEERING
        # =============================
        data, dia_semana = build_features(
            fecha,
            hora,
            producto,
            categoria_producto,
            precio,
            tipo_promocion,
            tipo_zona,
            ubicacion_tienda,
            clima
        )

        # =============================
        # ENCODING
        # =============================
        for col, le in encoders.items():

            if col in data.columns:

                data[col] = data[col].astype(str)

                data[col] = data[col].apply(
                    lambda x:
                    le.transform([x])[0]
                    if x in le.classes_
                    else -1
                )

        # =============================
        # PREDICCIÓN
        # =============================
        pred = model.predict(data)[0]

        # =============================
        # RESULTADO
        # =============================
        st.success(
            f"Cantidad estimada: {round(pred)} unidades"
        )

        # =============================
        # DETALLES
        # =============================
        st.subheader("📋 Resumen")

        resumen = pd.DataFrame([{
            "Fecha": fecha,
            "Día": dia_semana,
            "Producto": producto,
            "Categoría": categoria_producto,
            "Precio": precio,
            "Promoción": tipo_promocion,
            "Zona": tipo_zona,
            "Tienda": ubicacion_tienda,
            "Clima": clima,
            "Predicción": round(pred)
        }])

        st.dataframe(
            resumen,
            use_container_width=True
        )