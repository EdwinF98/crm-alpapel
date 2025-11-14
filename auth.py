# auth.py - VERSIÓN STREAMLIT
import time
from config import config
import sqlite3
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
    
    def can_view_vendedor(self, vendedor_nombre):
        """Verifica si el usuario puede ver datos de un vendedor específico"""
        if not self.current_user or not self.is_authenticated:
            return False
        
        user_role = self.current_user['rol']
        user_vendedor = self.current_user.get('vendedor_asignado')
        
        if user_role == 'admin':
            return True
        elif user_role == 'supervisor':
            return True
        elif user_role in ['comercial', 'consulta']:
            return vendedor_nombre == user_vendedor
        else:
            return False
    
    def get_available_vendedores(self):
        """Obtiene la lista de vendedores disponibles según el rol del usuario"""
        if not self.current_user or not self.is_authenticated:
            return []
        
        user_role = self.current_user['rol']
        user_vendedor = self.current_user.get('vendedor_asignado')
        
        if user_role == 'admin':
            try:
                # ✅ CORRECCIÓN: Usar método obtener_vendedores() de DatabaseManager
                vendedores_df = self.user_manager.obtener_vendedores()  # 🆕 SOLO ESTA LÍNEA CAMBIA
                vendedores = ["Todos los vendedores"] + vendedores_df['nombre_vendedor'].tolist()
                return vendedores
            except Exception as e:
                print(f"Error obteniendo vendedores: {e}")
                return ["Todos los vendedores", user_vendedor] if user_vendedor else ["Todos los vendedores"]
        elif user_role == 'supervisor':
            try:
                # ✅ CORRECCIÓN: Usar método obtener_vendedores() de DatabaseManager
                vendedores_df = self.user_manager.obtener_vendedores()  # 🆕 SOLO ESTA LÍNEA CAMBIA
                vendedores = ["Todos los vendedores"] + vendedores_df['nombre_vendedor'].tolist()
                return vendedores
            except:
                return ["Todos los vendedores", user_vendedor] if user_vendedor else ["Todos los vendedores"]
        elif user_role in ['comercial', 'consulta']:
            return [user_vendedor] if user_vendedor else []
        else:
            return []
    
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
        """Inicializa las tablas de usuarios en la base de datos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabla de usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                nombre_completo TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT 'comercial',
                vendedor_asignado TEXT,
                activo INTEGER DEFAULT 1,
                email_verificado INTEGER DEFAULT 0,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                ultimo_login DATETIME,
                intentos_login INTEGER DEFAULT 0,
                bloqueado_hasta DATETIME,
                reset_token TEXT,
                reset_token_expira DATETIME
            )
        ''')
        
        # Tabla de auditoría de login
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auditoria_login (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                email TEXT,
                fecha_login DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                exito INTEGER DEFAULT 0,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')
        
        # Crear usuario admin por defecto si no existe
        cursor.execute('SELECT COUNT(*) FROM usuarios WHERE email = "cartera@alpapel.com"')
        if cursor.fetchone()[0] == 0:
            default_password = self.hash_password("12345678")
            cursor.execute('''
                INSERT INTO usuarios (email, password_hash, nombre_completo, rol, email_verificado, activo)
                VALUES (?, ?, ?, ?, 1, 1)
            ''', ('cartera@alpapel.com', default_password, 'Administrador Principal', 'admin'))
            print("✅ Usuario admin creado: cartera@alpapel.com / 12345678")
        
        conn.commit()
        conn.close()
    
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
    
    def is_valid_email(self, email):
        """Valida que el email sea del dominio de Alpapel"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@alpapel\.com$'
        return re.match(pattern, email) is not None
    
    def autenticar_usuario(self, email, password, ip_address="", user_agent=""):
        """Autentica un usuario y registra el intento de login"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Verificar si el usuario está bloqueado
            cursor.execute('''
                SELECT id, bloqueado_hasta FROM usuarios 
                WHERE email = ? AND activo = 1
            ''', (email,))
            
            result = cursor.fetchone()
            if not result:
                self.registrar_intento_login(None, email, ip_address, user_agent, False)
                conn.close()
                return False, "Usuario no encontrado o inactivo", None
            
            user_id, bloqueado_hasta = result
            
            if bloqueado_hasta and datetime.strptime(bloqueado_hasta, '%Y-%m-%d %H:%M:%S') > datetime.now():
                self.registrar_intento_login(user_id, email, ip_address, user_agent, False)
                conn.close()
                return False, "Cuenta temporalmente bloqueada por múltiples intentos fallidos", None
            
            # Obtener datos del usuario
            cursor.execute('''
                SELECT id, password_hash, nombre_completo, rol, vendedor_asignado, intentos_login 
                FROM usuarios WHERE email = ?
            ''', (email,))
            
            result = cursor.fetchone()
            if not result:
                self.registrar_intento_login(user_id, email, ip_address, user_agent, False)
                conn.close()
                return False, "Error en la autenticación", None
            
            user_id, password_hash, nombre_completo, rol, vendedor_asignado, intentos_login = result
            
            # Verificar contraseña
            if self.verify_password(password, password_hash):
                # Login exitoso - resetear intentos
                cursor.execute('''
                    UPDATE usuarios 
                    SET intentos_login = 0, bloqueado_hasta = NULL, 
                        ultimo_login = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (user_id,))
                
                # Registrar login exitoso
                self.registrar_intento_login(user_id, email, ip_address, user_agent, True)
                
                user_data = {
                    'id': user_id,
                    'email': email,
                    'nombre_completo': nombre_completo,
                    'rol': rol,
                    'vendedor_asignado': vendedor_asignado
                }
                
                conn.commit()
                conn.close()
                return True, "Login exitoso", user_data
            else:
                # Login fallido - incrementar intentos
                nuevos_intentos = intentos_login + 1
                bloqueado_hasta = None
                
                cursor.execute('''
                    UPDATE usuarios 
                    SET intentos_login = ?, bloqueado_hasta = ?
                    WHERE id = ?
                ''', (nuevos_intentos, bloqueado_hasta, user_id))
                
                self.registrar_intento_login(user_id, email, ip_address, user_agent, False)
                
                conn.commit()
                conn.close()
                return False, "Contraseña incorrecta", None
                
        except Exception as e:
            return False, f"Error en autenticación: {str(e)}", None
    
    def registrar_intento_login(self, user_id, email, ip_address, user_agent, exito):
        """Registra un intento de login"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO auditoria_login (usuario_id, email, ip_address, user_agent, exito)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, email, ip_address, user_agent, 1 if exito else 0))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error registrando intento login: {e}")
    
    def obtener_usuarios(self):
        """Obtiene todos los usuarios del sistema"""
        try:
            import pandas as pd
            conn = self.get_connection()
            query = '''
                SELECT id, email, nombre_completo, rol, vendedor_asignado, activo, 
                       fecha_creacion, ultimo_login, email_verificado
                FROM usuarios 
                ORDER BY nombre_completo
            '''
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"Error obteniendo usuarios: {e}")
            return pd.DataFrame()
    
    def crear_usuario(self, email, nombre_completo, rol, vendedor_asignado=None, activo=True):
        """Crea un nuevo usuario en el sistema"""
        try:
            if not self.is_valid_email(email):
                return False, "Email debe ser del dominio @alpapel.com"
            
            # Verificar si el usuario ya existe
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM usuarios WHERE email = ?', (email,))
            if cursor.fetchone():
                conn.close()
                return False, "Ya existe un usuario con este email"
            
            # Generar contraseña temporal
            import random
            import string
            password_temporal = "Temp" + ''.join(random.choices(string.digits, k=4)) + "!"
            
            password_hash = self.hash_password(password_temporal)
            
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
        """Cambia la contraseña de un usuario"""
        try:
            password_hash = self.hash_password(nueva_password)
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE usuarios 
                SET password_hash = ?, intentos_login = 0, bloqueado_hasta = NULL
                WHERE id = ?
            ''', (password_hash, user_id))
            
            conn.commit()
            conn.close()
            return True, "Contraseña cambiada exitosamente"
        except Exception as e:
            return False, f"Error cambiando contraseña: {str(e)}"
    
    def eliminar_usuario(self, user_id):
        """Elimina un usuario del sistema"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
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
    
    def obtener_vendedores(self):
        """Obtiene todos los vendedores de la base de datos"""
        try:
            import pandas as pd
            conn = self.get_connection()
            query = 'SELECT nombre_vendedor FROM vendedores ORDER BY nombre_vendedor'
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"Error obteniendo vendedores: {e}")
            return pd.DataFrame()