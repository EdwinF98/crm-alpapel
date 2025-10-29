# session_utils.py
import streamlit as st
import time
import json
from datetime import datetime, timedelta

class SessionManager:
    def __init__(self, timeout_minutes=480):  # 8 horas por defecto
        self.timeout_minutes = timeout_minutes
        
    def save_session(self, user_data):
        """Guardar sesión en session_state persistente"""
        try:
            session_data = {
                'user': user_data,
                'login_time': time.time(),
                'expiry_time': time.time() + (self.timeout_minutes * 60)
            }
            # Guardar en session_state
            st.session_state.persistent_session = session_data
            print(f"✅ Sesión guardada para {user_data['email']}")
            return True
        except Exception as e:
            print(f"❌ Error guardando sesión: {e}")
            return False
    
    def load_session(self):
        """Cargar sesión desde session_state"""
        try:
            if 'persistent_session' in st.session_state:
                session_data = st.session_state.persistent_session
                
                # Verificar si la sesión no ha expirado
                current_time = time.time()
                if current_time < session_data['expiry_time']:
                    print(f"✅ Sesión cargada para {session_data['user']['email']}")
                    return session_data['user']
                else:
                    print("⚠️ Sesión expirada")
                    self.clear_session()
            return None
        except Exception as e:
            print(f"❌ Error cargando sesión: {e}")
            return None
    
    def clear_session(self):
        """Limpiar sesión persistente"""
        try:
            if 'persistent_session' in st.session_state:
                del st.session_state.persistent_session
                print("✅ Sesión limpiada")
            return True
        except Exception as e:
            print(f"❌ Error limpiando sesión: {e}")
            return False
    
    def get_remaining_time(self):
        """Obtener tiempo restante de sesión en minutos"""
        if 'persistent_session' in st.session_state:
            session_data = st.session_state.persistent_session
            remaining = (session_data['expiry_time'] - time.time()) / 60
            return max(0, int(remaining))
        return 0

# Instancia global
session_manager = SessionManager()