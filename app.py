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
        --bg:      #0d0f14;
        --surface: #161920;
        --card:    #1c1f2b;
        --accent:  #4f8eff;
        --accent2: #a78bfa;
        --success: #34d399;
        --text:    #FFFCFC;
        --muted:   #b0b8cc;      /* ← era #6b7280, ahora mucho más legible */
        --muted2:  #8892a4;      /* tono medio para jerarquía secundaria   */
        --border:  rgba(255,255,255,0.09);
    }

    .stApp { background: var(--bg) !important; font-family: 'DM Sans', sans-serif; color: var(--text); }
    .block-container { padding-top: 0 !important; padding-left: 2rem !important; padding-right: 2rem !important; max-width: 1400px; }

    /* ── Hero ── */
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
            rgba(79,142,255,0.15) 0%,
            rgba(167,139,250,0.08) 50%,
            transparent 70%);
        pointer-events: none;
    }

    .hero-tag {
        display: inline-block;
        border: 1px solid rgba(79,142,255,0.4);
        background: rgba(79,142,255,0.10);
        color: #7eaaff;           /* más claro que el accent puro */
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

    /* ← subtítulo hero: antes #6b7280, ahora visible */
    .hero-subtitle {
        font-size: 1.05rem;
        color: var(--muted);
        max-width: 520px;
        margin: 0 auto 3rem;
        line-height: 1.65;
        font-weight: 400;         /* era 300, subimos un poco el peso también */
    }

    /* ── Stats ── */
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
    /* ← stat label: antes #6b7280 casi invisible, ahora legible */
    .stat-label {
        font-size: 0.78rem;
        color: var(--muted);
        margin-top: 0.4rem;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        font-weight: 500;
    }

    /* ── Cards ── */
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
    }
    .cap-card:hover {
        border-color: rgba(79,142,255,0.30);
        background: #20243a;
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.35);
    }
    .cap-icon { font-size: 1.75rem; margin-bottom: 0.75rem; display: block; }

    .cap-title {
        font-family: 'Syne', sans-serif;
        font-size: 0.95rem;
        font-weight: 700;
        color: var(--text);
        margin-bottom: 0.4rem;
    }
    /* ← descripción de cards: el cambio más notorio */
    .cap-desc {
        font-size: 0.82rem;
        color: var(--muted);      /* era #6b7280 → ahora #b0b8cc */
        line-height: 1.55;
        font-weight: 400;
    }

    /* ── Botones ── */
    div[data-testid="stButton"] button {
        background: var(--accent) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important;
        transition: opacity 0.2s !important;
    }
    div[data-testid="stButton"] button:hover { opacity: 0.85 !important; }
    div[data-testid="stButton"] button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        color: #c8d0e0 !important;   /* era var(--muted) oscuro, ahora legible */
    }
    div[data-testid="stButton"] button[kind="secondary"]:hover {
        color: var(--text) !important;
        border-color: rgba(255,255,255,0.25) !important;
    }

    /* ── Separador ── */
    hr { border-color: var(--border) !important; margin: 0 !important; }
</style>
""", unsafe_allow_html=True)

from pages.dashboard import show_dashboard
from pages.prediccion import show_prediccion

# ── Navegación ───────────────────────────────────────────────────────────────
if "pagina" not in st.session_state:
    st.session_state.pagina = "Inicio"

pages = ["Inicio", "Dashboard", "Predicción"]
icons  = ["⌂", "◫", "⚡"]

col_brand, col_nav, _ = st.columns([2, 5, 1])
with col_brand:
    st.markdown(
        '<div style="font-family:\'Syne\',sans-serif;font-weight:800;font-size:1.2rem;'
        'color:#e8eaf0;padding:0.6rem 0;">📈 <span style="color:#4f8eff">Retail</span>Predict</div>',
        unsafe_allow_html=True
    )
with col_nav:
    nav_cols = st.columns(len(pages))
    for i, (page, icon) in enumerate(zip(pages, icons)):
        with nav_cols[i]:
            label = f"{icon} {page}" + (" 🆕" if page == "Predicción" else "")
            btn_type = "primary" if st.session_state.pagina == page else "secondary"
            if st.button(label, key=f"nav_{page}", type=btn_type, use_container_width=True):
                st.session_state.pagina = page
                st.rerun()

st.markdown("---")

# ── Páginas ──────────────────────────────────────────────────────────────────
pagina = st.session_state.pagina

if pagina == "Inicio":
    st.markdown("""
    <div class="hero-section">
        <div class="hero-tag">✦ Inteligencia Artificial · Retail</div>
        <div class="hero-title">Predicción inteligente<br><span class="gradient-text">para tu negocio</span></div>
        <div class="hero-subtitle">Analiza demanda, anticipa ventas y toma decisiones basadas en datos con modelos de IA en tiempo real.</div>
    </div>
    <div class="stats-row">
        <div class="stat-item"><div class="stat-value">94%</div><div class="stat-label">Precisión</div></div>
        <div class="stat-item"><div class="stat-value">+12</div><div class="stat-label">Indicadores</div></div>
        <div class="stat-item"><div class="stat-value">Real</div><div class="stat-label">Tiempo</div></div>
        <div class="stat-item"><div class="stat-value">5+</div><div class="stat-label">Modelos IA</div></div>
    </div>
    <div class="cards-grid">
        <div class="cap-card"><span class="cap-icon">📊</span><div class="cap-title">Análisis de Demanda</div><div class="cap-desc">Visualiza tendencias y patrones de consumo por producto y zona.</div></div>
        <div class="cap-card"><span class="cap-icon">🤖</span><div class="cap-title">Predicción de Ventas</div><div class="cap-desc">Modelos de ML entrenados con tu histórico para proyecciones precisas.</div></div>
        <div class="cap-card"><span class="cap-icon">🌦️</span><div class="cap-title">Impacto del Clima</div><div class="cap-desc">Correlaciona condiciones meteorológicas con comportamiento de compra.</div></div>
        <div class="cap-card"><span class="cap-icon">🏷️</span><div class="cap-title">Análisis Promocional</div><div class="cap-desc">Mide el ROI real de cada campaña y optimiza descuentos.</div></div>
        <div class="cap-card"><span class="cap-icon">⏰</span><div class="cap-title">Horas Pico</div><div class="cap-desc">Detecta automáticamente los momentos de mayor tráfico.</div></div>
        <div class="cap-card"><span class="cap-icon">🏪</span><div class="cap-title">Comparativa de Tiendas</div><div class="cap-desc">Benchmarking entre zonas y sucursales en un solo panel.</div></div>
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