# session_manager.py
import streamlit as st
import time
from datetime import datetime, timedelta

class SessionManager:
    def __init__(self, max_sessions=50, session_timeout=60):
        self.max_sessions = max_sessions
        self.session_timeout = session_timeout  # minutos
        self.active_sessions = {}
    
    def can_create_session(self, user_id):
        """Verificar si se puede crear nueva sesión"""
        self.clean_expired_sessions()
        return len(self.active_sessions) < self.max_sessions
    
    def create_session(self, user_id, session_data):
        """Crear nueva sesión"""
        if not self.can_create_session(user_id):
            return False
        
        self.active_sessions[user_id] = {
            'data': session_data,
            'created_at': datetime.now(),
            'last_activity': datetime.now()
        }
        return True
    
    def update_activity(self, user_id):
        """Actualizar actividad de sesión"""
        if user_id in self.active_sessions:
            self.active_sessions[user_id]['last_activity'] = datetime.now()
    
    def clean_expired_sessions(self):
        """Limpiar sesiones expiradas"""
        now = datetime.now()
        expired = []
        for user_id, session in self.active_sessions.items():
            if (now - session['last_activity']).total_seconds() > self.session_timeout * 60:
                expired.append(user_id)
        
        for user_id in expired:
            del self.active_sessions[user_id]
    
    def get_active_count(self):
        """Obtener número de sesiones activas"""
        self.clean_expired_sessions()
        return len(self.active_sessions)

# Instancia global
session_manager = SessionManager()