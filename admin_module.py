# admin_module.py - VERSIÓN TEMPORAL SIN ESTADÍSTICAS
import streamlit as st
import pandas as pd
from datetime import datetime
from config import config

def admin_section():
    """Sección de administración del sistema"""
    st.header("🛡️ Panel de Administración")
    
    # Verificar permisos de administrador
    if not st.session_state.auth_manager.has_permission('manage_users'):
        st.error("❌ No tienes permisos para acceder a esta sección")
        return
    
    # Pestañas de administración
    tab1, tab2, tab3 = st.tabs(["👥 Gestión de Usuarios", "📊 Estadísticas del Sistema", "⚙️ Configuración"])
    
    with tab1:
        st.subheader("👥 Gestión de Usuarios")
        
        # Formulario para crear nuevo usuario
        with st.expander("➕ Crear Nuevo Usuario", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                email = st.text_input("📧 Email", placeholder="usuario@alpapel.com")
                nombre_completo = st.text_input("👤 Nombre Completo", placeholder="Nombre Apellido")
                rol = st.selectbox(
                    "🎭 Rol",
                    options=list(config.ROLES.keys()),
                    format_func=lambda x: config.ROLES[x]
                )
            
            with col2:
                vendedores_df = st.session_state.user_manager.obtener_vendedores()
                vendedores_opciones = ["No asignado"] + vendedores_df['nombre_vendedor'].tolist()
                vendedor = st.selectbox("👤 Vendedor Asignado", options=vendedores_opciones)
                if vendedor == "No asignado":
                    vendedor = None
                
                activo = st.checkbox("✅ Usuario Activo", value=True)
            
            # BOTÓN DE CREAR USUARIO CON DEBUG
            if st.button("🚀 Crear Usuario", type="primary", key="btn_crear_usuario"):
                if email and nombre_completo:
                    print(f"🔍 DEBUG ADMIN - Iniciando creación de usuario: {email}")
                    
                    # Validar email del dominio
                    if not st.session_state.user_manager.is_valid_email(email):
                        st.error("❌ El email debe ser del dominio @alpapel.com")
                    else:
                        with st.spinner("Creando usuario..."):
                            try:
                                # LLAMAR AL MÉTODO DE CREACIÓN
                                success, message = st.session_state.user_manager.crear_usuario(
                                    email, nombre_completo, rol, vendedor, activo
                                )
                                
                                print(f"🔍 DEBUG ADMIN - Resultado creación: success={success}, message={message}")
                                
                                if success:
                                    st.success(f"✅ {message}")
                                    # Forzar actualización de la lista de usuarios
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                                    
                            except Exception as e:
                                print(f"❌ DEBUG ADMIN - Error en creación: {str(e)}")
                                st.error(f"❌ Error creando usuario: {str(e)}")
                else:
                    st.warning("⚠️ Por favor completa todos los campos obligatorios")
        
        # Lista de usuarios existentes
        st.subheader("📋 Usuarios del Sistema")
        
        try:
            usuarios_df = st.session_state.user_manager.obtener_usuarios()
            
            if not usuarios_df.empty:
                # Mostrar tabla de usuarios
                display_df = usuarios_df.copy()
                display_df['activo'] = display_df['activo'].apply(lambda x: '✅ Sí' if x == 1 else '❌ No')
                display_df['email_verificado'] = display_df['email_verificado'].apply(lambda x: '✅ Sí' if x == 1 else '❌ No')
                display_df['rol'] = display_df['rol'].apply(lambda x: config.ROLES.get(x, x))
                
                # Formatear fechas
                if 'fecha_creacion' in display_df.columns:
                    display_df['fecha_creacion'] = pd.to_datetime(display_df['fecha_creacion']).dt.strftime('%Y-%m-%d %H:%M')
                if 'ultimo_login' in display_df.columns:
                    display_df['ultimo_login'] = pd.to_datetime(display_df['ultimo_login']).dt.strftime('%Y-%m-%d %H:%M')
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Opciones de gestión por usuario
                st.subheader("⚙️ Gestión por Usuario")
                usuarios_lista = [f"{row['email']} - {row['nombre_completo']}" for _, row in usuarios_df.iterrows()]
                usuario_seleccionado = st.selectbox("Selecciona un usuario:", options=usuarios_lista, key="select_usuario_gestion")
                
                if usuario_seleccionado:
                    usuario_id = usuarios_df[usuarios_df['email'] == usuario_seleccionado.split(' - ')[0]]['id'].iloc[0]
                    usuario_data = usuarios_df[usuarios_df['id'] == usuario_id].iloc[0]
                    
                    col_gest1, col_gest2, col_gest3 = st.columns(3)
                    
                    with col_gest1:
                        st.write("**Editar Usuario:**")
                        nuevo_nombre = st.text_input("Nombre", value=usuario_data['nombre_completo'], key=f"nombre_{usuario_id}")
                        nuevo_rol = st.selectbox(
                            "Rol", 
                            options=list(config.ROLES.keys()),
                            index=list(config.ROLES.keys()).index(usuario_data['rol']),
                            format_func=lambda x: config.ROLES[x],
                            key=f"rol_{usuario_id}"
                        )
                        nuevo_vendedor = st.selectbox(
                            "Vendedor",
                            options=vendedores_opciones,
                            index=vendedores_opciones.index(usuario_data['vendedor_asignado']) if usuario_data['vendedor_asignado'] in vendedores_opciones else 0,
                            key=f"vendedor_{usuario_id}"
                        )
                        nuevo_activo = st.checkbox("Activo", value=usuario_data['activo'] == 1, key=f"activo_{usuario_id}")
                        
                        if st.button("💾 Actualizar Usuario", key=f"btn_actualizar_{usuario_id}"):
                            datos_actualizados = {
                                'nombre_completo': nuevo_nombre,
                                'rol': nuevo_rol,
                                'vendedor_asignado': nuevo_vendedor if nuevo_vendedor != "No asignado" else None,
                                'activo': 1 if nuevo_activo else 0
                            }
                            success, message = st.session_state.user_manager.actualizar_usuario(usuario_id, datos_actualizados)
                            if success:
                                st.success(f"✅ {message}")
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                    
                    with col_gest2:
                        st.write("**Cambiar Contraseña:**")
                        nueva_password = st.text_input("Nueva Contraseña", type="password", key=f"password_{usuario_id}")
                        if st.button("🔐 Cambiar Contraseña", key=f"btn_password_{usuario_id}"):
                            if nueva_password:
                                success, message = st.session_state.user_manager.cambiar_password(usuario_id, nueva_password)
                                if success:
                                    st.success(f"✅ {message}")
                                else:
                                    st.error(f"❌ {message}")
                            else:
                                st.warning("⚠️ Ingresa una nueva contraseña")
                    
                    with col_gest3:
                        st.write("**Acciones Peligrosas:**")
                        if st.button("🗑️ Eliminar Usuario", type="secondary", key=f"btn_eliminar_{usuario_id}"):
                            if usuario_data['email'] == st.session_state.user['email']:
                                st.error("❌ No puedes eliminarte a ti mismo")
                            else:
                                success, message = st.session_state.user_manager.eliminar_usuario(usuario_id)
                                if success:
                                    st.success(f"✅ {message}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
            else:
                st.info("📝 No hay usuarios registrados en el sistema")
                
        except Exception as e:
            st.error(f"❌ Error cargando usuarios: {str(e)}")
            print(f"❌ DEBUG ADMIN - Error obteniendo usuarios: {e}")
    
    with tab2:
        st.subheader("📊 Estadísticas del Sistema")
        
        try:
            stats = st.session_state.user_manager.obtener_estadisticas_sistema()
            
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            
            with col_stat1:
                st.metric("👥 Total Usuarios", stats['total_usuarios'])
            
            with col_stat2:
                st.metric("✅ Usuarios Activos", stats['usuarios_activos'])
            
            with col_stat3:
                st.metric("🔐 Logins Hoy", stats['logins_hoy'])
            
            with col_stat4:
                st.metric("🌐 Sesiones Activas", stats['sesiones_activas'])
            
        except Exception as e:
            st.error(f"❌ Error cargando estadísticas: {str(e)}")
    
    with tab3:
        st.subheader("⚙️ Configuración del Sistema")
        st.info("""
        **Configuración Actual:**
        - ⏰ Timeout de sesión: 60 minutos
        - 🔐 Longitud mínima de contraseña: 8 caracteres
        - 🚫 Intentos de login máximos: 5
        - ⏳ Tiempo de bloqueo: 30 minutos
        """)
        
        if st.button("🔄 Recargar Configuración", type="secondary"):
            st.rerun()

def gestion_usuarios_section():
    """Sección de gestión de usuarios"""
    st.subheader("👥 Gestión de Usuarios")
    
    # Barra de acciones
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.info("💡 Gestiona todos los usuarios del sistema desde aquí")
    
    with col2:
        if st.button("➕ Nuevo Usuario", use_container_width=True, type="primary"):
            st.session_state.mostrar_crear_usuario = True
            st.session_state.mostrar_editar_usuario = False
            st.rerun()
    
    with col3:
        if st.button("🔄 Actualizar Lista", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    # Mostrar formularios si están activos
    if st.session_state.mostrar_crear_usuario:
        mostrar_formulario_crear_usuario()
    
    if st.session_state.mostrar_editar_usuario and st.session_state.usuario_editar:
        mostrar_formulario_editar_usuario()
    
    # Mostrar tabla de usuarios
    mostrar_tabla_usuarios()

def mostrar_formulario_crear_usuario():
    """Muestra formulario para crear nuevo usuario"""
    st.subheader("📝 Crear Nuevo Usuario")
    
    with st.form("form_crear_usuario", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            email = st.text_input("📧 Email *", placeholder="usuario@alpapel.com", key="crear_email")
            nombre_completo = st.text_input("👤 Nombre Completo *", placeholder="Nombre Apellido", key="crear_nombre")
            rol = st.selectbox("🎭 Rol *", ["comercial", "consulta", "supervisor", "admin"], key="crear_rol")
        
        with col2:
            # Obtener vendedores disponibles de forma segura
            try:
                vendedores_df = st.session_state.user_manager.obtener_vendedores()
                vendedores = ["No asignado"] + vendedores_df['nombre_vendedor'].tolist() if not vendedores_df.empty else ["No asignado"]
            except:
                vendedores = ["No asignado"]
            
            vendedor_asignado = st.selectbox("👤 Vendedor Asignado", vendedores, key="crear_vendedor")
            activo = st.checkbox("✅ Usuario Activo", value=True, key="crear_activo")
        
        st.markdown("**ℹ️ Se generará una contraseña temporal automáticamente**")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submitted = st.form_submit_button("💾 Crear Usuario", type="primary", use_container_width=True)
        with col_btn2:
            cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if submitted:
            if not email or not nombre_completo:
                st.error("❌ Email y nombre completo son obligatorios")
                return
            
            if not email.endswith('@alpapel.com'):
                st.error("❌ El email debe ser del dominio @alpapel.com")
                return
            
            # Crear usuario
            try:
                success, message = st.session_state.user_manager.crear_usuario(
                    email=email,
                    nombre_completo=nombre_completo,
                    rol=rol,
                    vendedor_asignado=vendedor_asignado if vendedor_asignado != "No asignado" else None,
                    activo=activo
                )
                
                if success:
                    st.success(f"✅ {message}")
                    st.session_state.mostrar_crear_usuario = False
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
            except Exception as e:
                st.error(f"❌ Error al crear usuario: {str(e)}")
        
        if cancelar:
            st.session_state.mostrar_crear_usuario = False
            st.rerun()

def mostrar_formulario_editar_usuario():
    """Muestra formulario para editar usuario existente"""
    usuario = st.session_state.usuario_editar
    
    st.subheader(f"✏️ Editando Usuario: {usuario['email']}")
    
    with st.form("form_editar_usuario", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("📧 Email", value=usuario['email'], disabled=True)
            nombre_completo = st.text_input("👤 Nombre Completo *", value=usuario['nombre_completo'])
            rol = st.selectbox("🎭 Rol *", ["comercial", "consulta", "supervisor", "admin"], 
                             index=["comercial", "consulta", "supervisor", "admin"].index(usuario['rol']))
        
        with col2:
            # Obtener vendedores disponibles de forma segura
            try:
                vendedores_df = st.session_state.user_manager.obtener_vendedores()
                vendedores = ["No asignado"] + vendedores_df['nombre_vendedor'].tolist() if not vendedores_df.empty else ["No asignado"]
            except:
                vendedores = ["No asignado"]
            
            vendedor_actual = usuario.get('vendedor_asignado', '') or "No asignado"
            vendedor_index = vendedores.index(vendedor_actual) if vendedor_actual in vendedores else 0
            vendedor_asignado = st.selectbox("👤 Vendedor Asignado", vendedores, index=vendedor_index)
            
            activo = st.checkbox("✅ Usuario Activo", value=bool(usuario['activo']))
        
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            submitted = st.form_submit_button("💾 Guardar Cambios", type="primary", use_container_width=True)
        with col_btn2:
            cambiar_pass = st.form_submit_button("🔑 Cambiar Contraseña", use_container_width=True)
        with col_btn3:
            cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if submitted:
            if not nombre_completo:
                st.error("❌ El nombre completo es obligatorio")
                return
            
            # Actualizar usuario
            try:
                success, message = st.session_state.user_manager.actualizar_usuario(
                    user_id=usuario['id'],
                    datos={
                        'nombre_completo': nombre_completo,
                        'rol': rol,
                        'vendedor_asignado': vendedor_asignado if vendedor_asignado != "No asignado" else None,
                        'activo': 1 if activo else 0
                    }
                )
                
                if success:
                    st.success("✅ Usuario actualizado correctamente")
                    st.session_state.mostrar_editar_usuario = False
                    st.session_state.usuario_editar = None
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
            except Exception as e:
                st.error(f"❌ Error al actualizar usuario: {str(e)}")
        
        if cambiar_pass:
            st.session_state.cambiar_password_usuario_id = usuario['id']
            st.rerun()
        
        if cancelar:
            st.session_state.mostrar_editar_usuario = False
            st.session_state.usuario_editar = None
            st.rerun()

def mostrar_tabla_usuarios():
    """Muestra la tabla de usuarios con opciones de gestión"""
    st.subheader("📋 Lista de Usuarios")
    
    # Obtener usuarios de forma segura
    try:
        usuarios_df = st.session_state.user_manager.obtener_usuarios()
    except Exception as e:
        st.error(f"❌ Error al cargar usuarios: {str(e)}")
        return
    
    if usuarios_df.empty:
        st.info("📝 No hay usuarios registrados en el sistema")
        return
    
    # Preparar datos para mostrar
    display_df = usuarios_df.copy()
    
    # Formatear columnas
    display_df['rol'] = display_df['rol'].apply(lambda x: config.ROLES.get(x, x))
    display_df['vendedor_asignado'] = display_df['vendedor_asignado'].fillna('No asignado')
    display_df['activo'] = display_df['activo'].apply(lambda x: '✅ Activo' if x == 1 else '❌ Inactivo')
    
    # Manejar fechas de último login de forma segura
    try:
        display_df['ultimo_login'] = pd.to_datetime(display_df['ultimo_login']).dt.strftime('%Y-%m-%d %H:%M')
        display_df['ultimo_login'] = display_df['ultimo_login'].replace('NaT', 'Nunca')
    except:
        display_df['ultimo_login'] = display_df['ultimo_login'].fillna('Nunca')
    
    # Mostrar tabla
    st.dataframe(
        display_df[['email', 'nombre_completo', 'rol', 'vendedor_asignado', 'activo', 'ultimo_login']],
        use_container_width=True,
        hide_index=True
    )
    
    # Sistema de selección para acciones
    st.markdown("---")
    st.subheader("🔧 Acciones por Usuario")
    
    # Crear lista de opciones para selección
    opciones_usuarios = ["--- Selecciona un usuario ---"] + [
        f"{row['email']} - {row['nombre_completo']} ({'✅ Activo' if row['activo'] == 1 else '❌ Inactivo'})" 
        for _, row in usuarios_df.iterrows()
    ]
    
    usuario_seleccionado = st.selectbox(
        "Selecciona un usuario para gestionar:",
        options=opciones_usuarios,
        key="selector_usuario_admin"
    )
    
    if usuario_seleccionado and usuario_seleccionado != "--- Selecciona un usuario ---":
        email_usuario = usuario_seleccionado.split(" - ")[0]
        usuario_data = usuarios_df[usuarios_df['email'] == email_usuario].iloc[0]
        
        # Mostrar información del usuario seleccionado
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            st.write(f"**Email:** {usuario_data['email']}")
            st.write(f"**Nombre:** {usuario_data['nombre_completo']}")
            st.write(f"**Rol:** {config.ROLES.get(usuario_data['rol'], usuario_data['rol'])}")
        
        with col_info2:
            st.write(f"**Vendedor:** {usuario_data['vendedor_asignado'] or 'No asignado'}")
            st.write(f"**Estado:** {'✅ Activo' if usuario_data['activo'] == 1 else '❌ Inactivo'}")
            st.write(f"**Último login:** {usuario_data['ultimo_login'] if pd.notna(usuario_data['ultimo_login']) else 'Nunca'}")
        
        # Botones de acción
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            if st.button("✏️ Editar Usuario", use_container_width=True, key=f"editar_{usuario_data['id']}"):
                st.session_state.usuario_editar = usuario_data.to_dict()
                st.session_state.mostrar_editar_usuario = True
                st.session_state.mostrar_crear_usuario = False
                st.rerun()
        
        with col_btn2:
            if st.button("🔑 Cambiar Contraseña", use_container_width=True, key=f"password_{usuario_data['id']}"):
                st.session_state.cambiar_password_usuario_id = usuario_data['id']
                st.rerun()
        
        with col_btn3:
            # No permitir eliminarse a sí mismo
            if usuario_data['id'] == st.session_state.user['id']:
                st.button("🗑️ Eliminar (No disponible)", use_container_width=True, disabled=True, 
                         help="No puedes eliminarte a ti mismo")
            else:
                if st.button("🗑️ Eliminar Usuario", use_container_width=True, type="secondary", 
                           key=f"eliminar_{usuario_data['id']}"):
                    st.session_state.usuario_eliminar = usuario_data
                    st.rerun()
    
    # Manejar cambio de contraseña
    if 'cambiar_password_usuario_id' in st.session_state:
        cambiar_password_usuario(st.session_state.cambiar_password_usuario_id)
    
    # Manejar eliminación de usuario
    if 'usuario_eliminar' in st.session_state:
        eliminar_usuario_confirmacion(st.session_state.usuario_eliminar)

def cambiar_password_usuario(user_id):
    """Diálogo para cambiar contraseña de usuario"""
    st.subheader("🔑 Cambiar Contraseña")
    
    with st.form("form_cambiar_password"):
        nueva_password = st.text_input("Nueva Contraseña", type="password", 
                                     placeholder="Ingresa la nueva contraseña")
        confirmar_password = st.text_input("Confirmar Contraseña", type="password",
                                         placeholder="Confirma la nueva contraseña")
        
        col1, col2 = st.columns(2)
        with col1:
            guardar = st.form_submit_button("💾 Cambiar Contraseña", type="primary", use_container_width=True)
        with col2:
            cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if guardar:
            if not nueva_password or not confirmar_password:
                st.error("❌ Ambas contraseñas son obligatorias")
                return
            
            if nueva_password != confirmar_password:
                st.error("❌ Las contraseñas no coinciden")
                return
            
            # Validar fortaleza de contraseña
            try:
                is_valid, message = st.session_state.user_manager.is_strong_password(nueva_password)
                if not is_valid:
                    st.error(f"❌ {message}")
                    return
            except:
                st.error("❌ Error al validar la contraseña")
                return
            
            # Cambiar contraseña
            try:
                success, message = st.session_state.user_manager.cambiar_password(user_id, nueva_password)
                
                if success:
                    st.success("✅ Contraseña cambiada correctamente")
                    if 'cambiar_password_usuario_id' in st.session_state:
                        del st.session_state.cambiar_password_usuario_id
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
            except Exception as e:
                st.error(f"❌ Error al cambiar contraseña: {str(e)}")
        
        if cancelar:
            if 'cambiar_password_usuario_id' in st.session_state:
                del st.session_state.cambiar_password_usuario_id
            st.rerun()

def eliminar_usuario_confirmacion(usuario_data):
    """Diálogo de confirmación para eliminar usuario"""
    st.subheader("🗑️ Confirmar Eliminación")
    
    st.warning(f"""
    ⚠️ **Estás a punto de eliminar al usuario:**
    
    **Email:** {usuario_data['email']}
    **Nombre:** {usuario_data['nombre_completo']}
    **Rol:** {config.ROLES.get(usuario_data['rol'], usuario_data['rol'])}
    
    **Esta acción no se puede deshacer.**
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Confirmar Eliminación", type="primary", use_container_width=True):
            try:
                success, message = st.session_state.user_manager.eliminar_usuario(usuario_data['id'])
                
                if success:
                    st.success("✅ Usuario eliminado correctamente")
                    if 'usuario_eliminar' in st.session_state:
                        del st.session_state.usuario_eliminar
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
            except Exception as e:
                st.error(f"❌ Error al eliminar usuario: {str(e)}")
    
    with col2:
        if st.button("❌ Cancelar", use_container_width=True):
            if 'usuario_eliminar' in st.session_state:
                del st.session_state.usuario_eliminar
            st.rerun()

def configuracion_section():
    """Sección de configuración del sistema"""
    st.subheader("⚙️ Configuración del Sistema")
    
    st.info("🚧 **Módulo en construcción** - Próximamente más opciones de configuración")
    
    # Mostrar estadísticas básicas aquí temporalmente
    st.subheader("📊 Información Básica del Sistema")
    
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.info(f"""
        **🛡️ Información de Seguridad:**
        - Sesión activa: {st.session_state.user['nombre_completo']}
        - Rol actual: {config.ROLES.get(st.session_state.user['rol'])}
        - Tiempo restante: {st.session_state.auth_manager.get_session_time_remaining()} min
        """)
    
    with col_info2:
        st.info(f"""
        **📅 Información del Sistema:**
        - Versión: {config.VERSION}
        - Dominio: {config.COMPANY_DOMAIN}
        - Fecha actual: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Configuraciones planeadas:**")
        st.write("✅ Configuración de roles y permisos")
        st.write("✅ Parámetros del sistema")
        st.write("✅ Configuración de email")
        st.write("✅ Backup y restauración")
    
    with col2:
        st.write("**Opciones de mantenimiento:**")
        st.write("✅ Limpieza de datos temporales")
        st.write("✅ Regeneración de índices")
        st.write("✅ Logs del sistema")
        st.write("✅ Auditoría de seguridad")