# gestion_module.py - VERSIÓN COMPACTA MEJORADA CON BOTONES SIEMPRE VISIBLES
import streamlit as st
import pandas as pd
from datetime import datetime
import io
import tempfile
from config import config
from datetime import datetime, timedelta
import os

def gestion_section():
    """Sección completa de Gestión de Clientes - VERSIÓN COMPLETA CORREGIDA"""
    
    # ✅ INICIALIZACIÓN COMPLETA DEL ESTADO (MOVIDA AL INICIO)
    if 'gestion_initialized' not in st.session_state:
        st.session_state.gestion_initialized = True
        st.session_state.cliente_seleccionado_gestion = None
        st.session_state.historial_gestiones = pd.DataFrame()
        st.session_state.filtro_actual_gestion = "Todos los clientes"
        st.session_state.texto_busqueda_gestion = ""
        st.session_state.datos_cliente_actual = {}
        st.session_state.todos_los_clientes = pd.DataFrame()  # ✅ INICIALIZAR AQUÍ
        st.session_state.clientes_filtrados = pd.DataFrame()
        st.session_state.cartera_cliente_actual = pd.DataFrame()
        st.session_state.analisis_cartera = {}
        
        # Estado para exportación/importación
        st.session_state.mostrar_exportar = False
        st.session_state.mostrar_importar = False
    
    # ✅ NUEVO: Verificar si hay cliente pre-seleccionado desde cartera
    if (st.session_state.get('cliente_para_gestion') and 
        not st.session_state.get('cliente_seleccionado_gestion')):
        
        nit_cliente = st.session_state.cliente_para_gestion
        
        # ✅ CARGAR CLIENTES PRIMERO SI ESTÁN VACÍOS
        if st.session_state.todos_los_clientes.empty:
            with st.spinner("🔄 Cargando base de clientes..."):
                st.session_state.todos_los_clientes = cargar_todos_los_clientes()
                st.session_state.clientes_filtrados = st.session_state.todos_los_clientes.copy()
        
        with st.spinner("🔄 Cargando cliente seleccionado desde Cartera..."):
            success = seleccionar_cliente_desde_cartera(nit_cliente)
            if success:
                st.success(f"✅ Cliente cargado automáticamente en Gestión")
                # Limpiar la variable para evitar repeticiones
                st.session_state.cliente_para_gestion = None
            else:
                st.error("❌ No se pudo cargar el cliente en Gestión")
                st.session_state.cliente_para_gestion = None
    
    # Cargar todos los clientes si no están cargados
    if st.session_state.todos_los_clientes.empty:
        with st.spinner("Cargando clientes..."):
            st.session_state.todos_los_clientes = cargar_todos_los_clientes()
            st.session_state.clientes_filtrados = st.session_state.todos_los_clientes.copy()
    
    # ✅ BOTONES DE EXPORTACIÓN/IMPORTACIÓN SIEMPRE VISIBLES
    mostrar_botones_exportacion_importacion()
    
    # ✅ BÚSQUEDA Y FILTROS SIEMPRE VISIBLES
    mostrar_busqueda_filtros()
    
    # ✅ LISTA DE CLIENTES SIEMPRE VISIBLE
    mostrar_lista_clientes()
    
    # ✅ INFORMACIÓN DEL CLIENTE (solo si hay selección)
    if st.session_state.cliente_seleccionado_gestion:
        mostrar_informacion_cliente()
        mostrar_formulario_gestion()
        mostrar_historial_gestiones()
    else:
        # Mostrar estadísticas cuando no hay cliente seleccionado
        st.markdown("---")
        mostrar_estadisticas_generales_compactas()

def mostrar_botones_exportacion_importacion():
    """Muestra los botones de exportación/importación - SIEMPRE VISIBLES"""
    
    st.subheader("📤 Exportar / Importar Gestiones")
    
    # Crear dos columnas para los botones
    col_export, col_import = st.columns(2)
    
    with col_export:
        if st.button("📤 Exportar Gestiones", use_container_width=True, type="secondary"):
            st.session_state.mostrar_exportar = True
    
    with col_import:
        if st.button("📥 Importar Gestiones", use_container_width=True, type="secondary"):
            st.session_state.mostrar_importar = True
    
    # Mostrar diálogo de exportación si está activo
    if st.session_state.get('mostrar_exportar', False):
        mostrar_dialogo_exportacion()
    
    # Mostrar diálogo de importación si está activo
    if st.session_state.get('mostrar_importar', False):
        mostrar_dialogo_importacion()

def mostrar_busqueda_filtros():
    """Muestra búsqueda y filtros - SIEMPRE VISIBLE"""
    
    st.subheader("🔍 Búsqueda y Filtros")
    
    # BÚSQUEDA POR TEXTO - COMPACTA
    texto_busqueda = st.text_input(
        "Buscar cliente:",
        placeholder="NIT, Razón Social...",
        key="buscar_gestion_input",
        value=st.session_state.texto_busqueda_gestion
    )
    
    # ACTUALIZAR BÚSQUEDA SI CAMBIA
    if texto_busqueda != st.session_state.texto_busqueda_gestion:
        st.session_state.texto_busqueda_gestion = texto_busqueda
        aplicar_filtros()
        st.rerun()
    
    # FILTROS COMPACTOS
    filtro_tipo = st.selectbox(
        "Filtrar por estado:",
        options=[
            "Todos los clientes",
            "⚠️ Clientes en mora", 
            "✅ Clientes con gestión este mes",
            "⏳ Clientes sin gestión este mes",
            "📋 Clientes con gestión (histórico)",
            "📭 Clientes sin gestión (histórico)"
        ],
        key="filtro_clientes_gestion"
    )
    
    # ACTUALIZAR FILTRO SI CAMBIA
    if filtro_tipo != st.session_state.filtro_actual_gestion:
        st.session_state.filtro_actual_gestion = filtro_tipo
        aplicar_filtros()
        st.rerun()
    
    # BOTONES COMPACTOS
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 Actualizar", use_container_width=True):
            aplicar_filtros()
            st.rerun()
    
    with col_btn2:
        if st.button("🧹 Limpiar", use_container_width=True):
            st.session_state.texto_busqueda_gestion = ""
            st.session_state.filtro_actual_gestion = "Todos los clientes"
            st.session_state.clientes_filtrados = st.session_state.todos_los_clientes.copy()
            st.rerun()
    
    # ESTADÍSTICAS COMPACTAS
    st.info(f"📊 {len(st.session_state.clientes_filtrados)} de {len(st.session_state.todos_los_clientes)} clientes")

def mostrar_lista_clientes():
    """Muestra la lista de clientes - SIEMPRE VISIBLE"""
    
    st.subheader("👥 Lista de Clientes")
    
    if not st.session_state.clientes_filtrados.empty:
        # USAR UN SELECTBOX GIGANTE COMO LISTA
        clientes_options = []
        for index, cliente in st.session_state.clientes_filtrados.iterrows():
            display_text = f"{cliente['nit_cliente']} - {cliente['razon_social']}"
            clientes_options.append(display_text)
        
        # Agregar opción vacía al principio
        clientes_options.insert(0, "--- Selecciona un cliente ---")
        
        cliente_seleccionado = st.selectbox(
            "Clientes:",
            options=clientes_options,
            key="lista_clientes_select",
            label_visibility="collapsed"
        )
        
        # Detectar cuando se selecciona un cliente
        if cliente_seleccionado and cliente_seleccionado != "--- Selecciona un cliente ---":
            # Extraer NIT del texto seleccionado
            nit_seleccionado = cliente_seleccionado.split(" - ")[0]
            
            # Buscar el cliente correspondiente
            cliente_encontrado = st.session_state.clientes_filtrados[
                st.session_state.clientes_filtrados['nit_cliente'] == nit_seleccionado
            ]
            
            if not cliente_encontrado.empty:
                seleccionar_cliente(cliente_encontrado.iloc[0])
                st.rerun()
        
    else:
        st.warning("No se encontraron clientes con los filtros aplicados")

def mostrar_informacion_cliente():
    """Muestra información del cliente seleccionado"""
    
    cliente = st.session_state.cliente_seleccionado_gestion
    analisis = st.session_state.analisis_cartera
    
    st.markdown("---")
    st.subheader(f"👤 {cliente['razon_social']}")
    
    # BOTÓN PARA VOLVER
    if st.button("← Volver a lista", type="secondary", use_container_width=True):
        st.session_state.cliente_seleccionado_gestion = None
        st.rerun()
    
    # Tarjetas de información básica compactas
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("NIT", cliente.get('nit_cliente', 'N/A'), key="nit_display", disabled=True)
        st.text_input("Teléfono", cliente.get('telefono', 'No disponible') or 'No disponible', key="tel_display", disabled=True)
    
    with col2:
        st.text_input("Email", cliente.get('email', 'No disponible') or 'No disponible', key="email_display", disabled=True)
        st.text_input("Ciudad", cliente.get('ciudad', 'No disponible') or 'No disponible', key="ciudad_display", disabled=True)
    
    st.text_input("Vendedor", cliente.get('vendedor_asignado', 'No asignado') or 'No asignado', key="vendedor_display", disabled=True)
    
    st.markdown("---")
    
    # ANÁLISIS COMPACTO DE CARTERA
    st.subheader("💰 Análisis de Cartera")
    
    # Métricas principales de cartera - Compactas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Cartera", 
            f"${analisis['total_cartera']:,.0f}",
            help="Valor total de todas las facturas"
        )
    
    with col2:
        st.metric(
            "Cartera Corriente", 
            f"${analisis['cartera_corriente']:,.0f}",
            delta=f"{analisis['num_facturas_corriente']} facturas",
            delta_color="normal",
            help="Facturas al día"
        )
    
    with col3:
        st.metric(
            "Cartera en Mora", 
            f"${analisis['cartera_mora']:,.0f}",
            delta=f"{analisis['num_facturas_vencidas']} facturas",
            delta_color="inverse",
            help="Facturas vencidas"
        )
    
    with col4:
        st.metric(
            "Días Mora Máx", 
            f"{int(analisis['dias_mora_max'])} días",
            help="Máximo días de mora"
        )
    
    # DETALLE DE FACTURAS COMPACTO
    st.subheader("📄 Detalle de Facturas")
    
    # Pestañas para facturas corrientes y vencidas
    tab1, tab2 = st.tabs(["✅ Facturas Corrientes", "⚠️ Facturas Vencidas"])
    
    with tab1:
        if not analisis['facturas_corriente'].empty:
            st.dataframe(
                mostrar_facturas_formateadas(analisis['facturas_corriente']),
                use_container_width=True,
                height=200
            )
            st.caption(f"📊 {len(analisis['facturas_corriente'])} facturas corrientes")
        else:
            st.info("No hay facturas corrientes")
    
    with tab2:
        if not analisis['facturas_vencidas'].empty:
            st.dataframe(
                mostrar_facturas_formateadas(analisis['facturas_vencidas']),
                use_container_width=True,
                height=200
            )
            st.caption(f"📊 {len(analisis['facturas_vencidas'])} facturas vencidas")
        else:
            st.info("No hay facturas vencidas")

def mostrar_formulario_gestion():
    """Muestra el formulario para registrar nueva gestión"""
    
    st.markdown("---")
    st.subheader("➕ Registrar Nueva Gestión")
    
    with st.form("formulario_gestion_compacto", clear_on_submit=True):
        # Campos en columnas compactas
        col1, col2 = st.columns(2)
        
        with col1:
            tipo_contacto = st.selectbox(
                "Tipo de Contacto:",
                options=[
                    "Llamada telefónica", "WhatsApp", "Correo electrónico",
                    "Visita presencial", "Videollamada", "Mensaje de texto"
                ],
                key="tipo_contacto_gestion_compact"
            )
            
            fecha_contacto = st.date_input(
                "Fecha de Contacto:",
                value=datetime.now().date(),
                key="fecha_contacto_gestion_compact"
            )
        
        with col2:
            resultado = st.selectbox(
                "Resultado:",
                options=obtener_opciones_resultado(),
                key="resultado_gestion_compact"
            )
            
            proxima_gestion = st.date_input(
                "Próxima Gestión:",
                value=datetime.now().date() + pd.Timedelta(days=7),
                key="proxima_gestion_compact"
            )
        
        # Promesa de pago compacta
        col3, col4 = st.columns(2)
        
        with col3:
            promesa_fecha = st.date_input(
                "Promesa Pago - Fecha:",
                value=datetime.now().date() + pd.Timedelta(days=15),
                key="promesa_fecha_gestion_compact"
            )
        
        with col4:
            promesa_monto = st.number_input(
                "Promesa Pago - Monto:",
                min_value=0.0,
                value=0.0,
                step=1000.0,
                format="%.0f",
                key="promesa_monto_gestion_compact"
            )
        
        # Observaciones compacta
        observaciones = st.text_area(
            "Observaciones:",
            placeholder="Detalles de la gestión, acuerdos, comentarios...",
            height=80,
            key="observaciones_gestion_compact"
        )
        
        # Botón de guardar compacto
        guardar_gestion = st.form_submit_button(
            "💾 Guardar Gestión",
            use_container_width=True,
            type="primary"
        )
        
        if guardar_gestion:
            success = guardar_nueva_gestion(
                tipo_contacto, resultado, fecha_contacto, observaciones,
                promesa_fecha, promesa_monto, proxima_gestion
            )
            
            if success:
                st.success("✅ Gestión guardada correctamente")
                # Recargar historial
                cliente = st.session_state.cliente_seleccionado_gestion
                st.session_state.historial_gestiones = cargar_historial_gestiones_cliente(cliente['nit_cliente'])

def mostrar_historial_gestiones():
    """Muestra el historial de gestiones del cliente"""
    
    st.markdown("---")
    st.subheader("📊 Historial de Gestiones")
    
    if not st.session_state.historial_gestiones.empty:
        # Preparar datos para visualización compacta
        df_display = st.session_state.historial_gestiones.copy()
        
        # Formatear columnas
        if 'promesa_pago_monto' in df_display.columns:
            df_display['promesa_pago_monto'] = df_display['promesa_pago_monto'].apply(
                lambda x: f"${x:,.0f}" if pd.notna(x) and x > 0 else "N/A"
            )
        
        # Seleccionar y ordenar columnas para vista compacta
        columnas_mostrar = [
            'fecha_contacto', 'tipo_contacto', 'resultado', 'observaciones',
            'promesa_pago_fecha', 'promesa_pago_monto'
        ]
        
        columnas_existentes = [col for col in columnas_mostrar if col in df_display.columns]
        df_display = df_display[columnas_existentes]
        
        # Renombrar columnas
        mapeo_nombres = {
            'fecha_contacto': '📅 Fecha',
            'tipo_contacto': '📞 Tipo',
            'resultado': '🎯 Resultado',
            'observaciones': '📝 Observaciones',
            'promesa_pago_fecha': '💰 Fecha Promesa',
            'promesa_pago_monto': '💰 Monto Promesa'
        }
        
        df_display = df_display.rename(columns=mapeo_nombres)
        
        # Mostrar tabla compacta
        st.dataframe(
            df_display,
            use_container_width=True,
            height=300,
            hide_index=True
        )
        
        st.caption(f"📋 {len(df_display)} gestiones registradas")
        
    else:
        st.info("ℹ️ No hay gestiones registradas para este cliente")

# =============================================================================
# FUNCIONES DE EXPORTACIÓN/IMPORTACIÓN (las mismas que antes)
# =============================================================================

def mostrar_dialogo_exportacion():
    """Muestra el diálogo de exportación con opciones"""
    
    st.markdown("---")
    st.subheader("📊 Opciones de Exportación")
    
    # Opciones de exportación
    opciones = [
        "📅 Gestiones del mes actual",
        "📊 Todas las gestiones (histórico completo)"
    ]
    
    # Agregar opción de cliente actual si hay uno seleccionado
    if st.session_state.cliente_seleccionado_gestion:
        opciones.append("👤 Gestiones del cliente actual (filtrado)")
    
    opcion_export = st.radio(
        "Selecciona qué gestiones exportar:",
        options=opciones,
        key="opcion_export_gestiones"
    )
    
    # Información adicional según la opción
    if opcion_export == "📅 Gestiones del mes actual":
        st.info("ℹ️ Exportarás solo las gestiones registradas en el mes actual")
    elif opcion_export == "📊 Todas las gestiones (histórico completo)":
        st.warning("⚠️ El archivo puede ser grande. Exportarás TODAS las gestiones históricas")
    elif opcion_export == "👤 Gestiones del cliente actual (filtrado)":
        if st.session_state.cliente_seleccionado_gestion:
            cliente = st.session_state.cliente_seleccionado_gestion
            st.info(f"ℹ️ Exportarás solo las gestiones del cliente: {cliente['razon_social']}")
        else:
            st.error("❌ Debes seleccionar un cliente primero para usar esta opción")
            return
    
    # Nombre del archivo
    nombre_archivo = st.text_input(
        "Nombre del archivo:",
        value=f"gestiones_exportadas_{datetime.now().strftime('%Y%m%d_%H%M')}",
        help="Puedes personalizar el nombre del archivo Excel"
    )
    
    # Botones de acción
    col_confirmar, col_cancelar = st.columns(2)
    
    with col_confirmar:
        if st.button("✅ Exportar a Excel", use_container_width=True, type="primary"):
            exportar_gestiones_excel(opcion_export, nombre_archivo)
    
    with col_cancelar:
        if st.button("❌ Cancelar", use_container_width=True):
            st.session_state.mostrar_exportar = False
            st.rerun()

def exportar_gestiones_excel(opcion_export, nombre_archivo):
    """Exporta las gestiones según la opción seleccionada"""
    
    try:
        db = st.session_state.db
        
        # Obtener datos según la opción
        if opcion_export == "📅 Gestiones del mes actual":
            gestiones_df = db.obtener_gestiones_mes_actual()
            mensaje_exito = "gestiones del mes actual"
            
        elif opcion_export == "📊 Todas las gestiones (histórico completo)":
            gestiones_df = db.obtener_todas_gestiones()
            mensaje_exito = "todas las gestiones históricas"
            
        elif opcion_export == "👤 Gestiones del cliente actual (filtrado)":
            if st.session_state.cliente_seleccionado_gestion:
                nit_cliente = st.session_state.cliente_seleccionado_gestion['nit_cliente']
                gestiones_df = db.obtener_gestiones_cliente(nit_cliente)
                mensaje_exito = f"gestiones del cliente {st.session_state.cliente_seleccionado_gestion['razon_social']}"
            else:
                st.error("❌ No hay cliente seleccionado")
                return
        
        if gestiones_df.empty:
            st.error("❌ No hay gestiones para exportar con los criterios seleccionados")
            return
        
        # Preparar DataFrame para exportación
        df_export = preparar_dataframe_exportacion(gestiones_df)
        
        # Crear archivo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export.to_excel(writer, sheet_name='Gestiones', index=False)
            
            # Agregar hoja de metadatos
            metadata = pd.DataFrame({
                'Campo': ['Fecha exportación', 'Total registros', 'Opción exportación', 'Usuario'],
                'Valor': [
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    len(df_export),
                    opcion_export,
                    st.session_state.user['email']
                ]
            })
            metadata.to_excel(writer, sheet_name='Metadatos', index=False)
        
        output.seek(0)
        
        # Botón de descarga
        st.success(f"✅ Se prepararon {len(df_export)} gestiones para exportar")
        
        st.download_button(
            label="⬇️ Descargar Archivo Excel",
            data=output.getvalue(),
            file_name=f"{nombre_archivo}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        # Botón para cerrar el diálogo
        if st.button("🗙 Cerrar diálogo de exportación", use_container_width=True):
            st.session_state.mostrar_exportar = False
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ Error al exportar gestiones: {str(e)}")

def preparar_dataframe_exportacion(gestiones_df):
    """Prepara el DataFrame para exportación con formato amigable"""
    
    if gestiones_df.empty:
        return pd.DataFrame()
    
    df_export = gestiones_df.copy()
    
    # Seleccionar y ordenar columnas importantes
    columnas_export = [
        'nit_cliente', 'razon_social_cliente', 'fecha_contacto', 'tipo_contacto',
        'resultado', 'observaciones', 'promesa_pago_fecha', 'promesa_pago_monto',
        'proxima_gestion', 'usuario'
    ]
    
    # Filtrar solo las columnas que existen
    columnas_existentes = [col for col in columnas_export if col in df_export.columns]
    df_export = df_export[columnas_existentes]
    
    # Renombrar columnas para mejor legibilidad
    mapeo_nombres = {
        'nit_cliente': 'NIT Cliente',
        'razon_social_cliente': 'Razón Social', 
        'fecha_contacto': 'Fecha Contacto',
        'tipo_contacto': 'Tipo Contacto',
        'resultado': 'Resultado',
        'observaciones': 'Observaciones',
        'promesa_pago_fecha': 'Promesa Pago Fecha',
        'promesa_pago_monto': 'Promesa Pago Monto',
        'proxima_gestion': 'Próxima Gestión',
        'usuario': 'Usuario'
    }
    
    df_export = df_export.rename(columns=mapeo_nombres)
    
    # Formatear montos
    if 'Promesa Pago Monto' in df_export.columns:
        df_export['Promesa Pago Monto'] = df_export['Promesa Pago Monto'].apply(
            lambda x: f"${x:,.0f}" if pd.notna(x) and x > 0 else "N/A"
        )
    
    return df_export

def mostrar_dialogo_importacion():
    """Muestra el diálogo de importación con formato guía descargable"""
    
    st.markdown("---")
    st.subheader("📥 Importar Gestiones desde Excel")
    
    # SECCIÓN: DESCARGAR FORMATO GUÍA
    st.markdown("#### 📋 Formato Guía de Importación")
    st.info("""
    **Para importar gestiones correctamente:**
    - Descarga el formato guía con la estructura requerida
    - Completa los datos siguiendo las especificaciones
    - Sube el archivo completado para importar
    """)
    
    # Botón para descargar formato guía
    if st.button("⬇️ Descargar Formato Guía de Importación", 
                use_container_width=True, 
                type="secondary",
                key="descargar_formato_gestiones"):
        
        formato_excel = generar_formato_guia_importacion()
        if formato_excel:
            st.success("✅ Formato guía generado correctamente")
        else:
            st.error("❌ Error generando formato guía")
    
    st.markdown("---")
    
    # SECCIÓN: SUBIR ARCHIVO PARA IMPORTAR
    st.markdown("#### 📤 Subir Archivo para Importar")
    
    archivo_subido = st.file_uploader(
        "Selecciona archivo Excel de gestiones completado",
        type=['xlsx'],
        key="upload_gestiones_excel_mejorado",
        help="El archivo debe seguir el formato guía descargado"
    )
    
    if archivo_subido is not None:
        # Mostrar información del archivo
        file_details = {
            "Nombre": archivo_subido.name,
            "Tipo": archivo_subido.type,
            "Tamaño": f"{archivo_subido.size / 1024 / 1024:.2f} MB"
        }
        st.write("**Archivo seleccionado:**")
        st.json(file_details)
        
        # Vista previa del archivo
        try:
            df_preview = pd.read_excel(archivo_subido, nrows=5)
            st.write("**Vista previa (primeras 5 filas):**")
            st.dataframe(df_preview, use_container_width=True)
            
            # Verificar columnas requeridas
            columnas_requeridas = ['nit_cliente', 'razon_social_cliente', 'fecha_contacto', 'tipo_contacto', 'resultado']
            columnas_faltantes = [col for col in columnas_requeridas if col not in df_preview.columns]
            
            if columnas_faltantes:
                st.error(f"❌ Columnas requeridas faltantes: {', '.join(columnas_faltantes)}")
                st.warning("💡 Descarga el formato guía para obtener la estructura correcta")
            else:
                st.success("✅ El archivo tiene la estructura básica correcta")
                
                # Botón de importación
                col_importar, col_cancelar = st.columns(2)
                
                with col_importar:
                    if st.button("🚀 Iniciar Importación", 
                                type="primary", 
                                use_container_width=True,
                                key="iniciar_importacion_gestiones"):
                        importar_gestiones_desde_archivo(archivo_subido)
                
                with col_cancelar:
                    if st.button("❌ Cancelar", 
                                use_container_width=True,
                                key="cancelar_importacion_gestiones"):
                        st.session_state.mostrar_importar = False
                        st.rerun()
                        
        except Exception as e:
            st.error(f"❌ Error al leer el archivo: {str(e)}")
            st.warning("💡 Asegúrate de que el archivo no esté corrupto y sea un Excel válido")
    
    # Botón de cancelar general
    if st.button("🗙 Cerrar Diálogo de Importación", 
                use_container_width=True,
                key="cerrar_dialogo_importacion"):
        st.session_state.mostrar_importar = False
        st.rerun()

def generar_formato_guia_importacion():
    """Genera y descarga el formato guía para importar gestiones"""
    try:
        from config import config
        import io
        
        # Crear DataFrames para cada hoja
        with st.spinner("🔄 Generando formato guía..."):
            
            # HOJA 1: FORMATO DE IMPORTACIÓN
            formato_df = pd.DataFrame(columns=config.GESTIONES_COLUMNAS.keys())
            
            # Agregar fila de ejemplo
            ejemplo = {
                'nit_cliente': '9001234567',
                'razon_social_cliente': 'EMPRESA EJEMPLO SAS',
                'fecha_contacto': datetime.now().strftime('%Y-%m-%d'),
                'tipo_contacto': 'Llamada telefónica',
                'resultado': '1. Promesa de Pago Total (Fecha/Monto)',
                'observaciones': 'Cliente comprometió pago total para fecha acordada',
                'promesa_pago_fecha': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                'promesa_pago_monto': 1500000,
                'proxima_gestion': (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'),
                'usuario': 'usuario@empresa.com'
            }
            formato_df = formato_df._append(ejemplo, ignore_index=True)
            
            # HOJA 2: GUÍA DE CAMPOS
            guia_campos = []
            for columna, especificaciones in config.GESTIONES_COLUMNAS.items():
                guia_campos.append({
                    'Campo': columna,
                    'Nombre para Mostrar': especificaciones['nombre'],
                    'Tipo de Dato': especificaciones['tipo'],
                    'Obligatorio': 'Sí' if especificaciones['obligatorio'] else 'No',
                    'Descripción': obtener_descripcion_campo(columna),
                    'Formato/Ejemplo': obtener_formato_ejemplo(columna)
                })
            guia_df = pd.DataFrame(guia_campos)
            
            # HOJA 3: CATÁLOGO DE OPCIONES
            catalogo_data = []
            
            # Tipos de contacto
            for tipo in config.CATALOGOS_GESTIONES['tipos_contacto']:
                catalogo_data.append({
                    'Campo': 'tipo_contacto',
                    'Valor Válido': tipo,
                    'Descripción': 'Medio utilizado para el contacto con el cliente'
                })
            
            # Resultados
            for resultado in config.CATALOGOS_GESTIONES['resultados']:
                catalogo_data.append({
                    'Campo': 'resultado',
                    'Valor Válido': resultado,
                    'Descripción': 'Resultado obtenido de la gestión realizada'
                })
            
            catalogo_df = pd.DataFrame(catalogo_data)
            
            # Crear archivo Excel en memoria
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Hoja 1: Formato de importación
                formato_df.to_excel(writer, sheet_name='Formato Importación', index=False)
                
                # Hoja 2: Guía de campos
                guia_df.to_excel(writer, sheet_name='Guía de Campos', index=False)
                
                # Hoja 3: Catálogo de opciones
                catalogo_df.to_excel(writer, sheet_name='Catálogo Opciones', index=False)
                
                # Hoja 4: Instrucciones
                instrucciones_df = pd.DataFrame({
                    'Paso': ['1', '2', '3', '4', '5'],
                    'Instrucción': [
                        'Descarga este formato guía',
                        'Completa los datos en la hoja "Formato Importación"',
                        'Consulta las hojas "Guía de Campos" y "Catálogo Opciones" para referencia',
                        'Guarda el archivo Excel completado',
                        'Sube el archivo en el módulo de gestión para importar'
                    ]
                })
                instrucciones_df.to_excel(writer, sheet_name='Instrucciones', index=False)
            
            output.seek(0)
            
            # Botón de descarga
            st.download_button(
                label="💾 Descargar Formato Guía Completo",
                data=output.getvalue(),
                file_name=f"formato_importacion_gestiones_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
            return True
            
    except Exception as e:
        st.error(f"❌ Error generando formato guía: {str(e)}")
        return False

def obtener_descripcion_campo(campo):
    """Retorna la descripción de cada campo para la guía"""
    descripciones = {
        'nit_cliente': 'Número de identificación tributaria del cliente. Debe existir en la base de datos.',
        'razon_social_cliente': 'Nombre legal completo de la empresa cliente.',
        'fecha_contacto': 'Fecha en que se realizó la gestión con el cliente.',
        'tipo_contacto': 'Medio o método utilizado para contactar al cliente.',
        'resultado': 'Resultado específico obtenido de la gestión realizada.',
        'observaciones': 'Comentarios, acuerdos o detalles adicionales de la gestión.',
        'promesa_pago_fecha': 'Fecha acordada para el pago prometido por el cliente.',
        'promesa_pago_monto': 'Valor monetario del pago prometido por el cliente.',
        'proxima_gestion': 'Fecha sugerida para el siguiente contacto o seguimiento.',
        'usuario': 'Email del usuario que realiza la gestión (opcional, se autocompleta).'
    }
    return descripciones.get(campo, 'Campo de información')

def obtener_formato_ejemplo(campo):
    """Retorna el formato y ejemplo para cada campo"""
    formatos = {
        'nit_cliente': 'Ejemplo: 9001234567',
        'razon_social_cliente': 'Ejemplo: EMPRESA EJEMPLO SAS',
        'fecha_contacto': 'Formato: YYYY-MM-DD. Ejemplo: 2024-01-15',
        'tipo_contacto': 'Usar valores del catálogo: Llamada telefónica, WhatsApp, etc.',
        'resultado': 'Usar códigos del 1-21 o texto completo. Ejemplo: 1. Promesa de Pago Total...',
        'observaciones': 'Texto libre. Ejemplo: Cliente confirmó pago para fecha acordada',
        'promesa_pago_fecha': 'Formato: YYYY-MM-DD. Ejemplo: 2024-01-22',
        'promesa_pago_monto': 'Solo números. Ejemplo: 1500000',
        'proxima_gestion': 'Formato: YYYY-MM-DD. Ejemplo: 2024-02-01',
        'usuario': 'Email válido. Ejemplo: usuario@empresa.com'
    }
    return formatos.get(campo, 'Consultar guía de campos')

def importar_gestiones_desde_archivo(archivo_subido):
    """Importa gestiones desde un archivo Excel con validaciones mejoradas"""
    
    try:
        with st.spinner("📥 Validando y importando gestiones..."):
            
            # Guardar archivo temporalmente
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                tmp_file.write(archivo_subido.getvalue())
                tmp_path = tmp_file.name
            
            # Importar usando DatabaseManager con validaciones mejoradas
            db = st.session_state.db
            success, message = db.importar_gestiones_excel(tmp_path)
            
            # Limpiar archivo temporal
            os.unlink(tmp_path)
            
            if success:
                st.success(f"✅ {message}")
                
                # Actualizar datos en sesión si hay cliente seleccionado
                if st.session_state.cliente_seleccionado_gestion:
                    nit_cliente = st.session_state.cliente_seleccionado_gestion['nit_cliente']
                    st.session_state.historial_gestiones = db.obtener_gestiones_cliente(nit_cliente)
                
                # Mostrar resumen de importación
                if "gestiones importadas" in message.lower():
                    partes = message.split(":")
                    if len(partes) > 0:
                        st.balloons()
                
                # Cerrar diálogo después de éxito
                st.session_state.mostrar_importar = False
                st.rerun()
                
            else:
                st.error(f"❌ {message}")
                # Mantener el diálogo abierto para que corrija errores
                
    except Exception as e:
        st.error(f"❌ Error crítico en la importación: {str(e)}")
        st.info("💡 Verifica que el archivo no esté corrupto y tenga el formato correcto")

def cargar_todos_los_clientes():
    """Carga TODOS los clientes disponibles - VERSIÓN ROBUSTA"""
    try:
        db = st.session_state.db
        clientes = db.obtener_clientes()
        
        if clientes.empty:
            st.warning("⚠️ No se encontraron clientes en la base de datos")
            return pd.DataFrame()
        
        print(f"✅ Clientes cargados: {len(clientes)} registros")
        return clientes
        
    except Exception as e:
        st.error(f"❌ Error cargando clientes: {e}")
        return pd.DataFrame()

def aplicar_filtros():
    """Aplica todos los filtros a la lista de clientes"""
    try:
        # Empezar con todos los clientes
        clientes_filtrados = st.session_state.todos_los_clientes.copy()
        
        # Aplicar filtro de texto si existe
        if st.session_state.texto_busqueda_gestion and st.session_state.texto_busqueda_gestion.strip():
            texto = st.session_state.texto_busqueda_gestion.lower().strip()
            clientes_filtrados = clientes_filtrados[
                clientes_filtrados['nit_cliente'].astype(str).str.lower().str.contains(texto, na=False) |
                clientes_filtrados['razon_social'].astype(str).str.lower().str.contains(texto, na=False) |
                clientes_filtrados['ciudad'].astype(str).str.lower().str.contains(texto, na=False)
            ]
        
        # Aplicar filtro adicional por tipo
        filtro_tipo = st.session_state.filtro_actual_gestion
        
        if filtro_tipo == "⚠️ Clientes en mora":
            clientes_filtrados = filtrar_clientes_en_mora(clientes_filtrados)
        
        elif filtro_tipo == "✅ Clientes con gestión este mes":
            clientes_filtrados = filtrar_clientes_con_gestion_mes(clientes_filtrados)
        
        elif filtro_tipo == "⏳ Clientes sin gestión este mes":
            clientes_filtrados = filtrar_clientes_sin_gestion_mes(clientes_filtrados)
        
        elif filtro_tipo == "📋 Clientes con gestión (histórico)":
            clientes_filtrados = filtrar_clientes_con_gestion_historico(clientes_filtrados)
        
        elif filtro_tipo == "📭 Clientes sin gestión (histórico)":
            clientes_filtrados = filtrar_clientes_sin_gestion_historico(clientes_filtrados)
        
        st.session_state.clientes_filtrados = clientes_filtrados
        
    except Exception as e:
        st.error(f"Error aplicando filtros: {e}")

def filtrar_clientes_en_mora(clientes):
    """Filtra clientes que tienen mora"""
    try:
        db = st.session_state.db
        cartera = db.obtener_cartera_actual()
        if not cartera.empty:
            clientes_mora = cartera[cartera['dias_vencidos'] > 0]['nit_cliente'].unique()
            return clientes[clientes['nit_cliente'].isin(clientes_mora)]
        return clientes
    except:
        return clientes

def filtrar_clientes_con_gestion_mes(clientes):
    """Filtra clientes con gestión este mes"""
    try:
        db = st.session_state.db
        gestiones_mes = db.obtener_gestiones_mes_actual()
        if not gestiones_mes.empty:
            clientes_con_gestion = gestiones_mes['nit_cliente'].unique()
            return clientes[clientes['nit_cliente'].isin(clientes_con_gestion)]
        return pd.DataFrame()
    except:
        return clientes

def filtrar_clientes_sin_gestion_mes(clientes):
    """Filtra clientes sin gestión este mes"""
    try:
        db = st.session_state.db
        gestiones_mes = db.obtener_gestiones_mes_actual()
        if not gestiones_mes.empty:
            clientes_con_gestion = gestiones_mes['nit_cliente'].unique()
            return clientes[~clientes['nit_cliente'].isin(clientes_con_gestion)]
        return clientes
    except:
        return clientes

def filtrar_clientes_con_gestion_historico(clientes):
    """Filtra clientes con gestión histórica"""
    try:
        db = st.session_state.db
        todas_gestiones = db.obtener_todas_gestiones()
        if not todas_gestiones.empty:
            clientes_con_gestion = todas_gestiones['nit_cliente'].unique()
            return clientes[clientes['nit_cliente'].isin(clientes_con_gestion)]
        return pd.DataFrame()
    except:
        return clientes

def filtrar_clientes_sin_gestion_historico(clientes):
    """Filtra clientes sin gestión histórica"""
    try:
        db = st.session_state.db
        todas_gestiones = db.obtener_todas_gestiones()
        if not todas_gestiones.empty:
            clientes_con_gestion = todas_gestiones['nit_cliente'].unique()
            return clientes[~clientes['nit_cliente'].isin(clientes_con_gestion)]
        return clientes
    except:
        return clientes

def seleccionar_cliente(cliente):
    """Selecciona un cliente y carga toda su información"""
    try:
        db = st.session_state.db
        
        # Guardar cliente seleccionado
        st.session_state.cliente_seleccionado_gestion = cliente.to_dict()
        st.session_state.datos_cliente_actual = cliente.to_dict()
        
        # Cargar cartera del cliente
        st.session_state.cartera_cliente_actual = db.obtener_cartera_actual()
        st.session_state.cartera_cliente_actual = st.session_state.cartera_cliente_actual[
            st.session_state.cartera_cliente_actual['nit_cliente'] == cliente['nit_cliente']
        ]
        
        # Calcular análisis de cartera
        st.session_state.analisis_cartera = calcular_analisis_cartera(
            st.session_state.cartera_cliente_actual
        )
        
        # Cargar historial de gestiones
        st.session_state.historial_gestiones = db.obtener_gestiones_cliente(cliente['nit_cliente'])
        
        st.rerun()
        
    except Exception as e:
        st.error(f"Error cargando información del cliente: {e}")

def calcular_analisis_cartera(cartera_cliente):
    """Calcula el análisis completo de la cartera del cliente"""
    if cartera_cliente.empty:
        return {
            'total_cartera': 0,
            'cartera_corriente': 0,
            'cartera_mora': 0,
            'dias_mora_max': 0,
            'num_facturas_total': 0,
            'num_facturas_corriente': 0,
            'num_facturas_vencidas': 0,
            'facturas_corriente': pd.DataFrame(),
            'facturas_vencidas': pd.DataFrame()
        }
    
    try:
        # Separar facturas corrientes y vencidas
        facturas_corriente = cartera_cliente[cartera_cliente['dias_vencidos'] == 0]
        facturas_vencidas = cartera_cliente[cartera_cliente['dias_vencidos'] > 0]
        
        return {
            'total_cartera': cartera_cliente['total_cop'].sum(),
            'cartera_corriente': facturas_corriente['total_cop'].sum(),
            'cartera_mora': facturas_vencidas['total_cop'].sum(),
            'dias_mora_max': facturas_vencidas['dias_vencidos'].max() if not facturas_vencidas.empty else 0,
            'num_facturas_total': len(cartera_cliente),
            'num_facturas_corriente': len(facturas_corriente),
            'num_facturas_vencidas': len(facturas_vencidas),
            'facturas_corriente': facturas_corriente,
            'facturas_vencidas': facturas_vencidas
        }
    except Exception as e:
        st.error(f"Error calculando análisis de cartera: {e}")
        return {
            'total_cartera': 0,
            'cartera_corriente': 0,
            'cartera_mora': 0,
            'dias_mora_max': 0,
            'num_facturas_total': 0,
            'num_facturas_corriente': 0,
            'num_facturas_vencidas': 0,
            'facturas_corriente': pd.DataFrame(),
            'facturas_vencidas': pd.DataFrame()
        }

def mostrar_facturas_formateadas(facturas_df):
    """Formatea el DataFrame de facturas para mostrar"""
    if facturas_df.empty:
        return pd.DataFrame()
    
    df_display = facturas_df.copy()
    
    # Seleccionar columnas importantes
    columnas = ['nro_factura', 'total_cop', 'fecha_emision', 'fecha_vencimiento', 'dias_vencidos', 'condicion_pago']
    columnas_existentes = [col for col in columnas if col in df_display.columns]
    df_display = df_display[columnas_existentes]
    
    # Formatear valores
    if 'total_cop' in df_display.columns:
        df_display['total_cop'] = df_display['total_cop'].apply(lambda x: f"${x:,.0f}")
    
    if 'dias_vencidos' in df_display.columns:
        df_display['dias_vencidos'] = df_display['dias_vencidos'].astype(int)
    
    # Renombrar columnas
    mapeo = {
        'nro_factura': 'Factura',
        'total_cop': 'Valor',
        'fecha_emision': 'Emisión',
        'fecha_vencimiento': 'Vencimiento',
        'dias_vencidos': 'Días Vencidos',
        'condicion_pago': 'Condición Pago'
    }
    
    df_display = df_display.rename(columns=mapeo)
    return df_display

def mostrar_estadisticas_generales_compactas():
    """Muestra estadísticas generales compactas"""
    try:
        db = st.session_state.db
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_clientes = len(st.session_state.todos_los_clientes)
            st.metric("Total Clientes", total_clientes)
        
        with col2:
            clientes_mora = len(filtrar_clientes_en_mora(st.session_state.todos_los_clientes))
            st.metric("Clientes en Mora", clientes_mora)
        
        with col3:
            clientes_gestion_mes = len(filtrar_clientes_con_gestion_mes(st.session_state.todos_los_clientes))
            st.metric("Gest. Este Mes", clientes_gestion_mes)
        
        with col4:
            gestiones_totales = len(db.obtener_todas_gestiones())
            st.metric("Total Gestiones", gestiones_totales)
            
    except Exception as e:
        st.error(f"Error cargando estadísticas: {e}")

def obtener_opciones_resultado():
    """Retorna las opciones de resultado categorizadas"""
    return [
        "💰 COMPROMISO DE PAGO",
        "1. Promesa de Pago Total (Fecha/Monto)",
        "2. Promesa de Pago Parcial (Fecha/Monto)",
        "3. Acuerdo de Pago Formalizado (Cuotas)",
        "4. Pago Efectuado / Cobro Exitoso",
        "",
        "📞 CONTACTO Y LOCALIZACIÓN",
        "5. Contacto Exitoso (Titular)",
        "6. Contacto con Tercero (Informó/Transmitió mensaje)",
        "7. Dejó Mensaje / Correo de Voz",
        "8. No Contesta / Ocupado",
        "9. Número Erróneo / Inexistente",
        "10. Email/Mensaje Enviado",
        "",
        "⚠️ DIFICULTAD Y RECHAZO",
        "11. Disputa / Reclamo de Facturación",
        "12. Problema de Servicio (Pendiente de Resolver)",
        "13. Negativa de Pago (Dificultad temporal)",
        "14. Negativa de Pago (Rechazo definitivo)",
        "15. Quiebra / Insolvencia Confirmada",
        "16. Cliente Inactivo / Ilocalizable",
        "",
        "🔄 SEGUIMIENTO Y ACCIONES INTERNAS",
        "17. Necesita Escalación (A Legal/Supervisión)",
        "18. Enviar Documentación Solicitada (Factura/Extracto)",
        "19. Agendar Nueva Llamada / Cita",
        "20. Datos Verificados / Actualizados",
        "21. Gestión No Finalizada (Reintentar pronto)"
    ]

def guardar_nueva_gestion(tipo_contacto, resultado, fecha_contacto, observaciones,
                         promesa_fecha, promesa_monto, proxima_gestion):
    """Guarda una nueva gestión en la base de datos"""
    
    try:
        cliente = st.session_state.cliente_seleccionado_gestion
        db = st.session_state.db
        
        # Validar campos obligatorios
        if not resultado or resultado.strip() == "" or resultado in [
            "💰 COMPROMISO DE PAGO", "📞 CONTACTO Y LOCALIZACIÓN", 
            "⚠️ DIFICULTAD Y RECHAZO", "🔄 SEGUIMIENTO Y ACCIONES INTERNAS", ""
        ]:
            st.error("❌ Por favor selecciona un resultado válido")
            return False
        
        # Preparar datos
        gestion_data = (
            cliente['nit_cliente'],
            cliente['razon_social'],
            tipo_contacto,
            resultado,
            fecha_contacto.strftime('%Y-%m-%d'),
            "",  # usuario se llena automáticamente en database.py
            observaciones,
            promesa_fecha.strftime('%Y-%m-%d') if promesa_fecha else None,
            float(promesa_monto) if promesa_monto and promesa_monto > 0 else None,
            proxima_gestion.strftime('%Y-%m-%d') if proxima_gestion else None
        )
        
        # Guardar en base de datos
        success = db.registrar_gestion(gestion_data)
        
        if success:
            # Actualizar historial
            st.session_state.historial_gestiones = db.obtener_gestiones_cliente(cliente['nit_cliente'])
            return True
        else:
            st.error("❌ Error al guardar la gestión")
            return False
            
    except Exception as e:
        st.error(f"❌ Error al guardar gestión: {str(e)}")
        return False

def cargar_historial_gestiones_cliente(nit_cliente):
    """Carga el historial de gestiones de un cliente específico"""
    try:
        db = st.session_state.db
        return db.obtener_gestiones_cliente(nit_cliente)
    except Exception as e:
        st.error(f"Error cargando historial: {e}")
        return pd.DataFrame()
    
# =============================================================================
# FUNCIONES DE NAVEGACIÓN DESDE CARTERA
# =============================================================================

def seleccionar_cliente_desde_cartera(nit_cliente):
    """Selecciona un cliente en el módulo de gestión desde cartera - VERSIÓN CORREGIDA"""
    try:
        # ✅ INICIALIZAR SI NO EXISTE
        if 'todos_los_clientes' not in st.session_state or st.session_state.todos_los_clientes.empty:
            st.session_state.todos_los_clientes = cargar_todos_los_clientes()
            st.session_state.clientes_filtrados = st.session_state.todos_los_clientes.copy()
        
        # Buscar el cliente por NIT
        cliente_encontrado = st.session_state.todos_los_clientes[
            st.session_state.todos_los_clientes['nit_cliente'] == nit_cliente
        ]
        
        if not cliente_encontrado.empty:
            # Seleccionar el cliente
            seleccionar_cliente(cliente_encontrado.iloc[0])
            return True
        else:
            st.error(f"❌ No se encontró el cliente con NIT: {nit_cliente}")
            return False
            
    except Exception as e:
        st.error(f"❌ Error seleccionando cliente: {e}")
        return False