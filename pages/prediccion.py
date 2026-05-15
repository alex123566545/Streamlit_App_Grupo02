import streamlit as st
import pandas as pd
import requests
import pickle
from utils.database import get_connection


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
# FEATURE ENGINEERING IGUAL AL ETL
# =============================
def build_features(fecha, hora, producto, precio, clima):

    df = pd.DataFrame([{
        "mes": fecha.month,
        "hora": hora,
        "precio_unitario": precio,

        "es_fin_semana": 1 if fecha.weekday() >= 5 else 0,
        "hora_pico": 1 if (12 <= hora <= 14 or 18 <= hora <= 21) else 0,

        "producto": producto,
        "categoria_producto": "default",
        "tipo_promocion": "normal",
        "tipo_zona": "urbana",
        "ubicacion_tienda": "default",
        "clima": clima,

        "producto_promocion": f"{producto}_normal",

        "temporada": (
            "Q1" if fecha.month <= 3 else
            "Q2" if fecha.month <= 6 else
            "Q3" if fecha.month <= 9 else
            "Q4"
        )
    }])

    return df


# =============================
# UI
# =============================
def show_prediccion():

    st.title("🤖 Predicción de Ventas")

    model, encoders = load_assets()

    fecha = st.date_input("Fecha")

    hora = st.number_input(
        "Hora",
        min_value=0,
        max_value=23
    )

    producto = st.selectbox(
        "Producto",
        ["Coca Cola", "Red Bull", "Inca Kola"]
    )

    precio = st.number_input(
        "Precio",
        min_value=0.0
    )

    clima = st.selectbox(
        "Clima",
        ["Soleado", "Lluvioso", "Nublado"]
    )

    if st.button("Predecir"):

        # =============================
        # CREAR FEATURES COMPLETAS
        # =============================
        data = build_features(fecha, hora, producto, precio, clima)

        # =============================
        # ENCODING IGUAL AL ENTRENAMIENTO
        # =============================
        for col, le in encoders.items():
            if col in data.columns:
                data[col] = data[col].astype(str)
                data[col] = data[col].apply(
                    lambda x: le.transform([x])[0] if x in le.classes_ else -1
                )

        # =============================
        # PREDICCIÓN REAL
        # =============================
        pred = model.predict(data)[0]

        st.success(f"Cantidad estimada: {round(pred)}")