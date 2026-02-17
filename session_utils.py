# session_utils.py
import streamlit as st
import time
import json

class SessionManager:
    def __init__(self, timeout_minutes=480):  # 8 horas
        self.timeout_minutes = timeout_minutes
        print(f"✅ SessionManager inicializado con timeout: {timeout_minutes}min")
        
    def save_session(self, user_data):
        """Guardar sesión en session_state"""
        try:
            session_data = {
                'user': user_data,
                'login_time': time.time(),
                'expiry_time': time.time() + (self.timeout_minutes * 60)
            }
            st.session_state.persistent_session = session_data
            print(f"✅ Sesión GUARDADA para: {user_data.get('email', 'Unknown')}")
            return True
        except Exception as e:
            print(f"❌ Error guardando sesión: {e}")
            return False
    
    def load_session(self):
        """Cargar sesión desde session_state"""
        try:
            if hasattr(st.session_state, 'persistent_session'):
                session_data = st.session_state.persistent_session
                current_time = time.time()
                
                print(f"🔍 Sesión encontrada, expira en: {(session_data['expiry_time'] - current_time)/60:.1f}min")
                
                if current_time < session_data['expiry_time']:
                    user_email = session_data['user'].get('email', 'Unknown')
                    print(f"✅ Sesión CARGADA para: {user_email}")
                    return session_data['user']
                else:
                    print("⚠️ Sesión EXPIRADA")
                    self.clear_session()
            else:
                print("🔍 No hay sesión persistente")
            return None
        except Exception as e:
            print(f"❌ Error cargando sesión: {e}")
            return None
    
    def clear_session(self):
        """Limpiar sesión"""
        try:
            if hasattr(st.session_state, 'persistent_session'):
                del st.session_state.persistent_session
                print("✅ Sesión LIMPIADA")
        except Exception as e:
            print(f"❌ Error limpiando sesión: {e}")

# Instancia global
session_manager = SessionManager()
print("✅ session_utils.py cargado completamente")