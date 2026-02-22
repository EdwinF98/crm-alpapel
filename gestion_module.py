# gestion_module.py - VERSIÓN COMPACTA MEJORADA CON BOTONES SIEMPRE VISIBLES
import streamlit as st
import pandas as pd
from datetime import datetime
from docxtpl import DocxTemplate
import io
import tempfile
from config import Config as config
from datetime import datetime, timedelta
from reporte_pdf import generar_pdf_estado_cuenta
import os

def gestion_section():
    """Sección principal optimizada con llamadas a Dialog"""
    if 'gestion_initialized' not in st.session_state:
        st.session_state.cliente_seleccionado_gestion = None
        st.session_state.todos_los_clientes = cargar_todos_los_clientes()
        st.session_state.clientes_filtrados = st.session_state.todos_los_clientes.copy()
        st.session_state.gestion_initialized = True

    st.header("📋 Gestión de Cartera ALPAPEL")
    mostrar_busqueda_filtros()
    
    col_lista, col_detalle = st.columns([1, 2.5])

    with col_lista:
        mostrar_lista_clientes()

    with col_detalle:
        if st.session_state.cliente_seleccionado_gestion:
            cliente = st.session_state.cliente_seleccionado_gestion
            st.subheader(f"🏢 {cliente['razon_social']}")
            
            # --- KPI'S ---
            resumen = st.session_state.analisis_cartera
            m1, m2, m3 = st.columns(3)
            m1.metric("Saldo Total", f"${resumen['total_cartera']:,.0f}")
            m2.metric("En Mora", f"${resumen['cartera_mora']:,.0f}", delta_color="inverse")
            m3.metric("Días Máx", f"{int(resumen['dias_mora_max'])} días")

            # --- ACCIONES ---
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                # AQUÍ ESTÁ EL CAMBIO: Llamamos a la función con el decorador @st.dialog
                if st.button("📝 Registrar Gestión", use_container_width=True, type="primary"):
                    mostrar_formulario_gestion_dialog()
            
            with c2:
                try:
                    pdf = generar_pdf_estado_cuenta(cliente, st.session_state.cartera_cliente_actual)
                    st.download_button("📄 Bajar Estado Cuenta", data=pdf, 
                                     file_name=f"Estado_{cliente['nit_cliente']}.pdf", 
                                     mime="application/pdf", use_container_width=True)
                except:
                    st.error("Error PDF")

            mostrar_historial_gestiones()
        else:
            st.info("👈 Selecciona un cliente para empezar")

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
    """Muestra la lista de clientes evitando el bucle de reseteo de pantalla"""
    st.subheader("👥 Lista de Clientes")
    
    if not st.session_state.clientes_filtrados.empty:
        opciones_lista = ["--- Selecciona un cliente ---"]
        clientes_df = st.session_state.clientes_filtrados
        
        for _, row in clientes_df.iterrows():
            opciones_lista.append(f"{row['nit_cliente']} - {row['razon_social']}")
        
        # Determinar el índice actual para que el selectbox no se mueva solo
        index_actual = 0
        if st.session_state.cliente_seleccionado_gestion:
            nit_actual = st.session_state.cliente_seleccionado_gestion['nit_cliente']
            for i, opt in enumerate(opciones_lista):
                if nit_actual in opt:
                    index_actual = i
                    break

        seleccion = st.selectbox(
            "Seleccionar Cliente:",
            options=opciones_lista,
            index=index_actual,
            key="selector_maestro_gestion",
            label_visibility="collapsed"
        )
        
        if seleccion != "--- Selecciona un cliente ---":
            nit_nuevo = seleccion.split(" - ")[0].strip()
            # SOLO seleccionamos si es un cliente distinto al cargado
            if not st.session_state.cliente_seleccionado_gestion or \
               st.session_state.cliente_seleccionado_gestion['nit_cliente'] != nit_nuevo:
                
                cliente_row = clientes_df[clientes_df['nit_cliente'] == nit_nuevo].iloc[0]
                ejecutar_seleccion_limpia(cliente_row)
    else:
        st.warning("No hay clientes con esos filtros.")

def ejecutar_seleccion_limpia(cliente_row):
    """Carga los datos del cliente sin resetear variables de interfaz"""
    db = st.session_state.db
    cliente_dict = cliente_row.to_dict()
    nit = str(cliente_dict['nit_cliente'])
    
    # Cargar datos pesados a la sesión
    st.session_state.cliente_seleccionado_gestion = cliente_dict
    df_cartera = db.obtener_cartera_actual()
    st.session_state.cartera_cliente_actual = df_cartera[df_cartera['nit_cliente'] == nit]
    st.session_state.analisis_cartera = calcular_analisis_cartera(st.session_state.cartera_cliente_actual)
    st.session_state.historial_gestiones = db.obtener_gestiones_cliente(nit)
    st.rerun()

def mostrar_informacion_cliente():
    """Muestra el detalle completo, saldos y acciones del cliente seleccionado"""
    
    cliente = st.session_state.cliente_seleccionado_gestion
    analisis = st.session_state.get('analisis_cartera', {})
    
    # 1. Identificación del Cliente
    nombre = cliente.get('nombre_cliente') or cliente.get('razon_social') or "Cliente"
    
    st.markdown("---")
    st.subheader(f"👤 {nombre}")
    
    # Botón para limpiar selección y volver
    if st.button("← Volver a la lista completa", type="secondary", use_container_width=True):
        st.session_state.cliente_seleccionado_gestion = None
        st.rerun()
    
    # 2. Bloque de Datos Maestros
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("NIT", cliente.get('nit_cliente', 'N/A'), disabled=True)
        st.text_input("Teléfono", cliente.get('telefono', 'No disponible'), disabled=True)
    with col2:
        st.text_input("Vendedor Asignado", cliente.get('vendedor_asignado', 'No asignado'), disabled=True)
        st.text_input("Ciudad / Ruta", cliente.get('ciudad', 'No disponible'), disabled=True)

    st.markdown("---")
    
    # 3. Métrica de Cartera
    st.subheader("💰 Resumen de Cartera")
    total_cartera = analisis.get('total_cartera', 0)
    cartera_mora = analisis.get('cartera_mora', 0)
    facturas_vencidas = analisis.get('num_facturas_vencidas', 0)
    dias_max = analisis.get('dias_mora_max', 0)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Saldo Total", f"${total_cartera:,.0f}")
    m2.metric("En Mora", f"${cartera_mora:,.0f}", delta=f"{facturas_vencidas} facturas", delta_color="inverse")
    m3.metric("Días Mora Máx", f"{int(dias_max)} días")
    m4.metric("Días Crédito", f"{cliente.get('dias_credito', 0)}")

    # 4. BOTONES DE ACCIÓN (PDF DESDE PLANTILLA)
    st.markdown("### 🛠️ Acciones Disponibles")
    c_btn1, c_btn2 = st.columns(2)
    
    with c_btn1:
        try:
            # Llamamos al nuevo generador que usa la plantilla Word de assets
            # Solo pasamos cliente y la cartera actual del estado de sesión
            pdf_buffer = generar_pdf_estado_cuenta(
                cliente, 
                st.session_state.cartera_cliente_actual
            )
            
            if pdf_buffer:
                nombre_archivo = f"Estado_Cuenta_ALPAPEL_{str(nombre).replace(' ', '_').upper()}.pdf"
                st.download_button(
                    label="📄 Descargar Estado de Cuenta (PDF)",
                    data=pdf_buffer,
                    file_name=nombre_archivo,
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
        except Exception as e:
            st.error(f"No se pudo generar el PDF: {e}")

    with c_btn2:
        if st.button("📝 Registrar Gestión Manual", use_container_width=True):
            st.session_state.mostrar_formulario_gestion = True
            st.rerun()

    # 5. Detalle de Facturas en Tabs
    st.markdown("---")
    st.subheader("📄 Listado de Documentos")
    tab_mora, tab_al_dia = st.tabs(["⚠️ Facturas en Mora", "✅ Facturas al Día"])
    
    with tab_mora:
        f_vencidas = analisis.get('facturas_vencidas', pd.DataFrame())
        if not f_vencidas.empty:
            st.dataframe(mostrar_facturas_formateadas(f_vencidas), use_container_width=True, hide_index=True)
        else:
            st.success("Este cliente no tiene facturas vencidas.")

    with tab_al_dia:
        f_corriente = analisis.get('facturas_corriente', pd.DataFrame())
        if not f_corriente.empty:
            st.dataframe(mostrar_facturas_formateadas(f_corriente), use_container_width=True, hide_index=True)
        else:
            st.info("No hay facturas corrientes pendientes.")

@st.dialog("📝 Registrar Nueva Gestión")
def mostrar_formulario_gestion_dialog():
    """Formulario moderno en ventana emergente (Pop-up) con lógica inteligente"""
    cliente = st.session_state.cliente_seleccionado_gestion
    st.write(f"**Cliente:** {cliente.get('razon_social')}")
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            tipo_contacto = st.selectbox(
                "Tipo de Contacto:",
                options=["Llamada telefónica", "WhatsApp", "Correo electrónico", "Visita presencial"]
            )
            fecha_contacto = st.date_input("Fecha de Contacto:", value=datetime.now().date())
        
        with col2:
            opciones = obtener_opciones_resultado()
            # Quitamos los encabezados de categoría para que no los elijan por error
            opciones_limpias = [opt for opt in opciones if opt.strip() and not opt.startswith(("💰", "📞", "⚠️", "🔄"))]
            resultado = st.selectbox("Resultado de la Gestión:", options=opciones_limpias)

        # --- LÓGICA DINÁMICA PARA PROMESAS ---
        es_promesa = "Promesa" in resultado or "Acuerdo" in resultado
        
        if es_promesa:
            st.markdown("### 💰 Detalle de la Promesa")
            c3, c4 = st.columns(2)
            with c3:
                promesa_fecha = st.date_input("¿Para cuándo prometió pago?", value=datetime.now().date() + timedelta(days=5))
            with c4:
                promesa_monto = st.number_input("Monto de la promesa ($):", min_value=0.0, step=100000.0, format="%.0f")
            
            # Sugerencia automática de próxima gestión (2 días después de la promesa)
            sugerencia_prox = promesa_fecha + timedelta(days=2)
        else:
            promesa_fecha = None
            promesa_monto = 0
            # Sugerencia estándar (7 días)
            sugerencia_prox = datetime.now().date() + timedelta(days=7)

        st.markdown("---")
        c5, c6 = st.columns(2)
        with c5:
            proxima_gestion = st.date_input("📅 Agendar Próximo Seguimiento:", value=sugerencia_prox)
        with c6:
            st.info("💡 La fecha se ajusta automáticamente según el resultado.")

        observaciones = st.text_area("Observaciones Detalladas:", placeholder="Escribe aquí los acuerdos alcanzados...", height=100)

        if st.button("💾 Guardar Gestión Final", use_container_width=True, type="primary"):
            if not observaciones:
                st.error("Por favor agrega una observación.")
            else:
                success = guardar_nueva_gestion(
                    tipo_contacto, resultado, fecha_contacto, observaciones,
                    promesa_fecha, promesa_monto, proxima_gestion
                )
                if success:
                    st.success("¡Gestión Guardada!")
                    st.rerun() # Esto cierra el dialog automáticamente

def mostrar_historial_gestiones():
    """Muestra el historial de gestiones del cliente con información del usuario"""
    
    st.markdown("---")
    st.subheader("📊 Historial de Gestiones")
    
    if not st.session_state.historial_gestiones.empty:
        # Preparar datos para visualización con usuario
        df_display = st.session_state.historial_gestiones.copy()
        
        # Formatear columnas
        if 'promesa_pago_monto' in df_display.columns:
            df_display['promesa_pago_monto'] = df_display['promesa_pago_monto'].apply(
                lambda x: f"${x:,.0f}" if pd.notna(x) and x > 0 else "N/A"
            )
        
        # Formatear usuario (mostrar nombre corto)
        if 'usuario' in df_display.columns:
            df_display['usuario_display'] = df_display['usuario'].apply(
                lambda x: x.split('@')[0] if '@' in str(x) else str(x)
            )
        
        # Seleccionar y ordenar columnas para vista completa
        columnas_mostrar = [
            'fecha_contacto', 'usuario_display', 'tipo_contacto', 'resultado', 
            'observaciones', 'promesa_pago_fecha', 'promesa_pago_monto'
        ]
        
        # Asegurar que solo usamos columnas existentes
        columnas_existentes = [col for col in columnas_mostrar if col in df_display.columns]
        df_display = df_display[columnas_existentes]
        
        # Renombrar columnas para mejor legibilidad
        mapeo_nombres = {
            'fecha_contacto': '📅 Fecha',
            'usuario_display': '👤 Registrado por',
            'tipo_contacto': '📞 Tipo',
            'resultado': '🎯 Resultado',
            'observaciones': '📝 Observaciones',
            'promesa_pago_fecha': '💰 Fecha Promesa',
            'promesa_pago_monto': '💰 Monto Promesa'
        }
        
        # Renombrar solo las columnas que existen
        renombrar_dict = {old: new for old, new in mapeo_nombres.items() if old in df_display.columns}
        df_display = df_display.rename(columns=renombrar_dict)
        
        # Mostrar tabla
        st.dataframe(
            df_display,
            use_container_width=True,
            height=300,
            hide_index=True,
            column_config={
                '👤 Registrado por': st.column_config.TextColumn(
                    width="small",
                    help="Usuario que registró la gestión"
                ),
                '📅 Fecha': st.column_config.DateColumn(
                    format="DD/MM/YYYY",
                    help="Fecha de la gestión"
                ),
                '🎯 Resultado': st.column_config.TextColumn(
                    width="medium",
                    help="Resultado obtenido"
                )
            }
        )
        
        # Estadísticas del historial
        total_gestiones = len(st.session_state.historial_gestiones)
        if 'usuario' in st.session_state.historial_gestiones.columns:
            usuarios_unicos = st.session_state.historial_gestiones['usuario'].nunique()
            st.caption(f"📋 {total_gestiones} gestiones registradas | 👥 {usuarios_unicos} usuarios diferentes")
        else:
            st.caption(f"📋 {total_gestiones} gestiones registradas")
        
    else:
        st.info("ℹ️ No hay gestiones registradas para este cliente")

# =======================================
# FUNCIONES DE EXPORTACIÓN/IMPORTACIÓN
# =======================================

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
    """Importa gestiones desde un archivo Excel con validaciones mejoradas y muestra resumen detallado"""
    
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
                # Mostrar resumen expandido con formato mejorado
                st.success("### ✅ IMPORTACIÓN COMPLETADA")
                
                # Dividir el mensaje en líneas para mejor formato
                lineas = message.split('\n')
                for linea in lineas:
                    if linea.startswith('📊') or linea.startswith('⚠️'):
                        st.subheader(linea)
                    elif linea.startswith('•'):
                        st.write(linea)
                    elif linea.strip() and not linea.startswith('✅'):
                        st.info(linea)
                
                # Mostrar métricas visuales si hay gestiones importadas
                if "Gestiones importadas:" in message:
                    try:
                        # Extraer números del mensaje para métricas
                        import re
                        gestiones_importadas = re.search(r'Gestiones importadas: (\d+)', message)
                        clientes_unicos = re.search(r'Clientes únicos: (\d+)', message)
                        monto_promesas = re.search(r'Monto total promesas: \$([\d,]+)', message)
                        
                        if gestiones_importadas and clientes_unicos:
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Gestiones Importadas", gestiones_importadas.group(1))
                            with col2:
                                st.metric("Clientes Únicos", clientes_unicos.group(1))
                            with col3:
                                if monto_promesas:
                                    st.metric("Monto Promesas", monto_promesas.group(1))
                    except:
                        pass  # Si falla la extracción, continuar sin métricas
                
                # Actualizar datos en sesión si hay cliente seleccionado
                if st.session_state.cliente_seleccionado_gestion:
                    nit_cliente = st.session_state.cliente_seleccionado_gestion['nit_cliente']
                    st.session_state.historial_gestiones = db.obtener_gestiones_cliente(nit_cliente)
                
                # Botón para cerrar el diálogo después de revisar resultados
                st.markdown("---")
                if st.button("🗙 Cerrar y Volver a Gestión", type="primary", use_container_width=True):
                    st.session_state.mostrar_importar = False
                    st.rerun()
                
            else:
                st.error("### ❌ ERROR EN IMPORTACIÓN")
                
                # Mostrar errores con formato mejorado
                lineas = message.split('\n')
                for linea in lineas:
                    if linea.startswith('❌') or "Columnas requeridas" in linea:
                        st.error(linea)
                    elif linea.startswith('•'):
                        st.warning(linea)
                    elif linea.strip():
                        st.info(linea)
                
                # Mantener el diálogo abierto para que corrija errores
                st.warning("💡 Corrige los errores en el archivo y vuelve a intentar la importación")
                
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
        
        # CORRECCIÓN CRÍTICA: Unificar nombres de columnas
        # La BD usa 'razon_social' pero el código espera 'nombre_cliente'
        if 'razon_social' in clientes.columns and 'nombre_cliente' not in clientes.columns:
            clientes['nombre_cliente'] = clientes['razon_social']
        
        # Asegurar que NIT sea string
        clientes['nit_cliente'] = clientes['nit_cliente'].astype(str).str.strip()
        
        print(f"✅ Clientes cargados: {len(clientes)} registros")
        print(f"📊 Columnas disponibles: {clientes.columns.tolist()}")
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
        
        # Convertir a diccionario
        cliente_dict = cliente.to_dict()
        
        # CORRECCIÓN: Asegurar nombres de columnas
        if 'razon_social' in cliente_dict and 'nombre_cliente' not in cliente_dict:
            cliente_dict['nombre_cliente'] = cliente_dict['razon_social']
        
        # Normalizar NIT
        nit_cliente = str(cliente_dict.get('nit_cliente', '')).strip()
        cliente_dict['nit_cliente'] = nit_cliente
        
        # Guardar en sesión
        st.session_state.cliente_seleccionado_gestion = cliente_dict
        st.session_state.datos_cliente_actual = cliente_dict
        
        # Cargar cartera
        df_cartera = db.obtener_cartera_actual()
        
        if not df_cartera.empty:
            # Asegurar tipos
            df_cartera['nit_cliente'] = df_cartera['nit_cliente'].astype(str).str.strip()
            
            # CORRECCIÓN: Mapear columnas de cartera
            # La BD usa 'total_cop', el código espera 'saldo'
            if 'total_cop' in df_cartera.columns and 'saldo' not in df_cartera.columns:
                df_cartera['saldo'] = df_cartera['total_cop']
            
            # La BD usa 'nro_factura', el código espera 'documento'
            if 'nro_factura' in df_cartera.columns and 'documento' not in df_cartera.columns:
                df_cartera['documento'] = df_cartera['nro_factura']
            
            # Filtrar por NIT
            st.session_state.cartera_cliente_actual = df_cartera[
                df_cartera['nit_cliente'] == nit_cliente
            ]
        else:
            st.session_state.cartera_cliente_actual = pd.DataFrame()
        
        # Calcular análisis
        st.session_state.analisis_cartera = calcular_analisis_cartera(
            st.session_state.cartera_cliente_actual
        )
        
        # Cargar historial
        st.session_state.historial_gestiones = db.obtener_gestiones_cliente(nit_cliente)
        
        # Cerrar formulario si estaba abierto
        st.session_state.mostrar_formulario_gestion = False
        
        st.rerun()
        
    except Exception as e:
        st.error(f"Error cargando información del cliente: {e}")
        import traceback
        traceback.print_exc()

def calcular_analisis_cartera(cartera_cliente):
    """Calcula el análisis usando la columna correcta"""
    base_stats = {
        'total_cartera': 0, 'cartera_corriente': 0, 'cartera_mora': 0,
        'dias_mora_max': 0, 'num_facturas_total': 0,
        'num_facturas_corriente': 0, 'num_facturas_vencidas': 0,
        'facturas_corriente': pd.DataFrame(), 'facturas_vencidas': pd.DataFrame()
    }

    if cartera_cliente.empty:
        return base_stats
    
    try:
        # Determinar columna de monto
        col_monto = None
        for col in ['saldo', 'total_cop']:
            if col in cartera_cliente.columns:
                col_monto = col
                break
        
        if col_monto is None:
            return base_stats
        
        facturas_corriente = cartera_cliente[cartera_cliente['dias_vencidos'] <= 0]
        facturas_vencidas = cartera_cliente[cartera_cliente['dias_vencidos'] > 0]
        
        return {
            'total_cartera': cartera_cliente[col_monto].sum(),
            'cartera_corriente': facturas_corriente[col_monto].sum(),
            'cartera_mora': facturas_vencidas[col_monto].sum(),
            'dias_mora_max': cartera_cliente['dias_vencidos'].max() if not cartera_cliente.empty else 0,
            'num_facturas_total': len(cartera_cliente),
            'num_facturas_corriente': len(facturas_corriente),
            'num_facturas_vencidas': len(facturas_vencidas),
            'facturas_corriente': facturas_corriente,
            'facturas_vencidas': facturas_vencidas
        }
    except Exception as e:
        print(f"Error en cálculos: {e}")
        return base_stats

def mostrar_facturas_formateadas(facturas_df):
    """Formatea el DataFrame usando 'saldo' y 'documento'"""
    if facturas_df.empty:
        return pd.DataFrame()
    
    df_display = facturas_df.copy()
    
    # Mapeo de columnas dinámico para evitar KeyErrors
    columnas_posibles = {
        'documento': 'Factura',
        'nro_factura': 'Factura',
        'saldo': 'Valor',
        'total_cop': 'Valor',
        'fecha_emision': 'Emisión',
        'fecha_vencimiento': 'Vencimiento',
        'dias_vencidos': 'Días Vencidos'
    }
    
    # Renombrar solo las que existan
    columnas_a_renombrar = {k: v for k, v in columnas_posibles.items() if k in df_display.columns}
    df_display = df_display[list(columnas_a_renombrar.keys())].rename(columns=columnas_a_renombrar)
    
    # Formatear moneda en la columna 'Valor'
    if 'Valor' in df_display.columns:
        df_display['Valor'] = df_display['Valor'].apply(lambda x: f"${x:,.0f}")
        
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

def mostrar_estadisticas_gestion_usuario():
    """Muestra estadísticas de gestión por usuario (solo para admin/supervisor)"""
    try:
        user = st.session_state.get('user', {})
        
        if user.get('rol') not in ['admin', 'supervisor']:
            return
        
        st.markdown("---")
        st.subheader("👥 Estadísticas por Usuario")
        
        # Obtener usuarios con gestiones
        db = st.session_state.db
        usuarios_con_gestiones = db.obtener_usuarios_con_gestiones()
        
        if not usuarios_con_gestiones.empty:
            # Obtener todas las gestiones
            todas_gestiones = db.obtener_todas_gestiones()
            
            # Calcular estadísticas por usuario
            stats = []
            for _, usuario in usuarios_con_gestiones.iterrows():
                email = usuario['email']
                gestiones_usuario = todas_gestiones[todas_gestiones['usuario'] == email]
                
                if not gestiones_usuario.empty:
                    stats.append({
                        'Usuario': usuario['nombre_completo'],
                        'Email': email,
                        'Vendedor': usuario['vendedor_asignado'] or 'No asignado',
                        'Total Gestiones': len(gestiones_usuario),
                        'Última Gestión': gestiones_usuario['fecha_contacto'].max(),
                        'Clientes Únicos': gestiones_usuario['nit_cliente'].nunique()
                    })
            
            if stats:
                df_stats = pd.DataFrame(stats)
                
                # Mostrar métricas resumidas
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Usuarios Activos", len(stats))
                with col2:
                    total_gestiones = df_stats['Total Gestiones'].sum()
                    st.metric("Total Gestiones", f"{total_gestiones:,}")
                with col3:
                    promedio = total_gestiones / len(stats) if len(stats) > 0 else 0
                    st.metric("Promedio por Usuario", f"{promedio:.1f}")
                
                # Mostrar tabla detallada
                st.dataframe(
                    df_stats.sort_values('Total Gestiones', ascending=False),
                    use_container_width=True,
                    height=250,
                    hide_index=True
                )
        else:
            st.info("No hay datos de gestión por usuario disponibles")
            
    except Exception as e:
        print(f"Error mostrando estadísticas por usuario: {e}")

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
    """Guarda una nueva gestión en la base de datos con información del usuario"""
    
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
        
        # Obtener usuario actual
        usuario_actual = ""
        if st.session_state.get('user'):
            usuario_actual = st.session_state.user.get('email', '')
        
        # Preparar datos (usuario se llena automáticamente en database.py)
        gestion_data = (
            cliente['nit_cliente'],
            cliente['razon_social'],
            tipo_contacto,
            resultado,
            fecha_contacto.strftime('%Y-%m-%d'),
            usuario_actual,  # Se pasa el email del usuario
            observaciones,
            promesa_fecha.strftime('%Y-%m-%d') if promesa_fecha else None,
            float(promesa_monto) if promesa_monto and promesa_monto > 0 else None,
            proxima_gestion.strftime('%Y-%m-%d') if proxima_gestion else None
        )
        
        # Guardar en base de datos
        success = db.registrar_gestion(gestion_data)
        
        if success:
            # Mostrar confirmación con información del usuario
            usuario_nombre = st.session_state.user.get('nombre_completo', usuario_actual) if st.session_state.get('user') else usuario_actual
            st.success(f"✅ Gestión guardada correctamente por: {usuario_nombre}")
            
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
    """Selecciona un cliente en el módulo de gestión desde cartera"""
    try:
        # Inicializar si no existe
        if 'todos_los_clientes' not in st.session_state or st.session_state.todos_los_clientes.empty:
            st.session_state.todos_los_clientes = cargar_todos_los_clientes()
            st.session_state.clientes_filtrados = st.session_state.todos_los_clientes.copy()
        
        # Normalizar NIT de entrada
        nit_cliente = str(nit_cliente).strip()
        
        # Normalizar columna NIT en DataFrame
        clientes_df = st.session_state.todos_los_clientes.copy()
        clientes_df['nit_cliente'] = clientes_df['nit_cliente'].astype(str).str.strip()
        
        # Buscar cliente
        cliente_encontrado = clientes_df[clientes_df['nit_cliente'] == nit_cliente]
        
        if not cliente_encontrado.empty:
            seleccionar_cliente(cliente_encontrado.iloc[0])
            return True
        else:
            st.error(f"❌ No se encontró el cliente con NIT: {nit_cliente}")
            return False
            
    except Exception as e:
        st.error(f"❌ Error seleccionando cliente: {e}")
        return False