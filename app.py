# app.py - VERSIÓN CORREGIDA CON FORM KEYS ÚNICOS
import streamlit as st
import pandas as pd
import time
from datetime import datetime
import os
import traceback
from datetime import datetime, timedelta
from streamlit_styles import STREAMLIT_STYLES
import warnings
from gestion_module import gestion_section
from analisis_cartera_module import analisis_cartera_section
from admin_module import admin_section
from PIL import Image
import base64

warnings.filterwarnings('ignore', category=UserWarning)

# Importar tus módulos existentes
from database import DatabaseManager
from user_manager import UserManager
from auth import AuthManager
from config import config

def set_custom_page_config():
    """Configuración personalizada de la página sin logos"""
    try:
        st.set_page_config(
            page_title=config.APP_NAME,
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    except Exception as e:
        st.set_page_config(
            page_title=config.APP_NAME,
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )

def main():
    try:
        set_custom_page_config()
        init_session_state()
        
        # Aplicar estilos corporativos
        st.markdown(STREAMLIT_STYLES, unsafe_allow_html=True)
        
        if st.session_state.user is None:
            login_section()
        else:
            main_app()
    except Exception as e:
        st.error("""
        ⚠️ **Error en la aplicación**
        
        Por favor recarga la página. Si el problema persiste, contacta al administrador.
        """)
        st.stop()

def init_session_state():
    """Inicializar el estado de la sesión con persistencia - VERSIÓN DEBUG"""
    print("=" * 50)
    print("🔍 DEBUG: init_session_state() INICIADO")
    
    # 1. Inicializar managers básicos
    if 'db' not in st.session_state:
        st.session_state.db = DatabaseManager()
        print("✅ DatabaseManager inicializado")
    
    if 'user_manager' not in st.session_state:
        st.session_state.user_manager = UserManager(st.session_state.db.db_path)
        print("✅ UserManager inicializado")
    
    if 'auth_manager' not in st.session_state:
        st.session_state.auth_manager = AuthManager(st.session_state.user_manager)
        print("✅ AuthManager inicializado")
    
    # 2. INTENTAR CARGAR SESIÓN PERSISTENTE
    print("🔍 Buscando sesión persistente...")
    try:
        from session_utils import session_manager
        saved_user = session_manager.load_session()
        
        if saved_user:
            print(f"✅ SESIÓN PERSISTENTE ENCONTRADA: {saved_user.get('email')}")
            st.session_state.user = saved_user
            st.session_state.db.set_current_user(saved_user)
            st.session_state.auth_manager.current_user = saved_user
            st.session_state.auth_manager.is_authenticated = True
            st.session_state.auth_manager.session_start = time.time()
        else:
            st.session_state.user = None
            print("🔍 No hay usuario en sesión persistente")
            
    except Exception as e:
        print(f"❌ ERROR en carga de sesión: {e}")
        st.session_state.user = None
    
    # 3. Inicializar el resto del estado
    defaults = {
        'section': "🏠 Dashboard",
        'cliente_para_gestion': None,
        'ir_a_gestion': False,
        'carga_en_progreso': False,
        'archivo_cargado': False,
        'mensaje_carga': "",
        'archivo_data': None,
        'archivo_nombre': "",
        'datos_actualizados': False,
        'ultima_actualizacion': None,
        'mostrar_uploader': False,
        'cliente_seleccionado': None,
        'datos_cliente_completos': None
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
            print(f"✅ {key} inicializado: {default_value}")
    
    # 4. Estado final
    if st.session_state.user:
        print(f"🎯 ESTADO FINAL: Usuario AUTENTICADO - {st.session_state.user.get('email')}")
    else:
        print("🎯 ESTADO FINAL: Usuario NO autenticado - Mostrar login")
    
    print("=" * 50)

    # Inicializar sección por defecto
    if 'section' not in st.session_state:
        st.session_state.section = "🏠 Dashboard"

    # Estado para gestión de clientes
    if 'cliente_para_gestion' not in st.session_state:
        st.session_state.cliente_para_gestion = None
    if 'ir_a_gestion' not in st.session_state:
        st.session_state.ir_a_gestion = False
    
    # Estado para carga de archivos
    if 'carga_en_progreso' not in st.session_state:
        st.session_state.carga_en_progreso = False
    if 'archivo_cargado' not in st.session_state:
        st.session_state.archivo_cargado = False
    if 'mensaje_carga' not in st.session_state:
        st.session_state.mensaje_carga = ""
    if 'archivo_data' not in st.session_state:
        st.session_state.archivo_data = None
    if 'archivo_nombre' not in st.session_state:
        st.session_state.archivo_nombre = ""
    
    # Estado para actualización de datos
    if 'datos_actualizados' not in st.session_state:
        st.session_state.datos_actualizados = False
    if 'ultima_actualizacion' not in st.session_state:
        st.session_state.ultima_actualizacion = None

    # Estado para UI
    if 'mostrar_uploader' not in st.session_state:
        st.session_state.mostrar_uploader = False
    if 'cliente_seleccionado' not in st.session_state:
        st.session_state.cliente_seleccionado = None
    if 'datos_cliente_completos' not in st.session_state:
        st.session_state.datos_cliente_completos = None

    # Debug final
    if st.session_state.user:
        print(f"🔍 DEBUG INIT: Sesión iniciada para {st.session_state.user['email']}")
    else:
        print("🔍 DEBUG INIT: Sesión NO iniciada - Mostrar login")

def login_section():
    """Sección de login para Streamlit - VERSIÓN SIN LOGOS"""
    
    # Usar columnas para centrar el login
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Header principal único y compacto SIN LOGOS
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="margin:0; color:#00B3B0; font-size:28px; font-weight:bold;">🔐 {config.APP_NAME}</h1>
            <p style="margin:0; color:#e6f7f7; font-size:16px; margin-top:5px;">ALPAPEL SAS</p>
        </div>
        """, unsafe_allow_html=True)
        
        # ✅ FIX: Crear el formulario SIN key dinámico (esto causa problemas)
        with st.form("login_form", clear_on_submit=True):
            st.markdown("### Iniciar Sesión")
            
            email = st.text_input("📧 Email", placeholder="usuario@alpapel.com", key="login_email")
            password = st.text_input("🔒 Contraseña", type="password", placeholder="Ingresa tu contraseña", key="login_password")
            
            # Botón de login centrado
            login_button = st.form_submit_button("🚀 Ingresar al Sistema", use_container_width=True, type="primary")
            
            if login_button:
                if email and password:
                    allowed_domains = ['@alpapel.com', '@gmail.com', '@hotmail.com']
                    if not any(email.endswith(domain) for domain in allowed_domains):
                        st.error("❌ Dominio de email no permitido")
                    else:
                        with st.spinner("🔐 Autenticando..."):
                            # ✅ REDUCIR tiempo de espera
                            time.sleep(0.5)
                            success, message, user_data = st.session_state.user_manager.autenticar_usuario(
                                email, password, "web_app", "Streamlit_CRM"
                            )
                            
                            if success:
                                st.session_state.user = user_data
                                st.session_state.db.set_current_user(user_data)
                                st.session_state.auth_manager.current_user = user_data
                                st.session_state.auth_manager.is_authenticated = True
                                st.session_state.auth_manager.session_start = time.time()
                                
                                # ✅ GUARDAR SESIÓN PERSISTENTE
                                from session_utils import session_manager
                                session_manager.save_session(user_data)
                                
                                st.success(f"✅ ¡Bienvenid@ {user_data['nombre_completo']}!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                else:
                    st.warning("⚠️ Por favor ingresa email y contraseña")
        
        # Enlaces de ayuda
        st.markdown("---")
        col_help1, col_help2 = st.columns(2)
        with col_help1:
            if st.button("¿Olvidaste contraseña?", use_container_width=True, key="btn_forgot_pass"):
                st.info("📞 Contacta al administrador: cartera@alpapel.com")
        with col_help2:
            if st.button("Ayuda", use_container_width=True, key="btn_help_support"):
                st.info("""
                **Soporte Técnico - ALPAPEL SAS**
                
                📧 Email: cartera@alpapel.com
                ⏰ Horario: L-V 8:00 AM - 5:00 PM
                """)

def main_app():
    """Aplicación principal una vez autenticado - SIN LOGOS"""
    
    # ✅ VERIFICAR SI DEBEMOS NAVEGAR A GESTIÓN AUTOMÁTICAMENTE
    if st.session_state.get('ir_a_gestion', False) and st.session_state.get('cliente_para_gestion'):
        st.session_state.section = "📞 Gestión"
        st.session_state.ir_a_gestion = False
        st.rerun()
    
    # Header superior SIN LOGOS
    st.markdown(
        """
        <style>
        .compact-header {
            background: linear-gradient(135deg, #00B3B0, #009690);
            padding: 0.5rem 1rem;
            border-radius: 0px 0px 10px 10px;
            color: white;
            margin-bottom: 0.5rem;
            border-bottom: 3px solid #00C8C5;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .header-content {
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
        }
        .header-text {
            flex: 1;
            text-align: center;
        }
        .header-title {
            font-size: 1.4rem;
            font-weight: bold;
            margin: 0;
            padding: 0;
        }
        .header-subtitle {
            font-size: 0.9rem;
            margin: 0;
            padding: 0;
            opacity: 0.9;
        }
        .user-panel-compact {
            background: rgba(255,255,255,0.1);
            padding: 0.4rem 0.8rem;
            border-radius: 6px;
            border: 1px solid rgba(255,255,255,0.2);
            margin: 0 15px;
        }
        .user-name-compact {
            font-size: 0.85rem;
            font-weight: bold;
            margin: 0;
            line-height: 1.2;
        }
        .user-role-compact {
            font-size: 0.75rem;
            margin: 0;
            opacity: 0.9;
            line-height: 1.2;
        }
        
        /* ✅ NUEVO: Estilos para móvil */
        .mobile-menu-help {
            display: none;
            background: #ffeb3b;
            color: #333;
            padding: 8px 12px;
            border-radius: 5px;
            margin: 5px 0;
            text-align: center;
            font-size: 12px;
            border-left: 4px solid #00B3B0;
        }
        
        @media (max-width: 768px) {
            .mobile-menu-help {
                display: block;
            }
            
            .compact-header {
                padding: 0.3rem 0.8rem;
            }
            
            .header-title {
                font-size: 1.1rem;
            }
            
            .header-subtitle {
                font-size: 0.75rem;
            }
            
            .user-name-compact {
                font-size: 0.75rem;
            }
            
            .user-role-compact {
                font-size: 0.65rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Header compacto SIN LOGO
    st.markdown(
        f"""
        <div class="compact-header">
            <div class="header-content">
                <div class="header-text">
                    <div class="header-title">{config.APP_NAME}</div>
                    <div class="header-subtitle">ALPAPEL SAS</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # ✅ NUEVO: Ayuda para móvil
    st.markdown(
        """
        <div class="mobile-menu-help">
        📱 <strong>Para ver el menú:</strong> Toca el ícono ☰ en la esquina superior derecha
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Segunda fila: Información de usuario y logout
    col_user, col_logout = st.columns([4, 1])
    
    with col_user:
        user_role = config.ROLES.get(st.session_state.user['rol'], 'Usuario')
        st.markdown(
            f"""
            <div style="text-align: left; padding: 0.3rem;">
                <div class="user-name-compact">👤 {st.session_state.user['nombre_completo']}</div>
                <div class="user-role-compact">🎭 {user_role} | ⏰ Sesión: {st.session_state.auth_manager.get_session_time_remaining()} min</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col_logout:
        if st.button("🔒 Cerrar Sesión", use_container_width=True, type="primary", key="logout_btn"):
            # ✅ Limpiar sesión persistente
            from session_utils import session_manager
            session_manager.clear_session()
            
            st.session_state.user = None
            st.session_state.auth_manager.logout()
            st.success("✅ Sesión cerrada correctamente")
            time.sleep(0.5)
            st.rerun()
    
    st.markdown("---")
    
    # Sidebar con navegación
    with st.sidebar:
        st.header("🧭 Navegación")
        
        # Definir secciones disponibles según permisos
        sections = {
            "🏠 Dashboard": "dashboard",
            "📁 Cartera": "cartera", 
            "📞 Gestión": "gestion",
            "📊 Análisis Cartera": "analisis_cartera",
            "📈 Análisis Gestión": "analisis_gestion",
        }
        
        # ✅ Solo mostrar Admin si tiene permisos
        if st.session_state.auth_manager.has_permission('manage_users'):
            sections["🛡️ Admin"] = "admin"
        
        # Selector de sección
        selected_section = st.radio(
            "Selecciona una sección:",
            options=list(sections.keys()),
            index=list(sections.keys()).index(st.session_state.section) if st.session_state.section in sections else 0,
            key="nav_radio"
        )
        
        st.session_state.section = selected_section
        
        # Información de sesión
        st.markdown("---")
        st.markdown("**💼 Información de Sesión**")
        tiempo_restante = st.session_state.auth_manager.get_session_time_remaining()
        st.write(f"⏰ Tiempo restante: {tiempo_restante} min")
        
        # ✅ NUEVO: Información de sesión persistente
        try:
            from session_utils import session_manager
            tiempo_persistente = session_manager.get_remaining_time()
            st.write(f"💾 Sesión persistente: {tiempo_persistente} min")
        except:
            pass
        
        if st.session_state.user.get('vendedor_asignado'):
            st.write(f"👤 Vendedor: {st.session_state.user['vendedor_asignado']}")
        
        st.markdown("---")
        st.markdown("**👨‍💻 Desarrollado por**")
        st.markdown("Edwin Franco (EF)")
        st.markdown("---")
        
        # Botón de actualizar datos
        if st.button("🔄 Actualizar Datos", use_container_width=True, key="btn_actualizar_datos"):
            with st.spinner("Actualizando datos..."):
                load_initial_data()
                st.success("✅ Datos actualizados")
    
    # Ejecutar sección seleccionada
    section_handlers = {
        "🏠 Dashboard": dashboard_section,
        "📁 Cartera": cartera_section,
        "📞 Gestión": gestion_section,
        "📊 Análisis Cartera": analisis_cartera_section,
        "📈 Análisis Gestión": analisis_gestion_section,
    }
    
    # ✅ Agregar admin si tiene permisos
    if st.session_state.auth_manager.has_permission('manage_users'):
        section_handlers["🛡️ Admin"] = admin_section
    
    if selected_section in section_handlers:
        section_handlers[selected_section]()

def load_initial_data():
    """Cargar datos iniciales para la aplicación"""
    try:
        # Forzar actualización de datos
        st.session_state.datos_actualizados = True
        st.session_state.ultima_actualizacion = datetime.now()
        
        # ✅ Asegurar que DatabaseManager tiene el usuario actual
        if st.session_state.user:
            st.session_state.db.set_current_user(st.session_state.user)
        
        # Debug: Verificar usuario actual
        print(f"🔍 DEBUG - Usuario actual: {st.session_state.user}")
        print(f"🔍 DEBUG - Rol: {st.session_state.user['rol']}")
        
        # ✅ Debug adicional: Verificar datos de cartera
        cartera = st.session_state.db.obtener_cartera_actual()
        print(f"🔍 DEBUG - Cartera obtenida: {len(cartera)} registros")
        
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
    
def dashboard_section():
    """Sección del Dashboard - VERSIÓN LIMPIA Y FUNCIONAL"""
    st.header("📊 Dashboard Principal")
    
    try:
        # Obtener métricas
        with st.spinner("Cargando métricas..."):
            metricas = st.session_state.db.obtener_metricas_principales()
        
        # Mostrar métricas en cards
        st.subheader("📊 Métricas Principales")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "CARTERA TOTAL", 
                f"${metricas['cartera_total']:,.0f}",
                help="Valor total de la cartera"
            )
        
        with col2:
            st.metric(
                "CARTERA EN MORA", 
                f"${metricas['cartera_mora']:,.0f}",
                help="Valor de cartera con días vencidos > 0"
            )
        
        with col3:
            st.metric(
                "TOTAL CLIENTES", 
                f"{metricas['total_clientes']:,}",
                help="Número total de clientes únicos"
            )
        
        with col4:
            st.metric(
                "CLIENTES EN MORA", 
                f"{metricas['clientes_mora']:,}",
                help="Clientes con cartera vencida"
            )
        
        st.markdown("---")
        
        # Gráficas
        try:
            from graficas import crear_grafica_distribucion_estado, crear_grafica_top_clientes, crear_grafica_evolucion_mensual
            
            # Obtener datos para gráficas
            datos_graficas = st.session_state.db.obtener_datos_graficas()
            
            # Gráfica 1: Distribución por Estado
            st.subheader("📊 Distribución de Cartera por Estado")
            fig1 = crear_grafica_distribucion_estado(datos_graficas)
            if fig1:
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No hay datos suficientes para mostrar la distribución de cartera por estado")
            
            # Gráfica 2: Top Clientes con Mora
            st.subheader("⚠️ Top 10 Clientes con Mayor Mora")
            fig2 = crear_grafica_top_clientes(datos_graficas)
            if fig2:
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No hay clientes con mora para mostrar")
            
            # Gráfica 3: Evolución Mensual
            st.subheader("📈 Evolución Mensual de Cartera")
            fig3 = crear_grafica_evolucion_mensual(datos_graficas)
            if fig3:
                st.plotly_chart(fig3, use_container_width=True)
            else:
                # Crear gráfica directa desde cartera actual como alternativa
                cartera_actual = st.session_state.db.obtener_cartera_actual()
                if not cartera_actual.empty:
                    fig_alternativa = crear_grafica_directa_evolucion(cartera_actual)
                    if fig_alternativa:
                        st.plotly_chart(fig_alternativa, use_container_width=True)
                else:
                    st.info("No hay datos disponibles para mostrar evolución mensual")
                
        except Exception as e:
            st.error(f"Error cargando gráficas: {e}")
        
    except Exception as e:
        st.error(f"Error en el dashboard: {e}")

def crear_grafica_directa_evolucion(cartera_df):
    """Crea gráfica de evolución directamente desde los datos de cartera actual"""
    try:
        import plotly.express as px
        import pandas as pd
        from datetime import datetime, timedelta
        
        if cartera_df.empty:
            return None
        
        # Convertir fechas
        cartera_df['fecha_vencimiento'] = pd.to_datetime(cartera_df['fecha_vencimiento'])
        
        # Filtrar últimos 12 meses
        fecha_limite = datetime.now() - timedelta(days=365)
        cartera_filtrada = cartera_df[cartera_df['fecha_vencimiento'] >= fecha_limite]
        
        if cartera_filtrada.empty:
            return None
        
        # Agrupar por mes
        cartera_filtrada['mes'] = cartera_filtrada['fecha_vencimiento'].dt.strftime('%m/%y')
        cartera_por_mes = cartera_filtrada.groupby('mes').agg({
            'total_cop': 'sum',
            'nro_factura': 'count',
            'nit_cliente': 'nunique'
        }).reset_index()
        
        # Ordenar por mes
        meses_orden = sorted(cartera_por_mes['mes'].unique(),   
                           key=lambda x: datetime.strptime(x, '%m/%y'))
        cartera_por_mes = cartera_por_mes.set_index('mes').loc[meses_orden].reset_index()
        
        # Convertir a millones
        cartera_por_mes['total_millones'] = cartera_por_mes['total_cop'] / 1000000
        
        # Crear gráfica
        fig = px.bar(
            cartera_por_mes,
            x='mes',
            y='total_millones',
            title="Cartera por Mes de Vencimiento (Último Año)",
            labels={
                'total_millones': 'Valor (Millones COP)',
                'mes': 'Mes de Vencimiento',
                'nro_factura': 'N° Facturas'
            },
            text='total_millones'
        )
        
        # Actualizar diseño
        fig.update_traces(
            texttemplate='$%{y:.1f}M<br>%{customdata[0]} facturas',
            textposition='outside',
            customdata=cartera_por_mes[['nro_factura']].values,
            marker_color='#00B3B0'
        )
        
        fig.update_layout(
            plot_bgcolor='#1e293b',
            paper_bgcolor='#1e293b',
            font_color='#e2e8f0',
            height=500,
            showlegend=False
        )
        
        fig.update_yaxes(
            title='Millones de COP',
            tickprefix='$',
            tickformat='.1f'
        )
        fig.update_xaxes(title='Mes de Vencimiento')
        
        return fig
        
    except Exception as e:
        print(f"Error creando gráfica directa: {e}")
        return None

def cartera_section():
    """Sección de Cartera - VERSIÓN MEJORADA CON DATOS DE CLIENTE"""
    st.header("📁 Cartera y Gestión de Clientes")
    
    # INICIALIZAR ESTADO PARA CLIENTE SELECCIONADO
    if 'cliente_seleccionado' not in st.session_state:
        st.session_state.cliente_seleccionado = None
        st.session_state.datos_cliente_completos = None
    
    # Primero procesar cualquier carga pendiente
    procesar_carga_excel()
    
    try:
        # MÉTRICAS RÁPIDAS DE CARTERA
        st.subheader("📊 Métricas Rápidas de Cartera")
        
        # Obtener datos iniciales
        cartera_completa = st.session_state.db.obtener_cartera_actual()
        
        # Mostrar métricas en tiempo real
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_cartera = cartera_completa['total_cop'].sum() if not cartera_completa.empty else 0
            st.metric(
                "CARTERA TOTAL", 
                f"${total_cartera:,.0f}",
                delta=None
            )
        
        with col2:
            cartera_mora = cartera_completa[cartera_completa['dias_vencidos'] > 0]['total_cop'].sum() if not cartera_completa.empty else 0
            st.metric(
                "CARTERA EN MORA", 
                f"${cartera_mora:,.0f}",
                delta=None
            )
        
        with col3:
            total_clientes = cartera_completa['nit_cliente'].nunique() if not cartera_completa.empty else 0
            st.metric("TOTAL CLIENTES", f"{total_clientes:,}")
        
        with col4:
            clientes_mora = cartera_completa[cartera_completa['dias_vencidos'] > 0]['nit_cliente'].nunique() if not cartera_completa.empty else 0
            st.metric("CLIENTES EN MORA", f"{clientes_mora:,}")
        
        st.markdown("---")
        
        # FILTROS DE BÚSQUEDA
        st.subheader("🔍 Filtros de Búsqueda")
        
        # Fila 1: Búsqueda textual
        col_search1, col_search2, col_search3 = st.columns([1, 3, 1])
        with col_search1:
            st.write("🔍 Buscar:")
        with col_search2:
            texto_busqueda = st.text_input(
                "Buscar por NIT, Razón Social, Factura...",
                placeholder="Ingresa texto para buscar...",
                label_visibility="collapsed",
                key="buscar_cartera_input"
            )
        with col_search3:
            if st.button("🧹 Limpiar", use_container_width=True, key="btn_limpiar_filtros"):
                st.rerun()
        
        # Fila 2: Filtros dropdown
        col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
        
        with col_filtro1:
            vendedores_disponibles = st.session_state.auth_manager.get_available_vendedores()
            filtro_vendedor = st.selectbox(
                "👤 Vendedor:",
                options=vendedores_disponibles,
                key="filtro_vendedor_cartera"
            )
        
        with col_filtro2:
            ciudades_df = st.session_state.db.obtener_ciudades()
            ciudades = ["Todas las ciudades"] + ciudades_df['ciudad'].dropna().unique().tolist()
            filtro_ciudad = st.selectbox(
                "🏙️ Ciudad:", 
                options=ciudades,
                key="filtro_ciudad_cartera"
            )
        
        with col_filtro3:
            filtro_dias = st.selectbox(
                "⏰ Días de mora:",
                options=[
                    "Todos los días",
                    "0 días (Corriente)",
                    "1-30 días",
                    "31-60 días", 
                    "61-90 días",
                    "+90 días"
                ],
                key="filtro_dias_cartera"
            )
        
        # BOTONES DE ACCIÓN
        st.markdown("---")
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        
        with col_btn1:
            # Botón para cargar Excel
            if st.button("📤 Cargar Excel", use_container_width=True, type="primary", key="btn_cargar_excel"):
                st.session_state.mostrar_uploader = True
        
        with col_btn2:
            if st.button("🔄 Actualizar Vista", use_container_width=True, key="btn_actualizar_vista"):
                st.rerun()
        
        with col_btn3:
            if st.session_state.datos_actualizados and st.session_state.ultima_actualizacion:
                st.info(f"📊 Datos actualizados: {st.session_state.ultima_actualizacion.strftime('%H:%M:%S')}")
        
        # Mostrar uploader si está activado
        if st.session_state.get('mostrar_uploader', False):
            cargar_excel_cartera_streamlit()
        
        # Cargar datos filtrados
        with st.spinner("Aplicando filtros..."):
            cartera_filtrada = cargar_datos_cartera_filtrados(texto_busqueda, filtro_vendedor, filtro_ciudad, filtro_dias)
            
        if st.session_state.cliente_seleccionado:
            mostrar_panel_cliente_detallado()
        else:
            # VISTA COMPLETA DE DATOS (COMO EXCEL) - EXISTENTE
            st.subheader("📋 Vista Completa de Cartera")
            
            if not cartera_filtrada.empty:
                # Mostrar información del dataset
                st.info(f"📊 Mostrando {len(cartera_filtrada)} registros filtrados")
                
                # Mostrar tabla completa CON SELECCIÓN DE CLIENTE
                mostrar_tabla_cartera_con_seleccion(cartera_filtrada)
            else:
                st.warning("No hay datos para mostrar con los filtros actuales")
                
    except Exception as e:
        st.error(f"❌ Error en la sección de cartera: {e}")

def mostrar_tabla_cartera_con_seleccion(cartera_df):
    """Muestra la tabla de cartera con capacidad de seleccionar cliente"""
    
    # Crear una copia para no modificar el original
    display_df = cartera_df.copy()
    
    # Formatear columnas numéricas
    if 'total_cop' in display_df.columns:
        display_df['total_cop'] = display_df['total_cop'].apply(lambda x: f"${x:,.0f}")
    
    if 'dias_vencidos' in display_df.columns:
        display_df['dias_vencidos'] = display_df['dias_vencidos'].astype(int)
    
    # NUEVO: Agregar columna de selección
    display_df['seleccionar'] = "👆 Seleccionar"
    
    # Mostrar todas las columnas disponibles + selección
    columnas_mostrar = ['seleccionar'] + [col for col in display_df.columns if col != 'seleccionar']
    
    st.dataframe(
        display_df[columnas_mostrar],
        use_container_width=True,
        height=400,
        hide_index=True
    )
    
    # NUEVO: Selección de cliente
    st.subheader("👤 Seleccionar Cliente para Ver Detalles")
    
    col_sel1, col_sel2 = st.columns([3, 1])
    
    with col_sel1:
        # Crear lista de clientes únicos para selección
        clientes_unicos = cartera_df[['nit_cliente', 'razon_social_cliente']].drop_duplicates()
        opciones_clientes = ["--- Selecciona un cliente ---"] + [
            f"{row['nit_cliente']} - {row['razon_social_cliente']}" 
            for _, row in clientes_unicos.iterrows()
        ]
        
        cliente_seleccionado = st.selectbox(
            "Selecciona un cliente para ver detalles completos:",
            options=opciones_clientes,
            key="selector_cliente_detalle"
        )
    
    with col_sel2:
        if st.button("📋 Ver Detalles", use_container_width=True, key="btn_ver_detalles") and cliente_seleccionado != "--- Selecciona un cliente ---":
            # Extraer NIT del cliente seleccionado
            nit_cliente = cliente_seleccionado.split(" - ")[0]
            seleccionar_cliente_para_detalles(nit_cliente)

def seleccionar_cliente_para_detalles(nit_cliente):
    """Selecciona un cliente y carga sus datos completos"""
    try:
        with st.spinner("Cargando información del cliente..."):
            datos_completos = st.session_state.db.obtener_datos_completos_cliente(nit_cliente)
            
            if datos_completos['cliente'] is not None:
                st.session_state.cliente_seleccionado = nit_cliente
                st.session_state.datos_cliente_completos = datos_completos
                st.rerun()
            else:
                st.error("❌ No se encontró información completa para este cliente")
                
    except Exception as e:
        st.error(f"❌ Error cargando datos del cliente: {e}")

def mostrar_panel_cliente_detallado():
    """Muestra el panel detallado del cliente seleccionado - VERSIÓN CORREGIDA"""
    
    datos = st.session_state.datos_cliente_completos
    cliente = datos['cliente']
    resumen = datos['resumen_cartera']
    
    st.markdown("---")
    st.header(f"👤 {cliente['razon_social']}")
    
    # Botón para volver
    if st.button("← Volver a lista completa", type="secondary", key="btn_volver_lista"):
        st.session_state.cliente_seleccionado = None
        st.rerun()
    
    # ====================
    # SECCIÓN 1: DATOS DE CONTACTO
    # ====================
    st.subheader("📞 Datos de Contacto")
    
    col_contact1, col_contact2 = st.columns(2)
    
    with col_contact1:
        st.text_input("NIT", cliente.get('nit_cliente', 'N/A'), disabled=True, key="nit_display")
        st.text_input("Teléfono", cliente.get('telefono', 'No disponible') or 'No disponible', disabled=True, key="telefono_display")
        st.text_input("Celular", cliente.get('celular', 'No disponible') or 'No disponible', disabled=True, key="celular_display")
    
    with col_contact2:
        st.text_input("Email", cliente.get('email', 'No disponible') or 'No disponible', disabled=True, key="email_display")
        st.text_input("Ciudad", cliente.get('ciudad', 'No disponible') or 'No disponible', disabled=True, key="ciudad_display")
        st.text_input("Vendedor", cliente.get('vendedor_asignado', 'No asignado') or 'No asignado', disabled=True, key="vendedor_display")
    
    # Dirección completa
    st.text_input("Dirección", cliente.get('direccion', 'No disponible') or 'No disponible', disabled=True, key="direccion_display")
    
    # ====================
    # SECCIÓN 2: RESUMEN CARTERA - ✅ CORREGIDO
    # ====================
    st.subheader("💰 Resumen de Cartera")
    
    col_res1, col_res2, col_res3, col_res4 = st.columns(4)
    
    with col_res1:
        st.metric("Total Cartera", f"${resumen['total_cartera']:,.0f}")
    
    with col_res2:
        st.metric("Cartera en Mora", f"${resumen['cartera_mora']:,.0f}")
    
    with col_res3:
        st.metric("Facturas Totales", resumen['total_facturas'])
    
    with col_res4:
        st.metric("Facturas Vencidas", resumen['facturas_vencidas'])
    
    # ====================
    # SECCIÓN 3: DETALLE DE FACTURAS
    # ====================
    if not datos['cartera'].empty:
        st.subheader("📄 Detalle de Facturas")
        
        # Separar facturas corrientes y vencidas
        facturas_corrientes = datos['cartera'][datos['cartera']['dias_vencidos'] == 0]
        facturas_vencidas = datos['cartera'][datos['cartera']['dias_vencidos'] > 0]
        
        tab1, tab2 = st.tabs([f"✅ Facturas Corrientes ({len(facturas_corrientes)})", 
                             f"⚠️ Facturas Vencidas ({len(facturas_vencidas)})"])
        
        with tab1:
            if not facturas_corrientes.empty:
                df_display = facturas_corrientes[['nro_factura', 'total_cop', 'fecha_emision', 'fecha_vencimiento', 'condicion_pago']].copy()
                df_display['total_cop'] = df_display['total_cop'].apply(lambda x: f"${x:,.0f}")
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                st.info("No hay facturas corrientes")
        
        with tab2:
            if not facturas_vencidas.empty:
                df_display = facturas_vencidas[['nro_factura', 'total_cop', 'fecha_emision', 'fecha_vencimiento', 'dias_vencidos', 'condicion_pago']].copy()
                df_display['total_cop'] = df_display['total_cop'].apply(lambda x: f"${x:,.0f}")
                df_display['dias_vencidos'] = df_display['dias_vencidos'].astype(int)
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                st.info("No hay facturas vencidas")
    
    # ====================
    # SECCIÓN 4: HISTORIAL DE GESTIONES
    # ====================
    if not datos['gestiones'].empty:
        st.subheader("📊 Últimas Gestiones")
        
        df_gestiones = datos['gestiones'].head(5).copy()  # Mostrar solo las 5 más recientes
        
        # Formatear para mostrar
        columnas_mostrar = ['fecha_contacto', 'tipo_contacto', 'resultado', 'observaciones']
        columnas_existentes = [col for col in columnas_mostrar if col in df_gestiones.columns]
        
        df_display = df_gestiones[columnas_existentes]
        st.dataframe(df_display, use_container_width=True, height=200, hide_index=True)
        
        if len(datos['gestiones']) > 5:
            st.caption(f"Mostrando 5 de {len(datos['gestiones'])} gestiones totales")
    else:
        st.info("📝 No hay gestiones registradas para este cliente")
    
    # ====================
    # SECCIÓN 5: ACCIONES RÁPIDAS
    # ====================
    st.markdown("---")
    st.subheader("🚀 Acciones Rápidas")
    
    col_acc1, col_acc2, col_acc3 = st.columns(3)
    
    with col_acc1:
        if st.button("💬 WhatsApp Cliente", use_container_width=True, key="btn_whatsapp_cliente"):

            # ✅ MEJORA: VALIDACIÓN ROBUSTA DE AMBOS CAMPOS (CELULAR Y TELÉFONO)

            numero_whatsapp = None
            celular = cliente.get('celular')
            telefono = cliente.get('telefono')
            
            # Función auxiliar para validar y limpiar número
            def validar_numero(numero_str):
                if not numero_str or numero_str == 'No disponible':
                    return None
                
                # Convertir a string y limpiar
                numero_limpio = ''.join(filter(str.isdigit, str(numero_str)))
                
                # Validar que sea un número colombiano (10 dígitos)
                if len(numero_limpio) == 10 and numero_limpio.startswith(('3', '2', '1')):
                    return numero_limpio
                return None
            
            # Validar ambos campos exhaustivamente
            numero_celular_valido = validar_numero(celular)
            numero_telefono_valido = validar_numero(telefono)
            
            # Priorizar celular válido, luego teléfono válido
            if numero_celular_valido:
                numero_whatsapp = numero_celular_valido
                tipo_numero = "celular"
            elif numero_telefono_valido:
                numero_whatsapp = numero_telefono_valido
                tipo_numero = "teléfono"
            else:
                numero_whatsapp = None
            
            if numero_whatsapp:
                # Agregar prefijo internacional para Colombia
                numero_final = f"57{numero_whatsapp}"
                enlace_whatsapp = f"https://wa.me/{numero_final}"
                
                st.success(f"💬 WhatsApp listo para: {numero_whatsapp} ({tipo_numero})")
                st.markdown(f"""
                **Opciones:**
                - 📱 **Abrir WhatsApp:** [Click aquí]({enlace_whatsapp})
                - 📋 **Número copiado:** `{numero_whatsapp}`
                - 🔍 **Tipo:** {tipo_numero.capitalize()}
                """)
                
                # Mostrar enlace directo como botón adicional
                st.link_button("📱 Abrir Conversación WhatsApp", enlace_whatsapp)
                
                # Debug info (opcional)
                st.caption(f"🔍 Validación: Celular='{celular}' → {numero_celular_valido} | Teléfono='{telefono}' → {numero_telefono_valido}")
            else:
                st.warning("📵 No hay número de contacto válido para WhatsApp")
                st.info(f"""
                **Números encontrados:**
                - 📞 Celular: `{celular if celular and celular != 'No disponible' else 'No disponible'}`
                - 📞 Teléfono: `{telefono if telefono and telefono != 'No disponible' else 'No disponible'}`
                
                **Requisitos para WhatsApp:**
                - 10 dígitos colombianos
                - Comenzar con 3, 2 o 1
                - Sin espacios ni caracteres especiales
                """)
    
    with col_acc2:
        if st.button("📧 Email Corporativo", use_container_width=True, key="btn_email_corporativo"):
            email = cliente.get('email')
            if email and email != 'No disponible' and '@' in str(email):
                # Obtener facturas vencidas del cliente
                facturas_vencidas = datos['cartera'][datos['cartera']['dias_vencidos'] > 0]
                
                if not facturas_vencidas.empty:
                    # Calcular variables para la plantilla
                    razon_social = cliente.get('razon_social', 'Cliente')
                    nit = cliente.get('nit_cliente', 'N/A')
                    cantidad_facturas = len(facturas_vencidas)
                    total_mora = facturas_vencidas['total_cop'].sum()
                    max_dias_mora = facturas_vencidas['dias_vencidos'].max()
                    
                    # Formatear valores
                    total_mora_formateado = f"{total_mora:,.0f}"
                    
                    # Plantilla de email CORPORATIVA
                    asunto = "RECORDATORIO DE PAGO - ALPAPEL SAS"
                    cuerpo = f"""Señores
{razon_social}
NIT: {nit}

ASUNTO: {asunto}

Estimado Cliente:

Desde ALPAPEL S.A.S., nos permitimos informarles que actualmente presentan {cantidad_facturas} factura/s vencida/s por un valor de ${total_mora_formateado} COP, la/s cual/es a la fecha presenta/n hasta {max_dias_mora} días de mora.

Recordamos que facturas con mora igual o superior a 10 días pueden generar bloqueos en futuros pedidos.

Si realizó pagos que aún no están reflejados, por favor enviar el soporte al 3184776379 o hacer caso omiso en espera de su aplicación.

Cuentas habilitadas:
• Bancolombia – CC 23902956641
• Banco de Bogotá – CC 032075574
• Davivienda – CC 478069999447
• Pagos por PSE, Tarjeta de crédito y debido (Solicitar al WhatsApp de cartera)

Contacto:
WhatsApp: 3184776379 / 3233255021
Correo: cartera@alpapel.com / coordinador.cartera@alpapel.com

Cordialmente,

ALPAPEL S.A.S
860.524.523-1"""
                    
                    # Codificar para URL
                    asunto_codificado = asunto.replace(' ', '%20')
                    cuerpo_codificado = cuerpo.replace('\n', '%0D%0A').replace(' ', '%20')
                    
                    enlace_email = f"mailto:{email}?subject={asunto_codificado}&body={cuerpo_codificado}"
                    
                    st.success(f"📧 Email corporativo listo para: {email}")
                    st.markdown(f"""
                    **Email preparado con:**
                    - 📋 **Plantilla corporativa** completa
                    - 📊 **{cantidad_facturas} facturas** en mora
                    - 💰 **${total_mora_formateado} COP** pendientes
                    - ⏰ **Hasta {max_dias_mora} días** de mora
                    """)
                    
                    # Mostrar enlace directo como botón adicional
                    st.link_button("📧 Abrir Email Corporativo", enlace_email)
                    
                else:
                    # Cliente SIN facturas vencidas - Email vacío
                    enlace_email = f"mailto:{email}"
                    
                    st.success(f"📧 Email listo para: {email}")
                    st.info("""
                    **Cliente al día - Email vacío:**
                    - 📧 **Destinatario:** {email}
                    - 📝 **Asunto y cuerpo:** Vacíos para redacción personalizada
                    """)
                    
                    # Mostrar enlace directo como botón adicional
                    st.link_button("📧 Abrir Email", enlace_email)
            else:
                st.warning("📧 No hay dirección de email válida disponible")
    
    with col_acc3:
        if st.button("📋 Ir a Gestión", use_container_width=True, key="btn_ir_gestion"):
            if st.session_state.cliente_seleccionado:
                # ✅ GUARDAR CLIENTE PARA GESTIÓN
                st.session_state.cliente_para_gestion = st.session_state.cliente_seleccionado
                st.session_state.ir_a_gestion = True
                
                # ✅ FORZAR CAMBIO DE SECCIÓN INMEDIATAMENTE
                st.session_state.section = "📞 Gestión"
                
                st.success("🔄 Navegando a Gestión...")
                
                # ✅ DELAY CORTO Y RERUN FORZADO
                import time
                time.sleep(0.3)
                st.rerun()
            else:
                st.error("❌ No hay cliente seleccionado")

def cargar_datos_cartera_filtrados(texto_busqueda, filtro_vendedor, filtro_ciudad, filtro_dias):
    """Carga los datos de cartera aplicando filtros - VERSIÓN MEJORADA"""
    try:
        # Obtener datos base según permisos de usuario
        cartera_base = st.session_state.db.obtener_cartera_actual()
        
        if cartera_base.empty:
            return pd.DataFrame()
        
        # Aplicar filtro de texto si existe
        if texto_busqueda and texto_busqueda.strip():
            texto = texto_busqueda.lower().strip()
            mask = (
                cartera_base['nit_cliente'].astype(str).str.lower().str.contains(texto, na=False) |
                cartera_base['razon_social_cliente'].astype(str).str.lower().str.contains(texto, na=False) |
                cartera_base['nro_factura'].astype(str).str.lower().str.contains(texto, na=False) |
                cartera_base['nombre_vendedor'].astype(str).str.lower().str.contains(texto, na=False)
            )
            cartera_filtrada = cartera_base[mask]
        else:
            cartera_filtrada = cartera_base.copy()
        
        # Aplicar filtro de vendedor
        if filtro_vendedor and filtro_vendedor != "Todos los vendedores":
            cartera_filtrada = cartera_filtrada[cartera_filtrada['nombre_vendedor'] == filtro_vendedor]
        
        # Aplicar filtro de ciudad (necesita join con clientes)
        if filtro_ciudad and filtro_ciudad != "Todas las ciudades":
            try:
                clientes = st.session_state.db.obtener_clientes()
                if not clientes.empty and 'ciudad' in clientes.columns:
                    cartera_filtrada = cartera_filtrada.merge(
                        clientes[['nit_cliente', 'ciudad']], 
                        on='nit_cliente', 
                        how='left'
                    )
                    cartera_filtrada = cartera_filtrada[cartera_filtrada['ciudad_y'] == filtro_ciudad]
            except Exception as e:
                print(f"⚠️ Error filtrando por ciudad: {e}")
        
        # Aplicar filtro de días vencidos
        if filtro_dias != "Todos los días":
            if filtro_dias == "0 días (Corriente)":
                cartera_filtrada = cartera_filtrada[cartera_filtrada['dias_vencidos'] == 0]
            elif filtro_dias == "1-30 días":
                cartera_filtrada = cartera_filtrada[(cartera_filtrada['dias_vencidos'] >= 1) & (cartera_filtrada['dias_vencidos'] <= 30)]
            elif filtro_dias == "31-60 días":
                cartera_filtrada = cartera_filtrada[(cartera_filtrada['dias_vencidos'] >= 31) & (cartera_filtrada['dias_vencidos'] <= 60)]
            elif filtro_dias == "61-90 días":
                cartera_filtrada = cartera_filtrada[(cartera_filtrada['dias_vencidos'] >= 61) & (cartera_filtrada['dias_vencidos'] <= 90)]
            elif filtro_dias == "+90 días":
                cartera_filtrada = cartera_filtrada[cartera_filtrada['dias_vencidos'] > 90]
        
        print(f"🔍 DEBUG - Filtros aplicados: {len(cartera_filtrada)} registros")
        return cartera_filtrada
        
    except Exception as e:
        st.error(f"❌ Error aplicando filtros: {e}")
        return pd.DataFrame()

def mostrar_tabla_cartera(cartera_df):
    """Muestra la tabla de cartera con todas las columnas"""
    if cartera_df.empty:
        st.warning("No se encontraron registros con los filtros aplicados")
        return
    
    # Definir columnas a mostrar
    columnas = [
        "NIT Cliente", "Razón Social", "Vendedor", "Factura", "Total COP", 
        "Fecha Emisión", "Fecha Vcto", "Días Vencidos", "Condición Pago", "Ciudad"
    ]
    
    # Mapeo de columnas de la base de datos
    mapeo_columnas = {
        'nit_cliente': 'NIT Cliente',
        'razon_social_cliente': 'Razón Social', 
        'nombre_vendedor': 'Vendedor',
        'nro_factura': 'Factura',
        'total_cop': 'Total COP',
        'fecha_emision': 'Fecha Emisión',
        'fecha_vencimiento': 'Fecha Vcto',
        'dias_vencidos': 'Días Vencidos',
        'condicion_pago': 'Condición Pago',
        'ciudad': 'Ciudad'
    }
    
    # Crear DataFrame para mostrar
    display_df = cartera_df.copy()
    
    # Renombrar columnas
    for col_orig, col_nuevo in mapeo_columnas.items():
        if col_orig in display_df.columns:
            display_df = display_df.rename(columns={col_orig: col_nuevo})
    
    # Seleccionar solo las columnas que existen
    columnas_existentes = [col for col in columnas if col in display_df.columns]
    display_df = display_df[columnas_existentes]
    
    # Formatear columnas
    if 'Total COP' in display_df.columns:
        display_df['Total COP'] = display_df['Total COP'].apply(lambda x: f"${x:,.0f}")
    
    # Mostrar tabla
    st.dataframe(
        display_df,
        use_container_width=True,
        height=600,
        hide_index=True
    )
    
    # Mostrar resumen
    total_cartera = cartera_df['total_cop'].sum() if 'total_cop' in cartera_df.columns else 0
    total_registros = len(cartera_df)
    st.success(f"**Resumen:** {total_registros} registros | **Valor total:** ${total_cartera:,.0f}")

def mostrar_tabla_cartera_completa(cartera_df):
    """Muestra la tabla de cartera completa con todas las columnas disponibles"""
    
    # Crear una copia para no modificar el original
    display_df = cartera_df.copy()
    
    # Formatear columnas numéricas
    if 'total_cop' in display_df.columns:
        display_df['total_cop'] = display_df['total_cop'].apply(lambda x: f"${x:,.0f}")
    
    if 'dias_vencidos' in display_df.columns:
        display_df['dias_vencidos'] = display_df['dias_vencidos'].astype(int)
    
    # Mostrar todas las columnas disponibles
    st.dataframe(
        display_df,
        use_container_width=True,
        height=600,
        hide_index=True
    )
    
    # Opciones de exportación
    col_exp1, col_exp2 = st.columns(2)
    
    with col_exp1:
        if st.button("📊 Exportar a CSV", use_container_width=True, key="btn_export_csv"):
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="⬇️ Descargar CSV",
                data=csv,
                file_name=f"cartera_filtrada_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="btn_download_csv"
            )
    
    with col_exp2:
        if st.button("📋 Copiar al Portapapeles", use_container_width=True, key="btn_copy_clipboard"):
            # Crear una versión para copiar
            copy_df = display_df.copy()
            # Remover formato de dinero para mejor copiado
            if 'total_cop' in copy_df.columns:
                copy_df['total_cop'] = cartera_df['total_cop']
            
            st.success("✅ Datos copiados al portapapeles (puedes pegarlos en Excel)")    

def cargar_excel_cartera_streamlit():
    """Función para cargar Excel en Streamlit - VERSIÓN MEJORADA"""
    
    st.subheader("📤 Cargar Archivo Excel de Cartera")
    
    uploaded_file = st.file_uploader(
        "Selecciona archivo Excel de cartera",
        type=['xlsx', 'xls'],
        key="upload_excel_cartera"
    )
    
    if uploaded_file is not None:
        # Mostrar información del archivo
        file_details = {
            "Nombre": uploaded_file.name,
            "Tipo": uploaded_file.type,
            "Tamaño": f"{uploaded_file.size / 1024 / 1024:.2f} MB"
        }
        st.write("**Archivo seleccionado:**")
        st.json(file_details)
        
        # Botón para confirmar la carga
        if st.button("🚀 Iniciar Carga del Archivo", use_container_width=True, type="primary", key="btn_iniciar_carga"):
            # Guardar el archivo en session_state
            st.session_state.archivo_data = uploaded_file.getvalue()
            st.session_state.archivo_nombre = uploaded_file.name
            st.session_state.carga_en_progreso = True
            st.rerun()

def procesar_carga_excel():
    """Procesar la carga del archivo Excel"""
    if not st.session_state.carga_en_progreso:
        return
        
    try:
        st.info("🔄 Iniciando proceso de carga...")
        
        # Crear elementos de UI para el progreso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Paso 1: Guardar archivo temporal
        status_text.text("📁 Paso 1/4: Guardando archivo...")
        try:
            with open("temp_cartera.xlsx", "wb") as f:
                f.write(st.session_state.archivo_data)
            progress_bar.progress(25)
            time.sleep(1)
        except Exception as e:
            st.error(f"❌ Error guardando archivo: {str(e)}")
            st.session_state.carga_en_progreso = False
            return
        
        # Paso 2: Validar archivo
        status_text.text("🔍 Paso 2/4: Validando Excel...")
        try:
            test_df = pd.read_excel("temp_cartera.xlsx", nrows=5)
            progress_bar.progress(50)
            time.sleep(1)
        except Exception as e:
            st.error(f"❌ Error validando Excel: {str(e)}")
            st.session_state.carga_en_progreso = False
            return
        
        # Paso 3: Cargar a base de datos
        status_text.text("💾 Paso 3/4: Cargando a base de datos...")
        try:
            success, message = st.session_state.db.cargar_excel_cartera("temp_cartera.xlsx")
            progress_bar.progress(75)
            time.sleep(1)
        except Exception as e:
            st.error(f"❌ Error en la carga: {str(e)}")
            st.session_state.carga_en_progreso = False
            return
        
        # Paso 4: Finalizar
        status_text.text("✅ Paso 4/4: Finalizando...")
        progress_bar.progress(100)
        
        if success:
            st.success(f"✅ {message}")
            
            # Actualizar estado
            st.session_state.datos_actualizados = True
            st.session_state.ultima_actualizacion = datetime.now()
            st.session_state.mostrar_uploader = False
            
            st.info("🔄 Usa 'Actualizar Vista' para ver los nuevos datos")
        
        # Finalizar estado
        st.session_state.carga_en_progreso = False
        time.sleep(2)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error inesperado: {str(e)}")
        st.session_state.carga_en_progreso = False

def analisis_cartera_section():
    """Sección de Análisis de Cartera"""
    from analisis_cartera_module import analisis_cartera_section as cartera_analisis
    cartera_analisis()

def analisis_gestion_section():
    """Sección de Análisis de Gestión - CON FILTROS DINÁMICOS"""
    # Esta línea ya importa el módulo actualizado con los filtros dinámicos
    from analisis_gestion_module import analisis_gestion_section as gestion_analisis
    gestion_analisis()

if __name__ == "__main__":
    main()