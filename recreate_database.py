# recreate_database.py
import sqlite3
import os
import hashlib
import secrets
from datetime import datetime

def crear_base_datos_completa():
    """Crea la base de datos cartera_crm.db con la estructura exacta y el usuario admin solicitado"""
    
    db_name = "cartera_crm.db"
    
    # Eliminar base de datos existente si existe para limpieza total
    if os.path.exists(db_name):
        try:
            os.remove(db_name)
            print(f"🗑️ Base de datos '{db_name}' anterior eliminada")
        except PermissionError:
            print(f"❌ ERROR: No se pudo eliminar '{db_name}'. Asegúrate de cerrar Streamlit primero.")
            return

    # Conectar a la nueva base de datos
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    print("🔄 Creando estructura de base de datos sincronizada...")

    # --- 1. TABLA DE VENDEDORES ---
    cursor.execute('''
        CREATE TABLE vendedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_vendedor TEXT UNIQUE
        )
    ''')

    # --- 2. TABLA DE CLIENTES ---
    cursor.execute('''
        CREATE TABLE clientes (
            nit_cliente TEXT PRIMARY KEY,
            razon_social TEXT NOT NULL,
            telefono TEXT,
            celular TEXT,
            direccion TEXT,
            email TEXT,
            ciudad TEXT,
            vendedor_asignado TEXT,
            estado_cupo TEXT DEFAULT 'activo',
            fecha_registro DATE DEFAULT CURRENT_DATE,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- 3. TABLA DE CARTERA ACTUAL ---
    cursor.execute('''
        CREATE TABLE cartera_actual (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nit_cliente TEXT,
            razon_social_cliente TEXT,
            nombre_vendedor TEXT,
            centro_operacion TEXT,
            nro_factura TEXT,
            total_cop REAL,
            fecha_emision DATE,
            fecha_vencimiento DATE,
            condicion_pago TEXT,
            dias_vencidos INTEGER,
            dias_gracia INTEGER,
            fecha_carga DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (nit_cliente) REFERENCES clientes (nit_cliente)
        )
    ''')

    # --- 4. TABLA DE GESTIONES ---
    cursor.execute('''
        CREATE TABLE gestiones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nit_cliente TEXT,
            razon_social_cliente TEXT,
            tipo_contacto TEXT,
            resultado TEXT,
            fecha_contacto DATETIME,
            usuario TEXT,
            observaciones TEXT,
            promesa_pago_fecha DATE,
            promesa_pago_monto REAL,
            proxima_gestion DATE,
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (nit_cliente) REFERENCES clientes (nit_cliente)
        )
    ''')

    # --- 5. TABLA DE HISTORIAL CARTERA DIARIO ---
    cursor.execute('''
        CREATE TABLE historial_cartera_diario (
            fecha_carga DATE,
            nit_cliente TEXT,
            razon_social_cliente TEXT,
            nombre_vendedor TEXT,
            centro_operacion TEXT,
            nro_factura TEXT,
            total_cop REAL,
            fecha_emision DATE,
            fecha_vencimiento DATE,
            condicion_pago TEXT,
            dias_vencidos INTEGER,
            dias_gracia INTEGER,
            telefono TEXT,
            celular TEXT,
            direccion TEXT,
            email TEXT,
            ciudad TEXT,
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (fecha_carga, nit_cliente, nro_factura)
        )
    ''')

    # --- 6. TABLA DE USUARIOS (Sincronizada con auth.py) ---
    cursor.execute('''
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nombre_completo TEXT NOT NULL,
            rol TEXT NOT NULL DEFAULT 'comercial',
            vendedor_asignado TEXT,
            activo INTEGER DEFAULT 1,
            intentos_fallidos INTEGER DEFAULT 0,
            bloqueado_hasta DATETIME,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            ultimo_login DATETIME,
            email_verificado INTEGER DEFAULT 0
        )
    ''')

    # --- 7. TABLA DE AUDITORÍA ---
    cursor.execute('''
        CREATE TABLE auditoria_login (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            email TEXT,
            ip_address TEXT,
            user_agent TEXT,
            exito INTEGER,
            fecha_login DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- FUNCIÓN DE ENCRIPTACIÓN ---
    def hash_password(password):
        salt = secrets.token_hex(16)
        return f"{salt}${hashlib.sha256((salt + password).encode()).hexdigest()}"

    # --- USUARIO ADMINISTRADOR SOLICITADO ---
    admin_email = "cartera@alpapel.com"
    admin_password = "12345678"  # <--- Contraseña ajustada para ti
    admin_hash = hash_password(admin_password)

    cursor.execute('''
        INSERT INTO usuarios (email, password_hash, nombre_completo, rol, activo)
        VALUES (?, ?, ?, ?, 1)
    ''', (admin_email, admin_hash, 'Administrador ALPAPEL', 'admin'))

    # --- ÍNDICES ---
    cursor.execute('CREATE INDEX idx_cartera_vencidos ON cartera_actual(dias_vencidos)')
    cursor.execute('CREATE INDEX idx_usuarios_email ON usuarios(email)')

    conn.commit()
    conn.close()
    
    print(f"\n🎉 ¡BASE DE DATOS CREADA EXITOSAMENTE!")
    print(f"=======================================")
    print(f"📧 Usuario: {admin_email}")
    print(f"🔐 Clave:   {admin_password}")
    print(f"📍 Ubicación: {os.path.abspath(db_name)}")

if __name__ == "__main__":
    crear_base_datos_completa()