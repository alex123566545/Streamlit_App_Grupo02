import streamlit as st
import pandas as pd
import plotly.express as px

from utils.database import get_connection

DASHBOARD_CSS = """
<style>
    .kpi-card { background: var(--card, #1c1f2b); border: 1px solid var(--border, rgba(255,255,255,0.07)); border-radius: 14px; padding: 1.25rem 1.5rem; transition: all 0.2s ease; }
    .kpi-card:hover { border-color: rgba(79,142,255,0.25); transform: translateY(-2px); box-shadow: 0 8px 32px rgba(0,0,0,0.25); }
    .kpi-label { font-size: 0.75rem; color: var(--muted, #b0b8cc); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem; font-weight: 600; }
    .kpi-value { font-family: 'Syne', sans-serif; font-size: 1.9rem; font-weight: 800; color: var(--text, #e8eaf0); line-height: 1; }
    .kpi-value.accent  { color: #4f8eff; }
    .kpi-value.success { color: #34d399; }
    .kpi-value.purple  { color: #a78bfa; }
    .section-header { display: flex; align-items: center; gap: 0.6rem; margin: 2rem 0 1rem; }
    .section-header .dot { width: 8px; height: 8px; border-radius: 50%; background: #4f8eff; flex-shrink: 0; }
    .section-title { font-family: 'Syne', sans-serif; font-size: 1.1rem; font-weight: 700; color: #e8eaf0; }
    .filter-title { font-family: 'Syne', sans-serif; font-size: 0.8rem; font-weight: 700; color: #b0b8cc; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.75rem; }

    /* ── Selectbox y Multiselect: fondo oscuro, texto legible ── */
    div[data-baseweb="select"] > div {
        background: #1c1f2b !important;
        border-color: rgba(255,255,255,0.12) !important;
        border-radius: 8px !important;
        color: #e8eaf0 !important;
    }
    div[data-baseweb="select"] > div > div {
        color: #e8eaf0 !important;
    }
    /* Dropdown desplegado */
    div[data-baseweb="popover"] ul {
        background: #1c1f2b !important;
        border: 1px solid rgba(255,255,255,0.10) !important;
    }
    div[data-baseweb="popover"] li {
        background: #1c1f2b !important;
        color: #e8eaf0 !important;
    }
    div[data-baseweb="popover"] li:hover {
        background: #20243a !important;
        color: #ffffff !important;
    }
    /* Tags del multiselect */
    div[data-baseweb="tag"] { background: rgba(79,142,255,0.2) !important; color: #7eaaff !important; }
    div[data-baseweb="tag"] span { color: #7eaaff !important; }
</style>
"""

PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_family="DM Sans",
    font_color="#e8eaf0",
    margin=dict(t=30, b=30, l=10, r=10),
    legend=dict(bgcolor="rgba(22,25,32,0.8)", bordercolor="rgba(255,255,255,0.07)", borderwidth=1),
)
ACCENT      = "#4f8eff"
COLOR_SEQ   = ["#4f8eff", "#a78bfa", "#34d399", "#f97316", "#fb7185", "#fbbf24"]
ORDEN_DIAS  = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
ORDEN_MESES = ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]


def apply_layout(fig):
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.05)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.05)")
    return fig


def show_dashboard():

    if "pagina" not in st.session_state:
        st.stop()

    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-bottom:1.5rem;">
        <div style="font-family:'Syne',sans-serif;font-size:1.8rem;font-weight:800;color:#e8eaf0;letter-spacing:-0.5px;">
            Inteligencia Comercial
        </div>
        <div style="color:#b0b8cc;font-size:0.9rem;margin-top:0.25rem;">
            Análisis predictivo de ventas en tiempo real
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Cargar datos ──────────────────────────────────────────────────────────
    @st.cache_data
    def load_data():
        conn = get_connection()
        df = pd.read_sql("SELECT * FROM gold_ml.ventas_predicha", conn)
        conn.close()
        return df

    df = load_data()

    if df.empty:
        st.warning("No existen datos en ventas_predicha")
        st.stop()

    df["fecha"]      = pd.to_datetime(df["fecha"])
    df["anio"]       = df["fecha"].dt.year
    df["mes_nombre"] = df["fecha"].dt.strftime("%B")
    df["semana"]     = df["fecha"].dt.isocalendar().week
    df["dia"]        = df["fecha"].dt.day_name()

    # ── Filtros ───────────────────────────────────────────────────────────────
    with st.expander("🔎 Filtros y configuración", expanded=True):

        st.markdown('<div class="filter-title">Filtros de datos</div>', unsafe_allow_html=True)
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)

        with col_f1:
            productos = st.multiselect(
                "Producto", options=df["producto"].unique(),
                default=df["producto"].unique(), key="f_productos"
            )
        with col_f2:
            climas = st.multiselect(
                "Clima", options=df["clima"].unique(),
                default=df["clima"].unique(), key="f_climas"
            )
        with col_f3:
            zonas = st.multiselect(
                "Zona", options=df["tipo_zona"].unique(),
                default=df["tipo_zona"].unique(), key="f_zonas"
            )
        with col_f4:
            promociones = st.multiselect(
                "Promoción", options=df["tipo_promocion"].unique(),
                default=df["tipo_promocion"].unique(), key="f_promos"
            )

        st.markdown('<div class="filter-title" style="margin-top:1rem;">Configuración de análisis</div>',
                    unsafe_allow_html=True)

        tipo_analisis = st.selectbox(
            "Tipo de análisis",
            ["Demanda Temporal", "Producto vs Tiempo", "Promoción vs Tiempo",
             "Clima vs Tiempo", "Zona vs Tiempo"],
            key="tipo_analisis"
        )

        tipo_tiempo       = "Mes"
        producto_analisis = "Todos"

        if tipo_analisis == "Demanda Temporal":
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                tipo_tiempo = st.selectbox(
                    "Agrupar por", ["Día", "Semana", "Mes", "Hora"], key="tipo_tiempo"
                )
            with col_a2:
                producto_analisis = st.selectbox(
                    "Producto específico",
                    ["Todos"] + list(df["producto"].unique()),
                    key="prod_analisis"
                )

    # ── Aplicar filtros ───────────────────────────────────────────────────────
    df_filtrado = df[
        df["producto"].isin(productos) &
        df["clima"].isin(climas) &
        df["tipo_zona"].isin(zonas) &
        df["tipo_promocion"].isin(promociones)
    ]

    if tipo_analisis == "Demanda Temporal" and producto_analisis != "Todos":
        df_temporal = df_filtrado[df_filtrado["producto"] == producto_analisis].copy()
    else:
        df_temporal = df_filtrado.copy()

    # ── KPIs ──────────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-header"><div class="dot"></div>'
        '<div class="section-title">Indicadores clave</div></div>',
        unsafe_allow_html=True
    )

    producto_top = (
        df_filtrado.groupby("producto")["cantidad_predicha"].sum().idxmax()
        if not df_filtrado.empty else "—"
    )
    total_pred = int(df_filtrado["cantidad_predicha"].sum()) if not df_filtrado.empty else 0
    prom_pred  = round(df_filtrado["cantidad_predicha"].mean(), 2) if not df_filtrado.empty else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Total registros</div>'
                    f'<div class="kpi-value accent">{len(df_filtrado):,}</div></div>',
                    unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Cantidad predicha total</div>'
                    f'<div class="kpi-value">{total_pred:,}</div></div>',
                    unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Promedio por registro</div>'
                    f'<div class="kpi-value success">{prom_pred}</div></div>',
                    unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Producto más demandado</div>'
                    f'<div class="kpi-value purple" style="font-size:1.15rem;padding-top:0.3rem;">'
                    f'{producto_top}</div></div>',
                    unsafe_allow_html=True)

    # ── Gráfico ───────────────────────────────────────────────────────────────
    st.markdown(
        f'<div class="section-header"><div class="dot"></div>'
        f'<div class="section-title">{tipo_analisis}</div></div>',
        unsafe_allow_html=True
    )

    fig = None

    if tipo_analisis == "Demanda Temporal":
        if tipo_tiempo == "Día":
            t = df_temporal.groupby("dia")["cantidad_predicha"].sum().reset_index()
            t["dia"] = pd.Categorical(t["dia"], categories=ORDEN_DIAS, ordered=True)
            fig = px.bar(t.sort_values("dia"), x="dia", y="cantidad_predicha",
                         text_auto=True, color_discrete_sequence=[ACCENT])
        elif tipo_tiempo == "Semana":
            t = df_temporal.groupby("semana")["cantidad_predicha"].sum().reset_index()
            fig = px.line(t, x="semana", y="cantidad_predicha",
                          markers=True, color_discrete_sequence=[ACCENT])
        elif tipo_tiempo == "Mes":
            t = df_temporal.groupby("mes_nombre")["cantidad_predicha"].sum().reset_index()
            t["mes_nombre"] = pd.Categorical(t["mes_nombre"], categories=ORDEN_MESES, ordered=True)
            fig = px.line(t.sort_values("mes_nombre"), x="mes_nombre", y="cantidad_predicha",
                          markers=True, color_discrete_sequence=[ACCENT])
        else:  # Hora
            t = df_temporal.groupby("hora")["cantidad_predicha"].sum().reset_index()
            fig = px.line(t, x="hora", y="cantidad_predicha",
                          markers=True, color_discrete_sequence=[ACCENT])

    elif tipo_analisis == "Producto vs Tiempo":
        t = df_filtrado.groupby(["producto", "mes_nombre"])["cantidad_predicha"].sum().reset_index()
        t["mes_nombre"] = pd.Categorical(t["mes_nombre"], categories=ORDEN_MESES, ordered=True)
        fig = px.bar(t.sort_values("mes_nombre"), x="mes_nombre", y="cantidad_predicha",
                     color="producto", barmode="group", color_discrete_sequence=COLOR_SEQ)

    elif tipo_analisis == "Promoción vs Tiempo":
        t = df_filtrado.groupby(["tipo_promocion", "mes_nombre"])["cantidad_predicha"].mean().reset_index()
        t["mes_nombre"] = pd.Categorical(t["mes_nombre"], categories=ORDEN_MESES, ordered=True)
        fig = px.line(t.sort_values("mes_nombre"), x="mes_nombre", y="cantidad_predicha",
                      color="tipo_promocion", markers=True, color_discrete_sequence=COLOR_SEQ)

    elif tipo_analisis == "Clima vs Tiempo":
        t = df_filtrado.groupby(["clima", "mes_nombre"])["cantidad_predicha"].mean().reset_index()
        t["mes_nombre"] = pd.Categorical(t["mes_nombre"], categories=ORDEN_MESES, ordered=True)
        fig = px.line(t.sort_values("mes_nombre"), x="mes_nombre", y="cantidad_predicha",
                      color="clima", markers=True, color_discrete_sequence=COLOR_SEQ)

    elif tipo_analisis == "Zona vs Tiempo":
        t = df_filtrado.groupby(["tipo_zona", "mes_nombre"])["cantidad_predicha"].sum().reset_index()
        t["mes_nombre"] = pd.Categorical(t["mes_nombre"], categories=ORDEN_MESES, ordered=True)
        fig = px.bar(t.sort_values("mes_nombre"), x="mes_nombre", y="cantidad_predicha",
                     color="tipo_zona", barmode="group", color_discrete_sequence=COLOR_SEQ)
    if fig:
            apply_layout(fig)
            fig.update_layout(
                title_font_color="#ffffff",
                font=dict(color="#ffffff"),
                xaxis=dict(
                    tickfont=dict(color="#ffffff"),
                    title_font=dict(color="#ffffff"),
                ),
                yaxis=dict(
                    tickfont=dict(color="#ffffff"),
                    title_font=dict(color="#ffffff"),
                ),
                legend=dict(
                    font=dict(color="#ffffff"),
                ),
            )
            fig.update_traces(
                textfont=dict(color="#ffffff"),
            )
            st.plotly_chart(fig, use_container_width=True)

    # ── Tabla ─────────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-header"><div class="dot"></div>'
        '<div class="section-title">Datos analizados</div></div>',
        unsafe_allow_html=True
    )
    st.dataframe(df_filtrado, use_container_width=True, height=300)