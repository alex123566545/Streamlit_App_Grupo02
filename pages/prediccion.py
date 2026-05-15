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
    response.raise_for_status()  # 🔥 evita silencios si falla
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
# UI
# =============================
def show_prediccion():

    st.title("🤖 Predicción de Ventas")

    # 🔌 conexión a base de datos (si luego quieres guardar predicción)
    conn = get_connection()

    # 🤖 modelo + encoders desde Supabase Storage
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
        # INPUT BASE
        # =============================
        data = pd.DataFrame([{
            "hora": hora,
            "producto": producto,
            "precio_unitario": precio,
            "clima": clima
        }])

        # =============================
        # ENCODING (igual al entrenamiento)
        # =============================
        for col, le in encoders.items():
            if col in data.columns:
                data[col] = data[col].astype(str)
                data[col] = data[col].apply(
                    lambda x: le.transform([x])[0] if x in le.classes_ else -1
                )

        # =============================
        # PREDICCIÓN
        # =============================
        pred = model.predict(data)[0]

        st.success(f"Cantidad estimada: {round(pred)}")