import sqlite3
import sys
import os
from PySide6.QtGui import QIcon
from PySide6.QtGui import QGuiApplication
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas  # ← IMPORTANTE
import matplotlib.dates as mdates
import seaborn as sns
import time
from datetime import datetime
from PySide6.QtWidgets import QMessageBox

# Importaciones locales
from styles import STYLESHEET
from config import config

# Importaciones de PySide6
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                              QTabWidget, QFrame, QLabel, QPushButton, QTableWidget, 
                              QTableWidgetItem, QListWidget, QListWidgetItem, QTextEdit,
                              QComboBox, QLineEdit, QDateEdit, QGroupBox, QGridLayout,
                              QScrollArea, QProgressBar, QMessageBox, QFileDialog,
                              QSplitter, QHeaderView, QFormLayout, QSizePolicy, QDialog,
                              QDialogButtonBox, QMenu, QToolBar, QStatusBar, QInputDialog, QProgressDialog, QCheckBox)
from PySide6.QtCore import Qt, QDate, QTimer, QSize
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QAction

# Ahora importamos después de definir todas las dependencias de PySide6
from database import DatabaseManager
from user_manager import UserManager
from auth import AuthManager
from login_dialog import LoginDialog

class ExportDialog(QDialog):
    def __init__(self, graficas_checkboxes, parent=None):
        super().__init__(parent)
        self.graficas_checkboxes = graficas_checkboxes
        self.setWindowTitle("Exportar Gráficas a PDF")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Título
        title_label = QLabel("📊 Exportar Gráficas Seleccionadas")
        title_label.setObjectName("section_title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Descripción
        desc_label = QLabel("Selecciona las gráficas que quieres incluir en el reporte PDF:")
        desc_label.setStyleSheet("color: #cbd5e1; padding: 10px;")
        layout.addWidget(desc_label)
        
        # Lista de gráficas seleccionables
        self.graficas_group = QGroupBox("Gráficas Disponibles")
        graficas_layout = QVBoxLayout()
        
        self.pdf_checkboxes = {}
        for chart_id, checkbox in self.graficas_checkboxes.items():
            if checkbox:  # Solo las gráficas que existen
                pdf_checkbox = QCheckBox(checkbox.text())
                pdf_checkbox.setChecked(checkbox.isChecked())  # Mismo estado que el selector
                pdf_checkbox.setStyleSheet("QCheckBox { color: #cbd5e1; font-size: 11px; padding: 5px; }")
                self.pdf_checkboxes[chart_id] = pdf_checkbox
                graficas_layout.addWidget(pdf_checkbox)
        
        self.graficas_group.setLayout(graficas_layout)
        layout.addWidget(self.graficas_group)
        
        # Opciones de exportación
        options_group = QGroupBox("Opciones de Exportación")
        options_layout = QVBoxLayout()
        
        # Nombre del archivo
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Nombre del archivo:"))
        self.filename_input = QLineEdit()
        self.filename_input.setText(f"reporte_cartera_{datetime.now().strftime('%Y%m%d_%H%M')}")
        self.filename_input.setPlaceholderText("nombre_del_archivo")
        name_layout.addWidget(self.filename_input)
        name_layout.addWidget(QLabel(".pdf"))
        options_layout.addLayout(name_layout)
        
        # Incluir métricas
        self.include_metrics = QCheckBox("Incluir métricas rápidas")
        self.include_metrics.setChecked(True)
        self.include_metrics.setStyleSheet("QCheckBox { color: #cbd5e1; }")
        options_layout.addWidget(self.include_metrics)
        
        # Incluir filtros aplicados
        self.include_filters = QCheckBox("Incluir configuración de filtros")
        self.include_filters.setChecked(True)
        self.include_filters.setStyleSheet("QCheckBox { color: #cbd5e1; }")
        options_layout.addWidget(self.include_filters)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Botones
        button_layout = QHBoxLayout()
        
        btn_exportar = QPushButton("📄 Exportar a PDF")
        btn_exportar.clicked.connect(self.accept)
        btn_exportar.setObjectName("primary")
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        
        button_layout.addWidget(btn_exportar)
        button_layout.addStretch()
        button_layout.addWidget(btn_cancelar)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def get_selected_charts(self):
        """Retorna la lista de gráficas seleccionadas para exportar"""
        return [chart_id for chart_id, checkbox in self.pdf_checkboxes.items() 
                if checkbox.isChecked()]
    
    def get_export_options(self):
        """Retorna las opciones de exportación"""
        return {
            'filename': self.filename_input.text().strip(),
            'include_metrics': self.include_metrics.isChecked(),
            'include_filters': self.include_filters.isChecked(),
            'selected_charts': self.get_selected_charts()
        }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exportar Gestiones")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.option_group = QGroupBox("Seleccionar opción de exportación")
        option_layout = QVBoxLayout()
        
        self.radio_mes = QPushButton("📅 Exportar gestiones del mes actual")
        self.radio_mes.setCheckable(True)
        self.radio_mes.setChecked(True)
        self.radio_mes.clicked.connect(self.on_option_selected)
        
        self.radio_completo = QPushButton("📊 Exportar historial completo")
        self.radio_completo.setCheckable(True)
        self.radio_completo.clicked.connect(self.on_option_selected)
        
        option_layout.addWidget(self.radio_mes)
        option_layout.addWidget(self.radio_completo)
        self.option_group.setLayout(option_layout)
        layout.addWidget(self.option_group)
        
        # Botones
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def on_option_selected(self):
        sender = self.sender()
        if sender == self.radio_mes:
            self.radio_completo.setChecked(False)
        else:
            self.radio_mes.setChecked(False)
            
    def get_export_option(self):
        if self.radio_mes.isChecked():
            return "mes_actual"
        else:
            return "completo"

class MetricCard(QFrame):
    def __init__(self, title, value, format_str="{:,.0f}", parent=None):
        super().__init__(parent)
        self.setObjectName("metric_card")
        self.setMinimumHeight(100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.value_label = QLabel(format_str.format(value))
        self.value_label.setObjectName("metric_value")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setWordWrap(True)
        
        self.title_label = QLabel(title)
        self.title_label.setObjectName("metric_title")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        
        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)
        self.setLayout(layout)

    def update_value(self, value, format_str="{:,.0f}"):
        """Actualiza el valor de la métrica"""
        self.value_label.setText(format_str.format(value))

class ProgressCard(QFrame):
    def __init__(self, title, current, total, parent=None):
        super().__init__(parent)
        self.setObjectName("metric_card")
        self.setMinimumHeight(130)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Título
        title_label = QLabel(title)
        title_label.setObjectName("metric_title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Porcentaje
        if total > 0:
            percentage = (current / total) * 100
        else:
            percentage = 0
            
        self.percentage_label = QLabel(f"{percentage:.1f}%")
        self.percentage_label.setObjectName("metric_value")
        self.percentage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.percentage_label)
        
        # ✅ BARRA DE PROGRESO CON COLOR DINÁMICO
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(int(percentage))
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat(f"{current}/{total}")
        
        # ✅ APLICAR COLOR DINÁMICO BASADO EN PORCENTAJE
        self.actualizar_color_barra(percentage)
        
        layout.addWidget(self.progress_bar)
        
        # Texto descriptivo
        self.desc_label = QLabel(f"✅ {current} gestionados | ⏳ {total - current} pendientes")
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_label.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        layout.addWidget(self.desc_label)
        
        self.setLayout(layout)

    def actualizar_color_barra(self, porcentaje):
        """Actualiza el color de la barra basado en el porcentaje"""
        try:
            # ✅ GRADIENTE DE COLOR: Naranja (0%) → Amarillo (50%) → Verde (100%)
            if porcentaje <= 50:
                # Naranja → Amarillo
                factor = porcentaje / 50.0
                red = 245 + int((255 - 245) * factor)    # 245 → 255
                green = 124 + int((193 - 124) * factor)  # 124 → 193
                blue = 0                                 # 0 → 0
            else:
                # Amarillo → Verde
                factor = (porcentaje - 50) / 50.0
                red = 255 - int((255 - 0) * factor)      # 255 → 0
                green = 193 + int((179 - 193) * factor)  # 193 → 179
                blue = 0 + int((179 - 0) * factor)       # 0 → 179
            
            color_hex = f"#{red:02x}{green:02x}{blue:02x}"
            
            # ✅ APLICAR ESTILO DINÁMICO
            estilo = f"""
            QProgressBar {{
                border: 2px solid #415A77;
                border-radius: 6px;
                background-color: #1B263B;
                text-align: center;
                color: #e2e8f0;
                font-weight: bold;
                font-size: 11px;
                height: 20px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color_hex}, stop:1 {color_hex});
                border-radius: 4px;
            }}
            """
            self.progress_bar.setStyleSheet(estilo)
            
        except Exception as e:
            print(f"Error actualizando color de barra: {e}")

    def update_progress(self, current, total):
        """Actualiza el progreso y el color de la barra"""
        try:
            if total > 0:
                percentage = (current / total) * 100
            else:
                percentage = 0
            
            # Actualizar porcentaje
            self.percentage_label.setText(f"{percentage:.1f}%")
            
            # Actualizar barra
            self.progress_bar.setValue(int(percentage))
            self.progress_bar.setFormat(f"{current}/{total}")
            
            # ✅ ACTUALIZAR COLOR DINÁMICAMENTE
            self.actualizar_color_barra(percentage)
            
            # Actualizar texto descriptivo
            self.desc_label.setText(f"✅ {current} gestionados | ⏳ {total - current} pendientes")
            
        except Exception as e:
            print(f"Error actualizando progreso: {e}")

class ReporteCargaDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("📋 Reporte de Carga - Historial Cartera")
        self.setModal(True)
        self.setMinimumSize(900, 600)
        self.setup_ui()
        self.cargar_datos()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Header corporativo
        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout()
        
        title = QLabel("📊 REPORTE DE CARGA - HISTORIAL CARTERA")
        title.setObjectName("section_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(title)
        header.setLayout(header_layout)
        layout.addWidget(header)
        
        # Resumen en cards
        self.resumen_frame = QFrame()
        self.resumen_frame.setObjectName("card")
        resumen_layout = QHBoxLayout()
        
        self.cards = {
            'total_dias': MetricCard("DÍAS CARGADOS", 0),
            'total_registros': MetricCard("REGISTROS", 0, "{:,.0f}"),
            'promedio': MetricCard("PROMEDIO/DÍA", 0, "{:,.0f}"),
            'rango_fechas': MetricCard("RANGO FECHAS", "N/A", "{}")
        }
        
        for card in self.cards.values():
            resumen_layout.addWidget(card)
            
        self.resumen_frame.setLayout(resumen_layout)
        layout.addWidget(self.resumen_frame)
        
        # Tabla de detalle
        detalle_group = QGroupBox("📅 Detalle por Fecha de Carga")
        detalle_layout = QVBoxLayout()
        
        self.tabla_detalle = QTableWidget()
        self.tabla_detalle.setColumnCount(6)
        self.tabla_detalle.setHorizontalHeaderLabels([
            "Fecha Carga", "Registros", "Clientes", "Cartera Total", "Cartera Mora", "Vendedores"
        ])
        
        header = self.tabla_detalle.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)
        
        detalle_layout.addWidget(self.tabla_detalle)
        detalle_group.setLayout(detalle_layout)
        layout.addWidget(detalle_group)
        
        # Botones
        button_layout = QHBoxLayout()
        btn_exportar = QPushButton("📤 Exportar a Excel")
        btn_exportar.clicked.connect(self.exportar_reporte)
        btn_exportar.setObjectName("primary")
        
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.reject)
        
        button_layout.addWidget(btn_exportar)
        button_layout.addStretch()
        button_layout.addWidget(btn_cerrar)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def cargar_datos(self):
        """Carga los datos del reporte"""
        try:
            reporte = self.db.obtener_reporte_carga_historial()
            detalle = reporte['detalle']
            resumen = reporte['resumen']
            
            # Actualizar cards de resumen
            self.cards['total_dias'].update_value(resumen.get('total_dias', 0))
            self.cards['total_registros'].update_value(resumen.get('total_registros', 0))
            self.cards['promedio'].update_value(resumen.get('promedio_registros', 0))
            
            rango_text = f"{resumen.get('fecha_minima', 'N/A')} a {resumen.get('fecha_maxima', 'N/A')}"
            self.cards['rango_fechas'].update_value(rango_text, "{}")
            
            # Llenar tabla de detalle
            self.tabla_detalle.setRowCount(len(detalle))
            for row, (_, item) in enumerate(detalle.iterrows()):
                self.tabla_detalle.setItem(row, 0, QTableWidgetItem(str(item['Fecha Carga'])))
                self.tabla_detalle.setItem(row, 1, QTableWidgetItem(f"{item['Registros Cargados']:,}"))
                self.tabla_detalle.setItem(row, 2, QTableWidgetItem(f"{item['Clientes Únicos']:,}"))
                self.tabla_detalle.setItem(row, 3, QTableWidgetItem(f"${item['Cartera Total']:,.0f}"))
                self.tabla_detalle.setItem(row, 4, QTableWidgetItem(f"${item['Cartera en Mora']:,.0f}"))
                self.tabla_detalle.setItem(row, 5, QTableWidgetItem(f"{item['Vendedores']:,}"))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando reporte: {str(e)}")
            
    def exportar_reporte(self):
        """Exporta el reporte a Excel"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Guardar reporte", "reporte_carga_historial.xlsx", "Excel Files (*.xlsx)"
            )
            
            if file_path:
                reporte = self.db.obtener_reporte_carga_historial()
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    reporte['detalle'].to_excel(writer, sheet_name='Detalle por Fecha', index=False)
                    
                    # Crear hoja de resumen
                    resumen_df = pd.DataFrame([reporte['resumen']])
                    resumen_df.to_excel(writer, sheet_name='Resumen General', index=False)
                    
                QMessageBox.information(self, "Éxito", f"Reporte exportado a:\n{file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error exportando reporte: {str(e)}")

class ModernCRM(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Inicializar managers
        self.db = DatabaseManager()
        self.user_manager = UserManager(self.db.db_path)
        self.auth_manager = AuthManager(self.user_manager)
        
        # Mostrar login primero - PERO NO MOSTRAR LA VENTANA PRINCIPAL AÚN
        if self.show_login():
            # Solo si el login es exitoso, configurar UI
            self.setup_ui()
            self.load_icon()
        else:
            # Si el login falla, cerrar aplicación
            sys.exit(0)

    def show_login(self):
        """Muestra el diálogo de login y retorna True si es exitoso - VERSIÓN CORREGIDA"""
        from login_dialog import LoginDialog
        login_dialog = LoginDialog(self.user_manager, self)
        
        if login_dialog.exec() == QDialog.DialogCode.Accepted:
            if hasattr(login_dialog, 'user_data') and login_dialog.user_data:
                user_data = login_dialog.user_data
                self.auth_manager.current_user = user_data
                self.auth_manager.is_authenticated = True
                self.auth_manager.session_start = time.time()
                self.db.set_current_user(user_data)
                print(f"✅ Usuario autenticado: {user_data['email']} - Rol: {user_data['rol']}")
                return True
        return False
       
    def setup_ui(self):
        # PRIMERO: Configurar ventana básica SIN mostrar maximizada
        self.setWindowTitle(f"{config.APP_NAME} - Usuario: {self.auth_manager.current_user['nombre_completo']}")
        self.setStyleSheet(STYLESHEET)
        
        # Configurar tamaño mínimo mientras carga
        self.setMinimumSize(1200, 700)
        
        # Crear pantalla de carga
        self.create_loading_screen()
        
        # Mostrar ventana (no maximizada aún)
        self.show()
        
        # Centrar en pantalla
        self.center_on_screen()
        
        # Cargar datos primero, luego maximizar
        QTimer.singleShot(100, self.initialize_after_load)

    def create_loading_screen(self):
        """Crea una pantalla de carga mientras se inicializa la aplicación"""
        self.loading_widget = QWidget()
        self.loading_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0D1B2A, stop:1 #1B263B);
            }
        """)
        
        layout = QVBoxLayout(self.loading_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo/Spinner
        spinner_label = QLabel("⏳")
        spinner_label.setStyleSheet("""
            QLabel {
                font-size: 60px;
                color: #00B3B0;
                padding: 20px;
            }
        """)
        spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Texto de carga
        loading_text = QLabel("Iniciando CRM ALPAPEL SAS...")
        loading_text.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #e2e8f0;
                padding: 10px;
            }
        """)
        loading_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Información adicional
        info_text = QLabel("Cargando datos y configurando interfaz...")
        info_text.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #cbd5e1;
                padding: 5px;
            }
        """)
        info_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(spinner_label)
        layout.addWidget(loading_text)
        layout.addWidget(info_text)
        
        self.setCentralWidget(self.loading_widget)

    def center_on_screen(self):
        """Centra la ventana en la pantalla"""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.frameGeometry()
            
            x = (screen_geometry.width() - window_geometry.width()) // 2
            y = (screen_geometry.height() - window_geometry.height()) // 2
            
            self.move(x, y)

    def initialize_after_load(self):
        """Inicializa la UI completa después de cargar datos"""
        try:
            print("🔄 Iniciando carga automática de datos...")
            
            # 1. Primero cargar todos los datos CON FUERZA
            self.load_data()
            
            # 2. Forzar actualización inmediata del dashboard
            QApplication.processEvents()  # Actualizar UI
            
            # 3. Luego crear la UI principal
            self.create_main_ui()
            
            # 4. Pequeña pausa y luego maximizar
            QTimer.singleShot(1000, self.finalize_initialization)
            
        except Exception as e:
            print(f"❌ Error en inicialización: {e}")
            self.show_error_loading(str(e))

    def create_main_ui(self):
        """Crea la UI principal reemplazando la pantalla de carga"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        self.create_header(layout)
        self.create_toolbar()
        self.create_statusbar()
        
        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.tabs)
        
        # Crear pestañas en orden específico
        self.create_dashboard_tab()
        self.create_cartera_tab()
        self.create_gestion_tab()
        self.create_clientes_tab()
        self.create_analisis_cartera_tab()
        self.create_analisis_gestion_tab()
        
        if self.auth_manager.has_permission('manage_users'):
            self.create_admin_tab()
        
        # Configurar timers
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_data)
        self.timer.start(config.UI_REFRESH_INTERVAL)
        
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self.check_session_timeout)
        self.session_timer.start(config.SESSION_CHECK_INTERVAL)  # ✅ Usar configuración

    def finalize_initialization(self):
        """Finaliza la inicialización maximizando la ventana y actualizando datos"""
        try:
            # Forzar actualización de la UI
            QApplication.processEvents()
            
            # Maximizar después de que todo esté cargado
            self.showMaximized()
            
            # Opcional: Forzar focus en dashboard
            self.tabs.setCurrentIndex(0)
            
            # LLAMAR DIRECTAMENTE a load_data después de un breve delay
            QTimer.singleShot(1500, self.load_data)
            
            print("✅ CRM iniciado correctamente en pantalla completa")
            
        except Exception as e:
            print(f"Error al finalizar inicialización: {e}")

    def auto_click_refresh(self):
        """Simula un clic en el botón de actualizar automáticamente"""
        try:
            print("🔄 Ejecutando actualización automática...")
            
            # Buscar y hacer clic en el botón de actualizar de la toolbar
            for action in self.findChildren(QAction):
                if action.text() == "🔄 Actualizar":
                    action.trigger()
                    print("✅ Botón de actualizar activado automáticamente")
                    return
            
            # Si no encuentra en toolbar, buscar en otros lugares
            print("⚠️ No se encontró el botón de actualizar en toolbar, buscando alternativas...")
            
            # Buscar en el tab de cartera
            for button in self.findChildren(QPushButton):
                if button.text() == "🔄 Actualizar":
                    button.click()
                    print("✅ Botón de actualizar encontrado y activado")
                    return
            
            print("❌ No se encontró ningún botón de actualizar")
            
        except Exception as e:
            print(f"❌ Error en actualización automática: {e}")

    def show_error_loading(self, error_message):
        """Muestra error si falla la carga"""
        error_widget = QWidget()
        layout = QVBoxLayout(error_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        error_label = QLabel(f"❌ Error al cargar la aplicación:\n{error_message}")
        error_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #ef4444;
                padding: 20px;
                text-align: center;
            }
        """)
        error_label.setWordWrap(True)
        
        retry_button = QPushButton("Reintentar")
        retry_button.setObjectName("primary")
        retry_button.clicked.connect(self.retry_initialization)
        
        layout.addWidget(error_label)
        layout.addWidget(retry_button)
        
        self.setCentralWidget(error_widget)

    def retry_initialization(self):
        """Reintenta la inicialización"""
        self.setup_ui()

    def load_icon(self):
        """Carga el icono de la aplicación de manera robusta"""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(base_dir, 'assets', 'icon.ico')
            
            print(f"🔍 Buscando icono en: {icon_path}")
            
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                print("✅ Icono cargado correctamente")
            else:
                print(f"❌ Icono no encontrado en: {icon_path}")
                # Listar archivos en assets para debug
                assets_dir = os.path.join(base_dir, 'assets')
                if os.path.exists(assets_dir):
                    print(f"📁 Archivos en assets: {os.listdir(assets_dir)}")
                
        except Exception as e:
            print(f"❌ Error cargando icono: {e}")
    
    def create_header(self, layout):
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(100)  # Aumenté de 90 a 100px para dar más espacio
        header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 10, 20, 10)  # Aumenté márgenes verticales
        
        # Logo
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            logo_path = os.path.join(base_dir, 'assets', 'logo.png')
            if os.path.exists(logo_path):
                logo_label = QLabel()
                pixmap = QPixmap(logo_path)
                logo_label.setPixmap(pixmap.scaled(150, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                header_layout.addWidget(logo_label)
        except Exception as e:
            print(f"Error cargando logo: {e}")
        
        # Título principal 
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(10, 5, 10, 5)  # Ajusté márgenes
        title_layout.setSpacing(0)  # Cero espacio entre líneas
        
        title_label = QLabel("CRM GESTIÓN DE CARTERA")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        subtitle_label = QLabel("ALPAPEL SAS")
        subtitle_label.setObjectName("subtitle") 
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("font-size: 14px;")
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        
        header_layout.addWidget(title_container)
        header_layout.addStretch()
        
        # Panel de información del usuario - CORREGIDO
        user_panel = QFrame()
        user_panel.setObjectName("user_panel")
        user_layout = QVBoxLayout(user_panel)
        user_layout.setContentsMargins(15, 8, 15, 8)  # Márgenes internos adecuados
        user_layout.setSpacing(2)  # Espacio mínimo entre líneas
        
        user_name = QLabel(self.auth_manager.current_user['nombre_completo'])
        user_name.setObjectName("user_name")
        user_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_name.setWordWrap(True)
        user_name.setMinimumHeight(20)  # Altura mínima garantizada
        
        user_role = QLabel(config.ROLES.get(self.auth_manager.current_user['rol'], 'Usuario'))
        user_role.setObjectName("user_role") 
        user_role.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_role.setWordWrap(True)
        user_role.setMinimumHeight(18)  # Altura mínima garantizada
        
        user_layout.addWidget(user_name)
        user_layout.addWidget(user_role)
        
        header_layout.addWidget(user_panel)
        
        # Botón de logout (ya lo tenías bien)
        btn_logout = QPushButton("🔒 Cerrar Sesión")
        btn_logout.setToolTip("Cerrar sesión y salir del sistema")
        btn_logout.clicked.connect(self.logout)
        btn_logout.setObjectName("danger")
        btn_logout.setMinimumWidth(120)
        btn_logout.setMinimumHeight(35)
        
        header_layout.addWidget(btn_logout)
        
        header.setLayout(header_layout)
        layout.addWidget(header)
    
    def create_toolbar(self):
        """Crea la barra de herramientas con acciones del usuario"""
        toolbar = QToolBar("Herramientas")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)
        
        # Acción de actualizar
        act_actualizar = QAction("🔄 Actualizar", self)
        act_actualizar.setShortcut("F5")
        act_actualizar.triggered.connect(self.load_data)
        toolbar.addAction(act_actualizar)
        
        toolbar.addSeparator()
        
        # Acción de perfil (solo si no es admin)
        if self.auth_manager.current_user['rol'] != 'admin':
            act_perfil = QAction("👤 Mi Perfil", self)
            act_perfil.triggered.connect(self.show_user_profile)
            toolbar.addAction(act_perfil)
        
        # Acción de administración (solo para admins)
        if self.auth_manager.has_permission('manage_users'):
            act_admin = QAction("🛡️ Administración", self)
            act_admin.triggered.connect(self.show_admin_panel)
            toolbar.addAction(act_admin)
    
    def create_statusbar(self):
        """Crea la barra de estado con información de sesión"""
        statusbar = QStatusBar()
        self.setStatusBar(statusbar)
        
        # Información de usuario
        user_info = f"Usuario: {self.auth_manager.current_user['nombre_completo']} | Rol: {config.ROLES.get(self.auth_manager.current_user['rol'], 'Usuario')}"
        statusbar.addWidget(QLabel(user_info))
        
        # Vendedor asignado (si aplica)
        if self.auth_manager.current_user.get('vendedor_asignado'):
            vendedor_info = f" | Vendedor: {self.auth_manager.current_user['vendedor_asignado']}"
            statusbar.addWidget(QLabel(vendedor_info))
        
        # ✅ ACTUALIZADO: Tiempo de inactividad permitido
        statusbar.addPermanentWidget(QLabel(f" | Inactividad: {self.auth_manager.get_session_time_remaining()} min"))
        
        # Texto del desarrollador
        desarrollador_label = QLabel(" | Desarrollado por Edwin Franco (EF)")
        desarrollador_label.setStyleSheet("color: #00B3B0; font-weight: bold;")
        statusbar.addPermanentWidget(desarrollador_label)
    
    def create_admin_tab(self):
        """Crea la pestaña de administración solo para usuarios admin"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(15)
        
        # Título
        title_label = QLabel("🛡️ ADMINISTRACIÓN DEL SISTEMA")
        title_label.setObjectName("section_title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(title_label)
        
        # Gestión de usuarios
        users_group = QGroupBox("👥 Gestión de Usuarios")
        users_layout = QVBoxLayout()
        
        # Barra de herramientas de usuarios
        users_toolbar = QHBoxLayout()
        
        btn_nuevo_usuario = QPushButton("➕ Nuevo Usuario")
        btn_nuevo_usuario.clicked.connect(self.show_new_user_dialog)
        btn_nuevo_usuario.setObjectName("primary")
        
        btn_actualizar_lista = QPushButton("🔄 Actualizar Lista")
        btn_actualizar_lista.clicked.connect(self.load_users_data)
        
        users_toolbar.addWidget(btn_nuevo_usuario)
        users_toolbar.addWidget(btn_actualizar_lista)
        users_toolbar.addStretch()
        
        users_layout.addLayout(users_toolbar)
        
        # Tabla de usuarios
        self.users_table = QTableWidget()
        self.users_table.setObjectName("users_table")
        self.users_table.setColumnCount(8)
        self.users_table.setHorizontalHeaderLabels([
            "ID", "Email", "Nombre Completo", "Rol", "Vendedor Asignado", 
            "Activo", "Último Login", "Acciones"
        ])
        
        header = self.users_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)
        
        users_layout.addWidget(self.users_table)
        users_group.setLayout(users_layout)
        scroll_layout.addWidget(users_group)
        
        # Estadísticas del sistema
        stats_group = QGroupBox("📊 Estadísticas del Sistema")
        stats_layout = QHBoxLayout()
        
        self.stats_cards = {
            'total_usuarios': MetricCard("TOTAL USUARIOS", 0),
            'usuarios_activos': MetricCard("USUARIOS ACTIVOS", 0),
            'logins_hoy': MetricCard("LOGINS HOY", 0),
            'sesiones_activas': MetricCard("SESIONES ACTIVAS", 1)
        }
        
        for card in self.stats_cards.values():
            stats_layout.addWidget(card)
        
        stats_group.setLayout(stats_layout)
        scroll_layout.addWidget(stats_group)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        self.tabs.addTab(widget, "🛡️ Admin")
        
        # Cargar datos de usuarios
        self.load_users_data()
    
    def load_users_data(self):
        """Carga los datos de usuarios en la tabla de administración"""
        try:
            usuarios = self.user_manager.obtener_usuarios()
            self.users_table.setRowCount(len(usuarios))
            
            # Actualizar estadísticas
            total_usuarios = len(usuarios)
            usuarios_activos = len(usuarios[usuarios['activo'] == 1])
            
            self.stats_cards['total_usuarios'].update_value(total_usuarios)
            self.stats_cards['usuarios_activos'].update_value(usuarios_activos)
            
            for row, (_, usuario) in enumerate(usuarios.iterrows()):
                # ID
                self.users_table.setItem(row, 0, QTableWidgetItem(str(usuario['id'])))
                
                # Email
                self.users_table.setItem(row, 1, QTableWidgetItem(usuario['email']))
                
                # Nombre completo
                self.users_table.setItem(row, 2, QTableWidgetItem(usuario['nombre_completo']))
                
                # Rol con estilo
                rol_item = QTableWidgetItem(config.ROLES.get(usuario['rol'], usuario['rol']))
                self.users_table.setItem(row, 3, rol_item)
                
                # Vendedor asignado
                vendedor = usuario['vendedor_asignado'] or "No asignado"
                self.users_table.setItem(row, 4, QTableWidgetItem(vendedor))
                
                # Estado activo
                estado = "✅ Activo" if usuario['activo'] else "❌ Inactivo"
                self.users_table.setItem(row, 5, QTableWidgetItem(estado))
                
                # Último login
                ultimo_login = usuario['ultimo_login'] or "Nunca"
                self.users_table.setItem(row, 6, QTableWidgetItem(str(ultimo_login)))
                
                # Acciones
                acciones_widget = QWidget()
                acciones_layout = QHBoxLayout()
                acciones_layout.setContentsMargins(5, 2, 5, 2)
                
                btn_editar = QPushButton("✏️")
                btn_editar.setToolTip("Editar usuario")
                btn_editar.clicked.connect(lambda checked, uid=usuario['id']: self.editar_usuario(uid))
                btn_editar.setFixedSize(30, 25)
                
                btn_password = QPushButton("🔑")
                btn_password.setToolTip("Cambiar contraseña")
                btn_password.clicked.connect(lambda checked, uid=usuario['id']: self.cambiar_password_usuario(uid))
                btn_password.setFixedSize(30, 25)
                btn_eliminar = QPushButton("🗑️")
                btn_eliminar.setToolTip("Eliminar usuario")
                btn_eliminar.clicked.connect(lambda checked, uid=usuario['id'], email=usuario['email']: self.eliminar_usuario(uid, email))
                btn_eliminar.setFixedSize(30, 25)
                btn_eliminar.setObjectName("danger")

                              
                
                acciones_layout.addWidget(btn_editar)
                acciones_layout.addWidget(btn_password)
                acciones_layout.addWidget(btn_eliminar) 
                acciones_layout.addStretch()
                
                
                acciones_widget.setLayout(acciones_layout)
                self.users_table.setCellWidget(row, 7, acciones_widget)
                
        except Exception as e:
            print(f"Error cargando datos de usuarios: {e}")
    
    def create_dashboard_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(15)
        
        # Métricas principales
        metrics_group = QGroupBox("📊 Métricas Principales")
        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(10)
        
        self.metric_cards = {
            'cartera_total': MetricCard("CARTERA TOTAL", 0, "${:,.0f}"),
            'cartera_mora': MetricCard("CARTERA EN MORA", 0, "${:,.0f}"),
            'clientes_mora': MetricCard("CLIENTES EN MORA", 0),
            'gestiones_mes': MetricCard("GESTIONES MES", 0)
        }
        
        metrics_layout.addWidget(self.metric_cards['cartera_total'], 0, 0)
        metrics_layout.addWidget(self.metric_cards['cartera_mora'], 0, 1)
        metrics_layout.addWidget(self.metric_cards['clientes_mora'], 1, 0)
        metrics_layout.addWidget(self.metric_cards['gestiones_mes'], 1, 1)
        
        metrics_group.setLayout(metrics_layout)
        scroll_layout.addWidget(metrics_group)
        
        # Gráficas
        charts_splitter = QSplitter(Qt.Orientation.Horizontal)
        charts_splitter.setChildrenCollapsible(False)
        
        # Gráfica 1: Distribución por estado
        chart1_container = QWidget()
        chart1_layout = QVBoxLayout(chart1_container)
        chart1_title = QLabel("📊 Distribución por Estado")
        chart1_title.setObjectName("section_title")
        chart1_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart1_layout.addWidget(chart1_title)
        self.chart1_canvas = None
        self.chart1_layout = QVBoxLayout()
        chart1_layout.addLayout(self.chart1_layout)
        charts_splitter.addWidget(chart1_container)
        
        # Gráfica 2: Top clientes con mora
        chart2_container = QWidget()
        chart2_layout = QVBoxLayout(chart2_container)
        chart2_title = QLabel("⚠️ Top Clientes con Mora")
        chart2_title.setObjectName("section_title")
        chart2_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart2_layout.addWidget(chart2_title)
        self.chart2_canvas = None
        self.chart2_layout = QVBoxLayout()
        chart2_layout.addLayout(self.chart2_layout)
        charts_splitter.addWidget(chart2_container)
        
        # Gráfica 3: Evolución mensual con proyección
        chart3_container = QWidget()
        chart3_layout = QVBoxLayout(chart3_container)
        chart3_title = QLabel("📅 Evolución Mensual + Proyección 3M")
        chart3_title.setObjectName("section_title")
        chart3_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart3_layout.addWidget(chart3_title)
        self.chart3_canvas = None
        self.chart3_layout = QVBoxLayout()
        chart3_layout.addLayout(self.chart3_layout)
        charts_splitter.addWidget(chart3_container)
        
        charts_splitter.setSizes([400, 400, 400])
        scroll_layout.addWidget(charts_splitter)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        self.tabs.addTab(widget, "🏠 Dashboard")
    
    def create_cartera_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        controls_group = QGroupBox("🔍 Filtros de Búsqueda")
        controls_layout = QVBoxLayout()
        
        search_layout = QHBoxLayout()
        self.buscar_cartera_input = QLineEdit()
        self.buscar_cartera_input.setPlaceholderText("Buscar por NIT, Razón Social, Factura...")
        self.buscar_cartera_input.setMinimumHeight(35)
        self.buscar_cartera_input.textChanged.connect(self.filtrar_cartera)
        btn_limpiar_busqueda = QPushButton("Limpiar")
        btn_limpiar_busqueda.clicked.connect(self.limpiar_busqueda_cartera)
        
        search_layout.addWidget(QLabel("🔍 Buscar:"))
        search_layout.addWidget(self.buscar_cartera_input)
        search_layout.addWidget(btn_limpiar_busqueda)
        
        filters_layout = QHBoxLayout()
        
        self.filtro_vendedor_cartera = QComboBox()
        self.filtro_vendedor_cartera.addItem("Todos los vendedores")
        self.filtro_vendedor_cartera.currentTextChanged.connect(self.filtrar_cartera)
        
        self.filtro_ciudad_cartera = QComboBox()
        self.filtro_ciudad_cartera.addItem("Todas las ciudades")
        self.filtro_ciudad_cartera.currentTextChanged.connect(self.filtrar_cartera)
        
        self.filtro_dias_vencidos = QComboBox()
        self.filtro_dias_vencidos.addItems([
            "Todos los días",
            "0 días (Corriente)",
            "1-30 días",
            "31-60 días", 
            "61-90 días",
            "+90 días"
        ])
        self.filtro_dias_vencidos.currentTextChanged.connect(self.filtrar_cartera)
        
        filters_layout.addWidget(QLabel("👤 Vendedor:"))
        filters_layout.addWidget(self.filtro_vendedor_cartera)
        filters_layout.addWidget(QLabel("🏙️ Ciudad:"))
        filters_layout.addWidget(self.filtro_ciudad_cartera)
        filters_layout.addWidget(QLabel("⏰ Días:"))
        filters_layout.addWidget(self.filtro_dias_vencidos)
        
        controls_layout.addLayout(search_layout)
        controls_layout.addLayout(filters_layout)
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        action_layout = QHBoxLayout()
        
        btn_cargar = QPushButton("📁 Cargar Excel")
        btn_cargar.clicked.connect(self.cargar_excel)
        btn_cargar.setObjectName("primary")
        
        btn_actualizar = QPushButton("🔄 Actualizar")
        btn_actualizar.clicked.connect(self.actualizar_cartera)
        
        action_layout.addWidget(btn_cargar)
        action_layout.addWidget(btn_actualizar)
        action_layout.addStretch()
        
        layout.addLayout(action_layout)
        
        self.cartera_table = QTableWidget()
        self.cartera_table.setColumnCount(10)
        self.cartera_table.setHorizontalHeaderLabels([
            "NIT Cliente", "Razón Social", "Vendedor", "Factura", "Total COP", 
            "Fecha Emisión", "Fecha Vcto", "Días Vencidos", "Condición Pago", "Ciudad"
        ])
        
        header = self.cartera_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)
        
        layout.addWidget(self.cartera_table)
        
        self.tabs.addTab(widget, "📁 Cartera")
    
    def create_gestion_tab(self):
        """Crea el tab de gestión con SCROLL funcional"""
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(8)
        
        # SCROLL AREA para toda la pestaña
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Widget contenedor para el scroll
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(8)
        scroll_layout.setContentsMargins(5, 5, 5, 5)
        
        # Splitter principal
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        # === PANEL IZQUIERDO (Compacto) ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(6)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        # Búsqueda
        search_group = QGroupBox("🔍 Búsqueda Rápida")
        search_layout = QVBoxLayout(search_group)
        search_layout.setSpacing(4)
        search_layout.setContentsMargins(8, 12, 8, 8)
        
        self.buscar_gestion_input = QLineEdit()
        self.buscar_gestion_input.setPlaceholderText("Buscar cliente por NIT o Razón Social...")
        self.buscar_gestion_input.setMinimumHeight(32)
        self.buscar_gestion_input.textChanged.connect(self.buscar_cliente_gestion)
        search_layout.addWidget(self.buscar_gestion_input)
        left_layout.addWidget(search_group)
        
        # Filtros
        filters_group = QGroupBox("📋 Filtros")
        filters_layout = QVBoxLayout(filters_group)
        filters_layout.setSpacing(4)
        filters_layout.setContentsMargins(8, 12, 8, 8)
        
        self.filtro_clientes = QComboBox()
        self.filtro_clientes.addItems([
            "Todos los clientes",
            "Clientes en mora", 
            "Clientes sin gestión este mes",
            "Clientes con gestión este mes"
        ])
        self.filtro_clientes.currentTextChanged.connect(self.aplicar_filtro_clientes)
        filters_layout.addWidget(QLabel("Filtrar por:"))
        filters_layout.addWidget(self.filtro_clientes)
        left_layout.addWidget(filters_group)
        
        # Lista de clientes
        list_label = QLabel("👥 Lista de Clientes")
        list_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(list_label)
        
        self.clientes_list = QListWidget()
        self.clientes_list.currentItemChanged.connect(self.on_cliente_selected)
        left_layout.addWidget(self.clientes_list)
        
        splitter.addWidget(left_widget)
        
        # === PANEL DERECHO ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(8)
        
        # Información del cliente
        self.panel_cliente = QGroupBox("👤 Cliente Seleccionado")
        panel_layout = QGridLayout(self.panel_cliente)
        panel_layout.setVerticalSpacing(4)
        panel_layout.setHorizontalSpacing(10)
        
        self.lbl_razon_social = QLabel("Seleccione un cliente")
        self.lbl_razon_social.setStyleSheet("font-weight: bold; color: #e2e8f0;")
        self.lbl_telefono = QLabel("")
        self.lbl_email = QLabel("")
        self.lbl_ciudad = QLabel("")
        self.lbl_dias_vencidos = QLabel("")
        self.lbl_total_mora = QLabel("")
        
        panel_layout.addWidget(QLabel("Razón Social:"), 0, 0)
        panel_layout.addWidget(self.lbl_razon_social, 0, 1)
        panel_layout.addWidget(QLabel("Teléfono:"), 1, 0)
        panel_layout.addWidget(self.lbl_telefono, 1, 1)
        panel_layout.addWidget(QLabel("Email:"), 2, 0)
        panel_layout.addWidget(self.lbl_email, 2, 1)
        panel_layout.addWidget(QLabel("Ciudad:"), 3, 0)
        panel_layout.addWidget(self.lbl_ciudad, 3, 1)
        panel_layout.addWidget(QLabel("Días Vencidos:"), 4, 0)
        panel_layout.addWidget(self.lbl_dias_vencidos, 4, 1)
        panel_layout.addWidget(QLabel("Total Mora:"), 5, 0)
        panel_layout.addWidget(self.lbl_total_mora, 5, 1)
        
        right_layout.addWidget(self.panel_cliente)
        
        # Formulario de gestión
        form_group = QGroupBox("➕ Nueva Gestión")
        form_layout = QVBoxLayout(form_group)
        form_layout.setSpacing(8)
        form_layout.setContentsMargins(10, 15, 10, 10)
        
        # Campos del formulario en grid
        grid_layout = QGridLayout()
        grid_layout.setVerticalSpacing(8)
        grid_layout.setHorizontalSpacing(10)
        
        # Crear widgets del formulario
        self.tipo_contacto = QComboBox()
        self.tipo_contacto.addItems([
            "Llamada telefónica", "WhatsApp", "Correo electrónico",
            "Visita presencial", "Videollamada", "Mensaje de texto"
        ])
        self.tipo_contacto.setMinimumHeight(32)
        
        self.resultado = QComboBox()
        self.actualizar_resultados_gestion()
        self.resultado.setMinimumHeight(32)
        
        self.fecha_contacto = QDateEdit()
        self.fecha_contacto.setDate(QDate.currentDate())
        self.fecha_contacto.setCalendarPopup(True)
        self.fecha_contacto.setMinimumHeight(32)
        
        self.observaciones = QTextEdit()
        self.observaciones.setMaximumHeight(80)
        self.observaciones.setMinimumHeight(60)
        
        self.promesa_fecha = QDateEdit()
        self.promesa_fecha.setDate(QDate.currentDate())
        self.promesa_fecha.setCalendarPopup(True)
        self.promesa_fecha.setMinimumHeight(32)
        
        self.promesa_monto = QLineEdit()
        self.promesa_monto.setPlaceholderText("0")
        self.promesa_monto.setMinimumHeight(32)
        
        self.proxima_gestion = QDateEdit()
        self.proxima_gestion.setDate(QDate.currentDate())
        self.proxima_gestion.setCalendarPopup(True)
        self.proxima_gestion.setMinimumHeight(32)
        
        # Añadir campos al grid
        grid_layout.addWidget(QLabel("Tipo Contacto:"), 0, 0)
        grid_layout.addWidget(self.tipo_contacto, 0, 1)
        grid_layout.addWidget(QLabel("Resultado:"), 1, 0)
        grid_layout.addWidget(self.resultado, 1, 1)
        grid_layout.addWidget(QLabel("Fecha Contacto:"), 2, 0)
        grid_layout.addWidget(self.fecha_contacto, 2, 1)
        grid_layout.addWidget(QLabel("Observaciones:"), 3, 0)
        grid_layout.addWidget(self.observaciones, 3, 1)
        grid_layout.addWidget(QLabel("Promesa Pago Fecha:"), 4, 0)
        grid_layout.addWidget(self.promesa_fecha, 4, 1)
        grid_layout.addWidget(QLabel("Promesa Pago Monto:"), 5, 0)
        grid_layout.addWidget(self.promesa_monto, 5, 1)
        grid_layout.addWidget(QLabel("Próxima Gestión:"), 6, 0)
        grid_layout.addWidget(self.proxima_gestion, 6, 1)
        
        form_layout.addLayout(grid_layout)
        
        # Botón de guardar
        btn_guardar = QPushButton("💾 Guardar Gestión")
        btn_guardar.clicked.connect(self.guardar_gestion)
        btn_guardar.setObjectName("primary")
        btn_guardar.setMinimumHeight(35)
        form_layout.addWidget(btn_guardar)
        
        right_layout.addWidget(form_group)
        
        # Historial de gestiones (CON SCROLL INTERNO)
        historial_group = QGroupBox("📊 Historial de Gestiones")
        historial_layout = QVBoxLayout(historial_group)
        
        # Botones de exportar/importar
        export_layout = QHBoxLayout()
        btn_exportar = QPushButton("📤 Exportar Gestiones")
        btn_exportar.clicked.connect(self.mostrar_dialogo_exportar)
        btn_exportar.setObjectName("primary")
        
        btn_importar = QPushButton("📥 Importar Gestiones")
        btn_importar.clicked.connect(self.importar_gestiones)
        btn_importar.setObjectName("primary")
        
        export_layout.addWidget(btn_exportar)
        export_layout.addWidget(btn_importar)
        export_layout.addStretch()
        historial_layout.addLayout(export_layout)
        
        # Tabla de historial con altura fija para permitir scroll
        self.historial_table = QTableWidget()
        self.historial_table.setColumnCount(8)
        self.historial_table.setHorizontalHeaderLabels([
            "Cliente", "Fecha", "Tipo", "Resultado", "Observaciones", "Promesa", "Monto", "Próx. Gestión"
        ])
        
        header = self.historial_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Observaciones se expande
        
        self.historial_table.verticalHeader().setDefaultSectionSize(80)
        self.historial_table.setWordWrap(True)
        self.historial_table.setMinimumHeight(400)  # Altura suficiente para mostrar varias filas
        
        historial_layout.addWidget(self.historial_table)
        right_layout.addWidget(historial_group)
        
        splitter.addWidget(right_widget)
        
        # Configurar proporciones del splitter
        splitter.setSizes([250, 750])
        
        # Añadir splitter al layout del scroll
        scroll_layout.addWidget(splitter)
        
        # Configurar el scroll area
        scroll.setWidget(scroll_widget)
        
        # Añadir scroll al layout principal
        main_layout.addWidget(scroll)
        
        self.tabs.addTab(widget, "📞 Gestión")
    
    def create_clientes_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        filters_group = QGroupBox("🔍 Filtros de Búsqueda")
        filters_layout = QVBoxLayout()
        
        search_layout = QHBoxLayout()
        self.buscar_clientes_input = QLineEdit()
        self.buscar_clientes_input.setPlaceholderText("Buscar por NIT, Razón Social, Ciudad...")
        self.buscar_clientes_input.setMinimumHeight(35)
        self.buscar_clientes_input.textChanged.connect(self.filtrar_clientes)
        btn_limpiar_clientes = QPushButton("Limpiar")
        btn_limpiar_clientes.clicked.connect(self.limpiar_busqueda_clientes)
        
        search_layout.addWidget(QLabel("🔍 Buscar:"))
        search_layout.addWidget(self.buscar_clientes_input)
        search_layout.addWidget(btn_limpiar_clientes)
        
        dropdown_layout = QHBoxLayout()
        
        self.filtro_vendedor_clientes = QComboBox()
        self.filtro_vendedor_clientes.addItem("Todos los vendedores")
        self.filtro_vendedor_clientes.currentTextChanged.connect(self.filtrar_clientes)
        
        self.filtro_ciudad_clientes = QComboBox()
        self.filtro_ciudad_clientes.addItem("Todas las ciudades")
        self.filtro_ciudad_clientes.currentTextChanged.connect(self.filtrar_clientes)
        
        dropdown_layout.addWidget(QLabel("👤 Vendedor:"))
        dropdown_layout.addWidget(self.filtro_vendedor_clientes)
        dropdown_layout.addWidget(QLabel("🏙️ Ciudad:"))
        dropdown_layout.addWidget(self.filtro_ciudad_clientes)
        
        filters_layout.addLayout(search_layout)
        filters_layout.addLayout(dropdown_layout)
        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)
        
        self.clientes_table = QTableWidget()
        self.clientes_table.setColumnCount(6)
        self.clientes_table.setHorizontalHeaderLabels([
            "NIT Cliente", "Razón Social", "Vendedor", "Ciudad", "Teléfono", "Email"
        ])
        
        layout.addWidget(self.clientes_table)
        
        self.tabs.addTab(widget, "👥 Clientes")
    
    def create_analisis_cartera_tab(self):
        """Crea la pestaña de Análisis de Cartera - VERSIÓN RESPONSIVA COMPATIBLE"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        # SCROLL AREA PRINCIPAL
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(5, 5, 5, 5)
        scroll_layout.setSpacing(8)
        
        # ===== FILTROS RESPONSIVE =====
        filters_group = QGroupBox("🔍 Filtros de Análisis")
        filters_layout = QVBoxLayout(filters_group)
        filters_layout.setSpacing(8)

        # Usar QFormLayout para mejor responsividad
        form_layout = QFormLayout()
        form_layout.setHorizontalSpacing(10)
        form_layout.setVerticalSpacing(5)

        # Fila 1 - Filtros principales
        filtros_row1 = QHBoxLayout()
        self.filtro_vendedor_analisis = QComboBox()
        self.filtro_vendedor_analisis.addItem("Todos los vendedores")
        self.filtro_vendedor_analisis.currentTextChanged.connect(self.actualizar_analisis_cartera)

        self.filtro_condicion_analisis = QComboBox()
        self.filtro_condicion_analisis.addItem("Todas las condiciones")
        self.filtro_condicion_analisis.addItems(["CON", "CO1", "10D", "15D", "30D", "45D", "60D", "75D", "90D", "NC"])
        self.filtro_condicion_analisis.currentTextChanged.connect(self.actualizar_analisis_cartera)

        filtros_row1.addWidget(QLabel("Vendedor:"))
        filtros_row1.addWidget(self.filtro_vendedor_analisis)
        filtros_row1.addWidget(QLabel("Condición:"))
        filtros_row1.addWidget(self.filtro_condicion_analisis)
        filtros_row1.addStretch()

        # Fila 2 - Filtros adicionales
        filtros_row2 = QHBoxLayout()
        self.filtro_centro_analisis = QComboBox()
        self.filtro_centro_analisis.addItem("Todos los centros")
        self.filtro_centro_analisis.addItems(["CON", "CO1"])
        self.filtro_centro_analisis.currentTextChanged.connect(self.actualizar_analisis_cartera)

        self.filtro_dias_analisis = QComboBox()
        self.filtro_dias_analisis.addItems([
            "Todos los días", "0 días (Corriente)", "1-30 días",
            "31-60 días", "61-90 días", "+90 días"
        ])
        self.filtro_dias_analisis.currentTextChanged.connect(self.actualizar_analisis_cartera)

        self.filtro_ciudad_analisis = QComboBox()
        self.filtro_ciudad_analisis.addItem("Todas las ciudades")
        self.filtro_ciudad_analisis.currentTextChanged.connect(self.actualizar_analisis_cartera)

        filtros_row2.addWidget(QLabel("Centro:"))
        filtros_row2.addWidget(self.filtro_centro_analisis)
        filtros_row2.addWidget(QLabel("Días:"))
        filtros_row2.addWidget(self.filtro_dias_analisis)
        filtros_row2.addWidget(QLabel("Ciudad:"))
        filtros_row2.addWidget(self.filtro_ciudad_analisis)
        filtros_row2.addStretch()

        # Botones de acción
        action_layout = QHBoxLayout()
        btn_actualizar = QPushButton("🔄 Actualizar")
        btn_actualizar.clicked.connect(self.actualizar_analisis_cartera)
        btn_actualizar.setObjectName("primary")

        btn_cargar_historial = QPushButton("📁 Cargar Historial")
        btn_cargar_historial.clicked.connect(self.cargar_historial_completo)
        btn_cargar_historial.setObjectName("primary")

        btn_reporte_carga = QPushButton("📋 Reporte de Carga")
        btn_reporte_carga.clicked.connect(self.mostrar_reporte_carga)

        btn_actualizar_incremental = QPushButton("🔄 Actualizar Historial")
        btn_actualizar_incremental.clicked.connect(self.actualizar_historial_incremental)

        action_layout.addWidget(btn_actualizar)
        action_layout.addWidget(btn_cargar_historial)
        action_layout.addStretch()
        action_layout.addWidget(btn_reporte_carga)
        action_layout.addWidget(btn_actualizar_incremental)

        # Agregar al layout principal
        filters_layout.addLayout(filtros_row1)
        filters_layout.addLayout(filtros_row2)
        filters_layout.addLayout(action_layout)
        scroll_layout.addWidget(filters_group)

        # ===== SELECTOR DE GRÁFICAS RESPONSIVE =====
        selector_group = QGroupBox("🎛️ Control de Gráficas")
        selector_layout = QVBoxLayout(selector_group)

        # Checkboxes para cada gráfica - EN GRID RESPONSIVO
        checkboxes_layout = QGridLayout()
        checkboxes_layout.setHorizontalSpacing(15)
        checkboxes_layout.setVerticalSpacing(8)
        
        self.graficas_checkboxes = {}

        graficas_config = [
            ("chart1", "📊 Distribución por Estado", 0, 0),
            ("chart2", "📈 Top 10 Clientes Mora", 0, 1), 
            ("chart3", "👥 Cartera por Vendedor", 0, 2),
            ("chart4", "💰 Condiciones de Pago", 1, 0),
            ("chart5", "📅 Evolución + Proyección", 1, 1),
            ("chart6", "📊 Concentración 20/80", 1, 2),
            ("chart7", "📈 Envejecimiento Detallado", 2, 0),
            ("chart8", "🏙️ Análisis Geográfico", 2, 1),
            ("chart9", "💰 Proyección por Crédito", 2, 2)
        ]

        for chart_id, chart_name, row, col in graficas_config:
            checkbox = QCheckBox(chart_name)
            checkbox.setChecked(True)
            checkbox.setStyleSheet("QCheckBox { color: #cbd5e1; font-size: 11px; padding: 4px; }")
            checkbox.toggled.connect(self.actualizar_visibilidad_graficas_compatible)
            self.graficas_checkboxes[chart_id] = checkbox
            checkboxes_layout.addWidget(checkbox, row, col)

        selector_layout.addLayout(checkboxes_layout)

        # Botones de acción
        botones_layout = QHBoxLayout()
        btn_todas = QPushButton("✅ Todas")
        btn_todas.clicked.connect(self.seleccionar_todas_graficas)
        btn_todas.setFixedHeight(25)

        btn_ninguna = QPushButton("❌ Ninguna") 
        btn_ninguna.clicked.connect(self.deseleccionar_todas_graficas)
        btn_ninguna.setFixedHeight(25)

        btn_aplicar = QPushButton("🔄 Aplicar")
        btn_aplicar.clicked.connect(self.actualizar_analisis_cartera)
        btn_aplicar.setObjectName("primary")
        btn_aplicar.setFixedHeight(25)

        botones_layout.addWidget(btn_todas)
        botones_layout.addWidget(btn_ninguna)
        botones_layout.addStretch()
        botones_layout.addWidget(btn_aplicar)

        selector_layout.addLayout(botones_layout)
        scroll_layout.addWidget(selector_group)

        # ===== MÉTRICAS RÁPIDAS =====
        metrics_group = QGroupBox("📈 Métricas Rápidas")
        metrics_layout = QHBoxLayout(metrics_group)
        
        self.metricas_analisis = {
            'total_cartera': MetricCard("CARTERA TOTAL", 0, "${:,.0f}"),
            'cartera_mora': MetricCard("CARTERA MORA", 0, "${:,.0f}"),
            'clientes_totales': MetricCard("TOTAL CLIENTES", 0),
            'condiciones_activas': MetricCard("CLIENTES EN MORA", 0)
        }
        
        for card in self.metricas_analisis.values():
            card.setMinimumWidth(180)  # Ancho mínimo responsivo
            card.setMaximumWidth(250)  # Ancho máximo responsivo
            metrics_layout.addWidget(card)
        
        scroll_layout.addWidget(metrics_group)
        
        # ===== GRÁFICAS PRINCIPALES - MANTENER TU ESTRUCTURA ACTUAL =====
        
        # Gráfica 1: Distribución por Estado + Condición
        self.chart1_group = QGroupBox("📊 Distribución por Estado y Condición de Pago")
        self.chart1_analisis_layout = QVBoxLayout(self.chart1_group)
        scroll_layout.addWidget(self.chart1_group)
        
        # Gráfica 2: Top Clientes Mora
        self.chart2_group = QGroupBox("📈 Top 10 Clientes con Mayor Mora")
        self.chart2_analisis_layout = QVBoxLayout(self.chart2_group)
        scroll_layout.addWidget(self.chart2_group)
        
        # Gráfica 3: Cartera por Vendedor + Condiciones
        self.chart3_group = QGroupBox("👥 Cartera por Vendedor y Condiciones")
        self.chart3_analisis_layout = QVBoxLayout(self.chart3_group)
        scroll_layout.addWidget(self.chart3_group)

        # Gráfica 4: Distribución por Condición de Pago
        self.chart4_group = QGroupBox("💰 Distribución por Condición de Pago")
        self.chart4_analisis_layout = QVBoxLayout(self.chart4_group)
        scroll_layout.addWidget(self.chart4_group)  
        
        # Gráfica 5: Evolución Histórica + Proyección
        self.chart5_group = QGroupBox("📈 Evolución Histórica (12M) + Proyección Vencimientos (4M)")
        self.chart5_analisis_layout = QVBoxLayout(self.chart5_group)
        scroll_layout.addWidget(self.chart5_group)

        # Gráfica 6: Concentración de Cartera
        self.chart6_group = QGroupBox("📊 Concentración de Cartera - Principio 20/80")
        self.chart6_analisis_layout = QVBoxLayout(self.chart6_group)
        scroll_layout.addWidget(self.chart6_group)
        
        # Gráfica 7: Análisis de Envejecimiento Detallado
        self.chart7_group = QGroupBox("📈 Análisis de Envejecimiento Detallado")
        self.chart7_analisis_layout = QVBoxLayout(self.chart7_group)
        scroll_layout.addWidget(self.chart7_group)
        
        # Gráfica 8: Análisis Geográfico
        self.chart8_group = QGroupBox("🏙️ Análisis Geográfico de Cartera")
        self.chart8_analisis_layout = QVBoxLayout(self.chart8_group)
        scroll_layout.addWidget(self.chart8_group)
        
        # Gráfica 9: Proyección por Tipo de Crédito
        self.chart9_group = QGroupBox("💰 Proyección por Tipo de Crédito - Vencimientos")
        self.chart9_analisis_layout = QVBoxLayout(self.chart9_group)
        scroll_layout.addWidget(self.chart9_group)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        self.tabs.addTab(widget, "📊 Análisis Cartera")
        
        # Cargar datos iniciales
        QTimer.singleShot(500, self.inicializar_analisis_cartera) 

    def actualizar_visibilidad_graficas_compatible(self):
        """Actualiza la visibilidad de las gráficas - VERSIÓN COMPATIBLE"""
        try:
            # Mapeo de checkboxes a grupos de gráficas
            chart_groups = {
                'chart1': self.chart1_group,
                'chart2': self.chart2_group,
                'chart3': self.chart3_group,
                'chart4': self.chart4_group,
                'chart5': self.chart5_group,
                'chart6': self.chart6_group,
                'chart7': self.chart7_group,
                'chart8': self.chart8_group,
                'chart9': self.chart9_group
            }
            
            for chart_id, group in chart_groups.items():
                checkbox = self.graficas_checkboxes.get(chart_id)
                if checkbox:
                    group.setVisible(checkbox.isChecked())
                    
            print("✅ Visibilidad de gráficas actualizada")
            
        except Exception as e:
            print(f"Error actualizando visibilidad de gráficas: {e}")
    
    def inicializar_analisis_cartera(self):
        """Inicializa los filtros y datos del análisis de cartera"""
        try:
            # Cargar vendedores disponibles
            vendedores_disponibles = self.auth_manager.get_available_vendedores()
            self.filtro_vendedor_analisis.clear()
            self.filtro_vendedor_analisis.addItem("Todos los vendedores")
            for vendedor in vendedores_disponibles:
                if vendedor != "Todos los vendedores":
                    self.filtro_vendedor_analisis.addItem(vendedor)
            
            # Cargar ciudades disponibles
            ciudades = self.db.obtener_ciudades()
            self.filtro_ciudad_analisis.clear()
            self.filtro_ciudad_analisis.addItem("Todas las ciudades")
            for _, ciudad in ciudades.iterrows():
                if ciudad['ciudad'] and ciudad['ciudad'] not in ["", "N/A"]:
                    self.filtro_ciudad_analisis.addItem(ciudad['ciudad'])
            
            # Actualizar análisis por primera vez
            self.actualizar_analisis_cartera()
            
        except Exception as e:
            print(f"Error inicializando análisis de cartera: {e}")

    def actualizar_analisis_cartera(self):
        """Actualiza todas las gráficas y métricas del análisis de cartera"""
        try:
            # Obtener datos filtrados
            datos_filtrados = self.obtener_datos_analisis_filtrados()
            
            # Actualizar métricas rápidas
            self.actualizar_metricas_analisis(datos_filtrados)
            
            # Actualizar gráficas
            self.actualizar_graficas_analisis(datos_filtrados)
            
        except Exception as e:
            print(f"Error actualizando análisis de cartera: {e}")

    def obtener_datos_analisis_filtrados(self):
        """Obtiene los datos de cartera aplicando los filtros seleccionados"""
        try:
            # Obtener cartera completa (ya viene filtrada por usuario)
            cartera = self.db.obtener_cartera_actual()
            
            # Aplicar filtros adicionales
            vendedor = self.filtro_vendedor_analisis.currentText()
            condicion = self.filtro_condicion_analisis.currentText()
            centro = self.filtro_centro_analisis.currentText()
            dias_filtro = self.filtro_dias_analisis.currentText()
            ciudad = self.filtro_ciudad_analisis.currentText()
            
            # Filtrar por vendedor
            if vendedor != "Todos los vendedores":
                cartera = cartera[cartera['nombre_vendedor'] == vendedor]
            
            # Filtrar por condición de pago
            if condicion != "Todas las condiciones":
                cartera = cartera[cartera['condicion_pago'] == condicion]
            
            # Filtrar por centro de operación
            if centro != "Todos los centros":
                cartera = cartera[cartera['centro_operacion'] == centro]
            
            # Filtrar por ciudad
            if ciudad != "Todas las ciudades":
                # Necesitamos unir con clientes para filtrar por ciudad
                clientes = self.db.obtener_clientes()
                cartera = cartera.merge(
                    clientes[['nit_cliente', 'ciudad']], 
                    on='nit_cliente', 
                    how='left'
                )
                cartera = cartera[cartera['ciudad_y'] == ciudad]
            
            # Filtrar por días vencidos
            if dias_filtro != "Todos los días":
                if dias_filtro == "0 días (Corriente)":
                    cartera = cartera[cartera['dias_vencidos'] == 0]
                elif dias_filtro == "1-30 días":
                    cartera = cartera[(cartera['dias_vencidos'] >= 1) & (cartera['dias_vencidos'] <= 30)]
                elif dias_filtro == "31-60 días":
                    cartera = cartera[(cartera['dias_vencidos'] >= 31) & (cartera['dias_vencidos'] <= 60)]
                elif dias_filtro == "61-90 días":
                    cartera = cartera[(cartera['dias_vencidos'] >= 61) & (cartera['dias_vencidos'] <= 90)]
                elif dias_filtro == "+90 días":
                    cartera = cartera[cartera['dias_vencidos'] > 90]
            
            return cartera
            
        except Exception as e:
            print(f"Error obteniendo datos filtrados: {e}")
            return pd.DataFrame()

    def actualizar_metricas_analisis(self, datos):
        """Actualiza las métricas rápidas del análisis - CLIENTES EN MORA DINÁMICO"""
        try:
            if datos.empty:
                for card in self.metricas_analisis.values():
                    card.update_value(0)
                return
            
            total_cartera = datos['total_cop'].sum()
            cartera_mora = datos[datos['dias_vencidos'] > 0]['total_cop'].sum()
            clientes_totales = datos['nit_cliente'].nunique()

            # ✅ CORRECCIÓN: Calcular CLIENTES EN MORA dinámicamente según filtros
            clientes_en_mora = datos[datos['dias_vencidos'] > 0]['nit_cliente'].nunique()
            
            self.metricas_analisis['total_cartera'].update_value(total_cartera, "${:,.0f}")
            self.metricas_analisis['cartera_mora'].update_value(cartera_mora, "${:,.0f}")
            self.metricas_analisis['clientes_totales'].update_value(clientes_totales)
            self.metricas_analisis['condiciones_activas'].update_value(clientes_en_mora)  # ✅ Ahora muestra clientes en mora
            
            print(f"📊 Métricas actualizadas: {clientes_totales} clientes totales, {clientes_en_mora} en mora")
            
        except Exception as e:
            print(f"Error actualizando métricas: {e}")

    def actualizar_graficas_analisis(self, datos):
        """Actualiza las gráficas del análisis de cartera - CON CONTROL DE VISIBILIDAD"""
        try:
            # Mapeo de gráficas y sus funciones
            graficas_config = [
                ('chart1', self.crear_grafica_distribucion_estado_condicion, self.chart1_analisis_layout),
                ('chart2', self.crear_grafica_top_clientes_mora, self.chart2_analisis_layout),
                ('chart3', self.crear_grafica_cartera_vendedor_condiciones, self.chart3_analisis_layout),
                ('chart4', self.crear_grafica_condiciones_pago, self.chart4_analisis_layout),
                ('chart5', self.crear_grafica_proyeccion_vencimientos_actual, self.chart5_analisis_layout),
                ('chart6', self.crear_grafica_concentracion_cartera, self.chart6_analisis_layout),
                ('chart7', self.crear_grafica_envejecimiento_detallado, self.chart7_analisis_layout),
                ('chart8', self.crear_grafica_analisis_geografico, self.chart8_analisis_layout),
                ('chart9', self.crear_grafica_proyeccion_credito, self.chart9_analisis_layout)
            ]
            
            for chart_id, crear_func, layout in graficas_config:
                # Limpiar gráfica anterior
                self.clear_layout(layout)
                
                # Verificar si la gráfica está activa
                checkbox = self.graficas_checkboxes.get(chart_id)
                if checkbox and not checkbox.isChecked():
                    # Gráfica desactivada - mostrar mensaje o dejar vacío
                    no_data_label = QLabel("Gráfica desactivada - Activa en el selector superior")
                    no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    no_data_label.setStyleSheet("color: #94a3b8; font-style: italic; padding: 40px; font-size: 12px;")
                    layout.addWidget(no_data_label)
                    continue  # Saltar creación de gráfica
                
                if datos.empty:
                    self.mostrar_mensaje_sin_datos(layout)
                    continue
                    
                try:
                    crear_func(datos)
                except Exception as e:
                    print(f"Error creando gráfica {chart_id}: {e}")
                    self.mostrar_error_grafica(layout, str(e))
                
        except Exception as e:
            print(f"Error actualizando gráficas de análisis: {e}")

    def crear_grafica_distribucion_estado_condicion(self, datos):
        """Crea gráfica de distribución por estado (SIMPLIFICADA - sin condiciones)"""
        try:
            if datos.empty:
                self.mostrar_mensaje_sin_datos(self.chart1_analisis_layout)
                return
            
            # SIMPLIFICADO: Solo por estado, sin condiciones
            categorias_estado = ['Corriente', '1-30 días', '31-60 días', '61-90 días', '+90 días']
            
            # Calcular valores por estado
            valores_estado = [
                datos[datos['dias_vencidos'] == 0]['total_cop'].sum(),
                datos[(datos['dias_vencidos'] >= 1) & (datos['dias_vencidos'] <= 30)]['total_cop'].sum(),
                datos[(datos['dias_vencidos'] >= 31) & (datos['dias_vencidos'] <= 60)]['total_cop'].sum(),
                datos[(datos['dias_vencidos'] >= 61) & (datos['dias_vencidos'] <= 90)]['total_cop'].sum(),
                datos[datos['dias_vencidos'] > 90]['total_cop'].sum()
            ]
            
            if not any(val > 0 for val in valores_estado):
                self.mostrar_mensaje_sin_datos(self.chart1_analisis_layout)
                return
            
            # Crear gráfica SIMPLIFICADA
            plt.style.use('dark_background')
            screen_size = QApplication.primaryScreen().availableSize()
            fig_width = max(8, screen_size.width() / 150)
            fig_height = max(4, screen_size.height() / 200)
            fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor='#1e293b', edgecolor='#334155')
            
            colors = ['#10b981', '#f59e0b', '#f97316', '#dc2626', '#991b1b']
            bars = ax.bar(categorias_estado, valores_estado, color=colors)
            
            ax.set_xlabel('Estado de Cartera', color='#cbd5e1', fontsize=12)
            ax.set_ylabel('Valor COP', color='#cbd5e1', fontsize=12)
            ax.set_title('Distribución por Estado de Cartera', 
                        fontsize=14, fontweight='bold', color='#e2e8f0', pad=20)
            ax.set_xticklabels(categorias_estado, color='#cbd5e1', fontsize=10)
            ax.tick_params(axis='y', colors='#cbd5e1', labelsize=10)
            
            # Formatear eje Y
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.1f}M' if x >= 1e6 else f'${x/1e3:.0f}K'))
            
            # Añadir etiquetas de valor
            for bar, valor in zip(bars, valores_estado):
                if valor > 0:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + max(valores_estado)*0.01,
                        f'${valor/1e6:.1f}M' if valor >= 1e6 else f'${valor/1e3:.0f}K',
                        ha='center', va='bottom', fontsize=9, color='white', fontweight='bold')
            
            # Ajustar diseño
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            canvas = FigureCanvas(fig)
            self.chart1_analisis_layout.addWidget(canvas)
            
        except Exception as e:
            print(f"Error creando gráfica de distribución simplificada: {e}")
            self.mostrar_error_grafica(self.chart1_analisis_layout, str(e))

    def crear_grafica_top_clientes_mora(self, datos):
        """Crea gráfica de top 10 clientes con mayor mora - ORDEN CORREGIDO"""
        try:
            # Filtrar solo clientes con mora
            datos_mora = datos[datos['dias_vencidos'] > 0]
            
            if datos_mora.empty:
                self.mostrar_mensaje_sin_datos(self.chart2_analisis_layout)
                return
            
            # Agrupar por cliente y sumar mora
            top_clientes = datos_mora.groupby('razon_social_cliente').agg({
                'total_cop': 'sum',
                'dias_vencidos': 'max'
            }).nlargest(10, 'total_cop')
            
            if top_clientes.empty:
                self.mostrar_mensaje_sin_datos(self.chart2_analisis_layout)
                return
            
            # ✅ CORRECCIÓN: Invertir el orden para que el mayor quede ARRIBA
            top_clientes = top_clientes.iloc[::-1]  # Esto invierte el DataFrame
            
            # Crear gráfica
            plt.style.use('dark_background')
            screen_size = QApplication.primaryScreen().availableSize()
            fig_width = max(8, screen_size.width() / 150)
            fig_height = max(4, screen_size.height() / 200)  # Más alta para mejor visualización
            fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor='#1e293b', edgecolor='#334155')
            
            clientes = [nombre[:20] + '...' if len(nombre) > 20 else nombre 
                    for nombre in top_clientes.index]
            valores = top_clientes['total_cop'].values
            
            colors = plt.cm.Reds(np.linspace(0.4, 0.8, len(clientes)))
            bars = ax.barh(clientes, valores, color=colors)
            
            # Añadir etiquetas de valor
            for bar, valor in zip(bars, valores):
                width = bar.get_width()
                ax.text(width + max(valores)*0.01, bar.get_y() + bar.get_height()/2,
                    f'${valor/1e6:.1f}M' if valor >= 1e6 else f'${valor/1e3:.0f}K',
                    ha='left', va='center', fontsize=9, color='white')
            
            ax.set_xlabel('Valor en Mora (COP)', color='#cbd5e1')
            ax.set_title('Top 10 Clientes con Mayor Mora', 
                        fontsize=12, fontweight='bold', color='#e2e8f0', pad=20)
            ax.tick_params(axis='x', colors='#cbd5e1')
            ax.tick_params(axis='y', colors='#cbd5e1')
            
            # Formatear eje X
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.0f}M' if x >= 1e6 else f'${x/1e3:.0f}K'))
            
            plt.tight_layout()
            
            canvas = FigureCanvas(fig)
            self.chart2_analisis_layout.addWidget(canvas)
            
        except Exception as e:
            print(f"Error creando gráfica de top clientes: {e}")
            self.mostrar_error_grafica(self.chart2_analisis_layout, str(e))

    def crear_grafica_cartera_vendedor_condiciones(self, datos):
        """Crea gráfica de cartera por vendedor - ORDEN CORREGIDO: mayor a menor"""
        try:
            if datos.empty:
                self.mostrar_mensaje_sin_datos(self.chart3_analisis_layout)
                return
            
            # USAR CONDICIONES REALES (sin clasificación inteligente)
            datos_reales = datos.copy()
            
            # Unir CO1 y CON como "CONTADO"
            datos_reales['condicion_display'] = datos_reales['condicion_pago'].apply(
                lambda x: 'CONTADO' if str(x).upper() in ['CO1', 'CON'] else str(x)
            )
            
            # Agrupar por vendedor y condición REAL
            agrupacion = datos_reales.groupby(['nombre_vendedor', 'condicion_display'])['total_cop'].sum().reset_index()
            
            # Pivot para tener vendedores como filas y condiciones REALES como columnas
            pivot_data = agrupacion.pivot(index='nombre_vendedor', columns='condicion_display', values='total_cop').fillna(0)
            
            if pivot_data.empty:
                self.mostrar_mensaje_sin_datos(self.chart3_analisis_layout)
                return
            
            # ✅ CORRECCIÓN: Ordenar por TOTAL de MAYOR a MENOR
            total_por_vendedor = pivot_data.sum(axis=1)
            pivot_data = pivot_data.loc[total_por_vendedor.sort_values(ascending=False).index]  # Mayor a menor
            
            # Limitar a las condiciones más importantes (top 6 por valor)
            condiciones_totales = pivot_data.sum().sort_values(ascending=False)
            condiciones_principales = condiciones_totales.head(6).index
            pivot_data = pivot_data[condiciones_principales]
            
            # Calcular total por vendedor y porcentajes
            total_por_vendedor = pivot_data.sum(axis=1)
            total_general = total_por_vendedor.sum()
            
            # Acortar nombres de vendedores si son muy largos
            vendedores = []
            for vendedor in pivot_data.index:
                if len(vendedor) > 15:
                    vendedores.append(vendedor[:12] + '...')
                else:
                    vendedores.append(vendedor)
            
            # Crear gráfica de barras apiladas
            plt.style.use('dark_background')
            screen_size = QApplication.primaryScreen().availableSize()
            fig_width = max(10, screen_size.width() / 120)
            fig_height = max(6, screen_size.height() / 150)
            fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor='#1e293b', edgecolor='#334155')
            
            condiciones_reales = pivot_data.columns
            
            # ✅ CORRECCIÓN DE COLORES: Contado diferente, 60D diferente
            # Nuevos colores - Contado en azul distintivo, 60D en naranja
            colors = ['#3b82f6', '#00B3B0', '#f59e0b', '#ef4444', '#8b5cf6', '#10b981']
            
            # Mapeo especial para asegurar que CONTADO y 60D tengan colores distintivos
            color_map = {}
            available_colors = colors.copy()
            
            # Asignar colores específicos a condiciones importantes
            for condicion in condiciones_reales:
                if 'CONTADO' in condicion:
                    color_map[condicion] = "#cdf507"  # Amarillo para CONTADO
                elif '60D' in condicion:
                    color_map[condicion] = '#f59e0b'  # Naranja para 60D
                elif '30D' in condicion:
                    color_map[condicion] = "#F706C3"  # Rosa para 30D
                elif '90D' in condicion:
                    color_map[condicion] = '#ef4444'  # Rojo para 90D
                else:
                    # Para otras condiciones, usar colores disponibles
                    if available_colors:
                        color_map[condicion] = available_colors.pop(0)
                    else:
                        color_map[condicion] = '#94a3b8'  # Gris por defecto
            
            bottom = np.zeros(len(vendedores))
            for i, condicion in enumerate(condiciones_reales):
                valores = pivot_data[condicion].values
                bar_color = color_map.get(condicion, colors[i % len(colors)])
                bars = ax.bar(vendedores, valores, bottom=bottom, label=condicion, color=bar_color)
                bottom += valores
            
            # AÑADIR MONTOS Y PORCENTAJES EN LA PARTE SUPERIOR DE CADA BARRA
            for i, (vendedor, total_vendedor) in enumerate(zip(vendedores, total_por_vendedor)):
                porcentaje_vendedor = (total_vendedor / total_general) * 100
                
                # Texto del monto total y porcentaje
                ax.text(i, total_vendedor + max(total_por_vendedor) * 0.02, 
                    f'${total_vendedor/1e6:.1f}M\n({porcentaje_vendedor:.1f}%)', 
                    ha='center', va='bottom', color='#e2e8f0', fontsize=8, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#1e293b', edgecolor='#00B3B0', alpha=0.8))
            
            ax.set_xlabel('Vendedor', color='#cbd5e1', fontsize=12)
            ax.set_ylabel('Valor COP', color='#cbd5e1', fontsize=12)
            ax.set_title('Cartera por Vendedor - Condiciones De Pago', 
                        fontsize=14, fontweight='bold', color='#e2e8f0', pad=20)
            
            # Rotar etiquetas de vendedores y ajustar tamaño
            ax.tick_params(axis='x', rotation=45, colors='#cbd5e1', labelsize=9)
            ax.tick_params(axis='y', colors='#cbd5e1', labelsize=10)
            
            # Leyenda compacta con condiciones reales
            ax.legend(facecolor='#1e293b', edgecolor='#334155', 
                    bbox_to_anchor=(1.05, 1), loc='upper left', 
                    fontsize=9, title='Condiciones', title_fontsize=10)
            
            # Formatear eje Y
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.0f}M' if x >= 1e6 else f'${x/1e3:.0f}K'))
            
            # Ajustar los límites del eje Y para dar espacio a las etiquetas
            ax.set_ylim(0, max(total_por_vendedor) * 1.15)
            
            # Ajustar diseño para que quepan las etiquetas
            plt.tight_layout()
            
            canvas = FigureCanvas(fig)
            self.chart3_analisis_layout.addWidget(canvas)
            
        except Exception as e:
            print(f"Error creando gráfica de vendedores con condiciones reales: {e}")
            self.mostrar_error_grafica(self.chart3_analisis_layout, str(e))

    def crear_grafica_condiciones_pago(self, datos):
        """Crea gráfica exclusiva de distribución por condición de pago - ORDEN CORREGIDO"""
        try:
            if datos.empty:
                self.mostrar_mensaje_sin_datos(self.chart4_analisis_layout)
                return
            
            # ✅ CORRECCIÓN: Unir CO1 y CON como "CONTADO"
            datos_modificados = datos.copy()
            datos_modificados['condicion_display'] = datos_modificados['condicion_pago'].apply(
                lambda x: 'CONTADO' if str(x).upper() in ['CO1', 'CON'] else str(x)
            )
            
            # Agrupar por condición de pago individual (sin clasificación)
            distribucion = datos_modificados.groupby('condicion_display').agg({
                'total_cop': 'sum',
                'nit_cliente': 'nunique'  # Contar clientes únicos
            }).sort_values('total_cop', ascending=False)  # Ya está ordenado de mayor a menor
            
            if distribucion.empty:
                self.mostrar_mensaje_sin_datos(self.chart4_analisis_layout)
                return
            
            # ✅ CORRECCIÓN: Invertir el orden para gráfica horizontal (mayor arriba)
            distribucion = distribucion.iloc[::-1]
            
            # Crear gráfica de barras horizontales
            plt.style.use('dark_background')
            screen_size = QApplication.primaryScreen().availableSize()
            fig_width = max(10, screen_size.width() / 120)
            fig_height = max(7, screen_size.height() / 130)
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(fig_width, fig_height), facecolor='#1e293b', 
                                        gridspec_kw={'height_ratios': [2, 1]})
            
            # TÍTULO CON MÁS ESPACIO
            fig.suptitle('Distribución por Condición de Pago - Mayor a Menor', 
                        fontsize=16, fontweight='bold', color='#e2e8f0', y=0.98)
            
            # GRÁFICA DE BARRAS HORIZONTALES (parte superior)
            condiciones = distribucion.index
            valores = distribucion['total_cop'].values
            clientes = distribucion['nit_cliente'].values
            total_cartera = distribucion['total_cop'].sum()
            total_clientes = distribucion['nit_cliente'].sum()
            
            colors = ['#00B3B0', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#10b981', '#f97316', '#84cc16', '#06b6d4']
            
            bars = ax1.barh(condiciones, valores, color=colors[:len(condiciones)])
            ax1.set_xlabel('Valor COP', color='#cbd5e1', fontsize=12)
            ax1.set_ylabel('Condición de Pago', color='#cbd5e1', fontsize=12)
            ax1.tick_params(axis='x', colors='#cbd5e1', labelsize=10)
            ax1.tick_params(axis='y', colors='#cbd5e1', labelsize=10)
            ax1.grid(True, alpha=0.3, axis='x')
            
            # Formatear eje X
            ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.1f}M' if x >= 1e6 else f'${x/1e3:.0f}K'))
            
            # Añadir etiquetas de valor en las barras
            for bar, valor, n_clientes in zip(bars, valores, clientes):
                width = bar.get_width()
                porcentaje = (valor / total_cartera) * 100
                ax1.text(width + max(valores)*0.01, bar.get_y() + bar.get_height()/2,
                        f'${valor/1e6:.1f}M\n({n_clientes} clientes)', 
                        ha='left', va='center', color='#e2e8f0', fontsize=9, fontweight='bold')
            
            # TABLA MEJORADA (parte inferior) - CON ESTILOS OSCUROS
            ax2.axis('off')  # Ocultar ejes de la tabla
            
            # Preparar datos de la tabla
            table_data = []
            for condicion, (valor, n_clientes) in distribucion.iterrows():
                porcentaje = (valor / total_cartera) * 100
                table_data.append([
                    condicion, 
                    f'${valor:,.0f}', 
                    f'{porcentaje:.1f}%',
                    f'{n_clientes}'
                ])
            
            # Agregar fila de TOTAL
            table_data.append([
                'TOTAL CARTERA', 
                f'${total_cartera:,.0f}', 
                '100.0%',
                f'{total_clientes}'
            ])
            
            # Crear tabla con estilos oscuros
            table = ax2.table(
                cellText=table_data,
                colLabels=['CONDICIÓN', 'VALOR COP', 'PORCENTAJE', 'N° CLIENTES'],
                cellLoc='center',
                loc='center',
                bbox=[0.05, 0.1, 0.9, 0.8]
            )
            
            # ESTILOS PARA LA TABLA (TEMA OSCURO)
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 1.8)
            
            # Colores de la tabla
            for i in range(len(table_data) + 1):  # +1 para los headers
                for j in range(4):
                    if i == 0:  # Headers
                        table[(i, j)].set_facecolor('#00B3B0')
                        table[(i, j)].set_text_props(color='white', fontweight='bold')
                    elif i == len(table_data):  # Fila de TOTAL
                        table[(i, j)].set_facecolor('#1e40af')
                        table[(i, j)].set_text_props(color='white', fontweight='bold')
                    else:  # Filas normales
                        table[(i, j)].set_facecolor('#334155')
                        table[(i, j)].set_text_props(color='#e2e8f0')
            
            # Bordes de la tabla
            for key, cell in table.get_celld().items():
                cell.set_edgecolor('#475569')
            
            # AJUSTAR MÁRGENES PARA EVITAR SUPERPOSICIÓN
            plt.subplots_adjust(top=0.92, bottom=0.08, left=0.1, right=0.95, hspace=0.3)
            
            canvas = FigureCanvas(fig)
            self.chart4_analisis_layout.addWidget(canvas)
            
        except Exception as e:
            print(f"Error creando gráfica de condiciones de pago: {e}")
            self.mostrar_error_grafica(self.chart4_analisis_layout, str(e))

    def crear_grafica_evolucion_morosidad(self, datos):
        """Crea gráfica de evolución de morosidad con datos REALES del historial"""
        try:
            # Limpiar gráfica anterior
            self.clear_layout(self.chart5_analisis_layout)

            if datos.empty:
                no_data_label = QLabel("No hay datos históricos suficientes para mostrar la evolución\n(Se necesitan al menos 2 meses de datos)")
                no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_data_label.setStyleSheet("color: #94a3b8; font-style: italic; padding: 40px; font-size: 12px;")
                self.chart5_analisis_layout.addWidget(no_data_label)
                return

            # Verificar que tenemos al menos 2 meses de datos
            if len(datos) < 2:
                no_data_label = QLabel(f"Solo hay {len(datos)} mes(es) de datos históricos\nSe necesitan al menos 2 meses para mostrar evolución")
                no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_data_label.setStyleSheet("color: #94a3b8; font-style: italic; padding: 40px; font-size: 12px;")
                self.chart5_analisis_layout.addWidget(no_data_label)
                return

            print(f"📈 Gráfica evolución: {len(datos)} meses de datos")

            # Crear gráfica
            plt.style.use('dark_background')
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), facecolor='#1e293b', 
                                        gridspec_kw={'height_ratios': [2, 1]})
            
            # GRÁFICA SUPERIOR: Evolución de cartera
            meses = [f"{mes[5:7]}/{mes[2:4]}" for mes in datos['mes']]
            cartera_total = datos['cartera_total'].values
            cartera_mora = datos['cartera_mora'].values
            
            # Líneas de evolución
            ax1.plot(meses, cartera_total, marker='o', linewidth=3, label='Cartera Total', color='#00B3B0', markersize=6)
            ax1.plot(meses, cartera_mora, marker='s', linewidth=3, label='Cartera en Mora', color='#ef4444', markersize=6)
            ax1.fill_between(meses, cartera_mora, alpha=0.3, color='#ef4444')
            
            ax1.set_ylabel('Valor COP', color='#cbd5e1', fontsize=12)
            ax1.set_title('Evolución de Cartera vs Morosidad (Últimos 6 Meses)', fontsize=14, fontweight='bold', color='#e2e8f0', pad=20)
            ax1.tick_params(axis='x', rotation=45, colors='#cbd5e1', labelsize=10)
            ax1.tick_params(axis='y', colors='#cbd5e1', labelsize=10)
            ax1.legend(facecolor='#1e293b', edgecolor='#334155', loc='upper left')
            ax1.grid(True, alpha=0.3)
            
            # Formatear eje Y
            ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.1f}M' if x >= 1e6 else f'${x/1e3:.0f}K'))
            
            # Añadir etiquetas de valor en los puntos
            for i, (mes, total, mora) in enumerate(zip(meses, cartera_total, cartera_mora)):
                ax1.annotate(f'${total/1e6:.1f}M', (mes, total), 
                            textcoords="offset points", xytext=(0,10), 
                            ha='center', va='bottom', color='#00B3B0', fontsize=8,
                            bbox=dict(boxstyle='round,pad=0.2', facecolor='#1e293b', alpha=0.8))
                
                if mora > 0:
                    ax1.annotate(f'${mora/1e6:.1f}M', (mes, mora), 
                                textcoords="offset points", xytext=(0,10), 
                                ha='center', va='bottom', color='#ef4444', fontsize=8,
                                bbox=dict(boxstyle='round,pad=0.2', facecolor='#1e293b', alpha=0.8))
            
            # GRÁFICA INFERIOR: Tasa de morosidad
            tasa_morosidad = (cartera_mora / cartera_total) * 100
            
            bars = ax2.bar(meses, tasa_morosidad, color='#f59e0b', alpha=0.8)
            ax2.set_ylabel('Tasa de Morosidad (%)', color='#cbd5e1', fontsize=12)
            ax2.set_xlabel('Mes', color='#cbd5e1', fontsize=12)
            ax2.tick_params(axis='x', rotation=45, colors='#cbd5e1', labelsize=10)
            ax2.tick_params(axis='y', colors='#cbd5e1', labelsize=10)
            ax2.grid(True, alpha=0.3, axis='y')
            
            # Añadir valores en las barras
            for bar, tasa in zip(bars, tasa_morosidad):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                        f'{tasa:.1f}%', ha='center', va='bottom', color='#e2e8f0', 
                        fontsize=9, fontweight='bold')
            
            # Línea de referencia (10% de morosidad)
            ax2.axhline(y=10, color='#dc2626', linestyle='--', alpha=0.7, linewidth=2, label='Límite 10%')
            ax2.legend(facecolor='#1e293b', edgecolor='#334155', loc='upper left')
            
            # Ajustar diseño
            plt.tight_layout()
            plt.subplots_adjust(top=0.92, hspace=0.4)
            
            canvas = FigureCanvas(fig)
            self.chart5_analisis_layout.addWidget(canvas)
            
        except Exception as e:
            print(f"Error creando gráfica de evolución de morosidad: {e}")
            self.mostrar_error_grafica(self.chart5_analisis_layout, str(e))

    def crear_grafica_proyeccion_vencimientos_actual(self, datos):
        """Crea gráfica combinada: histórico último año + proyección próximos 4 meses"""
        try:
            # Obtener datos históricos del último año (igual que el dashboard)
            datos_graficas = self.db.obtener_datos_graficas()
            evolucion_mensual = datos_graficas['evolucion_mensual']
            
            # Procesar datos de cartera actual para proyección futura
            hoy = datetime.now().date()
            datos['fecha_vencimiento'] = pd.to_datetime(datos['fecha_vencimiento'])
            datos_futuro = datos[datos['fecha_vencimiento'] >= pd.to_datetime(hoy)]
            
            # Crear proyección futura por mes
            proyeccion_futura = {}
            
            # Generar próximos 4 meses
            for i in range(4):
                mes_futuro = (hoy.replace(day=1) + timedelta(days=32*i)).replace(day=1)
                mes_nombre = mes_futuro.strftime('%b %Y')  # Ej: "Oct 2024"
                
                # Calcular cartera que vence en ese mes
                inicio_mes = mes_futuro
                fin_mes = (mes_futuro + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                
                datos_mes = datos_futuro[
                    (datos_futuro['fecha_vencimiento'] >= pd.to_datetime(inicio_mes)) & 
                    (datos_futuro['fecha_vencimiento'] <= pd.to_datetime(fin_mes))
                ]
                total_mes = datos_mes['total_cop'].sum()
                
                proyeccion_futura[mes_nombre] = total_mes
            
            # Preparar datos para la gráfica
            meses_combinados = []
            valores_combinados = []
            es_proyeccion = []  # Para diferenciar histórico vs proyección
            
            # Agregar datos históricos (igual que el dashboard)
            if evolucion_mensual:
                for item in evolucion_mensual:
                    mes_historico = datetime.strptime(item[0], '%Y-%m').strftime('%b %Y')
                    meses_combinados.append(mes_historico)
                    valores_combinados.append(item[1] or 0)  # cartera_total
                    es_proyeccion.append(False)
            
            # Agregar proyección futura
            for mes, valor in proyeccion_futura.items():
                if valor > 0:  # Solo agregar meses con valores
                    meses_combinados.append(mes)
                    valores_combinados.append(valor)
                    es_proyeccion.append(True)
            
            if not meses_combinados:
                no_data_label = QLabel("No hay datos históricos ni proyección disponible")
                no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_data_label.setStyleSheet("color: #94a3b8; font-style: italic; padding: 40px; font-size: 12px;")
                self.chart5_analisis_layout.addWidget(no_data_label)
                return
            
            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=(14, 7), facecolor='#1e293b', edgecolor='#334155')
            
            # Separar datos históricos y de proyección
            meses_historicos = [mes for i, mes in enumerate(meses_combinados) if not es_proyeccion[i]]
            valores_historicos = [val for i, val in enumerate(valores_combinados) if not es_proyeccion[i]]
            meses_proyeccion = [mes for i, mes in enumerate(meses_combinados) if es_proyeccion[i]]
            valores_proyeccion = [val for i, val in enumerate(valores_combinados) if es_proyeccion[i]]
            
            # GRÁFICA DE LÍNEA COMBINADA
            # Línea histórica (sólida)
            if meses_historicos:
                ax.plot(meses_historicos, valores_historicos, marker='o', linewidth=3, 
                    markersize=8, color='#00B3B0', markerfacecolor='#00B3B0',
                    markeredgecolor='white', markeredgewidth=2, label='Cartera Total Histórica')
            
            # Línea de proyección (punteada)
            if meses_proyeccion:
                ax.plot(meses_proyeccion, valores_proyeccion, marker='s', linewidth=3, 
                    markersize=8, color='#F57C00', markerfacecolor='#F57C00',
                    markeredgecolor='white', markeredgewidth=2, linestyle='--', 
                    label='Proyección Vencimientos')
            
            # Configurar ejes y título
            ax.set_ylabel('Valor COP (Millones)', color='#cbd5e1', fontsize=12)
            ax.set_xlabel('Periodo', color='#cbd5e1', fontsize=12)
            ax.set_title('Evolución Histórica + Proyección de Vencimientos', 
                        fontsize=14, fontweight='bold', color='#e2e8f0', pad=20)
            
            # Configurar ticks
            ax.tick_params(axis='x', rotation=45, colors='#cbd5e1', labelsize=10)
            ax.tick_params(axis='y', colors='#cbd5e1', labelsize=10)
            
            # Formatear eje Y SIEMPRE en millones
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.0f}M'))
            
            # ✅✅✅ AÑADIR VALORES EN CADA PUNTO - TODOS LOS PUNTOS ✅✅✅
            max_valor = max(valores_combinados) if valores_combinados else 0
            
            # Para puntos HISTÓRICOS (arriba del punto)
            for i, (mes, valor) in enumerate(zip(meses_historicos, valores_historicos)):
                if valor > 0:
                    ax.annotate(f'${valor/1e6:.1f}M', 
                            xy=(mes, valor), 
                            xytext=(0, 15),  # 15 puntos arriba
                            textcoords='offset points',
                            ha='center', va='bottom',
                            color='#00B3B0', fontsize=9, fontweight='bold',
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='#1e293b', 
                                    edgecolor='#00B3B0', alpha=0.9))
            
            # Para puntos de PROYECCIÓN (arriba del punto)
            for i, (mes, valor) in enumerate(zip(meses_proyeccion, valores_proyeccion)):
                if valor > 0:
                    ax.annotate(f'${valor/1e6:.1f}M', 
                            xy=(mes, valor), 
                            xytext=(0, 15),  # 15 puntos arriba
                            textcoords='offset points',
                            ha='center', va='bottom',
                            color='#F57C00', fontsize=9, fontweight='bold',
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='#1e293b', 
                                    edgecolor='#F57C00', alpha=0.9))
            
            # Cuadrícula y estilo
            ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
            ax.set_facecolor('#0f172a')
            
            # Ajustar límites del eje Y para dar espacio a las etiquetas
            if valores_combinados:
                ax.set_ylim(0, max(valores_combinados) * 1.4)  # Más espacio para etiquetas
            
            # Leyenda
            ax.legend(facecolor='#1e293b', edgecolor='#334155', loc='upper left')
            
            # Ajustar diseño
            plt.tight_layout()
            
            canvas = FigureCanvas(fig)
            self.chart5_analisis_layout.addWidget(canvas)
            
            print(f"📈 Gráfica combinada: {len(meses_historicos)}M histórico + {len(meses_proyeccion)}M proyección")
            
        except Exception as e:
            print(f"Error creando gráfica combinada histórico + proyección: {e}")
            self.mostrar_error_grafica(self.chart5_analisis_layout, str(e))

    def crear_grafica_concentracion_cartera(self, datos):
        """Muestra concentración de cartera con TOP clientes y análisis 20/80 PRÁCTICO - ORDEN CORREGIDO"""
        try:
            if datos.empty:
                self.mostrar_mensaje_sin_datos(self.chart6_analisis_layout)
                return
            
            # Calcular concentración por cliente
            cartera_por_cliente = datos.groupby(['nit_cliente', 'razon_social_cliente'])['total_cop'].sum().sort_values(ascending=False)
            total_cartera = cartera_por_cliente.sum()
            
            if total_cartera == 0:
                self.mostrar_mensaje_sin_datos(self.chart6_analisis_layout)
                return
            
            # Calcular principio 20/80
            acumulado = cartera_por_cliente.cumsum()
            porcentaje_acumulado = (acumulado / total_cartera) * 100
            
            # Encontrar punto 20/80
            clientes_20 = len(acumulado[acumulado <= total_cartera * 0.2])
            cartera_80 = acumulado.iloc[clientes_20] if clientes_20 < len(acumulado) else acumulado.iloc[-1]
            
            # TOP 15 clientes para análisis detallado
            top_clientes = cartera_por_cliente.head(15)
            
            plt.style.use('dark_background')
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), facecolor='#1e293b',
                                        gridspec_kw={'height_ratios': [2, 1]})
            
            # GRÁFICA SUPERIOR: Top 15 clientes con mayor cartera - ✅ CORREGIDO: mayor arriba
            # ✅ CORRECCIÓN: Invertir el orden para que el mayor quede ARRIBA
            top_clientes = top_clientes.iloc[::-1]  # Esto invierte el DataFrame
            
            clientes_nombres = [nombre[:20] + '...' if len(nombre) > 20 else nombre 
                            for nombre in top_clientes.index.get_level_values(1)]
            valores = top_clientes.values
            
            colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(clientes_nombres)))
            bars = ax1.barh(clientes_nombres, valores, color=colors)
            
            ax1.set_xlabel('Valor COP (Millones)', color='#cbd5e1', fontsize=12)
            ax1.set_title(f'Top 15 Clientes - Concentración de Cartera\n'
                        f'20% Clientes = {clientes_20} clientes controlan ${cartera_80/1e6:.1f}M ({cartera_80/total_cartera*100:.1f}%)', 
                        fontsize=14, fontweight='bold', color='#e2e8f0', pad=20)
            ax1.tick_params(axis='x', colors='#cbd5e1')
            ax1.tick_params(axis='y', colors='#cbd5e1')
            
            # Formatear eje X en millones
            ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.0f}M'))
            
            # Añadir valores y porcentajes
            for bar, valor, cliente_nombre in zip(bars, valores, clientes_nombres):
                width = bar.get_width()
                porcentaje = (valor / total_cartera) * 100
                ax1.text(width + max(valores)*0.01, bar.get_y() + bar.get_height()/2,
                        f'${valor/1e6:.1f}M\n({porcentaje:.1f}%)', 
                        ha='left', va='center', color='#e2e8f0', fontsize=8)
            
            # GRÁFICA INFERIOR: Análisis 20/80 detallado - ✅ CORREGIDO: mayor arriba
            categorias = [f'Top {clientes_20} Clientes\n({clientes_20/len(cartera_por_cliente)*100:.1f}%)', 
                        f'Resto {len(cartera_por_cliente)-clientes_20} Clientes']
            valores_80_20 = [cartera_80, total_cartera - cartera_80]
            colores = ['#00B3B0', '#475569']
            
            # ✅ CORRECCIÓN: Invertir orden para que mayor quede arriba
            categorias = categorias[::-1]
            valores_80_20 = valores_80_20[::-1]
            colores = colores[::-1]
            
            bars2 = ax2.bar(categorias, valores_80_20, color=colores, alpha=0.8)
            ax2.set_ylabel('Valor COP (Millones)', color='#cbd5e1', fontsize=12)
            ax2.set_title('Distribución 20/80 - Cartera Total', 
                        fontsize=12, fontweight='bold', color='#e2e8f0', pad=15)
            ax2.tick_params(axis='x', colors='#cbd5e1')
            ax2.tick_params(axis='y', colors='#cbd5e1')
            
            # Formatear eje Y en millones
            ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.0f}M'))
            
            # Añadir valores
            for bar, valor in zip(bars2, valores_80_20):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(valores_80_20)*0.01,
                        f'${valor/1e6:.1f}M\n({valor/total_cartera*100:.1f}%)', 
                        ha='center', va='bottom', color='#e2e8f0', fontsize=10, fontweight='bold')
            
            plt.tight_layout()
            canvas = FigureCanvas(fig)
            self.chart6_analisis_layout.addWidget(canvas)
            
            # ✅ INFORMACIÓN ADICIONAL EN CONSOLA
            print(f"📊 ANÁLISIS PARETO 20/80:")
            print(f"   Total clientes: {len(cartera_por_cliente)}")
            print(f"   Top {clientes_20} clientes controlan: ${cartera_80/1e6:.1f}M ({cartera_80/total_cartera*100:.1f}%)")
            print(f"   TOP 5 CLIENTES:")
            for i, ((nit, nombre), valor) in enumerate(cartera_por_cliente.head(5).items()):
                print(f"     {i+1}. {nombre} - ${valor/1e6:.1f}M ({(valor/total_cartera*100):.1f}%)")
            
        except Exception as e:
            print(f"Error creando gráfica de concentración: {e}")
            self.mostrar_error_grafica(self.chart6_analisis_layout, str(e))

    def crear_grafica_envejecimiento_detallado(self, datos):
        """Crea análisis detallado de envejecimiento usando cartera actual"""
        try:
            if datos.empty:
                self.mostrar_mensaje_sin_datos(self.chart7_analisis_layout)
                return
            
            # Rangos de envejecimiento
            rangos = {
                'Corriente (0 días)': (0, 0),
                '1-15 días': (1, 15),
                '16-30 días': (16, 30),
                '31-60 días': (31, 60),
                '61-90 días': (61, 90),
                '91-180 días': (91, 180),
                '181-365 días': (181, 365),
                '+365 días': (366, 9999)
            }
            
            # Calcular con datos actuales
            valores_rangos = {}
            clientes_rangos = {}
            
            for nombre, (min_dias, max_dias) in rangos.items():
                if max_dias == 9999:
                    datos_rango = datos[datos['dias_vencidos'] >= min_dias]
                else:
                    datos_rango = datos[(datos['dias_vencidos'] >= min_dias) & (datos['dias_vencidos'] <= max_dias)]
                
                valores_rangos[nombre] = datos_rango['total_cop'].sum()
                clientes_rangos[nombre] = datos_rango['nit_cliente'].nunique()
            
            # Filtrar rangos con valores
            rangos_filtrados = {k: v for k, v in valores_rangos.items() if v > 0}
            
            if not rangos_filtrados:
                self.mostrar_mensaje_sin_datos(self.chart7_analisis_layout)
                return
            
            plt.style.use('dark_background')
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), facecolor='#1e293b')
            
            # Gráfica 1: Barras por rango
            rangos_nombres = list(rangos_filtrados.keys())
            rangos_valores = list(rangos_filtrados.values())
            rangos_clientes = [clientes_rangos[k] for k in rangos_filtrados.keys()]
            
            colores = ['#10b981', '#84cc16', '#f59e0b', '#f97316', '#ef4444', '#dc2626', '#991b1b', '#7f1d1d']
            colores = colores[:len(rangos_nombres)]
            
            bars = ax1.bar(rangos_nombres, rangos_valores, color=colores, alpha=0.8)
            ax1.set_ylabel('Valor COP (Millones)', color='#cbd5e1', fontsize=12)
            ax1.set_title('Análisis Detallado de Envejecimiento - Cartera Actual', 
                        fontsize=14, fontweight='bold', color='#e2e8f0', pad=20)
            ax1.tick_params(axis='x', rotation=45, colors='#cbd5e1', labelsize=10)
            ax1.tick_params(axis='y', colors='#cbd5e1', labelsize=10)
            ax1.grid(True, alpha=0.3, axis='y')
            
            # SIEMPRE en millones
            ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.0f}M'))
            
            # Valores en millones
            for bar, valor, clientes in zip(bars, rangos_valores, rangos_clientes):
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(rangos_valores)*0.01,
                        f'${valor/1e6:.0f}M\n{clientes} clientes', 
                        ha='center', va='bottom', color='#e2e8f0', fontsize=8, fontweight='bold')
            
            # Gráfica 2: Distribución porcentual
            total_cartera = sum(rangos_valores)
            porcentajes = [v / total_cartera * 100 for v in rangos_valores]
            
            wedges, texts, autotexts = ax2.pie(porcentajes, labels=rangos_nombres, colors=colores, autopct='%1.1f%%',
                                            startangle=90, textprops={'color': '#e2e8f0', 'fontsize': 9})
            
            ax2.set_title('Distribución Porcentual por Antigüedad', 
                        fontsize=14, fontweight='bold', color='#e2e8f0', pad=20)
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            plt.tight_layout()
            canvas = FigureCanvas(fig)
            self.chart7_analisis_layout.addWidget(canvas)
            
        except Exception as e:
            print(f"Error creando gráfica de envejecimiento: {e}")
            self.mostrar_error_grafica(self.chart7_analisis_layout, str(e))

    def crear_grafica_analisis_geografico(self, datos):
        """Crea análisis geográfico - ORDEN CORREGIDO: Mayor a Menor en morosidad"""
        try:
            if datos.empty:
                self.mostrar_mensaje_sin_datos(self.chart8_analisis_layout)
                return
            
            # Obtener datos geográficos de clientes actuales
            clientes = self.db.obtener_clientes()
            datos_con_geografia = datos.merge(clientes[['nit_cliente', 'ciudad']], on='nit_cliente', how='left')
            
            if datos_con_geografia.empty:
                self.mostrar_mensaje_sin_datos(self.chart8_analisis_layout)
                return
            
            # Agrupar por ciudad con datos actuales
            cartera_por_ciudad = datos_con_geografia.groupby('ciudad').agg({
                'total_cop': 'sum',
                'nit_cliente': 'nunique',
                'dias_vencidos': 'mean'
            }).round(2)
            
            # ✅ CORRECCIÓN: Ordenar de mayor a menor para Top 15
            cartera_por_ciudad = cartera_por_ciudad.sort_values('total_cop', ascending=False).head(15)
            
            # ✅ CORRECCIÓN: Invertir para que mayor quede ARRIBA en gráfica horizontal
            cartera_por_ciudad = cartera_por_ciudad.iloc[::-1]
            
            if cartera_por_ciudad.empty:
                self.mostrar_mensaje_sin_datos(self.chart8_analisis_layout)
                return
            
            plt.style.use('dark_background')
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), facecolor='#1e293b')
            
            # Gráfica 1: Cartera por ciudad - ✅ CORREGIDA: mayor arriba
            ciudades = [ciudad[:20] + '...' if len(ciudad) > 20 else ciudad for ciudad in cartera_por_ciudad.index]
            valores = cartera_por_ciudad['total_cop'].values
            n_clientes = cartera_por_ciudad['nit_cliente'].values
            
            bars = ax1.barh(ciudades, valores, color='#3b82f6', alpha=0.8)
            ax1.set_xlabel('Valor COP (Millones)', color='#cbd5e1', fontsize=12)
            ax1.set_title('Top 15 Ciudades - Cartera Actual', fontsize=14, fontweight='bold', color='#e2e8f0')
            ax1.tick_params(axis='x', colors='#cbd5e1')
            ax1.tick_params(axis='y', colors='#cbd5e1')
            
            # SIEMPRE en millones
            ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.0f}M'))
            
            # Valores en millones
            for bar, valor, clientes in zip(bars, valores, n_clientes):
                ax1.text(bar.get_width() + max(valores)*0.01, bar.get_y() + bar.get_height()/2,
                        f'${valor/1e6:.0f}M\n{clientes} clientes', 
                        ha='left', va='center', color='#e2e8f0', fontsize=8)
            
            # Gráfica 2: Morosidad por ciudad - ✅ CORRECCIÓN: Mayor a Menor
            ciudades_mora = cartera_por_ciudad[cartera_por_ciudad['dias_vencidos'] > 0]
            if not ciudades_mora.empty:
                # ✅ CORRECCIÓN: Ordenar por días vencidos de MAYOR a MENOR
                ciudades_mora = ciudades_mora.sort_values('dias_vencidos', ascending=False)  # Mayor a menor
                
                ciudades_mora_nombres = [ciudad[:15] + '...' if len(ciudad) > 15 else ciudad for ciudad in ciudades_mora.index]
                promedios_mora = ciudades_mora['dias_vencidos'].values
                
                # ✅ CORRECCIÓN: Usar colores que reflejen la severidad (rojo para mayor mora)
                colors_mora = plt.cm.Reds(np.linspace(0.6, 0.9, len(ciudades_mora_nombres)))
                
                bars_mora = ax2.bar(ciudades_mora_nombres, promedios_mora, color=colors_mora, alpha=0.8)
                ax2.set_ylabel('Promedio Días Vencidos', color='#cbd5e1', fontsize=12)
                ax2.set_title('Promedio de Morosidad por Ciudad',  # Título actualizado
                            fontsize=14, fontweight='bold', color='#e2e8f0')
                ax2.tick_params(axis='x', rotation=45, colors='#cbd5e1', labelsize=9)
                ax2.tick_params(axis='y', colors='#cbd5e1')
                ax2.grid(True, alpha=0.3, axis='y')
                
                # ✅ CORRECCIÓN: Añadir valores en las barras
                for bar, valor in zip(bars_mora, promedios_mora):
                    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                            f'{valor:.0f} días', ha='center', va='bottom', 
                            color='#e2e8f0', fontsize=8, fontweight='bold',
                            bbox=dict(boxstyle='round,pad=0.2', facecolor='#1e293b', alpha=0.8))
            else:
                ax2.text(0.5, 0.5, 'No hay morosidad\nen las ciudades analizadas', 
                        ha='center', va='center', transform=ax2.transAxes, 
                        color='#94a3b8', fontsize=12, fontstyle='italic')
                ax2.set_xticks([])
                ax2.set_yticks([])
            
            plt.tight_layout()
            canvas = FigureCanvas(fig)
            self.chart8_analisis_layout.addWidget(canvas)
            
        except Exception as e:
            print(f"Error creando gráfica geográfica: {e}")
            self.mostrar_error_grafica(self.chart8_analisis_layout, str(e))

    def crear_grafica_proyeccion_credito(self, datos):
        """Crea proyección de vencimientos usando condiciones REALES - ORDEN: mayor a menor"""
        try:
            if datos.empty:
                self.mostrar_mensaje_sin_datos(self.chart9_analisis_layout)
                return
            
            # Usar condiciones REALES sin clasificación
            condiciones_reales = datos['condicion_pago'].unique()
            
            # Unir CO1 y CON como "CONTADO"
            datos_modificados = datos.copy()
            datos_modificados['condicion_display'] = datos_modificados['condicion_pago'].apply(
                lambda x: 'CONTADO' if str(x).upper() in ['CO1', 'CON'] else str(x)
            )
            
            # Calcular días hasta vencimiento
            hoy = datetime.now().date()
            datos_modificados['dias_hasta_vencimiento'] = (pd.to_datetime(datos_modificados['fecha_vencimiento']) - pd.to_datetime(hoy)).dt.days
            
            # Rangos de vencimiento MÁS AMPLIOS para evitar barras fuera de límites
            rangos_vencimiento = {
                'Vencido': (-9999, -1),
                'Vence este mes': (0, 30),
                '1-2 meses': (31, 60),
                '3-6 meses': (61, 180),
                '+6 meses': (181, 9999)
            }
            
            # Calcular proyección con condiciones REALES
            proyeccion = {}
            condiciones_unicas = datos_modificados['condicion_display'].unique()
            
            for condicion in condiciones_unicas:
                datos_condicion = datos_modificados[datos_modificados['condicion_display'] == condicion]
                proyeccion_condicion = {}
                
                for rango, (min_dias, max_dias) in rangos_vencimiento.items():
                    if max_dias == 9999:
                        datos_rango = datos_condicion[datos_condicion['dias_hasta_vencimiento'] >= min_dias]
                    else:
                        datos_rango = datos_condicion[
                            (datos_condicion['dias_hasta_vencimiento'] >= min_dias) & 
                            (datos_condicion['dias_hasta_vencimiento'] <= max_dias)
                        ]
                    
                    proyeccion_condicion[rango] = datos_rango['total_cop'].sum()
                
                proyeccion[condicion] = proyeccion_condicion
            
            # Crear DataFrame
            condiciones_display = list(proyeccion.keys())
            rangos = list(rangos_vencimiento.keys())
            
            df_proyeccion = pd.DataFrame(proyeccion).T.fillna(0)
            
            if df_proyeccion.empty:
                self.mostrar_mensaje_sin_datos(self.chart9_analisis_layout)
                return
            
            # FILTRAR condiciones con valor total > 0
            totales_por_condicion = df_proyeccion.sum(axis=1)
            condiciones_con_valor = totales_por_condicion[totales_por_condicion > 0].index
            df_proyeccion = df_proyeccion.loc[condiciones_con_valor]
            
            if df_proyeccion.empty:
                self.mostrar_mensaje_sin_datos(self.chart9_analisis_layout)
                return
            
            # ✅ CORRECCIÓN: Ordenar por TOTAL de MAYOR a MENOR
            totales_por_condicion = df_proyeccion.sum(axis=1)
            df_proyeccion = df_proyeccion.loc[totales_por_condicion.sort_values(ascending=False).index]  # Mayor a menor
            
            plt.style.use('dark_background')
            
            # TAMAÑO DINÁMICO basado en número de condiciones
            num_condiciones = len(df_proyeccion)
            fig_width = max(12, num_condiciones * 1.5)  # Ancho dinámico
            fig_height = 8  # Alto fijo suficiente
            
            fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor='#1e293b')
            
            # Colores para rangos
            colores = ['#ef4444', '#f59e0b', '#eab308', '#84cc16', '#10b981']
            
            # Gráfica de barras apiladas
            bottom = np.zeros(len(df_proyeccion))
            
            for i, rango in enumerate(rangos):
                if rango in df_proyeccion.columns:
                    valores = df_proyeccion[rango].values
                    bars = ax.bar(df_proyeccion.index, valores, bottom=bottom, label=rango, 
                                color=colores[i % len(colores)], alpha=0.8)
                    bottom += valores
            
            ax.set_ylabel('Valor COP', color='#cbd5e1', fontsize=12)
            ax.set_xlabel('Condición de Pago', color='#cbd5e1', fontsize=12)
            ax.set_title('Proyección de Vencimientos - Condiciones Reales',  # ✅ Título SIN cambios
                        fontsize=14, fontweight='bold', color='#e2e8f0', pad=20)
            
            # Rotar etiquetas para mejor visualización
            ax.tick_params(axis='x', rotation=45, colors='#cbd5e1', labelsize=10)
            ax.tick_params(axis='y', colors='#cbd5e1', labelsize=10)
            
            # Leyenda compacta
            ax.legend(facecolor='#1e293b', edgecolor='#334155', 
                    bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
            
            ax.grid(True, alpha=0.3, axis='y')
            
            # Formatear eje Y para evitar números muy grandes
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.0f}M' if x >= 1e6 else f'${x/1e3:.0f}K'))
            
            # Calcular totales y AJUSTAR LÍMITES DEL EJE Y
            totales = df_proyeccion.sum(axis=1)
            max_total = totales.max()
            
            # Añadir márgenes para las etiquetas (15% del máximo)
            ax.set_ylim(0, max_total * 1.15)
            
            # Añadir valores totales en millones (EVITAR SUPERPOSICIÓN)
            for i, (condicion, total) in enumerate(zip(df_proyeccion.index, totales)):
                if total > 0:
                    # Posición vertical ajustada para evitar superposición
                    y_pos = total + (max_total * 0.02)  # Solo 2% de margen
                    
                    ax.text(i, y_pos, f'${total/1e6:.1f}M', 
                        ha='center', va='bottom', color='#e2e8f0', fontsize=9, fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='#1e293b', alpha=0.8))
            
            # Ajustar diseño para que quepan todas las etiquetas
            plt.tight_layout()
            
            canvas = FigureCanvas(fig)
            self.chart9_analisis_layout.addWidget(canvas)
            
        except Exception as e:
            print(f"Error creando gráfica de proyección con condiciones reales: {e}")
            self.mostrar_error_grafica(self.chart9_analisis_layout, str(e))

    def mostrar_mensaje_sin_datos(self, layout):
        """Muestra mensaje cuando no hay datos"""
        label = QLabel("No hay datos para mostrar con los filtros actuales")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #94a3b8; font-style: italic; padding: 40px; font-size: 14px;")
        layout.addWidget(label)

    def mostrar_error_grafica(self, layout, mensaje_error):
        """Muestra mensaje de error en la gráfica"""
        label = QLabel(f"Error al crear gráfica:\n{mensaje_error}")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #ef4444; padding: 40px; font-size: 12px;")
        layout.addWidget(label)

    def clasificar_condicion_pago(self, condicion):
        """Clasifica las condiciones de pago según la definición de ALPAPEL"""
        condicion = str(condicion).upper().strip()
        
        # CONTADO
        if condicion in ['CON', 'CO1']:
            return 'CONTADO'
        
        # CRÉDITO CORTO
        elif condicion in ['10D', '15D', '30D']:
            return 'CRÉDITO CORTO'
        
        # CRÉDITO MEDIO  
        elif condicion in ['45D', '60D']:
            return 'CRÉDITO MEDIO'
        
        # CRÉDITO LARGO
        elif condicion in ['75D', '90D']:
            return 'CRÉDITO LARGO'
        
        # SIN CUPO
        elif condicion == 'NC':
            return 'SIN CUPO'
        
        # Por defecto
        else:
            return 'OTRAS CONDICIONES'

    def exportar_analisis_cartera(self):
        """Exporta el análisis actual a Excel"""
        try:
            datos = self.obtener_datos_analisis_filtrados()
            
            if datos.empty:
                QMessageBox.information(self, "Exportar", "No hay datos para exportar con los filtros actuales.")
                return
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Guardar reporte de análisis", "analisis_cartera.xlsx", "Excel Files (*.xlsx)"
            )
            
            if file_path:
                # Crear un Excel con múltiples hojas
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    # Hoja principal con datos
                    datos.to_excel(writer, sheet_name='Datos Filtrados', index=False)
                    
                    # Hoja con resumen por vendedor
                    resumen_vendedor = datos.groupby('nombre_vendedor').agg({
                        'total_cop': 'sum',
                        'nit_cliente': 'nunique',
                        'dias_vencidos': 'mean'
                    }).round(2)
                    resumen_vendedor.to_excel(writer, sheet_name='Resumen por Vendedor')
                    
                    # Hoja con resumen por condición
                    resumen_condicion = datos.groupby('condicion_pago').agg({
                        'total_cop': 'sum',
                        'nit_cliente': 'nunique'
                    })
                    resumen_condicion.to_excel(writer, sheet_name='Resumen por Condición')
                
                QMessageBox.information(self, "Éxito", f"Reporte exportado correctamente a:\n{file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar reporte: {str(e)}")

    def cargar_historial_completo(self):
        """Inicia la carga masiva del historial completo"""
        try:
            reply = QMessageBox.question(
                self, 
                "Cargar Historial Completo",
                "¿Estás seguro de cargar TODO el historial de cartera?\n\n"
                "Esto procesará todos los archivos en:\n"
                "CARTERA DIARIA/2025/...\n"
                "CARTERA DIARIA/2026/...\n\n"
                "Puede tomar varios minutos.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Mostrar diálogo de progreso simple
                self.progress_dialog = QProgressDialog("Cargando historial completo...", None, 0, 0, self)
                self.progress_dialog.setWindowTitle("Cargando Historial")
                self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
                self.progress_dialog.show()
                
                # Ejecutar en hilo separado para no bloquear la UI
                QTimer.singleShot(100, self.ejecutar_carga_historial)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error iniciando carga: {str(e)}")

    def ejecutar_carga_historial(self):
        """Ejecuta la carga del historial (llamado con timer para no bloquear UI)"""
        try:
            success, message = self.db.cargar_historial_completo()
            
            # Cerrar el diálogo de progreso
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.close()
            
            if success:
                QMessageBox.information(self, "Carga Completada", message)
                # Actualizar análisis con nuevo historial
                self.actualizar_analisis_cartera()
            else:
                QMessageBox.warning(self, "Carga con Errores", message)
                
        except Exception as e:
            # Cerrar el diálogo de progreso en caso de error
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.close()
            QMessageBox.critical(self, "Error", f"Error en carga: {str(e)}")

    def ejecutar_carga_historial(self):
        """Ejecuta la carga del historial (llamado con timer para no bloquear UI)"""
        try:
            success, message = self.db.cargar_historial_completo()
            
            # ⬇️⬇️⬇️ VERIFICAR RESULTADOS DE LA CARGA ⬇️⬇️⬇️
            if success:
                resumen = self.db.verificar_historial_cargado()
                if not resumen.empty:
                    total_registros = resumen.iloc[0]['total_registros']
                    dias_cargados = resumen.iloc[0]['dias_cargados']
                    fecha_min = resumen.iloc[0]['fecha_minima']
                    fecha_max = resumen.iloc[0]['fecha_maxima']
                    
                    print(f"📊 RESUMEN HISTORIAL CARGADO:")
                    print(f"   📁 Total registros: {total_registros:,}")
                    print(f"   📅 Días cargados: {dias_cargados}")
                    print(f"   🗓️  Rango fechas: {fecha_min} a {fecha_max}")
            
            # ⬆️⬆️⬆️ FIN DEL NUEVO CÓDIGO ⬆️⬆️⬆️
            
            # Cerrar el diálogo de progreso
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.close()
            
            if success:
                QMessageBox.information(self, "Carga Completada", message)
                # Actualizar análisis con nuevo historial
                self.actualizar_analisis_cartera()
            else:
                QMessageBox.warning(self, "Carga con Errores", message)
                
        except Exception as e:
            # Cerrar el diálogo de progreso en caso de error
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.close()
            QMessageBox.critical(self, "Error", f"Error en carga: {str(e)}")

    def create_analisis_gestion_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(10)
        
        # Panel de progreso de gestión (NUEVO)
        progreso_group = QGroupBox("📈 Progreso de Gestión Mensual")
        progreso_layout = QHBoxLayout()
        
        self.progreso_gestion = ProgressCard("Progreso General", 0, 0)
        self.progreso_mora = ProgressCard("Clientes en Mora Gestionados", 0, 0)
        
        progreso_layout.addWidget(self.progreso_gestion)
        progreso_layout.addWidget(self.progreso_mora)
        progreso_group.setLayout(progreso_layout)
        scroll_layout.addWidget(progreso_group)
        
        # Métricas de gestión mensual
        metrics_group = QGroupBox("📊 Métricas de Gestión Mensual")
        metrics_layout = QHBoxLayout()
        
        self.metricas_gestion = {
            'total_gestiones': MetricCard("TOTAL GESTIONES", 0),
            'clientes_unicos': MetricCard("CLIENTES ÚNICOS", 0),
            'tasa_contacto': MetricCard("TASA CONTACTO", 0, "{:.1f}%"),
            'promesas_generadas': MetricCard("PROMESAS", 0)
        }
        
        for card in self.metricas_gestion.values():
            metrics_layout.addWidget(card)
        
        metrics_group.setLayout(metrics_layout)
        scroll_layout.addWidget(metrics_group)
        
        # Gráficas de analytics
        analytics_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Gráfica 1: Efectividad por resultado (BARRAS HORIZONTALES)
        efectividad_widget = QWidget()
        efectividad_layout = QVBoxLayout(efectividad_widget)
        efectividad_title = QLabel("📊 Distribución de Resultados por Categoría")
        efectividad_title.setObjectName("section_title")
        efectividad_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        efectividad_layout.addWidget(efectividad_title)
        self.efectividad_canvas = None
        self.efectividad_layout = QVBoxLayout()
        efectividad_layout.addLayout(self.efectividad_layout)
        analytics_splitter.addWidget(efectividad_widget)
        
        # Gráfica 2: Evolución diaria
        evolucion_widget = QWidget()
        evolucion_layout = QVBoxLayout(evolucion_widget)
        evolucion_title = QLabel("📈 Evolución Diaria de Gestiones")
        evolucion_title.setObjectName("section_title")
        evolucion_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        evolucion_layout.addWidget(evolucion_title)
        self.evolucion_canvas = None
        self.evolucion_layout = QVBoxLayout()
        evolucion_layout.addLayout(self.evolucion_layout)
        analytics_splitter.addWidget(evolucion_widget)
        
        # NUEVA GRÁFICA 3: Evolución Histórica Simple
        historica_widget = QWidget()
        historica_layout = QVBoxLayout(historica_widget)
        historica_title = QLabel("📅 Evolución Histórica de Gestiones (Últimos 12 Meses)")
        historica_title.setObjectName("section_title")
        historica_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        historica_layout.addWidget(historica_title)
        self.historica_canvas = None
        self.historica_layout = QVBoxLayout()
        historica_layout.addLayout(self.historica_layout)
        analytics_splitter.addWidget(historica_widget)
        
        # Ajustar tamaños del splitter para las 3 gráficas
        analytics_splitter.setSizes([300, 300, 300])
        scroll_layout.addWidget(analytics_splitter)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        self.tabs.addTab(widget, "📊 Análisis De Gestión")

    def actualizar_resultados_gestion(self):
        self.resultado.clear()
        
        resultados = [
            "💰 COMPROMISO DE PAGO",
            "1. Promesa de Pago Total (Fecha/Monto)",
            "2. Promesa de Pago Parcial (Fecha/Monto)",
            "3. Acuerdo de Pago Formalizado (Cuotas)", 
            "4. Pago Efectuado / Cobro Exitoso",
            "",
            "📞 CONTACTO Y LOCALIZACIÓN",
            "5. Contacto Exitoso (Titular)",
            "6. Contacto con Tercero (Informó/Transmitió mensaje)",
            "7. Dejó Mensaje / Correo de Voz",
            "8. No Contesta / Ocupado",
            "9. Número Erróneo / Inexistente",
            "10. Email/Mensaje Enviado",
            "",
            "⚠️ DIFICULTAD Y RECHAZO",
            "11. Disputa / Reclamo de Facturación",
            "12. Problema de Servicio (Pendiente de Resolver)",
            "13. Negativa de Pago (Dificultad temporal)",
            "14. Negativa de Pago (Rechazo definitivo)",
            "15. Quiebra / Insolvencia Confirmada", 
            "16. Cliente Inactivo / Ilocalizable",
            "",
            "🔄 SEGUIMIENTO Y ACCIONES INTERNAS",
            "17. Necesita Escalación (A Legal/Supervisión)",
            "18. Enviar Documentación Solicitada (Factura/Extracto)",
            "19. Agendar Nueva Llamada / Cita",
            "20. Datos Verificados / Actualizados",
            "21. Gestión No Finalizada (Reintentar pronto)"
        ]
        
        for resultado in resultados:
            self.resultado.addItem(resultado)
    
    def load_data(self):
        """Carga todos los datos con manejo de errores"""
        try:
            print("🔄 EJECUTANDO CARGA AUTOMÁTICA DE DATOS...")
            
            # Cargar en orden secuencial
            self.actualizar_dashboard()
            QApplication.processEvents()
            
            self.actualizar_lista_clientes() 
            QApplication.processEvents()
            
            self.actualizar_cartera()
            QApplication.processEvents()
            
            self.load_clientes_data()
            QApplication.processEvents()
            
            self.actualizar_analytics()
            QApplication.processEvents()
            
            self.cargar_filtros()
            QApplication.processEvents()
            
            print("✅ CARGA AUTOMÁTICA COMPLETADA - Datos visibles")
            
        except Exception as e:
            print(f"❌ Error en carga automática: {e}")

    def cargar_filtros(self):
        try:
            # Obtener vendedores disponibles según el usuario
            vendedores_disponibles = self.auth_manager.get_available_vendedores()
            
            # Limpiar combos
            self.filtro_vendedor_cartera.clear()
            self.filtro_vendedor_clientes.clear()
            
            # Cargar vendedores disponibles
            for vendedor in vendedores_disponibles:
                self.filtro_vendedor_cartera.addItem(vendedor)
                self.filtro_vendedor_clientes.addItem(vendedor)
            
            # Cargar vendedores para análisis de cartera (si existe)
            if hasattr(self, 'filtro_vendedor_analisis'):
                self.filtro_vendedor_analisis.clear()
                self.filtro_vendedor_analisis.addItem("Todos los vendedores")
                for vendedor in vendedores_disponibles:
                    if vendedor != "Todos los vendedores":
                        self.filtro_vendedor_analisis.addItem(vendedor)  
                                  
            # Si el usuario es comercial, seleccionar automáticamente su vendedor
            if self.auth_manager.current_user['rol'] in ['comercial', 'consulta']:
                vendedor_usuario = self.auth_manager.current_user.get('vendedor_asignado')
                if vendedor_usuario:
                    index = self.filtro_vendedor_cartera.findText(vendedor_usuario)
                    if index >= 0:
                        self.filtro_vendedor_cartera.setCurrentIndex(index)
                        self.filtro_vendedor_clientes.setCurrentIndex(index)
            
            # Cargar ciudades
            ciudades = self.db.obtener_ciudades()
            self.filtro_ciudad_cartera.clear()
            self.filtro_ciudad_cartera.addItem("Todas las ciudades")
            self.filtro_ciudad_clientes.clear()
            self.filtro_ciudad_clientes.addItem("Todas las ciudades")
            
            for _, ciudad in ciudades.iterrows():
                if ciudad['ciudad']:
                    self.filtro_ciudad_cartera.addItem(ciudad['ciudad'])
                    self.filtro_ciudad_clientes.addItem(ciudad['ciudad'])
                    
        except Exception as e:
            print(f"Error cargando filtros: {e}")

    def actualizar_dashboard(self):
        try:
            metricas = self.db.obtener_metricas_principales()
            
            self.metric_cards['cartera_total'].update_value(metricas['cartera_total'], "${:,.0f}")
            self.metric_cards['cartera_mora'].update_value(metricas['cartera_mora'], "${:,.0f}")
            self.metric_cards['clientes_mora'].update_value(metricas['clientes_mora'])
            self.metric_cards['gestiones_mes'].update_value(metricas['gestiones_mes'])
            
            self.actualizar_graficas()
            
        except Exception as e:
            print(f"Error actualizando dashboard: {e}")

    def actualizar_graficas(self):
        try:
            datos = self.db.obtener_datos_graficas()
            proyeccion = self.db.obtener_proyeccion_vencimientos()
            
            # Limpiar gráficas anteriores
            self.clear_layout(self.chart1_layout)
            self.clear_layout(self.chart2_layout)
            self.clear_layout(self.chart3_layout)
            
            plt.style.use('dark_background')
            fig_params = {'facecolor': '#1e293b', 'edgecolor': '#334155'}
            
            # Gráfica 1: Distribución por estado
            if datos['distribucion_estado'] and any(val > 0 for val in datos['distribucion_estado']):
                fig1, ax1 = plt.subplots(figsize=(6, 4), **fig_params)
                categorias = ['Corriente', '1-30 días', '31-60 días', '61-90 días', '+90 días']
                valores = [datos['distribucion_estado'][i] or 0 for i in range(5)]
                
                colors = ['#10b981', '#f59e0b', '#f97316', '#dc2626', '#991b1b']
                bars = ax1.bar(categorias, valores, color=colors)
                ax1.set_title('Distribución de Cartera por Estado', fontsize=12, fontweight='bold', color='#e2e8f0')
                ax1.set_ylabel('Valor COP', color='#cbd5e1')
                ax1.tick_params(axis='x', rotation=45, colors='#cbd5e1')
                ax1.tick_params(axis='y', colors='#cbd5e1')
                
                ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.0f}M' if x >= 1e6 else f'${x/1e3:.0f}K'))
                
                for bar, valor in zip(bars, valores):
                    if valor > 0:
                        text_val = f'${valor/1e6:.1f}M' if valor >= 1e6 else f'${valor/1e3:.0f}K'
                        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(valores)*0.01,
                                text_val, ha='center', va='bottom', color='#e2e8f0', fontsize=8)
                
                plt.tight_layout()
                canvas1 = FigureCanvas(fig1)
                self.chart1_layout.addWidget(canvas1)
            else:
                no_data_label = QLabel("No hay datos para mostrar la distribución")
                no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_data_label.setStyleSheet("color: #94a3b8; font-style: italic; padding: 40px;")
                self.chart1_layout.addWidget(no_data_label)
            
            # Gráfica 2: Top clientes con mora
            if datos['top_clientes_mora'] and any(item[1] > 0 for item in datos['top_clientes_mora']):
                fig2, ax2 = plt.subplots(figsize=(6, 4), **fig_params)
                clientes = [item[0][:20] + '...' if len(item[0]) > 20 else item[0] for item in datos['top_clientes_mora']]
                valores = [item[1] for item in datos['top_clientes_mora']]
                
                colors = ['#dc2626', '#ef4444', '#f87171', '#fca5a5', '#fecaca']
                bars = ax2.barh(clientes, valores, color=colors[:len(clientes)])
                ax2.set_title('Top 10 Clientes con Mayor Mora', fontsize=12, fontweight='bold', color='#e2e8f0')
                ax2.set_xlabel('Valor COP', color='#cbd5e1')
                ax2.tick_params(axis='x', colors='#cbd5e1')
                ax2.tick_params(axis='y', colors='#cbd5e1')
                
                ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.0f}M' if x >= 1e6 else f'${x/1e3:.0f}K'))
                
                for bar, valor in zip(bars, valores):
                    text_val = f'${valor/1e6:.1f}M' if valor >= 1e6 else f'${valor/1e3:.0f}K'
                    ax2.text(bar.get_width() + max(valores)*0.01, bar.get_y() + bar.get_height()/2,
                            text_val, ha='left', va='center', color='#e2e8f0', fontsize=8)
                
                plt.tight_layout()
                canvas2 = FigureCanvas(fig2)
                self.chart2_layout.addWidget(canvas2)
            else:
                no_data_label = QLabel("No hay clientes con mora para mostrar")
                no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_data_label.setStyleSheet("color: #94a3b8; font-style: italic; padding: 40px;")
                self.chart2_layout.addWidget(no_data_label)
            
            # Gráfica 3: Evolución mensual con proyección
            if datos['evolucion_mensual'] or proyeccion:
                fig3, ax3 = plt.subplots(figsize=(6, 4), **fig_params)
                
                # Datos históricos
                if datos['evolucion_mensual']:
                    meses_hist = [item[0] for item in datos['evolucion_mensual']]
                    cartera_total_hist = [item[1] or 0 for item in datos['evolucion_mensual']]
                    cartera_mora_hist = [item[2] or 0 for item in datos['evolucion_mensual']]
                    
                    meses_formateados = [f"{mes[5:7]}/{mes[2:4]}" for mes in meses_hist]
                    
                    ax3.plot(meses_formateados, cartera_total_hist, marker='o', linewidth=2, 
                            label='Cartera Total (Real)', color='#3b82f6')
                    ax3.plot(meses_formateados, cartera_mora_hist, marker='s', linewidth=2, 
                            label='Cartera en Mora (Real)', color='#ef4444')
                
                # Proyección futura
                if proyeccion:
                    meses_proy = [item[0] for item in proyeccion]
                    cartera_total_proy = [item[1] or 0 for item in proyeccion]
                    cartera_mora_proy = [item[2] or 0 for item in proyeccion]
                    
                    meses_proy_formateados = [f"{mes[5:7]}/{mes[2:4]}" for mes in meses_proy]
                    
                    ax3.plot(meses_proy_formateados, cartera_total_proy, marker='o', linewidth=2, 
                            linestyle='--', label='Cartera Total (Proy)', color='#60a5fa')
                    ax3.plot(meses_proy_formateados, cartera_mora_proy, marker='s', linewidth=2, 
                            linestyle='--', label='Cartera en Mora (Proy)', color='#fca5a5')
                
                ax3.set_title('Evolución Mensual + Proyección 3M', fontsize=12, fontweight='bold', color='#e2e8f0')
                ax3.set_ylabel('Valor COP', color='#cbd5e1')
                ax3.tick_params(axis='x', rotation=45, colors='#cbd5e1')
                ax3.tick_params(axis='y', colors='#cbd5e1')
                ax3.legend(facecolor='#1e293b', edgecolor='#334155')
                ax3.grid(True, alpha=0.3)
                
                ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.0f}M' if x >= 1e6 else f'${x/1e3:.0f}K'))
                
                plt.tight_layout()
                canvas3 = FigureCanvas(fig3)
                self.chart3_layout.addWidget(canvas3)
            else:
                no_data_label = QLabel("No hay datos para mostrar evolución")
                no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_data_label.setStyleSheet("color: #94a3b8; font-style: italic; padding: 40px;")
                self.chart3_layout.addWidget(no_data_label)
            
        except Exception as e:
            print(f"Error actualizando gráficas: {e}")
            # Mostrar mensaje de error en las gráficas
            error_label = QLabel(f"Error cargando gráficas: {str(e)}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("color: #ef4444; padding: 40px;")
            self.chart1_layout.addWidget(error_label)

    # === MÉTODOS FALTANTES IMPLEMENTADOS ===
    
    def filtrar_cartera(self):
        """Filtra la cartera según los criterios seleccionados"""
        try:
            texto_busqueda = self.buscar_cartera_input.text().strip()
            vendedor = self.filtro_vendedor_cartera.currentText()
            ciudad = self.filtro_ciudad_cartera.currentText()
            dias_filtro = self.filtro_dias_vencidos.currentText()
            
            # Convertir filtro de días a rangos
            dias_min = None
            dias_max = None
            
            if dias_filtro == "0 días (Corriente)":
                dias_min = 0
                dias_max = 0
            elif dias_filtro == "1-30 días":
                dias_min = 1
                dias_max = 30
            elif dias_filtro == "31-60 días":
                dias_min = 31
                dias_max = 60
            elif dias_filtro == "61-90 días":
                dias_min = 61
                dias_max = 90
            elif dias_filtro == "+90 días":
                dias_min = 91
                dias_max = None
            
            # Aplicar filtros
            if texto_busqueda:
                df_filtrado = self.db.buscar_cartera(texto_busqueda)
            else:
                df_filtrado = self.db.filtrar_cartera(
                    vendedor if vendedor != "Todos los vendedores" else None,
                    ciudad if ciudad != "Todas las ciudades" else None,
                    dias_min, dias_max
                )
            
            self.mostrar_cartera_en_tabla(df_filtrado)
            
        except Exception as e:
            print(f"Error filtrando cartera: {e}")
    
    def mostrar_cartera_en_tabla(self, df):
        """Muestra los datos de cartera en la tabla"""
        try:
            self.cartera_table.setRowCount(len(df))
            
            for row, (_, item) in enumerate(df.iterrows()):
                self.cartera_table.setItem(row, 0, QTableWidgetItem(str(item.get('nit_cliente', ''))))
                self.cartera_table.setItem(row, 1, QTableWidgetItem(str(item.get('razon_social_cliente', ''))))
                self.cartera_table.setItem(row, 2, QTableWidgetItem(str(item.get('nombre_vendedor', ''))))
                self.cartera_table.setItem(row, 3, QTableWidgetItem(str(item.get('nro_factura', ''))))
                self.cartera_table.setItem(row, 4, QTableWidgetItem(f"${item.get('total_cop', 0):,.0f}"))
                self.cartera_table.setItem(row, 5, QTableWidgetItem(str(item.get('fecha_emision', ''))))
                self.cartera_table.setItem(row, 6, QTableWidgetItem(str(item.get('fecha_vencimiento', ''))))
                self.cartera_table.setItem(row, 7, QTableWidgetItem(str(item.get('dias_vencidos', 0))))
                self.cartera_table.setItem(row, 8, QTableWidgetItem(str(item.get('condicion_pago', ''))))
                self.cartera_table.setItem(row, 9, QTableWidgetItem(str(item.get('ciudad', ''))))
                
        except Exception as e:
            print(f"Error mostrando cartera en tabla: {e}")
    
    def limpiar_busqueda_cartera(self):
        """Limpia la búsqueda de cartera"""
        self.buscar_cartera_input.clear()
        self.filtrar_cartera()
    
    def actualizar_cartera(self):
        """Actualiza la vista de cartera"""
        self.filtrar_cartera()
    
    def cargar_excel(self):
        """Carga un archivo Excel de cartera"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Seleccionar archivo Excel", "", "Excel Files (*.xlsx *.xls)"
            )
            
            if file_path:
                success, message = self.db.cargar_excel_cartera(file_path)
                if success:
                    QMessageBox.information(self, "Éxito", message)
                    self.actualizar_cartera()
                else:
                    QMessageBox.critical(self, "Error", message)
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar Excel: {str(e)}")
    
    def actualizar_lista_clientes(self):
        """Actualiza la lista de clientes en el tab de gestión"""
        try:
            clientes = self.db.obtener_clientes_filtrados("todos")
            self.clientes_list.clear()
            
            for _, cliente in clientes.iterrows():
                item_text = f"{cliente['razon_social']} - {cliente['nit_cliente']}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, cliente['nit_cliente'])
                self.clientes_list.addItem(item)
                
        except Exception as e:
            print(f"Error actualizando lista de clientes: {e}")
    
    def buscar_cliente_gestion(self):
        """Busca clientes en el tab de gestión"""
        try:
            texto = self.buscar_gestion_input.text().strip()
            if texto:
                clientes = self.db.buscar_clientes(texto)
            else:
                clientes = self.db.obtener_clientes_filtrados("todos")
            
            self.clientes_list.clear()
            for _, cliente in clientes.iterrows():
                item_text = f"{cliente['razon_social']} - {cliente['nit_cliente']}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, cliente['nit_cliente'])
                self.clientes_list.addItem(item)
                
        except Exception as e:
            print(f"Error buscando cliente: {e}")
    
    def aplicar_filtro_clientes(self):
        """Aplica filtros a la lista de clientes"""
        try:
            filtro = self.filtro_clientes.currentText()
            tipo_filtro = ""
            
            if filtro == "Clientes en mora":
                tipo_filtro = "mora"
            elif filtro == "Clientes sin gestión este mes":
                tipo_filtro = "sin_gestion_mes"
            elif filtro == "Clientes con gestión este mes":
                tipo_filtro = "con_gestion_mes"
            else:
                tipo_filtro = "todos"
            
            clientes = self.db.obtener_clientes_filtrados(tipo_filtro)
            self.clientes_list.clear()
            
            for _, cliente in clientes.iterrows():
                item_text = f"{cliente['razon_social']} - {cliente['nit_cliente']}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, cliente['nit_cliente'])
                self.clientes_list.addItem(item)
                
        except Exception as e:
            print(f"Error aplicando filtro: {e}")
    
    def on_cliente_selected(self, current, previous):
        """Maneja la selección de un cliente"""
        if not current:
            return
            
        try:
            nit_cliente = current.data(Qt.ItemDataRole.UserRole)
            if not nit_cliente:
                return
            
            # Obtener información del cliente
            clientes = self.db.obtener_clientes()
            cliente = clientes[clientes['nit_cliente'] == nit_cliente]
            
            if not cliente.empty:
                cliente_info = cliente.iloc[0]
                self.lbl_razon_social.setText(cliente_info['razon_social'])
                self.lbl_telefono.setText(cliente_info.get('telefono', 'No disponible'))
                self.lbl_email.setText(cliente_info.get('email', 'No disponible'))
                self.lbl_ciudad.setText(cliente_info.get('ciudad', 'No disponible'))
            
            # Obtener información de cartera
            cartera = self.db.obtener_cartera_actual()
            cartera_cliente = cartera[cartera['nit_cliente'] == nit_cliente]
            
            if not cartera_cliente.empty:
                total_mora = cartera_cliente[cartera_cliente['dias_vencidos'] > 0]['total_cop'].sum()
                max_dias_vencidos = cartera_cliente['dias_vencidos'].max()
                
                self.lbl_total_mora.setText(f"${total_mora:,.0f}")
                self.lbl_dias_vencidos.setText(str(max_dias_vencidos))
            else:
                self.lbl_total_mora.setText("$0")
                self.lbl_dias_vencidos.setText("0")
            
            # Cargar historial de gestiones
            self.cargar_historial_gestiones(nit_cliente)
            
        except Exception as e:
            print(f"Error cargando información del cliente: {e}")
    
    def cargar_historial_gestiones(self, nit_cliente):
        """Carga el historial de gestiones de un cliente"""
        try:
            gestiones = self.db.obtener_gestiones_cliente(nit_cliente)
            self.historial_table.setRowCount(len(gestiones))
            
            for row, (_, gestion) in enumerate(gestiones.iterrows()):
                self.historial_table.setItem(row, 0, QTableWidgetItem(str(gestion.get('razon_social_cliente', ''))))
                self.historial_table.setItem(row, 1, QTableWidgetItem(str(gestion.get('fecha_contacto', ''))))
                self.historial_table.setItem(row, 2, QTableWidgetItem(str(gestion.get('tipo_contacto', ''))))
                self.historial_table.setItem(row, 3, QTableWidgetItem(str(gestion.get('resultado', ''))))
                self.historial_table.setItem(row, 4, QTableWidgetItem(str(gestion.get('observaciones', ''))))
                
                promesa_fecha = gestion.get('promesa_pago_fecha')
                self.historial_table.setItem(row, 5, QTableWidgetItem(str(promesa_fecha) if promesa_fecha else QTableWidgetItem("")))
                
                promesa_monto = gestion.get('promesa_pago_monto')
                self.historial_table.setItem(row, 6, QTableWidgetItem(f"${promesa_monto:,.0f}" if promesa_monto else QTableWidgetItem("")))
                
                proxima_gestion = gestion.get('proxima_gestion')
                self.historial_table.setItem(row, 7, QTableWidgetItem(str(proxima_gestion) if proxima_gestion else QTableWidgetItem("")))
                
        except Exception as e:
            print(f"Error cargando historial de gestiones: {e}")
    
    def guardar_gestion(self):
        """Guarda una nueva gestión"""
        try:
            current_item = self.clientes_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "Advertencia", "Por favor selecciona un cliente primero.")
                return
            
            nit_cliente = current_item.data(Qt.ItemDataRole.UserRole)
            razon_social = self.lbl_razon_social.text()
            
            if razon_social == "Seleccione un cliente":
                QMessageBox.warning(self, "Advertencia", "Por favor selecciona un cliente válido.")
                return
            
            # Validar campos obligatorios
            if self.resultado.currentText() in ["", "💰 COMPROMISO DE PAGO", "📞 CONTACTO Y LOCALIZACIÓN", 
                                              "⚠️ DIFICULTAD Y RECHAZO", "🔄 SEGUIMIENTO Y ACCIONES INTERNAS"]:
                QMessageBox.warning(self, "Advertencia", "Por favor selecciona un resultado válido.")
                return
            
            # Preparar datos
            gestion_data = (
                nit_cliente,
                razon_social,
                self.tipo_contacto.currentText(),
                self.resultado.currentText(),
                self.fecha_contacto.date().toString('yyyy-MM-dd'),
                self.auth_manager.current_user['email'],  # usuario
                self.observaciones.toPlainText(),
                self.promesa_fecha.date().toString('yyyy-MM-dd') if self.promesa_fecha.date() > QDate.currentDate() else None,
                float(self.promesa_monto.text()) if self.promesa_monto.text().strip() else None,
                self.proxima_gestion.date().toString('yyyy-MM-dd')
            )
            
            # Guardar en base de datos
            success = self.db.registrar_gestion(gestion_data)
            
            if success:
                QMessageBox.information(self, "Éxito", "Gestión guardada correctamente.")
                self.limpiar_formulario_gestion()
                self.cargar_historial_gestiones(nit_cliente)
                
                # ✅ ACTUALIZAR ANALYTICS DESPUÉS DE GUARDAR GESTIÓN
                self.actualizar_analytics()
                
            else:
                QMessageBox.critical(self, "Error", "Error al guardar la gestión.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar gestión: {str(e)}")
    
    def limpiar_formulario_gestion(self):
        """Limpia el formulario de gestión"""
        self.observaciones.clear()
        self.promesa_monto.clear()
        self.promesa_fecha.setDate(QDate.currentDate())
        self.proxima_gestion.setDate(QDate.currentDate())
        self.fecha_contacto.setDate(QDate.currentDate())
    
    def mostrar_dialogo_exportar(self):
        """Muestra diálogo para exportar gestiones"""
        try:
            dialog = ExportDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                opcion = dialog.get_export_option()
                
                if opcion == "mes_actual":
                    gestiones = self.db.obtener_gestiones_mes_actual()
                else:
                    gestiones = self.db.obtener_todas_gestiones()
                
                if gestiones.empty:
                    QMessageBox.information(self, "Exportar", "No hay gestiones para exportar.")
                    return
                
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "Guardar archivo Excel", "gestiones_exportadas.xlsx", "Excel Files (*.xlsx)"
                )
                
                if file_path:
                    gestiones.to_excel(file_path, index=False)
                    QMessageBox.information(self, "Éxito", f"Gestiones exportadas correctamente a:\n{file_path}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar gestiones: {str(e)}")
    
    def importar_gestiones(self):
        """Importa gestiones desde Excel"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Seleccionar archivo Excel", "", "Excel Files (*.xlsx *.xls)"
            )
            
            if file_path:
                success, message = self.db.importar_gestiones_excel(file_path)
                if success:
                    QMessageBox.information(self, "Éxito", message)
                    # Recargar datos si hay un cliente seleccionado
                    current_item = self.clientes_list.currentItem()
                    if current_item:
                        nit_cliente = current_item.data(Qt.ItemDataRole.UserRole)
                        self.cargar_historial_gestiones(nit_cliente)
                else:
                    QMessageBox.critical(self, "Error", message)
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al importar gestiones: {str(e)}")
    
    def filtrar_clientes(self):
        """Filtra la tabla de clientes"""
        try:
            texto_busqueda = self.buscar_clientes_input.text().strip()
            vendedor = self.filtro_vendedor_clientes.currentText()
            ciudad = self.filtro_ciudad_clientes.currentText()
            
            if texto_busqueda:
                df_filtrado = self.db.buscar_clientes(texto_busqueda)
            else:
                df_filtrado = self.db.obtener_clientes()
            
            # Aplicar filtros adicionales
            if vendedor != "Todos los vendedores":
                df_filtrado = df_filtrado[df_filtrado['vendedor_asignado'] == vendedor]
            
            if ciudad != "Todas las ciudades":
                df_filtrado = df_filtrado[df_filtrado['ciudad'] == ciudad]
            
            self.mostrar_clientes_en_tabla(df_filtrado)
            
        except Exception as e:
            print(f"Error filtrando clientes: {e}")
    
    def mostrar_clientes_en_tabla(self, df):
        """Muestra los clientes en la tabla"""
        try:
            self.clientes_table.setRowCount(len(df))
            
            for row, (_, cliente) in enumerate(df.iterrows()):
                self.clientes_table.setItem(row, 0, QTableWidgetItem(str(cliente.get('nit_cliente', ''))))
                self.clientes_table.setItem(row, 1, QTableWidgetItem(str(cliente.get('razon_social', ''))))
                self.clientes_table.setItem(row, 2, QTableWidgetItem(str(cliente.get('vendedor_asignado', ''))))
                self.clientes_table.setItem(row, 3, QTableWidgetItem(str(cliente.get('ciudad', ''))))
                self.clientes_table.setItem(row, 4, QTableWidgetItem(str(cliente.get('telefono', ''))))
                self.clientes_table.setItem(row, 5, QTableWidgetItem(str(cliente.get('email', ''))))
                
        except Exception as e:
            print(f"Error mostrando clientes en tabla: {e}")
    
    def limpiar_busqueda_clientes(self):
        """Limpia la búsqueda de clientes"""
        self.buscar_clientes_input.clear()
        self.filtrar_clientes()
    
    def load_clientes_data(self):
        """Carga los datos de clientes"""
        self.filtrar_clientes()
    
    def actualizar_analytics(self):
        """Actualiza la pestaña de analytics - VERSIÓN COMPLETAMENTE CORREGIDA"""
        try:
            print("🔄 Actualizando analytics...")
            
            # Progreso de gestión
            progreso = self.db.obtener_progreso_gestion()
            
            # Obtener los valores directamente
            total_general = progreso['total_clientes']
            gestionados_general = progreso['clientes_gestionados'] 
            total_mora = progreso['clientes_mora']
            gestionados_mora = progreso['clientes_mora_gestionados']
            
            # Calcular porcentajes
            porcentaje_general = (gestionados_general / total_general * 100) if total_general > 0 else 0
            porcentaje_mora = (gestionados_mora / total_mora * 100) if total_mora > 0 else 0
            
            print(f"📊 DATOS CALCULADOS:")
            print(f"   General: {gestionados_general}/{total_general} = {porcentaje_general:.1f}%")
            print(f"   Mora: {gestionados_mora}/{total_mora} = {porcentaje_mora:.1f}%")
            
            # ACTUALIZAR TARJETAS DE PROGRESO - MÉTODO DIRECTO Y SEGURO
            try:
                # Para Progreso General - ACTUALIZACIÓN DIRECTA
                self.progreso_gestion.progress_bar.setValue(int(porcentaje_general))
                self.progreso_gestion.progress_bar.setFormat(f"{gestionados_general}/{total_general}")
                
                # Buscar y actualizar el QLabel de porcentaje si existe
                for i in range(self.progreso_gestion.layout().count()):
                    widget = self.progreso_gestion.layout().itemAt(i).widget()
                    if isinstance(widget, QLabel) and hasattr(widget, 'text') and '%' in widget.text():
                        widget.setText(f"{porcentaje_general:.1f}%")
                        break
                
                # Buscar y actualizar el QLabel descriptivo si existe  
                for i in range(self.progreso_gestion.layout().count()):
                    widget = self.progreso_gestion.layout().itemAt(i).widget()
                    if isinstance(widget, QLabel) and ('gestionados' in widget.text() or 'pendientes' in widget.text()):
                        widget.setText(f"✅ {gestionados_general} gestionados | ⏳ {total_general - gestionados_general} pendientes")
                        break

                # Para Clientes en Mora Gestionados - ACTUALIZACIÓN DIRECTA
                self.progreso_mora.progress_bar.setValue(int(porcentaje_mora))
                self.progreso_mora.progress_bar.setFormat(f"{gestionados_mora}/{total_mora}")
                
                # Buscar y actualizar el QLabel de porcentaje si existe
                for i in range(self.progreso_mora.layout().count()):
                    widget = self.progreso_mora.layout().itemAt(i).widget()
                    if isinstance(widget, QLabel) and hasattr(widget, 'text') and '%' in widget.text():
                        widget.setText(f"{porcentaje_mora:.1f}%")
                        break
                
                # Buscar y actualizar el QLabel descriptivo si existe
                for i in range(self.progreso_mora.layout().count()):
                    widget = self.progreso_mora.layout().itemAt(i).widget()
                    if isinstance(widget, QLabel) and ('gestionados' in widget.text() or 'pendientes' in widget.text()):
                        widget.setText(f"✅ {gestionados_mora} gestionados | ⏳ {total_mora - gestionados_mora} pendientes")
                        break

            except Exception as e:
                print(f"⚠️ Error actualizando tarjetas de progreso: {e}")
            
            # ACTUALIZAR MÉTRICAS DE GESTIÓN MENSUAL
            try:
                # Obtener estadísticas FILTRADAS por usuario
                if self.auth_manager.current_user['rol'] in ['comercial', 'consulta']:
                    # Para comercial/consulta: obtener SOLO sus gestiones
                    gestiones_mes = self.db.obtener_gestiones_mes_actual()
                    # FILTRAR solo las gestiones del usuario actual
                    gestiones_mes = gestiones_mes[gestiones_mes['usuario'] == self.auth_manager.current_user['email']]
                else:
                    # Para admin/supervisor: obtener TODAS las gestiones
                    gestiones_mes = self.db.obtener_gestiones_mes_actual()
                
                total_gestiones = len(gestiones_mes)
                clientes_unicos = len(gestiones_mes['nit_cliente'].unique()) if not gestiones_mes.empty else 0
                
                # Calcular tasa de contacto (simplificado)
                contactos_exitosos = len(gestiones_mes[gestiones_mes['resultado'].str.contains('Contacto|Promesa|Pago', na=False)]) if not gestiones_mes.empty else 0
                tasa_contacto = (contactos_exitosos / total_gestiones * 100) if total_gestiones > 0 else 0
                
                # Contar promesas
                promesas_generadas = len(gestiones_mes[gestiones_mes['resultado'].str.contains('Promesa', na=False)]) if not gestiones_mes.empty else 0
                
                # Actualizar tarjetas de métricas
                self.metricas_gestion['total_gestiones'].update_value(total_gestiones)
                self.metricas_gestion['clientes_unicos'].update_value(clientes_unicos)
                self.metricas_gestion['tasa_contacto'].update_value(tasa_contacto)
                self.metricas_gestion['promesas_generadas'].update_value(promesas_generadas)
                
                print(f"📈 Métricas gestión COMERCIAL: {total_gestiones} gestiones, {clientes_unicos} clientes únicos")
                
            except Exception as e:
                print(f"⚠️ Error actualizando métricas de gestión: {e}")
            
            # ✅ ACTUALIZAR GRÁFICAS DE ANALYTICS
            self.actualizar_graficas_analytics()
            
            print("✅ Analytics actualizado correctamente")
            
        except Exception as e:
            print(f"❌ Error actualizando analytics: {e}")

    def actualizar_graficas_analytics(self):
        """Actualiza las gráficas de analytics - VERSIÓN CORREGIDA SIN DUPLICADOS"""
        try:
            # Limpiar gráficas anteriores
            self.clear_layout(self.efectividad_layout)
            self.clear_layout(self.evolucion_layout)
            self.clear_layout(self.historica_layout)  # Limpiar gráfica histórica
            
            plt.style.use('dark_background')
            fig_params = {'facecolor': '#1e293b', 'edgecolor': '#334155'}
            
            # Gráfica 1: Distribución de resultados
            estadisticas = self.db.obtener_estadisticas_resultados_filtrado()
            
            if estadisticas and any(estadisticas.values()):
                fig1, ax1 = plt.subplots(figsize=(8, 5), **fig_params)
                categorias = list(estadisticas.keys())
                valores = list(estadisticas.values())
                
                colors = ['#00B3B0', '#3b82f6', '#f59e0b', '#ef4444']
                bars = ax1.barh(categorias, valores, color=colors[:len(categorias)])
                ax1.set_title('Distribución de Resultados por Categoría', fontsize=12, fontweight='bold', color='#e2e8f0')
                ax1.set_xlabel('Cantidad de Gestiones', color='#cbd5e1')
                ax1.tick_params(axis='x', colors='#cbd5e1')
                ax1.tick_params(axis='y', colors='#cbd5e1')
                
                for bar, valor in zip(bars, valores):
                    if valor > 0:
                        ax1.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                                str(valor), ha='left', va='center', color='#e2e8f0', fontsize=10)
                
                plt.tight_layout()
                canvas1 = FigureCanvas(fig1)
                self.efectividad_layout.addWidget(canvas1)
            else:
                no_data_label = QLabel("No hay datos de resultados para mostrar")
                no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_data_label.setStyleSheet("color: #94a3b8; font-style: italic; padding: 40px;")
                self.efectividad_layout.addWidget(no_data_label)
            
            # Gráfica 2: Evolución diaria
            evolucion = self.db.obtener_evolucion_diaria_gestiones()
            
            if evolucion:
                fig2, ax2 = plt.subplots(figsize=(8, 4), **fig_params)
                fechas = [item[0] for item in evolucion]
                total_gestiones = [item[1] for item in evolucion]
                clientes_unicos = [item[2] for item in evolucion]
                
                # Formatear fechas
                fechas_formateadas = [fecha[8:] for fecha in fechas]  # Mostrar solo día
                
                ax2.plot(fechas_formateadas, total_gestiones, marker='o', linewidth=2, label='Total Gestiones', color='#00B3B0')
                ax2.plot(fechas_formateadas, clientes_unicos, marker='s', linewidth=2, label='Clientes Únicos', color='#f59e0b')
                ax2.set_title('Evolución Diaria de Gestiones', fontsize=12, fontweight='bold', color='#e2e8f0')
                ax2.set_ylabel('Cantidad', color='#cbd5e1')
                ax2.tick_params(axis='x', rotation=45, colors='#cbd5e1')
                ax2.tick_params(axis='y', colors='#cbd5e1')
                ax2.legend(facecolor='#1e293b', edgecolor='#334155')
                ax2.grid(True, alpha=0.3)
                
                plt.tight_layout()
                canvas2 = FigureCanvas(fig2)
                self.evolucion_layout.addWidget(canvas2)
            else:
                no_data_label = QLabel("No hay datos de evolución para mostrar")
                no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_data_label.setStyleSheet("color: #94a3b8; font-style: italic; padding: 40px;")
                self.evolucion_layout.addWidget(no_data_label)
            
            # GRÁFICA 3: Evolución Histórica Simple (SÓLO UNA VEZ)
            datos_historicos, max_historico = self.db.obtener_evolucion_historica_gestiones()
            
            if datos_historicos:
                fig3, ax3 = plt.subplots(figsize=(10, 4), **fig_params)
                
                meses = [f"{item[0][5:7]}/{item[0][2:4]}" for item in datos_historicos]  # Formato MM/YY
                totales = [item[1] for item in datos_historicos]
                
                # Línea de gestiones mensuales
                ax3.plot(meses, totales, marker='o', linewidth=2.5, 
                        label='Total Gestiones', color='#00B3B0', markersize=6)
                
                # Línea de máximo histórico
                if max_historico > 0:
                    ax3.axhline(y=max_historico, color='#F57C00', linestyle='--', 
                               linewidth=2, label=f'Máximo Histórico: {max_historico}')
                
                ax3.set_title('Evolución Histórica de Gestiones (Últimos 12 Meses)', 
                             fontsize=12, fontweight='bold', color='#e2e8f0', pad=15)
                ax3.set_ylabel('Total de Gestiones', color='#cbd5e1', fontsize=10)
                ax3.set_xlabel('Mes', color='#cbd5e1', fontsize=10)
                ax3.tick_params(axis='x', rotation=45, colors='#cbd5e1', labelsize=9)
                ax3.tick_params(axis='y', colors='#cbd5e1', labelsize=9)
                
                # Añadir etiquetas de valores en los puntos
                for i, (mes, total) in enumerate(zip(meses, totales)):
                    ax3.annotate(f'{total}', (mes, total), 
                                textcoords="offset points", xytext=(0,10), 
                                ha='center', va='bottom', color='#e2e8f0', fontsize=8,
                                bbox=dict(boxstyle='round,pad=0.3', facecolor='#1e293b', 
                                         edgecolor='#00B3B0', alpha=0.8))
                
                ax3.legend(facecolor='#1e293b', edgecolor='#334155', loc='upper left')
                ax3.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
                ax3.set_facecolor('#0f172a')
                
                # Ajustar márgenes
                plt.tight_layout()
                canvas3 = FigureCanvas(fig3)
                self.historica_layout.addWidget(canvas3)
            else:
                no_data_label = QLabel("No hay datos históricos para mostrar")
                no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_data_label.setStyleSheet("color: #94a3b8; font-style: italic; padding: 40px;")
                self.historica_layout.addWidget(no_data_label)
            
        except Exception as e:
            print(f"❌ Error actualizando gráficas de analytics: {e}")
            # Mostrar mensaje de error
            error_label = QLabel(f"Error cargando gráficas: {str(e)}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("color: #ef4444; padding: 20px;")
            self.efectividad_layout.addWidget(error_label)
    
    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def check_session_timeout(self):
        """Verifica si la sesión ha expirado"""
        if self.auth_manager.check_session_timeout():
            QMessageBox.warning(self, "Sesión Expirada", 
                              "Tu sesión ha expirado por inactividad. Por favor ingresa nuevamente.")
            self.logout()
    
    def logout(self):
        """Cierra sesión y reinicia la aplicación completamente"""
        reply = QMessageBox.question(
            self, 
            "Cerrar Sesión", 
            "¿Estás seguro de que quieres cerrar la sesión?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Guardar referencia a la aplicación
            app = QApplication.instance()
            
            # Cerrar esta ventana
            self.close()
            
            # Reiniciar después de un delay
            QTimer.singleShot(500, lambda: self.reiniciar_aplicacion_completa(app))

    def reiniciar_aplicacion_completa(self, app):
        """Reinicia la aplicación completamente"""
        try:
            # Importar aquí para evitar problemas
            from crm_gui import ModernCRM
            
            # Crear NUEVA ventana
            new_window = ModernCRM()
            new_window.show()
            
            print("🔄 Aplicación reiniciada exitosamente")
            
        except Exception as e:
            print(f"❌ Error al reiniciar: {e}")
            QMessageBox.critical(None, "Error", f"No se pudo reiniciar: {e}")
            app.quit()
    
    def show_new_user_dialog(self):
        """Muestra diálogo completo para crear nuevo usuario"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("➕ Crear Nuevo Usuario")
            dialog.setModal(True)
            dialog.setFixedSize(500, 400)
            
            layout = QVBoxLayout(dialog)
            
            # Título
            title = QLabel("CREAR NUEVO USUARIO")
            title.setObjectName("section_title")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title)
            
            # Formulario
            form_layout = QFormLayout()
            form_layout.setSpacing(10)
            
            # Campo Email
            self.new_user_email = QLineEdit()
            self.new_user_email.setPlaceholderText("usuario@alpapel.com")
            self.new_user_email.setMinimumHeight(35)
            form_layout.addRow("📧 Email:", self.new_user_email)
            
            # Campo Nombre
            self.new_user_nombre = QLineEdit()
            self.new_user_nombre.setPlaceholderText("Nombre completo del usuario")
            self.new_user_nombre.setMinimumHeight(35)
            form_layout.addRow("👤 Nombre completo:", self.new_user_nombre)
            
            # Campo Rol
            self.new_user_rol = QComboBox()
            self.new_user_rol.addItems([
                "comercial", 
                "consulta", 
                "supervisor", 
                "admin"
            ])
            self.new_user_rol.setMinimumHeight(35)
            form_layout.addRow("🎭 Rol:", self.new_user_rol)
            
            # Campo Vendedor Asignado
            self.new_user_vendedor = QComboBox()
            self.new_user_vendedor.addItem("No asignado")
            
            # Cargar vendedores disponibles
            vendedores = self.db.obtener_vendedores()
            for _, vendedor in vendedores.iterrows():
                if vendedor['nombre_vendedor']:
                    self.new_user_vendedor.addItem(vendedor['nombre_vendedor'])
            
            self.new_user_vendedor.setMinimumHeight(35)
            form_layout.addRow("👤 Vendedor asignado:", self.new_user_vendedor)
            
            # Checkbox Activo
            self.new_user_activo = QCheckBox("Usuario activo")
            self.new_user_activo.setChecked(True)
            form_layout.addRow("Estado:", self.new_user_activo)
            
            layout.addLayout(form_layout)
            
            # Información de contraseña
            password_info = QLabel("ℹ️ Se generará una contraseña temporal automáticamente")
            password_info.setStyleSheet("color: #94a3b8; font-size: 11px; padding: 10px;")
            password_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(password_info)
            
            # Botones
            button_layout = QHBoxLayout()
            
            btn_crear = QPushButton("💾 Crear Usuario")
            btn_crear.setObjectName("primary")
            btn_crear.clicked.connect(lambda: self.crear_usuario_completo(dialog))
            
            btn_cancelar = QPushButton("Cancelar")
            btn_cancelar.clicked.connect(dialog.reject)
            
            button_layout.addWidget(btn_crear)
            button_layout.addStretch()
            button_layout.addWidget(btn_cancelar)
            
            layout.addLayout(button_layout)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al crear diálogo: {str(e)}")

    def crear_usuario_completo(self, dialog):
        """Crea un usuario con todos los datos del formulario"""
        try:
            email = self.new_user_email.text().strip()
            nombre = self.new_user_nombre.text().strip()
            rol = self.new_user_rol.currentText()
            vendedor = self.new_user_vendedor.currentText()
            activo = 1 if self.new_user_activo.isChecked() else 0
            
            # Validaciones
            if not email or not nombre:
                QMessageBox.warning(dialog, "Datos incompletos", "Email y nombre son obligatorios")
                return
                
            if not email.endswith('@alpapel.com'):
                QMessageBox.warning(dialog, "Email inválido", "El email debe ser del dominio @alpapel.com")
                return
            
            # Generar contraseña temporal
            import random
            import string
            password_temporal = "Temp" + ''.join(random.choices(string.digits, k=4)) + "!"
            
            # Crear usuario en la base de datos
            conn = self.user_manager.get_connection()
            cursor = conn.cursor()
            
            # Verificar si el usuario ya existe
            cursor.execute('SELECT id FROM usuarios WHERE email = ?', (email,))
            if cursor.fetchone():
                QMessageBox.warning(dialog, "Usuario existente", "Ya existe un usuario con este email")
                conn.close()
                return
            
            # Insertar nuevo usuario
            password_hash = self.user_manager.hash_password(password_temporal)
            
            cursor.execute('''
                INSERT INTO usuarios 
                (email, password_hash, nombre_completo, rol, vendedor_asignado, activo, email_verificado)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (email, password_hash, nombre, rol, vendedor if vendedor != "No asignado" else None, activo))
            
            conn.commit()
            conn.close()
            
            # Mostrar éxito con contraseña temporal
            mensaje = f"""
            ✅ Usuario creado exitosamente:

            📧 Email: {email}
            👤 Nombre: {nombre}
            🎭 Rol: {config.ROLES.get(rol, rol)}
            👤 Vendedor: {vendedor if vendedor != "No asignado" else "No asignado"}
            🔑 Contraseña temporal: {password_temporal}

            ⚠️ El usuario debe cambiar su contraseña en el primer acceso.
            """
            
            QMessageBox.information(dialog, "Usuario Creado", mensaje)
            
            # Actualizar lista de usuarios
            self.load_users_data()
            
            # Cerrar diálogo
            dialog.accept()
            
        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"Error al crear usuario: {str(e)}")
    
    def editar_usuario(self, user_id):
        """Muestra diálogo para editar usuario existente"""
        try:
            # Obtener datos actuales del usuario
            conn = self.user_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT email, nombre_completo, rol, vendedor_asignado, activo 
                FROM usuarios WHERE id = ?
            ''', (user_id,))
            
            usuario = cursor.fetchone()
            conn.close()
            
            if not usuario:
                QMessageBox.warning(self, "Error", "Usuario no encontrado")
                return
                
            dialog = QDialog(self)
            dialog.setWindowTitle("✏️ Editar Usuario")
            dialog.setModal(True)
            dialog.setFixedSize(500, 400)
            
            layout = QVBoxLayout(dialog)
            
            # Título
            title = QLabel(f"EDITAR USUARIO: {usuario[0]}")
            title.setObjectName("section_title")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title)
            
            # Formulario
            form_layout = QFormLayout()
            form_layout.setSpacing(10)
            
            # Email (solo lectura)
            email_label = QLabel(usuario[0])
            email_label.setStyleSheet("background-color: #374151; padding: 8px; border-radius: 5px;")
            form_layout.addRow("📧 Email:", email_label)
            
            # Campo Nombre
            edit_nombre = QLineEdit(usuario[1])
            edit_nombre.setMinimumHeight(35)
            form_layout.addRow("👤 Nombre completo:", edit_nombre)
            
            # Campo Rol
            edit_rol = QComboBox()
            edit_rol.addItems(["comercial", "consulta", "supervisor", "admin"])
            edit_rol.setCurrentText(usuario[2])
            edit_rol.setMinimumHeight(35)
            form_layout.addRow("🎭 Rol:", edit_rol)
            
            # Campo Vendedor Asignado
            edit_vendedor = QComboBox()
            edit_vendedor.addItem("No asignado")
            
            vendedores = self.db.obtener_vendedores()
            for _, vendedor in vendedores.iterrows():
                if vendedor['nombre_vendedor']:
                    edit_vendedor.addItem(vendedor['nombre_vendedor'])
            
            if usuario[3]:
                index = edit_vendedor.findText(usuario[3])
                if index >= 0:
                    edit_vendedor.setCurrentIndex(index)
            
            edit_vendedor.setMinimumHeight(35)
            form_layout.addRow("👤 Vendedor asignado:", edit_vendedor)
            
            # Checkbox Activo
            edit_activo = QCheckBox("Usuario activo")
            edit_activo.setChecked(bool(usuario[4]))
            form_layout.addRow("Estado:", edit_activo)
            
            layout.addLayout(form_layout)
            
            # Botones
            button_layout = QHBoxLayout()
            
            btn_guardar = QPushButton("💾 Guardar Cambios")
            btn_guardar.setObjectName("primary")
            btn_guardar.clicked.connect(lambda: self.guardar_cambios_usuario(
                user_id, edit_nombre.text(), edit_rol.currentText(), 
                edit_vendedor.currentText(), edit_activo.isChecked(), dialog
            ))
            
            btn_cancelar = QPushButton("Cancelar")
            btn_cancelar.clicked.connect(dialog.reject)
            
            button_layout.addWidget(btn_guardar)
            button_layout.addStretch()
            button_layout.addWidget(btn_cancelar)
            
            layout.addLayout(button_layout)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al editar usuario: {str(e)}")

    def eliminar_usuario(self, user_id, email):
        """Elimina un usuario después de confirmación"""
        try:
            # No permitir eliminarse a sí mismo
            if user_id == self.auth_manager.current_user['id']:
                QMessageBox.warning(self, "Error", "No puedes eliminar tu propio usuario")
                return
            
            reply = QMessageBox.question(
                self, 
                "Confirmar Eliminación",
                f"¿Estás seguro de eliminar al usuario:\n{email}?\n\nEsta acción no se puede deshacer.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                conn = self.user_manager.get_connection()
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM usuarios WHERE id = ?', (user_id,))
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Éxito", f"Usuario {email} eliminado correctamente")
                self.load_users_data()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al eliminar usuario: {str(e)}")

    def guardar_cambios_usuario(self, user_id, nombre, rol, vendedor, activo, dialog):
        """Guarda los cambios del usuario editado"""
        try:
            success, message = self.user_manager.actualizar_usuario(user_id, {
                'nombre_completo': nombre,
                'rol': rol,
                'vendedor_asignado': vendedor if vendedor != "No asignado" else None,
                'activo': 1 if activo else 0
            })
            
            if success:
                QMessageBox.information(dialog, "Éxito", "Usuario actualizado correctamente")
                self.load_users_data()
                dialog.accept()
            else:
                QMessageBox.critical(dialog, "Error", message)
                
        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"Error al guardar cambios: {str(e)}")
    
    def cambiar_password_usuario(self, user_id):
        """Cambia la contraseña de un usuario"""
        new_password, ok = QInputDialog.getText(self, "Cambiar Contraseña", 
                                              "Nueva contraseña:", QLineEdit.EchoMode.Password)
        if ok and new_password:
            success, message = self.user_manager.cambiar_password(user_id, new_password)
            if success:
                QMessageBox.information(self, "Contraseña Cambiada", message)
            else:
                QMessageBox.critical(self, "Error", message)
    
    def show_user_profile(self):
        """Muestra el perfil del usuario actual"""
        user = self.auth_manager.current_user
        profile_text = f"""
        👤 PERFIL DE USUARIO
        
        Nombre: {user['nombre_completo']}
        Email: {user['email']}
        Rol: {config.ROLES.get(user['rol'], 'Usuario')}
        Vendedor Asignado: {user.get('vendedor_asignado', 'No asignado')}
        
        Tiempo restante de sesión: {self.auth_manager.get_session_time_remaining()} minutos
        """
        
        QMessageBox.information(self, "Mi Perfil", profile_text)
    
    def show_admin_panel(self):
        """Muestra el panel de administración"""
        # Navegar a la pestaña de admin si existe
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "🛡️ Admin":
                self.tabs.setCurrentIndex(i)
                break

    def mostrar_reporte_carga(self):
        """Muestra el diálogo de reporte de carga"""
        try:
            # ⬇️⬇️⬇️ DIAGNÓSTICO CÁLCULOS PROBLEMÁTICOS ⬇️⬇️⬇️
            print("🚀 EJECUTANDO DIAGNÓSTICO DE CÁLCULOS...")
            self.db.diagnosticar_calculos_problematicos()
            
            dialog = ReporteCargaDialog(self.db, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error mostrando reporte: {str(e)}")

    def actualizar_historial_incremental(self):
        """Actualiza el historial con solo archivos nuevos"""
        try:
            reply = QMessageBox.question(
                self, 
                "Actualizar Historial",
                "¿Buscar y cargar solo archivos nuevos que no estén en el historial?\n\n"
                "Esto escaneará la carpeta CARTERA DIARIA y cargará solo\n"
                "los archivos que no han sido procesados anteriormente.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.progress_dialog = QProgressDialog("Buscando archivos nuevos...", None, 0, 0, self)
                self.progress_dialog.setWindowTitle("Actualizando Historial")
                self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
                self.progress_dialog.show()
                
                QTimer.singleShot(100, self.ejecutar_actualizacion_incremental)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error iniciando actualización: {str(e)}")

    def ejecutar_actualizacion_incremental(self):
        """Ejecuta la actualización incremental"""
        try:
            success, message = self.db.cargar_historial_incremental()
            
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.close()
            
            if success:
                QMessageBox.information(self, "Actualización Completada", message)
                # Actualizar análisis con nuevo historial
                self.actualizar_analisis_cartera()
            else:
                QMessageBox.warning(self, "Actualización con Resultados", message)
                
        except Exception as e:
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.close()
            QMessageBox.critical(self, "Error", f"Error en actualización: {str(e)}")

    def actualizar_visibilidad_graficas(self):
        """Actualiza la visibilidad de las gráficas según los checkboxes"""
        try:
            # Mapeo de checkboxes a layouts de gráficas
            chart_mapping = {
                'chart1': self.chart1_analisis_layout,
                'chart2': self.chart2_analisis_layout, 
                'chart3': self.chart3_analisis_layout,
                'chart4': self.chart4_analisis_layout,
                'chart5': self.chart5_analisis_layout,
                'chart6': self.chart6_analisis_layout,
                'chart7': self.chart7_analisis_layout, 
                'chart8': self.chart8_analisis_layout,
                'chart9': self.chart9_analisis_layout
            }
            
            for chart_id, layout in chart_mapping.items():
                checkbox = self.graficas_checkboxes.get(chart_id)
                if checkbox and layout:
                    # Encontrar el QGroupBox padre
                    parent_widget = layout.parent()
                    if parent_widget and isinstance(parent_widget, QGroupBox):
                        parent_widget.setVisible(checkbox.isChecked())
                        
        except Exception as e:
            print(f"Error actualizando visibilidad de gráficas: {e}")

    def seleccionar_todas_graficas(self):
        """Selecciona todas las gráficas"""
        for checkbox in self.graficas_checkboxes.values():
            checkbox.setChecked(True)

    def deseleccionar_todas_graficas(self):
        """Deselecciona todas las gráficas"""  
        for checkbox in self.graficas_checkboxes.values():
            checkbox.setChecked(False)

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = ModernCRM()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()