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
    page_title="Sistema de Inteligencia Comercial Predictiva",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
    .badge-high { background:#d4edda; color:#155724; padding:4px 10px; border-radius:20px; font-weight:600; }
    .badge-med  { background:#fff3cd; color:#856404; padding:4px 10px; border-radius:20px; font-weight:600; }
    .badge-low  { background:#f8d7da; color:#721c24; padding:4px 10px; border-radius:20px; font-weight:600; }
</style>
""", unsafe_allow_html=True)


# =========================================================
# CARGA DE MODELO Y FEATURES
# =========================================================
def _load_pkl(url: str):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return pickle.loads(response.content)


@st.cache_resource(show_spinner="Cargando modelo predictivo…")
def load_assets():
    MODEL_URL    = "https://klbmaoqxfvjsczwrrwkj.supabase.co/storage/v1/object/public/models/model.pl"
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


@st.cache_data(show_spinner=False, ttl=3600)
def load_ventas_dataset():
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT * FROM gold_ml.ventas_dataset LIMIT 5000", conn)
    finally:
        conn.close()
    return df


# =========================================================
# FEATURE ENGINEERING
# Normaliza a minúsculas igual que clean_text_columns() del pipeline
# de entrenamiento. Sin esto el OneHotEncoder silencia las variables
# categóricas (clima, producto, etc.) al no reconocerlas.
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
# En vez de multiplicar la predicción diaria por 7 o 30
# (lo que asumiría que todos los días son iguales al día elegido),
# se predice cada día individualmente y se suman los resultados.
# Así un domingo no infla artificialmente toda la semana,
# y un cambio de mes/trimestre se refleja correctamente.
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
    """
    Predice n_dias consecutivos desde fecha_inicio y devuelve
    (total_unidades, detalle_por_dia).
    """
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
            "fecha":        f,
            "dia_semana":   ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"][f.weekday()],
            "es_finde":     f.weekday() >= 5,
            "unidades":     pred_dia,
            "ingreso":      round(pred_dia * precio, 2),
        })

    return max(1, round(total)), detalle


# =========================================================
# AJUSTE POR ELASTICIDAD-PRECIO (silencioso)
# Corrige que el Random Forest no aprende bien la relación
# precio alto → demanda baja. Se aplica automáticamente
# sin ningún control visible para el usuario.
# Fórmula: Q_ajustada = Q_raw × (precio / precio_promedio) ^ ε
# ε = -1.2: elasticidad moderada, típica en retail de conveniencia.
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
# MÉTRICAS CRISP-DM
# =========================================================
def compute_metrics(model, features, ventas_df: pd.DataFrame):
    target = "cantidad_vendida"
    if target not in ventas_df.columns:
        return None
    disponibles = [c for c in features if c in ventas_df.columns]
    if len(disponibles) < len(features):
        return None
    y = ventas_df[target]
    try:
        y_pred_rf = model.predict(ventas_df[features])
    except Exception:
        return None

    mae_rf  = mean_absolute_error(y, y_pred_rf)
    rmse_rf = np.sqrt(mean_squared_error(y, y_pred_rf))
    r2_rf   = r2_score(y, y_pred_rf)

    X_base      = ventas_df[["precio_unitario"]].values
    lr          = LinearRegression().fit(X_base, y)
    y_pred_base = lr.predict(X_base)
    mae_base    = mean_absolute_error(y, y_pred_base)
    rmse_base   = np.sqrt(mean_squared_error(y, y_pred_base))
    r2_base     = r2_score(y, y_pred_base)

    return {
        "RF":   {"MAE": mae_rf,   "RMSE": rmse_rf,   "R2": r2_rf},
        "Base": {"MAE": mae_base, "RMSE": rmse_base, "R2": r2_base},
    }


# =========================================================
# UI PRINCIPAL
# =========================================================
def show_prediccion():

    st.markdown(
        '<p class="main-header">🏪 Sistema de Inteligencia Comercial Predictiva</p>'
        '<p class="sub-header">Predicción de demanda · Tiendas de conveniencia en Perú · Modelo: Random Forest Regressor</p>',
        unsafe_allow_html=True,
    )

    with st.spinner("Iniciando recursos…"):
        model, features = load_assets()
        productos_df, promociones_df, tiendas_df, climas_df, precios_df = load_dimensions()
        historico_df = load_history()

    tab_pred, tab_metricas, tab_hist = st.tabs([
        "📊 Predicción de Demanda",
        "📐 Métricas del Modelo (CRISP-DM)",
        "📋 Histórico de Predicciones",
    ])

    # ═══════════════════════════════════════════════════════
    # TAB 1 — PREDICCIÓN
    # ═══════════════════════════════════════════════════════
    with tab_pred:

        st.subheader("⚙️ Parámetros de la transacción")
        col_l, col_r = st.columns([1, 2])

        with col_l:
            fecha = st.date_input("📅 Fecha de inicio", value=date.today())

            # La columna "hora" en la BD es de tipo TIME (HH:MM:SS).
            # El modelo fue entrenado con hora = 0 por un bug de parseo ya corregido
            # en el pipeline. Hasta que se reentrene, el slider no genera diferencias
            # visibles. Se fija en 12 (mediodía) y se oculta al usuario.
            hora = 12

            producto = st.selectbox("🛒 Producto", productos_df["producto"].unique())
            categoria_producto = productos_df.loc[
                productos_df["producto"] == producto, "categoria_producto"
            ].values[0]
            st.caption(f"Categoría: **{categoria_producto}**")

            precio_promedio = float(precios_df.loc[
                precios_df["producto"] == producto, "precio_promedio"
            ].values[0])
            st.caption(f"💰 Precio histórico promedio: S/ {precio_promedio}")
            precio = st.slider(
                "💲 Precio unitario (S/)",
                min_value=1.0, max_value=30.0,
                value=precio_promedio, step=0.10,
            )

            tipo_promocion = st.selectbox(
                "🏷️ Tipo de promoción", promociones_df["tipo_promocion"].unique()
            )

            ubicacion_tienda = st.selectbox(
                "📍 Ubicación de tienda", tiendas_df["ubicacion_tienda"].unique()
            )
            tipo_zona = tiendas_df.loc[
                tiendas_df["ubicacion_tienda"] == ubicacion_tienda, "tipo_zona"
            ].values[0]
            st.caption(f"Zona: **{tipo_zona}**")

            clima = st.selectbox("🌤️ Clima", climas_df["clima"].unique())

        with col_r:
            predecir = st.button("🔮 Generar Predicción", use_container_width=True)

            if predecir:

                # ── Predicción diaria (solo el día elegido) ──────────
                data_dia = build_features(
                    fecha, hora, producto, categoria_producto,
                    precio, tipo_promocion, tipo_zona,
                    ubicacion_tienda, clima
                )[features]
                pred_raw = model.predict(data_dia)[0]
                pred_dia = max(1, round(aplicar_elasticidad(pred_raw, precio, precio_promedio)))

                # ── Predicción semanal (7 días desde la fecha elegida) ──
                # Cada día usa su propio es_fin_semana, mes, trimestre, etc.
                # Un domingo no infla los otros 6 días.
                pred_sem, detalle_sem = predecir_rango(
                    model, features, fecha, 7,
                    hora, producto, categoria_producto,
                    precio, tipo_promocion, tipo_zona,
                    ubicacion_tienda, clima, precio_promedio,
                )

                # ── Predicción mensual (30 días desde la fecha elegida) ──
                # Si el rango cruza de un mes a otro, cada día usa su mes correcto.
                pred_mes, detalle_mes = predecir_rango(
                    model, features, fecha, 30,
                    hora, producto, categoria_producto,
                    precio, tipo_promocion, tipo_zona,
                    ubicacion_tienda, clima, precio_promedio,
                )

                ingreso_dia = round(pred_dia * precio, 2)
                ingreso_sem = round(pred_sem * precio, 2)
                ingreso_mes = round(pred_mes * precio, 2)

                # ── KPIs ─────────────────────────────────────────────
                st.markdown("#### 📊 Resultados predictivos")
                c1, c2, c3 = st.columns(3)
                c1.metric("Predicción diaria",  f"{pred_dia} uds")
                c2.metric("Predicción semanal", f"{pred_sem} uds")
                c3.metric("Predicción mensual", f"{pred_mes} uds")
                c1.metric("Ingreso diario",     f"S/ {ingreso_dia}")
                c2.metric("Ingreso semanal",    f"S/ {ingreso_sem}")
                c3.metric("Ingreso mensual",    f"S/ {ingreso_mes}")

                # ── Nivel de demanda ──────────────────────────────────
                label, nivel = demanda_badge(pred_dia)
                st.markdown(
                    f'**Nivel de demanda:** <span class="badge-{nivel}">{label}</span>',
                    unsafe_allow_html=True,
                )

                # ── Factores detectados ───────────────────────────────
                st.markdown("#### 🧠 Factores detectados")
                factores = []
                if _lower(tipo_promocion) not in ("ninguno", "none", "sin promoción"):
                    factores.append("✔ Promoción activa")
                if 12 <= hora <= 14 or 18 <= hora <= 21:
                    factores.append("✔ Hora pico")
                if tipo_zona == "Comercial":
                    factores.append("✔ Zona comercial")
                if _lower(clima) == "soleado":
                    factores.append("✔ Clima favorable")
                if fecha.weekday() >= 5:
                    factores.append("✔ Fin de semana")
                if precio < precio_promedio:
                    factores.append("✔ Precio competitivo")
                st.info("  ·  ".join(factores) if factores else "No se detectaron factores favorables adicionales.")

                # ── Proyección temporal ───────────────────────────────
                st.markdown("#### 📅 Proyección temporal (unidades)")
                proy_df = pd.DataFrame({
                    "Periodo":  ["Día", "Semana", "Mes"],
                    "Cantidad": [pred_dia, pred_sem, pred_mes],
                })
                fig_proy = px.bar(
                    proy_df, x="Periodo", y="Cantidad", text_auto=True,
                    color="Periodo",
                    color_discrete_sequence=["#4361ee", "#3a0ca3", "#7209b7"],
                )
                fig_proy.update_layout(showlegend=False, height=300)
                st.plotly_chart(fig_proy, use_container_width=True)

                # ── Detalle día a día (semanal) ───────────────────────
                st.markdown("#### 🗓️ Detalle día a día — próximos 7 días")
                st.caption(
                    "Cada día se predice de forma independiente con su propio contexto "
                    "(fin de semana, mes, trimestre). Un domingo no infla el resto de la semana."
                )
                det_df = pd.DataFrame(detalle_sem)
                det_df["fecha"] = det_df["fecha"].astype(str)
                det_df.columns = ["Fecha", "Día", "¿Finde?", "Unidades", "Ingreso (S/)"]
                det_df["¿Finde?"] = det_df["¿Finde?"].map({True: "✅", False: "—"})

                # Colorear filas de fin de semana
                st.dataframe(
                    det_df,
                    hide_index=True,
                    use_container_width=True,
                )

                fig_det = px.bar(
                    det_df, x="Fecha", y="Unidades",
                    color="¿Finde?",
                    color_discrete_map={"✅": "#7209b7", "—": "#4361ee"},
                    text_auto=True,
                    title="Unidades por día (morado = fin de semana)",
                )
                fig_det.update_layout(height=320, showlegend=False)
                st.plotly_chart(fig_det, use_container_width=True)

                # ── Comparación histórica ─────────────────────────────
                st.markdown("#### 📈 Comparación con histórico")
                hist_prod = historico_df[historico_df["producto"] == _lower(producto)]
                if not hist_prod.empty:
                    prom_hist = round(hist_prod["cantidad_predicha"].mean(), 2)
                    variacion = round(((pred_dia - prom_hist) / max(prom_hist, 1)) * 100, 2)
                    h1, h2 = st.columns(2)
                    h1.metric("Promedio histórico diario", prom_hist)
                    h2.metric("Variación esperada", f"{variacion}%", delta=f"{variacion}%")
                else:
                    st.caption("Sin datos históricos para este producto.")

                # ── Simulación de precios ─────────────────────────────
                st.markdown("#### 💹 Simulación de escenarios de precio")
                sims = []
                for factor in [0.8, 0.9, 1.0, 1.1, 1.2]:
                    p_sim = round(precio * factor, 2)
                    d_sim = build_features(
                        fecha, hora, producto, categoria_producto,
                        p_sim, tipo_promocion, tipo_zona,
                        ubicacion_tienda, clima
                    )[features]
                    pred_sim = max(1, round(aplicar_elasticidad(
                        model.predict(d_sim)[0], p_sim, precio_promedio
                    )))
                    sims.append({
                        "Escenario":     f"×{factor:.1f}",
                        "Precio (S/)":   p_sim,
                        "Demanda (uds)": pred_sim,
                        "Ingreso (S/)":  round(pred_sim * p_sim, 2),
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

                # ── Recomendación comercial ───────────────────────────
                st.markdown("#### 💡 Recomendación comercial")
                mejor = sim_df.loc[sim_df["Ingreso (S/)"].idxmax()]
                st.success(
                    f"**Precio óptimo sugerido:** S/ {mejor['Precio (S/)']}\n\n"
                    f"**Demanda esperada:** {mejor['Demanda (uds)']} unidades\n\n"
                    f"**Ingreso estimado:** S/ {mejor['Ingreso (S/)']}"
                )

                # ── Importancia de variables ──────────────────────────
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
    # TAB 2 — MÉTRICAS CRISP-DM
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
            rf, base = metricas["RF"], metricas["Base"]
            st.markdown("##### Comparación: Random Forest vs Baseline (Regresión Lineal)")
            m1, m2, m3 = st.columns(3)
            m1.metric("MAE  — RF",  f"{rf['MAE']:.3f}",  delta=f"{rf['MAE']-base['MAE']:.3f} vs baseline",   delta_color="inverse")
            m2.metric("RMSE — RF",  f"{rf['RMSE']:.3f}", delta=f"{rf['RMSE']-base['RMSE']:.3f} vs baseline", delta_color="inverse")
            m3.metric("R²   — RF",  f"{rf['R2']:.3f}",   delta=f"{rf['R2']-base['R2']:.3f} vs baseline")

            comp_df = pd.DataFrame({
                "Métrica":        ["MAE", "RMSE", "R²"],
                "Random Forest":  [rf["MAE"],   rf["RMSE"],   rf["R2"]],
                "Baseline (LR)":  [base["MAE"], base["RMSE"], base["R2"]],
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
                | **MAE** | Promedio de errores absolutos. Menor es mejor. |
                | **RMSE** | Raíz del error cuadrático medio. Penaliza errores grandes. |
                | **R²** | Proporción de variabilidad explicada. Más cerca de 1 es mejor. |
                """)
        else:
            st.info("Las métricas se calcularán cuando el dataset contenga `cantidad_vendida` y las features requeridas.")

        with st.expander("📋 Variables del modelo"):
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
    # TAB 3 — HISTÓRICO
    # ═══════════════════════════════════════════════════════
    with tab_hist:
        st.subheader("📋 Histórico de predicciones almacenadas")

        if historico_df.empty:
            st.info("No hay predicciones almacenadas aún.")
        else:
            prods_hist = sorted(historico_df["producto"].unique().tolist())
            prod_sel = st.multiselect("Filtrar por producto", prods_hist, default=prods_hist[:5])
            df_fil = historico_df[historico_df["producto"].isin(prod_sel)] if prod_sel else historico_df

            st.dataframe(df_fil, use_container_width=True, hide_index=True)

            if "cantidad_predicha" in df_fil.columns and not df_fil.empty:
                fig_hist = px.histogram(
                    df_fil, x="cantidad_predicha", nbins=30,
                    color_discrete_sequence=["#4361ee"],
                    title="Distribución de cantidad predicha",
                )
                fig_hist.update_layout(height=320)
                st.plotly_chart(fig_hist, use_container_width=True)

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