# analisis_gestion_module.py - VERSIÓN CORREGIDA
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

def analisis_gestion_section():
    """Sección completa de Análisis de Gestión - VERSIÓN CORREGIDA"""
    
    st.header("📈 Análisis de Gestión")
    
    # ✅ INICIALIZAR ESTADO CORRECTAMENTE
    if 'filtro_periodo_gestion' not in st.session_state:
        st.session_state.filtro_periodo_gestion = "Mes Actual"
    
    try:
        # 1. FILTROS PRINCIPALES (con manejo correcto del estado)
        periodo_seleccionado = mostrar_filtros_gestion()
        
        # 2. MÉTRICAS DE PROGRESO (pasar el período)
        mostrar_metricas_progreso(periodo_seleccionado)
            
        # 3. GRÁFICAS PRINCIPALES (pasar el período)
        mostrar_graficas_gestion(periodo_seleccionado)
                
        # 4. TABLA DETALLADA (pasar el período)  
        mostrar_tabla_detallada(periodo_seleccionado)
        
        # 5. BOTONES DE ACCIÓN
        mostrar_botones_accion_gestion()
        
    except Exception as e:
        st.error(f"❌ Error en análisis de gestión: {str(e)}")
        st.info("💡 Si el error persiste, intenta actualizar la página")

def mostrar_filtros_gestion():
    """Muestra los filtros de análisis de gestión - VERSIÓN CORREGIDA"""
    
    st.subheader("🔍 Filtros de Análisis")
    
    # Usar columnas para filtros compactos
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Filtro de período - SIN modificar session_state directamente
        periodo_options = ["Mes Actual", "Mes Anterior", "Personalizado"]
        
        # Usar key único y manejar el retorno
        periodo_seleccionado = st.selectbox(
            "📅 Período:",
            options=periodo_options,
            index=periodo_options.index(st.session_state.filtro_periodo_gestion),
            key="selectbox_periodo_gestion"  # Key diferente al session_state
        )
    
    with col2:
        # Filtro de tipo de gestión
        tipo_gestion = st.selectbox(
            "📞 Tipo Gestión:",
            options=["Todos los tipos", "Llamada telefónica", "WhatsApp", "Correo electrónico", "Visita presencial"],
            key="filtro_tipo_gestion"
        )
    
    with col3:
        # Filtro de resultado
        resultado_options = [
            "Todos los resultados",
            "Compromisos de Pago", 
            "Contactos Exitosos",
            "Dificultades/Rechazos",
            "Seguimientos Pendientes"
        ]
        resultado_seleccionado = st.selectbox(
            "🎯 Resultado:",
            options=resultado_options,
            key="filtro_resultado_gestion"
        )

    # Selector de rango de fechas para Personalizado
    if periodo_seleccionado == "Personalizado":
        st.markdown("**📅 Seleccionar rango de fechas:**")
        col_fecha1, col_fecha2 = st.columns(2)
        with col_fecha1:
            fecha_inicio = st.date_input("Fecha inicio", value=datetime.now() - timedelta(days=30))
        with col_fecha2:
            fecha_fin = st.date_input("Fecha fin", value=datetime.now())
        
        # Guardar en session_state
        st.session_state.fecha_inicio_personalizado = fecha_inicio
        st.session_state.fecha_fin_personalizado = fecha_fin

    # Botones de acción - CORREGIDOS (esto ya existe en tu código)
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])

    # Botones de acción - CORREGIDOS
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    
    with col_btn1:
        if st.button("🔄 Aplicar Filtros", use_container_width=True, type="primary", key="btn_aplicar_filtros"):
            # ✅ ACTUALIZAR session_state SOLO cuando se presiona el botón
            st.session_state.filtro_periodo_gestion = periodo_seleccionado
            st.rerun()
    
    with col_btn2:
        if st.button("🧹 Limpiar Filtros", use_container_width=True, key="btn_limpiar_filtros"):
            st.session_state.filtro_periodo_gestion = "Mes Actual"
            st.rerun()
    
    with col_btn3:
        # Mostrar información del filtro aplicado
        st.info(f"📊 Filtro activo: {st.session_state.filtro_periodo_gestion}")
    
    return periodo_seleccionado

def mostrar_metricas_progreso(periodo_seleccionado=None):
    """Muestra las métricas de progreso con barras dinámicas - VERSIÓN CORREGIDA"""
    
    st.subheader("📊 Progreso de Gestión")
    
    try:
        # Obtener datos de progreso
        progreso_data = st.session_state.db.obtener_progreso_gestion()
        
        if not progreso_data:
            st.warning("No hay datos de progreso disponibles")
            return
        
        # Mostrar métricas en 2 filas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_clientes = progreso_data.get('total_clientes', 0)
            gestionados = progreso_data.get('clientes_gestionados', 0)
            porcentaje = progreso_data.get('porcentaje_general', 0)
            
            # Crear barra de progreso personalizada
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
            # Total gestiones del mes
            gestiones_mes = st.session_state.db.obtener_gestiones_mes_actual()
            if st.session_state.auth_manager.current_user['rol'] in ['comercial', 'consulta']:
                gestiones_mes = gestiones_mes[gestiones_mes['usuario'] == st.session_state.auth_manager.current_user['email']]
            total_gestiones = len(gestiones_mes)
            
            # ✅ CORREGIDO: Quitar el parámetro 'key' que causa el error
            st.metric(
                "Total Gestiones",
                f"{total_gestiones:,}",
                help="Número total de gestiones realizadas"
            )
        
        with col4:
            # Clientes únicos gestionados
            if not gestiones_mes.empty:
                clientes_unicos = gestiones_mes['nit_cliente'].nunique()
            else:
                clientes_unicos = 0
                
            # ✅ CORREGIDO: Quitar el parámetro 'key' que causa el error
            st.metric(
                "Clientes Únicos",
                f"{clientes_unicos:,}",
                help="Clientes diferentes gestionados"
            )
        
        # Segunda fila de métricas - CORREGIDA
        st.markdown("---")
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            # Tasa de contacto
            if not gestiones_mes.empty:
                contactos_exitosos = len(gestiones_mes[gestiones_mes['resultado'].str.contains('Contacto|Promesa|Pago', na=False)])
                tasa_contacto = (contactos_exitosos / total_gestiones * 100) if total_gestiones > 0 else 0
            else:
                tasa_contacto = 0
                
            # ✅ CORREGIDO: Quitar el parámetro 'key' que causa el error
            st.metric(
                "Tasa de Contacto",
                f"{tasa_contacto:.1f}%",
                help="Porcentaje de gestiones con contacto exitoso"
            )
        
        with col6:
            # Promesas generadas
            if not gestiones_mes.empty:
                promesas = len(gestiones_mes[gestiones_mes['resultado'].str.contains('Promesa', na=False)])
            else:
                promesas = 0
                
            # ✅ CORREGIDO: Quitar el parámetro 'key' que causa el error
            st.metric(
                "Promesas Generadas",
                f"{promesas:,}",
                help="Compromisos de pago obtenidos"
            )
        
        with col7:
            # Efectividad general
            if total_clientes > 0:
                efectividad = (gestionados / total_clientes * 100)
            else:
                efectividad = 0
                
            # ✅ CORREGIDO: Quitar el parámetro 'key' que causa el error
            st.metric(
                "Efectividad General",
                f"{efectividad:.1f}%",
                delta=f"+{gestionados} clientes" if gestionados > 0 else None
            )
        
        with col8:
            # Pendientes por gestionar
            pendientes = total_clientes - gestionados
            # ✅ CORREGIDO: Quitar el parámetro 'key' que causa el error
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

def mostrar_graficas_gestion(periodo_seleccionado=None):
    """Muestra las 3 gráficas principales de análisis de gestión"""
    
    st.subheader("📈 Gráficas de Análisis")
    
    # Obtener datos para las gráficas
    try:
        # Gráfica 1: Distribución de resultados
        with st.spinner("Cargando distribución de resultados..."):
            fig_distribucion = crear_grafica_distribucion_resultados(periodo_seleccionado)
            if fig_distribucion:
                st.plotly_chart(fig_distribucion, use_container_width=True)
            else:
                st.info("📊 No hay datos suficientes para mostrar la distribución de resultados")
        
        # Dividir las siguientes gráficas en columnas para mejor responsividad
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfica 2: Evolución diaria
            with st.spinner("Cargando evolución diaria..."):
                fig_evolucion = crear_grafica_evolucion_diaria(periodo_seleccionado)
                if fig_evolucion:
                    st.plotly_chart(fig_evolucion, use_container_width=True)
                else:
                    st.info("📅 No hay datos de evolución diaria")
        
        with col2:
            # Gráfica 3: Evolución histórica
            with st.spinner("Cargando evolución histórica..."):
                fig_historica = crear_grafica_evolucion_historica(periodo_seleccionado)
                if fig_historica:
                    st.plotly_chart(fig_historica, use_container_width=True)
                else:
                    st.info("📈 No hay datos históricos suficientes")
                    
    except Exception as e:
        st.error(f"❌ Error cargando gráficas: {str(e)}")

def crear_grafica_distribucion_resultados(periodo_seleccionado=None):
    """Crea gráfica de distribución de resultados por categoría"""
    
    try:
        # Obtener estadísticas filtradas por usuario
        estadisticas = st.session_state.db.obtener_estadisticas_resultados_filtrado()
        
        if not estadisticas or not any(estadisticas.values()):
            return None
        
        categorias = list(estadisticas.keys())
        valores = list(estadisticas.values())
        
        # Colores corporativos
        colores = ['#00B3B0', '#3b82f6', '#f59e0b', '#ef4444']
        
        # Crear DataFrame para Plotly
        df = pd.DataFrame({
            'Categoría': categorias,
            'Cantidad': valores,
            'Color': colores[:len(categorias)]
        })
        
        # Crear gráfica de barras horizontales
        fig = px.bar(
            df,
            y='Categoría',
            x='Cantidad',
            title="📊 Distribución de Resultados por Categoría",
            labels={'Cantidad': 'Cantidad de Gestiones', 'Categoría': 'Tipo de Resultado'},
            orientation='h',
            color='Categoría',
            color_discrete_sequence=colores[:len(categorias)]
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
        
        # Añadir etiquetas de valor
        fig.update_traces(
            texttemplate='%{x} gestiones',
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>%{x} gestiones<extra></extra>'
        )
        
        return fig
        
    except Exception as e:
        print(f"Error creando gráfica de distribución: {e}")
        return None

def crear_grafica_evolucion_diaria(periodo_seleccionado=None):
    """Crea gráfica de evolución diaria de gestiones"""
    
    try:
        # Obtener datos de evolución diaria
        evolucion_data = st.session_state.db.obtener_evolucion_diaria_gestiones()
        
        if not evolucion_data:
            return None
        
        # Preparar datos
        fechas = [item[0] for item in evolucion_data]
        total_gestiones = [item[1] for item in evolucion_data]
        clientes_unicos = [item[2] for item in evolucion_data]
        
        # Formatear fechas para mejor visualización
        fechas_formateadas = [fecha.split('-')[-1] + '/' + fecha.split('-')[-2] if '-' in fecha else fecha 
                             for fecha in fechas]
        
        # Crear DataFrame
        df = pd.DataFrame({
            'Fecha': fechas_formateadas,
            'Total_Gestiones': total_gestiones,
            'Clientes_Unicos': clientes_unicos
        })
        
        # Crear gráfica de líneas
        fig = go.Figure()
        
        # Línea de total de gestiones
        fig.add_trace(go.Scatter(
            x=df['Fecha'],
            y=df['Total_Gestiones'],
            mode='lines+markers+text',
            name='Total Gestiones',
            line=dict(color='#00B3B0', width=4),
            marker=dict(size=8, color='#00B3B0'),
            text=df['Total_Gestiones'],
            textposition='top center',
            hovertemplate='<b>%{x}</b><br>Total: %{y} gestiones<extra></extra>'
        ))
        
        # Línea de clientes únicos
        fig.add_trace(go.Scatter(
            x=df['Fecha'],
            y=df['Clientes_Unicos'],
            mode='lines+markers',
            name='Clientes Únicos',
            line=dict(color='#f59e0b', width=3, dash='dash'),
            marker=dict(size=6, color='#f59e0b'),
            hovertemplate='<b>%{x}</b><br>Clientes: %{y}<extra></extra>'
        ))
        
        # Actualizar diseño
        fig.update_layout(
            title="📈 Evolución Diaria de Gestiones",
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
            xaxis=dict(
                showgrid=True,
                gridcolor='#334155',
                tickangle=-45
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#334155'
            )
        )
        
        return fig
        
    except Exception as e:
        print(f"Error creando gráfica de evolución diaria: {e}")
        return None

def crear_grafica_evolucion_historica(periodo_seleccionado=None):
    """Crea gráfica de evolución histórica mensual"""
    
    try:
        # Obtener datos históricos
        datos_historicos, max_historico = st.session_state.db.obtener_evolucion_historica_gestiones()
        
        if not datos_historicos:
            return None
        
        # Preparar datos
        meses = [f"{item[0][5:7]}/{item[0][2:4]}" for item in datos_historicos]
        totales = [item[1] for item in datos_historicos]
        
        # Crear gráfica
        fig = go.Figure()
        
        # Línea principal
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
        
        # Línea de máximo histórico
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
            title="📅 Evolución Histórica (Últimos 12 Meses)",
            plot_bgcolor='#1e293b',
            paper_bgcolor='#1e293b',
            font_color='#e2e8f0',
            height=400,
            showlegend=False,
            xaxis=dict(
                showgrid=True,
                gridcolor='#334155',
                tickangle=-45
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#334155',
                title='Total de Gestiones'
            )
        )
        
        return fig
        
    except Exception as e:
        print(f"Error creando gráfica histórica: {e}")
        return None

def mostrar_tabla_detallada(periodo_seleccionado=None):
    """Muestra tabla detallada de gestiones recientes"""
    
    st.subheader("📋 Gestiones Recientes")
    
    try:
        # Obtener gestiones del mes actual
        gestiones = st.session_state.db.obtener_gestiones_por_periodo(periodo_seleccionado)
        
        # Filtrar por usuario si es comercial/consulta
        if st.session_state.auth_manager.current_user['rol'] in ['comercial', 'consulta']:
            gestiones = gestiones[gestiones['usuario'] == st.session_state.auth_manager.current_user['email']]
        
        if gestiones.empty:
            st.info("📝 No hay gestiones registradas en el período actual")
            return
        
        # Limitar a las 10 más recientes para mejor rendimiento
        gestiones_recientes = gestiones.head(10).copy()
        
        # Formatear columnas para mostrar
        columnas_mostrar = ['fecha_contacto', 'razon_social_cliente', 'tipo_contacto', 'resultado']
        columnas_existentes = [col for col in columnas_mostrar if col in gestiones_recientes.columns]
        
        # Crear DataFrame para mostrar
        df_display = gestiones_recientes[columnas_existentes].copy()
        
        # Renombrar columnas para mejor legibilidad
        mapeo_nombres = {
            'fecha_contacto': 'Fecha',
            'razon_social_cliente': 'Cliente',
            'tipo_contacto': 'Tipo Contacto',
            'resultado': 'Resultado'
        }
        
        df_display = df_display.rename(columns=mapeo_nombres)
        
        # Mostrar tabla
        st.dataframe(
            df_display,
            use_container_width=True,
            height=400,
            hide_index=True
        )
        
        # Mostrar estadísticas rápidas
        total_gestiones = len(gestiones)
        st.caption(f"Mostrando 10 de {total_gestiones} gestiones totales")
        
    except Exception as e:
        st.error(f"❌ Error cargando tabla de gestiones: {str(e)}")

def mostrar_botones_accion_gestion():
    """Muestra botones de acción para el módulo de gestión"""
    
    st.markdown("---")
    st.subheader("🚀 Acciones")
    
    col1, col2, col3 = st.columns(3)
    
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
    """Exporta el reporte de análisis de gestión a Excel"""
    
    try:
        import io
        
        # Obtener datos para exportar
        gestiones_mes = st.session_state.db.obtener_gestiones_mes_actual()
        progreso_data = st.session_state.db.obtener_progreso_gestion()
        estadisticas = st.session_state.db.obtener_estadisticas_resultados_filtrado()
        
        # Crear Excel en memoria
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja 1: Gestiones del mes
            if not gestiones_mes.empty:
                gestiones_mes.to_excel(writer, sheet_name='Gestiones_Mes', index=False)
            
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
                    'Total Clientess en Cartera',
                    'Clientes Gestionados', 
                    'Porcentaje de Gestión',
                    'Clientes en Mora',
                    'Clientes en Mora Gestionados',
                    'Porcentaje Mora Gestionada',
                    'Total Gestiones Mes',
                    'Tasa de Contacto'
                ],
                'Valor': [
                    progreso_data.get('total_clientes', 0),
                    progreso_data.get('clientes_gestionados', 0),
                    f"{progreso_data.get('porcentaje_general', 0):.1f}%",
                    progreso_data.get('clientes_mora', 0),
                    progreso_data.get('clientes_mora_gestionados', 0),
                    f"{progreso_data.get('porcentaje_mora', 0):.1f}%",
                    len(gestiones_mes) if not gestiones_mes.empty else 0,
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
            file_name=f"reporte_gestion_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"❌ Error exportando reporte: {str(e)}")  