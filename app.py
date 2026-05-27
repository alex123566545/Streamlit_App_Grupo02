import streamlit as st

st.set_page_config(
    page_title="Sistema Predictivo Retail",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    :root {
        --bg:      #151922;
        --surface: #1c2230;
        --card:    #252c3d;

        --accent:  #4f8eff;
        --accent2: #a78bfa;
        --success: #34d399;

        --text:    #ffffff;
        --muted:   #c7ccd6;
        --muted2:  #9ca3af;

        --border:  rgba(255,255,255,0.12);
    }

    .stApp {
        background: linear-gradient(180deg, #151922 0%, #1a2030 100%) !important;
        font-family: 'DM Sans', sans-serif;
        color: var(--text);
    }

    .block-container {
        padding-top: 0 !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1400px;
    }

    /* ───────────────── HERO ───────────────── */
    .hero-section {
        text-align: center;
        padding: 5rem 2rem 4rem;
        position: relative;
        overflow: hidden;
    }

    .hero-section::before {
        content: '';
        position: absolute;
        top: -120px;
        left: 50%;
        transform: translateX(-50%);

        width: 700px;
        height: 400px;

        background: radial-gradient(
            ellipse at center,
            rgba(79,142,255,0.18) 0%,
            rgba(167,139,250,0.10) 50%,
            transparent 70%
        );

        pointer-events: none;
    }

    .hero-tag {
        display: inline-block;
        border: 1px solid rgba(79,142,255,0.4);
        background: rgba(79,142,255,0.10);
        color: #ffffff;

        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;

        padding: 0.35rem 1rem;
        border-radius: 20px;
        margin-bottom: 1.5rem;
    }

    .hero-title {
        font-family: 'Syne', sans-serif;
        font-size: clamp(2.5rem, 5vw, 4rem);
        font-weight: 800;
        line-height: 1.1;
        letter-spacing: -1.5px;

        color: #ffffff;
        margin-bottom: 1.25rem;
    }

    .hero-title .gradient-text {
        background: linear-gradient(
            135deg,
            var(--accent) 0%,
            var(--accent2) 100%
        );

        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .hero-subtitle {
        font-size: 1.05rem;
        color: var(--muted);

        max-width: 520px;
        margin: 0 auto 3rem;

        line-height: 1.65;
        font-weight: 400;
    }

    /* ───────────────── STATS ───────────────── */
    .stats-row {
        display: flex;
        justify-content: center;
        gap: 3rem;

        padding: 2.5rem 0;

        border-top: 1px solid var(--border);
        border-bottom: 1px solid var(--border);

        margin: 3rem 0;

        background: rgba(255,255,255,0.02);
        border-radius: 18px;
        backdrop-filter: blur(10px);
    }

    .stat-item {
        text-align: center;
    }

    .stat-value {
        font-family: 'Syne', sans-serif;
        font-size: 2rem;
        font-weight: 800;

        color: var(--accent);
        line-height: 1;
    }

    .stat-label {
        font-size: 0.78rem;
        color: var(--muted);

        margin-top: 0.4rem;

        text-transform: uppercase;
        letter-spacing: 0.09em;
        font-weight: 500;
    }

    /* ───────────────── CARDS ───────────────── */
    .cards-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);

        gap: 1rem;

        max-width: 900px;
        margin: 0 auto;

        padding: 0 1rem;
    }

    .cap-card {
        background: linear-gradient(
            180deg,
            rgba(37,44,61,0.95) 0%,
            rgba(31,38,54,0.95) 100%
        );

        border: 1px solid var(--border);
        border-radius: 16px;

        padding: 1.5rem;

        transition: all 0.25s ease;

        box-shadow: 0 8px 24px rgba(0,0,0,0.18);
    }

    .cap-card:hover {
        border-color: rgba(79,142,255,0.35);
        background: #31384d;

        transform: translateY(-4px);

        box-shadow: 0 16px 40px rgba(0,0,0,0.35);
    }

    .cap-icon {
        font-size: 1.75rem;
        margin-bottom: 0.75rem;
        display: block;
    }

    .cap-title {
        font-family: 'Syne', sans-serif;
        font-size: 0.95rem;
        font-weight: 700;

        color: #ffffff;
        margin-bottom: 0.4rem;
    }

    .cap-desc {
        font-size: 0.82rem;
        color: #b8c0cc;

        line-height: 1.55;
        font-weight: 400;
    }

    /* ───────────────── BOTONES ───────────────── */
    div[data-testid="stButton"] button {
        background: linear-gradient(
            135deg,
            var(--accent) 0%,
            #6ea6ff 100%
        ) !important;

        color: white !important;

        border: none !important;
        border-radius: 12px !important;

        font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important;

        transition: all 0.2s ease !important;

        box-shadow: 0 8px 20px rgba(79,142,255,0.20);
    }

    div[data-testid="stButton"] button:hover {
        transform: translateY(-1px);
        opacity: 0.92 !important;
    }

    div[data-testid="stButton"] button[kind="secondary"] {
        background: rgba(255,255,255,0.03) !important;

        border: 1px solid rgba(255,255,255,0.15) !important;

        color: #ffffff !important;

        box-shadow: none !important;
    }

    div[data-testid="stButton"] button[kind="secondary"]:hover {
        background: rgba(255,255,255,0.06) !important;

        color: #ffffff !important;

        border-color: rgba(255,255,255,0.25) !important;
    }

    /* ───────────────── SEPARADOR ───────────────── */
    hr {
        border-color: var(--border) !important;
        margin: 0 !important;
    }

    /* ───────────────── TEXTOS GLOBALES ───────────────── */
    p, span, label, div, h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }

    [data-testid="stMetricLabel"] {
        color: var(--muted) !important;
    }

    [data-testid="stMetricValue"] {
        color: #ffffff !important;
    }

    [data-testid="stMetricDelta"] {
        color: #34d399 !important;
    }

    .stCaption,
    [data-testid="stCaptionContainer"] {
        color: var(--muted2) !important;
    }

    [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
    }

    [data-testid="stMarkdownContainer"] span {
        color: #ffffff !important;
    }

    /* ───────────────── SCROLLBAR ───────────────── */
    ::-webkit-scrollbar {
        width: 10px;
    }

    ::-webkit-scrollbar-track {
        background: #1a2030;
    }

    ::-webkit-scrollbar-thumb {
        background: #39445f;
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #4f8eff;
    }

    /* ───────────────── RESPONSIVE ───────────────── */
    @media (max-width: 900px) {

        .cards-grid {
            grid-template-columns: 1fr;
        }

        .stats-row {
            flex-wrap: wrap;
            gap: 2rem;
        }

        .hero-section {
            padding: 4rem 1rem 3rem;
        }
    }
</style>
""", unsafe_allow_html=True)

from pages.dashboard import show_dashboard
from pages.prediccion import show_prediccion

# ───────────────── NAVEGACIÓN ─────────────────
if "pagina" not in st.session_state:
    st.session_state.pagina = "Inicio"

pages = ["Inicio", "Dashboard", "Predicción"]
icons = ["⌂", "◫", "⚡"]

col_brand, col_nav, _ = st.columns([2, 5, 1])

with col_brand:
    st.markdown(
        '''
        <div style="
            font-family:'Syne',sans-serif;
            font-weight:800;
            font-size:1.2rem;
            color:#ffffff;
            padding:0.6rem 0;
        ">
            📈 <span style="color:#4f8eff">Retail</span>Predict
        </div>
        ''',
        unsafe_allow_html=True
    )

with col_nav:

    nav_cols = st.columns(len(pages))

    for i, (page, icon) in enumerate(zip(pages, icons)):

        with nav_cols[i]:

            label = f"{icon} {page}" + (
                " 🆕" if page == "Predicción" else ""
            )

            btn_type = (
                "primary"
                if st.session_state.pagina == page
                else "secondary"
            )

            if st.button(
                label,
                key=f"nav_{page}",
                type=btn_type,
                use_container_width=True
            ):
                st.session_state.pagina = page
                st.rerun()

st.markdown("---")

# ───────────────── PÁGINAS ─────────────────
pagina = st.session_state.pagina

if pagina == "Inicio":

    st.markdown("""
    <div class="hero-section">

        <div class="hero-tag">
            ✦ Inteligencia Artificial · Retail
        </div>

        <div class="hero-title">
            Predicción inteligente<br>
            <span class="gradient-text">
                para tu negocio
            </span>
        </div>

        <div class="hero-subtitle">
            Analiza demanda, anticipa ventas y toma decisiones
            basadas en datos con modelos de IA en tiempo real.
        </div>

    </div>

    <div class="stats-row">

        <div class="stat-item">
            <div class="stat-value">94%</div>
            <div class="stat-label">Precisión</div>
        </div>

        <div class="stat-item">
            <div class="stat-value">+12</div>
            <div class="stat-label">Indicadores</div>
        </div>

        <div class="stat-item">
            <div class="stat-value">Real</div>
            <div class="stat-label">Tiempo</div>
        </div>

        <div class="stat-item">
            <div class="stat-value">5+</div>
            <div class="stat-label">Modelos IA</div>
        </div>

    </div>

    <div class="cards-grid">

        <div class="cap-card">
            <span class="cap-icon">📊</span>
            <div class="cap-title">Análisis de Demanda</div>
            <div class="cap-desc">
                Visualiza tendencias y patrones de consumo por producto y zona.
            </div>
        </div>

        <div class="cap-card">
            <span class="cap-icon">🤖</span>
            <div class="cap-title">Predicción de Ventas</div>
            <div class="cap-desc">
                Modelos de ML entrenados con tu histórico para proyecciones precisas.
            </div>
        </div>

        <div class="cap-card">
            <span class="cap-icon">🌦️</span>
            <div class="cap-title">Impacto del Clima</div>
            <div class="cap-desc">
                Correlaciona condiciones meteorológicas con comportamiento de compra.
            </div>
        </div>

        <div class="cap-card">
            <span class="cap-icon">🏷️</span>
            <div class="cap-title">Análisis Promocional</div>
            <div class="cap-desc">
                Mide el ROI real de cada campaña y optimiza descuentos.
            </div>
        </div>

        <div class="cap-card">
            <span class="cap-icon">⏰</span>
            <div class="cap-title">Horas Pico</div>
            <div class="cap-desc">
                Detecta automáticamente los momentos de mayor tráfico.
            </div>
        </div>

        <div class="cap-card">
            <span class="cap-icon">🏪</span>
            <div class="cap-title">Comparativa de Tiendas</div>
            <div class="cap-desc">
                Benchmarking entre zonas y sucursales en un solo panel.
            </div>
        </div>

    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    _, c_cta, _ = st.columns([2, 1, 2])

    with c_cta:

        if st.button("Ver Dashboard →", use_container_width=True):
            st.session_state.pagina = "Dashboard"
            st.rerun()

elif pagina == "Dashboard":
    show_dashboard()

elif pagina == "Predicción":
    show_prediccion()