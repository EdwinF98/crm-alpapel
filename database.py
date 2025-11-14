import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
import traceback
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

class DatabaseManager:
    def __init__(self):
        self.db_path = self.get_database_path()
        self.init_database()
        self.current_user = None
    
    def set_current_user(self, user_data):
        """Establece el usuario actual para filtrado"""
        self.current_user = user_data
    
    def get_database_path(self):
        """Usa Google Drive con credentials.json para persistencia real"""
        import os
        
        # ✅ CONFIGURACIÓN - CAMBIA ESTOS VALORES
        CREDENTIALS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
        DRIVE_FOLDER_ID = "1G8EcHjHrjM5m_BqU3GOkgtG8F_lJifnS"  # ⬅️ ID de la carpeta en Google Drive
        DRIVE_DB_NAME = "cartera_crm.db"
        
        # Verificar que credentials.json existe
        if not os.path.exists(CREDENTIALS_PATH):
            print("❌ credentials.json no encontrado. Usando SQLite local.")
            return self.get_fallback_db_path()
        
        try:
            print("🔑 Conectando a Google Drive...")
            
            # Crear servicio de Google Drive
            credentials = service_account.Credentials.from_service_account_file(
                CREDENTIALS_PATH, 
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            drive_service = build('drive', 'v3', credentials=credentials)
            
            # ✅ BUSCAR ARCHIVO EXISTENTE EN GOOGLE DRIVE
            query = f"name='{DRIVE_DB_NAME}' and '{DRIVE_FOLDER_ID}' in parents and trashed=false"
            results = drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            files = results.get('files', [])
            
            # Ruta local temporal para trabajar con la BD
            local_db_path = os.path.join(os.path.dirname(__file__), "temp_cartera_crm.db")
            
            if files:
                # ✅ DESCARGAR BD EXISTENTE DE GOOGLE DRIVE
                print("📥 Descargando base de datos desde Google Drive...")
                file_id = files[0]['id']
                
                request = drive_service.files().get_media(fileId=file_id)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                
                # Guardar localmente
                with open(local_db_path, 'wb') as f:
                    f.write(fh.getvalue())
                    
                print(f"✅ Base de datos descargada: {local_db_path}")
                
            else:
                # ✅ CREAR NUEVA BD EN GOOGLE DRIVE
                print("🆕 Creando nueva base de datos en Google Drive...")
                
                # Crear BD local vacía primero
                self.create_empty_database(local_db_path)
                
                # Subir a Google Drive
                file_metadata = {
                    'name': DRIVE_DB_NAME,
                    'parents': [DRIVE_FOLDER_ID]
                }
                media = MediaFileUpload(local_db_path, resumable=True)
                file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                
                print(f"✅ Nueva base de datos creada en Google Drive. ID: {file.get('id')}")
            
            # ✅ CONFIGURAR SYNC AUTOMÁTICO
            if hasattr(st, 'session_state'):
                st.session_state.drive_service = drive_service
                st.session_state.drive_file_id = files[0]['id'] if files else file.get('id')
                st.session_state.local_db_path = local_db_path
            
            print(f"📍 Trabajando con: {local_db_path} (sincronizado con Google Drive)")
            return local_db_path
            
        except Exception as e:
            print(f"❌ Error con Google Drive: {e}")
            return self.get_fallback_db_path()
    
    def get_fallback_db_path(self):
        """Fallback a SQLite local si Google Drive falla"""
        import os
        fallback_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cartera_crm_local.db")
        print(f"📍 Fallback a BD local: {fallback_path}")
        return fallback_path
    
    def create_empty_database(self, db_path):
        """Crea una base de datos vacía con la estructura necesaria"""
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Crear tabla de usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                nombre_completo TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT 'comercial',
                vendedor_asignado TEXT,
                activo INTEGER DEFAULT 1
            )
        ''')
        
        # Insertar usuario admin por defecto
        from auth import UserManager
        user_manager = UserManager(db_path)
        default_password = user_manager.hash_password("12345678")
        
        cursor.execute('''
            INSERT OR IGNORE INTO usuarios 
            (email, password_hash, nombre_completo, rol, activo)
            VALUES (?, ?, ?, ?, 1)
        ''', ('cartera@alpapel.com', default_password, 'Administrador Principal', 'admin'))
        
        # Crear el resto de tablas (tu estructura actual)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vendedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_vendedor TEXT UNIQUE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cartera_actual (
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
        
        # ... (AGREGA AQUÍ TODAS LAS DEMÁS TABLAS DE TU init_database ACTUAL)
        
        conn.commit()
        conn.close()
        print(f"✅ Base de datos vacía creada: {db_path}")

    def sync_to_drive(self):
        """Sincroniza la base de datos local con Google Drive"""
        try:
            if hasattr(st, 'session_state') and hasattr(st.session_state, 'drive_service'):
                drive_service = st.session_state.drive_service
                file_id = st.session_state.drive_file_id
                local_path = st.session_state.local_db_path
                
                if drive_service and file_id and local_path and os.path.exists(local_path):
                    print("🔄 Sincronizando con Google Drive...")
                    
                    media = MediaFileUpload(local_path, resumable=True)
                    updated_file = drive_service.files().update(
                        fileId=file_id,
                        media_body=media
                    ).execute()
                    
                    print("✅ Sincronización completada")
                    return True
        except Exception as e:
            print(f"❌ Error en sincronización: {e}")
        return False

    def init_database(self):
        """Inicializa la base de datos con todas las tablas necesarias"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de vendedores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vendedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_vendedor TEXT UNIQUE
            )
        ''')
        
        # Tabla de clientes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
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
        
        # Tabla de cartera actual
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cartera_actual (
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
        
        # Tabla de historial de cartera
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historial_cartera (
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
        
        # Tabla de gestiones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gestiones (
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
        
        # Tabla de historial cartera diario
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historial_cartera_diario (
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
        
        conn.commit()
        conn.close()
    
    def convertir_fecha(self, fecha):
        """Convierte diferentes formatos de fecha a string YYYY-MM-DD"""
        if pd.isna(fecha):
            return None
        if isinstance(fecha, str):
            try:
                for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%y']:
                    try:
                        return datetime.strptime(fecha, fmt).strftime('%Y-%m-%d')
                    except ValueError:
                        continue
                return None
            except:
                return None
        elif hasattr(fecha, 'strftime'):
            return fecha.strftime('%Y-%m-%d')
        return str(fecha)
    
    def limpiar_valor_monetario(self, valor):
        """Limpia y convierte valores monetarios"""
        if pd.isna(valor):
            return 0.0
        if isinstance(valor, str):
            valor = valor.replace('$', '').replace('.', '').replace(',', '.').replace(' ', '').strip()
            try:
                return float(valor)
            except:
                return 0.0
        return float(valor)
    
    # ============================================================
    # 🆕 NUEVA FUNCIÓN PARA RANGOS DE FECHA - FILTROS DINÁMICOS
    # ============================================================
    
    def obtener_rango_fechas_por_periodo(self, periodo_seleccionado, fecha_inicio_personalizada=None, fecha_fin_personalizada=None):
        """Calcula el rango de fechas según el período seleccionado"""
        hoy = datetime.now()
        
        if periodo_seleccionado == "Mes Actual":
            inicio = hoy.replace(day=1)
            fin = hoy
        elif periodo_seleccionado == "Mes Anterior":
            primer_dia_mes_actual = hoy.replace(day=1)
            fin = primer_dia_mes_actual - timedelta(days=1)
            inicio = fin.replace(day=1)
        elif periodo_seleccionado == "Últimos 7 días":
            inicio = hoy - timedelta(days=7)
            fin = hoy
        elif periodo_seleccionado == "Últimos 30 días":
            inicio = hoy - timedelta(days=30)
            fin = hoy
        elif periodo_seleccionado == "Trimestre Actual":
            trimestre_actual = (hoy.month - 1) // 3
            inicio = datetime(hoy.year, trimestre_actual * 3 + 1, 1)
            fin = hoy
        elif periodo_seleccionado == "Personalizado" and fecha_inicio_personalizada and fecha_fin_personalizada:
            # Usar fechas personalizadas
            inicio = datetime.strptime(fecha_inicio_personalizada, '%Y-%m-%d')
            fin = datetime.strptime(fecha_fin_personalizada, '%Y-%m-%d')
        else:
            # Por defecto: mes actual
            inicio = hoy.replace(day=1)
            fin = hoy
        
        return inicio.strftime('%Y-%m-%d'), fin.strftime('%Y-%m-%d')
    
    def cargar_excel_cartera(self, file_path):
        """Carga datos del Excel de cartera a la base de datos"""
        try:
            df = pd.read_excel(file_path)
            
            column_mapping = {
                'Razón social vend. cliente': 'nombre_vendedor',
                'Cliente': 'nit_cliente', 
                'Razón social sucursal': 'razon_social_cliente',
                'C.O.': 'centro_operacion',
                'Nro. docto. cruce': 'nro_factura',
                'Total COP': 'total_cop',
                'Fecha docto cruce': 'fecha_emision',
                'Fecha vcto.': 'fecha_vencimiento',
                'Cond. pago cliente': 'condicion_pago',
                'Dias vencidos': 'dias_vencidos',
                'Dias gracia': 'dias_gracia',
                'Teléfono': 'telefono',
                'Celular': 'celular',
                'Dirección 1': 'direccion',
                'Email': 'email',
                'Ciudad': 'ciudad'
            }
            
            existing_columns = {}
            for orig_col, new_col in column_mapping.items():
                if orig_col in df.columns:
                    existing_columns[orig_col] = new_col
            
            df = df.rename(columns=existing_columns)
            
            if 'total_cop' in df.columns:
                df['total_cop'] = df['total_cop'].apply(self.limpiar_valor_monetario)
            
            if 'dias_vencidos' in df.columns:
                df['dias_vencidos'] = pd.to_numeric(df['dias_vencidos'], errors='coerce').fillna(0)
            
            if 'dias_gracia' in df.columns:
                df['dias_gracia'] = pd.to_numeric(df['dias_gracia'], errors='coerce').fillna(0)
            
            if 'fecha_emision' in df.columns:
                df['fecha_emision'] = df['fecha_emision'].apply(self.convertir_fecha)
            
            if 'fecha_vencimiento' in df.columns:
                df['fecha_vencimiento'] = df['fecha_vencimiento'].apply(self.convertir_fecha)
            
            conn = sqlite3.connect(self.db_path)
            
            # 1. Insertar vendedores
            if 'nombre_vendedor' in df.columns:
                vendedores_unicos = df['nombre_vendedor'].dropna().unique()
                for vendedor in vendedores_unicos:
                    if vendedor and str(vendedor).strip() != '':
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT OR IGNORE INTO vendedores (nombre_vendedor)
                            VALUES (?)
                        ''', (str(vendedor).strip(),))
            
            # 2. Insertar clientes
            for _, row in df.iterrows():
                if 'nit_cliente' in df.columns and pd.notna(row['nit_cliente']):
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO clientes 
                        (nit_cliente, razon_social, telefono, celular, direccion, 
                         email, ciudad, vendedor_asignado)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        str(row['nit_cliente']),
                        str(row.get('razon_social_cliente', '')),
                        str(row.get('telefono', '')),
                        str(row.get('celular', '')),
                        str(row.get('direccion', '')),
                        str(row.get('email', '')),
                        str(row.get('ciudad', '')),
                        str(row.get('nombre_vendedor', ''))
                    ))
            
            # 3. Limpiar cartera actual e insertar nueva
            cursor.execute('DELETE FROM cartera_actual')
            
            for _, row in df.iterrows():
                if 'nit_cliente' in df.columns and pd.notna(row['nit_cliente']):
                    cursor.execute('''
                        INSERT INTO cartera_actual 
                        (nit_cliente, razon_social_cliente, nombre_vendedor, centro_operacion,
                         nro_factura, total_cop, fecha_emision, fecha_vencimiento,
                         condicion_pago, dias_vencidos, dias_gracia)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        str(row['nit_cliente']),
                        str(row.get('razon_social_cliente', '')),
                        str(row.get('nombre_vendedor', '')),
                        str(row.get('centro_operacion', '')),
                        str(row.get('nro_factura', '')),
                        float(row.get('total_cop', 0)),
                        row.get('fecha_emision'),
                        row.get('fecha_vencimiento'),
                        str(row.get('condicion_pago', '')),
                        int(row.get('dias_vencidos', 0)),
                        int(row.get('dias_gracia', 0))
                    ))
            
            # 4. Guardar en historial
            cursor.execute('''
                INSERT INTO historial_cartera 
                (nit_cliente, nro_factura, total_cop, fecha_emision,
                 fecha_vencimiento, condicion_pago, dias_vencidos, fecha_registro)
                SELECT nit_cliente, nro_factura, total_cop, fecha_emision,
                       fecha_vencimiento, condicion_pago, dias_vencidos, CURRENT_DATE
                FROM cartera_actual
            ''')
            
            conn.commit()
            conn.close()
            self.sync_to_drive()
            
            return True, f"Cartera cargada exitosamente. {len(df)} registros procesados."
            
        except Exception as e:
            return False, f"Error al cargar Excel: {str(e)}"
    
    def obtener_cartera_actual(self):
        """Obtiene la cartera actual - VERSIÓN CORREGIDA"""
        conn = sqlite3.connect(self.db_path)
        
        user = self.current_user
                
        if not user:
            # Si no hay usuario, mostrar datos limitados o todos
            query = 'SELECT * FROM cartera_actual'
            params = ()
        else:
            # ✅ ADMIN y SUPERVISOR ven TODOS los datos
            if user['rol'] in ['admin', 'supervisor']:
                query = 'SELECT * FROM cartera_actual'
                params = ()
            elif user['rol'] in ['comercial', 'consulta']:
                vendedor = user.get('vendedor_asignado')
                if vendedor:
                    query = 'SELECT * FROM cartera_actual WHERE nombre_vendedor = ?'
                    params = (vendedor,)
                else:
                    # ✅ CORRECCIÓN: Si es comercial sin vendedor, mostrar TODOS los datos temporalmente
                    query = 'SELECT * FROM cartera_actual'
                    params = ()
                    print("🔍 DEBUG - Comercial sin vendedor, mostrando TODOS los datos")
            else:
                query = 'SELECT * FROM cartera_actual'
                params = ()
        
        query += ' ORDER BY dias_vencidos DESC, total_cop DESC'
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def obtener_clientes(self):
        """Obtiene todos los clientes FILTRADOS por usuario - VERSIÓN CORREGIDA"""
        conn = sqlite3.connect(self.db_path)
        
        user = self.current_user
        if not user:
            query = 'SELECT * FROM clientes WHERE 1=0'
            params = ()
        else:
            # ✅ CORREGIDO: Admin y supervisor ven TODOS los clientes
            if user['rol'] in ['admin', 'supervisor']:
                query = 'SELECT * FROM clientes'
                params = ()
                print("🔍 DEBUG - Mostrando TODOS los clientes (admin/supervisor)")
            elif user['rol'] in ['comercial', 'consulta']:
                vendedor = user.get('vendedor_asignado')
                if vendedor:
                    query = 'SELECT * FROM clientes WHERE vendedor_asignado = ?'
                    params = (vendedor,)
                    print(f"🔍 DEBUG - Filtrando clientes por vendedor: {vendedor}")
                else:
                    # Si es comercial pero no tiene vendedor, no mostrar clientes
                    query = 'SELECT * FROM clientes WHERE 1=0'
                    params = ()
                    print("🔍 DEBUG - Comercial sin vendedor asignado, no muestra clientes")
            else:
                query = 'SELECT * FROM clientes WHERE 1=0'
                params = ()
        
        query += ' ORDER BY razon_social'
        
        try:
            df = pd.read_sql_query(query, conn, params=params)
            print(f"🔍 DEBUG - Clientes obtenidos: {len(df)} registros")
        except Exception as e:
            print(f"❌ Error cargando clientes: {e}")
            df = pd.DataFrame()
        
        conn.close()
        return df
    
    def obtener_vendedores(self):
        """Obtiene todos los vendedores"""
        conn = sqlite3.connect(self.db_path)
        query = 'SELECT nombre_vendedor FROM vendedores ORDER BY nombre_vendedor'
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def obtener_ciudades(self):
        """Obtiene todas las ciudades únicas"""
        conn = sqlite3.connect(self.db_path)
        query = 'SELECT DISTINCT ciudad FROM clientes WHERE ciudad IS NOT NULL AND ciudad != "" ORDER BY ciudad'
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def buscar_clientes(self, texto_busqueda):
        """Busca clientes por texto"""
        conn = sqlite3.connect(self.db_path)
        
        user = self.current_user
        if not user:
            query = 'SELECT * FROM clientes WHERE 1=0'
            params = ()
        else:
            base_query = '''
                SELECT * FROM clientes 
                WHERE (nit_cliente LIKE ? OR razon_social LIKE ? OR ciudad LIKE ?)
            '''
            
            if user['rol'] in ['comercial', 'consulta']:
                vendedor = user.get('vendedor_asignado')
                if vendedor:
                    query = base_query + ' AND vendedor_asignado = ?'
                    params = (f'%{texto_busqueda}%', f'%{texto_busqueda}%', f'%{texto_busqueda}%', vendedor)
                else:
                    query = base_query + ' AND 1=0'
                    params = (f'%{texto_busqueda}%', f'%{texto_busqueda}%', f'%{texto_busqueda}%')
            else:
                query = base_query
                params = (f'%{texto_busqueda}%', f'%{texto_busqueda}%', f'%{texto_busqueda}%')
        
        query += ' ORDER BY razon_social'
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    
    def buscar_cartera(self, texto_busqueda):
        """Busca en cartera por texto FILTRADO por usuario"""
        conn = sqlite3.connect(self.db_path)
        
        user = self.current_user
        if not user:
            query = 'SELECT * FROM cartera_actual WHERE 1=0'
            params = ()
        else:
            base_query = '''
                SELECT * FROM cartera_actual 
                WHERE (nit_cliente LIKE ? OR razon_social_cliente LIKE ? OR nro_factura LIKE ?)
            '''
            
            if user['rol'] in ['comercial', 'consulta']:
                vendedor = user.get('vendedor_asignado')
                if vendedor:
                    query = base_query + ' AND nombre_vendedor = ?'
                    params = (f'%{texto_busqueda}%', f'%{texto_busqueda}%', f'%{texto_busqueda}%', vendedor)
                else:
                    query = base_query + ' AND 1=0'
                    params = (f'%{texto_busqueda}%', f'%{texto_busqueda}%', f'%{texto_busqueda}%')
            else:
                query = base_query
                params = (f'%{texto_busqueda}%', f'%{texto_busqueda}%', f'%{texto_busqueda}%')
        
        query += ' ORDER BY dias_vencidos DESC'
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    
    def filtrar_cartera(self, vendedor=None, ciudad=None, dias_vencidos_min=None, dias_vencidos_max=None):
        """Filtra cartera con múltiples criterios Y por usuario"""
        conn = sqlite3.connect(self.db_path)
        
        user = self.current_user
        if not user:
            query = 'SELECT * FROM cartera_actual WHERE 1=0'
            params = []
        else:
            query = 'SELECT * FROM cartera_actual WHERE 1=1'
            params = []
            
            if user['rol'] in ['comercial', 'consulta']:
                user_vendedor = user.get('vendedor_asignado')
                if user_vendedor:
                    query += ' AND nombre_vendedor = ?'
                    params.append(user_vendedor)
                else:
                    query += ' AND 1=0'
            
            if vendedor and vendedor != "Todos los vendedores" and user['rol'] in ['admin', 'supervisor']:
                query += ' AND nombre_vendedor = ?'
                params.append(vendedor)
            
            if ciudad and ciudad != "Todas las ciudades":
                # Necesitamos unir con la tabla clientes para filtrar por ciudad
                query = '''
                    SELECT ca.* 
                    FROM cartera_actual ca
                    LEFT JOIN clientes c ON ca.nit_cliente = c.nit_cliente
                    WHERE 1=1
                '''
                if user['rol'] in ['comercial', 'consulta']:
                    user_vendedor = user.get('vendedor_asignado')
                    if user_vendedor:
                        query += ' AND ca.nombre_vendedor = ?'
                        params.append(user_vendedor)
                    else:
                        query += ' AND 1=0'
                
                if vendedor and vendedor != "Todos los vendedores" and user['rol'] in ['admin', 'supervisor']:
                    query += ' AND ca.nombre_vendedor = ?'
                    params.append(vendedor)
                
                query += ' AND c.ciudad = ?'
                params.append(ciudad)
            
            if dias_vencidos_min is not None:
                query += ' AND dias_vencidos >= ?'
                params.append(dias_vencidos_min)
            
            if dias_vencidos_max is not None:
                query += ' AND dias_vencidos <= ?'
                params.append(dias_vencidos_max)
        
        query += ' ORDER BY dias_vencidos DESC, total_cop DESC'
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    
    def cargar_excel_cartera_con_debug(self, file_path):
        """Versión con debugging de la carga de Excel"""
        print(f"🔍 DEBUG: Iniciando carga de Excel desde: {file_path}")
        
        try:
            # Paso 1: Verificar que el archivo existe
            if not os.path.exists(file_path):
                print("❌ DEBUG: Archivo no encontrado")
                return False, "Archivo no encontrado"
            
            print(f"✅ DEBUG: Archivo encontrado, tamaño: {os.path.getsize(file_path)} bytes")
            
            # Paso 2: Intentar leer el Excel
            try:
                df = pd.read_excel(file_path)
                print(f"✅ DEBUG: Excel leído correctamente - {len(df)} filas, {len(df.columns)} columnas")
                print(f"📋 DEBUG: Columnas: {list(df.columns)}")
                
                # Mostrar primeras filas para debugging
                if len(df) > 0:
                    print("📊 DEBUG: Primeras 3 filas:")
                    print(df.head(3))
                    
            except Exception as e:
                print(f"❌ DEBUG: Error leyendo Excel: {str(e)}")
                return False, f"Error leyendo archivo Excel: {str(e)}"
            
            # Continuar con el procesamiento normal...
            return True, f"Procesados {len(df)} registros"
            
        except Exception as e:
            print(f"❌ DEBUG: Error general: {str(e)}")
            import traceback
            print(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
            return False, f"Error general: {str(e)}"

    def registrar_gestion(self, gestion_data):
        """Registra una nueva gestión con información del usuario"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        user = self.current_user
        if user:
            gestion_data_list = list(gestion_data)
            gestion_data_list[5] = user['email']  # usuario
            gestion_data = tuple(gestion_data_list)
        
        cursor.execute('''
            INSERT INTO gestiones 
            (nit_cliente, razon_social_cliente, tipo_contacto, resultado, fecha_contacto, usuario,
            observaciones, promesa_pago_fecha, promesa_pago_monto, proxima_gestion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', gestion_data)
        
        conn.commit()
        conn.close()
        self.sync_to_drive()
        
        return True
    
    def obtener_gestiones_cliente(self, nit_cliente):
        """Obtiene el historial de gestiones de un cliente"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT * FROM gestiones 
            WHERE nit_cliente = ? 
            ORDER BY fecha_contacto DESC
        '''
        df = pd.read_sql_query(query, conn, params=(nit_cliente,))
        conn.close()
        return df

    def obtener_todas_gestiones(self):
        """Obtiene TODAS las gestiones para exportar"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT * FROM gestiones 
            ORDER BY fecha_contacto DESC
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    # ============================================================
    # 🆕 FUNCIONES MODIFICADAS PARA FILTROS DINÁMICOS
    # ============================================================

    def obtener_gestiones_por_periodo(self, fecha_inicio, fecha_fin):
        """Obtiene gestiones dentro de un rango de fechas específico"""
        conn = sqlite3.connect(self.db_path)
        
        user = self.current_user
        if not user:
            return pd.DataFrame()
        
        try:
            # Condiciones según el usuario
            user_condition = ""
            user_params = []
            
            if user['rol'] in ['comercial', 'consulta']:
                user_condition = "AND usuario = ?"
                user_params = [user['email']]
            
            query = f'''
                SELECT * FROM gestiones 
                WHERE fecha_contacto BETWEEN ? AND ?
                {user_condition}
                ORDER BY fecha_contacto DESC
            '''
            
            params = [fecha_inicio, fecha_fin] + user_params
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df
            
        except Exception as e:
            conn.close()
            print(f"Error en obtener_gestiones_por_periodo: {e}")
            return pd.DataFrame()

    def obtener_progreso_gestion(self, fecha_inicio=None, fecha_fin=None):
        """Obtiene progreso de gestión para un período específico"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            user = self.current_user
            if not user:
                conn.close()
                return self._progreso_vacio()
            
            # Si no se especifican fechas, usar mes actual por defecto
            if not fecha_inicio or not fecha_fin:
                fecha_inicio = datetime.now().replace(day=1).strftime('%Y-%m-%d')
                fecha_fin = datetime.now().strftime('%Y-%m-%d')
            
            # Obtener condiciones de filtro según el usuario
            where_conditions = []
            params = []
            
            if user['rol'] in ['comercial', 'consulta']:
                vendedor = user.get('vendedor_asignado')
                if vendedor:
                    where_conditions.append('nombre_vendedor = ?')
                    params.append(vendedor)
                else:
                    # Si es comercial pero no tiene vendedor, no mostrar datos
                    conn.close()
                    return self._progreso_vacio()
            
            where_clause = ''
            if where_conditions:
                where_clause = 'WHERE ' + ' AND '.join(where_conditions)
            
            # 1. Total clientes en cartera (FILTRADO por usuario)
            cursor.execute(f'''
                SELECT COUNT(DISTINCT nit_cliente) 
                FROM cartera_actual 
                {where_clause}
            ''', params)
            total_clientes = cursor.fetchone()[0] or 0
            
            # 2. Clientes gestionados en el período (FILTRADO por usuario)
            gestion_conditions = []
            gestion_params = []
            
            if user['rol'] in ['comercial', 'consulta']:
                gestion_conditions.append('g.usuario = ?')
                gestion_params.append(user['email'])
            
            # Aplicar mismo filtro de vendedor a las gestiones
            if where_conditions:
                gestion_conditions.append('ca.nombre_vendedor = ?')
                gestion_params.append(params[0])  # El vendedor del usuario
            
            gestion_where = ''
            if gestion_conditions:
                gestion_where = 'WHERE ' + ' AND '.join(gestion_conditions)
            
            cursor.execute(f'''
                SELECT COUNT(DISTINCT g.nit_cliente) 
                FROM gestiones g
                JOIN cartera_actual ca ON g.nit_cliente = ca.nit_cliente
                {gestion_where}
                AND g.fecha_contacto BETWEEN ? AND ?
            ''', gestion_params + [fecha_inicio, fecha_fin])
            clientes_gestionados = cursor.fetchone()[0] or 0
            
            # 3. Clientes en mora (FILTRADO por usuario)
            mora_conditions = where_conditions.copy()
            mora_conditions.append('dias_vencidos > 0')
            mora_where = 'WHERE ' + ' AND '.join(mora_conditions) if mora_conditions else ''
            
            cursor.execute(f'''
                SELECT COUNT(DISTINCT nit_cliente) 
                FROM cartera_actual 
                {mora_where}
            ''', params)
            clientes_mora = cursor.fetchone()[0] or 0
            
            # 4. Clientes en mora gestionados en el período (FILTRADO por usuario)
            mora_gestion_conditions = gestion_conditions.copy()
            mora_gestion_conditions.append('ca.dias_vencidos > 0')
            mora_gestion_where = 'WHERE ' + ' AND '.join(mora_gestion_conditions) if mora_gestion_conditions else ''
            
            cursor.execute(f'''
                SELECT COUNT(DISTINCT g.nit_cliente) 
                FROM gestiones g
                JOIN cartera_actual ca ON g.nit_cliente = ca.nit_cliente
                {mora_gestion_where}
                AND g.fecha_contacto BETWEEN ? AND ?
            ''', gestion_params + [fecha_inicio, fecha_fin])
            clientes_mora_gestionados = cursor.fetchone()[0] or 0
            
            conn.close()
            
            # Calcular porcentajes
            porcentaje_general = (clientes_gestionados / total_clientes * 100) if total_clientes > 0 else 0
            porcentaje_mora = (clientes_mora_gestionados / clientes_mora * 100) if clientes_mora > 0 else 0
            
            print(f"🔍 DEBUG Progreso Gestión - Período: {fecha_inicio} a {fecha_fin}")
            print(f"   Total clientes: {total_clientes}")
            print(f"   Clientes gestionados: {clientes_gestionados}")
            print(f"   Clientes en mora: {clientes_mora}")
            print(f"   Clientes mora gestionados: {clientes_mora_gestionados}")
            print(f"   Porcentaje general: {porcentaje_general:.1f}%")
            print(f"   Porcentaje mora: {porcentaje_mora:.1f}%")
            
            return {
                'total_clientes': total_clientes,
                'clientes_gestionados': clientes_gestionados,
                'clientes_mora': clientes_mora,
                'clientes_mora_gestionados': clientes_mora_gestionados,
                'porcentaje_general': porcentaje_general,
                'porcentaje_mora': porcentaje_mora,
                'periodo': f"{fecha_inicio} a {fecha_fin}"
            }
            
        except Exception as e:
            print(f"❌ Error en obtener_progreso_gestion: {e}")
            return self._progreso_vacio()
        finally:
            try:
                conn.close()
            except:
                pass

    def obtener_estadisticas_resultados_filtrado(self, fecha_inicio=None, fecha_fin=None):
        """Obtiene estadísticas FILTRADAS por usuario actual y período específico"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        user = self.current_user
        if not user:
            return {}
        
        # Si no se especifican fechas, usar mes actual por defecto
        if not fecha_inicio or not fecha_fin:
            fecha_inicio = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            fecha_fin = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # SIEMPRE filtrar por usuario para comercial/consulta
            if user['rol'] in ['comercial', 'consulta']:
                query = '''
                    SELECT 
                        COUNT(CASE WHEN resultado LIKE '%Promesa%' OR resultado LIKE '%Pago%' THEN 1 END) as compromisos,
                        COUNT(CASE WHEN resultado LIKE '%Contacto%' OR resultado LIKE '%Mensaje%' OR resultado LIKE '%Email%' THEN 1 END) as contactos,
                        COUNT(CASE WHEN resultado LIKE '%Dificultad%' OR resultado LIKE '%Negativa%' OR resultado LIKE '%Reclamo%' THEN 1 END) as dificultades,
                        COUNT(CASE WHEN resultado LIKE '%Seguimiento%' OR resultado LIKE '%Escalación%' OR resultado LIKE '%Documentación%' THEN 1 END) as seguimientos
                    FROM gestiones 
                    WHERE fecha_contacto BETWEEN ? AND ?
                    AND usuario = ?
                '''
                cursor.execute(query, (fecha_inicio, fecha_fin, user['email']))
            else:
                query = '''
                    SELECT 
                        COUNT(CASE WHEN resultado LIKE '%Promesa%' OR resultado LIKE '%Pago%' THEN 1 END) as compromisos,
                        COUNT(CASE WHEN resultado LIKE '%Contacto%' OR resultado LIKE '%Mensaje%' OR resultado LIKE '%Email%' THEN 1 END) as contactos,
                        COUNT(CASE WHEN resultado LIKE '%Dificultad%' OR resultado LIKE '%Negativa%' OR resultado LIKE '%Reclamo%' THEN 1 END) as dificultades,
                        COUNT(CASE WHEN resultado LIKE '%Seguimiento%' OR resultado LIKE '%Escalación%' OR resultado LIKE '%Documentación%' THEN 1 END) as seguimientos
                    FROM gestiones 
                    WHERE fecha_contacto BETWEEN ? AND ?
                '''
                cursor.execute(query, (fecha_inicio, fecha_fin))
            
            resultado = cursor.fetchone()
            conn.close()
            
            if resultado:
                return {
                    'Compromisos de Pago': resultado[0] or 0,
                    'Contactos Exitosos': resultado[1] or 0,
                    'Dificultades/Rechazos': resultado[2] or 0,
                    'Seguimientos Pendientes': resultado[3] or 0
                }
            return {}
            
        except Exception as e:
            conn.close()
            print(f"Error en obtener_estadisticas_resultados_filtrado: {e}")
            return {}

    def obtener_evolucion_diaria_gestiones(self, fecha_inicio=None, fecha_fin=None):
        """Obtiene evolución diaria de gestiones para un período específico"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        user = self.current_user
        if not user:
            return []
        
        # Si no se especifican fechas, usar mes actual por defecto
        if not fecha_inicio or not fecha_fin:
            fecha_inicio = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            fecha_fin = datetime.now().strftime('%Y-%m-%d')
        
        try:
            if user['rol'] in ['comercial', 'consulta']:
                cursor.execute('''
                    SELECT 
                        DATE(fecha_contacto) as fecha,
                        COUNT(*) as total_gestiones,
                        COUNT(DISTINCT nit_cliente) as clientes_unicos
                    FROM gestiones 
                    WHERE fecha_contacto BETWEEN ? AND ?
                    AND usuario = ?
                    GROUP BY DATE(fecha_contacto)
                    ORDER BY fecha
                ''', (fecha_inicio, fecha_fin, user['email']))
            else:
                cursor.execute('''
                    SELECT 
                        DATE(fecha_contacto) as fecha,
                        COUNT(*) as total_gestiones,
                        COUNT(DISTINCT nit_cliente) as clientes_unicos
                    FROM gestiones 
                    WHERE fecha_contacto BETWEEN ? AND ?
                    GROUP BY DATE(fecha_contacto)
                    ORDER BY fecha
                ''', (fecha_inicio, fecha_fin))
            
            resultado = cursor.fetchall()
            conn.close()
            return resultado
            
        except Exception as e:
            conn.close()
            print(f"Error en obtener_evolucion_diaria_gestiones: {e}")
            return []

    def obtener_evolucion_historica_gestiones(self, fecha_inicio=None, fecha_fin=None):
        """Obtiene evolución histórica de gestiones para un período específico"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        user = self.current_user
        if not user:
            return [], 0
        
        # Si no se especifican fechas, usar últimos 12 meses por defecto
        if not fecha_inicio or not fecha_fin:
            fecha_fin = datetime.now().strftime('%Y-%m-%d')
            fecha_inicio = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        try:
            # Condiciones de filtro según usuario
            user_condition = ""
            user_params = []
            
            if user['rol'] in ['comercial', 'consulta']:
                user_condition = "AND usuario = ?"
                user_params = [user['email']]
            
            # Obtener total de gestiones por mes en el período
            query = f'''
                SELECT 
                    strftime('%Y-%m', fecha_contacto) as mes,
                    COUNT(*) as total_gestiones
                FROM gestiones 
                WHERE fecha_contacto BETWEEN ? AND ?
                {user_condition}
                GROUP BY mes 
                ORDER BY mes
            '''
            
            cursor.execute(query, [fecha_inicio, fecha_fin] + user_params)
            datos_mensuales = cursor.fetchall()
            
            # Calcular máximo histórico
            max_historico = 0
            if datos_mensuales:
                max_historico = max([item[1] for item in datos_mensuales])
            
            conn.close()
            return datos_mensuales, max_historico
            
        except Exception as e:
            conn.close()
            print(f"Error en obtener_evolucion_historica_gestiones: {e}")
            return [], 0

    # ============================================================
    # FUNCIONES AUXILIARES Y DE COMPATIBILIDAD
    # ============================================================

    def _progreso_vacio(self):
        """Retorna progreso vacío cuando no hay datos"""
        return {
            'total_clientes': 0,
            'clientes_gestionados': 0,
            'clientes_mora': 0,
            'clientes_mora_gestionados': 0,
            'porcentaje_general': 0,
            'porcentaje_mora': 0,
            'periodo': 'Sin datos'
        }

    def obtener_gestiones_mes_actual(self):
        """Función de compatibilidad - usa el nuevo sistema con mes actual por defecto"""
        fecha_inicio = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        fecha_fin = datetime.now().strftime('%Y-%m-%d')
        return self.obtener_gestiones_por_periodo(fecha_inicio, fecha_fin)

    def importar_gestiones_excel(self, file_path):
        """Importa gestiones desde archivo Excel con validaciones robustas y estadísticas detalladas"""
        try:
            # Leer archivo Excel
            df = pd.read_excel(file_path)
            total_registros_archivo = len(df)
            
            # Validar estructura básica del archivo
            columnas_requeridas = ['nit_cliente', 'razon_social_cliente', 'fecha_contacto', 'tipo_contacto', 'resultado']
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
            
            if columnas_faltantes:
                return False, f"Columnas requeridas faltantes: {', '.join(columnas_faltantes)}"
            
            # Validar datos específicos
            errores_validacion = self.validar_datos_gestiones_importacion(df)
            if errores_validacion:
                mensaje_errores = "\n".join(errores_validacion[:5])  # Mostrar máximo 5 errores
                return False, f"Errores de validación:\n{mensaje_errores}"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            gestiones_importadas = 0
            gestiones_con_errores = 0
            errores_detallados = []
            nits_procesados = set()
            total_promesas_monto = 0
            gestiones_con_promesa = 0
            
            for index, row in df.iterrows():
                try:
                    # Validar NIT existe en base de datos
                    nit_valido = self.validar_nit_existente(str(row['nit_cliente']))
                    if not nit_valido:
                        gestiones_con_errores += 1
                        errores_detallados.append(f"Fila {index + 2}: NIT {row['nit_cliente']} no existe en BD")
                        continue
                    
                    # Convertir fechas
                    fecha_contacto = self.convertir_fecha(row['fecha_contacto'])
                    if not fecha_contacto:
                        gestiones_con_errores += 1
                        errores_detallados.append(f"Fila {index + 2}: Fecha contacto inválida")
                        continue
                    
                    promesa_fecha = self.convertir_fecha(row.get('promesa_pago_fecha', None))
                    proxima_gestion = self.convertir_fecha(row.get('proxima_gestion', None))
                    
                    # Validar tipo de contacto
                    tipo_contacto_valido = self.validar_tipo_contacto(str(row['tipo_contacto']))
                    if not tipo_contacto_valido:
                        gestiones_con_errores += 1
                        errores_detallados.append(f"Fila {index + 2}: Tipo contacto '{row['tipo_contacto']}' inválido")
                        continue
                    
                    # Validar resultado
                    resultado_valido = self.validar_resultado_gestion(str(row['resultado']))
                    if not resultado_valido:
                        gestiones_con_errores += 1
                        errores_detallados.append(f"Fila {index + 2}: Resultado '{row['resultado']}' inválido")
                        continue
                    
                    # Calcular monto de promesa si existe
                    monto_promesa = 0
                    if pd.notna(row.get('promesa_pago_monto')) and row.get('promesa_pago_monto', 0) > 0:
                        monto_promesa = float(row.get('promesa_pago_monto', 0))
                        total_promesas_monto += monto_promesa
                        gestiones_con_promesa += 1
                    
                    # Insertar gestión
                    cursor.execute('''
                        INSERT INTO gestiones 
                        (nit_cliente, razon_social_cliente, tipo_contacto, resultado, fecha_contacto, usuario,
                        observaciones, promesa_pago_fecha, promesa_pago_monto, proxima_gestion)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        str(row['nit_cliente']),
                        str(row['razon_social_cliente']),
                        str(row['tipo_contacto']),
                        str(row['resultado']),
                        fecha_contacto,
                        str(row.get('usuario', 'importado_excel')),
                        str(row.get('observaciones', '')),
                        promesa_fecha,
                        monto_promesa if monto_promesa > 0 else None,
                        proxima_gestion
                    ))
                    
                    # Actualizar estadísticas
                    gestiones_importadas += 1
                    nits_procesados.add(str(row['nit_cliente']))
                    
                except Exception as e:
                    gestiones_con_errores += 1
                    errores_detallados.append(f"Fila {index + 2}: Error interno - {str(e)}")
                    continue
            
            conn.commit()
            conn.close()
            
            # Preparar mensaje de resultado CON ESTADÍSTICAS DETALLADAS
            if gestiones_importadas > 0:
                mensaje_resultado = f"✅ IMPORTACIÓN COMPLETADA EXITOSAMENTE\n\n"
                mensaje_resultado += f"📊 RESUMEN DE IMPORTACIÓN:\n"
                mensaje_resultado += f"• Registros procesados: {total_registros_archivo}\n"
                mensaje_resultado += f"• Gestiones importadas: {gestiones_importadas}\n"
                mensaje_resultado += f"• Registros con errores: {gestiones_con_errores}\n"
                mensaje_resultado += f"• Clientes únicos: {len(nits_procesados)}\n"
                mensaje_resultado += f"• Gestiones con promesa: {gestiones_con_promesa}\n"
                mensaje_resultado += f"• Monto total promesas: ${total_promesas_monto:,.0f}\n"
                
                if gestiones_con_errores > 0:
                    mensaje_resultado += f"\n⚠️ ERRORES DETECTADOS ({min(len(errores_detallados), 5)} de {len(errores_detallados)}):\n"
                    for error in errores_detallados[:5]:  # Mostrar máximo 5 errores
                        mensaje_resultado += f"• {error}\n"
                    
                    if len(errores_detallados) > 5:
                        mensaje_resultado += f"• ... y {len(errores_detallados) - 5} errores más\n"
            else:
                mensaje_resultado = f"❌ IMPORTACIÓN FALLIDA\n\n"
                mensaje_resultado += f"No se pudieron importar gestiones. Errores encontrados:\n"
                for error in errores_detallados[:10]:  # Mostrar máximo 10 errores
                    mensaje_resultado += f"• {error}\n"
            
            return gestiones_importadas > 0, mensaje_resultado
            
        except Exception as e:
            return False, f"Error al importar Excel: {str(e)}"

    def validar_datos_gestiones_importacion(self, df):
        """Valida los datos del DataFrame de importación"""
        errores = []
        
        # Validar NITs no nulos
        if df['nit_cliente'].isnull().any():
            errores.append("❌ Hay NITs vacíos en el archivo")
        
        # Validar fechas de contacto
        for index, fecha in df['fecha_contacto'].items():
            if pd.isna(fecha):
                errores.append(f"Fila {index + 2}: Fecha contacto vacía")
                continue
            
            fecha_convertida = self.convertir_fecha(fecha)
            if not fecha_convertida:
                errores.append(f"Fila {index + 2}: Formato fecha contacto inválido")
        
        # Validar tipos de contacto
        tipos_validos = ['Llamada telefónica', 'WhatsApp', 'Correo electrónico', 
                        'Visita presencial', 'Videollamada', 'Mensaje de texto']
        tipos_invalidos = df[~df['tipo_contacto'].isin(tipos_validos)]['tipo_contacto'].unique()
        if len(tipos_invalidos) > 0:
            errores.append(f"Tipos de contacto inválidos: {', '.join(tipos_invalidos)}")
        
        return errores

    def validar_nit_existente(self, nit):
        """Valida que un NIT exista en la base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM clientes WHERE nit_cliente = ?', (str(nit),))
        resultado = cursor.fetchone()[0]
        
        conn.close()
        return resultado > 0

    def validar_tipo_contacto(self, tipo_contacto):
        """Valida que el tipo de contacto sea válido"""
        tipos_validos = ['Llamada telefónica', 'WhatsApp', 'Correo electrónico', 
                        'Visita presencial', 'Videollamada', 'Mensaje de texto']
        return tipo_contacto in tipos_validos

    def validar_resultado_gestion(self, resultado):
        """Valida que el resultado de gestión sea válido"""
        # Verificar si es un resultado numérico (1-21) o texto completo
        import re
        if re.match(r'^\d+\.', resultado):
            # Es formato numérico, verificar que esté entre 1-21
            numero = int(resultado.split('.')[0])
            return 1 <= numero <= 21
        else:
            # Es texto completo, verificar que esté en la lista
            resultados_validos = [
                'Promesa de Pago Total (Fecha/Monto)',
                'Promesa de Pago Parcial (Fecha/Monto)',
                'Acuerdo de Pago Formalizado (Cuotas)',
                'Pago Efectuado / Cobro Exitoso',
                'Contacto Exitoso (Titular)',
                'Contacto con Tercero (Informó/Transmitió mensaje)',
                'Dejó Mensaje / Correo de Voz',
                'No Contesta / Ocupado',
                'Número Erróneo / Inexistente',
                'Email/Mensaje Enviado',
                'Disputa / Reclamo de Facturación',
                'Problema de Servicio (Pendiente de Resolver)',
                'Negativa de Pago (Dificultad temporal)',
                'Negativa de Pago (Rechazo definitivo)',
                'Quiebra / Insolvencia Confirmada',
                'Cliente Inactivo / Ilocalizable',
                'Necesita Escalación (A Legal/Supervisión)',
                'Enviar Documentación Solicitada (Factura/Extracto)',
                'Agendar Nueva Llamada / Cita',
                'Datos Verificados / Actualizados',
                'Gestión No Finalizada (Reintentar pronto)'
            ]
            return resultado in resultados_validos
    
    def obtener_metricas_principales(self):
        """Obtiene métricas principales del dashboard - VERSIÓN SIMPLIFICADA Y SEGURA"""
        try:
            user = self.current_user
            if not user:
                return self._metricas_vacias()
            
            # Obtener cartera completa según permisos
            cartera_df = self.obtener_cartera_actual()
            
            if cartera_df.empty:
                return self._metricas_vacias()
            
            # Calcular métricas básicas
            cartera_total = cartera_df['total_cop'].sum() if 'total_cop' in cartera_df.columns else 0
            cartera_mora = cartera_df[cartera_df['dias_vencidos'] > 0]['total_cop'].sum() if 'total_cop' in cartera_df.columns else 0
            total_clientes = cartera_df['nit_cliente'].nunique() if 'nit_cliente' in cartera_df.columns else 0
            clientes_mora = cartera_df[cartera_df['dias_vencidos'] > 0]['nit_cliente'].nunique() if 'nit_cliente' in cartera_df.columns else 0

            
            return {
                'cartera_total': cartera_total,
                'cartera_mora': cartera_mora,
                'clientes_mora': clientes_mora,
                'total_clientes': total_clientes,
                'gestiones_hoy': 0,
                'gestiones_mes': 0,
                'promesas_activas': 0,
                'clientes_gestionados_mes': 0,
                'cartera_rangos': (0, 0, 0, 0, 0)
            }
            
        except Exception as e:
            print(f"❌ Error en obtener_metricas_principales: {e}")
            return self._metricas_vacias()
    
    def _metricas_vacias(self):
        """Retorna métricas vacías cuando no hay datos"""
        return {
            'cartera_total': 0,
            'cartera_mora': 0,
            'clientes_mora': 0,
            'total_clientes': 0,
            'gestiones_hoy': 0,
            'gestiones_mes': 0,
            'promesas_activas': 0,
            'clientes_gestionados_mes': 0,
            'cartera_rangos': (0, 0, 0, 0, 0)
        }

    def _datos_graficas_vacios(self):
        """Retorna datos vacíos para gráficas cuando no hay datos"""
        return {
            'distribucion_estado': (0, 0, 0, 0, 0),
            'top_clientes_mora': [],
            'evolucion_mensual': []
        }

    def obtener_datos_graficas(self):
        """Obtiene datos para las gráficas del dashboard - VERSIÓN SIMPLIFICADA"""
        try:
            user = self.current_user
            if not user:
                return self._datos_graficas_vacios()
            
            # Obtener cartera completa según permisos
            cartera_df = self.obtener_cartera_actual()
            
            if cartera_df.empty:
                print("🔍 DEBUG - No hay datos para gráficas")
                return self._datos_graficas_vacios()
            
            # Distribución por estado
            corriente = cartera_df[cartera_df['dias_vencidos'] == 0]['total_cop'].sum() if 'total_cop' in cartera_df.columns else 0
            ven1_30 = cartera_df[(cartera_df['dias_vencidos'] >= 1) & (cartera_df['dias_vencidos'] <= 30)]['total_cop'].sum() if 'total_cop' in cartera_df.columns else 0
            ven31_60 = cartera_df[(cartera_df['dias_vencidos'] >= 31) & (cartera_df['dias_vencidos'] <= 60)]['total_cop'].sum() if 'total_cop' in cartera_df.columns else 0
            ven61_90 = cartera_df[(cartera_df['dias_vencidos'] >= 61) & (cartera_df['dias_vencidos'] <= 90)]['total_cop'].sum() if 'total_cop' in cartera_df.columns else 0
            ven90_mas = cartera_df[cartera_df['dias_vencidos'] > 90]['total_cop'].sum() if 'total_cop' in cartera_df.columns else 0
            
            distribucion_estado = (corriente, ven1_30, ven31_60, ven61_90, ven90_mas)
            
            # Top clientes con mora
            clientes_mora = cartera_df[cartera_df['dias_vencidos'] > 0]
            if not clientes_mora.empty:
                top_clientes = clientes_mora.groupby('razon_social_cliente')['total_cop'].sum().nlargest(10)
                top_clientes_mora = [(cliente, monto) for cliente, monto in top_clientes.items()]
            else:
                top_clientes_mora = []
            
            # Evolución mensual (placeholder)
            evolucion_mensual = []
            
            print(f"🔍 DEBUG - Datos gráficas: distribución={distribucion_estado}, top_clientes={len(top_clientes_mora)}")
            
            return {
                'distribucion_estado': distribucion_estado,
                'top_clientes_mora': top_clientes_mora,
                'evolucion_mensual': evolucion_mensual
            }
            
        except Exception as e:
            print(f"❌ Error en obtener_datos_graficas: {e}")
            return self._datos_graficas_vacios()

    def obtener_proyeccion_vencimientos(self):
        """Obtiene proyección de vencimientos para los próximos 3 meses"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        user = self.current_user
        if not user:
            return []
        
        try:
            where_conditions = []
            params = []
            
            if user['rol'] in ['comercial', 'consulta']:
                vendedor = user.get('vendedor_asignado')
                if vendedor:
                    where_conditions.append('nombre_vendedor = ?')
                    params.append(vendedor)
            
            where_clause = ''
            if where_conditions:
                where_clause = 'WHERE ' + ' AND '.join(where_conditions)
            
            proyeccion = []
            hoy = datetime.now()
            
            for i in range(1, 4):
                mes_proyeccion = (hoy.replace(day=1) + timedelta(days=32*i)).replace(day=1)
                mes_str = mes_proyeccion.strftime('%Y-%m')
                
                proyeccion_params = params + [mes_str]
                proyeccion_where = where_clause + (' AND ' if where_clause else 'WHERE ') + 'strftime("%Y-%m", fecha_vencimiento) = ?'
                
                cursor.execute(f'''
                    SELECT 
                        SUM(total_cop) as total_vencer,
                        SUM(CASE WHEN dias_vencidos > 0 THEN total_cop ELSE 0 END) as mora_vencer
                    FROM cartera_actual 
                    {proyeccion_where}
                ''', proyeccion_params)
                
                resultado = cursor.fetchone()
                total_vencer = resultado[0] or 0
                mora_vencer = resultado[1] or 0
                
                proyeccion.append((mes_str, total_vencer, mora_vencer))
            
            conn.close()
            return proyeccion
            
        except Exception as e:
            conn.close()
            print(f"Error en obtener_proyeccion_vencimientos: {e}")
            return []

    def obtener_datos_completos_cliente(self, nit_cliente):
        """Obtiene todos los datos de un cliente incluyendo información de contacto"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Obtener datos básicos del cliente
            query_cliente = '''
                SELECT * FROM clientes 
                WHERE nit_cliente = ?
            '''
            cliente_df = pd.read_sql_query(query_cliente, conn, params=(nit_cliente,))
            
            # Obtener cartera del cliente
            query_cartera = '''
                SELECT * FROM cartera_actual 
                WHERE nit_cliente = ?
                ORDER BY dias_vencidos DESC, total_cop DESC
            '''
            cartera_df = pd.read_sql_query(query_cartera, conn, params=(nit_cliente,))
            
            # Obtener historial de gestiones
            query_gestiones = '''
                SELECT * FROM gestiones 
                WHERE nit_cliente = ?
                ORDER BY fecha_contacto DESC
                LIMIT 10
            '''
            gestiones_df = pd.read_sql_query(query_gestiones, conn, params=(nit_cliente,))
            
            conn.close()
            
            return {
                'cliente': cliente_df.iloc[0] if not cliente_df.empty else None,
                'cartera': cartera_df,
                'gestiones': gestiones_df,
                'resumen_cartera': self.calcular_resumen_cartera_cliente(cartera_df)
            }
            
        except Exception as e:
            conn.close()
            print(f"Error obteniendo datos completos del cliente: {e}")
            return {'cliente': None, 'cartera': pd.DataFrame(), 'gestiones': pd.DataFrame(), 'resumen_cartera': {}}

    def calcular_resumen_cartera_cliente(self, cartera_df):
        """Calcula resumen de cartera para un cliente específico"""
        if cartera_df.empty:
            return {
                'total_cartera': 0,
                'cartera_corriente': 0,
                'cartera_mora': 0,
                'total_facturas': 0,
                'facturas_vencidas': 0,
                'dias_mora_max': 0
            }
        
        try:
            facturas_vencidas = cartera_df[cartera_df['dias_vencidos'] > 0]
            
            return {
                'total_cartera': cartera_df['total_cop'].sum(),
                'cartera_corriente': cartera_df[cartera_df['dias_vencidos'] == 0]['total_cop'].sum(),
                'cartera_mora': facturas_vencidas['total_cop'].sum(),
                'total_facturas': len(cartera_df),
                'facturas_vencidas': len(facturas_vencidas),
                'dias_mora_max': facturas_vencidas['dias_vencidos'].max() if not facturas_vencidas.empty else 0
            }
        except Exception as e:
            print(f"Error calculando resumen de cartera: {e}")
            return {
                'total_cartera': 0,
                'cartera_corriente': 0,
                'cartera_mora': 0,
                'total_facturas': 0,
                'facturas_vencidas': 0,
                'dias_mora_max': 0
            }

    def obtener_clientes_filtrados(self, filtro_tipo):
        """Obtiene clientes según filtros específicos Y por usuario"""
        conn = sqlite3.connect(self.db_path)
        
        user = self.current_user
        if not user:
            return pd.DataFrame()
        
        try:
            user_conditions = []
            user_params = []
            
            if user['rol'] in ['comercial', 'consulta']:
                vendedor = user.get('vendedor_asignado')
                if vendedor:
                    user_conditions.append('c.vendedor_asignado = ?')
                    user_params.append(vendedor)
            
            user_where = ''
            if user_conditions:
                user_where = 'AND ' + ' AND '.join(user_conditions)
            
            if filtro_tipo == "mora":
                query = f'''
                    SELECT DISTINCT c.* 
                    FROM clientes c
                    JOIN cartera_actual ca ON c.nit_cliente = ca.nit_cliente
                    WHERE ca.dias_vencidos > 0 {user_where}
                    ORDER BY ca.dias_vencidos DESC
                '''
                params = user_params
            elif filtro_tipo == "sin_gestion_mes":
                query = f'''
                    SELECT DISTINCT c.* 
                    FROM clientes c
                    JOIN cartera_actual ca ON c.nit_cliente = ca.nit_cliente
                    WHERE c.nit_cliente NOT IN (
                        SELECT DISTINCT nit_cliente 
                        FROM gestiones 
                        WHERE strftime("%Y-%m", fecha_contacto) = strftime("%Y-%m", "now")
                    ) {user_where}
                    ORDER BY ca.dias_vencidos DESC
                '''
                params = user_params
            elif filtro_tipo == "con_gestion_mes":
                query = f'''
                    SELECT DISTINCT c.* 
                    FROM clientes c
                    WHERE c.nit_cliente IN (
                        SELECT DISTINCT nit_cliente 
                        FROM gestiones 
                        WHERE strftime("%Y-%m", fecha_contacto) = strftime("%Y-%m", "now")
                    ) {user_where}
                    ORDER BY c.razon_social
                '''
                params = user_params
            else:
                query = f'SELECT * FROM clientes WHERE 1=1 {user_where.replace("AND", "WHERE") if user_where else ""} ORDER BY razon_social'
                params = user_params
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df
            
        except Exception as e:
            conn.close()
            print(f"Error en obtener_clientes_filtrados: {e}")
            return pd.DataFrame()

    # ============================================================
    # FUNCIONES DE HISTORIAL (EXISTENTES - SIN CAMBIOS)
    # ============================================================

    def cargar_historial_completo(self, ruta_base="CARTERA DIARIA"):
        """Carga todos los archivos Excel históricos usando solo columnas básicas"""
        try:
            import os
            import glob
            from datetime import datetime
            
            # Verificar que existe la carpeta base
            if not os.path.exists(ruta_base):
                return False, f"No se encuentra la carpeta: {ruta_base}"
            
            archivos_procesados = 0
            errores = 0
            resultados = []
            
            # Escanear estructura de carpetas: Año → Mes → Archivos
            for año_dir in os.listdir(ruta_base):
                ruta_año = os.path.join(ruta_base, año_dir)
                
                # Verificar que es un directorio de año (2025, 2026, etc.)
                if not os.path.isdir(ruta_año) or not año_dir.isdigit():
                    continue
                    
                año = int(año_dir)
                print(f"📅 Procesando año: {año}")
                
                # Procesar cada mes en el año
                for mes_dir in os.listdir(ruta_año):
                    ruta_mes = os.path.join(ruta_año, mes_dir)
                    
                    if not os.path.isdir(ruta_mes):
                        continue
                    
                    # Buscar archivos Excel en la carpeta del mes
                    patron_archivos = os.path.join(ruta_mes, "CARTERA *.xlsx")
                    archivos_mes = glob.glob(patron_archivos)
                    
                    for archivo_path in archivos_mes:
                        try:
                            # Extraer fecha del nombre del archivo
                            nombre_archivo = os.path.basename(archivo_path)
                            # Formato: "CARTERA 01-10.xlsx" → día=01, mes=10
                            partes = nombre_archivo.replace('CARTERA ', '').replace('.xlsx', '').split('-')
                            if len(partes) == 2:
                                dia = int(partes[0])
                                mes_num = int(partes[1])
                                
                                # Validar fecha
                                fecha_carga = datetime(año, mes_num, dia)
                                fecha_str = fecha_carga.strftime('%Y-%m-%d')
                                
                                # Cargar el archivo Excel
                                success, message = self.cargar_excel_historial(archivo_path, fecha_str)
                                
                                if success:
                                    archivos_procesados += 1
                                    resultados.append(f"✅ {fecha_str}: {message}")
                                else:
                                    errores += 1
                                    resultados.append(f"❌ {fecha_str}: {message}")
                                    
                        except Exception as e:
                            errores += 1
                            resultados.append(f"❌ Error procesando {archivo_path}: {str(e)}")
            
            # Resumen final
            mensaje_final = f"Procesamiento completado:\n"
            mensaje_final += f"📊 Archivos procesados: {archivos_procesados}\n"
            mensaje_final += f"❌ Errores: {errores}\n"
            
            if resultados:
                mensaje_final += f"\nÚltimos resultados:\n" + "\n".join(resultados[-10:])
            
            return archivos_procesados > 0, mensaje_final
            
        except Exception as e:
            return False, f"Error en carga masiva: {str(e)}"

    def cargar_excel_historial(self, file_path, fecha_carga):
        """Carga un archivo Excel al historial diario usando solo las primeras 10 columnas"""
        try:
            # Leer SOLO las primeras 10 columnas (por posición, sin importar nombres)
            df = pd.read_excel(file_path, usecols=range(10))
            
            # Asignar nombres estándar a las columnas (las primeras 10 siempre en el mismo orden)
            nombres_columnas = [
                'nombre_vendedor',      # Columna 0: Razón social vend. cliente
                'nit_cliente',          # Columna 1: Cliente
                'razon_social_cliente', # Columna 2: Razón social sucursal
                'centro_operacion',     # Columna 3: C.O.
                'nro_factura',          # Columna 4: Nro. docto. cruce
                'total_cop',            # Columna 5: Total COP
                'fecha_emision',        # Columna 6: Fecha docto cruce
                'fecha_vencimiento',    # Columna 7: Fecha vcto.
                'condicion_pago',       # Columna 8: Cond. pago cliente
                'dias_vencidos'         # Columna 9: Dias vencidos
            ]
            
            # Renombrar las columnas
            df.columns = nombres_columnas[:len(df.columns)]
            
            print(f"📁 Procesando: {os.path.basename(file_path)} - {len(df)} registros")
            
            # Limpiar y convertir datos
            df['total_cop'] = df['total_cop'].apply(self.limpiar_valor_monetario)
            df['dias_vencidos'] = pd.to_numeric(df['dias_vencidos'], errors='coerce').fillna(0)
            
            # Convertir fechas
            df['fecha_emision'] = df['fecha_emision'].apply(self.convertir_fecha)
            df['fecha_vencimiento'] = df['fecha_vencimiento'].apply(self.convertir_fecha)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insertar en historial_cartera_diario
            registros_insertados = 0
            for _, row in df.iterrows():
                if pd.notna(row.get('nit_cliente')):
                    try:
                        cursor.execute('''
                            INSERT OR REPLACE INTO historial_cartera_diario 
                            (fecha_carga, nit_cliente, razon_social_cliente, nombre_vendedor, 
                            centro_operacion, nro_factura, total_cop, fecha_emision, fecha_vencimiento,
                            condicion_pago, dias_vencidos)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            fecha_carga,
                            str(row.get('nit_cliente', '')),
                            str(row.get('razon_social_cliente', '')),
                            str(row.get('nombre_vendedor', '')),
                            str(row.get('centro_operacion', '')),
                            str(row.get('nro_factura', '')),
                            float(row.get('total_cop', 0)),
                            row.get('fecha_emision'),
                            row.get('fecha_vencimiento'),
                            str(row.get('condicion_pago', '')),
                            int(row.get('dias_vencidos', 0))
                        ))
                        registros_insertados += 1
                    except Exception as e:
                        print(f"⚠️ Error insertando registro: {e}")
                        continue
            
            conn.commit()
            conn.close()
            
            return True, f"{registros_insertados} registros cargados"
            
        except Exception as e:
            return False, f"Error cargando archivo {os.path.basename(file_path)}: {str(e)}"

    def verificar_historial_cargado(self):
        """Verifica cuántos registros hay en el historial"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT 
                COUNT(*) as total_registros,
                COUNT(DISTINCT fecha_carga) as dias_cargados,
                MIN(fecha_carga) as fecha_minima,
                MAX(fecha_carga) as fecha_maxima
            FROM historial_cartera_diario
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def obtener_reporte_carga_historial(self):
        """Obtiene un reporte detallado de lo que se ha cargado en el historial - VERSIÓN CORREGIDA"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
            SELECT 
                fecha_carga as "Fecha Carga",
                COUNT(*) as "Registros Cargados",
                COUNT(DISTINCT nit_cliente) as "Clientes Únicos",
                SUM(total_cop) as "Cartera Total",
                SUM(CASE WHEN dias_vencidos > 0 THEN total_cop ELSE 0 END) as "Cartera en Mora",
                COUNT(DISTINCT nombre_vendedor) as "Vendedores"
            FROM historial_cartera_diario 
            GROUP BY fecha_carga
            ORDER BY fecha_carga DESC
            ''' 
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            # Estadísticas resumen
            total_registros = df['Registros Cargados'].sum() if not df.empty else 0
            total_dias = len(df)
            fecha_min = df['Fecha Carga'].min() if not df.empty else 'N/A'
            fecha_max = df['Fecha Carga'].max() if not df.empty else 'N/A'
            
            return {
                'detalle': df,
                'resumen': {
                    'total_registros': total_registros,
                    'total_dias': total_dias,
                    'fecha_minima': fecha_min,
                    'fecha_maxima': fecha_max,
                    'promedio_registros': total_registros / total_dias if total_dias > 0 else 0
                }
            }
            
        except Exception as e:
            print(f"Error obteniendo reporte de carga: {e}")
            return {'detalle': pd.DataFrame(), 'resumen': {}}
        
    def cargar_historial_incremental(self, ruta_base="CARTERA DIARIA"):
        """Carga solo los archivos que no están en el historial"""
        try:
            import glob
            from datetime import datetime
            
            # Obtener fechas ya cargadas
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT fecha_carga FROM historial_cartera_diario ORDER BY fecha_carga')
            fechas_cargadas = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            print(f"📅 Fechas ya cargadas: {len(fechas_cargadas)}")
            
            archivos_nuevos = 0
            errores = 0
            resultados = []
            
            # Escanear estructura de carpetas
            for año_dir in os.listdir(ruta_base):
                ruta_año = os.path.join(ruta_base, año_dir)
                
                if not os.path.isdir(ruta_año) or not año_dir.isdigit():
                    continue
                    
                año = int(año_dir)
                print(f"🔍 Escaneando año: {año}")
                
                # Procesar cada mes en el año
                for mes_dir in os.listdir(ruta_año):
                    ruta_mes = os.path.join(ruta_año, mes_dir)
                    
                    if not os.path.isdir(ruta_mes):
                        continue
                    
                    # Buscar archivos Excel en la carpeta del mes
                    patron_archivos = os.path.join(ruta_mes, "CARTERA *.xlsx")
                    archivos_mes = glob.glob(patron_archivos)
                    
                    for archivo_path in archivos_mes:
                        try:
                            # Extraer fecha del nombre del archivo
                            nombre_archivo = os.path.basename(archivo_path)
                            partes = nombre_archivo.replace('CARTERA ', '').replace('.xlsx', '').split('-')
                            if len(partes) == 2:
                                dia = int(partes[0])
                                mes_num = int(partes[1])
                                
                                # Validar fecha
                                fecha_carga = datetime(año, mes_num, dia)
                                fecha_str = fecha_carga.strftime('%Y-%m-%d')
                                
                                # Verificar si ya está cargada
                                if fecha_str in fechas_cargadas:
                                    print(f"⏭️  Ya cargado: {fecha_str}")
                                    continue
                                
                                # Cargar el archivo nuevo
                                success, message = self.cargar_excel_historial(archivo_path, fecha_str)
                                
                                if success:
                                    archivos_nuevos += 1
                                    resultados.append(f"✅ {fecha_str}: {message}")
                                    fechas_cargadas.append(fecha_str)  # Agregar a la lista local
                                else:
                                    errores += 1
                                    resultados.append(f"❌ {fecha_str}: {message}")
                                    
                        except Exception as e:
                            errores += 1
                            resultados.append(f"❌ Error procesando {archivo_path}: {str(e)}")
            
            # Resumen final
            mensaje_final = f"Actualización completada:\n"
            mensaje_final += f"📥 Archivos nuevos: {archivos_nuevos}\n"
            mensaje_final += f"❌ Errores: {errores}\n"
            
            if resultados:
                mensaje_final += f"\nResultados:\n" + "\n".join(resultados[-10:])
            
            return archivos_nuevos > 0, mensaje_final
            
        except Exception as e:
            return False, f"Error en carga incremental: {str(e)}"

    # ============================================================
    # MÉTODOS DE USUARIOS - PARA COMPATIBILIDAD CON app.py
    # ============================================================

    def autenticar_usuario(self, email, password, ip_address="", user_agent=""):
        """Método de compatibilidad - delega a UserManager"""
        try:
            from auth import UserManager  # Import DENTRO de la función
            user_manager = UserManager(self.db_path)
            return user_manager.autenticar_usuario(email, password, ip_address, user_agent)
        except Exception as e:
            print(f"❌ Error en autenticar_usuario: {e}")
            return False, f"Error de autenticación: {str(e)}", None

    def obtener_usuarios(self):
        """Obtiene todos los usuarios"""
        try:
            from auth import UserManager  # Import DENTRO de la función
            user_manager = UserManager(self.db_path)
            return user_manager.obtener_usuarios()
        except Exception as e:
            print(f"Error obteniendo usuarios: {e}")
            return pd.DataFrame()

    def crear_usuario(self, email, nombre_completo, rol, vendedor_asignado=None, activo=True):
        """Crea un nuevo usuario"""
        try:
            from auth import UserManager  # Import DENTRO de la función
            user_manager = UserManager(self.db_path)
            return user_manager.crear_usuario(email, nombre_completo, rol, vendedor_asignado, activo)
        except Exception as e:
            return False, f"Error creando usuario: {str(e)}"

    def actualizar_usuario(self, user_id, datos):
        """Actualiza un usuario"""
        try:
            from auth import UserManager  # Import DENTRO de la función
            user_manager = UserManager(self.db_path)
            return user_manager.actualizar_usuario(user_id, datos)
        except Exception as e:
            return False, f"Error actualizando usuario: {str(e)}"

    def cambiar_password(self, user_id, nueva_password):
        """Cambia contraseña de usuario"""
        try:
            from auth import UserManager  # Import DENTRO de la función
            user_manager = UserManager(self.db_path)
            return user_manager.cambiar_password(user_id, nueva_password)
        except Exception as e:
            return False, f"Error cambiando contraseña: {str(e)}"

    def eliminar_usuario(self, user_id):
        """Elimina un usuario"""
        try:
            from auth import UserManager  # Import DENTRO de la función
            user_manager = UserManager(self.db_path)
            return user_manager.eliminar_usuario(user_id)
        except Exception as e:
            return False, f"Error eliminando usuario: {str(e)}"

    def obtener_estadisticas_sistema(self):
        """Obtiene estadísticas del sistema"""
        try:
            from auth import UserManager  # Import DENTRO de la función
            user_manager = UserManager(self.db_path)
            return user_manager.obtener_estadisticas_sistema()
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return {
                'total_usuarios': 0,
                'usuarios_activos': 0,
                'logins_hoy': 0,
                'sesiones_activas': 1
            }

    def obtener_vendedores(self):
        """Obtiene todos los vendedores"""
        try:
            from auth import UserManager  # Import DENTRO de la función
            user_manager = UserManager(self.db_path)
            return user_manager.obtener_vendedores()
        except Exception as e:
            print(f"Error obteniendo vendedores: {e}")
            return pd.DataFrame()