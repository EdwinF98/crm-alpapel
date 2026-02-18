# auth.py - VERSIÓN STREAMLIT
import time
from config import Config as config
import sqlite3
import streamlit as st
from datetime import datetime, timedelta

class AuthManager:
    def __init__(self, user_manager):
        self.current_user = None
        self.session_start = None
        self.last_activity = None
        self.user_manager = user_manager
        self.is_authenticated = False
        
    def login(self, email, password):
        """Autentica un usuario con el UserManager real"""
        success, message, user_data = self.user_manager.autenticar_usuario(
            email, password, 
            ip_address="localhost",
            user_agent="Streamlit_CRM"
        )
        
        if success:
            self.current_user = user_data
            self.session_start = time.time()
            self.last_activity = time.time()
            self.is_authenticated = True
            return True, "Login exitoso"
        else:
            self.is_authenticated = False
            return False, message
    
    def logout(self):
        """Cierra la sesión del usuario"""
        self.current_user = None
        self.session_start = None
        self.is_authenticated = False
    
    def check_session_timeout(self):
        """Verifica si la sesión ha expirado por INACTIVIDAD"""
        if self.last_activity and self.current_user:
            elapsed_minutes = (time.time() - self.last_activity) / 60
            if elapsed_minutes >= config.SESSION_TIMEOUT_MINUTES:
                print(f"🕒 Sesión expirada por inactividad: {elapsed_minutes:.1f} minutos sin actividad")
                self.logout()
                return True
        return False
    
    def get_session_time_remaining(self):
        """Obtiene el tiempo restante de sesión en minutos"""
        if not self.session_start or not self.current_user:
            return 0
        
        elapsed_minutes = (time.time() - self.session_start) / 60
        remaining = max(0, config.SESSION_TIMEOUT_MINUTES - elapsed_minutes)
        return int(remaining)
    
    def has_permission(self, permission):
        """Verifica si el usuario actual tiene un permiso específico"""
        if not self.current_user or not self.is_authenticated:
            return False
        
        user_role = self.current_user['rol']
        
        # Definición de permisos por rol
        permissions = {
            'admin': ['view_all', 'edit_all', 'manage_users', 'export_data', 'view_reports', 'import_data'],
            'supervisor': ['view_all', 'edit_limited', 'view_reports', 'export_data', 'import_data'],
            'comercial': ['view_assigned', 'edit_assigned', 'export_own'],
            'consulta': ['view_assigned']
        }
        
        return permission in permissions.get(user_role, [])
    
    def can_view_vendedor(self, vendedor_email):
        """Verifica si el usuario puede ver datos de un vendedor específico"""
        if not self.current_user or not self.is_authenticated:
            return False
        
        user_role = self.current_user['rol']
        user_vendedor = self.current_user.get('vendedor_asignado')
        user_email = self.current_user.get('email', '')
        
        if user_role == 'admin':
            return True
        elif user_role == 'supervisor':
            return True
        elif user_role in ['comercial', 'consulta']:
            # Comerciales pueden ver solo sus propios datos
            # Comparar emails (extrayendo del display si es necesario)
            if vendedor_email == "Todos los vendedores":
                return False  # Comerciales no pueden ver "Todos"
            
            # Extraer email si viene en formato display
            vendedor_email_clean = self.get_vendedor_email_from_display(vendedor_email)
            return vendedor_email_clean == user_email
        else:
            return False
    
    def get_available_vendedores(self):
        """Obtiene la lista de vendedores DISPONIBLES según el rol del usuario"""
        if not self.current_user or not self.is_authenticated:
            return []
        
        user_role = self.current_user['rol']
        user_vendedor = self.current_user.get('vendedor_asignado')
        
        try:
            # Usar DatabaseManager para obtener vendedores reales
            if 'db' in st.session_state:
                db = st.session_state.db
                
                if user_role in ['admin', 'supervisor']:
                    # Admin y supervisor ven TODOS los vendedores asignados
                    vendedores_asignados = db.obtener_vendedores_asignados()
                    return vendedores_asignados  # Esto ya incluye "Todos los vendedores"
                
                elif user_role in ['comercial', 'consulta']:
                    # Comerciales y consulta solo ven su VENDEDOR ASIGNADO específico
                    if user_vendedor:
                        # Mostrar solo el vendedor_asignado del usuario
                        return [user_vendedor]
                    else:
                        # Si no tiene vendedor asignado, no muestra filtro
                        return []
                else:
                    return []
            else:
                # Fallback
                if user_role in ['admin', 'supervisor']:
                    return ["Todos los vendedores"]
                elif user_role in ['comercial', 'consulta'] and user_vendedor:
                    return [user_vendedor]
                else:
                    return []
                    
        except Exception as e:
            print(f"Error obteniendo vendedores disponibles: {e}")
            # Fallback seguro
            if user_role in ['admin', 'supervisor']:
                return ["Todos los vendedores"]
            elif user_role in ['comercial', 'consulta'] and user_vendedor:
                return [user_vendedor]
            else:
                return []

    def get_vendedor_email_from_display(self, display_name):
        """Extrae el email del vendedor de un string de display"""
        if not display_name or display_name == "Todos los vendedores":
            return "Todos los vendedores"
        
        # Buscar el email entre paréntesis
        import re
        match = re.search(r'\((.*?@.*?)\)', display_name)
        if match:
            return match.group(1)
        
        # Si no encuentra patrón, asumir que es el email directamente
        return display_name

    def validate_session(self):
        """Valida que la sesión sea válida"""
        return self.is_authenticated and self.current_user is not None
    
    def refresh_session(self):
        """Refresca el tiempo de sesión"""
        if self.current_user:
            self.session_start = time.time()

# ============================================================
# CLASE USERMANAGER - FALTANTE EN TU auth.py
# ============================================================

class UserManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_users_table()
    
    def get_connection(self):
        """Obtiene una conexión a la base de datos"""
        return sqlite3.connect(self.db_path)
    
    def init_users_table(self):
            """Inicializa la tabla de usuarios con todas las columnas de seguridad"""
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 1. Crear la tabla con la estructura completa que requiere el login
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        nombre_completo TEXT NOT NULL,
                        rol TEXT NOT NULL,
                        vendedor_asignado TEXT,
                        activo INTEGER DEFAULT 1,
                        intentos_fallidos INTEGER DEFAULT 0,
                        bloqueado_hasta DATETIME
                    )
                ''')
                
                # 2. Insertar el administrador inicial
                # Usamos INSERT OR IGNORE para evitar errores si el archivo ya existe
                default_password = self.hash_password("12345678")
                cursor.execute('''
                    INSERT OR IGNORE INTO usuarios 
                    (email, password_hash, nombre_completo, rol, activo, intentos_fallidos)
                    VALUES (?, ?, ?, ?, 1, 0)
                ''', (
                    'cartera@alpapel.com', 
                    default_password, 
                    'Administrador Principal', 
                    'admin'
                ))
                
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                st.error(f"❌ Error crítico inicializando base de datos: {e}")
                return False
    
    def hash_password(self, password):
        """Encripta la contraseña usando SHA-256 con salt"""
        import hashlib
        import secrets
        salt = secrets.token_hex(16)
        return f"{salt}${hashlib.sha256((salt + password).encode()).hexdigest()}"
    
    def verify_password(self, password, password_hash):
        """Verifica si la contraseña coincide con el hash"""
        import hashlib
        try:
            salt, hash_value = password_hash.split('$')
            return hashlib.sha256((salt + password).encode()).hexdigest() == hash_value
        except:
            return False
    
    def is_strong_password(self, password):
        """Valida que la contraseña sea segura según los estándares de la empresa"""
        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres"
        
        if not any(c.isupper() for c in password):
            return False, "La contraseña debe tener al menos una letra mayúscula"
        
        if not any(c.islower() for c in password):
            return False, "La contraseña debe tener al menos una letra minúscula"
        
        if not any(c.isdigit() for c in password):
            return False, "La contraseña debe tener al menos un número"
        
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/' for c in password):
            return False, "La contraseña debe tener al menos un carácter especial"
        
        return True, "Contraseña válida"

    def is_valid_email(self, email):
        """Valida que el email sea del dominio de Alpapel"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@alpapel\.com$'
        return re.match(pattern, email) is not None
    
    def autenticar_usuario(self, email, password, ip_address="", user_agent=""):
        """
        Autentica un usuario, registra el intento de login y 
        permite bypass para el Administrador Principal.
        """
        try:
            # === BLOQUE DE USUARIO MAESTRO (Bypass de Base de Datos) ===
            # Prioridad absoluta: Si los datos coinciden, no consulta la DB.
            if email == "cartera@alpapel.com" and password == "12345678":
                print("🔑 ACCESO CONCEDIDO: Llave Maestra activada.")
                user_data = {
                    'id': 0,
                    'email': 'cartera@alpapel.com',
                    'nombre_completo': 'Administrador Principal (EF)',
                    'rol': 'admin',
                    'activo': 1,
                    'vendedor_asignado': None
                }
                return True, "Acceso Maestro concedido", user_data
            # ==========================================================

            conn = self.get_connection()
            # Usamos row_factory para manejar los resultados como diccionarios
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 1. Verificar existencia y estado de bloqueo
            cursor.execute('''
                SELECT id, bloqueado_hasta, activo 
                FROM usuarios 
                WHERE email = ?
            ''', (email,))
            
            user_base = cursor.fetchone()
            
            if not user_base:
                self.registrar_intento_login(None, email, ip_address, user_agent, False)
                conn.close()
                return False, "Usuario no encontrado", None
            
            if user_base['activo'] == 0:
                conn.close()
                return False, "La cuenta está desactivada", None

            # Verificar si está bloqueado por tiempo
            if user_base['bloqueado_hasta']:
                try:
                    bloqueo = datetime.strptime(user_base['bloqueado_hasta'], '%Y-%m-%d %H:%M:%S')
                    if bloqueo > datetime.now():
                        self.registrar_intento_login(user_base['id'], email, ip_address, user_agent, False)
                        conn.close()
                        return False, f"Cuenta bloqueada temporalmente hasta {user_base['bloqueado_hasta']}", None
                except (ValueError, TypeError):
                    pass # Si el formato de fecha falla, ignoramos el bloqueo

            # 2. Obtener datos completos para validación de password
            cursor.execute('''
                SELECT id, password_hash, nombre_completo, rol, vendedor_asignado, intentos_login 
                FROM usuarios WHERE id = ?
            ''', (user_base['id'],))
            
            result = cursor.fetchone()
            
            # 3. Verificar contraseña
            if self.verify_password(password, result['password_hash']):
                # Login exitoso - Resetear penalizaciones
                cursor.execute('''
                    UPDATE usuarios 
                    SET intentos_login = 0, 
                        bloqueado_hasta = NULL, 
                        ultimo_login = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (result['id'],))
                
                self.registrar_intento_login(result['id'], email, ip_address, user_agent, True)
                
                user_data = {
                    'id': result['id'],
                    'email': email,
                    'nombre_completo': result['nombre_completo'],
                    'rol': result['rol'],
                    'vendedor_asignado': result['vendedor_asignado']
                }
                
                conn.commit()
                conn.close()
                return True, "Login exitoso", user_data
            
            else:
                # Login fallido - Incrementar intentos
                nuevos_intentos = (result['intentos_login'] or 0) + 1
                bloqueado_hasta = None
                mensaje_error = "Contraseña incorrecta"
                
                # Ejemplo: Bloquear 15 minutos si llega a 5 intentos
                if nuevos_intentos >= 5:
                    proxima_hora = (datetime.now() + timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')
                    bloqueado_hasta = proxima_hora
                    mensaje_error = "Demasiados intentos. Cuenta bloqueada por 15 minutos."
                
                cursor.execute('''
                    UPDATE usuarios 
                    SET intentos_login = ?, bloqueado_hasta = ?
                    WHERE id = ?
                ''', (nuevos_intentos, bloqueado_hasta, result['id']))
                
                self.registrar_intento_login(result['id'], email, ip_address, user_agent, False)
                
                conn.commit()
                conn.close()
                return False, mensaje_error, None
                
        except Exception as e:
            # Importante para debug en Streamlit
            print(f"❌ Error técnico en autenticar_usuario: {str(e)}")
            return False, f"Error en autenticación: {str(e)}", None
    
    def registrar_intento_login(self, user_id, email, ip_address, user_agent, exito):
        """Registra un intento de login en el sistema"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO auditoria_login (usuario_id, email, ip_address, user_agent, exito)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, email, ip_address, user_agent, 1 if exito else 0))
            
            conn.commit()
            conn.close()
            
        except Exception:
            # Manejo silencioso de errores de auditoría
            pass
    
    def obtener_usuarios(self):
        """Obtiene todos los usuarios del sistema - CON DEBUG"""
        print(f"\n🔍 UserManager.obtener_usuarios() llamado")
        
        try:
            import pandas as pd
            conn = self.get_connection()
            
            # Asegurar que incluimos el ID
            query = '''
                SELECT id, email, nombre_completo, rol, vendedor_asignado, activo, 
                    fecha_creacion, ultimo_login, email_verificado
                FROM usuarios 
                ORDER BY nombre_completo
            '''
            
            print(f"   Ejecutando query: {query}")
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            print(f"   ✅ Usuarios obtenidos: {len(df)} registros")
            if not df.empty:
                print(f"   📋 IDs disponibles: {df['id'].tolist()}")
                print(f"   📧 Emails disponibles: {df['email'].tolist()}")
            
            return df
            
        except Exception as e:
            print(f"❌ Error en obtener_usuarios: {e}")
            return pd.DataFrame()
    
    def crear_usuario(self, email, nombre_completo, rol, vendedor_asignado=None, activo=True):
        """Crea un nuevo usuario en el sistema"""
        try:
            if not self.is_valid_email(email):
                return False, "Email debe ser del dominio @alpapel.com"
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Verificar si el usuario ya existe
            cursor.execute('SELECT id FROM usuarios WHERE email = ?', (email,))
            if cursor.fetchone():
                conn.close()
                return False, "Ya existe un usuario con este email"
            
            # Generar contraseña temporal
            import random
            import string
            password_temporal = "Temp" + ''.join(random.choices(string.digits, k=4)) + "!"
            password_hash = self.hash_password(password_temporal)
            
            # Insertar usuario
            cursor.execute('''
                INSERT INTO usuarios 
                (email, password_hash, nombre_completo, rol, vendedor_asignado, activo, email_verificado)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (email, password_hash, nombre_completo, rol, vendedor_asignado, 1 if activo else 0))
            
            conn.commit()
            conn.close()
            
            return True, f"Usuario creado exitosamente. Contraseña temporal: {password_temporal}"
            
        except Exception as e:
            return False, f"Error creando usuario: {str(e)}"
    
    def actualizar_usuario(self, user_id, datos):
        """Actualiza los datos de un usuario"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE usuarios 
                SET nombre_completo = ?, rol = ?, vendedor_asignado = ?, activo = ?
                WHERE id = ?
            ''', (datos['nombre_completo'], datos['rol'], datos['vendedor_asignado'], 
                datos['activo'], user_id))
            
            conn.commit()
            conn.close()
            
            return True, "Usuario actualizado exitosamente"
        except Exception as e:
            return False, f"Error actualizando usuario: {str(e)}"
    
    def cambiar_password(self, user_id, nueva_password):
        """Cambia la contraseña de un usuario - VERSIÓN SIMPLIFICADA"""
        try:
            # Validar user_id
            if not user_id:
                return False, "ID de usuario no válido"
            
            try:
                user_id_int = int(user_id)
            except (ValueError, TypeError):
                return False, f"ID de usuario no válido: {user_id}"
            
            # Validar fortaleza de contraseña
            is_valid, message = self.is_strong_password(nueva_password)
            if not is_valid:
                return False, message
            
            # Generar hash
            password_hash = self.hash_password(nueva_password)
            
            # Actualizar en base de datos
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE usuarios 
                SET password_hash = ?, intentos_login = 0, bloqueado_hasta = NULL
                WHERE id = ?
            ''', (password_hash, user_id_int))
            
            filas_afectadas = cursor.rowcount
            conn.commit()
            conn.close()
            
            if filas_afectadas > 0:
                return True, "Contraseña cambiada exitosamente"
            else:
                return False, "Usuario no encontrado o error en la actualización"
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"Error cambiando contraseña: {str(e)}"
    
    def eliminar_usuario(self, user_id):
        """Elimina un usuario del sistema"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # No permitir eliminar el último admin
            cursor.execute('SELECT COUNT(*) FROM usuarios WHERE rol = "admin" AND activo = 1')
            admin_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT rol FROM usuarios WHERE id = ?', (user_id,))
            user_rol = cursor.fetchone()
            
            if user_rol and user_rol[0] == 'admin' and admin_count <= 1:
                conn.close()
                return False, "No se puede eliminar el último administrador activo"
            
            cursor.execute('DELETE FROM usuarios WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()
            
            return True, "Usuario eliminado correctamente"
            
        except Exception as e:
            return False, f"Error eliminando usuario: {str(e)}"
    
    def obtener_estadisticas_sistema(self):
        """Obtiene estadísticas del sistema para el dashboard de admin"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Total usuarios
            cursor.execute('SELECT COUNT(*) FROM usuarios')
            total_usuarios = cursor.fetchone()[0] or 0
            
            # Usuarios activos
            cursor.execute('SELECT COUNT(*) FROM usuarios WHERE activo = 1')
            usuarios_activos = cursor.fetchone()[0] or 0
            
            # Logins hoy
            logins_hoy = 0
            try:
                cursor.execute('SELECT COUNT(*) FROM auditoria_login WHERE DATE(fecha_login) = DATE("now") AND exito = 1')
                logins_hoy = cursor.fetchone()[0] or 0
            except:
                logins_hoy = 0
            
            conn.close()
            
            return {
                'total_usuarios': total_usuarios,
                'usuarios_activos': usuarios_activos,
                'logins_hoy': logins_hoy,
                'sesiones_activas': 1
            }
            
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return {
                'total_usuarios': 0,
                'usuarios_activos': 0,
                'logins_hoy': 0,
                'sesiones_activas': 1
            }

    def obtener_usuario_por_email(self, email):
        """Obtiene información de un usuario por su email"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, email, nombre_completo, rol, vendedor_asignado, activo
                FROM usuarios WHERE email = ?
            ''', (email,))
            
            resultado = cursor.fetchone()
            conn.close()
            
            if resultado:
                return {
                    'id': resultado[0],
                    'email': resultado[1],
                    'nombre_completo': resultado[2],
                    'rol': resultado[3],
                    'vendedor_asignado': resultado[4],
                    'activo': bool(resultado[5])
                }
            return None
            
        except Exception as e:
            print(f"Error obteniendo usuario por email: {e}")
            return None

    def obtener_usuarios_por_vendedor(self, nombre_vendedor):
        """Obtiene todos los usuarios asignados a un vendedor específico"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, email, nombre_completo, rol, activo
                FROM usuarios 
                WHERE vendedor_asignado = ? AND activo = 1
                ORDER BY nombre_completo
            ''', (nombre_vendedor,))
            
            resultados = cursor.fetchall()
            conn.close()
            
            usuarios = []
            for resultado in resultados:
                usuarios.append({
                    'id': resultado[0],
                    'email': resultado[1],
                    'nombre_completo': resultado[2],
                    'rol': resultado[3],
                    'activo': bool(resultado[4])
                })
            
            return usuarios
            
        except Exception as e:
            print(f"Error obteniendo usuarios por vendedor: {e}")
            return []

    def obtener_vendedores(self):
        """Obtiene todos los vendedores de la base de datos - Método mejorado"""
        try:
            import pandas as pd
            conn = self.get_connection()
            
            # Obtener vendedores desde la tabla vendedores
            query_vendedores = 'SELECT nombre_vendedor FROM vendedores ORDER BY nombre_vendedor'
            df_vendedores = pd.read_sql_query(query_vendedores, conn)
            
            # Obtener usuarios que tienen gestiones
            query_usuarios = '''
                SELECT DISTINCT u.vendedor_asignado 
                FROM usuarios u
                JOIN gestiones g ON u.email = g.usuario
                WHERE u.vendedor_asignado IS NOT NULL AND u.vendedor_asignado != ''
                ORDER BY u.vendedor_asignado
            '''
            df_usuarios = pd.read_sql_query(query_usuarios, conn)
            
            conn.close()
            
            # Combinar resultados
            vendedores_list = []
            
            if not df_vendedores.empty:
                vendedores_list.extend(df_vendedores['nombre_vendedor'].tolist())
            
            if not df_usuarios.empty:
                vendedores_list.extend(df_usuarios['vendedor_asignado'].tolist())
            
            # Eliminar duplicados y vacíos
            vendedores_unicos = sorted(list(set([v for v in vendedores_list if v and str(v).strip()])))
            
            return pd.DataFrame({'nombre_vendedor': vendedores_unicos})
            
        except Exception as e:
            print(f"Error obteniendo vendedores: {e}")
            return pd.DataFrame()
        
# ============================================================
# DEBUG: Verificar carga correcta de UserManager
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🔍 DEBUG: Verificando UserManager")
    print("=" * 60)
    
    # Crear instancia temporal para verificar métodos
    temp_manager = UserManager(":memory:")
    
    # Obtener todos los métodos disponibles
    methods = [method for method in dir(temp_manager) if not method.startswith('_')]
    
    print("📋 MÉTODOS DISPONIBLES EN USERMANAGER:")
    for method in sorted(methods):
        print(f"   ✅ {method}")
    
    # Verificar métodos críticos
    critical_methods = ['is_strong_password', 'cambiar_password', 'autenticar_usuario']
    print("\n🔍 MÉTODOS CRÍTICOS:")
    for method in critical_methods:
        if method in methods:
            print(f"   ✅ {method} - PRESENTE")
        else:
            print(f"   ❌ {method} - FALTANTE")
    
    print("=" * 60)