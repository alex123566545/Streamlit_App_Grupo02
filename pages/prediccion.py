import streamlit as st
import pandas as pd
import requests
import pickle
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np
from datetime import date, timedelta

from utils.database import get_connection


# =========================================================
# ESTILOS
# =========================================================
PREDICCION_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

    .main-header {
        font-family: 'Syne', sans-serif;
        font-size: 1.8rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 0.2rem;
        letter-spacing: -0.5px;
    }
    .sub-header {
        font-size: 0.9rem;
        color: #ffffff;
        margin-bottom: 1.5rem;
    }

    /* Badges de demanda */
    .badge-high { background: rgba(52,211,153,0.15); color: #34d399; border: 1px solid rgba(52,211,153,0.3); padding: 4px 12px; border-radius: 20px; font-weight: 600; }
    .badge-med  { background: rgba(251,191,36,0.15);  color: #fbbf24; border: 1px solid rgba(251,191,36,0.3);  padding: 4px 12px; border-radius: 20px; font-weight: 600; }
    .badge-low  { background: rgba(251,113,133,0.15); color: #fb7185; border: 1px solid rgba(251,113,133,0.3); padding: 4px 12px; border-radius: 20px; font-weight: 600; }

    /* Cards de segmento */
    .seg-card {
        background: #1c1f2b;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 0.75rem;
        transition: all 0.2s ease;
    }
    .seg-card:hover { border-color: rgba(79,142,255,0.25); transform: translateY(-1px); }
    .seg-label { font-size: 0.72rem; color: #ffffff; text-transform: uppercase; letter-spacing: 0.09em; font-weight: 600; margin-bottom: 0.3rem; }
    .seg-value { font-family: 'Syne', sans-serif; font-size: 1.5rem; font-weight: 800; color: #ffffff; line-height: 1; }
    .seg-sub   { font-size: 0.8rem; color: #ffffff; margin-top: 0.25rem; }

    /* Selectbox oscuro */
    div[data-baseweb="select"] > div {
        background: #1c1f2b !important;
        border-color: rgba(255,255,255,0.12) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
    }
    div[data-baseweb="select"] > div > div { color: #ffffff !important; }
    div[data-baseweb="popover"] ul  { background: #1c1f2b !important; border: 1px solid rgba(255,255,255,0.10) !important; }
    div[data-baseweb="popover"] li  { background: #1c1f2b !important; color: #ffffff !important; }
    div[data-baseweb="popover"] li:hover { background: #20243a !important; color: #ffffff !important; }
    div[data-baseweb="tag"] { background: rgba(79,142,255,0.2) !important; color: #ffffff !important; }
    div[data-baseweb="tag"] span { color: #ffffff !important; }

    /* Section header */
    .sec-header { display: flex; align-items: center; gap: 0.6rem; margin: 1.75rem 0 0.75rem; }
    .sec-dot { width: 8px; height: 8px; border-radius: 50%; background: #4f8eff; flex-shrink: 0; }
    .sec-title { font-family: 'Syne', sans-serif; font-size: 1rem; font-weight: 700; color: #ffffff; }
</style>
"""


# =========================================================
# CARGA DE MODELO Y FEATURES
# =========================================================
def _load_pkl(url: str):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return pickle.loads(response.content)


@st.cache_resource(show_spinner="Cargando modelo predictivo…")
def load_assets():
    MODEL_URL    = "https://klbmaoqxfvjsczwrrwkj.supabase.co/storage/v1/object/public/models/model.pkl"
    FEATURES_URL = "https://klbmaoqxfvjsczwrrwkj.supabase.co/storage/v1/object/public/models/features.pkl"
    return _load_pkl(MODEL_URL), _load_pkl(FEATURES_URL)


# =========================================================
# CARGA DE DIMENSIONES
# =========================================================
@st.cache_data(show_spinner="Cargando catálogos…", ttl=3600)
def load_dimensions():
    conn = get_connection()
    try:
        productos   = pd.read_sql("SELECT DISTINCT producto, categoria_producto FROM gold_dim.dim_producto ORDER BY producto", conn)
        promociones = pd.read_sql("SELECT DISTINCT tipo_promocion FROM gold_dim.dim_promocion ORDER BY tipo_promocion", conn)
        tiendas     = pd.read_sql("SELECT DISTINCT ubicacion_tienda, tipo_zona FROM gold_dim.dim_tienda ORDER BY ubicacion_tienda", conn)
        climas      = pd.read_sql("SELECT DISTINCT clima FROM gold_dim.dim_clima ORDER BY clima", conn)
        precios     = pd.read_sql("SELECT producto, ROUND(AVG(precio_unitario),2) AS precio_promedio FROM gold_ml.ventas_dataset GROUP BY producto", conn)
    finally:
        conn.close()
    return productos, promociones, tiendas, climas, precios


@st.cache_data(show_spinner=False, ttl=3600)
def load_history():
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT * FROM gold_ml.ventas_predicha", conn)
    finally:
        conn.close()
    return df


# =========================================================
# FEATURE ENGINEERING
# =========================================================
def _lower(s: str) -> str:
    return str(s).strip().lower()


def build_features(
    fecha, hora, producto, categoria_producto,
    precio, tipo_promocion, tipo_zona,
    ubicacion_tienda, clima
) -> pd.DataFrame:
    trimestre = (
        1 if fecha.month <= 3 else
        2 if fecha.month <= 6 else
        3 if fecha.month <= 9 else 4
    )
    return pd.DataFrame([{
        "mes":                fecha.month,
        "dia_mes":            fecha.day,
        "hora":               hora,
        "precio_unitario":    float(precio),
        "trimestre":          trimestre,
        "es_fin_semana":      int(fecha.weekday() >= 5),
        "hora_pico":          int(12 <= hora <= 14 or 18 <= hora <= 21),
        "producto":           _lower(producto),
        "categoria_producto": _lower(categoria_producto),
        "tipo_promocion":     _lower(tipo_promocion),
        "tipo_zona":          _lower(tipo_zona),
        "ubicacion_tienda":   _lower(ubicacion_tienda),
        "clima":              _lower(clima),
        "producto_promocion": f"{_lower(producto)}_{_lower(tipo_promocion)}",
        "temporada":          ["Q1","Q2","Q3","Q4"][trimestre - 1],
    }])


# =========================================================
# PREDICCIÓN MULTI-DÍA
# =========================================================
def predecir_rango(
    model, features,
    fecha_inicio: date,
    n_dias: int,
    hora: int,
    producto: str,
    categoria_producto: str,
    precio: float,
    tipo_promocion: str,
    tipo_zona: str,
    ubicacion_tienda: str,
    clima: str,
    precio_promedio: float,
) -> tuple[int, list[dict]]:
    total   = 0.0
    detalle = []
    for i in range(n_dias):
        f = fecha_inicio + timedelta(days=i)
        data = build_features(
            f, hora, producto, categoria_producto,
            precio, tipo_promocion, tipo_zona,
            ubicacion_tienda, clima
        )[features]
        pred_raw = model.predict(data)[0]
        pred_adj = aplicar_elasticidad(pred_raw, precio, precio_promedio)
        pred_dia = max(1, round(pred_adj))
        total += pred_dia
        detalle.append({
            "fecha":      f,
            "dia_semana": ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"][f.weekday()],
            "es_finde":   f.weekday() >= 5,
            "unidades":   pred_dia,
            "ingreso":    round(pred_dia * precio, 2),
        })
    return max(1, round(total)), detalle


# =========================================================
# ELASTICIDAD-PRECIO
# =========================================================
def aplicar_elasticidad(
    pred_raw: float,
    precio: float,
    precio_promedio: float,
    elasticidad: float = -1.2,
) -> float:
    if precio_promedio <= 0:
        return pred_raw
    factor = (precio / precio_promedio) ** elasticidad
    return max(1.0, pred_raw * factor)


# =========================================================
# NIVEL DE DEMANDA
# =========================================================
def demanda_badge(pred_dia: int):
    if pred_dia < 15:
        return "🔴 Demanda Baja", "low"
    elif pred_dia < 35:
        return "🟡 Demanda Media", "med"
    else:
        return "🟢 Demanda Alta", "high"


# =========================================================
# HELPERS DE VISUALIZACIÓN
# =========================================================
PLOTLY_DARK = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_family="DM Sans",
    font_color="#ffffff",
    margin=dict(t=40, b=30, l=10, r=10),
    legend=dict(bgcolor="rgba(22,25,32,0.8)", bordercolor="rgba(255,255,255,0.07)", borderwidth=1),
)
COLOR_SEQ = ["#4f8eff", "#a78bfa", "#34d399", "#f97316", "#fb7185", "#fbbf24"]

def dark_fig(fig):

    fig.update_layout(**PLOTLY_DARK)

    fig.update_layout(
        font=dict(
            color="#ffffff",
            family="DM Sans"
        ),

        title_font=dict(
            color="#ffffff"
        )
    )

    fig.update_xaxes(
        gridcolor="rgba(255,255,255,0.08)",
        linecolor="rgba(255,255,255,0.25)",
        tickfont=dict(color="#ffffff"),
        title_font=dict(color="#ffffff"),
    )

    fig.update_yaxes(
        gridcolor="rgba(255,255,255,0.08)",
        linecolor="rgba(255,255,255,0.25)",
        tickfont=dict(color="#ffffff"),
        title_font=dict(color="#ffffff"),
    )

    fig.update_traces(
        textfont=dict(color="#ffffff")
    )

    return fig

def sec(title: str):
    st.markdown(
        f'<div class="sec-header"><div class="sec-dot"></div>'
        f'<div class="sec-title">{title}</div></div>',
        unsafe_allow_html=True,
    )


# =========================================================
# UI PRINCIPAL
# =========================================================
def show_prediccion():

    st.markdown(PREDICCION_CSS, unsafe_allow_html=True)

    st.markdown(
        '<p class="main-header">🏪 Sistema de Inteligencia Comercial Predictiva</p>'
        '<p class="sub-header">Predicción de demanda · Fidelización · Análisis Económico · Modelo: Random Forest Regressor</p>',
        unsafe_allow_html=True,
    )

    with st.spinner("Iniciando recursos…"):
        model, features = load_assets()
        productos_df, promociones_df, tiendas_df, climas_df, precios_df = load_dimensions()
        historico_df = load_history()

    tab_pred, tab_hist, tab_fidelizacion, tab_economico = st.tabs([
        "📊 Predicción de Demanda",
        "📋 Histórico",
        "🏆 Fidelización de Clientes",
        "💰 Análisis Económico",
    ])

    # ═══════════════════════════════════════════════════════
# TAB 1 — PREDICCIÓN
# ═══════════════════════════════════════════════════════
with tab_pred:

    st.subheader("⚙️ Parámetros de la transacción")
    col_l, col_r = st.columns([1, 2])

    with col_l:
        fecha = st.date_input("📅 Fecha de inicio", value=date.today())
        hora = 12

        producto = st.selectbox(
            "🛒 Producto",
            productos_df["producto"].dropna().unique()
        )

        categoria_producto = productos_df.loc[
            productos_df["producto"] == producto,
            "categoria_producto"
        ].iloc[0]

        st.caption(f"Categoría: **{categoria_producto}**")

        precio_data = precios_df.loc[
            precios_df["producto"] == producto,
            "precio_promedio"
        ]

        precio_promedio = float(precio_data.iloc[0]) if not precio_data.empty else 10.0

        st.caption(f"💰 Precio histórico promedio: S/ {precio_promedio}")

        precio = st.slider(
            "💲 Precio unitario (S/)",
            min_value=1.0,
            max_value=30.0,
            value=float(precio_promedio),
            step=0.10,
        )

        tipo_promocion = st.selectbox(
            "🏷️ Tipo de promoción",
            promociones_df["tipo_promocion"].dropna().unique()
        )

        ubicacion_tienda = st.selectbox(
            "📍 Ubicación de tienda",
            tiendas_df["ubicacion_tienda"].dropna().unique()
        )

        zona_data = tiendas_df.loc[
            tiendas_df["ubicacion_tienda"] == ubicacion_tienda,
            "tipo_zona"
        ]

        tipo_zona = zona_data.iloc[0] if not zona_data.empty else "Residencial"

        st.caption(f"Zona: **{tipo_zona}**")

        clima = st.selectbox(
            "🌤️ Clima",
            climas_df["clima"].dropna().unique()
        )

    with col_r:

        predecir = st.button(
            "🔮 Generar Predicción",
            use_container_width=True
        )

        if predecir:

            # =====================================================
            # PREDICCIÓN PRINCIPAL
            # =====================================================
            data_dia = build_features(
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

            data_dia = data_dia.reindex(columns=features, fill_value=0)

            pred_raw = model.predict(data_dia)[0]

            pred_dia = max(
                1,
                round(
                    aplicar_elasticidad(
                        pred_raw,
                        precio,
                        precio_promedio
                    )
                )
            )

            # =====================================================
            # PREDICCIÓN SEMANA / MES
            # =====================================================
            pred_sem, detalle_sem = predecir_rango(
                model,
                features,
                fecha,
                7,
                hora,
                producto,
                categoria_producto,
                precio,
                tipo_promocion,
                tipo_zona,
                ubicacion_tienda,
                clima,
                precio_promedio,
            )

            pred_mes, detalle_mes = predecir_rango(
                model,
                features,
                fecha,
                30,
                hora,
                producto,
                categoria_producto,
                precio,
                tipo_promocion,
                tipo_zona,
                ubicacion_tienda,
                clima,
                precio_promedio,
            )

            ingreso_dia = round(pred_dia * precio, 2)
            ingreso_sem = round(pred_sem * precio, 2)
            ingreso_mes = round(pred_mes * precio, 2)

            # =====================================================
            # RESULTADOS
            # =====================================================
            sec("📊 Resultados predictivos")

            c1, c2, c3 = st.columns(3)

            c1.metric("Predicción diaria", f"{pred_dia} uds")
            c2.metric("Predicción semanal", f"{pred_sem} uds")
            c3.metric("Predicción mensual", f"{pred_mes} uds")

            c1.metric("Ingreso diario", f"S/ {ingreso_dia}")
            c2.metric("Ingreso semanal", f"S/ {ingreso_sem}")
            c3.metric("Ingreso mensual", f"S/ {ingreso_mes}")

            # =====================================================
            # DEMANDA
            # =====================================================
            label, nivel = demanda_badge(pred_dia)

            st.markdown(
                f'**Nivel de demanda:** <span class="badge-{nivel}">{label}</span>',
                unsafe_allow_html=True,
            )

            # =====================================================
            # FACTORES
            # =====================================================
            sec("🧠 Factores detectados")

            factores = []

            if _lower(tipo_promocion) not in (
                "ninguno",
                "none",
                "sin promoción"
            ):
                factores.append("✔ Promoción activa")

            if 12 <= hora <= 14 or 18 <= hora <= 21:
                factores.append("✔ Hora pico")

            if _lower(tipo_zona) == "comercial":
                factores.append("✔ Zona comercial")

            if _lower(clima) == "soleado":
                factores.append("✔ Clima favorable")

            if fecha.weekday() >= 5:
                factores.append("✔ Fin de semana")

            if precio < precio_promedio:
                factores.append("✔ Precio competitivo")

            st.info(
                "  ·  ".join(factores)
                if factores
                else "No se detectaron factores favorables adicionales."
            )

            # =====================================================
            # PROYECCIÓN
            # =====================================================
            sec("📅 Proyección temporal (unidades)")

            proy_df = pd.DataFrame({
                "Periodo": ["Día", "Semana", "Mes"],
                "Cantidad": [pred_dia, pred_sem, pred_mes],
            })

            fig_proy = dark_fig(
                px.bar(
                    proy_df,
                    x="Periodo",
                    y="Cantidad",
                    text_auto=True,
                    color="Periodo",
                    color_discrete_sequence=[
                        "#4f8eff",
                        "#a78bfa",
                        "#34d399"
                    ],
                )
            )

            fig_proy.update_layout(
                showlegend=False,
                height=300,
            )

            fig_proy.update_traces(
                textfont=dict(color="black")
            )

            st.plotly_chart(
                fig_proy,
                use_container_width=True
            )

            # =====================================================
            # DETALLE SEMANAL
            # =====================================================
            sec("🗓️ Detalle día a día — próximos 7 días")

            st.caption(
                "Cada día se predice de forma independiente con su propio contexto."
            )

            det_df = pd.DataFrame(detalle_sem)

            det_df["fecha"] = det_df["fecha"].astype(str)

            det_df.columns = [
                "Fecha",
                "Día",
                "¿Finde?",
                "Unidades",
                "Ingreso (S/)"
            ]

            det_df["¿Finde?"] = det_df["¿Finde?"].map({
                True: "✅",
                False: "—"
            })

            st.dataframe(
                det_df,
                hide_index=True,
                use_container_width=True
            )

            fig_det = dark_fig(
                px.bar(
                    det_df,
                    x="Fecha",
                    y="Unidades",
                    color="¿Finde?",
                    color_discrete_map={
                        "✅": "#a78bfa",
                        "—": "#4f8eff"
                    },
                    text_auto=True,
                    title="Unidades por día (morado = fin de semana)",
                )
            )

            fig_det.update_layout(
                height=320,
                showlegend=False,
            )

            fig_det.update_traces(
                textfont=dict(color="black")
            )

            st.plotly_chart(
                fig_det,
                use_container_width=True
            )

            # =====================================================
            # HISTÓRICO
            # =====================================================
            sec("📈 Comparación con histórico")

            hist_prod = historico_df[
                historico_df["producto"] == _lower(producto)
            ]

            if not hist_prod.empty:

                prom_hist = round(
                    hist_prod["cantidad_predicha"].mean(),
                    2
                )

                variacion = round(
                    ((pred_dia - prom_hist) / max(prom_hist, 1)) * 100,
                    2
                )

                h1, h2 = st.columns(2)

                h1.metric(
                    "Promedio histórico diario",
                    prom_hist
                )

                h2.metric(
                    "Variación esperada",
                    f"{variacion}%",
                    delta=f"{variacion}%"
                )

            else:
                st.caption(
                    "Sin datos históricos para este producto."
                )

            # =====================================================
            # SIMULACIÓN
            # =====================================================
            sec("💹 Simulación de escenarios de precio")

            sims = []

            for factor in [0.8, 0.9, 1.0, 1.1, 1.2]:

                p_sim = round(precio * factor, 2)

                d_sim = build_features(
                    fecha,
                    hora,
                    producto,
                    categoria_producto,
                    p_sim,
                    tipo_promocion,
                    tipo_zona,
                    ubicacion_tienda,
                    clima
                )

                d_sim = d_sim.reindex(
                    columns=features,
                    fill_value=0
                )

                pred_sim = max(
                    1,
                    round(
                        aplicar_elasticidad(
                            model.predict(d_sim)[0],
                            p_sim,
                            precio_promedio
                        )
                    )
                )

                sims.append({
                    "Escenario": f"×{factor:.1f}",
                    "Precio (S/)": p_sim,
                    "Demanda (uds)": pred_sim,
                    "Ingreso (S/)": round(pred_sim * p_sim, 2),
                })

            sim_df = pd.DataFrame(sims)

            st.dataframe(
                sim_df,
                use_container_width=True,
                hide_index=True
            )

            fig_sim = dark_fig(
                px.line(
                    sim_df,
                    x="Precio (S/)",
                    y="Ingreso (S/)",
                    markers=True,
                    title="Curva ingreso vs precio",
                    color_discrete_sequence=["#4f8eff"],
                )
            )

            fig_sim.update_layout(
                height=300,
            )

            st.plotly_chart(
                fig_sim,
                use_container_width=True
            )

            # =====================================================
            # RECOMENDACIÓN
            # =====================================================
            sec("💡 Recomendación comercial")

            mejor = sim_df.loc[
                sim_df["Ingreso (S/)"].idxmax()
            ]

            st.success(
                f"**Precio óptimo sugerido:** S/ {mejor['Precio (S/)']}\n\n"
                f"**Demanda esperada:** {mejor['Demanda (uds)']} unidades\n\n"
                f"**Ingreso estimado:** S/ {mejor['Ingreso (S/)']}"
            )

            # =====================================================
            # IMPORTANCIA VARIABLES
            # =====================================================
            sec("⚙️ Variables más influyentes (Random Forest)")

            try:

                importancias = model.named_steps[
                    "model"
                ].feature_importances_

                feat_names = model.named_steps[
                    "preprocess"
                ].get_feature_names_out()

                imp_df = pd.DataFrame({
                    "Variable": feat_names,
                    "Importancia": importancias
                })

                imp_df = (
                    imp_df
                    .sort_values(
                        "Importancia",
                        ascending=False
                    )
                    .head(10)
                )

                fig_imp = dark_fig(
                    px.bar(
                        imp_df,
                        x="Variable",
                        y="Importancia",
                        text_auto=".2f",
                        color="Importancia",
                        color_continuous_scale="Blues",
                    )
                )

                fig_imp.update_layout(
                    height=350,
                    coloraxis_showscale=False
                )

                fig_imp.update_traces(
                    textfont=dict(color="black")
                )

                st.plotly_chart(
                    fig_imp,
                    use_container_width=True
                )

            except Exception as e:
                st.caption(
                    f"Importancia no disponible: {e}"
                )

    # ═══════════════════════════════════════════════════════
    # TAB 2 — HISTÓRICO
    # ═══════════════════════════════════════════════════════
    with tab_hist:
        st.subheader("📋 Histórico de predicciones almacenadas")

        if historico_df.empty:
            st.info("No hay predicciones almacenadas aún.")
        else:
            prods_hist = sorted(historico_df["producto"].unique().tolist())
            prod_sel   = st.multiselect("Filtrar por producto", prods_hist, default=prods_hist[:5])
            df_fil     = historico_df[historico_df["producto"].isin(prod_sel)] if prod_sel else historico_df

            st.dataframe(df_fil, use_container_width=True, hide_index=True)

            if "cantidad_predicha" in df_fil.columns and not df_fil.empty:
                fig_hist = dark_fig(px.histogram(
                    df_fil, x="cantidad_predicha", nbins=30,
                    color_discrete_sequence=["#4f8eff"],
                    title="Distribución de cantidad predicha",
                ))
                fig_hist.update_layout(height=320)
                st.plotly_chart(fig_hist, use_container_width=True)

                top_df = (
                    df_fil.groupby("producto")["cantidad_predicha"]
                    .mean().reset_index()
                    .rename(columns={"cantidad_predicha": "Demanda promedio"})
                    .sort_values("Demanda promedio", ascending=False)
                    .head(10)
                )
                fig_top = dark_fig(px.bar(
                    top_df, x="producto", y="Demanda promedio",
                    text_auto=".1f", title="Top 10 productos por demanda promedio",
                    color_discrete_sequence=["#a78bfa"],
                ))
                fig_top.update_layout(height=350)
                st.plotly_chart(fig_top, use_container_width=True)

    # ═══════════════════════════════════════════════════════
    # TAB 3 — FIDELIZACIÓN DE CLIENTES
    # ═══════════════════════════════════════════════════════
    with tab_fidelizacion:
        st.subheader("🏆 Fidelización de Clientes")
        st.markdown(
            "Segmentación basada en patrones de demanda del histórico de predicciones. "
            "Se identifican combinaciones producto–zona–promoción con alta recurrencia "
            "como proxy de comportamiento fiel del consumidor."
        )

        if historico_df.empty:
            st.info("No hay datos históricos disponibles para el análisis de fidelización.")
        else:
            df_fid = historico_df.copy()

            sec("📊 Segmentación de demanda por producto")

            demanda_prod = (
                df_fid.groupby("producto")["cantidad_predicha"]
                .agg(["mean", "sum", "count"])
                .reset_index()
                .rename(columns={"mean": "promedio", "sum": "total", "count": "registros"})
                .sort_values("promedio", ascending=False)
            )

            p66 = demanda_prod["promedio"].quantile(0.66)
            p33 = demanda_prod["promedio"].quantile(0.33)

            def clasificar(val):
                if val >= p66:
                    return "🟢 Alta demanda"
                elif val >= p33:
                    return "🟡 Demanda media"
                else:
                    return "🔴 Baja demanda"

            demanda_prod["Segmento"] = demanda_prod["promedio"].apply(clasificar)

            k1, k2, k3 = st.columns(3)
            alta  = (demanda_prod["Segmento"] == "🟢 Alta demanda").sum()
            media = (demanda_prod["Segmento"] == "🟡 Demanda media").sum()
            baja  = (demanda_prod["Segmento"] == "🔴 Baja demanda").sum()
            k1.markdown(f'<div class="seg-card"><div class="seg-label">Productos alta demanda</div><div class="seg-value" style="color:#34d399">{alta}</div><div class="seg-sub">Demanda promedio ≥ {p66:.1f} uds</div></div>', unsafe_allow_html=True)
            k2.markdown(f'<div class="seg-card"><div class="seg-label">Productos demanda media</div><div class="seg-value" style="color:#fbbf24">{media}</div><div class="seg-sub">Entre {p33:.1f} y {p66:.1f} uds</div></div>', unsafe_allow_html=True)
            k3.markdown(f'<div class="seg-card"><div class="seg-label">Productos baja demanda</div><div class="seg-value" style="color:#fb7185">{baja}</div><div class="seg-sub">Demanda promedio < {p33:.1f} uds</div></div>', unsafe_allow_html=True)

            fig_seg = dark_fig(px.bar(
                demanda_prod.head(15),
                x="producto", y="promedio",
                color="Segmento",
                color_discrete_map={
                    "🟢 Alta demanda":   "#34d399",
                    "🟡 Demanda media":  "#fbbf24",
                    "🔴 Baja demanda":   "#fb7185",
                },
                text_auto=".1f",
                title="Demanda promedio por producto (top 15)",
            ))
            fig_seg.update_layout(
                height=380,
                xaxis_tickangle=-35,

                legend=dict(
                    font=dict(
                        color="#ffffff",
                        size=13
                    ),
                    bgcolor="rgba(0,0,0,0)"
                )
            )

            st.plotly_chart(fig_seg, use_container_width=True)


            if "tipo_zona" in df_fid.columns:
                sec("🗺️ Mapa de preferencia: Producto × Zona")
                st.caption("Intensidad = cantidad predicha promedio. Identifica qué productos son más demandados por zona.")

                heatmap_df = (
                    df_fid.groupby(["producto", "tipo_zona"])["cantidad_predicha"]
                    .mean()
                    .reset_index()
                    .pivot(index="producto", columns="tipo_zona", values="cantidad_predicha")
                    .fillna(0)
                )

                fig_heat = go.Figure(data=go.Heatmap(
                    z=heatmap_df.values,
                    x=heatmap_df.columns.tolist(),
                    y=heatmap_df.index.tolist(),
                    colorscale="Blues",
                    text=np.round(heatmap_df.values, 1),
                    texttemplate="%{text}",
                    hoverongaps=False,
                ))
                fig_heat.update_layout(
                **PLOTLY_DARK,

                height=max(300, len(heatmap_df) * 28),

                title=dict(
                    text="Demanda promedio por producto y zona",
                    font=dict(
                        color="#ffffff",
                        size=20
                    )
                ),

                xaxis=dict(
                    title="Zona",
                    title_font=dict(color="#ffffff"),
                    tickfont=dict(color="#ffffff")
                ),

                yaxis=dict(
                    title="Producto",
                    title_font=dict(color="#ffffff"),
                    tickfont=dict(color="#ffffff")
                ),

                font=dict(
                    color="#ffffff"
                )
                 )
                fig_heat.update_traces(
                    textfont=dict(
                        color="#000000"
                    ),

                    colorbar=dict(
                        tickfont=dict(color="#ffffff"),
                        title=dict(
                            text="Demanda",
                            font=dict(color="#ffffff")
                        )
                    )
                )
                st.plotly_chart(fig_heat, use_container_width=True)

            if "tipo_promocion" in df_fid.columns and "tipo_zona" in df_fid.columns:
                sec("🔁 Combinaciones más recurrentes (proxy de fidelización)")
                st.caption(
                    "Las combinaciones producto–zona–promoción con mayor demanda acumulada "
                    "representan los patrones de compra más consistentes: indicadores de lealtad."
                )

                combos = (
                    df_fid.groupby(["producto", "tipo_zona", "tipo_promocion"])["cantidad_predicha"]
                    .agg(["sum", "mean", "count"])
                    .reset_index()
                    .rename(columns={"sum": "Demanda total", "mean": "Demanda promedio", "count": "Frecuencia"})
                    .sort_values("Demanda total", ascending=False)
                    .head(10)
                )
                combos["Índice de fidelidad"] = (
                    (combos["Demanda total"] / combos["Demanda total"].max() * 50) +
                    (combos["Frecuencia"]    / combos["Frecuencia"].max()    * 50)
                ).round(1)

                st.dataframe(combos, use_container_width=True, hide_index=True)

                fig_combo = dark_fig(px.bar(
                    combos, x="Demanda total",
                    y=combos["producto"] + " · " + combos["tipo_zona"],
                    orientation="h",
                    color="Índice de fidelidad",
                    color_continuous_scale="Blues",
                    text_auto=True,
                    title="Top 10 combinaciones por demanda acumulada",
                ))
                fig_combo.update_layout(
                    height=400,
                    yaxis_title="",
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig_combo, use_container_width=True)

            if "tipo_promocion" in df_fid.columns:
                sec("🏷️ Impacto de promociones en la demanda")
                promo_df = (
                    df_fid.groupby("tipo_promocion")["cantidad_predicha"]
                    .agg(["mean", "sum"])
                    .reset_index()
                    .rename(columns={"mean": "Demanda promedio", "sum": "Demanda total"})
                    .sort_values("Demanda promedio", ascending=False)
                )

                fig_promo = dark_fig(px.bar(
                    promo_df, x="tipo_promocion", y="Demanda promedio",
                    color="Demanda promedio",
                    color_continuous_scale="Purples",
                    text_auto=".1f",
                    title="Demanda promedio según tipo de promoción",
                ))
                fig_promo.update_layout(height=320, coloraxis_showscale=False, xaxis_title="Tipo de promoción")
                st.plotly_chart(fig_promo, use_container_width=True)

    # ═══════════════════════════════════════════════════════
    # TAB 4 — ANÁLISIS ECONÓMICO
    # ═══════════════════════════════════════════════════════
    with tab_economico:
        st.subheader("💰 Análisis Económico")
        st.markdown(
            "Estimación de ingresos potenciales basada en el histórico de predicciones "
            "y los precios promedio por producto. Incluye comparativa con/sin promoción "
            "y escenarios de optimización de ingresos."
        )

        if historico_df.empty or precios_df.empty:
            st.info("No hay datos suficientes para el análisis económico.")
        else:
            historico_norm = historico_df.copy()
            precios_norm   = precios_df.copy()
            historico_norm["producto"] = historico_norm["producto"].str.strip().str.lower()
            precios_norm["producto"]   = precios_norm["producto"].str.strip().str.lower()

            df_eco = historico_norm.merge(precios_norm, on="producto", how="left")

            precio_mediana = df_eco["precio_promedio"].median()
            df_eco["precio_promedio"] = df_eco["precio_promedio"].fillna(precio_mediana)

            df_eco["ingreso_estimado"] = df_eco["cantidad_predicha"] * df_eco["precio_promedio"]

            sec("💵 Indicadores económicos globales")

            ingreso_total  = df_eco["ingreso_estimado"].sum()
            ingreso_prom   = df_eco["ingreso_estimado"].mean()
            producto_mayor = df_eco.groupby("producto")["ingreso_estimado"].sum().idxmax()
            ingreso_mayor  = df_eco.groupby("producto")["ingreso_estimado"].sum().max()

            e1, e2, e3 = st.columns(3)
            e1.markdown(f'<div class="seg-card"><div class="seg-label">Ingreso total estimado</div><div class="seg-value" style="color:#4f8eff">S/ {ingreso_total:,.0f}</div><div class="seg-sub">Suma de todos los registros</div></div>', unsafe_allow_html=True)
            e2.markdown(f'<div class="seg-card"><div class="seg-label">Ingreso promedio por registro</div><div class="seg-value" style="color:#34d399">S/ {ingreso_prom:,.2f}</div><div class="seg-sub">Promedio histórico</div></div>', unsafe_allow_html=True)
            e3.markdown(f'<div class="seg-card"><div class="seg-label">Producto más rentable</div><div class="seg-value" style="color:#a78bfa;font-size:1.1rem;padding-top:0.2rem">{producto_mayor}</div><div class="seg-sub">S/ {ingreso_mayor:,.0f} acumulado</div></div>', unsafe_allow_html=True)

            sec("📦 Ingresos estimados por producto")

            ing_prod = (
                df_eco.groupby("producto")
                .agg(
                    demanda_total   = ("cantidad_predicha", "sum"),
                    precio_promedio = ("precio_promedio",   "mean"),
                    ingreso_total   = ("ingreso_estimado",  "sum"),
                )
                .reset_index()
                .sort_values("ingreso_total", ascending=False)
            )
            ing_prod["precio_promedio"] = ing_prod["precio_promedio"].round(2)
            ing_prod["ingreso_total"]   = ing_prod["ingreso_total"].round(2)

            fig_ing = dark_fig(px.bar(
                ing_prod.head(12),
                x="producto", y="ingreso_total",
                color="ingreso_total",
                color_continuous_scale="Blues",
                text_auto=".0f",
                title="Ingreso estimado total por producto (top 12)",
            ))
            fig_ing.update_layout(height=380, xaxis_tickangle=-35, coloraxis_showscale=False)
            st.plotly_chart(fig_ing, use_container_width=True)

            st.dataframe(
                ing_prod.rename(columns={
                    "producto":       "Producto",
                    "demanda_total":  "Demanda total (uds)",
                    "precio_promedio":"Precio promedio (S/)",
                    "ingreso_total":  "Ingreso estimado (S/)",
                }),
                use_container_width=True, hide_index=True,
            )

            if "tipo_promocion" in df_eco.columns:
                sec("🏷️ ROI de promociones — Ingreso promedio con vs sin promoción")
                st.caption(
                    "Se compara el ingreso estimado promedio entre registros con promoción activa "
                    "y sin promoción. Un ROI positivo indica que la promoción genera más ingreso por transacción."
                )

                sin_promo_keywords = ["ninguno", "none", "sin promoción", "sin promo"]
                df_eco["tiene_promo"] = ~df_eco["tipo_promocion"].str.lower().isin(sin_promo_keywords)

                roi_df = (
                    df_eco.groupby("tiene_promo")["ingreso_estimado"]
                    .mean()
                    .reset_index()
                )
                roi_df["Tipo"] = roi_df["tiene_promo"].map({True: "Con promoción", False: "Sin promoción"})
                roi_df = roi_df.rename(columns={"ingreso_estimado": "Ingreso promedio (S/)"})

                fig_roi = dark_fig(px.bar(
                    roi_df, x="Tipo", y="Ingreso promedio (S/)",
                    color="Tipo",
                    color_discrete_map={"Con promoción": "#34d399", "Sin promoción": "#6b7280"},
                    text_auto=".2f",
                    title="Ingreso promedio: con vs sin promoción",
                ))
                fig_roi.update_layout(height=320, showlegend=False)
                st.plotly_chart(fig_roi, use_container_width=True)

                promo_eco = (
                    df_eco.groupby("tipo_promocion")
                    .agg(
                        ingreso_prom = ("ingreso_estimado", "mean"),
                        ingreso_sum  = ("ingreso_estimado", "sum"),
                        registros    = ("ingreso_estimado", "count"),
                    )
                    .reset_index()
                    .sort_values("ingreso_prom", ascending=False)
                    .rename(columns={
                        "tipo_promocion": "Tipo de promoción",
                        "ingreso_prom":   "Ingreso promedio (S/)",
                        "ingreso_sum":    "Ingreso total (S/)",
                        "registros":      "Registros",
                    })
                )
                promo_eco["Ingreso promedio (S/)"] = promo_eco["Ingreso promedio (S/)"].round(2)
                promo_eco["Ingreso total (S/)"]    = promo_eco["Ingreso total (S/)"].round(2)
                st.dataframe(promo_eco, use_container_width=True, hide_index=True)

            if "tipo_zona" in df_eco.columns:
                sec("🏪 Ingresos estimados por zona")

                zona_eco = (
                    df_eco.groupby("tipo_zona")["ingreso_estimado"]
                    .agg(["sum", "mean"])
                    .reset_index()
                    .rename(columns={
                        "tipo_zona": "Zona",
                        "sum":       "Ingreso total (S/)",
                        "mean":      "Ingreso promedio (S/)",
                    })
                    .sort_values("Ingreso total (S/)", ascending=False)
                )

                fig_zona = dark_fig(px.pie(
                    zona_eco,
                    names="Zona",
                    values="Ingreso total (S/)",
                    color_discrete_sequence=COLOR_SEQ,
                    title="Distribución de ingresos por zona",
                    hole=0.45,
                ))
                fig_zona.update_layout(
                    height=360,
                    title_font_color="#ffffff",        # ← título "Distribución de ingresos por zona"
                    legend=dict(
                        font=dict(color="#ffffff", size=14)  # ← leyenda (Comercial, Mixta, Residencial)
                    )
                )

                fig_zona.update_traces(
                    textfont=dict(color="#ffffff"),    # ← porcentajes/etiquetas dentro del gráfico
                )
                # ← AGREGA ESTO para cambiar el color de las letras
                fig_zona.update_layout(
                    height=360,
                    legend=dict(
                        font=dict(
                            color="#ffffff",   # ← cambia aquí el color que quieras
                            size=14,
                        )
                    )
                )
                
                fig_zona.update_layout(height=360)
                st.plotly_chart(fig_zona, use_container_width=True)

            sec("🎯 Producto de mayor potencial económico")
            mejor_prod = ing_prod.iloc[0]
            st.success(
                f"**Producto más rentable:** {mejor_prod['producto']}\n\n"
                f"**Demanda total estimada:** {int(mejor_prod['demanda_total']):,} unidades\n\n"
                f"**Precio promedio:** S/ {mejor_prod['precio_promedio']}\n\n"
                f"**Ingreso total estimado:** S/ {mejor_prod['ingreso_total']:,.2f}"
            )