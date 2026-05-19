import streamlit as st
import pandas as pd
import plotly.express as px



# =====================================
# CONFIG
# =====================================
st.set_page_config(
    page_title="Dashboard Retail IA",
    layout="wide"
)


# =====================================
# DASHBOARD
# =====================================
def show_dashboard():

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
    # VARIABLES TEMPORALES
    # =====================================
    df["anio"] = df["fecha"].dt.year

    df["mes_nombre"] = df["fecha"].dt.strftime("%B")

    df["semana"] = df["fecha"].dt.isocalendar().week

    df["dia"] = df["fecha"].dt.day_name()

    # =====================================
    # SIDEBAR
    # =====================================
    st.sidebar.header("🔎 Filtros")

    # =====================================
    # FILTRO PRODUCTOS
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
    # FILTRO TIEMPO
    # =====================================
    tipo_tiempo = st.sidebar.selectbox(
        "Analizar Demanda Por",
        [
            "Día",
            "Semana",
            "Mes",
            "Hora"
        ]
    )

    # =====================================
    # FILTRO PRODUCTO ANÁLISIS
    # =====================================
    producto_analisis = st.sidebar.selectbox(
        "Producto para análisis temporal",
        ["Todos"] + list(df["producto"].unique())
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
    # FILTRO PRODUCTO TEMPORAL
    # =====================================
    if producto_analisis != "Todos":

        df_temporal = df[
            df["producto"] == producto_analisis
        ]

    else:

        df_temporal = df.copy()

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
        producto_top = (
            df.groupby("producto")["cantidad_predicha"]
            .sum()
            .idxmax()
        )

        st.metric(
            "Producto Más Demandado",
            producto_top
        )

    # =====================================
    # DEMANDA TEMPORAL
    # =====================================
    st.subheader("📈 Demanda Temporal")

    if tipo_tiempo == "Día":

        tiempo_df = (
            df_temporal.groupby("dia")["cantidad_predicha"]
            .sum()
            .reset_index()
        )

        orden_dias = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday"
        ]

        tiempo_df["dia"] = pd.Categorical(
            tiempo_df["dia"],
            categories=orden_dias,
            ordered=True
        )

        tiempo_df = tiempo_df.sort_values("dia")

        fig_tiempo = px.bar(
            tiempo_df,
            x="dia",
            y="cantidad_predicha",
            text_auto=True
        )

    elif tipo_tiempo == "Semana":

        tiempo_df = (
            df_temporal.groupby("semana")["cantidad_predicha"]
            .sum()
            .reset_index()
        )

        fig_tiempo = px.line(
            tiempo_df,
            x="semana",
            y="cantidad_predicha",
            markers=True
        )

    elif tipo_tiempo == "Mes":

        tiempo_df = (
            df_temporal.groupby("mes_nombre")["cantidad_predicha"]
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

        tiempo_df["mes_nombre"] = pd.Categorical(
            tiempo_df["mes_nombre"],
            categories=orden_meses,
            ordered=True
        )

        tiempo_df = tiempo_df.sort_values("mes_nombre")

        fig_tiempo = px.line(
            tiempo_df,
            x="mes_nombre",
            y="cantidad_predicha",
            markers=True
        )

    else:

        tiempo_df = (
            df_temporal.groupby("hora")["cantidad_predicha"]
            .sum()
            .reset_index()
        )

        fig_tiempo = px.line(
            tiempo_df,
            x="hora",
            y="cantidad_predicha",
            markers=True
        )

    st.plotly_chart(
        fig_tiempo,
        use_container_width=True
    )

    # =====================================
    # PRODUCTOS Y TIEMPO
    # =====================================
    st.subheader("🛒 Producto vs Tiempo")

    producto_tiempo = (
        df.groupby(
            ["producto", "mes_nombre"]
        )["cantidad_predicha"]
        .sum()
        .reset_index()
    )

    fig_producto_tiempo = px.bar(
        producto_tiempo,
        x="mes_nombre",
        y="cantidad_predicha",
        color="producto",
        barmode="group"
    )

    st.plotly_chart(
        fig_producto_tiempo,
        use_container_width=True
    )

    # =====================================
    # PROMOCIONES Y TIEMPO
    # =====================================
    st.subheader("🏷️ Promociones vs Tiempo")

    promo_df = (
        df.groupby(
            ["tipo_promocion", "mes_nombre"]
        )["cantidad_predicha"]
        .mean()
        .reset_index()
    )

    fig_promo = px.line(
        promo_df,
        x="mes_nombre",
        y="cantidad_predicha",
        color="tipo_promocion",
        markers=True
    )

    st.plotly_chart(
        fig_promo,
        use_container_width=True
    )

    # =====================================
    # CLIMA Y TIEMPO
    # =====================================
    st.subheader("🌦️ Clima vs Tiempo")

    clima_df = (
        df.groupby(
            ["clima", "mes_nombre"]
        )["cantidad_predicha"]
        .mean()
        .reset_index()
    )

    fig_clima = px.line(
        clima_df,
        x="mes_nombre",
        y="cantidad_predicha",
        color="clima",
        markers=True
    )

    st.plotly_chart(
        fig_clima,
        use_container_width=True
    )

    # =====================================
    # ZONAS Y TIEMPO
    # =====================================
    st.subheader("🏪 Zona vs Tiempo")

    zona_df = (
        df.groupby(
            ["tipo_zona", "mes_nombre"]
        )["cantidad_predicha"]
        .sum()
        .reset_index()
    )

    fig_zona = px.bar(
        zona_df,
        x="mes_nombre",
        y="cantidad_predicha",
        color="tipo_zona",
        barmode="group"
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