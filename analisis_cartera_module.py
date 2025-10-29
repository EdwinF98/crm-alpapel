# analisis_cartera_module.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import io

def analisis_cartera_section():
    """Sección completa de Análisis de Cartera - VERSIÓN CORREGIDA"""
    
    st.header("📊 Análisis de Cartera")
    
    # ✅ INICIALIZAR ESTADO DE GRÁFICAS ACTIVAS
    if 'graficas_analisis_activas' not in st.session_state:
        st.session_state.graficas_analisis_activas = [
            'chart1', 'chart2', 'chart3', 'chart4', 'chart5', 
            'chart6', 'chart7', 'chart8', 'chart9'
        ]
    
    if 'datos_analisis_filtrados' not in st.session_state:
        st.session_state.datos_analisis_filtrados = pd.DataFrame()
    
    try:
        # 1. FILTROS PRINCIPALES
        mostrar_filtros_analisis()
        
        # 2. SELECTOR DE GRÁFICAS (CORREGIDO)
        mostrar_selector_graficas()
        
        # 3. MÉTRICAS RÁPIDAS
        mostrar_metricas_rapidas()
        
        # 4. GRÁFICAS PRINCIPALES
        mostrar_graficas_principales()
        
        # 5. BOTONES DE ACCIÓN
        mostrar_botones_accion()
        
    except Exception as e:
        st.error(f"❌ Error en análisis de cartera: {str(e)}")
        st.info("💡 Si el error persiste, intenta actualizar la página o contactar al administrador")

def mostrar_filtros_analisis():
    """Muestra los filtros de análisis - VERSIÓN COMPACTA Y RESPONSIVE"""
    
    st.subheader("🔍 Filtros de Análisis")
    
    # Usar columnas para filtros compactos
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Filtro de vendedor
        vendedores_disponibles = st.session_state.auth_manager.get_available_vendedores()
        filtro_vendedor = st.selectbox(
            "👤 Vendedor:",
            options=["Todos los vendedores"] + [v for v in vendedores_disponibles if v != "Todos los vendedores"],
            key="filtro_vendedor_analisis"
        )
    
    with col2:
        # Filtro de condición de pago
        condiciones = ["Todas las condiciones", "CON", "CO1", "10D", "15D", "30D", "45D", "60D", "75D", "90D", "NC"]
        filtro_condicion = st.selectbox(
            "💰 Condición:",
            options=condiciones,
            key="filtro_condicion_analisis"
        )
    
    with col3:
        # Filtro de días vencidos
        opciones_dias = [
            "Todos los días",
            "0 días (Corriente)", 
            "1-30 días",
            "31-60 días",
            "61-90 días", 
            "+90 días"
        ]
        filtro_dias = st.selectbox(
            "⏰ Días:",
            options=opciones_dias,
            key="filtro_dias_analisis"
        )
    
    with col4:
        # Filtro de ciudad
        ciudades_df = st.session_state.db.obtener_ciudades()
        ciudades_opciones = ["Todas las ciudades"] + ciudades_df['ciudad'].dropna().unique().tolist()
        filtro_ciudad = st.selectbox(
            "🏙️ Ciudad:",
            options=ciudades_opciones,
            key="filtro_ciudad_analisis"
        )
    
    # Botón de aplicar filtros
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    
    with col_btn1:
        if st.button("🔄 Aplicar Filtros", use_container_width=True, type="primary"):
            aplicar_filtros_analisis(filtro_vendedor, filtro_condicion, filtro_dias, filtro_ciudad)
    
    with col_btn2:
        if st.button("🧹 Limpiar Filtros", use_container_width=True):
            limpiar_filtros_analisis()
    
    with col_btn3:
        if st.session_state.datos_analisis_filtrados is not None and not st.session_state.datos_analisis_filtrados.empty:
            st.info(f"📊 {len(st.session_state.datos_analisis_filtrados)} registros filtrados")

def aplicar_filtros_analisis(vendedor, condicion, dias, ciudad):
    """Aplica los filtros y actualiza los datos"""
    try:
        with st.spinner("🔄 Aplicando filtros..."):
            datos_filtrados = obtener_datos_analisis_filtrados(vendedor, condicion, dias, ciudad)
            st.session_state.datos_analisis_filtrados = datos_filtrados
            st.success("✅ Filtros aplicados correctamente")
            st.rerun()
    except Exception as e:
        st.error(f"❌ Error aplicando filtros: {str(e)}")

def limpiar_filtros_analisis():
    """Limpia todos los filtros"""
    st.session_state.datos_analisis_filtrados = pd.DataFrame()
    st.rerun()

def obtener_datos_analisis_filtrados(vendedor, condicion, dias_filtro, ciudad):
    """Obtiene datos filtrados para análisis - MÉTODO REUTILIZADO DE PYSIDE6"""
    try:
        # Obtener cartera completa (ya viene filtrada por usuario)
        cartera = st.session_state.db.obtener_cartera_actual()
        
        if cartera.empty:
            return pd.DataFrame()
        
        # Aplicar filtros adicionales
        if vendedor != "Todos los vendedores":
            cartera = cartera[cartera['nombre_vendedor'] == vendedor]
        
        if condicion != "Todas las condiciones":
            cartera = cartera[cartera['condicion_pago'] == condicion]
        
        # Filtrar por ciudad
        if ciudad != "Todas las ciudades":
            clientes = st.session_state.db.obtener_clientes()
            cartera = cartera.merge(
                clientes[['nit_cliente', 'ciudad']], 
                on='nit_cliente', 
                how='left'
            )
            cartera = cartera[cartera['ciudad_y'] == ciudad]
        
        # Filtrar por días vencidos
        if dias_filtro != "Todos los días":
            if dias_filtro == "0 días (Corriente)":
                cartera = cartera[cartera['dias_vencidos'] == 0]
            elif dias_filtro == "1-30 días":
                cartera = cartera[(cartera['dias_vencidos'] >= 1) & (cartera['dias_vencidos'] <= 30)]
            elif dias_filtro == "31-60 días":
                cartera = cartera[(cartera['dias_vencidos'] >= 31) & (cartera['dias_vencidos'] <= 60)]
            elif dias_filtro == "61-90 días":
                cartera = cartera[(cartera['dias_vencidos'] >= 61) & (cartera['dias_vencidos'] <= 90)]
            elif dias_filtro == "+90 días":
                cartera = cartera[cartera['dias_vencidos'] > 90]
        
        return cartera
        
    except Exception as e:
        st.error(f"Error obteniendo datos filtrados: {e}")
        return pd.DataFrame()

def mostrar_selector_graficas():
    """Selector de gráficas con checkboxes - VERSIÓN CORREGIDA"""
    
    st.subheader("🎛️ Control de Gráficas")
    
    # Inicializar estado si no existe
    if 'graficas_analisis_activas' not in st.session_state:
        st.session_state.graficas_analisis_activas = [
            'chart1', 'chart2', 'chart3', 'chart4', 'chart5', 
            'chart6', 'chart7', 'chart8', 'chart9'
        ]
    
    # Definir configuración de gráficas
    graficas_config = {
        'chart1': '📊 Distribución por Estado',
        'chart2': '📈 Top 10 Clientes Mora', 
        'chart3': '👥 Cartera por Vendedor',
        'chart4': '💰 Condiciones de Pago',
        'chart5': '📅 Evolución + Proyección',
        'chart6': '📊 Concentración 20/80',
        'chart7': '📈 Envejecimiento Detallado',
        'chart8': '🏙️ Análisis Geográfico',
        'chart9': '💰 Proyección por Crédito'
    }
    
    # Crear checkboxes en columnas responsivas
    cols = st.columns(3)
    col_index = 0
    
    # Lista temporal para almacenar selecciones actuales
    selecciones_actuales = []
    
    for chart_id, chart_name in graficas_config.items():
        with cols[col_index]:
            # Crear checkbox con estado actual
            activa = st.checkbox(
                chart_name,
                value=chart_id in st.session_state.graficas_analisis_activas,
                key=f"checkbox_{chart_id}",
                help=f"Mostrar/ocultar {chart_name}"
            )
            
            if activa:
                selecciones_actuales.append(chart_id)
        
        col_index = (col_index + 1) % 3
    
    # **BOTONES DE ACCIÓN - CORREGIDOS**
    st.markdown("---")
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button("✅ Seleccionar Todas", use_container_width=True, key="btn_todas"):
            # Actualizar estado inmediatamente
            st.session_state.graficas_analisis_activas = list(graficas_config.keys())
            st.rerun()
    
    with col_btn2:
        if st.button("❌ Deseleccionar Todas", use_container_width=True, key="btn_ninguna"):
            # Limpiar todas las selecciones
            st.session_state.graficas_analisis_activas = []
            st.rerun()
    
    with col_btn3:
        if st.button("🔄 Aplicar Cambios", use_container_width=True, key="btn_aplicar", type="primary"):
            # Aplicar selecciones actuales de los checkboxes
            st.session_state.graficas_analisis_activas = selecciones_actuales
            st.rerun()
    
    # **ACTUALIZACIÓN AUTOMÁTICA**: Si hay cambios en los checkboxes, aplicar inmediatamente
    if selecciones_actuales != st.session_state.graficas_analisis_activas:
        st.session_state.graficas_analisis_activas = selecciones_actuales
        # No hacemos rerun automático para evitar loops, pero los cambios se aplican al siguiente rerun

def mostrar_metricas_rapidas():
    """Muestra las métricas rápidas del análisis"""
    
    if st.session_state.datos_analisis_filtrados is None or st.session_state.datos_analisis_filtrados.empty:
        # Obtener datos básicos si no hay filtros aplicados
        datos = st.session_state.db.obtener_cartera_actual()
    else:
        datos = st.session_state.datos_analisis_filtrados
    
    if datos.empty:
        st.warning("📭 No hay datos para mostrar métricas")
        return
    
    # Calcular métricas
    total_cartera = datos['total_cop'].sum()
    cartera_mora = datos[datos['dias_vencidos'] > 0]['total_cop'].sum()
    clientes_totales = datos['nit_cliente'].nunique()
    clientes_mora = datos[datos['dias_vencidos'] > 0]['nit_cliente'].nunique()
    
    # Mostrar en columnas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "CARTERA TOTAL",
            f"${total_cartera:,.0f}",
            help="Valor total de la cartera filtrada"
        )
    
    with col2:
        st.metric(
            "CARTERA EN MORA", 
            f"${cartera_mora:,.0f}",
            delta=f"{(cartera_mora/total_cartera*100) if total_cartera > 0 else 0:.1f}%",
            delta_color="inverse",
            help="Cartera con días vencidos > 0"
        )
    
    with col3:
        st.metric(
            "TOTAL CLIENTES",
            f"{clientes_totales:,}",
            help="Número total de clientes únicos"
        )
    
    with col4:
        st.metric(
            "CLIENTES EN MORA",
            f"{clientes_mora:,}",
            delta=f"{(clientes_mora/clientes_totales*100) if clientes_totales > 0 else 0:.1f}%",
            delta_color="inverse",
            help="Clientes con cartera vencida"
        )

def mostrar_graficas_principales():
    """Muestra las gráficas principales según selección - VERSIÓN CORREGIDA"""
    
    # ✅ VERIFICAR QUE HAY GRÁFICAS SELECCIONADAS
    if not st.session_state.graficas_analisis_activas:
        st.info("ℹ️ Selecciona al menos una gráfica para visualizar")
        return
    
    if st.session_state.datos_analisis_filtrados is None or st.session_state.datos_analisis_filtrados.empty:
        st.warning("📭 Aplica filtros primero para visualizar las gráficas")
        return
    
    datos = st.session_state.datos_analisis_filtrados
    
    # ✅ Mapeo de funciones de gráficas CORREGIDO
    graficas_functions = {
        'chart1': crear_grafica_distribucion_estado,
        'chart2': crear_grafica_top_clientes_mora,
        'chart3': crear_grafica_cartera_vendedor_condiciones,
        'chart4': crear_grafica_condiciones_pago,
        'chart5': crear_grafica_evolucion_proyeccion,
        'chart6': crear_grafica_concentracion_cartera,
        'chart7': crear_grafica_envejecimiento_detallado,
        'chart8': crear_grafica_analisis_geografico,
        'chart9': crear_grafica_proyeccion_credito
    }
    
    # ✅ Mostrar contador de gráficas activas
    st.info(f"📊 Mostrando {len(st.session_state.graficas_analisis_activas)} gráficas activas")
    
    # ✅ Mostrar gráficas en orden
    for chart_id in st.session_state.graficas_analisis_activas:
        if chart_id in graficas_functions:
            try:
                graficas_functions[chart_id](datos)
                st.markdown("---")  # Separador entre gráficas
            except Exception as e:
                st.error(f"❌ Error creando gráfica {chart_id}: {str(e)}")

def crear_grafica_distribucion_estado(datos):
    """Gráfica 1: Distribución por Estado de Cartera"""
    
    st.subheader("📊 Distribución por Estado de Cartera")
    
    if datos.empty:
        st.info("No hay datos para mostrar la distribución")
        return
    
    # Calcular distribución por estado
    categorias_estado = ['Corriente', '1-30 días', '31-60 días', '61-90 días', '+90 días']
    
    valores_estado = [
        datos[datos['dias_vencidos'] == 0]['total_cop'].sum(),
        datos[(datos['dias_vencidos'] >= 1) & (datos['dias_vencidos'] <= 30)]['total_cop'].sum(),
        datos[(datos['dias_vencidos'] >= 31) & (datos['dias_vencidos'] <= 60)]['total_cop'].sum(),
        datos[(datos['dias_vencidos'] >= 61) & (datos['dias_vencidos'] <= 90)]['total_cop'].sum(),
        datos[datos['dias_vencidos'] > 90]['total_cop'].sum()
    ]
    
    if not any(val > 0 for val in valores_estado):
        st.info("No hay valores positivos para mostrar")
        return
    
    # Crear gráfica Plotly
    fig = go.Figure()
    
    colors = ['#10b981', '#f59e0b', '#f97316', '#dc2626', '#991b1b']
    
    fig.add_trace(go.Bar(
        x=categorias_estado,
        y=valores_estado,
        marker_color=colors,
        text=[f'${v/1e6:.1f}M' if v >= 1e6 else f'${v/1e3:.0f}K' for v in valores_estado],
        textposition='auto',
    ))
    
    fig.update_layout(
        title="Distribución de Cartera por Estado",
        xaxis_title="Estado de Cartera",
        yaxis_title="Valor COP",
        template="plotly_dark",
        height=500,
        showlegend=False
    )
    
    fig.update_yaxes(tickprefix='$', tickformat='.0s')
    
    st.plotly_chart(fig, use_container_width=True)

def crear_grafica_top_clientes_mora(datos):
    """Gráfica 2: Top 10 Clientes con Mayor Mora"""
    
    st.subheader("⚠️ Top 10 Clientes con Mayor Mora")
    
    # Filtrar solo clientes con mora
    datos_mora = datos[datos['dias_vencidos'] > 0]
    
    if datos_mora.empty:
        st.info("No hay clientes con mora para mostrar")
        return
    
    # Agrupar por cliente y sumar mora
    top_clientes = datos_mora.groupby('razon_social_cliente').agg({
        'total_cop': 'sum',
        'dias_vencidos': 'max'
    }).nlargest(10, 'total_cop')
    
    if top_clientes.empty:
        st.info("No hay datos para top clientes")
        return
    
    # Invertir para que el mayor quede arriba
    top_clientes = top_clientes.iloc[::-1]
    
    # Crear gráfica
    clientes_nombres = [nombre[:20] + '...' if len(nombre) > 20 else nombre 
                       for nombre in top_clientes.index]
    valores = top_clientes['total_cop'].values
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=clientes_nombres,
        x=valores,
        orientation='h',
        marker_color='#ef4444',
        text=[f'${v/1e6:.1f}M' for v in valores],
        textposition='auto',
    ))
    
    fig.update_layout(
        title="Top 10 Clientes con Mayor Mora",
        xaxis_title="Valor en Mora (COP)",
        yaxis_title="Cliente",
        template="plotly_dark",
        height=500
    )
    
    fig.update_xaxes(tickprefix='$', tickformat='.0s')
    
    st.plotly_chart(fig, use_container_width=True)

def crear_grafica_cartera_vendedor_condiciones(datos):
    """Crea gráfica de cartera por vendedor y condiciones de pago"""
    try:
        st.subheader("👥 Cartera por Vendedor y Condiciones")
        
        if datos.empty:
            st.info("No hay datos para mostrar la cartera por vendedor")
            return
        
        # Unir CO1 y CON como "CONTADO" (igual que en PySide6)
        datos_modificados = datos.copy()
        datos_modificados['condicion_display'] = datos_modificados['condicion_pago'].apply(
            lambda x: 'CONTADO' if str(x).upper() in ['CO1', 'CON'] else str(x)
        )
        
        # Agrupar por vendedor y condición
        agrupacion = datos_modificados.groupby(['nombre_vendedor', 'condicion_display'])['total_cop'].sum().reset_index()
        
        # Pivot para tener vendedores como filas
        pivot_data = agrupacion.pivot(index='nombre_vendedor', columns='condicion_display', values='total_cop').fillna(0)
        
        if pivot_data.empty:
            st.info("No hay datos para la gráfica de vendedores")
            return
        
        # Ordenar por total (mayor a menor)
        total_por_vendedor = pivot_data.sum(axis=1)
        pivot_data = pivot_data.loc[total_por_vendedor.sort_values(ascending=False).index]
        
        # Limitar a condiciones principales (top 6 por valor)
        condiciones_totales = pivot_data.sum().sort_values(ascending=False)
        condiciones_principales = condiciones_totales.head(6).index
        pivot_data = pivot_data[condiciones_principales]
        
        # Crear gráfica con Plotly
        import plotly.graph_objects as go
        
        # Preparar datos
        vendedores = []
        for vendedor in pivot_data.index:
            if len(vendedor) > 15:
                vendedores.append(vendedor[:12] + '...')
            else:
                vendedores.append(vendedor)
        
        condiciones = pivot_data.columns
        total_por_vendedor = pivot_data.sum(axis=1)
        total_general = total_por_vendedor.sum()
        
        # Colores para condiciones
        colors = ['#00B3B0', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#10b981']
        
        # Crear gráfica de barras apiladas
        fig = go.Figure()
        
        # Añadir cada condición como una barra apilada
        for i, condicion in enumerate(condiciones):
            valores = pivot_data[condicion].values / 1000000  # En millones
            fig.add_trace(go.Bar(
                name=condicion,
                x=vendedores,
                y=valores,
                marker_color=colors[i % len(colors)],
                hovertemplate='<b>%{x}</b><br>Condición: %{meta[0]}<br>Valor: $%{y:.1f}M<extra></extra>',
                meta=[condicion] * len(vendedores)
            ))
        
        # Añadir anotaciones con totales y porcentajes
        for i, (vendedor, total_vendedor) in enumerate(zip(vendedores, total_por_vendedor)):
            porcentaje_vendedor = (total_vendedor / total_general) * 100
            fig.add_annotation(
                x=vendedor,
                y=total_vendedor / 1000000 + (max(total_por_vendedor) / 1000000 * 0.02),
                text=f'${total_vendedor/1000000:.1f}M<br>({porcentaje_vendedor:.1f}%)',
                showarrow=False,
                font=dict(color='#e2e8f0', size=9, weight='bold'),
                bgcolor='#1e293b',
                bordercolor='#00B3B0',
                borderwidth=1,
                borderpad=2
            )
        
        # Actualizar diseño
        fig.update_layout(
            barmode='stack',
            height=600,
            title="Cartera por Vendedor - Condiciones de Pago",
            xaxis_title="Vendedor",
            yaxis_title="Valor COP (Millones)",
            plot_bgcolor='#1e293b',
            paper_bgcolor='#1e293b',
            font=dict(color='#e2e8f0'),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                bgcolor='rgba(30, 41, 59, 0.8)'
            ),
            xaxis=dict(tickangle=45)
        )
        
        # Formatear eje Y
        fig.update_yaxes(tickprefix="$", ticksuffix="M")
        
        # Mostrar gráfica
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar tabla de resumen
        with st.expander("📋 Ver Detalles por Vendedor"):
            resumen_data = []
            for vendedor, total in total_por_vendedor.items():
                porcentaje = (total / total_general) * 100
                resumen_data.append({
                    'Vendedor': vendedor,
                    'Cartera Total (M)': f"${total/1000000:.1f}M",
                    'Porcentaje': f"{porcentaje:.1f}%",
                    'Condiciones Activas': len([c for c in condiciones if pivot_data.loc[vendedor, c] > 0])
                })
            
            import pandas as pd
            df_resumen = pd.DataFrame(resumen_data)
            st.dataframe(df_resumen, use_container_width=True, hide_index=True)
        
        # Estadísticas clave
        col1, col2, col3 = st.columns(3)
        
        with col1:
            vendedor_top = pivot_data.index[0]
            st.metric("Vendedor con Mayor Cartera", vendedor_top[:20] + '...' if len(vendedor_top) > 20 else vendedor_top)
        
        with col2:
            total_vendedores = len(pivot_data)
            st.metric("Total Vendedores", total_vendedores)
        
        with col3:
            condicion_mas_comun = condiciones_totales.index[0]
            st.metric("Condición Más Común", condicion_mas_comun)
            
    except Exception as e:
        st.error(f"❌ Error creando gráfica de vendedores: {str(e)}")

def crear_grafica_cartera_vendedor(datos):
    """Gráfica 3: Cartera por Vendedor y Condiciones"""
    
    st.subheader("👥 Cartera por Vendedor y Condiciones")
    
    if datos.empty:
        st.info("No hay datos para mostrar")
        return
    
    # Unir CO1 y CON como "CONTADO"
    datos_modificados = datos.copy()
    datos_modificados['condicion_display'] = datos_modificados['condicion_pago'].apply(
        lambda x: 'CONTADO' if str(x).upper() in ['CO1', 'CON'] else str(x)
    )
    
    # Agrupar por vendedor y condición
    agrupacion = datos_modificados.groupby(['nombre_vendedor', 'condicion_display'])['total_cop'].sum().reset_index()
    
    # Pivot para tener vendedores como filas
    pivot_data = agrupacion.pivot(index='nombre_vendedor', columns='condicion_display', values='total_cop').fillna(0)
    
    if pivot_data.empty:
        st.info("No hay datos para la gráfica")
        return
    
    # Ordenar por total
    total_por_vendedor = pivot_data.sum(axis=1)
    pivot_data = pivot_data.loc[total_por_vendedor.sort_values(ascending=False).index]
    
    # Limitar a condiciones principales
    condiciones_totales = pivot_data.sum().sort_values(ascending=False)
    condiciones_principales = condiciones_totales.head(6).index
    pivot_data = pivot_data[condiciones_principales]
    
    # Crear gráfica de barras apiladas
    fig = go.Figure()
    
    # Colores para condiciones
    colors = ['#00B3B0', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#10b981']
    
    for i, condicion in enumerate(pivot_data.columns):
        fig.add_trace(go.Bar(
            name=condicion,
            x=pivot_data.index,
            y=pivot_data[condicion],
            marker_color=colors[i % len(colors)]
        ))
    
    fig.update_layout(
        title="Cartera por Vendedor - Condiciones de Pago",
        xaxis_title="Vendedor",
        yaxis_title="Valor COP",
        template="plotly_dark",
        height=600,
        barmode='stack'
    )
    
    fig.update_yaxes(tickprefix='$', tickformat='.0s')
    fig.update_xaxes(tickangle=45)
    
    st.plotly_chart(fig, use_container_width=True)

def crear_grafica_condiciones_pago(datos):
    """Gráfica 4: Distribución por Condición de Pago"""
    
    st.subheader("💰 Distribución por Condición de Pago")
    
    if datos.empty:
        st.info("No hay datos para mostrar")
        return
    
    # Unir CO1 y CON como "CONTADO"
    datos_modificados = datos.copy()
    datos_modificados['condicion_display'] = datos_modificados['condicion_pago'].apply(
        lambda x: 'CONTADO' if str(x).upper() in ['CO1', 'CON'] else str(x)
    )
    
    # Agrupar por condición
    distribucion = datos_modificados.groupby('condicion_display').agg({
        'total_cop': 'sum',
        'nit_cliente': 'nunique'
    }).sort_values('total_cop', ascending=False)
    
    if distribucion.empty:
        st.info("No hay datos de condiciones")
        return
    
    # Invertir para gráfica horizontal
    distribucion = distribucion.iloc[::-1]
    
    # Crear gráfica
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=distribucion.index,
        x=distribucion['total_cop'],
        orientation='h',
        marker_color='#00B3B0',
        text=[f'${v/1e6:.1f}M' for v in distribucion['total_cop']],
        textposition='auto',
    ))
    
    fig.update_layout(
        title="Distribución por Condición de Pago",
        xaxis_title="Valor COP",
        yaxis_title="Condición de Pago",
        template="plotly_dark",
        height=500
    )
    
    fig.update_xaxes(tickprefix='$', tickformat='.0s')
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar tabla resumen
    with st.expander("📋 Ver Detalles por Condición"):
        distribucion_display = distribucion.copy()
        distribucion_display['Valor COP'] = distribucion_display['total_cop'].apply(lambda x: f"${x:,.0f}")
        distribucion_display['Porcentaje'] = (distribucion_display['total_cop'] / distribucion_display['total_cop'].sum() * 100).round(1)
        distribucion_display['Porcentaje'] = distribucion_display['Porcentaje'].apply(lambda x: f"{x}%")
        distribucion_display['Clientes'] = distribucion_display['nit_cliente']
        
        st.dataframe(
            distribucion_display[['Valor COP', 'Porcentaje', 'Clientes']],
            use_container_width=True
        )


def crear_grafica_evolucion_proyeccion(datos):
    """Crea gráfica combinada: histórico último año + proyección próximos 4 meses"""
    try:
        st.subheader("📅 Evolución Histórica + Proyección (12M + 4M)")
        
        if datos.empty:
            st.info("No hay datos suficientes para mostrar la evolución")
            return
        
        # Obtener datos históricos del último año
        from datetime import datetime, timedelta
        import pandas as pd
        
        # Procesar datos históricos (últimos 12 meses)
        datos_historicos = datos.copy()
        datos_historicos['fecha_vencimiento'] = pd.to_datetime(datos_historicos['fecha_vencimiento'], errors='coerce')
        
        # Filtrar últimos 12 meses desde la fecha más reciente
        if not datos_historicos.empty:
            fecha_maxima = datos_historicos['fecha_vencimiento'].max()
            fecha_limite = fecha_maxima - timedelta(days=365)
            datos_historicos = datos_historicos[datos_historicos['fecha_vencimiento'] >= fecha_limite]
        
        # Agrupar por mes para histórico
        historico_mensual = []
        if not datos_historicos.empty:
            datos_historicos['mes'] = datos_historicos['fecha_vencimiento'].dt.strftime('%Y-%m')
            agrupado_historico = datos_historicos.groupby('mes').agg({
                'total_cop': 'sum',
                'nit_cliente': 'nunique'
            }).reset_index()
            
            # Ordenar por mes
            agrupado_historico = agrupado_historico.sort_values('mes')
            
            for _, row in agrupado_historico.iterrows():
                historico_mensual.append({
                    'mes': row['mes'],
                    'cartera_total': row['total_cop'],
                    'clientes': row['nit_cliente']
                })
        
        # Proyección futura (próximos 4 meses)
        hoy = datetime.now().date()
        datos_futuro = datos.copy()
        datos_futuro['fecha_vencimiento'] = pd.to_datetime(datos_futuro['fecha_vencimiento'], errors='coerce')
        datos_futuro = datos_futuro[datos_futuro['fecha_vencimiento'] >= pd.to_datetime(hoy)]
        
        proyeccion_futura = []
        
        # Generar próximos 4 meses
        for i in range(4):
            mes_futuro = (hoy.replace(day=1) + timedelta(days=32*i)).replace(day=1)
            mes_nombre = mes_futuro.strftime('%Y-%m')
            mes_display = mes_futuro.strftime('%b %Y')  # Ej: "Oct 2024"
            
            # Calcular cartera que vence en ese mes
            inicio_mes = mes_futuro
            fin_mes = (mes_futuro + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            datos_mes = datos_futuro[
                (datos_futuro['fecha_vencimiento'] >= pd.to_datetime(inicio_mes)) & 
                (datos_futuro['fecha_vencimiento'] <= pd.to_datetime(fin_mes))
            ]
            
            total_mes = datos_mes['total_cop'].sum()
            clientes_mes = datos_mes['nit_cliente'].nunique()
            
            proyeccion_futura.append({
                'mes': mes_nombre,
                'mes_display': mes_display,
                'cartera_total': total_mes,
                'clientes': clientes_mes
            })
        
        # Preparar datos para la gráfica
        meses_combinados = []
        valores_combinados = []
        clientes_combinados = []
        es_proyeccion = []
        display_meses = []
        
        # Agregar datos históricos
        for item in historico_mensual:
            mes_display = datetime.strptime(item['mes'], '%Y-%m').strftime('%b %Y')
            meses_combinados.append(item['mes'])
            display_meses.append(mes_display)
            valores_combinados.append(item['cartera_total'])
            clientes_combinados.append(item['clientes'])
            es_proyeccion.append(False)
        
        # Agregar proyección futura
        for item in proyeccion_futura:
            if item['cartera_total'] > 0:  # Solo agregar meses con valores
                meses_combinados.append(item['mes'])
                display_meses.append(item['mes_display'])
                valores_combinados.append(item['cartera_total'])
                clientes_combinados.append(item['clientes'])
                es_proyeccion.append(True)
        
        if not meses_combinados:
            st.info("No hay datos históricos ni proyección disponible")
            return
        
        # Crear gráfica con Plotly
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        # Crear figura con subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(
                '📈 Evolución de Cartera (Millones COP)',
                '👥 Evolución de Clientes'
            ),
            vertical_spacing=0.1,
            specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
        )
        
        # Separar datos históricos y de proyección
        meses_historicos = [display_meses[i] for i in range(len(display_meses)) if not es_proyeccion[i]]
        valores_historicos = [valores_combinados[i] for i in range(len(valores_combinados)) if not es_proyeccion[i]]
        clientes_historicos = [clientes_combinados[i] for i in range(len(clientes_combinados)) if not es_proyeccion[i]]
        
        meses_proyeccion = [display_meses[i] for i in range(len(display_meses)) if es_proyeccion[i]]
        valores_proyeccion = [valores_combinados[i] for i in range(len(valores_combinados)) if es_proyeccion[i]]
        clientes_proyeccion = [clientes_combinados[i] for i in range(len(clientes_combinados)) if es_proyeccion[i]]
        
        # GRÁFICA 1: CARTERA EN MILLONES
        # Línea histórica (sólida)
        if meses_historicos:
            fig.add_trace(
                go.Scatter(
                    x=meses_historicos,
                    y=[v/1000000 for v in valores_historicos],  # Convertir a millones
                    mode='lines+markers+text',
                    name='Cartera Histórica',
                    line=dict(color='#00B3B0', width=4),
                    marker=dict(size=8, color='#00B3B0'),
                    text=[f'${v/1000000:.1f}M' for v in valores_historicos],
                    textposition='top center',
                    textfont=dict(color='#00B3B0', size=10),
                    hovertemplate='<b>%{x}</b><br>Cartera: $%{y:.1f}M<extra></extra>'
                ),
                row=1, col=1
            )
        
        # Línea de proyección (punteada)
        if meses_proyeccion:
            fig.add_trace(
                go.Scatter(
                    x=meses_proyeccion,
                    y=[v/1000000 for v in valores_proyeccion],  # Convertir a millones
                    mode='lines+markers+text',
                    name='Proyección Vencimientos',
                    line=dict(color='#F57C00', width=4, dash='dash'),
                    marker=dict(size=8, color='#F57C00'),
                    text=[f'${v/1000000:.1f}M' for v in valores_proyeccion],
                    textposition='top center',
                    textfont=dict(color='#F57C00', size=10),
                    hovertemplate='<b>%{x}</b><br>Proyección: $%{y:.1f}M<extra></extra>'
                ),
                row=1, col=1
            )
        
        # GRÁFICA 2: CLIENTES
        # Línea histórica de clientes
        if meses_historicos:
            fig.add_trace(
                go.Scatter(
                    x=meses_historicos,
                    y=clientes_historicos,
                    mode='lines+markers',
                    name='Clientes Históricos',
                    line=dict(color='#00B3B0', width=3),
                    marker=dict(size=6, color='#00B3B0'),
                    hovertemplate='<b>%{x}</b><br>Clientes: %{y}<extra></extra>',
                    showlegend=False
                ),
                row=2, col=1
            )
        
        # Línea de proyección de clientes
        if meses_proyeccion:
            fig.add_trace(
                go.Scatter(
                    x=meses_proyeccion,
                    y=clientes_proyeccion,
                    mode='lines+markers',
                    name='Clientes Proyectados',
                    line=dict(color='#F57C00', width=3, dash='dash'),
                    marker=dict(size=6, color='#F57C00'),
                    hovertemplate='<b>%{x}</b><br>Clientes Proyectados: %{y}<extra></extra>',
                    showlegend=False
                ),
                row=2, col=1
            )
        
        # Actualizar diseño
        fig.update_layout(
            height=700,
            showlegend=True,
            plot_bgcolor='#1e293b',
            paper_bgcolor='#1e293b',
            font=dict(color='#e2e8f0'),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                bgcolor='rgba(30, 41, 59, 0.8)'
            )
        )
        
        # Actualizar ejes - Gráfica 1 (Cartera)
        fig.update_xaxes(title_text="Mes", row=1, col=1, tickangle=-45)
        fig.update_yaxes(
            title_text="Millones COP", 
            row=1, col=1,
            tickprefix="$",
            ticksuffix="M"
        )
        
        # Actualizar ejes - Gráfica 2 (Clientes)
        fig.update_xaxes(title_text="Mes", row=2, col=1, tickangle=-45)
        fig.update_yaxes(title_text="Número de Clientes", row=2, col=1)
        
        # Mostrar gráfica
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar resumen estadístico
        with st.expander("📊 Ver Resumen Estadístico"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if historico_mensual:
                    promedio_historico = sum(valores_historicos) / len(valores_historicos) / 1000000
                    st.metric("Promedio Mensual Histórico", f"${promedio_historico:.1f}M")
            
            with col2:
                if proyeccion_futura:
                    total_proyeccion = sum(valores_proyeccion) / 1000000
                    st.metric("Total Proyección 4M", f"${total_proyeccion:.1f}M")
            
            with col3:
                if historico_mensual and proyeccion_futura:
                    crecimiento = ((sum(valores_proyeccion) - sum(valores_historicos[-4:])) / sum(valores_historicos[-4:]) * 100) if sum(valores_historicos[-4:]) > 0 else 0
                    st.metric("Crecimiento Proyectado", f"{crecimiento:+.1f}%")
        
        # Debug info (opcional)
        st.caption(f"📈 Datos: {len(historico_mensual)} meses históricos + {len(proyeccion_futura)} meses proyección")
            
    except Exception as e:
        st.error(f"❌ Error creando gráfica de evolución + proyección: {str(e)}")
        st.info("💡 Si el error persiste, verifica que los datos de cartera tengan fechas de vencimiento válidas")

def crear_grafica_concentracion_cartera(datos):
    """Gráfica 6: Concentración de Cartera - Principio 20/80"""
    st.subheader("📊 Concentración de Cartera - Principio 20/80")
    
    if datos.empty:
        st.info("No hay datos para mostrar")
        return
    
    # Calcular concentración por cliente
    cartera_por_cliente = datos.groupby(['nit_cliente', 'razon_social_cliente'])['total_cop'].sum().sort_values(ascending=False)
    total_cartera = cartera_por_cliente.sum()
    
    if total_cartera == 0:
        st.info("No hay cartera para analizar")
        return
    
    # Calcular principio 20/80
    acumulado = cartera_por_cliente.cumsum()
    clientes_20 = len(acumulado[acumulado <= total_cartera * 0.2])
    cartera_80 = acumulado.iloc[clientes_20] if clientes_20 < len(acumulado) else acumulado.iloc[-1]
    
    # Top 15 clientes
    top_clientes = cartera_por_cliente.head(15).iloc[::-1]  # Invertir para mayor arriba
    
    # Crear gráfica doble
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Top 15 Clientes - Concentración', 'Distribución 20/80'),
        specs=[[{"type": "bar"}, {"type": "bar"}]]
    )
    
    # Gráfica izquierda: Top clientes
    clientes_nombres = [nombre[:15] + '...' if len(nombre) > 15 else nombre 
                       for nombre in top_clientes.index.get_level_values(1)]
    
    fig.add_trace(
        go.Bar(
            y=clientes_nombres,
            x=top_clientes.values,
            orientation='h',
            name='Top Clientes',
            marker_color='#3b82f6'
        ),
        row=1, col=1
    )
    
    # Gráfica derecha: 20/80
    categorias = [f'Top {clientes_20} Clientes', f'Resto {len(cartera_por_cliente)-clientes_20} Clientes']
    valores_80_20 = [cartera_80, total_cartera - cartera_80]
    
    fig.add_trace(
        go.Bar(
            x=categorias,
            y=valores_80_20,
            name='Distribución 20/80',
            marker_color=['#00B3B0', '#475569']
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        title_text="Concentración de Cartera - Análisis 20/80",
        template="plotly_dark",
        height=500,
        showlegend=False
    )
    
    fig.update_xaxes(tickprefix='$', tickformat='.0s', row=1, col=1)
    fig.update_xaxes(tickprefix='$', tickformat='.0s', row=1, col=2)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Información adicional
    st.info(f"""
    **📈 Análisis Pareto:**
    - **Top {clientes_20} clientes** controlan **${cartera_80/1e6:.1f}M** ({(cartera_80/total_cartera*100):.1f}%)
    - **{len(cartera_por_cliente)} clientes** en total
    - **Principio 20/80:** 20% de clientes controlan 80% de la cartera
    """)

def crear_grafica_envejecimiento_detallado(datos):
    """Crea análisis detallado de envejecimiento usando cartera actual"""
    try:
        st.subheader("📈 Análisis de Envejecimiento Detallado")
        
        if datos.empty:
            st.info("No hay datos para mostrar el análisis de envejecimiento")
            return
        
        # Rangos de envejecimiento (igual que en PySide6)
        rangos = {
            'Corriente (0 días)': (0, 0),
            '1-15 días': (1, 15),
            '16-30 días': (16, 30),
            '31-60 días': (31, 60),
            '61-90 días': (61, 90),
            '91-180 días': (91, 180),
            '181-365 días': (181, 365),
            '+365 días': (366, 9999)
        }
        
        # Calcular con datos actuales
        valores_rangos = {}
        clientes_rangos = {}
        
        for nombre, (min_dias, max_dias) in rangos.items():
            if max_dias == 9999:
                datos_rango = datos[datos['dias_vencidos'] >= min_dias]
            else:
                datos_rango = datos[(datos['dias_vencidos'] >= min_dias) & 
                                  (datos['dias_vencidos'] <= max_dias)]
            
            valores_rangos[nombre] = datos_rango['total_cop'].sum()
            clientes_rangos[nombre] = datos_rango['nit_cliente'].nunique()
        
        # Filtrar rangos con valores
        rangos_filtrados = {k: v for k, v in valores_rangos.items() if v > 0}
        
        if not rangos_filtrados:
            st.info("No hay cartera en mora para mostrar en el análisis de envejecimiento")
            return
        
        # Crear gráfica con Plotly
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        # Preparar datos
        rangos_nombres = list(rangos_filtrados.keys())
        rangos_valores = [v / 1000000 for v in list(rangos_filtrados.values())]  # En millones
        rangos_clientes = [clientes_rangos[k] for k in rangos_filtrados.keys()]
        
        # Colores (gradiente de verde a rojo)
        colores = ['#10b981', '#84cc16', '#f59e0b', '#f97316', '#ef4444', '#dc2626', '#991b1b', '#7f1d1d']
        colores = colores[:len(rangos_nombres)]
        
        # Crear figura con subplots
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=(
                '📊 Cartera por Rango de Envejecimiento',
                '🥧 Distribución Porcentual'
            ),
            specs=[[{"type": "bar"}, {"type": "pie"}]]
        )
        
        # Gráfica de barras
        fig.add_trace(
            go.Bar(
                x=rangos_nombres,
                y=rangos_valores,
                marker_color=colores,
                text=[f'${v:.1f}M<br>{c} clientes' for v, c in zip(rangos_valores, rangos_clientes)],
                textposition='auto',
                hovertemplate='<b>%{x}</b><br>Cartera: $%{y:.1f}M<br>Clientes: %{customdata}<extra></extra>',
                customdata=rangos_clientes
            ),
            row=1, col=1
        )
        
        # Gráfica de torta
        total_cartera = sum(rangos_filtrados.values())
        porcentajes = [v / total_cartera * 100 for v in rangos_filtrados.values()]
        
        fig.add_trace(
            go.Pie(
                labels=rangos_nombres,
                values=porcentajes,
                marker_colors=colores,
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>Porcentaje: %{percent}<br>Valor: $%{value:.1f}M<extra></extra>',
                textposition='inside'
            ),
            row=1, col=2
        )
        
        # Actualizar diseño
        fig.update_layout(
            height=500,
            showlegend=False,
            plot_bgcolor='#1e293b',
            paper_bgcolor='#1e293b',
            font=dict(color='#e2e8f0'),
            title_text="Análisis Detallado de Envejecimiento - Cartera Actual"
        )
        
        # Actualizar ejes
        fig.update_xaxes(tickangle=45, row=1, col=1)
        fig.update_yaxes(title_text="Millones COP", tickprefix="$", row=1, col=1)
        
        # Mostrar gráfica
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar tabla resumen
        with st.expander("📋 Ver Detalles por Rango"):
            resumen_data = []
            for nombre in rangos_filtrados.keys():
                valor = valores_rangos[nombre] / 1000000
                clientes = clientes_rangos[nombre]
                porcentaje = (valores_rangos[nombre] / total_cartera * 100) if total_cartera > 0 else 0
                
                resumen_data.append({
                    'Rango': nombre,
                    'Cartera (M)': f"${valor:.1f}M",
                    'Clientes': clientes,
                    'Porcentaje': f"{porcentaje:.1f}%"
                })
            
            import pandas as pd
            df_resumen = pd.DataFrame(resumen_data)
            st.dataframe(df_resumen, use_container_width=True, hide_index=True)
        
        # Estadísticas clave
        col1, col2, col3 = st.columns(3)
        with col1:
            cartera_mora_total = sum([v for k, v in valores_rangos.items() if k != 'Corriente (0 días)'])
            st.metric("Cartera Total en Mora", f"${cartera_mora_total/1000000:.1f}M")
        
        with col2:
            max_rango = max(rangos_filtrados, key=rangos_filtrados.get)
            st.metric("Rango con Mayor Mora", max_rango.split(' ')[0])
        
        with col3:
            total_clientes_mora = sum([clientes_rangos[k] for k in rangos_filtrados.keys() if k != 'Corriente (0 días)'])
            st.metric("Clientes en Mora", f"{total_clientes_mora}")
            
    except Exception as e:
        st.error(f"❌ Error creando análisis de envejecimiento: {str(e)}")

def crear_grafica_analisis_geografico(datos):
    """Crea análisis geográfico de cartera - ORDEN CORREGIDO: Mayor a Menor"""
    try:
        st.subheader("🏙️ Análisis Geográfico de Cartera")
        
        if datos.empty:
            st.info("No hay datos para mostrar el análisis geográfico")
            return
        
        # Obtener datos geográficos de clientes
        clientes = st.session_state.db.obtener_clientes()
        datos_con_geografia = datos.merge(
            clientes[['nit_cliente', 'ciudad']], 
            on='nit_cliente', 
            how='left'
        )
        
        if datos_con_geografia.empty:
            st.info("No hay datos geográficos disponibles para los clientes")
            return
        
        # Agrupar por ciudad con datos actuales
        cartera_por_ciudad = datos_con_geografia.groupby('ciudad').agg({
            'total_cop': 'sum',
            'nit_cliente': 'nunique',
            'dias_vencidos': 'mean'
        }).round(2)
        
        # Filtrar ciudades con datos y ordenar de mayor a menor
        cartera_por_ciudad = cartera_por_ciudad[cartera_por_ciudad['total_cop'] > 0]
        cartera_por_ciudad = cartera_por_ciudad.sort_values('total_cop', ascending=False)
        
        # Tomar top 15 ciudades
        cartera_por_ciudad = cartera_por_ciudad.head(15)
        
        if cartera_por_ciudad.empty:
            st.info("No hay datos suficientes para el análisis geográfico")
            return
        
        # Crear gráficas con Plotly
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        # Preparar datos
        ciudades = [ciudad[:20] + '...' if len(ciudad) > 20 else ciudad 
                   for ciudad in cartera_por_ciudad.index]
        valores = cartera_por_ciudad['total_cop'].values / 1000000  # En millones
        n_clientes = cartera_por_ciudad['nit_cliente'].values
        
        # Filtrar ciudades con mora
        ciudades_con_mora = cartera_por_ciudad[cartera_por_ciudad['dias_vencidos'] > 0]
        
        # Crear figura con subplots
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=(
                '🏙️ Top 15 Ciudades - Cartera Actual',
                '📊 Promedio de Morosidad por Ciudad' if not ciudades_con_mora.empty else '📊 Sin Morosidad en Ciudades'
            ),
            specs=[[{"type": "bar"}, {"type": "bar"}]]
        )
        
        # Gráfica 1: Cartera por ciudad
        fig.add_trace(
            go.Bar(
                y=ciudades,
                x=valores,
                orientation='h',
                marker_color='#3b82f6',
                text=[f'${v:.1f}M<br>{c} clientes' for v, c in zip(valores, n_clientes)],
                textposition='auto',
                hovertemplate='<b>%{y}</b><br>Cartera: $%{x:.1f}M<br>Clientes: %{customdata}<extra></extra>',
                customdata=n_clientes
            ),
            row=1, col=1
        )
        
        # Gráfica 2: Morosidad por ciudad
        if not ciudades_con_mora.empty:
            # Ordenar por días vencidos de mayor a menor
            ciudades_con_mora = ciudades_con_mora.sort_values('dias_vencidos', ascending=False)
            
            ciudades_mora_nombres = [ciudad[:15] + '...' if len(ciudad) > 15 else ciudad 
                                   for ciudad in ciudades_con_mora.index]
            promedios_mora = ciudades_con_mora['dias_vencidos'].values
            
            # Colores gradiente (rojo para mayor mora)
            import numpy as np
            colors_mora = [f'rgb({int(239 + (220-239)*i/len(promedios_mora))}, {int(68 + (38-68)*i/len(promedios_mora))}, {int(68 + (38-68)*i/len(promedios_mora))})' 
                          for i in range(len(promedios_mora))]
            
            fig.add_trace(
                go.Bar(
                    x=ciudades_mora_nombres,
                    y=promedios_mora,
                    marker_color=colors_mora,
                    text=[f'{v:.0f} días' for v in promedios_mora],
                    textposition='auto',
                    hovertemplate='<b>%{x}</b><br>Días vencidos promedio: %{y:.0f} días<extra></extra>'
                ),
                row=1, col=2
            )
            
            # Rotar etiquetas para mejor visualización
            fig.update_xaxes(tickangle=45, row=1, col=2)
        else:
            # Mensaje cuando no hay morosidad
            fig.add_annotation(
                text="No hay morosidad<br>en las ciudades analizadas",
                xref="x2", yref="y2",
                x=0.5, y=0.5,
                xanchor="center", yanchor="middle",
                showarrow=False,
                font=dict(size=14, color="#94a3b8"),
                row=1, col=2
            )
        
        # Actualizar diseño
        fig.update_layout(
            height=500,
            showlegend=False,
            plot_bgcolor='#1e293b',
            paper_bgcolor='#1e293b',
            font=dict(color='#e2e8f0')
        )
        
        # Actualizar ejes
        fig.update_xaxes(title_text="Millones COP", tickprefix="$", row=1, col=1)
        fig.update_yaxes(title_text="Ciudad", row=1, col=1)
        
        if not ciudades_con_mora.empty:
            fig.update_yaxes(title_text="Días Vencidos Promedio", row=1, col=2)
        
        # Mostrar gráfica
        st.plotly_chart(fig, use_container_width=True)
        
        # Estadísticas resumen
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_ciudades = len(cartera_por_ciudad)
            st.metric("Total Ciudades Analizadas", total_ciudades)
        
        with col2:
            ciudad_mayor_cartera = cartera_por_ciudad.index[0]
            st.metric("Ciudad con Mayor Cartera", ciudad_mayor_cartera[:15] + '...' if len(ciudad_mayor_cartera) > 15 else ciudad_mayor_cartera)
        
        with col3:
            if not ciudades_con_mora.empty:
                ciudad_mayor_mora = ciudades_con_mora.index[0]
                st.metric("Ciudad con Mayor Mora", ciudad_mayor_mora[:15] + '...' if len(ciudad_mayor_mora) > 15 else ciudad_mayor_mora)
            else:
                st.metric("Ciudades con Mora", "0")
        
        # Tabla detallada
        with st.expander("📋 Ver Detalles por Ciudad"):
            detalle_data = []
            for ciudad, row in cartera_por_ciudad.iterrows():
                detalle_data.append({
                    'Ciudad': ciudad,
                    'Cartera (M)': f"${row['total_cop']/1000000:.1f}M",
                    'Clientes': row['nit_cliente'],
                    'Días Vencidos Prom.': f"{row['dias_vencidos']:.0f}" if row['dias_vencidos'] > 0 else "0"
                })
            
            import pandas as pd
            df_detalle = pd.DataFrame(detalle_data)
            st.dataframe(df_detalle, use_container_width=True, hide_index=True)
            
    except Exception as e:
        st.error(f"❌ Error creando análisis geográfico: {str(e)}")

def crear_grafica_proyeccion_credito(datos):
    """Crea proyección de vencimientos usando condiciones REALES - ORDEN: mayor a menor"""
    try:
        st.subheader("💰 Proyección por Tipo de Crédito")
        
        if datos.empty:
            st.info("No hay datos para mostrar la proyección por crédito")
            return
        
        # Usar condiciones REALES sin clasificación (igual que PySide6)
        datos_modificados = datos.copy()
        
        # Unir CO1 y CON como "CONTADO" (igual que PySide6)
        datos_modificados['condicion_display'] = datos_modificados['condicion_pago'].apply(
            lambda x: 'CONTADO' if str(x).upper() in ['CO1', 'CON'] else str(x)
        )
        
        # Calcular días hasta vencimiento
        from datetime import datetime, timedelta
        import pandas as pd
        import numpy as np
        
        hoy = datetime.now().date()
        datos_modificados['fecha_vencimiento'] = pd.to_datetime(datos_modificados['fecha_vencimiento'], errors='coerce')
        datos_modificados['dias_hasta_vencimiento'] = (datos_modificados['fecha_vencimiento'] - pd.to_datetime(hoy)).dt.days
        
        # Rangos de vencimiento (igual que PySide6)
        rangos_vencimiento = {
            'Vencido': (-9999, -1),
            'Vence este mes': (0, 30),
            '1-2 meses': (31, 60),
            '3-6 meses': (61, 180),
            '+6 meses': (181, 9999)
        }
        
        # Calcular proyección con condiciones REALES
        proyeccion = {}
        condiciones_unicas = datos_modificados['condicion_display'].unique()
        
        for condicion in condiciones_unicas:
            datos_condicion = datos_modificados[datos_modificados['condicion_display'] == condicion]
            proyeccion_condicion = {}
            
            for rango, (min_dias, max_dias) in rangos_vencimiento.items():
                if max_dias == 9999:
                    datos_rango = datos_condicion[datos_condicion['dias_hasta_vencimiento'] >= min_dias]
                else:
                    datos_rango = datos_condicion[
                        (datos_condicion['dias_hasta_vencimiento'] >= min_dias) & 
                        (datos_condicion['dias_hasta_vencimiento'] <= max_dias)
                    ]
                
                proyeccion_condicion[rango] = datos_rango['total_cop'].sum()
            
            proyeccion[condicion] = proyeccion_condicion
        
        # Crear DataFrame
        condiciones_display = list(proyeccion.keys())
        rangos = list(rangos_vencimiento.keys())
        
        df_proyeccion = pd.DataFrame(proyeccion).T.fillna(0)
        
        if df_proyeccion.empty:
            st.info("No hay datos para la proyección por tipo de crédito")
            return
        
        # FILTRAR condiciones con valor total > 0
        totales_por_condicion = df_proyeccion.sum(axis=1)
        condiciones_con_valor = totales_por_condicion[totales_por_condicion > 0].index
        df_proyeccion = df_proyeccion.loc[condiciones_con_valor]
        
        if df_proyeccion.empty:
            st.info("No hay condiciones de crédito con cartera para proyectar")
            return
        
        # ORDENAR por TOTAL de MAYOR a MENOR (igual que PySide6)
        totales_por_condicion = df_proyeccion.sum(axis=1)
        df_proyeccion = df_proyeccion.loc[totales_por_condicion.sort_values(ascending=False).index]
        
        # Crear gráfica con Plotly
        import plotly.graph_objects as go
        
        # Preparar datos para gráfica apilada
        condiciones = df_proyeccion.index.tolist()
        
        # Colores para rangos (igual que PySide6)
        colores = ['#ef4444', '#f59e0b', '#eab308', '#84cc16', '#10b981']
        
        # Crear gráfica de barras apiladas
        fig = go.Figure()
        
        # Añadir cada rango como una barra apilada
        for i, rango in enumerate(rangos):
            if rango in df_proyeccion.columns:
                valores = df_proyeccion[rango].values / 1000000  # En millones
                fig.add_trace(go.Bar(
                    name=rango,
                    x=condiciones,
                    y=valores,
                    marker_color=colores[i % len(colores)],
                    hovertemplate='<b>%{x}</b><br>Rango: %{meta[0]}<br>Valor: $%{y:.1f}M<extra></extra>',
                    meta=[rango] * len(condiciones)
                ))
        
        # Actualizar diseño
        fig.update_layout(
            barmode='stack',
            height=500,
            title="Proyección de Vencimientos - Condiciones Reales",
            xaxis_title="Condición de Pago",
            yaxis_title="Valor COP (Millones)",
            plot_bgcolor='#1e293b',
            paper_bgcolor='#1e293b',
            font=dict(color='#e2e8f0'),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                bgcolor='rgba(30, 41, 59, 0.8)'
            )
        )
        
        # Formatear eje Y
        fig.update_yaxes(tickprefix="$", ticksuffix="M")
        
        # Rotar etiquetas del eje X si son largas
        fig.update_xaxes(tickangle=45)
        
        # Mostrar gráfica
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar tabla de resumen
        with st.expander("📊 Ver Detalles por Condición y Rango"):
            # Crear tabla de resumen
            resumen_data = []
            for condicion in condiciones:
                total_condicion = df_proyeccion.loc[condicion].sum() / 1000000
                row_data = {'Condición': condicion, 'Total': f"${total_condicion:.1f}M"}
                
                for rango in rangos:
                    if rango in df_proyeccion.columns:
                        valor = df_proyeccion.loc[condicion, rango] / 1000000
                        row_data[rango] = f"${valor:.1f}M" if valor > 0 else "-"
                
                resumen_data.append(row_data)
            
            # Añadir fila de totales
            total_general = df_proyeccion.sum().sum() / 1000000
            total_row = {'Condición': 'TOTAL GENERAL', 'Total': f"${total_general:.1f}M"}
            for rango in rangos:
                if rango in df_proyeccion.columns:
                    total_rango = df_proyeccion[rango].sum() / 1000000
                    total_row[rango] = f"${total_rango:.1f}M"
            
            resumen_data.append(total_row)
            
            import pandas as pd
            df_resumen = pd.DataFrame(resumen_data)
            st.dataframe(df_resumen, use_container_width=True, hide_index=True)
        
        # Estadísticas clave
        col1, col2, col3 = st.columns(3)
        
        with col1:
            condicion_mayor = df_proyeccion.sum(axis=1).idxmax()
            st.metric("Condición con Mayor Cartera", condicion_mayor)
        
        with col2:
            total_vencido = df_proyeccion['Vencido'].sum() / 1000000 if 'Vencido' in df_proyeccion.columns else 0
            st.metric("Total Vencido", f"${total_vencido:.1f}M")
        
        with col3:
            total_futuro = df_proyeccion[['Vence este mes', '1-2 meses', '3-6 meses', '+6 meses']].sum().sum() / 1000000
            st.metric("Total por Vencer", f"${total_futuro:.1f}M")
            
    except Exception as e:
        st.error(f"❌ Error creando proyección por tipo de crédito: {str(e)}")

def mostrar_botones_accion():
    """Muestra botones de acción adicionales"""
    
    st.markdown("---")
    st.subheader("🚀 Acciones Adicionales")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📤 Exportar Reporte", use_container_width=True, help="Exportar análisis completo a Excel"):
            exportar_reporte_completo()
    
    with col2:
        if st.button("📊 Actualizar Datos", use_container_width=True, type="primary", help="Actualizar todos los datos del análisis"):
            st.session_state.datos_analisis_filtrados = pd.DataFrame()
            st.rerun()
    
    with col3:
        if st.button("🔄 Cargar Historial", use_container_width=True, help="Cargar datos históricos de cartera"):
            cargar_historial_datos()

def exportar_reporte_completo():
    """Exporta el reporte completo a Excel"""
    try:
        if st.session_state.datos_analisis_filtrados is None or st.session_state.datos_analisis_filtrados.empty:
            st.warning("No hay datos filtrados para exportar")
            return
        
        # Crear Excel en memoria
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja de datos filtrados
            st.session_state.datos_analisis_filtrados.to_excel(writer, sheet_name='Datos_Filtrados', index=False)
            
            # Hoja de resumen
            resumen = pd.DataFrame({
                'Métrica': ['Total Cartera', 'Cartera en Mora', 'Clientes Totales', 'Clientes en Mora'],
                'Valor': [
                    st.session_state.datos_analisis_filtrados['total_cop'].sum(),
                    st.session_state.datos_analisis_filtrados[st.session_state.datos_analisis_filtrados['dias_vencidos'] > 0]['total_cop'].sum(),
                    st.session_state.datos_analisis_filtrados['nit_cliente'].nunique(),
                    st.session_state.datos_analisis_filtrados[st.session_state.datos_analisis_filtrados['dias_vencidos'] > 0]['nit_cliente'].nunique()
                ]
            })
            resumen.to_excel(writer, sheet_name='Resumen', index=False)
        
        output.seek(0)
        
        # Botón de descarga
        st.download_button(
            label="⬇️ Descargar Reporte Excel",
            data=output.getvalue(),
            file_name=f"reporte_analisis_cartera_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"❌ Error exportando reporte: {str(e)}")

def cargar_historial_datos():
    """Carga datos históricos de cartera"""
    try:
        with st.spinner("📥 Cargando datos históricos..."):
            # Aquí iría la lógica para cargar datos históricos
            st.info("""
            **📋 Funcionalidad de Carga de Historial:**
            
            Esta característica permite cargar datos históricos de cartera 
            para análisis temporales completos.
            
            *Próximamente en actualizaciones futuras...*
            """)
            
    except Exception as e:
        st.error(f"❌ Error cargando historial: {str(e)}")