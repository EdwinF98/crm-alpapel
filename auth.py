# auth.py - VERSIÓN CORREGIDA
import time
import re
import hashlib
import secrets
import random
import string
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
from config import Config as config


class AuthManager:
    """Gestor de sesiones y permisos de usuario"""

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
        """Verifica si la sesión ha expirado por inactividad"""
        if self.last_activity and self.current_user:
            elapsed_minutes = (time.time() - self.last_activity) / 60
            if elapsed_minutes >= config.SESSION_TIMEOUT_MINUTES:
                print(f"🕒 Sesión expirada por inactividad: {elapsed_minutes:.1f} minutos")
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
        permissions = {
            'admin': ['view_all', 'edit_all', 'manage_users', 'export_data', 'view_reports', 'import_data'],
            'supervisor': ['view_all', 'edit_limited', 'view_reports', 'export_data', 'import_data'],
            'comercial': ['view_assigned', 'edit_assigned', 'export_own'],
            'consulta': ['view_assigned']
        }
        return permission in permissions.get(user_role, [])

    def can_view_vendedor(self, vendedor_display):
        """Verifica si el usuario puede ver datos de un vendedor específico"""
        if not self.current_user or not self.is_authenticated:
            return False

        user_role = self.current_user['rol']
        user_vendedor = self.current_user.get('vendedor_asignado')
        user_email = self.current_user.get('email', '')

        if user_role in ['admin', 'supervisor']:
            return True
        elif user_role in ['comercial', 'consulta']:
            if vendedor_display == "Todos los vendedores":
                return False
            vendedor_email_clean = self.get_vendedor_email_from_display(vendedor_display)
            return vendedor_email_clean == user_email
        else:
            return False

    def get_available_vendedores(self):
        """Obtiene la lista de vendedores disponibles según el rol del usuario"""
        if not self.current_user or not self.is_authenticated:
            return []

        user_role = self.current_user['rol']
        user_vendedor = self.current_user.get('vendedor_asignado')

        try:
            if 'db' in st.session_state:
                db = st.session_state.db
                if user_role in ['admin', 'supervisor']:
                    return db.obtener_vendedores_asignados()  # incluye "Todos los vendedores"
                elif user_role in ['comercial', 'consulta']:
                    return [user_vendedor] if user_vendedor else []
                else:
                    return []
            else:
                # Fallback sin DB
                if user_role in ['admin', 'supervisor']:
                    return ["Todos los vendedores"]
                elif user_role in ['comercial', 'consulta'] and user_vendedor:
                    return [user_vendedor]
                else:
                    return []
        except Exception as e:
            print(f"Error obteniendo vendedores disponibles: {e}")
            if user_role in ['admin', 'supervisor']:
                return ["Todos los vendedores"]
            elif user_role in ['comercial', 'consulta'] and user_vendedor:
                return [user_vendedor]
            else:
                return []

    def get_vendedor_email_from_display(self, display_name):
        """Extrae el email del vendedor de un string de display (ej: 'Nombre (email@alpapel.com)')"""
        if not display_name or display_name == "Todos los vendedores":
            return "Todos los vendedores"
        match = re.search(r'\((.*?@.*?)\)', display_name)
        return match.group(1) if match else display_name

    def validate_session(self):
        """Valida que la sesión sea válida"""
        return self.is_authenticated and self.current_user is not None

    def refresh_session(self):
        """Refresca el tiempo de sesión"""
        if self.current_user:
            self.session_start = time.time()


# ============================================================
# CLASE USERMANAGER (unificada y corregida)
# ============================================================

class UserManager:
    """Gestor de usuarios y autenticación"""

    def __init__(self, db_path):
        self.db_path = db_path
        self.init_users_table()

    def get_connection(self):
        """Obtiene una conexión a la base de datos"""
        return sqlite3.connect(self.db_path)

    def init_users_table(self):
        """Crea la tabla de usuarios con todas las columnas necesarias"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Tabla de usuarios (estructura completa)
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
                    bloqueado_hasta DATETIME,
                    ultimo_login DATETIME,
                    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    email_verificado INTEGER DEFAULT 0
                )
            ''')

            # Insertar administrador por defecto si no existe
            default_password = self.hash_password("12345678")
            cursor.execute('''
                INSERT OR IGNORE INTO usuarios 
                (email, password_hash, nombre_completo, rol, activo, intentos_fallidos, email_verificado)
                VALUES (?, ?, ?, ?, 1, 0, 1)
            ''', ('cartera@alpapel.com', default_password, 'Administrador Principal', 'admin'))

            conn.commit()
            conn.close()
            print("✅ Tabla de usuarios verificada/creada correctamente.")
            return True
        except Exception as e:
            st.error(f"❌ Error crítico inicializando tabla de usuarios: {e}")
            return False

    # ========== Métodos de contraseñas ==========

    def hash_password(self, password):
        """Encripta la contraseña usando SHA-256 con salt"""
        salt = secrets.token_hex(16)
        return f"{salt}${hashlib.sha256((salt + password).encode()).hexdigest()}"

    def verify_password(self, password, password_hash):
        """Verifica si la contraseña coincide con el hash"""
        try:
            salt, hash_value = password_hash.split('$')
            return hashlib.sha256((salt + password).encode()).hexdigest() == hash_value
        except Exception:
            return False

    def is_strong_password(self, password):
        """Valida que la contraseña sea segura"""
        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres"
        if not any(c.isupper() for c in password):
            return False, "Debe tener al menos una letra mayúscula"
        if not any(c.islower() for c in password):
            return False, "Debe tener al menos una letra minúscula"
        if not any(c.isdigit() for c in password):
            return False, "Debe tener al menos un número"
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/' for c in password):
            return False, "Debe tener al menos un carácter especial"
        return True, "Contraseña válida"

    def is_valid_email(self, email):
        """Valida que el email sea del dominio @alpapel.com"""
        pattern = r'^[a-zA-Z0-9._%+-]+@alpapel\.com$'
        return re.match(pattern, email) is not None

    # ========== Autenticación ==========

    def autenticar_usuario(self, email, password, ip_address="", user_agent=""):
        """Autentica un usuario, incluyendo llave maestra"""
        try:
            # Llave maestra (acceso de emergencia)
            if email == "cartera@alpapel.com" and password == "12345678":
                return True, "Acceso Maestro concedido", {
                    'id': 0,
                    'email': email,
                    'nombre_completo': 'Administrador Principal',
                    'rol': 'admin',
                    'activo': 1,
                    'vendedor_asignado': None
                }

            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM usuarios WHERE email = ? AND activo = 1", (email,))
            user = cursor.fetchone()

            if not user or not self.verify_password(password, user['password_hash']):
                conn.close()
                return False, "Credenciales incorrectas", None

            # Verificar bloqueo
            if user['bloqueado_hasta']:
                bloqueo = datetime.strptime(user['bloqueado_hasta'], '%Y-%m-%d %H:%M:%S')
                if bloqueo > datetime.now():
                    conn.close()
                    return False, "Cuenta bloqueada temporalmente", None

            # Actualizar último login y resetear intentos
            cursor.execute('''
                UPDATE usuarios 
                SET ultimo_login = CURRENT_TIMESTAMP, intentos_fallidos = 0, bloqueado_hasta = NULL
                WHERE id = ?
            ''', (user['id'],))
            conn.commit()
            conn.close()

            return True, "Login exitoso", dict(user)

        except Exception as e:
            return False, f"Error en autenticación: {str(e)}", None

    def registrar_intento_login(self, user_id, email, ip_address, user_agent, exito):
        """Registra intento de login en la tabla de auditoría (opcional)"""
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
            # La tabla puede no existir, ignoramos silenciosamente
            pass

    # ========== CRUD de usuarios ==========

    def obtener_usuarios(self):
        """Obtiene todos los usuarios del sistema"""
        try:
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
        """Crea un nuevo usuario con contraseña temporal"""
        try:
            if not self.is_valid_email(email):
                return False, "El email debe ser del dominio @alpapel.com"

            conn = self.get_connection()
            cursor = conn.cursor()

            # Verificar duplicado
            cursor.execute('SELECT id FROM usuarios WHERE email = ?', (email,))
            if cursor.fetchone():
                conn.close()
                return False, "Ya existe un usuario con este email"

            # Generar contraseña temporal
            password_temporal = "Temp" + ''.join(random.choices(string.digits, k=4)) + "!"
            password_hash = self.hash_password(password_temporal)

            cursor.execute('''
                INSERT INTO usuarios
                (email, password_hash, nombre_completo, rol, vendedor_asignado, activo, email_verificado)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (email, password_hash, nombre_completo, rol, vendedor_asignado, 1 if activo else 0))

            conn.commit()
            conn.close()

            return True, f"Usuario creado. Contraseña temporal: {password_temporal}"

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
            return True, "Usuario actualizado correctamente"
        except Exception as e:
            return False, f"Error actualizando usuario: {str(e)}"

    def cambiar_password(self, user_id, nueva_password):
        """Cambia la contraseña de un usuario"""
        try:
            # Validar ID
            if not user_id:
                return False, "ID de usuario no válido"
            try:
                user_id_int = int(user_id)
            except (ValueError, TypeError):
                return False, f"ID de usuario no válido: {user_id}"

            # Validar fortaleza
            is_valid, msg = self.is_strong_password(nueva_password)
            if not is_valid:
                return False, msg

            # Generar hash
            password_hash = self.hash_password(nueva_password)

            # Actualizar en BD
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE usuarios
                SET password_hash = ?, intentos_fallidos = 0, bloqueado_hasta = NULL
                WHERE id = ?
            ''', (password_hash, user_id_int))

            if cursor.rowcount == 0:
                conn.close()
                return False, "Usuario no encontrado"

            conn.commit()
            conn.close()
            return True, "Contraseña cambiada exitosamente"

        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"Error cambiando contraseña: {str(e)}"

    def eliminar_usuario(self, user_id):
        """Elimina un usuario (no permite eliminar el último admin)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Verificar si es el último admin
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

    # ========== Estadísticas y utilidades ==========

    def obtener_estadisticas_sistema(self):
        """Devuelve estadísticas básicas del sistema"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM usuarios')
            total = cursor.fetchone()[0] or 0
            cursor.execute('SELECT COUNT(*) FROM usuarios WHERE activo = 1')
            activos = cursor.fetchone()[0] or 0
            conn.close()
            return {
                'total_usuarios': total,
                'usuarios_activos': activos,
                'logins_hoy': 0,      # Podrías implementar consulta a auditoria_login
                'sesiones_activas': 1
            }
        except Exception:
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
            row = cursor.fetchone()
            conn.close()
            if row:
                return {
                    'id': row[0],
                    'email': row[1],
                    'nombre_completo': row[2],
                    'rol': row[3],
                    'vendedor_asignado': row[4],
                    'activo': bool(row[5])
                }
            return None
        except Exception as e:
            print(f"Error obteniendo usuario por email: {e}")
            return None

    def obtener_usuarios_por_vendedor(self, nombre_vendedor):
        """Obtiene usuarios asignados a un vendedor específico"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, email, nombre_completo, rol, activo
                FROM usuarios
                WHERE vendedor_asignado = ? AND activo = 1
                ORDER BY nombre_completo
            ''', (nombre_vendedor,))
            rows = cursor.fetchall()
            conn.close()
            usuarios = []
            for r in rows:
                usuarios.append({
                    'id': r[0],
                    'email': r[1],
                    'nombre_completo': r[2],
                    'rol': r[3],
                    'activo': bool(r[4])
                })
            return usuarios
        except Exception as e:
            print(f"Error obteniendo usuarios por vendedor: {e}")
            return []

    def obtener_vendedores(self):
        """Obtiene todos los vendedores (para compatibilidad)"""
        try:
            conn = self.get_connection()
            # Primero desde tabla vendedores
            df1 = pd.read_sql_query('SELECT nombre_vendedor FROM vendedores ORDER BY nombre_vendedor', conn)
            # Luego desde usuarios con vendedor_asignado
            df2 = pd.read_sql_query('''
                SELECT DISTINCT vendedor_asignado FROM usuarios
                WHERE vendedor_asignado IS NOT NULL AND vendedor_asignado != ''
                ORDER BY vendedor_asignado
            ''', conn)
            conn.close()

            vendedores = []
            if not df1.empty:
                vendedores.extend(df1['nombre_vendedor'].tolist())
            if not df2.empty:
                vendedores.extend(df2['vendedor_asignado'].tolist())

            # Unicos y ordenados
            vendedores = sorted(set(v for v in vendedores if v and str(v).strip()))
            return pd.DataFrame({'nombre_vendedor': vendedores})
        except Exception as e:
            print(f"Error obteniendo vendedores: {e}")
            return pd.DataFrame()


# ============================================================
# DEBUG (opcional, solo si se ejecuta directamente)
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🔍 Verificando UserManager")
    print("=" * 60)
    temp = UserManager(":memory:")
    methods = [m for m in dir(temp) if not m.startswith('_')]
    print("📋 Métodos disponibles:")
    for m in sorted(methods):
        print(f"   ✅ {m}")
    print("=" * 60)