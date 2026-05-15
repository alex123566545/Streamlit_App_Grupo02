import streamlit as st
import pandas as pd
import requests
import pickle

from utils.database import get_connection


# =====================================
# DESCARGAR PKL DESDE SUPABASE
# =====================================
def load_file(url):

    response = requests.get(url)

    response.raise_for_status()

    return pickle.loads(response.content)


# =====================================
# CARGAR MODELO + ENCODERS + FEATURES
# =====================================
@st.cache_resource
def load_assets():

    MODEL_URL = "https://klbmaoqxfvjsczwrrwkj.supabase.co/storage/v1/object/public/models/model.pkl"

    ENCODERS_URL = "https://klbmaoqxfvjsczwrrwkj.supabase.co/storage/v1/object/public/models/encoders.pkl"

    FEATURES_URL = "https://klbmaoqxfvjsczwrrwkj.supabase.co/storage/v1/object/public/models/features.pkl"

    model = load_file(MODEL_URL)

    encoders = load_file(ENCODERS_URL)

    features = load_file(FEATURES_URL)

    return model, encoders, features


# =====================================
# CARGAR DATOS GOLD_DIM
# =====================================
@st.cache_data
def load_dimensions():

    conn = get_connection()

    productos = pd.read_sql("""
        SELECT DISTINCT producto, categoria_producto
        FROM gold_dim.dim_producto
        ORDER BY producto
    """, conn)

    promociones = pd.read_sql("""
        SELECT DISTINCT tipo_promocion
        FROM gold_dim.dim_promocion
        ORDER BY tipo_promocion
    """, conn)

    tiendas = pd.read_sql("""
        SELECT DISTINCT ubicacion_tienda, tipo_zona
        FROM gold_dim.dim_tienda
        ORDER BY ubicacion_tienda
    """, conn)

    climas = pd.read_sql("""
        SELECT DISTINCT clima
        FROM gold_dim.dim_clima
        ORDER BY clima
    """, conn)

    conn.close()

    return productos, promociones, tiendas, climas


# =====================================
# FEATURE ENGINEERING
# =====================================
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

    df = pd.DataFrame([{

        "mes": fecha.month,

        "hora": hora,

        "precio_unitario": precio,

        "es_fin_semana":
            1 if fecha.weekday() >= 5 else 0,

        "hora_pico":
            1 if (
                12 <= hora <= 14 or
                18 <= hora <= 21
            ) else 0,

        "producto": producto,

        "categoria_producto": categoria_producto,

        "tipo_promocion": tipo_promocion,

        "tipo_zona": tipo_zona,

        "ubicacion_tienda": ubicacion_tienda,

        "clima": clima,

        "producto_promocion":
            f"{producto}_{tipo_promocion}",

        "temporada": (
            "Q1" if fecha.month <= 3 else
            "Q2" if fecha.month <= 6 else
            "Q3" if fecha.month <= 9 else
            "Q4"
        )

    }])

    return df


# =====================================
# UI
# =====================================
def show_prediccion():

    st.title("🤖 Predicción de Ventas")

    # ==============================
    # CARGAR RECURSOS
    # ==============================
    model, encoders, features = load_assets()

    productos_df, promociones_df, tiendas_df, climas_df = load_dimensions()

    # ==============================
    # FECHA
    # ==============================
    fecha = st.date_input("Fecha")

    # ==============================
    # HORA
    # ==============================
    hora = st.number_input(
        "Hora",
        min_value=0,
        max_value=23,
        value=12
    )

    # ==============================
    # PRODUCTO
    # ==============================
    producto = st.selectbox(
        "Producto",
        productos_df["producto"].unique()
    )

    categoria_producto = productos_df[
        productos_df["producto"] == producto
    ]["categoria_producto"].values[0]

    st.info(f"Categoría: {categoria_producto}")

    # ==============================
    # PRECIO
    # ==============================
    precio = st.number_input(
        "Precio Unitario",
        min_value=0.0,
        value=3.50
    )

    # ==============================
    # PROMOCIÓN
    # ==============================
    tipo_promocion = st.selectbox(
        "Tipo Promoción",
        promociones_df["tipo_promocion"].unique()
    )

    # ==============================
    # TIENDA
    # ==============================
    ubicacion_tienda = st.selectbox(
        "Ubicación Tienda",
        tiendas_df["ubicacion_tienda"].unique()
    )

    tipo_zona = tiendas_df[
        tiendas_df["ubicacion_tienda"] == ubicacion_tienda
    ]["tipo_zona"].values[0]

    st.info(f"Zona: {tipo_zona}")

    # ==============================
    # CLIMA
    # ==============================
    clima = st.selectbox(
        "Clima",
        climas_df["clima"].unique()
    )

    # ==============================
    # PREDECIR
    # ==============================
    if st.button("Predecir"):

        data = build_features(
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

        # ==============================
        # ENCODING
        # ==============================
        for col, le in encoders.items():

            if col in data.columns:

                data[col] = data[col].astype(str)

                data[col] = data[col].apply(
                    lambda x:
                    le.transform([x])[0]
                    if x in le.classes_
                    else -1
                )

        # ==============================
        # ORDEN EXACTO DEL ENTRENAMIENTO
        # ==============================
        data = data[features]

        # ==============================
        # PREDICCIÓN
        # ==============================
        pred = model.predict(data)[0]

        st.success(
            f"Cantidad estimada: {round(pred)} unidades"
        )
