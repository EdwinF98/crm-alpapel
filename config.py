import os
from datetime import timedelta

class Config:
    # Configuración de la aplicación
    APP_NAME = "CRM Cartera - ALPAPEL SAS"
    COMPANY_DOMAIN = "alpapel.com"
    VERSION = "2.0.1"  # Versión actualizada
    
    # Base de datos
    DB_PATH = "cartera_crm.db"
    
    # Configuración de email
    EMAIL_HOST = "smtp.office365.com"
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_TIMEOUT = 30
    
    # Seguridad
    SESSION_TIMEOUT_MINUTES = 60  # Aumentado a 1 hora
    PASSWORD_MIN_LENGTH = 8
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_TIME_MINUTES = 30
    
    # Configuración de interfaz
    UI_REFRESH_INTERVAL = 30000  # 30 segundos
    CHART_UPDATE_INTERVAL = 60000  # 1 minuto
    SESSION_CHECK_INTERVAL = 300000  # Revisar cada 5 minutos (300,000 ms)
    
    # Colores corporativos
    THEME_COLORS = {
        'primary': '#00B3B0',
        'accent': '#F57C00',
        'danger': '#dc2626',
        'success': '#10b981',
        'warning': '#f59e0b',
        'info': '#3b82f6'
    }
    
    # Roles del sistema
    ROLES = {
        'admin': 'Administrador',
        'supervisor': 'Supervisor', 
        'comercial': 'Comercial',
        'consulta': 'Consulta'
    }
    
    # Configuración de exportación
    EXPORT_FORMATS = {
        'excel': '.xlsx',
        'csv': '.csv'
    }
    
    # Límites del sistema
    MAX_FILE_SIZE_MB = 50
    MAX_RECORDS_PER_PAGE = 1000
    
    @classmethod
    def get_database_path(cls):
        """Obtiene la ruta completa de la base de datos"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, cls.DB_PATH)
    
    @classmethod
    def get_assets_path(cls):
        """Obtiene la ruta de la carpeta assets"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, 'assets')
    
    @classmethod
    def validate_environment(cls):
        """Valida que el entorno esté configurado correctamente"""
        required_dirs = ['assets']
        for dir_name in required_dirs:
            dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), dir_name)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                print(f"Directorio creado: {dir_path}")

# Instancia global de configuración
config = Config()