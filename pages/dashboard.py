import streamlit as st
import pandas as pd
import plotly.express as px

from utils.database import get_connection


# =====================================
# DASHBOARD
# =====================================
def show_dashboard():

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
    # FILTROS
    # =====================================
    st.sidebar.header("🔎 Filtros")

    productos = st.sidebar.multiselect(
        "Producto",
        options=df["producto"].unique(),
        default=df["producto"].unique()
    )

    climas = st.sidebar.multiselect(
        "Clima",
        options=df["clima"].unique(),
        default=df["clima"].unique()
    )

    zonas = st.sidebar.multiselect(
        "Zona",
        options=df["tipo_zona"].unique(),
        default=df["tipo_zona"].unique()
    )

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
    # GRÁFICO 1
    # =====================================
    st.subheader("🛒 Demanda por Producto")

    ventas_producto = (
        df.groupby("producto")["cantidad_predicha"]
        .sum()
        .reset_index()
        .sort_values(by="cantidad_predicha", ascending=False)
    )

    fig_producto = px.bar(
        ventas_producto,
        x="producto",
        y="cantidad_predicha",
        text_auto=True
    )

    st.plotly_chart(
        fig_producto,
        use_container_width=True
    )


    # =====================================
    # GRÁFICO 2
    # =====================================
    st.subheader("🌦️ Demanda según Clima")

    ventas_clima = (
        df.groupby("clima")["cantidad_predicha"]
        .mean()
        .reset_index()
    )

    fig_clima = px.pie(
        ventas_clima,
        names="clima",
        values="cantidad_predicha"
    )

    st.plotly_chart(
        fig_clima,
        use_container_width=True
    )


    # =====================================
    # GRÁFICO 3
    # =====================================
    st.subheader("🏷️ Impacto de Promociones")

    promo_df = (
        df.groupby("tipo_promocion")["cantidad_predicha"]
        .mean()
        .reset_index()
    )

    fig_promo = px.bar(
        promo_df,
        x="tipo_promocion",
        y="cantidad_predicha",
        text_auto=True
    )

    st.plotly_chart(
        fig_promo,
        use_container_width=True
    )


    # =====================================
    # GRÁFICO 4
    # =====================================
    st.subheader("⏰ Demanda por Hora")

    hora_df = (
        df.groupby("hora")["cantidad_predicha"]
        .sum()
        .reset_index()
    )

    fig_hora = px.line(
        hora_df,
        x="hora",
        y="cantidad_predicha",
        markers=True
    )

    st.plotly_chart(
        fig_hora,
        use_container_width=True
    )


    # =====================================
    # GRÁFICO 5
    # =====================================
    st.subheader("🏪 Demanda por Zona")

    zona_df = (
        df.groupby("tipo_zona")["cantidad_predicha"]
        .sum()
        .reset_index()
    )

    fig_zona = px.bar(
        zona_df,
        x="tipo_zona",
        y="cantidad_predicha",
        text_auto=True
    )

    st.plotly_chart(
        fig_zona,
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