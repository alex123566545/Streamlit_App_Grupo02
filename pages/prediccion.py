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
# CONFIGURACIÓN DE PÁGINA
# =========================================================
st.set_page_config(
    page_title="Sistema Predictivo Comercial",
    page_icon="📊",
    layout="wide"
)


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

    .badge-high {
        background: rgba(52,211,153,0.15);
        color: #34d399;
        border: 1px solid rgba(52,211,153,0.3);
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
    }

    .badge-med {
        background: rgba(251,191,36,0.15);
        color: #fbbf24;
        border: 1px solid rgba(251,191,36,0.3);
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
    }

    .badge-low {
        background: rgba(251,113,133,0.15);
        color: #fb7185;
        border: 1px solid rgba(251,113,133,0.3);
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
    }

    .seg-card {
        background: #1c1f2b;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 0.75rem;
        transition: all 0.2s ease;
    }

    .seg-card:hover {
        border-color: rgba(79,142,255,0.25);
        transform: translateY(-1px);
    }

    .seg-label {
        font-size: 0.72rem;
        color: #ffffff;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        font-weight: 600;
        margin-bottom: 0.3rem;
    }

    .seg-value {
        font-family: 'Syne', sans-serif;
        font-size: 1.5rem;
        font-weight: 800;
        color: #ffffff;
        line-height: 1;
    }

    .seg-sub {
        font-size: 0.8rem;
        color: #ffffff;
        margin-top: 0.25rem;
    }

    div[data-baseweb="select"] > div {
        background: #1c1f2b !important;
        border-color: rgba(255,255,255,0.12) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
    }

    div[data-baseweb="select"] > div > div {
        color: #ffffff !important;
    }

    div[data-baseweb="popover"] ul {
        background: #1c1f2b !important;
        border: 1px solid rgba(255,255,255,0.10) !important;
    }

    div[data-baseweb="popover"] li {
        background: #1c1f2b !important;
        color: #ffffff !important;
    }

    div[data-baseweb="popover"] li:hover {
        background: #20243a !important;
        color: #ffffff !important;
    }

    div[data-baseweb="tag"] {
        background: rgba(79,142,255,0.2) !important;
        color: #ffffff !important;
    }

    div[data-baseweb="tag"] span {
        color: #ffffff !important;
    }

    .sec-header {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin: 1.75rem 0 0.75rem;
    }

    .sec-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #4f8eff;
        flex-shrink: 0;
    }

    .sec-title {
        font-family: 'Syne', sans-serif;
        font-size: 1rem;
        font-weight: 700;
        color: #ffffff;
    }
</style>
"""


# =========================================================
# HELPERS
# =========================================================
def _lower(s: str) -> str:
    return str(s).strip().lower()


def sec(title: str):
    st.markdown(
        f'''
        <div class="sec-header">
            <div class="sec-dot"></div>
            <div class="sec-title">{title}</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


PLOTLY_DARK = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_family="DM Sans",
    font_color="#ffffff",
    margin=dict(t=40, b=30, l=10, r=10),
)

COLOR_SEQ = [
    "#4f8eff",
    "#a78bfa",
    "#34d399",
    "#f97316",
    "#fb7185",
    "#fbbf24"
]


def dark_fig(fig):
    fig.update_layout(**PLOTLY_DARK)

    fig.update_xaxes(
        gridcolor="rgba(255,255,255,0.05)",
        linecolor="rgba(255,255,255,0.05)"
    )

    fig.update_yaxes(
        gridcolor="rgba(255,255,255,0.05)",
        linecolor="rgba(255,255,255,0.05)"
    )

    return fig


# =========================================================
# CARGA DE MODELO
# =========================================================
def _load_pkl(url: str):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return pickle.loads(response.content)


@st.cache_resource(show_spinner="Cargando modelo...")
def load_assets():

    MODEL_URL = "https://klbmaoqxfvjsczwrrwkj.supabase.co/storage/v1/object/public/models/model.pkl"

    FEATURES_URL = "https://klbmaoqxfvjsczwrrwkj.supabase.co/storage/v1/object/public/models/features.pkl"

    model = _load_pkl(MODEL_URL)
    features = _load_pkl(FEATURES_URL)

    return model, features


# =========================================================
# CARGA DE DIMENSIONES
# =========================================================
@st.cache_data(show_spinner="Cargando dimensiones...", ttl=3600)
def load_dimensions():

    conn = get_connection()

    try:

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

        precios = pd.read_sql("""
            SELECT
                producto,
                ROUND(AVG(precio_unitario),2) AS precio_promedio
            FROM gold_ml.ventas_dataset
            GROUP BY producto
        """, conn)

    finally:
        conn.close()

    return productos, promociones, tiendas, climas, precios


@st.cache_data(show_spinner=False, ttl=3600)
def load_history():

    conn = get_connection()

    try:

        df = pd.read_sql("""
            SELECT *
            FROM gold_ml.ventas_predicha
        """, conn)

    finally:
        conn.close()

    return df


# =========================================================
# FEATURE ENGINEERING
# =========================================================
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

    trimestre = (
        1 if fecha.month <= 3 else
        2 if fecha.month <= 6 else
        3 if fecha.month <= 9 else 4
    )

    return pd.DataFrame([{
        "mes": fecha.month,
        "dia_mes": fecha.day,
        "hora": hora,
        "precio_unitario": float(precio),
        "trimestre": trimestre,
        "es_fin_semana": int(fecha.weekday() >= 5),
        "hora_pico": int(12 <= hora <= 14 or 18 <= hora <= 21),

        "producto": _lower(producto),
        "categoria_producto": _lower(categoria_producto),
        "tipo_promocion": _lower(tipo_promocion),
        "tipo_zona": _lower(tipo_zona),
        "ubicacion_tienda": _lower(ubicacion_tienda),
        "clima": _lower(clima),

        "producto_promocion":
            f"{_lower(producto)}_{_lower(tipo_promocion)}",

        "temporada":
            ["Q1", "Q2", "Q3", "Q4"][trimestre - 1],
    }])


# =========================================================
# ELASTICIDAD PRECIO
# =========================================================
def aplicar_elasticidad(
    pred_raw,
    precio,
    precio_promedio,
    elasticidad=-1.2
):

    if precio_promedio <= 0:
        return pred_raw

    factor = (precio / precio_promedio) ** elasticidad

    return max(1.0, pred_raw * factor)


# =========================================================
# PREDICCIÓN MULTI DÍA
# =========================================================
def predecir_rango(
    model,
    features,
    fecha_inicio,
    n_dias,
    hora,
    producto,
    categoria_producto,
    precio,
    tipo_promocion,
    tipo_zona,
    ubicacion_tienda,
    clima,
    precio_promedio,
):

    total = 0.0
    detalle = []

    for i in range(n_dias):

        f = fecha_inicio + timedelta(days=i)

        data = build_features(
            f,
            hora,
            producto,
            categoria_producto,
            precio,
            tipo_promocion,
            tipo_zona,
            ubicacion_tienda,
            clima
        )[features]

        pred_raw = model.predict(data)[0]

        pred_adj = aplicar_elasticidad(
            pred_raw,
            precio,
            precio_promedio
        )

        pred_dia = max(1, round(pred_adj))

        total += pred_dia

        detalle.append({
            "fecha": f,
            "dia_semana":
                ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"][f.weekday()],
            "es_finde": f.weekday() >= 5,
            "unidades": pred_dia,
            "ingreso": round(pred_dia * precio, 2),
        })

    return max(1, round(total)), detalle


# =========================================================
# NIVEL DE DEMANDA
# =========================================================
def demanda_badge(pred_dia):

    if pred_dia < 15:
        return "🔴 Demanda Baja", "low"

    elif pred_dia < 35:
        return "🟡 Demanda Media", "med"

    else:
        return "🟢 Demanda Alta", "high"


# =========================================================
# INTERFAZ PRINCIPAL
# =========================================================
def show_prediccion():

    st.markdown(PREDICCION_CSS, unsafe_allow_html=True)

    st.markdown(
        '''
        <p class="main-header">
            🏪 Sistema de Inteligencia Comercial Predictiva
        </p>

        <p class="sub-header">
            Predicción de demanda · Fidelización ·
            Análisis Económico · Modelo Random Forest
        </p>
        ''',
        unsafe_allow_html=True,
    )

    with st.spinner("Inicializando recursos..."):

        model, features = load_assets()

        (
            productos_df,
            promociones_df,
            tiendas_df,
            climas_df,
            precios_df
        ) = load_dimensions()

        historico_df = load_history()

    tab_pred, tab_hist, tab_fidelizacion, tab_economico = st.tabs([
        "📊 Predicción",
        "📋 Histórico",
        "🏆 Fidelización",
        "💰 Económico"
    ])

    # =====================================================
    # TAB PREDICCIÓN
    # =====================================================
    with tab_pred:

        st.subheader("⚙️ Configuración de predicción")

        col1, col2 = st.columns([1, 2])

        with col1:

            fecha = st.date_input(
                "📅 Fecha",
                value=date.today()
            )

            hora = 12

            producto = st.selectbox(
                "🛒 Producto",
                productos_df["producto"].unique()
            )

            categoria_producto = productos_df.loc[
                productos_df["producto"] == producto,
                "categoria_producto"
            ].values[0]

            st.caption(f"Categoría: {categoria_producto}")

            precio_promedio = float(
                precios_df.loc[
                    precios_df["producto"] == producto,
                    "precio_promedio"
                ].values[0]
            )

            st.caption(
                f"💰 Precio promedio histórico: S/ {precio_promedio}"
            )

            precio = st.slider(
                "💲 Precio",
                min_value=1.0,
                max_value=30.0,
                value=precio_promedio,
                step=0.10
            )

            tipo_promocion = st.selectbox(
                "🏷️ Promoción",
                promociones_df["tipo_promocion"].unique()
            )

            ubicacion_tienda = st.selectbox(
                "📍 Tienda",
                tiendas_df["ubicacion_tienda"].unique()
            )

            tipo_zona = tiendas_df.loc[
                tiendas_df["ubicacion_tienda"] == ubicacion_tienda,
                "tipo_zona"
            ].values[0]

            st.caption(f"Zona: {tipo_zona}")

            clima = st.selectbox(
                "🌤️ Clima",
                climas_df["clima"].unique()
            )

        with col2:

            predecir = st.button(
                "🔮 Generar Predicción",
                use_container_width=True
            )

            if predecir:

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
                )[features]

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
                    precio_promedio
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
                    precio_promedio
                )

                ingreso_dia = round(pred_dia * precio, 2)
                ingreso_sem = round(pred_sem * precio, 2)
                ingreso_mes = round(pred_mes * precio, 2)

                sec("📊 Resultados")

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "Predicción diaria",
                    f"{pred_dia} uds"
                )

                c2.metric(
                    "Predicción semanal",
                    f"{pred_sem} uds"
                )

                c3.metric(
                    "Predicción mensual",
                    f"{pred_mes} uds"
                )

                c1.metric(
                    "Ingreso diario",
                    f"S/ {ingreso_dia}"
                )

                c2.metric(
                    "Ingreso semanal",
                    f"S/ {ingreso_sem}"
                )

                c3.metric(
                    "Ingreso mensual",
                    f"S/ {ingreso_mes}"
                )

                label, nivel = demanda_badge(pred_dia)

                st.markdown(
                    f'''
                    **Nivel de demanda:**
                    <span class="badge-{nivel}">
                        {label}
                    </span>
                    ''',
                    unsafe_allow_html=True,
                )

                sec("📈 Proyección temporal")

                proy_df = pd.DataFrame({
                    "Periodo": ["Día", "Semana", "Mes"],
                    "Cantidad": [
                        pred_dia,
                        pred_sem,
                        pred_mes
                    ],
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
                        ]
                    )
                )

                fig_proy.update_layout(
                    showlegend=False,
                    height=300
                )

                st.plotly_chart(
                    fig_proy,
                    use_container_width=True
                )

                sec("🗓️ Próximos 7 días")

                det_df = pd.DataFrame(detalle_sem)

                det_df["fecha"] = det_df["fecha"].astype(str)

                det_df.columns = [
                    "Fecha",
                    "Día",
                    "¿Finde?",
                    "Unidades",
                    "Ingreso"
                ]

                det_df["¿Finde?"] = det_df["¿Finde?"].map({
                    True: "✅",
                    False: "—"
                })

                st.dataframe(
                    det_df,
                    use_container_width=True,
                    hide_index=True
                )

                fig_det = dark_fig(
                    px.bar(
                        det_df,
                        x="Fecha",
                        y="Unidades",
                        color="¿Finde?",
                        text_auto=True,
                        color_discrete_map={
                            "✅": "#a78bfa",
                            "—": "#4f8eff"
                        }
                    )
                )

                fig_det.update_layout(
                    height=320,
                    showlegend=False
                )

                st.plotly_chart(
                    fig_det,
                    use_container_width=True
                )

                sec("💹 Simulación de precios")

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
                    )[features]

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
                        "Escenario": f"x{factor:.1f}",
                        "Precio": p_sim,
                        "Demanda": pred_sim,
                        "Ingreso": round(pred_sim * p_sim, 2),
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
                        x="Precio",
                        y="Ingreso",
                        markers=True,
                        color_discrete_sequence=["#4f8eff"]
                    )
                )

                fig_sim.update_layout(height=300)

                st.plotly_chart(
                    fig_sim,
                    use_container_width=True
                )

                mejor = sim_df.loc[
                    sim_df["Ingreso"].idxmax()
                ]

                sec("💡 Recomendación")

                st.success(
                    f"""
                    Precio óptimo sugerido: S/ {mejor['Precio']}

                    Demanda esperada: {mejor['Demanda']} unidades

                    Ingreso esperado: S/ {mejor['Ingreso']}
                    """
                )


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    show_prediccion()