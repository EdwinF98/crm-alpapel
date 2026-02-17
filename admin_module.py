# admin_module.py
import streamlit as st
import pandas as pd
from datetime import datetime
from config import config

def admin_section():
    """Sección de administración de usuarios del sistema"""
    st.header("🛡️ Administración de Usuarios")
    
    # Inicializar estado para mensajes persistentes
    if 'admin_message' not in st.session_state:
        st.session_state.admin_message = ""
    if 'admin_message_type' not in st.session_state:
        st.session_state.admin_message_type = ""  # 'success' o 'error'
    if 'show_message' not in st.session_state:
        st.session_state.show_message = False
    
    # Mostrar mensaje persistente si existe
    if st.session_state.show_message and st.session_state.admin_message:
        if st.session_state.admin_message_type == 'success':
            success_container = st.container()
            with success_container:
                st.success(st.session_state.admin_message)
        else:
            error_container = st.container()
            with error_container:
                st.error(st.session_state.admin_message)
        
        # Botón para cerrar el mensaje
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🆗 Cerrar Mensaje", use_container_width=True, key="close_message_btn"):
                st.session_state.show_message = False
                st.session_state.admin_message = ""
                st.rerun()
        
        st.markdown("---")
    
    # Verificar permisos de administrador
    if not st.session_state.auth_manager.has_permission('manage_users'):
        st.error("⛔ No tienes permisos para acceder a esta sección")
        return
    
    # Estadísticas rápidas
    st.subheader("📊 Estadísticas del Sistema")
    
    try:
        stats = st.session_state.db.obtener_estadisticas_sistema()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Usuarios", stats['total_usuarios'])
        
        with col2:
            st.metric("Usuarios Activos", stats['usuarios_activos'])
        
        with col3:
            st.metric("Logins Hoy", stats['logins_hoy'])
        
        with col4:
            st.metric("Sesiones Activas", stats['sesiones_activas'])
            
    except Exception as e:
        st.error(f"Error cargando estadísticas: {e}")
    
    st.markdown("---")
    
    # Gestión de usuarios en pestañas
    tab1, tab2, tab3 = st.tabs(["👥 Lista de Usuarios", "➕ Crear Usuario", "🔐 Cambiar Contraseñas"])
    
    with tab1:
        st.subheader("👥 Usuarios del Sistema")
        
        try:
            usuarios_df = st.session_state.db.obtener_usuarios()
            
            if not usuarios_df.empty:
                # Mostrar tabla de usuarios
                st.dataframe(
                    usuarios_df[['email', 'nombre_completo', 'rol', 'vendedor_asignado', 'activo']],
                    use_container_width=True,
                    hide_index=True
                )
                
                # Opciones de gestión por usuario
                st.subheader("✏️ Gestión por Usuario")
                
                usuarios_lista = [f"{row['email']} ({row['nombre_completo']})" for _, row in usuarios_df.iterrows()]
                usuario_seleccionado = st.selectbox("Seleccionar usuario para gestionar:", usuarios_lista, key="user_selector")
                
                if usuario_seleccionado:
                    # Obtener datos del usuario seleccionado
                    usuario_email = usuario_seleccionado.split(" (")[0]
                    usuario_data = usuarios_df[usuarios_df['email'] == usuario_email].iloc[0]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Información Actual:**")
                        st.text_input("Email", usuario_data['email'], disabled=True)
                        st.text_input("Nombre Completo", usuario_data['nombre_completo'], disabled=True)
                        st.text_input("Rol", usuario_data['rol'], disabled=True)
                        st.text_input("Vendedor Asignado", usuario_data['vendedor_asignado'] or "No asignado", disabled=True)
                        st.text_input("Estado", "Activo" if usuario_data['activo'] else "Inactivo", disabled=True)
                    
                    with col2:
                        st.write("**Acciones:**")
                        
                        # Actualizar usuario
                        with st.form(f"update_form_{usuario_data['id']}"):
                            st.write("**Actualizar Datos:**")
                            
                            nuevo_nombre = st.text_input("Nombre Completo", value=usuario_data['nombre_completo'], key=f"nombre_{usuario_data['id']}")
                            nuevo_rol = st.selectbox("Rol", options=['admin', 'supervisor', 'comercial', 'consulta'], 
                                                   index=['admin', 'supervisor', 'comercial', 'consulta'].index(usuario_data['rol']), 
                                                   key=f"rol_{usuario_data['id']}")
                            
                            vendedores_df = st.session_state.db.obtener_vendedores()
                            vendedores_opciones = [""] + vendedores_df['nombre_vendedor'].tolist()
                            nuevo_vendedor = st.selectbox("Vendedor Asignado", options=vendedores_opciones,
                                                        index=vendedores_opciones.index(usuario_data['vendedor_asignado'] if usuario_data['vendedor_asignado'] else ""),
                                                        key=f"vendedor_{usuario_data['id']}")
                            
                            nuevo_estado = st.checkbox("Usuario Activo", value=bool(usuario_data['activo']), key=f"activo_{usuario_data['id']}")
                            
                            if st.form_submit_button("💾 Actualizar Usuario", use_container_width=True):
                                # Validar datos antes de guardar
                                if not nuevo_nombre or not nuevo_nombre.strip():
                                    st.session_state.admin_message = "❌ El nombre completo es obligatorio"
                                    st.session_state.admin_message_type = "error"
                                    st.session_state.show_message = True
                                else:
                                    datos_actualizados = {
                                        'nombre_completo': nuevo_nombre.strip(),
                                        'rol': nuevo_rol,
                                        'vendedor_asignado': nuevo_vendedor if nuevo_vendedor and nuevo_vendedor.strip() else None,
                                        'activo': 1 if nuevo_estado else 0  # Asegurar formato correcto (1/0)
                                    }
                                    
                                    # DEBUG: Mostrar datos que se van a guardar
                                    print(f"🔍 DEBUG - Actualizando usuario {usuario_data['id']}: {datos_actualizados}")
                                    
                                    # Intentar actualizar directamente con user_manager primero
                                    try:
                                        success = False
                                        message = ""
                                        
                                        # Método 1: Usar user_manager directamente (más confiable)
                                        if hasattr(st.session_state, 'user_manager'):
                                            success, message = st.session_state.user_manager.actualizar_usuario(
                                                usuario_data['id'], 
                                                datos_actualizados
                                            )
                                            print(f"🔍 DEBUG - user_manager.actualizar_usuario: {success}, {message}")
                                        
                                        # Método 2: Si falla el primero, usar db.actualizar_usuario
                                        if not success and hasattr(st.session_state, 'db'):
                                            success, message = st.session_state.db.actualizar_usuario(
                                                usuario_data['id'], 
                                                datos_actualizados
                                            )
                                            print(f"🔍 DEBUG - db.actualizar_usuario: {success}, {message}")
                                        
                                        if success:
                                            st.session_state.admin_message = f"✅ Usuario {usuario_data['email']} actualizado correctamente"
                                            st.session_state.admin_message_type = "success"
                                            st.session_state.show_message = True
                                            
                                            # Forzar recarga de datos
                                            import time
                                            time.sleep(0.5)
                                        else:
                                            st.session_state.admin_message = f"❌ Error al actualizar: {message}"
                                            st.session_state.admin_message_type = "error"
                                            st.session_state.show_message = True
                                            
                                    except Exception as e:
                                        error_msg = f"❌ Error técnico: {str(e)}"
                                        print(f"🔍 DEBUG - Excepción al actualizar: {e}")
                                        st.session_state.admin_message = error_msg
                                        st.session_state.admin_message_type = "error"
                                        st.session_state.show_message = True
                                    
                                    st.rerun()
                        
                        # Eliminar usuario - CON CONFIRMACIÓN
                        st.write("**Eliminar Usuario:**")

                        # Crear un contenedor único para el botón y la confirmación
                        delete_container = st.container()

                        with delete_container:
                            # Primer botón: Iniciar eliminación
                            if st.button("🗑️ Eliminar Usuario", use_container_width=True, key=f"delete_init_{usuario_data['id']}"):
                                # Guardar usuario a eliminar en session_state
                                st.session_state.usuario_a_eliminar = {
                                    'id': usuario_data['id'],
                                    'email': usuario_data['email'],
                                    'nombre': usuario_data['nombre_completo']
                                }
                                st.rerun()

                        # Mostrar confirmación si hay usuario pendiente de eliminar
                        if (st.session_state.get('usuario_a_eliminar') and 
                            st.session_state.usuario_a_eliminar.get('id') == usuario_data['id']):
                            
                            st.markdown("---")
                            st.warning(f"⚠️ **CONFIRMAR ELIMINACIÓN**")
                            
                            usuario_info = st.session_state.usuario_a_eliminar
                            
                            col_confirm1, col_confirm2 = st.columns(2)
                            
                            with col_confirm1:
                                # Botón CONFIRMAR eliminación
                                if st.button(f"✅ Sí, eliminar a {usuario_info['nombre']}", 
                                            use_container_width=True, 
                                            type="primary",
                                            key=f"confirm_delete_{usuario_data['id']}"):
                                    
                                    # Verificar que no se está eliminando a sí mismo
                                    if usuario_info['email'] == st.session_state.user['email']:
                                        st.session_state.admin_message = "❌ No puedes eliminar tu propio usuario"
                                        st.session_state.admin_message_type = "error"
                                        st.session_state.show_message = True
                                    else:
                                        # Llamar a la función de eliminación
                                        success, message = st.session_state.db.eliminar_usuario(usuario_info['id'])
                                        
                                        if success:
                                            st.session_state.admin_message = f"✅ Usuario {usuario_info['email']} eliminado exitosamente"
                                            st.session_state.admin_message_type = "success"
                                            st.session_state.show_message = True
                                            # Limpiar el usuario pendiente
                                            st.session_state.usuario_a_eliminar = None
                                        else:
                                            st.session_state.admin_message = f"❌ Error al eliminar: {message}"
                                            st.session_state.admin_message_type = "error"
                                            st.session_state.show_message = True
                                    
                                    st.rerun()
                            
                            with col_confirm2:
                                # Botón CANCELAR eliminación
                                if st.button("❌ Cancelar eliminación", 
                                            use_container_width=True,
                                            key=f"cancel_delete_{usuario_data['id']}"):
                                    st.session_state.usuario_a_eliminar = None
                                    st.rerun()
                            
                            # Información adicional
                            st.error(f"""
                            **⚠️ ATENCIÓN - ESTA ACCIÓN NO SE PUEDE DESHACER**
                            
                            Se eliminará permanentemente:
                            - **Usuario:** {usuario_info['nombre']}
                            - **Email:** {usuario_info['email']}
                            - **Todos los datos asociados al usuario**
                            """)
            
            else:
                st.info("📝 No hay usuarios registrados en el sistema")
                
        except Exception as e:
            st.error(f"Error cargando usuarios: {e}")
    
    with tab2:
        st.subheader("➕ Crear Nuevo Usuario")
        
        with st.form("create_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                nuevo_email = st.text_input("📧 Email", placeholder="usuario@alpapel.com")
                nuevo_nombre = st.text_input("👤 Nombre Completo", placeholder="Nombre del usuario")
            
            with col2:
                nuevo_rol = st.selectbox("🎭 Rol", options=['admin', 'supervisor', 'comercial', 'consulta'])
                
                vendedores_df = st.session_state.db.obtener_vendedores()
                vendedores_opciones = [""] + vendedores_df['nombre_vendedor'].tolist()
                vendedor_asignado = st.selectbox("👤 Vendedor Asignado", options=vendedores_opciones)
            
            usuario_activo = st.checkbox("✅ Usuario Activo", value=True)
            
            if st.form_submit_button("👥 Crear Usuario", use_container_width=True, type="primary"):
                if not nuevo_email or not nuevo_nombre:
                    st.session_state.admin_message = "❌ Email y nombre son obligatorios"
                    st.session_state.admin_message_type = "error"
                    st.session_state.show_message = True
                else:
                    success, message = st.session_state.db.crear_usuario(
                        nuevo_email, nuevo_nombre, nuevo_rol, vendedor_asignado, usuario_activo
                    )
                    
                    if success:
                        st.session_state.admin_message = f"✅ {message}"
                        st.session_state.admin_message_type = "success"
                        st.session_state.show_message = True
                    else:
                        st.session_state.admin_message = f"❌ {message}"
                        st.session_state.admin_message_type = "error"
                        st.session_state.show_message = True
                st.rerun()
    
    with tab3:
        st.subheader("🔐 Cambiar Contraseñas")
        
        st.info("💡 Selecciona un usuario y establece una nueva contraseña segura")
        
        # Inicializar estado específico para esta pestaña
        if 'cambiar_pass_data' not in st.session_state:
            st.session_state.cambiar_pass_data = {
                'usuario_seleccionado': None,
                'nueva_password': '',
                'confirmar_password': '',
                'mostrar_mensaje': False,
                'mensaje': '',
                'tipo_mensaje': ''
            }
        
        try:
            print(f"\n" + "="*60)
            print(f"🔐 TAB3 - CAMBIAR CONTRASEÑAS INICIADO")
            
            # OBTENER USUARIOS DIRECTAMENTE DEL USER_MANAGER
            usuarios_df = st.session_state.user_manager.obtener_usuarios()
            
            print(f"   Usuarios DataFrame shape: {usuarios_df.shape}")
            print(f"   Columnas disponibles: {list(usuarios_df.columns)}")
            
            if not usuarios_df.empty:
                # Crear lista para el dropdown
                usuarios_lista = [f"{row['email']} ({row['nombre_completo']})" for _, row in usuarios_df.iterrows()]
                print(f"   Lista dropdown creada: {usuarios_lista}")
                
                # SELECTOR DE USUARIO (fuera del form)
                usuario_seleccionado = st.selectbox(
                    "Seleccionar usuario:", 
                    usuarios_lista, 
                    key="cambiar_pass_user_selector",
                    index=0,
                    on_change=lambda: st.session_state.cambiar_pass_data.update({
                        'usuario_seleccionado': st.session_state.cambiar_pass_user_selector
                    })
                )
                
                # Actualizar estado
                st.session_state.cambiar_pass_data['usuario_seleccionado'] = usuario_seleccionado
                
                print(f"   Usuario seleccionado: {usuario_seleccionado}")
                
                # FORMULARIO SEPARADO para contraseñas
                with st.form("cambiar_password_form", clear_on_submit=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        nueva_password = st.text_input(
                            "Nueva contraseña:", 
                            type="password", 
                            key="nueva_pass_input",
                            placeholder="Ingresa la nueva contraseña",
                            value=st.session_state.cambiar_pass_data.get('nueva_password', '')
                        )
                    
                    with col2:
                        confirmar_password = st.text_input(
                            "Confirmar contraseña:", 
                            type="password", 
                            key="confirmar_pass_input",
                            placeholder="Confirma la nueva contraseña",
                            value=st.session_state.cambiar_pass_data.get('confirmar_password', '')
                        )
                    
                    # Mostrar requisitos de contraseña
                    with st.expander("📋 Requisitos de contraseña segura", expanded=True):
                        st.write("""
                        - **Mínimo 8 caracteres**
                        - **Al menos 1 letra mayúscula** (A-Z)
                        - **Al menos 1 letra minúscula** (a-z)  
                        - **Al menos 1 número** (0-9)
                        - **Al menos 1 carácter especial** (!@#$%^&*()_+-=[]{}|;:,.<>?/)
                        """)
                    
                    # Botones en la misma fila
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        cambiar_btn = st.form_submit_button(
                            "🔄 Cambiar Contraseña", 
                            use_container_width=True, 
                            type="primary"
                        )
                    
                    with col_btn2:
                        limpiar_btn = st.form_submit_button(
                            "🧹 Limpiar Campos", 
                            use_container_width=True,
                            type="secondary"
                        )
                    
                    # Manejar limpieza
                    if limpiar_btn:
                        st.session_state.cambiar_pass_data.update({
                            'nueva_password': '',
                            'confirmar_password': '',
                            'mostrar_mensaje': False
                        })
                        st.rerun()
                    
                    # Manejar cambio de contraseña
                    if cambiar_btn and usuario_seleccionado:
                        print(f"\n" + "="*60)
                        print(f"🔐 BOTÓN 'CAMBIAR CONTRASEÑA' PRESIONADO")
                        
                        # Guardar valores en estado
                        st.session_state.cambiar_pass_data.update({
                            'nueva_password': nueva_password,
                            'confirmar_password': confirmar_password
                        })
                        
                        if not nueva_password or not confirmar_password:
                            print(f"   ❌ Campos vacíos")
                            st.session_state.cambiar_pass_data.update({
                                'mostrar_mensaje': True,
                                'mensaje': "❌ Por favor completa ambos campos de contraseña",
                                'tipo_mensaje': 'error'
                            })
                            
                        elif nueva_password != confirmar_password:
                            print(f"   ❌ Contraseñas no coinciden")
                            st.session_state.cambiar_pass_data.update({
                                'mostrar_mensaje': True,
                                'mensaje': "❌ Las contraseñas no coinciden",
                                'tipo_mensaje': 'error'
                            })
                            
                        else:
                            print(f"   ✅ Campos validados")
                            
                            # 1. Obtener ID del usuario seleccionado
                            usuario_email = usuario_seleccionado.split(" (")[0]
                            print(f"   Email del usuario seleccionado: {usuario_email}")
                            
                            # 2. Buscar el usuario en el DataFrame
                            usuario_filtrado = usuarios_df[usuarios_df['email'] == usuario_email]
                            print(f"   Búsqueda de usuario en DataFrame: {len(usuario_filtrado)} resultados")
                            
                            if usuario_filtrado.empty:
                                print(f"   ❌ CRÍTICO: Usuario {usuario_email} NO encontrado")
                                print(f"   DataFrame actual:")
                                print(f"      Emails: {usuarios_df['email'].tolist()}")
                                print(f"      IDs: {usuarios_df['id'].tolist()}")
                                
                                st.session_state.cambiar_pass_data.update({
                                    'mostrar_mensaje': True,
                                    'mensaje': f"❌ Error: Usuario {usuario_email} no encontrado",
                                    'tipo_mensaje': 'error'
                                })
                            else:
                                usuario_id = usuario_filtrado.iloc[0]['id']
                                usuario_nombre = usuario_filtrado.iloc[0]['nombre_completo']
                                
                                print(f"   ✅ Usuario encontrado en DataFrame:")
                                print(f"      ID: {usuario_id}")
                                print(f"      Nombre: {usuario_nombre}")
                                print(f"      Email: {usuario_email}")
                                
                                # 3. Validar fortaleza de contraseña
                                try:
                                    print(f"   🔍 Validando fortaleza de contraseña...")
                                    is_valid, message = st.session_state.user_manager.is_strong_password(nueva_password)
                                    
                                    if not is_valid:
                                        print(f"   ❌ Validación fallida: {message}")
                                        st.session_state.cambiar_pass_data.update({
                                            'mostrar_mensaje': True,
                                            'mensaje': f"❌ {message}",
                                            'tipo_mensaje': 'error'
                                        })
                                    else:
                                        print(f"   ✅ Contraseña válida según reglas")
                                        
                                        # 4. Cambiar contraseña - LLAMADA DIRECTA
                                        print(f"   🚀 Llamando a user_manager.cambiar_password()...")
                                        print(f"      Parámetros: user_id={usuario_id}, password=[PROTEGIDO]")
                                        
                                        success, message = st.session_state.user_manager.cambiar_password(
                                            int(usuario_id),  # Asegurar que es int
                                            nueva_password
                                        )
                                        
                                        print(f"   Resultado de cambiar_password:")
                                        print(f"      Success: {success}")
                                        print(f"      Message: {message}")
                                        
                                        if success:
                                            st.session_state.cambiar_pass_data.update({
                                                'mostrar_mensaje': True,
                                                'mensaje': f"✅ {message}",
                                                'tipo_mensaje': 'success',
                                                'nueva_password': '',  # Limpiar después de éxito
                                                'confirmar_password': ''  # Limpiar después de éxito
                                            })
                                            print(f"   ✅ Contraseña cambiada exitosamente")
                                        else:
                                            st.session_state.cambiar_pass_data.update({
                                                'mostrar_mensaje': True,
                                                'mensaje': f"❌ {message}",
                                                'tipo_mensaje': 'error'
                                            })
                                            print(f"   ❌ Error al cambiar contraseña")
                                            
                                except Exception as e:
                                    print(f"   ❌ Excepción en validación: {e}")
                                    import traceback
                                    traceback.print_exc()
                                    st.session_state.cambiar_pass_data.update({
                                        'mostrar_mensaje': True,
                                        'mensaje': f"❌ Error técnico: {str(e)}",
                                        'tipo_mensaje': 'error'
                                    })
                            
                            print(f"🔐 FIN PROCESAMIENTO BOTÓN")
                            print("="*60 + "\n")
                        
                        # Forzar rerun para actualizar UI
                        st.rerun()
                
                # MOSTRAR MENSAJES SI EXISTEN
                if st.session_state.cambiar_pass_data.get('mostrar_mensaje', False):
                    mensaje = st.session_state.cambiar_pass_data['mensaje']
                    tipo_mensaje = st.session_state.cambiar_pass_data['tipo_mensaje']
                    
                    if tipo_mensaje == 'success':
                        st.success(mensaje)
                    else:
                        st.error(mensaje)
                    
                    # Botón para cerrar mensaje
                    if st.button("🆗 Cerrar Mensaje", key="cerrar_mensaje_cambiar_pass"):
                        st.session_state.cambiar_pass_data['mostrar_mensaje'] = False
                        st.rerun()
                
                # Mostrar información de debug (opcional)
                with st.expander("🔍 DEBUG: Información de usuarios", expanded=False):
                    st.write("**DataFrame de usuarios:**")
                    st.dataframe(usuarios_df[['id', 'email', 'nombre_completo']])
                    
                    st.write("**IDs disponibles:**")
                    for _, row in usuarios_df.iterrows():
                        st.code(f"ID {row['id']}: {row['email']} - {row['nombre_completo']}")
                        
            else:
                st.info("📝 No hay usuarios registrados en el sistema")
                
            print(f"🔐 TAB3 - CAMBIAR CONTRASEÑAS FINALIZADO")
            print("="*60 + "\n")
                
        except Exception as e:
            st.error(f"Error en cambio de contraseña: {str(e)}")
            import traceback
            traceback.print_exc()

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