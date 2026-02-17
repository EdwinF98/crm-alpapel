# analisis_gestion_module.py - VERSIÓN CORREGIDA CON FILTROS DINÁMICOS
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

def analisis_gestion_section():
    """Sección completa de Análisis de Gestión con 3 filtros"""
    
    st.header("📈 Análisis de Gestión")
    
    # INICIALIZAR VARIABLES DE SESIÓN
    if 'filtro_periodo_gestion' not in st.session_state:
        st.session_state.filtro_periodo_gestion = "Mes Actual"
    if 'filtro_usuario_gestion' not in st.session_state:
        st.session_state.filtro_usuario_gestion = "Todos los vendedores"
    if 'filtro_vendedor_asignado' not in st.session_state:
        st.session_state.filtro_vendedor_asignado = "Todos los vendedores"
    if 'filtro_resultado_gestion' not in st.session_state:
        st.session_state.filtro_resultado_gestion = "Todos los resultados"
    
    try:
        # 1. FILTROS PRINCIPALES (ahora con 4 opciones)
        periodo_seleccionado, fecha_inicio, fecha_fin, usuario_seleccionado, vendedor_asignado_seleccionado, resultado_seleccionado = mostrar_filtros_gestion()
        
        # Extraer email real del display de usuario
        usuario_email = extraer_email_usuario(usuario_seleccionado)
        
        # Mostrar información del filtro aplicado
        filtro_info = f"**Período activo:** {periodo_seleccionado} - {fecha_inicio} a {fecha_fin}"
        
        if usuario_seleccionado != "Todos los vendedores":
            usuario_nombre = usuario_seleccionado.split('(')[0].strip()
            filtro_info += f" | **Gestor:** {usuario_nombre}"
        
        if vendedor_asignado_seleccionado != "Todos los vendedores":
            filtro_info += f" | **Vendedor:** {vendedor_asignado_seleccionado}"
        
        if resultado_seleccionado != "Todos los resultados":
            filtro_info += f" | **Resultado:** {resultado_seleccionado}"
        
        st.info(filtro_info)
        
        # 2. MÉTRICAS DE PROGRESO (con todos los filtros)
        mostrar_metricas_progreso(fecha_inicio, fecha_fin, usuario_email, vendedor_asignado_seleccionado)
        
        # 3. GRÁFICAS PRINCIPALES (con todos los filtros)
        mostrar_graficas_gestion(fecha_inicio, fecha_fin, usuario_email, vendedor_asignado_seleccionado, resultado_seleccionado)
        
        # 4. TABLA DETALLADA (con todos los filtros)
        mostrar_tabla_detallada(fecha_inicio, fecha_fin, usuario_email, vendedor_asignado_seleccionado, resultado_seleccionado)
        
        # 5. BOTONES DE ACCIÓN
        mostrar_botones_accion_gestion()
        
    except Exception as e:
        st.error(f"❌ Error en análisis de gestión: {str(e)}")

def mostrar_filtros_gestion():
    """Muestra los filtros de análisis con manejo correcto de estado"""
    
    st.subheader("🔍 Filtros de Análisis")
    
    # 1. PRIMERO: Manejar cambios de filtro con callbacks
    def actualizar_filtro_periodo():
        st.session_state.filtro_periodo_gestion = st.session_state.selectbox_periodo_gestion_key
    
    def actualizar_filtro_usuario():
        st.session_state.filtro_usuario_gestion = st.session_state.selectbox_usuario_gestion_key
    
    def actualizar_filtro_vendedor():
        st.session_state.filtro_vendedor_asignado = st.session_state.selectbox_vendedor_asignado_key
    
    def actualizar_filtro_resultado():
        st.session_state.filtro_resultado_gestion = st.session_state.filtro_resultado_gestion_key
    
    # 2. Obtener datos para los dropdowns
    user = st.session_state.get('user', {})
    db = st.session_state.db
    
    # ========== CORRECCIÓN AQUÍ: Lista de usuarios para el filtro ==========
    # El problema era que para vendedores (comercial/consulta) solo mostraba su email
    # Pero deben poder ver todas las gestiones de todos los usuarios
    
    usuarios_disponibles = []
    
    if user.get('rol') in ['admin', 'supervisor']:
        # Admin y supervisor ven todos los usuarios
        usuarios_con_gestiones = db.obtener_usuarios_con_gestiones()
        if not usuarios_con_gestiones.empty:
            usuarios_disponibles = ["Todos los vendedores"]
            for _, usuario in usuarios_con_gestiones.iterrows():
                display_name = f"{usuario['nombre_completo']} ({usuario['email']})"
                usuarios_disponibles.append(display_name)
        else:
            usuarios_disponibles = ["Todos los vendedores"]
    else:
        # Vendedores (comercial/consulta) deben ver "Todos los vendedores" como opción
        # y también su propio email si quieren filtrar solo sus gestiones
        usuarios_con_gestiones = db.obtener_usuarios_con_gestiones()
        if not usuarios_con_gestiones.empty:
            usuarios_disponibles = ["Todos los vendedores"]
            # Agregar todos los usuarios para que el vendedor pueda ver todas las gestiones
            for _, usuario in usuarios_con_gestiones.iterrows():
                display_name = f"{usuario['nombre_completo']} ({usuario['email']})"
                usuarios_disponibles.append(display_name)
        else:
            # Si no hay usuarios, al menos mostrar la opción de todos
            usuarios_disponibles = ["Todos los vendedores"]
            # Y agregar el email del usuario actual
            user_email = user.get('email', '')
            if user_email:
                usuarios_disponibles.append(user_email)
    
    # Lista de vendedores asignados
    vendedores_asignados = db.obtener_vendedores_asignados()
    
    # Opciones de resultado
    resultado_options = [
        "Todos los resultados",
        "Compromisos de Pago", 
        "Contactos Exitosos",
        "Dificultades/Rechazos",
        "Seguimientos Pendientes"
    ]
    
    # 3. CREAR LOS WIDGETS CON on_change
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        periodo_seleccionado = st.selectbox(
            "📅 Período:",
            options=[
                "Mes Actual", "Mes Anterior", "Últimos 7 días", 
                "Últimos 30 días", "Trimestre Actual", "Personalizado"
            ],
            index=0,
            key="selectbox_periodo_gestion_key",
            on_change=actualizar_filtro_periodo
        )
    
    with col2:
        # El cambio aquí es que para vendedores ya no está deshabilitado
        usuario_seleccionado = st.selectbox(
            "👤 Usuario Gestión:",
            options=usuarios_disponibles,
            # IMPORTANTE: Ya no deshabilitar para vendedores
            disabled=False,  # Cambiado de: disabled=(user.get('rol') not in ['admin', 'supervisor'])
            help="Usuario que registró la gestión",
            key="selectbox_usuario_gestion_key",
            on_change=actualizar_filtro_usuario
        )
    
    with col3:
        vendedor_asignado_seleccionado = st.selectbox(
            "👔 Vendedor Asignado:",
            options=vendedores_asignados,
            help="Vendedor asignado al cliente en la cartera",
            key="selectbox_vendedor_asignado_key",
            on_change=actualizar_filtro_vendedor
        )
    
    with col4:
        resultado_seleccionado = st.selectbox(
            "🎯 Resultado:",
            options=resultado_options,
            help="Filtrar por tipo de resultado",
            key="filtro_resultado_gestion_key",
            on_change=actualizar_filtro_resultado
        )
    
    # 4. Inicializar session_state si no existe (solo primera vez)
    if 'filtro_periodo_gestion' not in st.session_state:
        st.session_state.filtro_periodo_gestion = periodo_seleccionado
    if 'filtro_usuario_gestion' not in st.session_state:
        st.session_state.filtro_usuario_gestion = usuario_seleccionado
    if 'filtro_vendedor_asignado' not in st.session_state:
        st.session_state.filtro_vendedor_asignado = vendedor_asignado_seleccionado
    if 'filtro_resultado_gestion' not in st.session_state:
        st.session_state.filtro_resultado_gestion = resultado_seleccionado
    
    # 5. SELECTOR DE FECHAS PERSONALIZADO
    fecha_inicio_temp = None
    fecha_fin_temp = None
    
    if periodo_seleccionado == "Personalizado":
        st.markdown("---")
        st.subheader("📅 Seleccionar Rango de Fechas Personalizado")
        
        col_fecha1, col_fecha2 = st.columns(2)
        
        with col_fecha1:
            fecha_inicio_seleccionada = st.date_input(
                "Fecha de inicio:",
                value=datetime.now().replace(day=1),
                max_value=datetime.now(),
                key="fecha_inicio_personalizada_key"
            )
        
        with col_fecha2:
            fecha_fin_seleccionada = st.date_input(
                "Fecha de fin:",
                value=datetime.now(),
                max_value=datetime.now(),
                key="fecha_fin_personalizada_key"
            )
        
        if fecha_inicio_seleccionada > fecha_fin_seleccionada:
            st.error("❌ La fecha de inicio no puede ser mayor que la fecha de fin")
            fecha_inicio_seleccionada = datetime.now().replace(day=1)
            fecha_fin_seleccionada = datetime.now()
        
        fecha_inicio_temp = fecha_inicio_seleccionada.strftime('%Y-%m-%d')
        fecha_fin_temp = fecha_fin_seleccionada.strftime('%Y-%m-%d')
    
    # 6. Botones para forzar actualización (opcional)
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    
    with col_btn1:
        if st.button("🔄 Aplicar Filtros", use_container_width=True, type="primary", key="btn_aplicar_filtros_unique"):
            # Los filtros ya se actualizaron con on_change, solo rerun
            st.rerun()
    
    with col_btn2:
        if st.button("🧹 Limpiar Filtros", use_container_width=True, key="btn_limpiar_filtros_unique"):
            st.session_state.filtro_periodo_gestion = "Mes Actual"
            st.session_state.filtro_usuario_gestion = "Todos los vendedores"
            st.session_state.filtro_vendedor_asignado = "Todos los vendedores"
            st.session_state.filtro_resultado_gestion = "Todos los resultados"
            st.rerun()
    
    with col_btn3:
        # Obtener rango de fechas
        fecha_inicio, fecha_fin = st.session_state.db.obtener_rango_fechas_por_periodo(
            periodo_seleccionado,
            fecha_inicio_temp,
            fecha_fin_temp
        )
        
        # Mostrar info
        info_text = f"📅 Período: {fecha_inicio} a {fecha_fin}"
        
        if usuario_seleccionado != "Todos los vendedores":
            usuario_nombre = usuario_seleccionado.split('(')[0].strip()
            info_text += f" | 👤 Gestor: {usuario_nombre}"
        
        if vendedor_asignado_seleccionado != "Todos los vendedores":
            info_text += f" | 👔 Vendedor: {vendedor_asignado_seleccionado}"
        
        if resultado_seleccionado != "Todos los resultados":
            info_text += f" | 🎯 Resultado: {resultado_seleccionado}"
        
        st.info(info_text)
    
    # 7. Calcular y retornar parámetros
    fecha_inicio, fecha_fin = st.session_state.db.obtener_rango_fechas_por_periodo(
        periodo_seleccionado,
        fecha_inicio_temp,
        fecha_fin_temp
    )
    
    return periodo_seleccionado, fecha_inicio, fecha_fin, usuario_seleccionado, vendedor_asignado_seleccionado, resultado_seleccionado

def extraer_email_usuario(display_name):
    """Extrae el email de un string de display de usuario"""
    if not display_name or display_name == "Todos los vendedores":
        return "Todos los vendedores"
    
    # Buscar email entre paréntesis
    import re
    match = re.search(r'\((.*?@.*?)\)', display_name)
    if match:
        return match.group(1)
    
    # Si no hay paréntesis, asumir que ya es el email
    return display_name

def mostrar_metricas_progreso(fecha_inicio, fecha_fin, usuario_email=None, vendedor_asignado=None):
    """Muestra métricas con filtros de usuario y vendedor asignado"""
    
    st.subheader("📊 Progreso de Gestión")
    
    try:
        # Obtener datos con ambos filtros
        progreso_data = st.session_state.db.obtener_progreso_gestion(
            fecha_inicio, fecha_fin, usuario_email, vendedor_asignado
        )
        
        if not progreso_data:
            st.warning("No hay datos disponibles con los filtros seleccionados")
            return
        
        # Mostrar información del filtro
        periodo_info = f"📅 Período: {progreso_data.get('periodo', 'No especificado')}"
        
        if usuario_email and usuario_email != "Todos los vendedores":
            usuario_nombre = usuario_email.split('@')[0]
            periodo_info += f" | 👤 Gestor: {usuario_nombre}"
        
        if vendedor_asignado and vendedor_asignado != "Todos los vendedores":
            periodo_info += f" | 👔 Vendedor: {vendedor_asignado}"
        
        st.caption(periodo_info)
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_clientes = progreso_data.get('total_clientes', 0)
            gestionados = progreso_data.get('clientes_gestionados', 0)
            porcentaje = progreso_data.get('porcentaje_general', 0)
            
            st.markdown(f"**Progreso General**")
            progreso_html = crear_barra_progreso_html(porcentaje, "primary")
            st.markdown(progreso_html, unsafe_allow_html=True)
            st.caption(f"✅ {gestionados} / {total_clientes} clientes ({porcentaje:.1f}%)")
        
        with col2:
            clientes_mora = progreso_data.get('clientes_mora', 0)
            mora_gestionados = progreso_data.get('clientes_mora_gestionados', 0)
            porcentaje_mora = progreso_data.get('porcentaje_mora', 0)
            
            st.markdown(f"**Clientes en Mora**")
            progreso_html = crear_barra_progreso_html(porcentaje_mora, "warning")
            st.markdown(progreso_html, unsafe_allow_html=True)
            st.caption(f"⚠️ {mora_gestionados} / {clientes_mora} clientes ({porcentaje_mora:.1f}%)")
        
        with col3:
            # Total gestiones con filtros
            gestiones_periodo = st.session_state.db.obtener_gestiones_por_periodo(
                fecha_inicio, fecha_fin, usuario_email, vendedor_asignado
            )
            total_gestiones = len(gestiones_periodo)
            
            st.metric(
                "Total Gestiones",
                f"{total_gestiones:,}",
                help="Número total de gestiones con filtros aplicados"
            )
        
        with col4:
            # Clientes únicos
            if not gestiones_periodo.empty:
                clientes_unicos = gestiones_periodo['nit_cliente'].nunique()
            else:
                clientes_unicos = 0
                
            st.metric(
                "Clientes Únicos",
                f"{clientes_unicos:,}",
                help="Clientes diferentes gestionados"
            )
        
        # Segunda fila de métricas
        st.markdown("---")
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            # Tasa de contacto
            if not gestiones_periodo.empty:
                contactos_exitosos = len(gestiones_periodo[
                    gestiones_periodo['resultado'].str.contains('Contacto|Promesa|Pago', na=False)
                ])
                tasa_contacto = (contactos_exitosos / total_gestiones * 100) if total_gestiones > 0 else 0
            else:
                tasa_contacto = 0
                
            st.metric(
                "Tasa de Contacto",
                f"{tasa_contacto:.1f}%",
                help="Porcentaje de gestiones con contacto exitoso"
            )
        
        with col6:
            # Promesas generadas
            if not gestiones_periodo.empty:
                promesas = len(gestiones_periodo[
                    gestiones_periodo['resultado'].str.contains('Promesa', na=False)
                ])
            else:
                promesas = 0
                
            st.metric(
                "Promesas Generadas",
                f"{promesas:,}",
                help="Compromisos de pago obtenidos"
            )
        
        with col7:
            # Efectividad
            if total_clientes > 0:
                efectividad = (gestionados / total_clientes * 100)
            else:
                efectividad = 0
                
            st.metric(
                "Efectividad General",
                f"{efectividad:.1f}%",
                delta=f"+{gestionados} clientes" if gestionados > 0 else None
            )
        
        with col8:
            # Pendientes
            pendientes = total_clientes - gestionados
            st.metric(
                "Pendientes",
                f"{pendientes:,}",
                delta_color="inverse",
                help="Clientes pendientes por gestionar"
            )
            
    except Exception as e:
        st.error(f"❌ Error cargando métricas: {str(e)}")

def crear_barra_progreso_html(porcentaje, tipo_color="primary"):
    """Crea una barra de progreso HTML personalizada"""
    
    # Definir colores según el tipo
    colores = {
        "primary": {"fondo": "#00B3B0", "texto": "#ffffff"},
        "warning": {"fondo": "#f59e0b", "texto": "#000000"},
        "success": {"fondo": "#10b981", "texto": "#ffffff"},
        "danger": {"fondo": "#ef4444", "texto": "#ffffff"}
    }
    
    color = colores.get(tipo_color, colores["primary"])
    
    barra_html = f"""
    <div style="background: #1e293b; border-radius: 10px; padding: 2px; margin: 5px 0;">
        <div style="background: {color['fondo']}; 
                    border-radius: 8px; 
                    height: 20px; 
                    width: {max(5, porcentaje)}%; 
                    display: flex; 
                    align-items: center; 
                    justify-content: center;
                    font-size: 12px;
                    font-weight: bold;
                    color: {color['texto']};
                    transition: width 0.5s ease;">
            {porcentaje:.1f}%
        </div>
    </div>
    """
    return barra_html

def mostrar_graficas_gestion(fecha_inicio, fecha_fin, usuario_email=None, 
                            vendedor_asignado=None, resultado_filtro=None):
    """Muestra gráficas principales con todos los filtros"""
    
    st.subheader("📈 Gráficas de Análisis")
    
    # Mostrar información de filtros
    filtro_info = f"📊 Datos del período: {fecha_inicio} a {fecha_fin}"
    
    if usuario_email and usuario_email != "Todos los vendedores":
        usuario_nombre = usuario_email.split('@')[0]
        filtro_info += f" | 👤 Gestor: {usuario_nombre}"
    
    if vendedor_asignado and vendedor_asignado != "Todos los vendedores":
        filtro_info += f" | 👔 Vendedor: {vendedor_asignado}"
    
    if resultado_filtro and resultado_filtro != "Todos los resultados":
        filtro_info += f" | 🎯 Resultado: {resultado_filtro}"
    
    st.caption(filtro_info)
    
    # Obtener datos con filtros
    try:
        # Gráfica 1: Distribución de resultados
        with st.spinner("Cargando distribución de resultados..."):
            fig_distribucion = crear_grafica_distribucion_resultados(
                fecha_inicio, fecha_fin, usuario_email, vendedor_asignado, resultado_filtro
            )
            if fig_distribucion:
                st.plotly_chart(fig_distribucion, use_container_width=True)
            else:
                st.info("📊 No hay datos suficientes para mostrar la distribución")
        
        # Dividir gráficas en columnas
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfica 2: Evolución diaria
            with st.spinner("Cargando evolución diaria..."):
                fig_evolucion = crear_grafica_evolucion_diaria(
                    fecha_inicio, fecha_fin, usuario_email, vendedor_asignado, resultado_filtro
                )
                if fig_evolucion:
                    st.plotly_chart(fig_evolucion, use_container_width=True)
                else:
                    st.info("📅 No hay datos de evolución diaria")
        
        with col2:
            # Gráfica 3: Evolución histórica
            with st.spinner("Cargando evolución histórica..."):
                fig_historica = crear_grafica_evolucion_historica(
                    fecha_inicio, fecha_fin, usuario_email, vendedor_asignado, resultado_filtro
                )
                if fig_historica:
                    st.plotly_chart(fig_historica, use_container_width=True)
                else:
                    st.info("📈 No hay datos históricos suficientes")
                    
    except Exception as e:
        st.error(f"❌ Error cargando gráficas: {str(e)}")

def crear_grafica_distribucion_resultados(fecha_inicio, fecha_fin, usuario_email=None,
                                         vendedor_asignado=None, resultado_filtro=None):
    """Crea gráfica de distribución con filtros múltiples"""
    
    try:
        # Obtener estadísticas con todos los filtros
        estadisticas = st.session_state.db.obtener_estadisticas_resultados_filtrado(
            fecha_inicio, fecha_fin, usuario_email, vendedor_asignado, resultado_filtro
        )
        
        if not estadisticas or not any(estadisticas.values()):
            return None
        
        categorias = list(estadisticas.keys())
        valores = list(estadisticas.values())
        
        # Título personalizado según filtros
        titulo = f"📊 Distribución de Resultados ({fecha_inicio} a {fecha_fin})"
        
        if vendedor_asignado and vendedor_asignado != "Todos los vendedores":
            titulo = f"📊 Resultados de {vendedor_asignado} ({fecha_inicio} a {fecha_fin})"
        elif usuario_email and usuario_email != "Todos los vendedores":
            usuario_nombre = usuario_email.split('@')[0]
            titulo = f"📊 Resultados de {usuario_nombre} ({fecha_inicio} a {fecha_fin})"
        
        if resultado_filtro and resultado_filtro != "Todos los resultados":
            titulo = f"📊 {resultado_filtro} ({fecha_inicio} a {fecha_fin})"
        
        # Crear gráfica
        df = pd.DataFrame({
            'Categoría': categorias,
            'Cantidad': valores
        })
        
        fig = px.bar(
            df,
            y='Categoría',
            x='Cantidad',
            title=titulo,
            labels={'Cantidad': 'Cantidad de Gestiones', 'Categoría': 'Tipo de Resultado'},
            orientation='h',
            color='Cantidad',
            color_continuous_scale=['#00B3B0', '#3b82f6', '#f59e0b', '#ef4444']
        )
        
        # Actualizar diseño
        fig.update_layout(
            plot_bgcolor='#1e293b',
            paper_bgcolor='#1e293b',
            font_color='#e2e8f0',
            showlegend=False,
            height=400,
            xaxis=dict(showgrid=True, gridcolor='#334155'),
            yaxis=dict(showgrid=False)
        )
        
        # Añadir etiquetas
        fig.update_traces(
            texttemplate='%{x} gestiones',
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>%{x} gestiones<extra></extra>'
        )
        
        return fig
        
    except Exception as e:
        print(f"Error creando gráfica de distribución: {e}")
        return None

def crear_grafica_evolucion_diaria(fecha_inicio, fecha_fin, usuario_email=None,
                                  vendedor_asignado=None, resultado_filtro=None):
    """Crea gráfica de evolución diaria con filtros múltiples"""
    
    try:
        # Obtener datos con filtros
        evolucion_data = st.session_state.db.obtener_evolucion_diaria_gestiones(
            fecha_inicio, fecha_fin, usuario_email, vendedor_asignado, resultado_filtro
        )
        
        if not evolucion_data:
            return None
        
        # Preparar datos
        fechas = [item[0] for item in evolucion_data]
        total_gestiones = [item[1] for item in evolucion_data]
        clientes_unicos = [item[2] for item in evolucion_data]
        
        fechas_formateadas = [fecha.split('-')[-1] + '/' + fecha.split('-')[-2] 
                            if '-' in fecha else fecha for fecha in fechas]
        
        # Título personalizado
        titulo = f"📈 Evolución Diaria de Gestiones ({fecha_inicio} a {fecha_fin})"
        
        if vendedor_asignado and vendedor_asignado != "Todos los vendedores":
            titulo = f"📈 Evolución Diaria - {vendedor_asignado} ({fecha_inicio} a {fecha_fin})"
        elif usuario_email and usuario_email != "Todos los vendedores":
            usuario_nombre = usuario_email.split('@')[0]
            titulo = f"📈 Evolución Diaria - {usuario_nombre} ({fecha_inicio} a {fecha_fin})"
        
        if resultado_filtro and resultado_filtro != "Todos los resultados":
            titulo = f"📈 {resultado_filtro} - Diario ({fecha_inicio} a {fecha_fin})"
        
        # Crear gráfica
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=fechas_formateadas,
            y=total_gestiones,
            mode='lines+markers+text',
            name='Total Gestiones',
            line=dict(color='#00B3B0', width=4),
            marker=dict(size=8, color='#00B3B0'),
            text=total_gestiones,
            textposition='top center',
            hovertemplate='<b>%{x}</b><br>Total: %{y} gestiones<extra></extra>'
        ))
        
        fig.add_trace(go.Scatter(
            x=fechas_formateadas,
            y=clientes_unicos,
            mode='lines+markers',
            name='Clientes Únicos',
            line=dict(color='#f59e0b', width=3, dash='dash'),
            marker=dict(size=6, color='#f59e0b'),
            hovertemplate='<b>%{x}</b><br>Clientes: %{y}<extra></extra>'
        ))
        
        # Actualizar diseño
        fig.update_layout(
            title=titulo,
            plot_bgcolor='#1e293b',
            paper_bgcolor='#1e293b',
            font_color='#e2e8f0',
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            xaxis=dict(showgrid=True, gridcolor='#334155', tickangle=-45),
            yaxis=dict(showgrid=True, gridcolor='#334155')
        )
        
        return fig
        
    except Exception as e:
        print(f"Error creando gráfica de evolución diaria: {e}")
        return None

def crear_grafica_evolucion_historica(fecha_inicio, fecha_fin, usuario_email=None,
                                     vendedor_asignado=None, resultado_filtro=None):
    """Crea gráfica de evolución histórica con filtros múltiples"""
    
    try:
        # Obtener datos con filtros
        datos_historicos, max_historico = st.session_state.db.obtener_evolucion_historica_gestiones(
            fecha_inicio, fecha_fin, usuario_email, vendedor_asignado, resultado_filtro
        )
        
        if not datos_historicos:
            return None
        
        # Preparar datos
        meses = [f"{item[0][5:7]}/{item[0][2:4]}" for item in datos_historicos]
        totales = [item[1] for item in datos_historicos]
        
        # Título personalizado
        titulo = f"📅 Evolución Histórica ({fecha_inicio} a {fecha_fin})"
        
        if vendedor_asignado and vendedor_asignado != "Todos los vendedores":
            titulo = f"📅 Evolución Histórica - {vendedor_asignado} ({fecha_inicio} a {fecha_fin})"
        elif usuario_email and usuario_email != "Todos los vendedores":
            usuario_nombre = usuario_email.split('@')[0]
            titulo = f"📅 Evolución Histórica - {usuario_nombre} ({fecha_inicio} a {fecha_fin})"
        
        if resultado_filtro and resultado_filtro != "Todos los resultados":
            titulo = f"📅 {resultado_filtro} - Histórico ({fecha_inicio} a {fecha_fin})"
        
        # Crear gráfica
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=meses,
            y=totales,
            mode='lines+markers+text',
            name='Gestiones Mensuales',
            line=dict(color='#00B3B0', width=4),
            marker=dict(size=8, color='#00B3B0'),
            text=totales,
            textposition='top center',
            textfont=dict(color='#00B3B0', size=10),
            hovertemplate='<b>%{x}</b><br>Gestiones: %{y}<extra></extra>'
        ))
        
        if max_historico > 0:
            fig.add_hline(
                y=max_historico,
                line_dash="dash",
                line_color="#F57C00",
                annotation_text=f"Máximo Histórico: {max_historico}",
                annotation_font_color="#F57C00"
            )
        
        # Actualizar diseño
        fig.update_layout(
            title=titulo,
            plot_bgcolor='#1e293b',
            paper_bgcolor='#1e293b',
            font_color='#e2e8f0',
            height=400,
            showlegend=False,
            xaxis=dict(showgrid=True, gridcolor='#334155', tickangle=-45),
            yaxis=dict(showgrid=True, gridcolor='#334155', title='Total de Gestiones')
        )
        
        return fig
        
    except Exception as e:
        print(f"Error creando gráfica histórica: {e}")
        return None

def mostrar_tabla_detallada(fecha_inicio, fecha_fin, usuario_email=None,
                           vendedor_asignado=None, resultado_filtro=None):
    """Muestra tabla detallada con todos los filtros aplicados"""
    
    st.subheader("📋 Gestiones del Período")
    
    try:
        # Obtener gestiones con filtros
        gestiones = st.session_state.db.obtener_gestiones_por_periodo(
            fecha_inicio, fecha_fin, usuario_email, vendedor_asignado, resultado_filtro
        )
        
        if gestiones.empty:
            st.info(f"📝 No hay gestiones registradas con los filtros aplicados")
            return
        
        # Mostrar información de filtros
        filtro_info = f"📅 Período: {fecha_inicio} a {fecha_fin}"
        
        if usuario_email and usuario_email != "Todos los vendedores":
            usuario_nombre = usuario_email.split('@')[0]
            filtro_info += f" | 👤 Gestor: {usuario_nombre}"
        
        if vendedor_asignado and vendedor_asignado != "Todos los vendedores":
            filtro_info += f" | 👔 Vendedor: {vendedor_asignado}"
        
        if resultado_filtro and resultado_filtro != "Todos los resultados":
            filtro_info += f" | 🎯 Resultado: {resultado_filtro}"
        
        st.caption(filtro_info)
        
        # Limitar a 20 más recientes
        gestiones_recientes = gestiones.head(20).copy()
        
        # Formatear columnas
        columnas_mostrar = ['fecha_contacto', 'usuario', 'razon_social_cliente', 'tipo_contacto', 'resultado']
        columnas_existentes = [col for col in columnas_mostrar if col in gestiones_recientes.columns]
        
        df_display = gestiones_recientes[columnas_existentes].copy()
        
        # Formatear usuario
        if 'usuario' in df_display.columns:
            df_display['usuario'] = df_display['usuario'].apply(
                lambda x: x.split('@')[0] if '@' in str(x) else str(x)
            )
        
        # Renombrar columnas
        mapeo_nombres = {
            'fecha_contacto': 'Fecha',
            'usuario': 'Usuario',
            'razon_social_cliente': 'Cliente',
            'tipo_contacto': 'Tipo Contacto',
            'resultado': 'Resultado'
        }
        
        renombrar_dict = {old: new for old, new in mapeo_nombres.items() if old in df_display.columns}
        df_display = df_display.rename(columns=renombrar_dict)
        
        # Mostrar tabla
        st.dataframe(
            df_display,
            use_container_width=True,
            height=400,
            hide_index=True,
            column_config={
                'Usuario': st.column_config.TextColumn(width="small"),
                'Fecha': st.column_config.DateColumn(format="DD/MM/YYYY"),
                'Cliente': st.column_config.TextColumn(width="medium"),
                'Resultado': st.column_config.TextColumn(width="large")
            }
        )
        
        # Estadísticas
        total_gestiones = len(gestiones)
        clientes_unicos = gestiones['nit_cliente'].nunique()
        usuarios_unicos = gestiones['usuario'].nunique() if 'usuario' in gestiones.columns else 1
        
        st.caption(f"📊 Resumen: {total_gestiones} gestiones | {clientes_unicos} clientes | {usuarios_unicos} usuarios")
        
    except Exception as e:
        st.error(f"❌ Error cargando tabla de gestiones: {str(e)}")

def mostrar_botones_accion_gestion():
    """Muestra botones de acción para el módulo de gestión"""
    
    st.markdown("---")
    st.subheader("🚀 Acciones")
    
    col1, col2, col_espacio, col3 = st.columns([1, 1, 1, 1])
    
    with col1:
        if st.button("📤 Exportar Reporte", use_container_width=True, help="Exportar análisis completo a Excel"):
            exportar_reporte_gestion()
    
    with col2:
        if st.button("🔄 Actualizar Datos", use_container_width=True, type="primary", help="Actualizar todos los datos del análisis"):
            st.rerun()
    
    with col3:
        if st.button("📊 Ver Todas las Gestiones", use_container_width=True, help="Ver el historial completo de gestiones"):
            # Navegar a la sección de gestión
            st.session_state.section = "📞 Gestión"
            st.rerun()

def exportar_reporte_gestion():
    """Exporta el reporte de análisis de gestión a Excel - VERSIÓN CON FILTROS DINÁMICOS"""
    
    try:
        import io
        
        # Obtener el período activo actual
        periodo_seleccionado = st.session_state.get('filtro_periodo_gestion', 'Mes Actual')
        fecha_inicio_personalizada = st.session_state.get('fecha_inicio_personalizada')
        fecha_fin_personalizada = st.session_state.get('fecha_fin_personalizada')
        
        # Calcular rango de fechas
        fecha_inicio, fecha_fin = st.session_state.db.obtener_rango_fechas_por_periodo(
            periodo_seleccionado,
            fecha_inicio_personalizada,
            fecha_fin_personalizada
        )
        
        # Obtener datos para exportar CON FILTROS DE FECHA
        gestiones_periodo = st.session_state.db.obtener_gestiones_por_periodo(fecha_inicio, fecha_fin)
        progreso_data = st.session_state.db.obtener_progreso_gestion(fecha_inicio, fecha_fin)
        estadisticas = st.session_state.db.obtener_estadisticas_resultados_filtrado(fecha_inicio, fecha_fin)
        
        # Crear Excel en memoria
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja 1: Gestiones del período
            if not gestiones_periodo.empty:
                gestiones_periodo.to_excel(writer, sheet_name='Gestiones_Periodo', index=False)
            
            # Hoja 2: Métricas de progreso
            metricas_df = pd.DataFrame([progreso_data])
            metricas_df.to_excel(writer, sheet_name='Metricas_Progreso', index=False)
            
            # Hoja 3: Estadísticas de resultados
            if estadisticas:
                stats_df = pd.DataFrame(list(estadisticas.items()), columns=['Categoria', 'Cantidad'])
                stats_df.to_excel(writer, sheet_name='Estadisticas_Resultados', index=False)
            
            # Hoja 4: Resumen ejecutivo
            resumen_data = {
                'Metrica': [
                    'Período del Reporte',
                    'Total Clientes en Cartera',
                    'Clientes Gestionados', 
                    'Porcentaje de Gestión',
                    'Clientes en Mora',
                    'Clientes en Mora Gestionados',
                    'Porcentaje Mora Gestionada',
                    'Total Gestiones Período',
                    'Clientes Únicos Gestionados',
                    'Tasa de Contacto'
                ],
                'Valor': [
                    f"{fecha_inicio} a {fecha_fin}",
                    progreso_data.get('total_clientes', 0),
                    progreso_data.get('clientes_gestionados', 0),
                    f"{progreso_data.get('porcentaje_general', 0):.1f}%",
                    progreso_data.get('clientes_mora', 0),
                    progreso_data.get('clientes_mora_gestionados', 0),
                    f"{progreso_data.get('porcentaje_mora', 0):.1f}%",
                    len(gestiones_periodo) if not gestiones_periodo.empty else 0,
                    gestiones_periodo['nit_cliente'].nunique() if not gestiones_periodo.empty else 0,
                    f"{(progreso_data.get('clientes_gestionados', 0) / progreso_data.get('total_clientes', 1) * 100) if progreso_data.get('total_clientes', 0) > 0 else 0:.1f}%"
                ]
            }
            resumen_df = pd.DataFrame(resumen_data)
            resumen_df.to_excel(writer, sheet_name='Resumen_Ejecutivo', index=False)
        
        output.seek(0)
        
        # Botón de descarga
        st.download_button(
            label="⬇️ Descargar Reporte Excel",
            data=output.getvalue(),
            file_name=f"reporte_gestion_{fecha_inicio}_a_{fecha_fin}_{datetime.now().strftime('%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"❌ Error exportando reporte: {str(e)}")