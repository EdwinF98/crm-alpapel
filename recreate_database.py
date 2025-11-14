# recreate_database.py
import sqlite3
import os
import hashlib
import secrets
from datetime import datetime

def crear_base_datos_completa():
    """Crea la base de datos cartera_crm.db con todas las tablas y usuario admin"""
    
    # Eliminar base de datos existente si existe
    if os.path.exists("cartera_crm.db"):
        os.remove("cartera_crm.db")
        print("🗑️  Base de datos anterior eliminada")
    
    # Conectar a la nueva base de datos
    conn = sqlite3.connect("cartera_crm.db")
    cursor = conn.cursor()
    
    print("🔄 Creando estructura de base de datos...")
    
    # ============================================================
    # 1. TABLA DE VENDEDORES
    # ============================================================
    cursor.execute('''
        CREATE TABLE vendedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_vendedor TEXT UNIQUE
        )
    ''')
    print("✅ Tabla 'vendedores' creada")
    
    # ============================================================
    # 2. TABLA DE CLIENTES
    # ============================================================
    cursor.execute('''
        CREATE TABLE clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nit_cliente TEXT UNIQUE,
            razon_social TEXT,
            telefono TEXT,
            celular TEXT,
            direccion TEXT,
            email TEXT,
            ciudad TEXT,
            vendedor_asignado TEXT,
            estado_cupo TEXT DEFAULT 'activo',
            fecha_registro DATE DEFAULT CURRENT_DATE
        )
    ''')
    print("✅ Tabla 'clientes' creada")
    
    # ============================================================
    # 3. TABLA DE CARTERA ACTUAL
    # ============================================================
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
            fecha_carga DATE DEFAULT CURRENT_DATE
        )
    ''')
    print("✅ Tabla 'cartera_actual' creada")
    
    # ============================================================
    # 4. TABLA DE HISTORIAL CARTERA
    # ============================================================
    cursor.execute('''
        CREATE TABLE historial_cartera (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nit_cliente TEXT,
            nro_factura TEXT,
            total_cop REAL,
            fecha_emision DATE,
            fecha_vencimiento DATE,
            condicion_pago TEXT,
            dias_vencidos INTEGER,
            fecha_registro DATE
        )
    ''')
    print("✅ Tabla 'historial_cartera' creada")
    
    # ============================================================
    # 5. TABLA DE GESTIONES
    # ============================================================
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
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Tabla 'gestiones' creada")
    
    # ============================================================
    # 6. TABLA DE HISTORIAL CARTERA DIARIO
    # ============================================================
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
    print("✅ Tabla 'historial_cartera_diario' creada")
    
    # ============================================================
    # 7. TABLA DE USUARIOS (SISTEMA DE AUTENTICACIÓN)
    # ============================================================
    cursor.execute('''
        CREATE TABLE usuarios (
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
    print("✅ Tabla 'usuarios' creada")
    
    # ============================================================
    # 8. TABLA DE AUDITORÍA LOGIN
    # ============================================================
    cursor.execute('''
        CREATE TABLE auditoria_login (
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
    print("✅ Tabla 'auditoria_login' creada")
    
    # ============================================================
    # CREAR USUARIO ADMINISTRADOR INICIAL
    # ============================================================
    def hash_password(password):
        """Encripta la contraseña usando SHA-256 con salt"""
        salt = secrets.token_hex(16)
        return f"{salt}${hashlib.sha256((salt + password).encode()).hexdigest()}"
    
    admin_email = "cartera@alpapel.com"
    admin_password = "12345678"
    admin_password_hash = hash_password(admin_password)
    
    cursor.execute('''
        INSERT INTO usuarios (email, password_hash, nombre_completo, rol, email_verificado, activo)
        VALUES (?, ?, ?, ?, 1, 1)
    ''', (admin_email, admin_password_hash, 'Administrador Principal', 'admin'))
    
    print("✅ Usuario administrador creado:")
    print(f"   📧 Email: {admin_email}")
    print(f"   🔐 Password: {admin_password}")
    print(f"   👤 Nombre: Administrador Principal")
    print(f"   🎭 Rol: admin")
    
    # ============================================================
    # CREAR ÍNDICES PARA MEJOR PERFORMANCE
    # ============================================================
    
    # Índices para cartera
    cursor.execute('CREATE INDEX idx_cartera_nit ON cartera_actual(nit_cliente)')
    cursor.execute('CREATE INDEX idx_cartera_vendedor ON cartera_actual(nombre_vendedor)')
    cursor.execute('CREATE INDEX idx_cartera_dias_vencidos ON cartera_actual(dias_vencidos)')
    
    # Índices para clientes
    cursor.execute('CREATE INDEX idx_clientes_nit ON clientes(nit_cliente)')
    cursor.execute('CREATE INDEX idx_clientes_vendedor ON clientes(vendedor_asignado)')
    
    # Índices para gestiones
    cursor.execute('CREATE INDEX idx_gestiones_nit ON gestiones(nit_cliente)')
    cursor.execute('CREATE INDEX idx_gestiones_fecha ON gestiones(fecha_contacto)')
    cursor.execute('CREATE INDEX idx_gestiones_usuario ON gestiones(usuario)')
    
    # Índices para usuarios
    cursor.execute('CREATE INDEX idx_usuarios_email ON usuarios(email)')
    cursor.execute('CREATE INDEX idx_usuarios_rol ON usuarios(rol)')
    
    print("✅ Índices de performance creados")
    
    # ============================================================
    # FINALIZAR
    # ============================================================
    
    conn.commit()
    conn.close()
    
    print("")
    print("🎉 ¡BASE DE DATOS CREADA EXITOSAMENTE!")
    print("=======================================")
    print("📍 Archivo: cartera_crm.db")
    print("📊 Tablas creadas: 8")
    print("👤 Usuario admin: cartera@alpapel.com / 12345678")
    print("")
    print("✅ Tu aplicación Streamlit funcionará inmediatamente")
    print("✅ Todo se guardará sincrónicamente en esta base de datos")
    print("✅ Sistema multiusuario listo para usar")

if __name__ == "__main__":
    crear_base_datos_completa()