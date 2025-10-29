import sys
import os
import logging
from pathlib import Path

# Configurar logging antes de cualquier import
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crm_system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def check_dependencies():
    """Verifica que todas las dependencias estén instaladas"""
    required_packages = {
        'pandas': 'pandas',
        'numpy': 'numpy', 
        'matplotlib': 'matplotlib',
        'seaborn': 'seaborn',
        'openpyxl': 'openpyxl',
        'PySide6': 'PySide6'
    }
    
    missing_packages = []
    
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            logger.info(f"✅ {package_name} está instalado")
        except ImportError as e:
            missing_packages.append(package_name)
            logger.error(f"❌ {package_name} no está instalado: {e}")
    
    if missing_packages:
        logger.error(f"Paquetes faltantes: {', '.join(missing_packages)}")
        print(f"❌ Paquetes faltantes: {', '.join(missing_packages)}")
        print("Por favor ejecuta: pip install -r requirements.txt")
        return False
    
    logger.info("Todas las dependencias están instaladas correctamente")
    return True

def setup_environment():
    """Configura el entorno de la aplicación"""
    try:
        # Validar configuración
        from config import config
        config.validate_environment()
        
        # Crear directorios necesarios
        required_dirs = ['assets', 'exports', 'backups']
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Directorio creado: {dir_path}")
        
        # Verificar archivos esenciales
        essential_files = ['cartera_crm.db', 'styles.py', 'config.py']
        for file in essential_files:
            if not Path(file).exists():
                logger.warning(f"Archivo {file} no encontrado - se creará automáticamente")
        
        # Verificar assets
        assets_dir = Path('assets')
        required_assets = ['logo.png', 'icon.ico']
        for asset in required_assets:
            asset_path = assets_dir / asset
            if not asset_path.exists():
                logger.warning(f"Asset no encontrado: {asset}")
        
        logger.info("Entorno configurado correctamente")
        return True
        
    except Exception as e:
        logger.error(f"Error configurando entorno: {e}")
        return False

def initialize_database():
    """Inicializa la base de datos si no existe"""
    try:
        from database import DatabaseManager
        db = DatabaseManager()
        logger.info("Base de datos inicializada correctamente")
        return True
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {e}")
        return False

def main():
    """Función principal de la aplicación"""
    try:
        logger.info("=" * 50)
        logger.info("INICIANDO CRM ALPAPEL SAS")
        logger.info("=" * 50)
        
        # Verificar dependencias
        if not check_dependencies():
            sys.exit(1)
        
        # Configurar entorno
        if not setup_environment():
            sys.exit(1)
        
        # Inicializar base de datos
        if not initialize_database():
            sys.exit(1)
        
        # Importar e iniciar la aplicación GUI
        from crm_gui import main as gui_main
        
        logger.info("Aplicación iniciada correctamente")
        gui_main()
        
    except KeyboardInterrupt:
        logger.info("Aplicación interrumpida por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Error crítico en la aplicación: {e}")
        # Mostrar mensaje de error al usuario
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            app = QApplication([])
            QMessageBox.critical(
                None, 
                "Error Crítico", 
                f"Error al iniciar la aplicación:\n\n{str(e)}\n\n"
                "Por favor contacte al administrador del sistema."
            )
        except:
            print(f"Error crítico: {e}")
        sys.exit(1)
    finally:
        logger.info("CRM cerrado")

if __name__ == "__main__":
    main()