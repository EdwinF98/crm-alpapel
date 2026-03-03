"""
Módulo de Gestión de Base de Datos - CRM Cartera ALPAPEL SAS
Controla todas las operaciones de persistencia de datos del sistema
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
import traceback
import streamlit as st


class DatabaseManager:
    """Gestor principal de base de datos SQLite para el sistema CRM"""

    def __init__(self):
        """Inicializa el gestor de base de datos y establece conexión"""
        self.db_path = self._get_database_path()
        self.init_db()  # Llama al método unificado de inicialización
        self.current_user = None

    def _get_database_path(self):
        """Define la ruta de la base de datos en la misma carpeta del proyecto"""
        # Obtiene la dirección de la carpeta donde está este archivo (database.py)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Une la carpeta con el nombre del archivo
        db_path = os.path.join(base_dir, "cartera_crm.db")
        
        print(f"📍 Base de datos ubicada en: {db_path}")
        return db_path

    def set_current_user(self, user_data):
        """Establece usuario actual para filtros de seguridad"""
        self.current_user = user_data

    def init_db(self):
        """Crea todas las tablas necesarias del sistema (unificado)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # --- Tabla de usuarios (con columnas de seguridad) ---
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        nombre_completo TEXT NOT NULL,
                        rol TEXT NOT NULL,
                        vendedor_asignado TEXT,
                        activo INTEGER DEFAULT 1,
                        intentos_fallidos INTEGER DEFAULT 0,
                        bloqueado_hasta DATETIME,
                        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                        ultimo_login DATETIME,
                        email_verificado INTEGER DEFAULT 0
                    )
                ''')

                # --- Tabla de control de cargas ---
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS control_cargas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fecha_actualizacion TEXT NOT NULL,
                        usuario_ejecutor TEXT NOT NULL,
                        nombre_archivo TEXT
                    )
                ''')

                # --- Tabla de vendedores ---
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS vendedores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre_vendedor TEXT UNIQUE
                    )
                ''')

                # --- Tabla de clientes ---
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS clientes (
                        nit_cliente TEXT PRIMARY KEY,
                        razon_social TEXT NOT NULL,
                        ciudad TEXT,
                        direccion TEXT,
                        telefono TEXT,
                        celular TEXT,
                        email TEXT,
                        vendedor_asignado TEXT,
                        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                        estado_cupo TEXT DEFAULT 'activo',
                        fecha_registro DATE DEFAULT CURRENT_DATE
                    )
                ''')

                # --- Tabla de cartera actual ---
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
                        fecha_carga DATE DEFAULT CURRENT_DATE,
                        FOREIGN KEY (nit_cliente) REFERENCES clientes (nit_cliente)
                    )
                ''')

                # --- Tabla de gestiones ---
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
                        fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (nit_cliente) REFERENCES clientes (nit_cliente)
                    )
                ''')

                # --- Tabla de historial de cartera (general) ---
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

                # --- Tabla de historial de cartera diario ---
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

                # --- Tabla de auditoría de login (opcional) ---
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS auditoria_login (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        usuario_id INTEGER,
                        email TEXT,
                        ip_address TEXT,
                        user_agent TEXT,
                        exito INTEGER,
                        fecha_login DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                conn.commit()
                print("✅ Tablas creadas/verificadas correctamente.")

        except Exception as e:
            print(f"❌ Error inicializando la base de datos: {e}")
            traceback.print_exc()

    # ------------------------------------------------------------
    # Métodos de utilidad (conversiones, fechas, etc.)
    # ------------------------------------------------------------

    def convertir_fecha(self, fecha):
        """Convierte diferentes formatos de fecha a estándar YYYY-MM-DD"""
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
        """Limpia y convierte valores monetarios a formato numérico"""
        if pd.isna(valor):
            return 0.0
        if isinstance(valor, str):
            valor = valor.replace('$', '').replace('.', '').replace(',', '.').replace(' ', '').strip()
            try:
                return float(valor)
            except:
                return 0.0
        return float(valor)

    def obtener_rango_fechas_por_periodo(self, periodo_seleccionado, fecha_inicio_personalizada=None, fecha_fin_personalizada=None):
        """Calcula rango de fechas según período seleccionado"""
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
            inicio = datetime.strptime(fecha_inicio_personalizada, '%Y-%m-%d')
            fin = datetime.strptime(fecha_fin_personalizada, '%Y-%m-%d')
        else:
            inicio = hoy.replace(day=1)
            fin = hoy

        return inicio.strftime('%Y-%m-%d'), fin.strftime('%Y-%m-%d')

    # ------------------------------------------------------------
    # Métodos de gestión de cargas y actualizaciones
    # ------------------------------------------------------------

    def registrar_actualizacion_cartera(self, email_usuario, nombre_archivo="Cartera_Principal.xlsx"):
        """Registra el momento exacto en que se cargaron los datos"""
        ahora = datetime.now().strftime("%d/%m/%Y %I:%M %p")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO control_cargas (fecha_actualizacion, usuario_ejecutor, nombre_archivo) VALUES (?, ?, ?)",
                    (ahora, email_usuario, nombre_archivo)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"Error al registrar carga: {e}")
            return False

    def obtener_ultima_actualizacion(self):
        """Devuelve la fecha de la última carga registrada"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT fecha_actualizacion FROM control_cargas ORDER BY id DESC LIMIT 1")
                resultado = cursor.fetchone()
                return resultado[0] if resultado else "Sin registros de carga"
        except Exception as e:
            return "Error al consultar fecha"

    # ------------------------------------------------------------
    # Métodos de carga de Excel (cartera principal)
    # ------------------------------------------------------------

    def cargar_excel_cartera(self, file_path):
        """Carga datos de archivo Excel a la base de datos (cartera actual)"""
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

            # Insertar vendedores
            if 'nombre_vendedor' in df.columns:
                vendedores_unicos = df['nombre_vendedor'].dropna().unique()
                for vendedor in vendedores_unicos:
                    if vendedor and str(vendedor).strip() != '':
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT OR IGNORE INTO vendedores (nombre_vendedor)
                            VALUES (?)
                        ''', (str(vendedor).strip(),))

            # Insertar clientes
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

            # Limpiar cartera actual e insertar nueva
            cursor = conn.cursor()
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

            # Guardar en historial
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

            return True, f"Cartera cargada exitosamente. {len(df)} registros procesados."

        except Exception as e:
            return False, f"Error al cargar Excel: {str(e)}"

    # ------------------------------------------------------------
    # Métodos de obtención de datos (con filtros de seguridad)
    # ------------------------------------------------------------

    def obtener_cartera_actual(self):
        """Obtiene cartera actual con filtros de seguridad por usuario"""
        conn = sqlite3.connect(self.db_path)

        user = self.current_user

        if not user:
            query = 'SELECT * FROM cartera_actual WHERE 1=0'  # No mostrar nada si no hay usuario
            params = ()
        else:
            if user['rol'] in ['admin', 'supervisor']:
                query = 'SELECT * FROM cartera_actual'
                params = ()
            elif user['rol'] in ['comercial', 'consulta']:
                vendedor_asignado = user.get('vendedor_asignado')

                if vendedor_asignado:
                    query = '''
                        SELECT * FROM cartera_actual 
                        WHERE UPPER(nombre_vendedor) LIKE ? 
                        OR UPPER(nombre_vendedor) LIKE ?
                        OR nombre_vendedor = ?
                    '''
                    vendedor_upper = vendedor_asignado.upper()
                    busqueda1 = f"%{vendedor_upper}%"
                    partes = vendedor_upper.split()
                    if len(partes) >= 2:
                        busqueda2 = f"%{partes[-1]}%"
                    else:
                        busqueda2 = f"%{vendedor_upper}%"
                    busqueda3 = vendedor_asignado
                    params = (busqueda1, busqueda2, busqueda3)
                else:
                    query = 'SELECT * FROM cartera_actual WHERE 1=0'
                    params = ()
            else:
                query = 'SELECT * FROM cartera_actual WHERE 1=0'
                params = ()

        query += ' ORDER BY dias_vencidos DESC, total_cop DESC'

        try:
            df = pd.read_sql_query(query, conn, params=params)
        except Exception as e:
            print(f"Error en obtener_cartera_actual: {e}")
            df = pd.DataFrame()

        conn.close()
        return df

    def obtener_clientes(self):
        """Obtiene todos los clientes con filtros de seguridad por usuario"""
        conn = sqlite3.connect(self.db_path)

        user = self.current_user
        if not user:
            query = 'SELECT * FROM clientes WHERE 1=0'
            params = ()
        else:
            if user['rol'] in ['admin', 'supervisor']:
                query = 'SELECT * FROM clientes'
                params = ()
            elif user['rol'] in ['comercial', 'consulta']:
                vendedor = user.get('vendedor_asignado')
                if vendedor:
                    query = 'SELECT * FROM clientes WHERE vendedor_asignado = ?'
                    params = (vendedor,)
                else:
                    query = 'SELECT * FROM clientes WHERE 1=0'
                    params = ()
            else:
                query = 'SELECT * FROM clientes WHERE 1=0'
                params = ()

        query += ' ORDER BY razon_social'

        try:
            df = pd.read_sql_query(query, conn, params=params)
        except Exception as e:
            print(f"Error cargando clientes: {e}")
            df = pd.DataFrame()

        conn.close()
        return df

    def obtener_vendedores(self):
        """Obtiene todos los vendedores registrados"""
        conn = sqlite3.connect(self.db_path)
        query = 'SELECT nombre_vendedor FROM vendedores ORDER BY nombre_vendedor'
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def obtener_vendedores_asignados(self):
        """Obtiene todos los vendedores asignados de la tabla vendedores y clientes"""
        try:
            conn = sqlite3.connect(self.db_path)

            query = '''
                SELECT DISTINCT nombre_vendedor 
                FROM (
                    SELECT nombre_vendedor FROM vendedores 
                    WHERE nombre_vendedor IS NOT NULL AND nombre_vendedor != ''
                    UNION
                    SELECT DISTINCT nombre_vendedor FROM cartera_actual 
                    WHERE nombre_vendedor IS NOT NULL AND nombre_vendedor != ''
                    UNION
                    SELECT DISTINCT vendedor_asignado FROM clientes 
                    WHERE vendedor_asignado IS NOT NULL AND vendedor_asignado != ''
                    UNION
                    SELECT DISTINCT vendedor_asignado FROM usuarios 
                    WHERE vendedor_asignado IS NOT NULL AND vendedor_asignado != ''
                )
                ORDER BY nombre_vendedor
            '''

            df = pd.read_sql_query(query, conn)
            conn.close()

            vendedores = ["Todos los vendedores"]
            if not df.empty:
                vendedores.extend(df['nombre_vendedor'].dropna().unique().tolist())

            return vendedores

        except Exception as e:
            print(f"Error obteniendo vendedores asignados: {e}")
            return ["Todos los vendedores"]

    def obtener_ciudades(self):
        """Obtiene todas las ciudades únicas de clientes"""
        conn = sqlite3.connect(self.db_path)
        query = 'SELECT DISTINCT ciudad FROM clientes WHERE ciudad IS NOT NULL AND ciudad != "" ORDER BY ciudad'
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    # ------------------------------------------------------------
    # Métodos de búsqueda y filtrado
    # ------------------------------------------------------------

    def buscar_clientes(self, texto_busqueda):
        """Busca clientes por texto con filtros de seguridad"""
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
        """Busca en cartera por texto con filtros de seguridad"""
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
        """Filtra cartera con múltiples criterios y seguridad por usuario"""
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
                # Necesitamos un JOIN con clientes para filtrar por ciudad
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

    # ------------------------------------------------------------
    # Métodos de gestión de gestiones
    # ------------------------------------------------------------

    def registrar_gestion(self, gestion_data):
        """Registra una nueva gestión con información del usuario"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        user = self.current_user
        if user:
            gestion_data_list = list(gestion_data)
            gestion_data_list[5] = user['email']
            gestion_data = tuple(gestion_data_list)

        cursor.execute('''
            INSERT INTO gestiones 
            (nit_cliente, razon_social_cliente, tipo_contacto, resultado, fecha_contacto, usuario,
             observaciones, promesa_pago_fecha, promesa_pago_monto, proxima_gestion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', gestion_data)

        conn.commit()
        conn.close()
        return True

    def obtener_gestiones_cliente(self, nit_cliente):
        """Obtiene historial de gestiones de un cliente específico"""
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
        """Obtiene todas las gestiones para exportación"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT * FROM gestiones 
            ORDER BY fecha_contacto DESC
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def obtener_gestiones_por_periodo(self, fecha_inicio, fecha_fin, usuario_email=None,
                                      vendedor_asignado=None, resultado_filtro=None):
        """Obtiene gestiones con filtros múltiples: usuario, vendedor asignado y resultado"""
        conn = sqlite3.connect(self.db_path)

        user = self.current_user
        if not user:
            return pd.DataFrame()

        try:
            where_conditions = ["g.fecha_contacto BETWEEN ? AND ?"]
            params = [fecha_inicio, fecha_fin]

            join_clause = ""
            if vendedor_asignado and vendedor_asignado != "Todos los vendedores":
                join_clause = "JOIN cartera_actual ca ON g.nit_cliente = ca.nit_cliente"
                where_conditions.append("ca.nombre_vendedor = ?")
                params.append(vendedor_asignado)

            if usuario_email and usuario_email != "Todos los vendedores":
                where_conditions.append("g.usuario = ?")
                params.append(usuario_email)

            if resultado_filtro and resultado_filtro != "Todos los resultados":
                if resultado_filtro == "Compromisos de Pago":
                    where_conditions.append("(g.resultado LIKE '%Promesa%' OR g.resultado LIKE '%Pago%')")
                elif resultado_filtro == "Contactos Exitosos":
                    where_conditions.append("(g.resultado LIKE '%Contacto%' OR g.resultado LIKE '%Mensaje%' OR g.resultado LIKE '%Email%')")
                elif resultado_filtro == "Dificultades/Rechazos":
                    where_conditions.append("(g.resultado LIKE '%Dificultad%' OR g.resultado LIKE '%Negativa%' OR g.resultado LIKE '%Reclamo%')")
                elif resultado_filtro == "Seguimientos Pendientes":
                    where_conditions.append("(g.resultado LIKE '%Seguimiento%' OR g.resultado LIKE '%Escalación%' OR g.resultado LIKE '%Documentación%')")

            where_clause = " WHERE " + " AND ".join(where_conditions)

            query = f'''
                SELECT g.* 
                FROM gestiones g
                {join_clause}
                {where_clause}
                ORDER BY g.fecha_contacto DESC
            '''

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df

        except Exception as e:
            conn.close()
            print(f"Error obteniendo gestiones con filtros: {e}")
            return pd.DataFrame()

    def obtener_gestiones_por_vendedor(self, vendedor_email, fecha_inicio=None, fecha_fin=None):
        """Obtiene todas las gestiones de un vendedor específico"""
        conn = sqlite3.connect(self.db_path)

        try:
            where_conditions = ["usuario = ?"]
            params = [vendedor_email]

            if fecha_inicio and fecha_fin:
                where_conditions.append("fecha_contacto BETWEEN ? AND ?")
                params.extend([fecha_inicio, fecha_fin])

            where_clause = " WHERE " + " AND ".join(where_conditions)

            query = f'''
                SELECT * FROM gestiones 
                {where_clause}
                ORDER BY fecha_contacto DESC
            '''

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df

        except Exception as e:
            conn.close()
            print(f"Error obteniendo gestiones por vendedor: {e}")
            return pd.DataFrame()

    # ------------------------------------------------------------
    # Métodos de progreso y estadísticas
    # ------------------------------------------------------------

    def obtener_progreso_gestion(self, fecha_inicio=None, fecha_fin=None,
                                  usuario_email=None, vendedor_asignado=None):
        """Obtiene progreso de gestión con filtros por usuario y vendedor asignado"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            user = self.current_user
            if not user:
                conn.close()
                return self._progreso_vacio()

            if not fecha_inicio or not fecha_fin:
                fecha_inicio = datetime.now().replace(day=1).strftime('%Y-%m-%d')
                fecha_fin = datetime.now().strftime('%Y-%m-%d')

            # Condiciones para cartera_actual
            where_conditions = []
            params = []

            if vendedor_asignado and vendedor_asignado != "Todos los vendedores":
                where_conditions.append('nombre_vendedor = ?')
                params.append(vendedor_asignado)
            elif user['rol'] in ['comercial', 'consulta']:
                vendedor_usuario = user.get('vendedor_asignado')
                if vendedor_usuario:
                    where_conditions.append('nombre_vendedor = ?')
                    params.append(vendedor_usuario)
                else:
                    conn.close()
                    return self._progreso_vacio()

            where_clause = ''
            if where_conditions:
                where_clause = 'WHERE ' + ' AND '.join(where_conditions)

            # Total clientes en cartera
            cursor.execute(f'''
                SELECT COUNT(DISTINCT nit_cliente) 
                FROM cartera_actual 
                {where_clause}
            ''', params)
            total_clientes = cursor.fetchone()[0] or 0

            # Condiciones para gestiones
            gestion_conditions = []
            gestion_params = []

            if usuario_email and usuario_email != "Todos los vendedores":
                gestion_conditions.append('g.usuario = ?')
                gestion_params.append(usuario_email)
            elif user['rol'] in ['comercial', 'consulta']:
                gestion_conditions.append('g.usuario = ?')
                gestion_params.append(user['email'])

            if where_conditions:
                gestion_conditions.append('ca.nombre_vendedor = ?')
                gestion_params.append(params[0])

            gestion_where = ''
            if gestion_conditions:
                gestion_where = 'WHERE ' + ' AND '.join(gestion_conditions)

            # Clientes gestionados en el período
            cursor.execute(f'''
                SELECT COUNT(DISTINCT g.nit_cliente) 
                FROM gestiones g
                JOIN cartera_actual ca ON g.nit_cliente = ca.nit_cliente
                {gestion_where}
                AND g.fecha_contacto BETWEEN ? AND ?
            ''', gestion_params + [fecha_inicio, fecha_fin])
            clientes_gestionados = cursor.fetchone()[0] or 0

            # Clientes en mora
            mora_conditions = where_conditions.copy()
            mora_conditions.append('dias_vencidos > 0')
            mora_where = 'WHERE ' + ' AND '.join(mora_conditions) if mora_conditions else ''

            cursor.execute(f'''
                SELECT COUNT(DISTINCT nit_cliente) 
                FROM cartera_actual 
                {mora_where}
            ''', params)
            clientes_mora = cursor.fetchone()[0] or 0

            # Clientes en mora gestionados
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

            porcentaje_general = (clientes_gestionados / total_clientes * 100) if total_clientes > 0 else 0
            porcentaje_mora = (clientes_mora_gestionados / clientes_mora * 100) if clientes_mora > 0 else 0

            return {
                'total_clientes': total_clientes,
                'clientes_gestionados': clientes_gestionados,
                'clientes_mora': clientes_mora,
                'clientes_mora_gestionados': clientes_mora_gestionados,
                'porcentaje_general': porcentaje_general,
                'porcentaje_mora': porcentaje_mora,
                'periodo': f"{fecha_inicio} a {fecha_fin}",
                'usuario_filtrado': usuario_email if usuario_email else "Todos",
                'vendedor_asignado_filtrado': vendedor_asignado if vendedor_asignado else "Todos"
            }

        except Exception as e:
            print(f"Error obteniendo progreso de gestión: {e}")
            return self._progreso_vacio()
        finally:
            try:
                conn.close()
            except:
                pass

    def _progreso_vacio(self):
        return {
            'total_clientes': 0,
            'clientes_gestionados': 0,
            'clientes_mora': 0,
            'clientes_mora_gestionados': 0,
            'porcentaje_general': 0,
            'porcentaje_mora': 0,
            'periodo': 'Sin datos'
        }

    def obtener_estadisticas_resultados_filtrado(self, fecha_inicio=None, fecha_fin=None,
                                                 usuario_email=None, vendedor_asignado=None,
                                                 resultado_especifico=None):
        """Obtiene estadísticas con filtros múltiples"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        user = self.current_user
        if not user:
            return {}

        if not fecha_inicio or not fecha_fin:
            fecha_inicio = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            fecha_fin = datetime.now().strftime('%Y-%m-%d')

        try:
            where_conditions = ["g.fecha_contacto BETWEEN ? AND ?"]
            params = [fecha_inicio, fecha_fin]

            join_clause = ""
            if vendedor_asignado and vendedor_asignado != "Todos los vendedores":
                join_clause = "JOIN cartera_actual ca ON g.nit_cliente = ca.nit_cliente"
                where_conditions.append("ca.nombre_vendedor = ?")
                params.append(vendedor_asignado)

            if usuario_email and usuario_email != "Todos los vendedores":
                where_conditions.append("g.usuario = ?")
                params.append(usuario_email)
            elif user['rol'] in ['comercial', 'consulta']:
                where_conditions.append("g.usuario = ?")
                params.append(user['email'])

            if resultado_especifico and resultado_especifico != "Todos los resultados":
                if resultado_especifico == "Compromisos de Pago":
                    where_conditions.append("(g.resultado LIKE '%Promesa%' OR g.resultado LIKE '%Pago%')")
                elif resultado_especifico == "Contactos Exitosos":
                    where_conditions.append("(g.resultado LIKE '%Contacto%' OR g.resultado LIKE '%Mensaje%' OR g.resultado LIKE '%Email%')")
                elif resultado_especifico == "Dificultades/Rechazos":
                    where_conditions.append("(g.resultado LIKE '%Dificultad%' OR g.resultado LIKE '%Negativa%' OR g.resultado LIKE '%Reclamo%')")
                elif resultado_especifico == "Seguimientos Pendientes":
                    where_conditions.append("(g.resultado LIKE '%Seguimiento%' OR g.resultado LIKE '%Escalación%' OR g.resultado LIKE '%Documentación%')")

            where_clause = " WHERE " + " AND ".join(where_conditions)

            query = f'''
                SELECT 
                    COUNT(CASE WHEN g.resultado LIKE '%Promesa%' OR g.resultado LIKE '%Pago%' THEN 1 END) as compromisos,
                    COUNT(CASE WHEN g.resultado LIKE '%Contacto%' OR g.resultado LIKE '%Mensaje%' OR g.resultado LIKE '%Email%' THEN 1 END) as contactos,
                    COUNT(CASE WHEN g.resultado LIKE '%Dificultad%' OR g.resultado LIKE '%Negativa%' OR g.resultado LIKE '%Reclamo%' THEN 1 END) as dificultades,
                    COUNT(CASE WHEN g.resultado LIKE '%Seguimiento%' OR g.resultado LIKE '%Escalación%' OR g.resultado LIKE '%Documentación%' THEN 1 END) as seguimientos
                FROM gestiones g
                {join_clause}
                {where_clause}
            '''

            cursor.execute(query, params)
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
            print(f"Error obteniendo estadísticas de resultados: {e}")
            return {}

    def obtener_evolucion_diaria_gestiones(self, fecha_inicio=None, fecha_fin=None,
                                            usuario_email=None, vendedor_asignado=None,
                                            resultado_filtro=None):
        """Obtiene evolución diaria con filtros múltiples"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        user = self.current_user
        if not user:
            return []

        if not fecha_inicio or not fecha_fin:
            fecha_inicio = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            fecha_fin = datetime.now().strftime('%Y-%m-%d')

        try:
            where_conditions = ["g.fecha_contacto BETWEEN ? AND ?"]
            params = [fecha_inicio, fecha_fin]

            join_clause = ""
            if vendedor_asignado and vendedor_asignado != "Todos los vendedores":
                join_clause = "JOIN cartera_actual ca ON g.nit_cliente = ca.nit_cliente"
                where_conditions.append("ca.nombre_vendedor = ?")
                params.append(vendedor_asignado)

            if usuario_email and usuario_email != "Todos los vendedores":
                where_conditions.append("g.usuario = ?")
                params.append(usuario_email)
            elif user['rol'] in ['comercial', 'consulta']:
                where_conditions.append("g.usuario = ?")
                params.append(user['email'])

            if resultado_filtro and resultado_filtro != "Todos los resultados":
                if resultado_filtro == "Compromisos de Pago":
                    where_conditions.append("(g.resultado LIKE '%Promesa%' OR g.resultado LIKE '%Pago%')")
                elif resultado_filtro == "Contactos Exitosos":
                    where_conditions.append("(g.resultado LIKE '%Contacto%' OR g.resultado LIKE '%Mensaje%' OR g.resultado LIKE '%Email%')")
                elif resultado_filtro == "Dificultades/Rechazos":
                    where_conditions.append("(g.resultado LIKE '%Dificultad%' OR g.resultado LIKE '%Negativa%' OR g.resultado LIKE '%Reclamo%')")
                elif resultado_filtro == "Seguimientos Pendientes":
                    where_conditions.append("(g.resultado LIKE '%Seguimiento%' OR g.resultado LIKE '%Escalación%' OR g.resultado LIKE '%Documentación%')")

            where_clause = " WHERE " + " AND ".join(where_conditions)

            cursor.execute(f'''
                SELECT 
                    DATE(g.fecha_contacto) as fecha,
                    COUNT(*) as total_gestiones,
                    COUNT(DISTINCT g.nit_cliente) as clientes_unicos
                FROM gestiones g
                {join_clause}
                {where_clause}
                GROUP BY DATE(g.fecha_contacto)
                ORDER BY fecha
            ''', params)

            resultado = cursor.fetchall()
            conn.close()
            return resultado

        except Exception as e:
            conn.close()
            print(f"Error obteniendo evolución diaria: {e}")
            return []

    def obtener_evolucion_historica_gestiones(self, fecha_inicio=None, fecha_fin=None,
                                              usuario_email=None, vendedor_asignado=None,
                                              resultado_filtro=None):
        """Obtiene evolución histórica con filtros múltiples"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        user = self.current_user
        if not user:
            return [], 0

        if not fecha_inicio or not fecha_fin:
            fecha_fin = datetime.now().strftime('%Y-%m-%d')
            fecha_inicio = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        try:
            where_conditions = ["g.fecha_contacto BETWEEN ? AND ?"]
            params = [fecha_inicio, fecha_fin]

            join_clause = ""
            if vendedor_asignado and vendedor_asignado != "Todos los vendedores":
                join_clause = "JOIN cartera_actual ca ON g.nit_cliente = ca.nit_cliente"
                where_conditions.append("ca.nombre_vendedor = ?")
                params.append(vendedor_asignado)

            if usuario_email and usuario_email != "Todos los vendedores":
                where_conditions.append("g.usuario = ?")
                params.append(usuario_email)
            elif user['rol'] in ['comercial', 'consulta']:
                where_conditions.append("g.usuario = ?")
                params.append(user['email'])

            if resultado_filtro and resultado_filtro != "Todos los resultados":
                if resultado_filtro == "Compromisos de Pago":
                    where_conditions.append("(g.resultado LIKE '%Promesa%' OR g.resultado LIKE '%Pago%')")
                elif resultado_filtro == "Contactos Exitosos":
                    where_conditions.append("(g.resultado LIKE '%Contacto%' OR g.resultado LIKE '%Mensaje%' OR g.resultado LIKE '%Email%')")
                elif resultado_filtro == "Dificultades/Rechazos":
                    where_conditions.append("(g.resultado LIKE '%Dificultad%' OR g.resultado LIKE '%Negativa%' OR g.resultado LIKE '%Reclamo%')")
                elif resultado_filtro == "Seguimientos Pendientes":
                    where_conditions.append("(g.resultado LIKE '%Seguimiento%' OR g.resultado LIKE '%Escalación%' OR g.resultado LIKE '%Documentación%')")

            where_clause = " WHERE " + " AND ".join(where_conditions)

            query = f'''
                SELECT 
                    strftime('%Y-%m', g.fecha_contacto) as mes,
                    COUNT(*) as total_gestiones
                FROM gestiones g
                {join_clause}
                {where_clause}
                GROUP BY mes 
                ORDER BY mes
            '''

            cursor.execute(query, params)
            datos_mensuales = cursor.fetchall()

            max_historico = 0
            if datos_mensuales:
                max_historico = max([item[1] for item in datos_mensuales])

            conn.close()
            return datos_mensuales, max_historico

        except Exception as e:
            conn.close()
            print(f"Error obteniendo evolución histórica: {e}")
            return [], 0

    # ------------------------------------------------------------
    # Métodos de importación/exportación
    # ------------------------------------------------------------

    def importar_gestiones_excel(self, file_path):
        """Importa gestiones desde archivo Excel con validaciones robustas"""
        try:
            df = pd.read_excel(file_path)
            total_registros_archivo = len(df)

            columnas_requeridas = ['nit_cliente', 'razon_social_cliente', 'fecha_contacto', 'tipo_contacto', 'resultado']
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]

            if columnas_faltantes:
                return False, f"Columnas requeridas faltantes: {', '.join(columnas_faltantes)}"

            errores_validacion = self.validar_datos_gestiones_importacion(df)
            if errores_validacion:
                mensaje_errores = "\n".join(errores_validacion[:5])
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
                    nit_valido = self.validar_nit_existente(str(row['nit_cliente']))
                    if not nit_valido:
                        gestiones_con_errores += 1
                        errores_detallados.append(f"Fila {index + 2}: NIT {row['nit_cliente']} no existe en BD")
                        continue

                    fecha_contacto = self.convertir_fecha(row['fecha_contacto'])
                    if not fecha_contacto:
                        gestiones_con_errores += 1
                        errores_detallados.append(f"Fila {index + 2}: Fecha contacto inválida")
                        continue

                    promesa_fecha = self.convertir_fecha(row.get('promesa_pago_fecha', None))
                    proxima_gestion = self.convertir_fecha(row.get('proxima_gestion', None))

                    tipo_contacto_valido = self.validar_tipo_contacto(str(row['tipo_contacto']))
                    if not tipo_contacto_valido:
                        gestiones_con_errores += 1
                        errores_detallados.append(f"Fila {index + 2}: Tipo contacto '{row['tipo_contacto']}' inválido")
                        continue

                    resultado_valido = self.validar_resultado_gestion(str(row['resultado']))
                    if not resultado_valido:
                        gestiones_con_errores += 1
                        errores_detallados.append(f"Fila {index + 2}: Resultado '{row['resultado']}' inválido")
                        continue

                    monto_promesa = 0
                    if pd.notna(row.get('promesa_pago_monto')) and row.get('promesa_pago_monto', 0) > 0:
                        monto_promesa = float(row.get('promesa_pago_monto', 0))
                        total_promesas_monto += monto_promesa
                        gestiones_con_promesa += 1

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

                    gestiones_importadas += 1
                    nits_procesados.add(str(row['nit_cliente']))

                except Exception as e:
                    gestiones_con_errores += 1
                    errores_detallados.append(f"Fila {index + 2}: Error interno - {str(e)}")
                    continue

            conn.commit()
            conn.close()

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
                    for error in errores_detallados[:5]:
                        mensaje_resultado += f"• {error}\n"
                    if len(errores_detallados) > 5:
                        mensaje_resultado += f"• ... y {len(errores_detallados) - 5} errores más\n"
            else:
                mensaje_resultado = f"❌ IMPORTACIÓN FALLIDA\n\n"
                mensaje_resultado += f"No se pudieron importar gestiones. Errores encontrados:\n"
                for error in errores_detallados[:10]:
                    mensaje_resultado += f"• {error}\n"

            return gestiones_importadas > 0, mensaje_resultado

        except Exception as e:
            return False, f"Error al importar Excel: {str(e)}"

    def validar_datos_gestiones_importacion(self, df):
        """Valida los datos del DataFrame de importación"""
        errores = []

        if df['nit_cliente'].isnull().any():
            errores.append("❌ Hay NITs vacíos en el archivo")

        for index, fecha in df['fecha_contacto'].items():
            if pd.isna(fecha):
                errores.append(f"Fila {index + 2}: Fecha contacto vacía")
                continue
            fecha_convertida = self.convertir_fecha(fecha)
            if not fecha_convertida:
                errores.append(f"Fila {index + 2}: Formato fecha contacto inválido")

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
        import re
        if re.match(r'^\d+\.', resultado):
            numero = int(resultado.split('.')[0])
            return 1 <= numero <= 21
        else:
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

    # ------------------------------------------------------------
    # Métodos de métricas y gráficas
    # ------------------------------------------------------------

    def obtener_metricas_principales(self):
        """Obtiene métricas principales del dashboard"""
        try:
            user = self.current_user
            if not user:
                return self._metricas_vacias()

            cartera_df = self.obtener_cartera_actual()

            if cartera_df.empty:
                return self._metricas_vacias()

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
            print(f"Error obteniendo métricas principales: {e}")
            return self._metricas_vacias()

    def _metricas_vacias(self):
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

    def obtener_datos_graficas(self):
        """Obtiene datos para las gráficas del dashboard"""
        try:
            user = self.current_user
            if not user:
                return self._datos_graficas_vacios()

            cartera_df = self.obtener_cartera_actual()

            if cartera_df.empty:
                return self._datos_graficas_vacios()

            corriente = cartera_df[cartera_df['dias_vencidos'] == 0]['total_cop'].sum() if 'total_cop' in cartera_df.columns else 0
            ven1_30 = cartera_df[(cartera_df['dias_vencidos'] >= 1) & (cartera_df['dias_vencidos'] <= 30)]['total_cop'].sum() if 'total_cop' in cartera_df.columns else 0
            ven31_60 = cartera_df[(cartera_df['dias_vencidos'] >= 31) & (cartera_df['dias_vencidos'] <= 60)]['total_cop'].sum() if 'total_cop' in cartera_df.columns else 0
            ven61_90 = cartera_df[(cartera_df['dias_vencidos'] >= 61) & (cartera_df['dias_vencidos'] <= 90)]['total_cop'].sum() if 'total_cop' in cartera_df.columns else 0
            ven90_mas = cartera_df[cartera_df['dias_vencidos'] > 90]['total_cop'].sum() if 'total_cop' in cartera_df.columns else 0

            distribucion_estado = (corriente, ven1_30, ven31_60, ven61_90, ven90_mas)

            clientes_mora = cartera_df[cartera_df['dias_vencidos'] > 0]
            if not clientes_mora.empty:
                top_clientes = clientes_mora.groupby('razon_social_cliente')['total_cop'].sum().nlargest(10)
                top_clientes_mora = [(cliente, monto) for cliente, monto in top_clientes.items()]
            else:
                top_clientes_mora = []

            evolucion_mensual = []

            return {
                'distribucion_estado': distribucion_estado,
                'top_clientes_mora': top_clientes_mora,
                'evolucion_mensual': evolucion_mensual
            }

        except Exception as e:
            print(f"Error obteniendo datos para gráficas: {e}")
            return self._datos_graficas_vacios()

    def _datos_graficas_vacios(self):
        return {
            'distribucion_estado': (0, 0, 0, 0, 0),
            'top_clientes_mora': [],
            'evolucion_mensual': []
        }

    def obtener_proyeccion_vencimientos(self):
        """Obtiene proyección de vencimientos para rangos específicos"""
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

            hoy = datetime.now()

            # VENCIDO
            cursor.execute(f'''
                SELECT SUM(total_cop) 
                FROM cartera_actual 
                {where_clause} AND dias_vencidos > 0
            ''', params)
            vencido = cursor.fetchone()[0] or 0

            # VENCE ESTE MES
            mes_actual_inicio = hoy.replace(day=1)
            mes_actual_fin = (mes_actual_inicio + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            cursor.execute(f'''
                SELECT SUM(total_cop) 
                FROM cartera_actual 
                {where_clause} AND dias_vencidos = 0 
                AND fecha_vencimiento BETWEEN ? AND ?
            ''', params + [mes_actual_inicio.strftime('%Y-%m-%d'), mes_actual_fin.strftime('%Y-%m-%d')])
            vence_este_mes = cursor.fetchone()[0] or 0

            # VENCE PRÓXIMO MES
            proximo_mes_inicio = (mes_actual_inicio + timedelta(days=32)).replace(day=1)
            proximo_mes_fin = (proximo_mes_inicio + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            cursor.execute(f'''
                SELECT SUM(total_cop) 
                FROM cartera_actual 
                {where_clause} AND dias_vencidos = 0 
                AND fecha_vencimiento BETWEEN ? AND ?
            ''', params + [proximo_mes_inicio.strftime('%Y-%m-%d'), proximo_mes_fin.strftime('%Y-%m-%d')])
            vence_proximo_mes = cursor.fetchone()[0] or 0

            # VENCE EN 2 MESES
            dos_meses_inicio = (proximo_mes_inicio + timedelta(days=32)).replace(day=1)
            dos_meses_fin = (dos_meses_inicio + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            cursor.execute(f'''
                SELECT SUM(total_cop) 
                FROM cartera_actual 
                {where_clause} AND dias_vencidos = 0 
                AND fecha_vencimiento BETWEEN ? AND ?
            ''', params + [dos_meses_inicio.strftime('%Y-%m-%d'), dos_meses_fin.strftime('%Y-%m-%d')])
            vence_2_meses = cursor.fetchone()[0] or 0

            conn.close()

            proyeccion = [
                ('Vencido', vencido),
                ('Vence Este Mes', vence_este_mes),
                ('Vence Próximo Mes', vence_proximo_mes),
                ('Vence en 2 Meses', vence_2_meses)
            ]

            return proyeccion

        except Exception as e:
            conn.close()
            print(f"Error obteniendo proyección de vencimientos: {e}")
            return []

    def obtener_datos_completos_cliente(self, nit_cliente):
        """Obtiene todos los datos de un cliente incluyendo información de contacto"""
        conn = sqlite3.connect(self.db_path)

        try:
            query_cliente = '''
                SELECT * FROM clientes 
                WHERE nit_cliente = ?
            '''
            cliente_df = pd.read_sql_query(query_cliente, conn, params=(nit_cliente,))

            query_cartera = '''
                SELECT * FROM cartera_actual 
                WHERE nit_cliente = ?
                ORDER BY dias_vencidos DESC, total_cop DESC
            '''
            cartera_df = pd.read_sql_query(query_cartera, conn, params=(nit_cliente,))

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
        """Obtiene clientes según filtros específicos y por usuario"""
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
            print(f"Error obteniendo clientes filtrados: {e}")
            return pd.DataFrame()

    # ------------------------------------------------------------
    # Métodos de historial de cartera
    # ------------------------------------------------------------

    def cargar_historial_completo(self, ruta_base="CARTERA DIARIA"):
        """Carga todos los archivos Excel históricos usando solo columnas básicas"""
        try:
            import glob

            if not os.path.exists(ruta_base):
                return False, f"No se encuentra la carpeta: {ruta_base}"

            archivos_procesados = 0
            errores = 0
            resultados = []

            for año_dir in os.listdir(ruta_base):
                ruta_año = os.path.join(ruta_base, año_dir)

                if not os.path.isdir(ruta_año) or not año_dir.isdigit():
                    continue

                año = int(año_dir)
                print(f"Procesando año: {año}")

                for mes_dir in os.listdir(ruta_año):
                    ruta_mes = os.path.join(ruta_año, mes_dir)

                    if not os.path.isdir(ruta_mes):
                        continue

                    patron_archivos = os.path.join(ruta_mes, "CARTERA *.xlsx")
                    archivos_mes = glob.glob(patron_archivos)

                    for archivo_path in archivos_mes:
                        try:
                            nombre_archivo = os.path.basename(archivo_path)
                            partes = nombre_archivo.replace('CARTERA ', '').replace('.xlsx', '').split('-')
                            if len(partes) == 2:
                                dia = int(partes[0])
                                mes_num = int(partes[1])

                                fecha_carga = datetime(año, mes_num, dia)
                                fecha_str = fecha_carga.strftime('%Y-%m-%d')

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
            df = pd.read_excel(file_path, usecols=range(10))

            nombres_columnas = [
                'nombre_vendedor',
                'nit_cliente',
                'razon_social_cliente',
                'centro_operacion',
                'nro_factura',
                'total_cop',
                'fecha_emision',
                'fecha_vencimiento',
                'condicion_pago',
                'dias_vencidos'
            ]

            df.columns = nombres_columnas[:len(df.columns)]

            print(f"Procesando: {os.path.basename(file_path)} - {len(df)} registros")

            df['total_cop'] = df['total_cop'].apply(self.limpiar_valor_monetario)
            df['dias_vencidos'] = pd.to_numeric(df['dias_vencidos'], errors='coerce').fillna(0)

            df['fecha_emision'] = df['fecha_emision'].apply(self.convertir_fecha)
            df['fecha_vencimiento'] = df['fecha_vencimiento'].apply(self.convertir_fecha)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

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
                        print(f"Error insertando registro: {e}")
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
        """Obtiene un reporte detallado de lo que se ha cargado en el historial"""
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

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT fecha_carga FROM historial_cartera_diario ORDER BY fecha_carga')
            fechas_cargadas = [row[0] for row in cursor.fetchall()]
            conn.close()

            print(f"Fechas ya cargadas: {len(fechas_cargadas)}")

            archivos_nuevos = 0
            errores = 0
            resultados = []

            for año_dir in os.listdir(ruta_base):
                ruta_año = os.path.join(ruta_base, año_dir)

                if not os.path.isdir(ruta_año) or not año_dir.isdigit():
                    continue

                año = int(año_dir)
                print(f"Escaneando año: {año}")

                for mes_dir in os.listdir(ruta_año):
                    ruta_mes = os.path.join(ruta_año, mes_dir)

                    if not os.path.isdir(ruta_mes):
                        continue

                    patron_archivos = os.path.join(ruta_mes, "CARTERA *.xlsx")
                    archivos_mes = glob.glob(patron_archivos)

                    for archivo_path in archivos_mes:
                        try:
                            nombre_archivo = os.path.basename(archivo_path)
                            partes = nombre_archivo.replace('CARTERA ', '').replace('.xlsx', '').split('-')
                            if len(partes) == 2:
                                dia = int(partes[0])
                                mes_num = int(partes[1])

                                fecha_carga = datetime(año, mes_num, dia)
                                fecha_str = fecha_carga.strftime('%Y-%m-%d')

                                if fecha_str in fechas_cargadas:
                                    continue

                                success, message = self.cargar_excel_historial(archivo_path, fecha_str)

                                if success:
                                    archivos_nuevos += 1
                                    resultados.append(f"✅ {fecha_str}: {message}")
                                    fechas_cargadas.append(fecha_str)
                                else:
                                    errores += 1
                                    resultados.append(f"❌ {fecha_str}: {message}")

                        except Exception as e:
                            errores += 1
                            resultados.append(f"❌ Error procesando {archivo_path}: {str(e)}")

            mensaje_final = f"Actualización completada:\n"
            mensaje_final += f"📥 Archivos nuevos: {archivos_nuevos}\n"
            mensaje_final += f"❌ Errores: {errores}\n"

            if resultados:
                mensaje_final += f"\nResultados:\n" + "\n".join(resultados[-10:])

            return archivos_nuevos > 0, mensaje_final

        except Exception as e:
            return False, f"Error en carga incremental: {str(e)}"

    # ------------------------------------------------------------
    # Métodos de autenticación (compatibilidad)
    # ------------------------------------------------------------

    def autenticar_usuario(self, email, password, ip_address="", user_agent=""):
        """Método de compatibilidad - usa el UserManager existente"""
        print(f"🔍 AUTENTICAR_USUARIO llamado para: {email}")

        try:
            import streamlit as st

            if hasattr(st, 'session_state') and 'user_manager' in st.session_state:
                print(f"   ✅ Usando UserManager existente desde session_state")
                user_manager = st.session_state.user_manager

                if hasattr(user_manager, 'autenticar_usuario'):
                    return user_manager.autenticar_usuario(email, password, ip_address, user_agent)
                else:
                    print(f"   ❌ ERROR: autenticar_usuario NO encontrado en user_manager")
                    return False, "Error interno: método de autenticación no disponible", None
            else:
                print(f"   ⚠️ UserManager no en session_state, creando temporal")
                from auth import UserManager
                temp_manager = UserManager(self.db_path)
                return temp_manager.autenticar_usuario(email, password, ip_address, user_agent)

        except Exception as e:
            print(f"❌ Error en autenticar_usuario: {e}")
            import traceback
            traceback.print_exc()
            return False, f"Error de autenticación: {str(e)}", None

    # ------------------------------------------------------------
    # Métodos de diagnóstico y normalización
    # ------------------------------------------------------------

    def diagnosticar_vendedor_usuario(self, user_id=None):
        """Función de diagnóstico para identificar problemas con vendedores asignados"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if not user_id and self.current_user:
                user_email = self.current_user.get('email', '')
                cursor.execute('SELECT id, vendedor_asignado FROM usuarios WHERE email = ?', (user_email,))
            elif user_id:
                cursor.execute('SELECT id, vendedor_asignado FROM usuarios WHERE id = ?', (user_id,))
            else:
                conn.close()
                return "No hay usuario para diagnosticar"

            usuario = cursor.fetchone()

            if not usuario:
                conn.close()
                return "Usuario no encontrado"

            user_id_db, vendedor_asignado = usuario

            cursor.execute('SELECT DISTINCT nombre_vendedor FROM cartera_actual ORDER BY nombre_vendedor')
            vendedores_cartera = [row[0] for row in cursor.fetchall() if row[0]]

            cursor.execute('SELECT DISTINCT nombre_vendedor FROM vendedores ORDER BY nombre_vendedor')
            vendedores_tabla = [row[0] for row in cursor.fetchall() if row[0]]

            conn.close()

            reporte = f"""
            ===== DIAGNÓSTICO DE VENDEDOR =====

            1. USUARIO ACTUAL:
               - ID: {user_id_db}
               - Vendedor asignado en BD: '{vendedor_asignado}'

            2. VENDEDORES EN CARTERA_ACTUAL ({len(vendedores_cartera)}):
            """

            for i, vendedor in enumerate(vendedores_cartera[:20], 1):
                reporte += f"   {i:2d}. {vendedor}\n"

            if len(vendedores_cartera) > 20:
                reporte += f"   ... y {len(vendedores_cartera) - 20} más\n"

            reporte += f"""
            3. VENDEDORES EN TABLA VENDEDORES ({len(vendedores_tabla)}):
            """

            for i, vendedor in enumerate(vendedores_tabla[:20], 1):
                reporte += f"   {i:2d}. {vendedor}\n"

            if len(vendedores_tabla) > 20:
                reporte += f"   ... y {len(vendedores_tabla) - 20} más\n"

            if vendedor_asignado:
                reporte += f"""
            4. COINCIDENCIAS PARA '{vendedor_asignado}':
                """

                nombre_buscar = vendedor_asignado
                if '(' in vendedor_asignado and ')' in vendedor_asignado:
                    import re
                    match = re.search(r'\((.*?)\)', vendedor_asignado)
                    if match:
                        nombre_buscar = match.group(1).strip()

                coincidencias_cartera = []
                for vendedor in vendedores_cartera:
                    if vendedor and nombre_buscar.upper() in vendedor.upper():
                        coincidencias_cartera.append(vendedor)

                coincidencias_tabla = []
                for vendedor in vendedores_tabla:
                    if vendedor and nombre_buscar.upper() in vendedor.upper():
                        coincidencias_tabla.append(vendedor)

                if coincidencias_cartera:
                    reporte += f"   En cartera_actual ({len(coincidencias_cartera)}):\n"
                    for vendedor in coincidencias_cartera:
                        reporte += f"     • {vendedor}\n"
                else:
                    reporte += f"   ❌ No hay coincidencias en cartera_actual\n"

                if coincidencias_tabla:
                    reporte += f"   En tabla vendedores ({len(coincidencias_tabla)}):\n"
                    for vendedor in coincidencias_tabla:
                        reporte += f"     • {vendedor}\n"
                else:
                    reporte += f"   ❌ No hay coincidencias en tabla vendedores\n"

            return reporte

        except Exception as e:
            return f"Error en diagnóstico: {str(e)}"

    def normalizar_nombres_vendedores(self):
        """Normaliza los nombres de vendedores para asegurar consistencia"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT DISTINCT nombre_vendedor FROM cartera_actual WHERE nombre_vendedor IS NOT NULL AND nombre_vendedor != ""')
            vendedores_cartera = [row[0] for row in cursor.fetchall()]

            cursor.execute('SELECT DISTINCT nombre_vendedor FROM vendedores WHERE nombre_vendedor IS NOT NULL AND nombre_vendedor != ""')
            vendedores_tabla = [row[0] for row in cursor.fetchall()]

            for vendedor in vendedores_cartera:
                if vendedor and vendedor.strip():
                    cursor.execute('''
                        INSERT OR IGNORE INTO vendedores (nombre_vendedor)
                        VALUES (?)
                    ''', (vendedor.strip(),))

            cursor.execute('SELECT DISTINCT vendedor_asignado FROM usuarios WHERE vendedor_asignado IS NOT NULL AND vendedor_asignado != ""')
            vendedores_usuarios = [row[0] for row in cursor.fetchall()]

            for vendedor in vendedores_usuarios:
                if vendedor and vendedor.strip():
                    if '(' in vendedor and ')' in vendedor:
                        import re
                        match = re.search(r'\((.*?)\)', vendedor)
                        if match:
                            nombre_vendedor = match.group(1).strip()
                            cursor.execute('''
                                INSERT OR IGNORE INTO vendedores (nombre_vendedor)
                                VALUES (?)
                            ''', (nombre_vendedor,))
                    else:
                        cursor.execute('''
                            INSERT OR IGNORE INTO vendedores (nombre_vendedor)
                            VALUES (?)
                        ''', (vendedor.strip(),))

            conn.commit()
            conn.close()

            return True, f"Tabla vendedores actualizada. Cartera: {len(vendedores_cartera)}, Tabla: {len(vendedores_tabla)}, Usuarios: {len(vendedores_usuarios)}"

        except Exception as e:
            return False, f"Error normalizando nombres: {str(e)}"

    # ------------------------------------------------------------
    # Métodos de usuarios (redirigen a UserManager)
    # ------------------------------------------------------------

    def obtener_usuarios(self):
        """Obtiene todos los usuarios"""
        try:
            import streamlit as st
            if hasattr(st, 'session_state') and 'user_manager' in st.session_state:
                return st.session_state.user_manager.obtener_usuarios()
            else:
                from auth import UserManager
                user_manager = UserManager(self.db_path)
                return user_manager.obtener_usuarios()
        except Exception as e:
            print(f"Error obteniendo usuarios: {e}")
            return pd.DataFrame()

    def obtener_usuarios_con_gestiones(self):
        """Obtiene todos los usuarios que tienen gestiones registradas"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = '''
                SELECT DISTINCT u.id, u.email, u.nombre_completo, u.vendedor_asignado
                FROM usuarios u
                JOIN gestiones g ON u.email = g.usuario
                WHERE u.activo = 1
                ORDER BY u.nombre_completo
            '''
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"Error obteniendo usuarios con gestiones: {e}")
            return pd.DataFrame()

    def crear_usuario(self, email, nombre_completo, rol, vendedor_asignado=None, activo=True):
        """Crea un nuevo usuario"""
        try:
            import streamlit as st
            if hasattr(st, 'session_state') and 'user_manager' in st.session_state:
                return st.session_state.user_manager.crear_usuario(
                    email, nombre_completo, rol, vendedor_asignado, activo
                )
            else:
                from auth import UserManager
                user_manager = UserManager(self.db_path)
                return user_manager.crear_usuario(email, nombre_completo, rol, vendedor_asignado, activo)
        except Exception as e:
            return False, f"Error creando usuario: {str(e)}"

    def actualizar_usuario(self, user_id, datos):
        """Actualiza un usuario"""
        try:
            from auth import UserManager
            user_manager = UserManager(self.db_path)
            return user_manager.actualizar_usuario(user_id, datos)
        except Exception as e:
            return False, f"Error actualizando usuario: {str(e)}"

    def cambiar_password(self, user_id, nueva_password):
        """Cambia contraseña de usuario usando el UserManager existente"""
        try:
            import streamlit as st

            if hasattr(st, 'session_state') and 'user_manager' in st.session_state:
                return st.session_state.user_manager.cambiar_password(user_id, nueva_password)
            else:
                from auth import UserManager
                temp_manager = UserManager(self.db_path)
                return temp_manager.cambiar_password(user_id, nueva_password)

        except Exception as e:
            return False, f"Error cambiando contraseña: {str(e)}"

    def eliminar_usuario(self, user_id):
        """Elimina un usuario"""
        try:
            from auth import UserManager
            user_manager = UserManager(self.db_path)
            return user_manager.eliminar_usuario(user_id)
        except Exception as e:
            return False, f"Error eliminando usuario: {str(e)}"

    def obtener_estadisticas_sistema(self):
        """Obtiene estadísticas del sistema"""
        try:
            from auth import UserManager
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

    def sync_to_drive(self):
        """Método de compatibilidad - no realiza sincronización externa"""
        return True