# streamlit_styles.py - VERSIÓN COMPLETA SIN LOGOS
STREAMLIT_STYLES = """
<style>
/* Colores corporativos ALPAPEL SAS */
:root {
    --primary: #00B3B0;
    --primary-dark: #009690;
    --accent: #F57C00;
    --primary-border: #00C8C5;
    --dark-bg: #1B263B;
    --darker-bg: #0D1B2A;
    --text-light: #e2e8f0;
    --text-muted: #cbd5e1;
}

/* ELIMINAR COMPLETAMENTE EL HEADER NATIVO DE STREAMLIT */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* FORZAR EL CONTENIDO PRINCIPAL HACIA ARRIBA */
.stApp {
    background-color: var(--darker-bg);
    color: var(--text-light);
    padding-top: 0rem !important;
    margin-top: 0rem !important;
}

/* ELIMINAR CUALQUIER ESPACIO EN EL CONTENEDOR PRINCIPAL */
.stApp > div {
    padding-top: 0rem !important;
    margin-top: 0rem !important;
}

.stApp > div > div {
    padding-top: 0rem !important;
    margin-top: 0rem !important;
}

/* BANNER CORPORATIVO PEGADO AL BORDE SUPERIOR */
.compact-header {
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    padding: 0.5rem 1rem !important;
    border-radius: 0px 0px 8px 8px !important;
    color: white;
    margin: 0rem !important;
    border-bottom: 3px solid var(--primary-border);
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    width: 100%;
}

.header-title {
    font-size: 1.3rem !important;
    font-weight: bold;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.3 !important;
}

.header-subtitle {
    font-size: 0.9rem !important;
    margin: 0 !important;
    padding: 0 !important;
    opacity: 0.9;
    line-height: 1.2 !important;
}

/* ✅ SOLUCIÓN SIMPLE: Sidebar siempre accesible */
@media (max-width: 768px) {
    /* Forzar que Streamlit muestre el botón de sidebar */
    .css-1d391kg { 
        display: block !important; 
    }
    
    /* Sidebar más ancha en móvil */
    section[data-testid="stSidebar"] > div {
        width: 280px !important;
    }
    
    /* Header más compacto en móvil */
    .compact-header {
        padding: 0.3rem 0.5rem !important;
    }
    
    .header-title {
        font-size: 1.1rem !important;
    }
    
    .header-subtitle {
        font-size: 0.8rem !important;
    }
}

/* Instrucciones para usuario móvil */
.mobile-help {
    display: none;
    background: #ffeb3b;
    color: #333;
    padding: 10px;
    border-radius: 5px;
    margin: 10px 0;
    text-align: center;
    font-size: 14px;
}

@media (max-width: 768px) {
    .mobile-help {
        display: block;
    }
}

.user-panel-compact {
    background: rgba(255,255,255,0.1);
    padding: 0.4rem 0.8rem !important;
    border-radius: 6px;
    border: 1px solid rgba(255,255,255,0.2);
}

.user-name-compact {
    font-size: 0.9rem !important;
    font-weight: bold;
    margin: 0 !important;
    line-height: 1.3 !important;
}

.user-role-compact {
    font-size: 0.8rem !important;
    margin: 0 !important;
    opacity: 0.9;
    line-height: 1.2 !important;
}

/* SEPARADOR PEGADO AL BANNER */
hr {
    margin: 0.1rem 0 0.8rem 0 !important;
    border: none;
    border-top: 2px solid #415A77;
}

/* CONTENIDO PRINCIPAL SIN ESPACIOS SUPERIORES */
.main .block-container {
    padding-top: 0.8rem !important;
    padding-bottom: 1rem;
}

/* BOTONES CON LETRAS MÁS GRANDES */
.stButton button {
    background-color: var(--primary);
    color: white;
    border: 2px solid var(--primary-border);
    border-radius: 6px;
    padding: 0.4rem 1rem !important;
    font-weight: bold;
    font-size: 0.9rem !important;
    transition: all 0.3s ease;
    height: auto;
    min-height: 38px !important;
}

.stButton button:hover {
    background-color: var(--primary-dark);
    border-color: #00E0DC;
    transform: translateY(-1px);
}

/* Botones de acento (naranja) */
.stButton button[kind="primary"] {
    background-color: var(--accent);
    border-color: #FF9800;
}

.stButton button[kind="primary"]:hover {
    background-color: #E57100;
    border-color: #FFB74D;
}

/* TARJETAS Y CONTAINERS */
.metric-card {
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    padding: 1rem !important;
    border-radius: 8px;
    border: 1px solid var(--primary-border);
    color: white;
    text-align: center;
}

.dark-card {
    background-color: var(--dark-bg);
    border: 1px solid #415A77;
    border-radius: 8px;
    padding: 1rem !important;
}

/* TEXTOS MÁS GRANDES */
.section-title {
    color: var(--primary);
    font-size: 1.4rem !important;
    font-weight: bold;
    border-bottom: 2px solid #415A77;
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
}

/* INPUTS CON LETRAS MÁS GRANDES */
.stTextInput input, .stSelectbox select, .stTextArea textarea {
    background-color: var(--dark-bg);
    color: var(--text-light);
    border: 1px solid #778DA9;
    border-radius: 6px;
    padding: 0.5rem 0.7rem !important;
    font-size: 0.95rem !important;
}

.stTextInput input:focus, .stSelectbox select:focus, .stTextArea textarea:focus {
    border-color: var(--primary);
    background-color: var(--darker-bg);
    box-shadow: 0 0 0 2px rgba(0, 179, 176, 0.2);
}

/* DATAFRAMES */
.dataframe {
    background-color: var(--dark-bg);
    border: 1px solid #415A77;
    border-radius: 6px;
    font-size: 0.9rem !important;
}

/* MEJORAS PARA MÓVILES */
@media (max-width: 768px) {
    .header-title {
        font-size: 1.2rem !important;
    }
    
    .header-subtitle {
        font-size: 0.8rem !important;
    }
    
    .compact-header {
        padding: 0.4rem 0.8rem !important;
    }
}

/* SCROLLBAR */
::-webkit-scrollbar {
    width: 6px;
}

::-webkit-scrollbar-track {
    background: var(--darker-bg);
}

::-webkit-scrollbar-thumb {
    background: var(--primary);
    border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--primary-dark);
}

/* AJUSTES FINALES PARA PEGAR TODO ARRIBA */
[data-testid="stAppViewContainer"] {
    padding-top: 0rem !important;
}

/* ELIMINAR CUALQUIER ELEMENTO QUE GENERE ESPACIO */
div[data-testid="stToolbar"] {
    display: none !important;
}

.stApp > div > div > div > div > section {
    padding-top: 0rem !important;
}

/* ESTILOS PARA FORMULARIOS DE LOGIN */
.login-container {
    background: var(--dark-bg);
    border: 1px solid #415A77;
    border-radius: 10px;
    padding: 2rem;
    margin: 2rem auto;
    max-width: 500px;
}

/* ESTILOS PARA TABLAS */
.stDataFrame {
    border: 1px solid #415A77;
    border-radius: 8px;
}

/* ESTILOS PARA METRICAS */
[data-testid="stMetric"] {
    background-color: var(--dark-bg);
    border: 1px solid #415A77;
    border-radius: 8px;
    padding: 1rem;
}

/* ESTILOS PARA SIDEBAR */
.css-1d391kg {
    background-color: var(--darker-bg);
}

section[data-testid="stSidebar"] {
    background-color: var(--darker-bg);
    border-right: 1px solid #415A77;
}

/* ESTILOS PARA TABS */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
}

.stTabs [data-baseweb="tab"] {
    background-color: var(--dark-bg);
    border-radius: 4px 4px 0px 0px;
    padding: 0.5rem 1rem;
}

.stTabs [aria-selected="true"] {
    background-color: var(--primary);
}

/* ESTILOS PARA EXPANDER */
.streamlit-expanderHeader {
    background-color: var(--dark-bg);
    border: 1px solid #415A77;
}

/* ESTILOS PARA MENSAJES DE ALERTA */
.stAlert {
    border-radius: 8px;
    border: 1px solid;
}

/* ESTILOS PARA PROGRESS BAR */
.stProgress > div > div > div > div {
    background-color: var(--primary);
}

/* ESTILOS PARA RADIO BUTTONS */
.stRadio > div {
    flex-direction: row;
    gap: 1rem;
}

.stRadio [data-testid="stMarkdownContainer"] {
    color: var(--text-light);
}

/* ESTILOS PARA CHECKBOX */
.stCheckbox [data-testid="stMarkdownContainer"] {
    color: var(--text-light);
}

/* ESTILOS PARA SELECTBOX */
.stSelectbox [data-testid="stMarkdownContainer"] {
    color: var(--text-light);
}

/* ESTILOS PARA MULTISELECT */
.stMultiSelect [data-testid="stMarkdownContainer"] {
    color: var(--text-light);
}

/* ESTILOS PARA DATE INPUT */
.stDateInput [data-testid="stMarkdownContainer"] {
    color: var(--text-light);
}

/* ESTILOS PARA TIME INPUT */
.stTimeInput [data-testid="stMarkdownContainer"] {
    color: var(--text-light);
}

/* ESTILOS PARA NUMBER INPUT */
.stNumberInput [data-testid="stMarkdownContainer"] {
    color: var(--text-light);
}

/* ESTILOS PARA TEXT AREA */
.stTextArea [data-testid="stMarkdownContainer"] {
    color: var(--text-light);
}

/* ESTILOS PARA FILE UPLOADER */
.stFileUploader [data-testid="stMarkdownContainer"] {
    color: var(--text-light);
}

/* ESTILOS PARA COLOR PICKER */
.stColorPicker [data-testid="stMarkdownContainer"] {
    color: var(--text-light);
}

/* ESTILOS PARA ECHART */
.echart {
    background-color: var(--dark-bg);
    border-radius: 8px;
    padding: 1rem;
}

/* ESTILOS PARA PLOTLY */
.js-plotly-plot {
    background-color: var(--dark-bg);
    border-radius: 8px;
}

/* ESTILOS PARA DECKGL */
.deckgl-wrapper {
    background-color: var(--dark-bg);
    border-radius: 8px;
}

/* ESTILOS PARA MAPA */
.mapboxgl-canvas {
    border-radius: 8px;
}

/* ESTILOS PARA VEGA-LITE */
.vega-embed {
    background-color: var(--dark-bg);
    border-radius: 8px;
    padding: 1rem;
}

/* ESTILOS PARA GRAPHVIZ */
.graphviz {
    background-color: var(--dark-bg);
    border-radius: 8px;
    padding: 1rem;
}

/* ESTILOS PARA ALTAR */
.vega-embed {
    background-color: var(--dark-bg);
}

/* ESTILOS PARA BOKEH */
.bk-root {
    background-color: var(--dark-bg);
    border-radius: 8px;
    padding: 1rem;
}

/* ESTILOS PARA PYPLOT */
.matplotlib {
    background-color: var(--dark-bg);
    border-radius: 8px;
    padding: 1rem;
}

/* ESTILOS PARA IMAGENES */
.stImage {
    border-radius: 8px;
    overflow: hidden;
}

/* ESTILOS PARA VIDEO */
.stVideo {
    border-radius: 8px;
    overflow: hidden;
}

/* ESTILOS PARA AUDIO */
.stAudio {
    border-radius: 8px;
    overflow: hidden;
}

/* ESTILOS PARA JSON */
.stJson {
    background-color: var(--dark-bg);
    border-radius: 8px;
    padding: 1rem;
}

/* ESTILOS PARA CODE */
.stCode {
    background-color: var(--dark-bg);
    border-radius: 8px;
    padding: 1rem;
}

/* ESTILOS PARA MARKDOWN */
.stMarkdown {
    color: var(--text-light);
}

/* ESTILOS PARA LATEX */
.stLatex {
    color: var(--text-light);
}

/* ESTILOS PARA INFO */
.stInfo {
    background-color: rgba(59, 130, 246, 0.1);
    border: 1px solid #3b82f6;
}

/* ESTILOS PARA SUCCESS */
.stSuccess {
    background-color: rgba(16, 185, 129, 0.1);
    border: 1px solid #10b981;
}

/* ESTILOS PARA WARNING */
.stWarning {
    background-color: rgba(245, 158, 11, 0.1);
    border: 1px solid #f59e0b;
}

/* ESTILOS PARA ERROR */
.stError {
    background-color: rgba(220, 38, 38, 0.1);
    border: 1px solid #dc2626;
}

/* ESTILOS PARA EXCEPTION */
.stException {
    background-color: rgba(220, 38, 38, 0.1);
    border: 1px solid #dc2626;
}

/* ESTILOS PARA BALLOONS */
.stBalloons {
    opacity: 0.8;
}

/* ESTILOS PARA SNOW */
.stSnow {
    opacity: 0.8;
}

/* ESTILOS PARA CONFETTI */
.stConfetti {
    opacity: 0.8;
}

/* ESTILOS PARA EMOJI */
.stEmoji {
    font-size: 1.2em;
}

/* ESTILOS PARA ICONOS */
.stIcon {
    font-size: 1.2em;
}
/* ✅ FIJAR SIDEBAR - NO SE PUEDE OCULTAR */
section[data-testid="stSidebar"] {
    visibility: visible !important;
    transform: translateX(0) !important;
}

/* OCULTAR BOTÓN DE OCULTAR SIDEBAR */
button[title="Hide sidebar"] {
    display: none !important;
}

/* EN MÓVIL: SIDEBAR SIEMPRE ACCESIBLE */
@media (max-width: 768px) {
    section[data-testid="stSidebar"] > div {
        width: 280px !important;
    }
    
    /* FORZAR BOTÓN TOGGLE VISIBLE */
    .css-1d391kg {
        display: block !important;
        z-index: 1000000 !important;
    }
}

/* ✅ ELIMINAR COMPLETAMENTE LA LÓGICA DE OCULTAR SIDEBAR */
[data-testid="stSidebar"] {
    /* Forzar visibilidad total */
    transform: translateX(0px) !important;
    visibility: visible !important;
    opacity: 1 !important;
    display: block !important;
    width: 16rem !important;
    min-width: 16rem !important;
    max-width: 16rem !important;
}

/* ✅ ELIMINAR BOTÓN DE OCULTAR */
button[data-testid="baseButton-header"] {
    display: none !important;
}

button[kind="header"] {
    display: none !important;
}

/* ✅ ELIMINAR COLLAPSE STATE */
[data-testid="stSidebar"][aria-expanded="false"] {
    transform: translateX(0px) !important;
    visibility: visible !important;
}

/* ✅ EN MÓVIL: BOTÓN HAMBURGUESA SIEMPRE VISIBLE */
.css-1d391kg {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 999999 !important;
}

/* ✅ ELIMINAR CUALQUIER HOVER QUE OCULTE */
[data-testid="stSidebar"]:hover {
    transform: translateX(0px) !important;
}
</style>

<script>
// ✅ FORZAR SIDEBAR SIEMPRE VISIBLE
function forceSidebarVisible() {
    // Sidebar siempre visible
    const sidebar = document.querySelector('section[data-testid="stSidebar"]');
    if (sidebar) {
        sidebar.style.visibility = 'visible';
        sidebar.style.transform = 'translateX(0)';
    }
    
    // Eliminar botón de ocultar
    const hideBtn = document.querySelector('button[title="Hide sidebar"]');
    if (hideBtn) hideBtn.style.display = 'none';
}

// Ejecutar cada 500ms para combatir Streamlit
setInterval(forceSidebarVisible, 500);
forceSidebarVisible();
</script>
"""