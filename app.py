import streamlit as st

# =====================================
# CONFIG
# =====================================
st.set_page_config(
    page_title="Sistema Predictivo Retail",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =====================================
# CSS: Ocultar sidebar nativo + diseño
# =====================================
st.markdown("""
<style>
    /* Importar fuentes */
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

    /* Ocultar sidebar y botón de collapse de Streamlit */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* Variables de color */
    :root {
        --bg:        #0d0f14;
        --surface:   #161920;
        --card:      #1c1f2b;
        --accent:    #4f8eff;
        --accent2:   #a78bfa;
        --success:   #34d399;
        --text:      #e8eaf0;
        --muted:     #6b7280;
        --border:    rgba(255,255,255,0.07);
    }

    /* Fondo principal */
    .stApp {
        background: var(--bg) !important;
        font-family: 'DM Sans', sans-serif;
        color: var(--text);
    }
    .block-container {
        padding-top: 0 !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1400px;
    }

    /* ── NAVBAR ── */
    .navbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 2rem;
        background: rgba(22, 25, 32, 0.95);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid var(--border);
        margin: -1rem -2rem 2rem -2rem;
        position: sticky;
        top: 0;
        z-index: 999;
    }
    .navbar-brand {
        font-family: 'Syne', sans-serif;
        font-weight: 800;
        font-size: 1.25rem;
        color: var(--text);
        letter-spacing: -0.5px;
    }
    .navbar-brand span {
        color: var(--accent);
    }
    .nav-links {
        display: flex;
        gap: 0.25rem;
        align-items: center;
    }
    .nav-pill {
        padding: 0.45rem 1.1rem;
        border-radius: 8px;
        font-size: 0.875rem;
        font-weight: 500;
        cursor: pointer;
        border: none;
        background: transparent;
        color: var(--muted);
        transition: all 0.2s ease;
        font-family: 'DM Sans', sans-serif;
        letter-spacing: 0.01em;
    }
    .nav-pill:hover {
        background: rgba(79,142,255,0.1);
        color: var(--text);
    }
    .nav-pill.active {
        background: rgba(79,142,255,0.15);
        color: var(--accent);
        font-weight: 600;
    }
    .nav-badge {
        display: inline-block;
        background: linear-gradient(135deg, var(--accent), var(--accent2));
        color: white;
        font-size: 0.65rem;
        font-weight: 700;
        padding: 0.15rem 0.45rem;
        border-radius: 20px;
        margin-left: 0.35rem;
        vertical-align: middle;
        letter-spacing: 0.04em;
    }

    /* ── HERO ── */
    .hero-section {
        text-align: center;
        padding: 5rem 2rem 4rem;
        position: relative;
        overflow: hidden;
    }
    .hero-section::before {
        content: '';
        position: absolute;
        top: -120px; left: 50%;
        transform: translateX(-50%);
        width: 700px; height: 400px;
        background: radial-gradient(ellipse at center,
            rgba(79,142,255,0.12) 0%,
            rgba(167,139,250,0.06) 50%,
            transparent 70%);
        pointer-events: none;
    }
    .hero-tag {
        display: inline-block;
        border: 1px solid rgba(79,142,255,0.3);
        background: rgba(79,142,255,0.08);
        color: var(--accent);
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
        color: var(--text);
        margin-bottom: 1.25rem;
    }
    .hero-title .gradient-text {
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent2) 100%);
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
        font-weight: 300;
    }

    /* ── TARJETAS DE CAPACIDADES ── */
    .cards-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        max-width: 900px;
        margin: 0 auto;
        padding: 0 1rem;
    }
    .cap-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 1.5rem;
        transition: all 0.25s ease;
        cursor: default;
    }
    .cap-card:hover {
        border-color: rgba(79,142,255,0.25);
        background: #20243a;
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.3);
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
        color: var(--text);
        margin-bottom: 0.35rem;
    }
    .cap-desc {
        font-size: 0.8rem;
        color: var(--muted);
        line-height: 1.5;
    }

    /* ── STATS ── */
    .stats-row {
        display: flex;
        justify-content: center;
        gap: 3rem;
        padding: 2.5rem 0;
        border-top: 1px solid var(--border);
        border-bottom: 1px solid var(--border);
        margin: 3rem 0;
    }
    .stat-item { text-align: center; }
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
        margin-top: 0.35rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    /* ── CTA BUTTONS ── */
    .cta-row {
        display: flex;
        gap: 1rem;
        justify-content: center;
        margin-top: 2.5rem;
    }
    .btn-primary {
        background: var(--accent);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 10px;
        font-size: 0.9rem;
        font-weight: 600;
        cursor: pointer;
        font-family: 'DM Sans', sans-serif;
        transition: all 0.2s;
    }
    .btn-primary:hover { opacity: 0.85; transform: translateY(-1px); }
    .btn-ghost {
        background: transparent;
        color: var(--muted);
        border: 1px solid var(--border);
        padding: 0.75rem 2rem;
        border-radius: 10px;
        font-size: 0.9rem;
        font-weight: 500;
        cursor: pointer;
        font-family: 'DM Sans', sans-serif;
        transition: all 0.2s;
    }
    .btn-ghost:hover { color: var(--text); border-color: rgba(255,255,255,0.15); }

    /* Streamlit widgets override */
    div[data-testid="stButton"] button {
        background: var(--accent) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        transition: opacity 0.2s !important;
    }
    div[data-testid="stButton"] button:hover { opacity: 0.85 !important; }
</style>
""", unsafe_allow_html=True)

# =====================================
# IMPORTAR PÁGINAS
# =====================================
from pages.dashboard import show_dashboard
from pages.prediccion import show_prediccion

# =====================================
# ESTADO DE NAVEGACIÓN
# =====================================
if "pagina" not in st.session_state:
    st.session_state.pagina = "Inicio"

# =====================================
# NAVBAR
# =====================================
pages = ["Inicio", "Dashboard", "Predicción"]
icons  = ["⌂", "◫", "⚡"]

cols = st.columns([2, 5, 1])
with cols[0]:
    st.markdown('<div class="navbar-brand">📈 <span>Retail</span>Predict</div>', unsafe_allow_html=True)

with cols[1]:
    nav_cols = st.columns(len(pages))
    for i, (page, icon) in enumerate(zip(pages, icons)):
        with nav_cols[i]:
            label = f"{icon} {page}"
            if page == "Predicción":
                label += " 🆕"
            is_active = st.session_state.pagina == page
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, key=f"nav_{page}", type=btn_type, use_container_width=True):
                st.session_state.pagina = page
                st.rerun()

st.markdown("---")

# =====================================
# PÁGINAS
# =====================================
pagina = st.session_state.pagina

if pagina == "Inicio":

    # Hero
    st.markdown("""
    <div class="hero-section">
        <div class="hero-tag">✦ Inteligencia Artificial · Retail</div>
        <div class="hero-title">
            Predicción inteligente<br>
            <span class="gradient-text">para tu negocio</span>
        </div>
        <div class="hero-subtitle">
            Analiza demanda, anticipa ventas y toma decisiones
            basadas en datos con modelos de IA en tiempo real.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Stats
    st.markdown("""
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
    """, unsafe_allow_html=True)

    # Capacidades
    st.markdown("""
    <div class="cards-grid">
        <div class="cap-card">
            <span class="cap-icon">📊</span>
            <div class="cap-title">Análisis de Demanda</div>
            <div class="cap-desc">Visualiza tendencias y patrones de consumo por producto y zona.</div>
        </div>
        <div class="cap-card">
            <span class="cap-icon">🤖</span>
            <div class="cap-title">Predicción de Ventas</div>
            <div class="cap-desc">Modelos de ML entrenados con tu histórico para proyecciones precisas.</div>
        </div>
        <div class="cap-card">
            <span class="cap-icon">🌦️</span>
            <div class="cap-title">Impacto del Clima</div>
            <div class="cap-desc">Correlaciona condiciones meteorológicas con comportamiento de compra.</div>
        </div>
        <div class="cap-card">
            <span class="cap-icon">🏷️</span>
            <div class="cap-title">Análisis Promocional</div>
            <div class="cap-desc">Mide el ROI real de cada campaña y optimiza descuentos.</div>
        </div>
        <div class="cap-card">
            <span class="cap-icon">⏰</span>
            <div class="cap-title">Horas Pico</div>
            <div class="cap-desc">Detecta automáticamente los momentos de mayor tráfico.</div>
        </div>
        <div class="cap-card">
            <span class="cap-icon">🏪</span>
            <div class="cap-title">Comparativa de Tiendas</div>
            <div class="cap-desc">Benchmarking entre zonas y sucursales en un solo panel.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # CTAs
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([2, 1, 2])
    with c2:
        if st.button("Ver Dashboard →", use_container_width=True):
            st.session_state.pagina = "Dashboard"
            st.rerun()

elif pagina == "Dashboard":
    show_dashboard()

elif pagina == "Predicción":
    show_prediccion()