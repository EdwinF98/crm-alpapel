# auth.py - VERSIÓN STREAMLIT
import time
from config import config

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
        # TU MÉTODO EXISTENTE - mantenerlo igual
        if not self.current_user or not self.is_authenticated:
            return []
        
        user_role = self.current_user['rol']
        user_vendedor = self.current_user.get('vendedor_asignado')
        
        if user_role == 'admin':
            try:
                vendedores_df = self.user_manager.get_connection().execute(
                    'SELECT nombre_vendedor FROM vendedores ORDER BY nombre_vendedor'
                ).fetchall()
                vendedores = ["Todos los vendedores"] + [v[0] for v in vendedores_df if v[0]]
                return vendedores
            except Exception as e:
                print(f"Error obteniendo vendedores: {e}")
                return ["Todos los vendedores", user_vendedor] if user_vendedor else ["Todos los vendedores"]
        elif user_role == 'supervisor':
            try:
                vendedores_df = self.user_manager.get_connection().execute(
                    'SELECT nombre_vendedor FROM vendedores ORDER BY nombre_vendedor'
                ).fetchall()
                vendedores = ["Todos los vendedores"] + [v[0] for v in vendedores_df if v[0]]
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