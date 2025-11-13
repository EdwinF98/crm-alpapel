import sqlite3
import hashlib
import secrets
import re
from datetime import datetime, timedelta
import pandas as pd
from config import config

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
        salt = secrets.token_hex(16)
        return f"{salt}${hashlib.sha256((salt + password).encode()).hexdigest()}"
    
    def verify_password(self, password, password_hash):
        """Verifica si la contraseña coincide con el hash"""
        try:
            salt, hash_value = password_hash.split('$')
            return hashlib.sha256((salt + password).encode()).hexdigest() == hash_value
        except:
            return False
    
    def is_valid_email(self, email):
        """Valida que el email sea del dominio de Alpapel"""
        pattern = r'^[a-zA-Z0-9._%+-]+@alpapel\.com$'
        return re.match(pattern, email) is not None
    
    def is_strong_password(self, password):
        """Valida que la contraseña sea segura"""
        if len(password) < config.PASSWORD_MIN_LENGTH:
            return False, f"La contraseña debe tener al menos {config.PASSWORD_MIN_LENGTH} caracteres"
        
        if not any(c.isupper() for c in password):
            return False, "La contraseña debe tener al menos una mayúscula"
        
        if not any(c.islower() for c in password):
            return False, "La contraseña debe tener al menos una minúscula"
        
        if not any(c.isdigit() for c in password):
            return False, "La contraseña debe tener al menos un número"
        
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/' for c in password):
            return False, "La contraseña debe tener al menos un carácter especial"
        
        return True, "Contraseña válida"
    
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
                
                if nuevos_intentos >= config.MAX_LOGIN_ATTEMPTS:
                    bloqueado_hasta = (datetime.now() + timedelta(minutes=config.LOCKOUT_TIME_MINUTES)).strftime('%Y-%m-%d %H:%M:%S')
                
                cursor.execute('''
                    UPDATE usuarios 
                    SET intentos_login = ?, bloqueado_hasta = ?
                    WHERE id = ?
                ''', (nuevos_intentos, bloqueado_hasta, user_id))
                
                self.registrar_intento_login(user_id, email, ip_address, user_agent, False)
                
                conn.commit()
                conn.close()
                
                intentos_restantes = config.MAX_LOGIN_ATTEMPTS - nuevos_intentos
                if intentos_restantes > 0:
                    return False, f"Contraseña incorrecta. Intentos restantes: {intentos_restantes}", None
                else:
                    return False, f"Cuenta bloqueada por {config.LOCKOUT_TIME_MINUTES} minutos debido a múltiples intentos fallidos", None
                
        except Exception as e:
            return False, f"Error en autenticación: {str(e)}", None
    
    def registrar_intento_login(self, user_id, email, ip_address, user_agent, exito):
        """Registra un intento de login - VERSIÓN SILENCIOSA"""
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
            # ✅ SILENCIOSO - no imprimir nada en consola
            pass  # Ignorar completamente el error
    
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
            is_valid, message = self.is_strong_password(nueva_password)
            if not is_valid:
                return False, message
            
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
    
    def obtener_vendedores(self):
        """Obtiene todos los vendedores de la base de datos"""
        try:
            conn = self.get_connection()
            query = 'SELECT nombre_vendedor FROM vendedores ORDER BY nombre_vendedor'
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"Error obteniendo vendedores: {e}")
            return pd.DataFrame()

    # === MÉTODOS QUE DEBEN ESTAR DENTRO DE LA CLASE ===

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
            
            # Generar contraseña temporal que cumpla con los requisitos
            import random
            import string
            
            # Contraseña que cumple: Mayúscula + minúscula + números + especial
            letras_mayus = random.choice(string.ascii_uppercase)
            letras_minus = random.choice(string.ascii_lowercase)
            numeros = ''.join(random.choices(string.digits, k=4))
            caracter_especial = random.choice('!@#$%^&*')
            
            # Ensamblar contraseña
            partes = [letras_mayus, letras_minus, numeros, caracter_especial]
            random.shuffle(partes)
            password_temporal = ''.join(partes)
            
            print(f"🔐 CONTRASEÑA GENERADA PARA {email}: {password_temporal}")  # DEBUG
            
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
            
            # Logins hoy (con manejo de tabla inexistente)
            logins_hoy = 0
            try:
                cursor.execute('SELECT COUNT(*) FROM auditoria_login WHERE DATE(fecha_login) = DATE("now") AND exito = 1')
                logins_hoy = cursor.fetchone()[0] or 0
            except:
                logins_hoy = 0
            
            # Sesiones activas (estimado basado en últimos 30 minutos)
            sesiones_activas = 1
            try:
                cursor.execute('SELECT COUNT(DISTINCT usuario_id) FROM auditoria_login WHERE fecha_login > datetime("now", "-30 minutes") AND exito = 1')
                result = cursor.fetchone()
                sesiones_activas = result[0] if result and result[0] else 1
            except:
                sesiones_activas = 1
            
            conn.close()
            
            return {
                'total_usuarios': total_usuarios,
                'usuarios_activos': usuarios_activos,
                'logins_hoy': logins_hoy,
                'sesiones_activas': sesiones_activas
            }
            
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return {
                'total_usuarios': 0,
                'usuarios_activos': 0,
                'logins_hoy': 0,
                'sesiones_activas': 1
            }