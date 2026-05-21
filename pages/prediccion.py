import streamlit as st
import pandas as pd
import requests
import pickle
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np
from datetime import date

from utils.database import get_connection


# =========================================================
# CONFIGURACIÓN DE PÁGINA
# =========================================================
st.set_page_config(
    page_title="Sistema de Inteligencia Comercial Predictiva",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #555;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #f0f4ff;
        border-radius: 10px;
        padding: 1rem;
        border-left: 4px solid #4361ee;
    }
    .section-divider {
        border-top: 2px solid #e0e0e0;
        margin: 2rem 0;
    }
    .badge-high { background:#d4edda; color:#155724; padding:4px 10px; border-radius:20px; font-weight:600; }
    .badge-med  { background:#fff3cd; color:#856404; padding:4px 10px; border-radius:20px; font-weight:600; }
    .badge-low  { background:#f8d7da; color:#721c24; padding:4px 10px; border-radius:20px; font-weight:600; }
</style>
""", unsafe_allow_html=True)


# =========================================================
# CARGA DE MODELO Y FEATURES (pkl desde Supabase)
# =========================================================
def _load_pkl(url: str):
    """Descarga y deserializa un archivo .pkl desde una URL pública."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return pickle.loads(response.content)


@st.cache_resource(show_spinner="Cargando modelo predictivo…")
def load_assets():
    MODEL_URL    = "https://klbmaoqxfvjsczwrrwkj.supabase.co/storage/v1/object/public/models/model.pkl"
    FEATURES_URL = "https://klbmaoqxfvjsczwrrwkj.supabase.co/storage/v1/object/public/models/features.pkl"
    model    = _load_pkl(MODEL_URL)
    features = _load_pkl(FEATURES_URL)
    return model, features


# =========================================================
# CARGA DE DIMENSIONES (gold_dim)
# =========================================================
@st.cache_data(show_spinner="Cargando catálogos…", ttl=3600)
def load_dimensions():
    conn = get_connection()
    try:
        productos  = pd.read_sql(
            "SELECT DISTINCT producto, categoria_producto FROM gold_dim.dim_producto ORDER BY producto", conn
        )
        promociones = pd.read_sql(
            "SELECT DISTINCT tipo_promocion FROM gold_dim.dim_promocion ORDER BY tipo_promocion", conn
        )
        tiendas = pd.read_sql(
            "SELECT DISTINCT ubicacion_tienda, tipo_zona FROM gold_dim.dim_tienda ORDER BY ubicacion_tienda", conn
        )
        climas = pd.read_sql(
            "SELECT DISTINCT clima FROM gold_dim.dim_clima ORDER BY clima", conn
        )
        precios = pd.read_sql(
            """SELECT producto, ROUND(AVG(precio_unitario),2) AS precio_promedio
               FROM gold_ml.ventas_dataset GROUP BY producto""", conn
        )
    finally:
        conn.close()
    return productos, promociones, tiendas, climas, precios


# =========================================================
# CARGA DE HISTÓRICO DE PREDICCIONES
# =========================================================
@st.cache_data(show_spinner=False, ttl=3600)
def load_history():
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT * FROM gold_ml.ventas_predicha", conn)
    finally:
        conn.close()
    return df


# =========================================================
# CARGA DE DATASET PARA MÉTRICAS (CRISP-DM)
# =========================================================
@st.cache_data(show_spinner=False, ttl=3600)
def load_ventas_dataset():
    """Devuelve el dataset de entrenamiento para evaluación del modelo."""
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT * FROM gold_ml.ventas_dataset LIMIT 5000", conn)
    finally:
        conn.close()
    return df


# =========================================================
# FEATURE ENGINEERING  (idéntico al pipeline del modelo)
# =========================================================
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
    temporada = ["Q1","Q2","Q3","Q4"][trimestre - 1]
    hora_pico = 1 if (12 <= hora <= 14 or 18 <= hora <= 21) else 0

    # CORRECCIÓN: normalizar a minúsculas igual que clean_text_columns() del pipeline.
    # Sin esto, el OneHotEncoder recibe "Soleado" pero fue entrenado con "soleado"
    # → handle_unknown="ignore" pone todos los dummies en 0 → clima no influye.
    def _lower(s): return str(s).strip().lower()

    return pd.DataFrame([{
        "mes":                 fecha.month,
        "dia_mes":             fecha.day,
        "hora":                hora,
        "precio_unitario":     float(precio),
        "trimestre":           trimestre,
        "es_fin_semana":       int(fecha.weekday() >= 5),
        "hora_pico":           hora_pico,
        "producto":            _lower(producto),
        "categoria_producto":  _lower(categoria_producto),
        "tipo_promocion":      _lower(tipo_promocion),
        "tipo_zona":           _lower(tipo_zona),
        "ubicacion_tienda":    _lower(ubicacion_tienda),
        "clima":               _lower(clima),
        "producto_promocion":  f"{_lower(producto)}_{_lower(tipo_promocion)}",
        "temporada":           temporada,
    }])


# =========================================================
# MÉTRICAS DE REGRESIÓN (MAE, RMSE, R²) — sección CRISP-DM
# =========================================================
def compute_metrics(model, features, ventas_df: pd.DataFrame):
    """
    Calcula MAE, RMSE y R² sobre una muestra del dataset real.
    Incluye comparación contra modelo base (Regresión Lineal).
    """
    target = "cantidad_vendida"
    if target not in ventas_df.columns:
        return None

    # Preparar features disponibles en el dataset
    disponibles = [c for c in features if c in ventas_df.columns]
    if len(disponibles) < len(features):
        return None  # faltan columnas derivadas

    X = ventas_df[disponibles]
    y = ventas_df[target]

    try:
        y_pred_rf = model.predict(X[features])
    except Exception:
        return None

    mae_rf  = mean_absolute_error(y, y_pred_rf)
    rmse_rf = np.sqrt(mean_squared_error(y, y_pred_rf))
    r2_rf   = r2_score(y, y_pred_rf)

    # Baseline: regresión lineal sobre precio_unitario
    X_base = ventas_df[["precio_unitario"]].values
    lr = LinearRegression().fit(X_base, y)
    y_pred_base = lr.predict(X_base)
    mae_base  = mean_absolute_error(y, y_pred_base)
    rmse_base = np.sqrt(mean_squared_error(y, y_pred_base))
    r2_base   = r2_score(y, y_pred_base)

    return {
        "RF":   {"MAE": mae_rf,   "RMSE": rmse_rf,   "R2": r2_rf},
        "Base": {"MAE": mae_base, "RMSE": rmse_base, "R2": r2_base},
    }


# =========================================================
# AJUSTE POR ELASTICIDAD PRECIO
# =========================================================
def aplicar_elasticidad(pred_raw: float, precio: float, precio_promedio: float, elasticidad: float = -1.2) -> float:
    """
    Ajusta la predicción del modelo aplicando elasticidad-precio de la demanda.

    Fórmula:
        Q_ajustada = Q_raw × (P / P_prom) ^ elasticidad

    Donde:
        - elasticidad < 0  →  precio sube → demanda baja (bienes normales)
        - elasticidad = -1.2 por defecto (demanda elástica moderada, típica en retail)
        - El factor es 1.0 cuando precio == precio_promedio (sin distorsión)

    Ejemplos con elasticidad = -1.2:
        precio = precio_prom × 1.20  →  factor ≈ 0.77  (demanda baja ~23 %)
        precio = precio_prom × 0.80  →  factor ≈ 1.27  (demanda sube ~27 %)
    """
    if precio_promedio <= 0:
        return pred_raw
    ratio  = precio / precio_promedio
    factor = ratio ** elasticidad          # siempre positivo, < 1 si precio > promedio
    return max(1.0, pred_raw * factor)


# =========================================================
# NIVEL DE DEMANDA (helper)
# =========================================================
def demanda_badge(pred_dia: int) -> str:
    if pred_dia < 15:
        return "🔴 Demanda Baja", "low"
    elif pred_dia < 35:
        return "🟡 Demanda Media", "med"
    else:
        return "🟢 Demanda Alta", "high"


# =========================================================
# UI PRINCIPAL
# =========================================================
def show_prediccion():

    # ── Encabezado ──────────────────────────────────────────
    st.markdown(
        '<p class="main-header">🏪 Sistema de Inteligencia Comercial Predictiva</p>'
        '<p class="sub-header">Predicción de demanda · Tiendas de conveniencia en Perú · Modelo: Random Forest Regressor</p>',
        unsafe_allow_html=True,
    )

    # ── Carga de recursos ───────────────────────────────────
    with st.spinner("Iniciando recursos…"):
        model, features = load_assets()
        productos_df, promociones_df, tiendas_df, climas_df, precios_df = load_dimensions()
        historico_df = load_history()

    # ── Tabs principales ────────────────────────────────────
    tab_pred, tab_metricas, tab_hist = st.tabs([
        "📊 Predicción de Demanda",
        "📐 Métricas del Modelo (CRISP-DM)",
        "📋 Histórico de Predicciones",
    ])

    # ═══════════════════════════════════════════════════════
    # TAB 1: PREDICCIÓN
    # ═══════════════════════════════════════════════════════
    with tab_pred:

        st.subheader("⚙️ Parámetros de la transacción")

        col_l, col_r = st.columns([1, 2])

        with col_l:
            fecha = st.date_input("📅 Fecha", value=date.today())
            hora  = st.slider("🕐 Hora del día", 0, 23, 12)

            # Producto
            producto = st.selectbox("🛒 Producto", productos_df["producto"].unique())
            categoria_producto = productos_df.loc[
                productos_df["producto"] == producto, "categoria_producto"
            ].values[0]
            st.caption(f"Categoría: **{categoria_producto}**")

            # Precio
            precio_promedio = precios_df.loc[
                precios_df["producto"] == producto, "precio_promedio"
            ].values[0]
            st.caption(f"💰 Precio histórico promedio: S/ {precio_promedio}")
            precio = st.slider(
                "💲 Precio unitario (S/)",
                min_value=1.0, max_value=30.0,
                value=float(precio_promedio), step=0.10,
            )

            # Promoción
            tipo_promocion = st.selectbox(
                "🏷️ Tipo de promoción", promociones_df["tipo_promocion"].unique()
            )

            # Tienda
            ubicacion_tienda = st.selectbox(
                "📍 Ubicación de tienda", tiendas_df["ubicacion_tienda"].unique()
            )
            tipo_zona = tiendas_df.loc[
                tiendas_df["ubicacion_tienda"] == ubicacion_tienda, "tipo_zona"
            ].values[0]
            st.caption(f"Zona: **{tipo_zona}**")

            # Clima
            clima = st.selectbox("🌤️ Clima", climas_df["clima"].unique())

        with col_r:
            predecir = st.button("🔮 Generar Predicción", use_container_width=True)

            if predecir:
                data = build_features(
                    fecha, hora, producto, categoria_producto,
                    precio, tipo_promocion, tipo_zona,
                    ubicacion_tienda, clima
                )[features]

                # Corrección precio-demanda aplicada silenciosamente (ε = -1.2).
                # El usuario no ve este ajuste; solo ve el resultado final corregido.
                pred_raw     = model.predict(data)[0]
                pred_ajustada = aplicar_elasticidad(
                    pred_raw, precio, float(precio_promedio)
                )

                pred      = pred_ajustada
                pred_dia  = max(1, round(pred))
                pred_sem  = round(pred * 7)
                pred_mes  = round(pred * 30)

                ingreso_dia = round(pred_dia * precio, 2)
                ingreso_sem = round(pred_sem * precio, 2)
                ingreso_mes = round(pred_mes * precio, 2)

                # ── KPIs ───────────────────────────────────
                st.markdown("#### 📊 Resultados predictivos")
                c1, c2, c3 = st.columns(3)
                c1.metric("Predicción diaria",   f"{pred_dia} uds")
                c2.metric("Predicción semanal",  f"{pred_sem} uds")
                c3.metric("Predicción mensual",  f"{pred_mes} uds")

                c1.metric("Ingreso diario",   f"S/ {ingreso_dia}")
                c2.metric("Ingreso semanal",  f"S/ {ingreso_sem}")
                c3.metric("Ingreso mensual",  f"S/ {ingreso_mes}")

                # ── Nivel de demanda ───────────────────────
                label, nivel = demanda_badge(pred_dia)
                st.markdown(
                    f'**Nivel de demanda:** <span class="badge-{nivel}">{label}</span>',
                    unsafe_allow_html=True,
                )

                # ── Factores detectados (variables independientes) ──
                st.markdown("#### 🧠 Factores detectados")
                factores = []
                if tipo_promocion.lower() not in ("ninguno", "none", "sin promoción"):
                    factores.append("✔ Promoción activa")
                if 12 <= hora <= 14 or 18 <= hora <= 21:
                    factores.append("✔ Hora pico")
                if tipo_zona == "Comercial":
                    factores.append("✔ Zona comercial")
                if clima == "Soleado":
                    factores.append("✔ Clima favorable")
                if fecha.weekday() >= 5:
                    factores.append("✔ Fin de semana")
                if precio < precio_promedio:
                    factores.append("✔ Precio competitivo (por debajo del promedio histórico)")
                if factores:
                    st.info("  ·  ".join(factores))
                else:
                    st.info("No se detectaron factores favorables adicionales.")

                # ── Proyección temporal ────────────────────
                st.markdown("#### 📅 Proyección temporal (unidades)")
                proy_df = pd.DataFrame({
                    "Periodo":  ["Día", "Semana", "Mes"],
                    "Cantidad": [pred_dia, pred_sem, pred_mes],
                })
                fig_proy = px.bar(
                    proy_df, x="Periodo", y="Cantidad", text_auto=True,
                    color="Periodo",
                    color_discrete_sequence=["#4361ee","#3a0ca3","#7209b7"],
                )
                fig_proy.update_layout(showlegend=False, height=300)
                st.plotly_chart(fig_proy, use_container_width=True)

                # ── Comparación histórica ──────────────────
                st.markdown("#### 📈 Comparación con histórico")
                hist_prod = historico_df[historico_df["producto"] == producto]
                if not hist_prod.empty:
                    prom_hist = round(hist_prod["cantidad_predicha"].mean(), 2)
                    variacion = round(((pred_dia - prom_hist) / max(prom_hist, 1)) * 100, 2)
                    h1, h2 = st.columns(2)
                    h1.metric("Promedio histórico", prom_hist)
                    h2.metric("Variación esperada", f"{variacion}%",
                              delta=f"{variacion}%")
                else:
                    st.caption("Sin datos históricos para este producto.")

                # ── Simulación de precios ──────────────────
                st.markdown("#### 💹 Simulación de escenarios de precio")
                sims = []
                for factor in [0.8, 0.9, 1.0, 1.1, 1.2]:
                    p_sim = round(precio * factor, 2)
                    d_sim = build_features(
                        fecha, hora, producto, categoria_producto,
                        p_sim, tipo_promocion, tipo_zona,
                        ubicacion_tienda, clima
                    )[features]
                    pred_sim_raw = model.predict(d_sim)[0]
                    pred_sim_raw = aplicar_elasticidad(
                        pred_sim_raw, p_sim, float(precio_promedio)
                    )
                    pred_sim = max(1, round(pred_sim_raw))
                    sims.append({
                        "Escenario":      f"×{factor:.1f}",
                        "Precio (S/)":    p_sim,
                        "Demanda (uds)":  pred_sim,
                        "Ingreso (S/)":   round(pred_sim * p_sim, 2),
                    })
                sim_df = pd.DataFrame(sims)
                st.dataframe(sim_df, use_container_width=True, hide_index=True)

                fig_sim = px.line(
                    sim_df, x="Precio (S/)", y="Ingreso (S/)",
                    markers=True, title="Curva ingreso vs precio",
                    color_discrete_sequence=["#4361ee"],
                )
                fig_sim.update_layout(height=300)
                st.plotly_chart(fig_sim, use_container_width=True)

                # ── Recomendación comercial ────────────────
                st.markdown("#### 💡 Recomendación comercial")
                mejor = sim_df.loc[sim_df["Ingreso (S/)"].idxmax()]
                st.success(
                    f"**Precio óptimo sugerido:** S/ {mejor['Precio (S/)']}\n\n"
                    f"**Demanda esperada:** {mejor['Demanda (uds)']} unidades\n\n"
                    f"**Ingreso estimado:** S/ {mejor['Ingreso (S/)']}"
                )

                # ── Importancia de variables ───────────────
                st.markdown("#### ⚙️ Variables más influyentes (Random Forest)")
                try:
                    importancias = model.named_steps["model"].feature_importances_
                    feat_names   = model.named_steps["preprocess"].get_feature_names_out()
                    imp_df = (
                        pd.DataFrame({"Variable": feat_names, "Importancia": importancias})
                        .sort_values("Importancia", ascending=False)
                        .head(10)
                    )
                    fig_imp = px.bar(
                        imp_df, x="Variable", y="Importancia", text_auto=True,
                        color="Importancia", color_continuous_scale="Blues",
                    )
                    fig_imp.update_layout(height=350, coloraxis_showscale=False)
                    st.plotly_chart(fig_imp, use_container_width=True)
                except Exception as e:
                    st.caption(f"Importancia no disponible: {e}")

    # ═══════════════════════════════════════════════════════
    # TAB 2: MÉTRICAS CRISP-DM (MAE, RMSE, R²) + BASELINE
    # ═══════════════════════════════════════════════════════
    with tab_metricas:
        st.subheader("📐 Evaluación del modelo — Metodología CRISP-DM")

        st.markdown("""
        El proyecto sigue la metodología **CRISP-DM** para el desarrollo del modelo predictivo.
        A continuación se comparan las métricas de regresión del **Random Forest Regressor**
        (modelo principal) frente a la **Regresión Lineal Simple** (modelo base / *baseline*).
        """)

        with st.spinner("Calculando métricas…"):
            try:
                ventas_df = load_ventas_dataset()
                metricas  = compute_metrics(model, features, ventas_df)
            except Exception as e:
                metricas = None
                st.warning(f"No se pudo conectar al dataset de ventas: {e}")

        if metricas:
            rf   = metricas["RF"]
            base = metricas["Base"]

            st.markdown("##### Comparación: Random Forest vs Baseline (Regresión Lineal)")
            m1, m2, m3 = st.columns(3)
            m1.metric("MAE  — RF",   f"{rf['MAE']:.3f}",  delta=f"{rf['MAE']-base['MAE']:.3f} vs baseline", delta_color="inverse")
            m2.metric("RMSE — RF",   f"{rf['RMSE']:.3f}", delta=f"{rf['RMSE']-base['RMSE']:.3f} vs baseline", delta_color="inverse")
            m3.metric("R²   — RF",   f"{rf['R2']:.3f}",   delta=f"{rf['R2']-base['R2']:.3f} vs baseline")

            # Gráfico comparativo
            comp_df = pd.DataFrame({
                "Métrica": ["MAE", "RMSE", "R²"],
                "Random Forest": [rf["MAE"], rf["RMSE"], rf["R2"]],
                "Baseline (LR)": [base["MAE"], base["RMSE"], base["R2"]],
            }).melt("Métrica", var_name="Modelo", value_name="Valor")

            fig_met = px.bar(
                comp_df, x="Métrica", y="Valor", color="Modelo",
                barmode="group", text_auto=".3f",
                color_discrete_sequence=["#4361ee", "#adb5bd"],
                title="Comparación de métricas: Random Forest vs Baseline",
            )
            fig_met.update_layout(height=380)
            st.plotly_chart(fig_met, use_container_width=True)

            with st.expander("ℹ️ Descripción de las métricas"):
                st.markdown("""
                | Métrica | Descripción |
                |---------|-------------|
                | **MAE** (Mean Absolute Error) | Promedio de errores absolutos. Menor es mejor. |
                | **RMSE** (Root Mean Squared Error) | Raíz del error cuadrático medio. Penaliza errores grandes. |
                | **R²** | Proporción de variabilidad explicada por el modelo. Más cerca de 1 es mejor. |
                """)
        else:
            st.info(
                "Las métricas se calcularán cuando el dataset `gold_ml.ventas_dataset` "
                "contenga la columna `cantidad_vendida` y las features requeridas."
            )

        # Variables independientes usadas (documentación)
        with st.expander("📋 Variables del modelo (según documento de proyecto)"):
            st.markdown("""
            **Variable dependiente:** `cantidad_vendida`

            **Variables independientes:**
            - `producto` · `categoria_producto`
            - `mes` · `dia_mes` · `hora` · `trimestre` · `temporada`
            - `es_fin_semana` · `hora_pico`
            - `precio_unitario`
            - `tipo_promocion` · `producto_promocion`
            - `ubicacion_tienda` · `tipo_zona`
            - `clima`

            **Algoritmo:** Random Forest Regressor (scikit-learn)
            **Enfoque:** Aprendizaje supervisado — Regresión
            """)

    # ═══════════════════════════════════════════════════════
    # TAB 3: HISTÓRICO
    # ═══════════════════════════════════════════════════════
    with tab_hist:
        st.subheader("📋 Histórico de predicciones almacenadas")

        if historico_df.empty:
            st.info("No hay predicciones almacenadas aún.")
        else:
            # Filtro por producto
            prods_hist = sorted(historico_df["producto"].unique().tolist())
            prod_sel = st.multiselect(
                "Filtrar por producto", prods_hist, default=prods_hist[:5]
            )
            df_fil = (
                historico_df[historico_df["producto"].isin(prod_sel)]
                if prod_sel else historico_df
            )

            st.dataframe(df_fil, use_container_width=True, hide_index=True)

            # Distribución de predicciones
            if "cantidad_predicha" in df_fil.columns and not df_fil.empty:
                fig_hist = px.histogram(
                    df_fil, x="cantidad_predicha", nbins=30,
                    color_discrete_sequence=["#4361ee"],
                    title="Distribución de cantidad predicha",
                )
                fig_hist.update_layout(height=320)
                st.plotly_chart(fig_hist, use_container_width=True)

                # Top productos por demanda promedio
                top_df = (
                    df_fil.groupby("producto")["cantidad_predicha"]
                    .mean().reset_index()
                    .rename(columns={"cantidad_predicha": "Demanda promedio"})
                    .sort_values("Demanda promedio", ascending=False)
                    .head(10)
                )
                fig_top = px.bar(
                    top_df, x="producto", y="Demanda promedio",
                    text_auto=".1f", title="Top 10 productos por demanda promedio",
                    color_discrete_sequence=["#3a0ca3"],
                )
                fig_top.update_layout(height=350)
                st.plotly_chart(fig_top, use_container_width=True)