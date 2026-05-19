import streamlit as st
import pandas as pd
import plotly.express as px

from utils.database import get_connection


# =====================================
# CONFIG
# =====================================
st.set_page_config(
    page_title="Dashboard Retail IA",
    layout="wide"
)

st.title("📊 Dashboard Inteligencia Comercial")


# =====================================
# CARGAR DATOS
# =====================================
@st.cache_data
def load_data():

    conn = get_connection()

    query = """
    SELECT *
    FROM gold_ml.ventas_predicha
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


df = load_data()


# =====================================
# VALIDACIÓN
# =====================================
if df.empty:

    st.warning("No existen datos en ventas_predicha")

    st.stop()


# =====================================
# CONVERTIR FECHA
# =====================================
df["fecha"] = pd.to_datetime(df["fecha"])


# =====================================
# SIDEBAR
# =====================================
st.sidebar.header("🔎 Filtros")


# =====================================
# FILTRO PRODUCTO
# =====================================
productos = st.sidebar.multiselect(
    "Producto",
    options=df["producto"].unique(),
    default=df["producto"].unique()
)


# =====================================
# FILTRO CLIMA
# =====================================
climas = st.sidebar.multiselect(
    "Clima",
    options=df["clima"].unique(),
    default=df["clima"].unique()
)


# =====================================
# FILTRO ZONA
# =====================================
zonas = st.sidebar.multiselect(
    "Zona",
    options=df["tipo_zona"].unique(),
    default=df["tipo_zona"].unique()
)


# =====================================
# FILTRO PROMOCIÓN
# =====================================
promociones = st.sidebar.multiselect(
    "Promoción",
    options=df["tipo_promocion"].unique(),
    default=df["tipo_promocion"].unique()
)


# =====================================
# APLICAR FILTROS
# =====================================
df = df[
    (df["producto"].isin(productos)) &
    (df["clima"].isin(climas)) &
    (df["tipo_zona"].isin(zonas)) &
    (df["tipo_promocion"].isin(promociones))
]


# =====================================
# KPIs
# =====================================
st.subheader("📌 Indicadores Principales")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Predicciones",
        len(df)
    )

with col2:
    st.metric(
        "Cantidad Predicha Total",
        int(df["cantidad_predicha"].sum())
    )

with col3:
    st.metric(
        "Promedio Predicción",
        round(df["cantidad_predicha"].mean(), 2)
    )

with col4:
    st.metric(
        "Productos Únicos",
        df["producto"].nunique()
    )


# =====================================
# SELECTBOX DE ANÁLISIS
# =====================================
st.subheader("📈 Análisis de Demanda")

analisis = st.selectbox(
    "Selecciona el tipo de análisis",
    [
        "Producto",
        "Clima",
        "Promociones",
        "Hora",
        "Zona",
        "Día",
        "Semana",
        "Mes"
    ]
)


# =====================================
# DEMANDA POR PRODUCTO
# =====================================
if analisis == "Producto":

    ventas_producto = (
        df.groupby("producto")["cantidad_predicha"]
        .sum()
        .reset_index()
        .sort_values(by="cantidad_predicha", ascending=False)
    )

    fig = px.bar(
        ventas_producto,
        x="producto",
        y="cantidad_predicha",
        text_auto=True,
        title="Demanda por Producto"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =====================================
# DEMANDA POR CLIMA
# =====================================
elif analisis == "Clima":

    ventas_clima = (
        df.groupby("clima")["cantidad_predicha"]
        .mean()
        .reset_index()
    )

    fig = px.pie(
        ventas_clima,
        names="clima",
        values="cantidad_predicha",
        title="Demanda según Clima"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =====================================
# IMPACTO PROMOCIONES
# =====================================
elif analisis == "Promociones":

    promo_df = (
        df.groupby("tipo_promocion")["cantidad_predicha"]
        .mean()
        .reset_index()
    )

    fig = px.bar(
        promo_df,
        x="tipo_promocion",
        y="cantidad_predicha",
        text_auto=True,
        title="Impacto de Promociones"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =====================================
# DEMANDA POR HORA
# =====================================
elif analisis == "Hora":

    hora_df = (
        df.groupby("hora")["cantidad_predicha"]
        .sum()
        .reset_index()
    )

    fig = px.line(
        hora_df,
        x="hora",
        y="cantidad_predicha",
        markers=True,
        title="Demanda por Hora"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =====================================
# DEMANDA POR ZONA
# =====================================
elif analisis == "Zona":

    zona_df = (
        df.groupby("tipo_zona")["cantidad_predicha"]
        .sum()
        .reset_index()
    )

    fig = px.bar(
        zona_df,
        x="tipo_zona",
        y="cantidad_predicha",
        text_auto=True,
        title="Demanda por Zona"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =====================================
# DEMANDA POR DÍA
# =====================================
elif analisis == "Día":

    dia_df = (
        df.groupby("fecha")["cantidad_predicha"]
        .sum()
        .reset_index()
        .sort_values(by="fecha")
    )

    fig = px.line(
        dia_df,
        x="fecha",
        y="cantidad_predicha",
        markers=True,
        title="Demanda por Día"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =====================================
# DEMANDA POR SEMANA
# =====================================
elif analisis == "Semana":

    df["semana"] = df["fecha"].dt.isocalendar().week

    semana_df = (
        df.groupby("semana")["cantidad_predicha"]
        .sum()
        .reset_index()
    )

    fig = px.bar(
        semana_df,
        x="semana",
        y="cantidad_predicha",
        text_auto=True,
        title="Demanda por Semana"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =====================================
# DEMANDA POR MES
# =====================================
elif analisis == "Mes":

    mes_df = (
        df.groupby("mes")["cantidad_predicha"]
        .sum()
        .reset_index()
        .sort_values(by="mes")
    )

    fig = px.line(
        mes_df,
        x="mes",
        y="cantidad_predicha",
        markers=True,
        title="Demanda por Mes"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =====================================
# TABLA FINAL
# =====================================
st.subheader("📋 Datos Analizados")

st.dataframe(
    df,
    use_container_width=True
)