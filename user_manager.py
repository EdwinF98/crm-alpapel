"""
Módulo de Gestión de Usuarios - WRAPPER
Este archivo ahora es solo un wrapper para importar UserManager desde auth.py
"""

# Importar la clase real desde auth.py
from auth import UserManager

# Exportar la misma clase para compatibilidad
__all__ = ['UserManager']

# Nota: Todos los métodos están en la clase UserManager de auth.py
# Este archivo solo sirve como punto de importación único