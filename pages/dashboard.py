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
    # CONVERTIR FECHAS
    # =====================================
    df["fecha"] = pd.to_datetime(df["fecha"])

    df["semana"] = df["fecha"].dt.isocalendar().week

    df["mes_nombre"] = df["fecha"].dt.strftime("%B")


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
    # DEMANDA POR PRODUCTO
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
    # DEMANDA POR CLIMA
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
    # PROMOCIONES
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
    # HORAS PICO
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
    # ZONAS
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
    # GRÁFICO 6
    # DEMANDA DIARIA
    # =====================================
    st.subheader("📅 Demanda por Día")

    dia_df = (
        df.groupby("fecha")["cantidad_predicha"]
        .sum()
        .reset_index()
    )

    fig_dia = px.line(
        dia_df,
        x="fecha",
        y="cantidad_predicha",
        markers=True
    )

    st.plotly_chart(
        fig_dia,
        use_container_width=True
    )


    # =====================================
    # GRÁFICO 7
    # DEMANDA SEMANAL
    # =====================================
    st.subheader("🗓️ Demanda por Semana")

    semana_df = (
        df.groupby("semana")["cantidad_predicha"]
        .sum()
        .reset_index()
    )

    fig_semana = px.bar(
        semana_df,
        x="semana",
        y="cantidad_predicha",
        text_auto=True
    )

    st.plotly_chart(
        fig_semana,
        use_container_width=True
    )


    # =====================================
    # GRÁFICO 8
    # DEMANDA MENSUAL
    # =====================================
    st.subheader("📦 Demanda por Mes")

    mes_df = (
        df.groupby("mes_nombre")["cantidad_predicha"]
        .sum()
        .reset_index()
    )

    orden_meses = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December"
    ]

    mes_df["mes_nombre"] = pd.Categorical(
        mes_df["mes_nombre"],
        categories=orden_meses,
        ordered=True
    )

    mes_df = mes_df.sort_values("mes_nombre")

    fig_mes = px.line(
        mes_df,
        x="mes_nombre",
        y="cantidad_predicha",
        markers=True
    )

    st.plotly_chart(
        fig_mes,
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