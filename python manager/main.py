# librerias necesarias
import os
import sys
import json
import mysql.connector
from mysql.connector import Error
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QComboBox, QPushButton, 
                             QTextEdit, QMessageBox, QFrame, QTableWidget, 
                             QTableWidgetItem, QLineEdit, QHeaderView, QStatusBar, 
                             QInputDialog, QDialog, QStyle, QTabWidget, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QPoint, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon, QPixmap
from PyQt5.QtWidgets import QSizePolicy

# Clase para mostrar notificaciones estilo toast
class NotificationWidget(QWidget):
    """Widget de notificación estilo toast"""   
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.animation = QPropertyAnimation(self, b"pos")
        
    def setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("""
            background-color: #323232;
            color: white;
            border-radius: 4px;
            padding: 10px;
        """)
        layout = QHBoxLayout(self)
        self.icon_label = QLabel()
        self.message_label = QLabel()
        self.message_label.setStyleSheet("font-size: 12px;")
        self.message_label.setWordWrap(True)
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.message_label)
        layout.setContentsMargins(10, 5, 10, 5)

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.adjustSize()
        
    def show_notification(self, message, is_success=True):
        if is_success:
            self.icon_label.setPixmap(QIcon.fromTheme("dialog-ok").pixmap(24, 24))
            self.setStyleSheet("""
                background-color: #4CAF50;
                color: white;
                border-radius: 4px;
                padding: 10px;
            """)
        else:
            self.icon_label.setPixmap(QIcon.fromTheme("dialog-error").pixmap(24, 24))
            self.setStyleSheet("""
                background-color: #F44336;
                color: white;
                border-radius: 4px;
                padding: 10px;
            """)
        
        self.message_label.setText(message)
        self.adjustSize()
        
        parent_rect = self.parent().geometry()
        end_pos = QPoint(
            parent_rect.width() - self.width() - 20,
            parent_rect.height() - self.height() - 20
        )
        
        self.move(end_pos)
        self.show()
        
        if is_success:
            self.hide_timer = self.startTimer(3000)
        
    def timerEvent(self, event):
        self.killTimer(event.timerId())
        self.hide()

class GestorConexion:
    """Clase para gestionar la conexión y operaciones con MySQL"""
    
    def __init__(self):
        self.config = {
          # Configuración por defecto
            'host': '',#coloca tu host/ip
            'port': 3306,
            'user': '',#coloca tu usuario de mysql
            'password': '', #coloca tu contraseña del usuario mysql 
            'database': None
        }
        self.conexion = None
        self.database = None
        self.cargar_configuracion()
    
    def cargar_configuracion(self):
        """Intenta cargar la configuración desde un archivo"""
        try:
            if os.path.exists('config_db.json'):
                with open('config_db.json', 'r') as f:
                    saved_config = json.load(f)
                    # Actualizar solo las claves existentes
                    for key in saved_config:
                        if key in self.config:
                            self.config[key] = saved_config[key]
        except Exception as e:
            print(f"Error al cargar configuración: {e}")
    
    def guardar_configuracion(self):
        """Guarda la configuración actual en un archivo"""
        try:
            with open('config_db.json', 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error al guardar configuración: {e}")
    
    def actualizar_configuracion(self, host=None, port=None, user=None, password=None):
        """Actualiza la configuración de conexión"""
        if host is not None:
            self.config['host'] = host
        if port is not None:
            self.config['port'] = port
        if user is not None:
            self.config['user'] = user
        if password is not None:
            self.config['password'] = password
            
        self.guardar_configuracion()
        return self.verificar_conexion()

    def verificar_conexion(self):
        try:
            config = self.config.copy()
            self.conexion = mysql.connector.connect(**config)
            if self.conexion.is_connected():
                print("Conexión verificada correctamente")
                return True
            return False
        except Error as e:
            print(f"Error de conexión: {e}")
            return False

    def obtener_bases_datos(self):
        try:
            if not self.conexion or not self.conexion.is_connected():
                self.conexion = mysql.connector.connect(**self.config)
            
            bases_sistema = {
                'information_schema', 
                'mysql', 
                'performance_schema', 
                'sys',
                'phpmyadmin'
            }
            
            cursor = self.conexion.cursor() 
            cursor.execute("SHOW DATABASES")
            bases_datos = [bd[0] for bd in cursor.fetchall() 
                         if bd[0] not in bases_sistema]
            cursor.close()
            return bases_datos
        except Error as e:
            print(f"❌ Error al obtener bases de datos: {e}")
            return []

    def seleccionar_base_datos(self, database):
        try:
            self.database = database
            if self.conexion and self.conexion.is_connected():
                self.conexion.database = database
                print(f"✅ Base de datos {database} seleccionada")
                return True
            return False
        except Error as e:
            print(f"❌ Error al seleccionar base de datos: {e}")
            return False
    
    def obtener_conexion(self):
        try:
            if not self.conexion or not self.conexion.is_connected():
                config = self.config.copy()
                if self.database:
                    config['database'] = self.database
                self.conexion = mysql.connector.connect(**config)
            return self.conexion
        except Error as e:
            print(f"❌ Error al obtener conexión: {e}")
            return None
    
    def obtener_tablas(self):
        tablas = []
        try:
            if not self.conexion or not self.conexion.is_connected():
                self.conexion = mysql.connector.connect(**self.config, database=self.database)
            
            cursor = self.conexion.cursor()
            cursor.execute("SHOW TABLES")
            tablas = [tabla[0] for tabla in cursor.fetchall()]
            cursor.close()
            return tablas
        except Error as e:
            print(f"❌ Error al obtener tablas: {e}")
            return []
    
    def cerrar_conexion(self):
        try:
            if self.conexion and self.conexion.is_connected():
                self.conexion.close()
                print("✅ Conexión cerrada correctamente")
        except Error as e:
            print(f"❌ Error al cerrar conexión: {e}")
    
    def obtener_datos_tabla(self, nombre_tabla_formateado):
        try:
            if not self.database:
                return None, "No hay base de datos seleccionada"
                
            conexion = self.obtener_conexion()
            if not conexion:
                return None, "No hay conexión a la base de datos"
            
            cursor = conexion.cursor(dictionary=True)
            
            cursor.execute("SHOW TABLES")
            tablas_disponibles = []
            for t in cursor.fetchall():
                if isinstance(t, dict):
                    tablas_disponibles.append(t[f'Tables_in_{self.database}'])
                else:
                    tablas_disponibles.append(t[0])
            
            nombre_original = None
            nombre_buscado = nombre_tabla_formateado.replace(' ', '_').lower()
            
            for tabla_real in tablas_disponibles:
                if tabla_real.lower() == nombre_buscado.lower():
                    nombre_original = tabla_real
                    break
            
            if not nombre_original:
                return None, f"La tabla {nombre_tabla_formateado} no existe"
            
            cursor.execute(f"SELECT COUNT(*) as count FROM `{nombre_original}`")
            count_result = cursor.fetchone()
            
            if count_result['count'] == 0:
                return None, "empty"
            
            cursor.execute(f"SELECT * FROM `{nombre_original}` LIMIT 100")
            datos = cursor.fetchall()
            
            if datos:
                encabezados = list(datos[0].keys())
                return encabezados, datos
            
            return None, "No se encontraron datos"
            
        except Error as e:
            print(f"❌ Error al obtener datos: {e}")
            return None, f"Error: {str(e)}"
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def buscar_en_toda_bd(self, texto_busqueda):
        resultados = {}
        try:
            conexion = self.obtener_conexion()
            if not conexion:
                return None
            
            cursor = conexion.cursor(dictionary=True)
            
            cursor.execute("SHOW TABLES")
            tablas = [t[f'Tables_in_{self.database}'] for t in cursor.fetchall()]
            
            for tabla in tablas:
                cursor.execute(f"DESCRIBE `{tabla}`")
                columnas = [col['Field'] for col in cursor.fetchall()]
                
                condiciones = " OR ".join([f"`{col}` LIKE %s" for col in columnas])
                query = f"SELECT * FROM `{tabla}` WHERE {condiciones} LIMIT 100"
                
                params = [f"%{texto_busqueda}%"] * len(columnas)
                
                cursor.execute(query, params)
                datos = cursor.fetchall()
                
                if datos:
                    encabezados = list(datos[0].keys())
                    resultados[tabla] = (encabezados, datos)
            return resultados
        except Error as e:
            print(f"Error en búsqueda global: {e}")
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    @staticmethod
    def formatear_nombre_tabla(nombre):
        return nombre.replace('_', ' ').title()

class ConfiguracionDialog(QDialog):
    """Diálogo para configurar la conexión a MySQL con pestañas"""
    def __init__(self, config_actual, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Conexión")
        self.setWindowIcon(QIcon("RUTA/imagenes/gestion-de-base-de-datos.png"))
        self.setModal(True)
        self.config_actual = config_actual
        
        # Crear pestañas
        self.tab_widget = QTabWidget()
        
        # Pestaña de configuración básica
        self.tab_basica = QWidget()
        self.setup_ui_basica()
        
        # Pestaña de configuración avanzada
        self.tab_avanzada = QWidget()
        self.setup_ui_avanzada()
        
        # Agregar pestañas al widget
        self.tab_widget.addTab(self.tab_basica, "Básica")
        self.tab_widget.addTab(self.tab_avanzada, "Avanzada")
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_aceptar = QPushButton("Aceptar")
        btn_cancelar = QPushButton("Cancelar")
        btn_aceptar.clicked.connect(self.accept)
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_aceptar)
        btn_layout.addWidget(btn_cancelar)
        
        # Layout principal
        layout = QVBoxLayout()
        layout.addWidget(self.tab_widget)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
    def setup_ui_basica(self):
        """Configura la interfaz de la pestaña básica (solo host)"""
        layout = QVBoxLayout(self.tab_basica)
        layout.setContentsMargins(20, 20, 20, 20)
        
        group = QGroupBox("Configuración Rápida")
        group_layout = QVBoxLayout()
        
        host_layout = QHBoxLayout()
        host_label = QLabel("Host/IP:")
        self.host_basico_input = QLineEdit(self.config_actual['host'])
        host_layout.addWidget(host_label)
        host_layout.addWidget(self.host_basico_input)
        
        group_layout.addLayout(host_layout)
        group.setLayout(group_layout)
        
        layout.addWidget(group)
        layout.addStretch()
        
    def setup_ui_avanzada(self):
        """Configura la interfaz de la pestaña avanzada (todos los campos)"""
        layout = QVBoxLayout(self.tab_avanzada)
        layout.setContentsMargins(20, 20, 20, 20)
        
        group = QGroupBox("Configuración Completa")
        group_layout = QVBoxLayout()
        
        # Host
        host_layout = QHBoxLayout()
        host_label = QLabel("Host/IP:")
        self.host_avanzado_input = QLineEdit(self.config_actual['host'])
        host_layout.addWidget(host_label)
        host_layout.addWidget(self.host_avanzado_input)
        group_layout.addLayout(host_layout)
        
        # Puerto
        port_layout = QHBoxLayout()
        port_label = QLabel("Puerto:")
        self.port_input = QLineEdit(str(self.config_actual.get('port', 3306)))
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_input)
        group_layout.addLayout(port_layout)
        
        # Usuario
        user_layout = QHBoxLayout()
        user_label = QLabel("Usuario:")
        self.user_input = QLineEdit(self.config_actual['user'])
        user_layout.addWidget(user_label)
        user_layout.addWidget(self.user_input)
        group_layout.addLayout(user_layout)
        
        # Contraseña
        pass_layout = QHBoxLayout()
        pass_label = QLabel("Contraseña:")
        self.pass_input = QLineEdit(self.config_actual['password'])
        self.pass_input.setEchoMode(QLineEdit.Password)
        pass_layout.addWidget(pass_label)
        pass_layout.addWidget(self.pass_input)
        group_layout.addLayout(pass_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        layout.addStretch()
        
    def get_config(self):
        """Obtiene la configuración completa según la pestaña activa"""
        if self.tab_widget.currentIndex() == 0:  # Pestaña básica
            return {
                'host': self.host_basico_input.text(),
                'port': self.config_actual.get('port', 3306),
                'user': self.config_actual.get('user', ''),
                'password': self.config_actual.get('password', ''),
                'database': self.config_actual.get('database', '')
            }
        else:  # Pestaña avanzada
            try:
                port = int(self.port_input.text())
            except ValueError:
                port = 3306
                
            return {
                'host': self.host_avanzado_input.text(),
                'port': port,
                'user': self.user_input.text(),
                'password': self.pass_input.text()
            }

class ConexionThread(QThread):
    """Hilo para verificar la conexión a MySQL sin bloquear la UI"""
    conexion_result = pyqtSignal(bool, str)
    
    def __init__(self, gestor):
        super().__init__()
        self.gestor = gestor
    
    def run(self):
        try:
            resultado = self.gestor.verificar_conexion()
            if resultado:
                self.conexion_result.emit(True, "Conexión establecida correctamente")
            else:
                self.conexion_result.emit(False, "No se pudo establecer la conexión")
        except Exception as e:
            self.conexion_result.emit(False, f"Error: {str(e)}")

class MainWindow(QMainWindow):
    """Ventana principal de la aplicación AISA Revens Data"""
    def __init__(self):
        super().__init__()
        self.gestor_conexion = GestorConexion()
        self.datos_actuales = None
        self.init_ui()
        self.verificar_conexion_inicial()
        self.setup_auto_refresh()
        self.showMaximized()
    
    def init_ui(self):
        self.setWindowTitle("AISA Revens Data - Grupo AISA")
        self.setGeometry(100, 100, 1000, 700)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QLabel {
                color: #343a40;
                font-size: 11px;
                font-weight: bold;
            }
            QComboBox {
                padding: 6px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: transparent;
                min-height: 20px;
                font-size: 11px;
            }
            QComboBox:hover {
                border: 1px solid #adb5bd;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #ced4da;
                selection-background-color: #4361ee;
                selection-color: blue;
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url("RUTA/imagenes/flecha.png");
                margin-right: 20px;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
                font-size: 11px;
            }
            QPushButton {
                background-color: #4361ee;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #3a56d4;
            }
            QPushButton:pressed {
                background-color: #2f4bc2;
            }
            QTableWidget {
                border: 1px solid #dee2e6;
                background-color: white;
                font-size: 11px;
                gridline-color: #e9ecef;
            }
            QHeaderView::section {
                background-color: #f1f3f5;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
            QTextEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
                padding: 8px;
                font-size: 11px;
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
                padding: 5px;
            }
            QTabBar::tab {
                padding: 8px 12px;
                background: #f1f3f5;
                border: 1px solid #ddd;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #fff;
                border-bottom: 2px solid #4361ee;
            }
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        header_frame = QFrame()
        header_frame.setFrameShape(QFrame.StyledPanel)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setSpacing(15)
        header_layout.setContentsMargins(10, 10, 10, 10)

        db_frame = QFrame()
        db_frame.setFrameShape(QFrame.StyledPanel)
        db_layout = QVBoxLayout(db_frame)
        db_layout.setSpacing(5)
        db_label = QLabel("Seleccione una base de datos")
        self.db_combo = QComboBox()
        self.db_combo.setFixedWidth(250)
        self.db_combo.setPlaceholderText("Seleccione base de datos...")
        self.db_combo.currentTextChanged.connect(self.on_database_selected)
        db_layout.addWidget(db_label)
        db_layout.addWidget(self.db_combo)

        tabla_frame = QFrame()
        tabla_frame.setFrameShape(QFrame.StyledPanel)
        tabla_layout = QVBoxLayout(tabla_frame)
        tabla_layout.setSpacing(5)
        tabla_label = QLabel("Seleccione una tabla")
        self.tabla_combo = QComboBox()
        self.tabla_combo.setFixedWidth(250)
        self.tabla_combo.setPlaceholderText("Seleccione tabla...")
        self.tabla_combo.setEnabled(False)
        self.tabla_combo.currentTextChanged.connect(self.on_tabla_seleccionada)
        tabla_layout.addWidget(tabla_label)
        tabla_layout.addWidget(self.tabla_combo)

        search_frame = QFrame()
        search_frame.setFrameShape(QFrame.StyledPanel)
        search_layout = QVBoxLayout(search_frame)
        search_layout.setSpacing(5)
        search_label = QLabel("Buscar en toda la base de datos")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ingrese texto a buscar...")
        self.search_input.setFixedWidth(400)
        self.search_input.textChanged.connect(self.filtrar_datos)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)

        header_layout.addWidget(db_frame)
        header_layout.addWidget(tabla_frame)
        header_layout.addWidget(search_frame)
        header_layout.addStretch()

        content_frame = QFrame()
        content_frame.setFrameShape(QFrame.StyledPanel)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(10, 10, 10, 10)

        self.tabla_title = QLabel("Tabla seleccionada: ninguna")
        self.tabla_title.setFont(QFont("Arial", 12, QFont.Bold))
        self.tabla_title.setStyleSheet("color: #495057;")

        self.table_widget = QTableWidget()
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.verticalHeader().setVisible(False)

        content_layout.addWidget(self.tabla_title)
        content_layout.addWidget(self.table_widget)
        
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setSpacing(15)
        
        self.btn_agregar_base = QPushButton("Agregar base de datos")
        self.btn_agregar_base.clicked.connect(self.agregar_base_datos)
        
        self.btn_agregar_tabla = QPushButton("Agregar/modificar tabla")
        self.btn_agregar_tabla.clicked.connect(self.agregar_modificar_tabla)
        self.btn_agregar_tabla.setEnabled(True)
        
        button_layout.addWidget(self.btn_agregar_base)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_agregar_tabla)
        
        footer_label = QLabel("Ravens Developers © - Grupo AISA")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: #6c757d; font-size: 10px; margin-top: 10px;")
        
        main_layout.addWidget(header_frame)
        main_layout.addWidget(content_frame, 1)
        main_layout.addWidget(button_frame)
        main_layout.addWidget(footer_label)
        
        central_widget.setLayout(main_layout)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.btn_config_status = QPushButton()
        self.btn_config_status.setIcon(QIcon(QPixmap("RUTA/imagenes/gestion-de-base-de-datos.png")))
        self.btn_config_status.setFixedSize(24, 24)
        self.btn_config_status.setToolTip("Configurar conexión")
        self.btn_config_status.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                margin: 0 5px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 12px;
            }
        """)
        self.btn_config_status.clicked.connect(self.mostrar_dialogo_configuracion)
        
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.addWidget(self.btn_config_status)
        
        self.status_bar.addPermanentWidget(status_widget)
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #f0f0f0;
                color: #333;
                font-size: 11px;
                border-top: 1px solid #ddd;
            }
        """)
        
        self.notification = NotificationWidget(self)
        self.notification.hide()
    
    def filtrar_datos(self):
        search_text = self.search_input.text().strip()
        
        if not search_text:
            if self.tabla_combo.currentText() and self.tabla_combo.currentText() != "No hay tablas disponibles":
                self.mostrar_datos_tabla(self.tabla_combo.currentText())
            return
        
        resultados = self.gestor_conexion.buscar_en_toda_bd(search_text)
        
        if not resultados:
            self.mostrar_resultados_globales({}, search_text)
            return
        
        self.mostrar_resultados_globales(resultados, search_text)
    
    def mostrar_resultados_globales(self, resultados, search_text):
        self.table_widget.clear()
        
        if not resultados:
            self.tabla_title.setText(f"Búsqueda: '{search_text}' - 0 resultados")
            self.table_widget.setRowCount(1)
            self.table_widget.setColumnCount(1)
            item = QTableWidgetItem("No se encontraron resultados en ninguna tabla")
            item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setItem(0, 0, item)
            return
        
        total_resultados = sum(len(datos[1]) for datos in resultados.values())
        self.tabla_title.setText(f"Búsqueda: '{search_text}' - {total_resultados} resultados en {len(resultados)} tablas")
        
        encabezados_comunes = ["Tabla de origen"]
        
        todos_encabezados = set()
        for encabezados, _ in resultados.values():
            todos_encabezados.update(encabezados)
        
        encabezados_comunes.extend(sorted(todos_encabezados))
        
        self.table_widget.setColumnCount(len(encabezados_comunes))
        self.table_widget.setHorizontalHeaderLabels(encabezados_comunes)
        
        filas = []
        for tabla, (encabezados, datos) in resultados.items():
            nombre_formateado = self.gestor_conexion.formatear_nombre_tabla(tabla)
            
            for fila in datos:
                nueva_fila = {"Tabla de origen": nombre_formateado}
                for k, v in fila.items():
                    nueva_fila[k] = str(v)
                filas.append(nueva_fila)
        
        self.table_widget.setRowCount(len(filas))
        
        for row_idx, fila in enumerate(filas):
            for col_idx, encabezado in enumerate(encabezados_comunes):
                valor = fila.get(encabezado, "")
                item = QTableWidgetItem(valor)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                
                if search_text.lower() in valor.lower():
                    item.setBackground(QColor(255, 255, 150))
                
                self.table_widget.setItem(row_idx, col_idx, item)
        
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    
    def setup_auto_refresh(self):
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.auto_refresh_data)
        self.refresh_timer.start(30000)
    
    def auto_refresh_data(self):
        if self.tabla_combo.currentText() and self.tabla_combo.currentText() != "No hay tablas disponibles":
            current_table = self.tabla_combo.currentText()
            self.mostrar_datos_tabla(current_table)
    
    def verificar_conexion_inicial(self):
        self.thread_conexion = ConexionThread(self.gestor_conexion)
        self.thread_conexion.conexion_result.connect(self.mostrar_resultado_conexion)
        self.thread_conexion.start()
    
    def mostrar_resultado_conexion(self, exito, mensaje):
        if exito:
            self.notification.show_notification("Conexión exitosa a MySQL", True)
            self.status_bar.showMessage("Conectado al servidor MySQL")
            self.status_bar.setStyleSheet("""
                QStatusBar {
                    background-color: #e8f5e9;
                    color: #2e7d32;
                    font-size: 11px;
                    border-top: 1px solid #c8e6c9;
                }
                QPushButton {
                    background-color: transparent;
                    border: none;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.2);
                    border-radius: 12px;
                }
            """)
            
            self.cargar_bases_datos()
            
            self.db_combo.setEnabled(True)
            self.tabla_combo.setEnabled(False)
            self.search_input.setEnabled(False)
            self.btn_agregar_base.setEnabled(True)
            self.btn_agregar_tabla.setEnabled(False)
        else:
            self.notification.show_notification(f"Error de conexión: {mensaje}", False)
            self.status_bar.showMessage("Sin conexión - " + mensaje)
            self.status_bar.setStyleSheet("""
                QStatusBar {
                    background-color: #ffebee;
                    color: #c62828;
                    font-size: 11px;
                    border-top: 1px solid #ffcdd2;
                }
            """)
            
            self.mostrar_mensaje_error(mensaje)
            
            self.tabla_combo.setEnabled(False)
            self.search_input.setEnabled(False)
            self.btn_agregar_base.setEnabled(False)
            self.btn_agregar_tabla.setEnabled(False)
    
    def mostrar_mensaje_error(self, mensaje):
        self.table_widget.clear()
        self.table_widget.setRowCount(1)
        self.table_widget.setColumnCount(1)
        self.table_widget.setHorizontalHeaderLabels(["Error de Conexión"])
        item = QTableWidgetItem(mensaje)
        item.setTextAlignment(Qt.AlignCenter)
        self.table_widget.setItem(0, 0, item)
        self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    
    def cargar_bases_datos(self):
        self.db_combo.clear()
        bases_datos = self.gestor_conexion.obtener_bases_datos()
        if bases_datos:
            self.db_combo.addItem("")
            self.db_combo.addItems(bases_datos)
        else:
            self.notification.show_notification("No se encontraron bases de datos", False)

    def on_database_selected(self, database):
        if not database:
            self.tabla_combo.clear()
            self.tabla_combo.setEnabled(False)
            self.search_input.setEnabled(False) 
            self.tabla_title.setText("Tabla seleccionada: ninguna")
            self.table_widget.clear()
            return
        
        if self.gestor_conexion.seleccionar_base_datos(database):
            self.cargar_tablas()
            self.notification.show_notification(f"Base de datos {database} seleccionada", True)
        else:
            self.notification.show_notification(f"Error al seleccionar la base de datos {database}", False)
    
    def cargar_tablas(self):
        try:
            tablas = self.gestor_conexion.obtener_tablas()
            self.tabla_combo.clear()
            
            if tablas:
                self.tabla_combo.addItem("")
                for tabla in tablas:
                    nombre_formateado = self.gestor_conexion.formatear_nombre_tabla(tabla)
                    self.tabla_combo.addItem(nombre_formateado)
                self.tabla_combo.setEnabled(True)
                self.search_input.setEnabled(True)
                self.btn_agregar_tabla.setEnabled(True)
            else:
                self.tabla_combo.setEnabled(False)
                self.search_input.setEnabled(False)
                self.btn_agregar_tabla.setEnabled(False)
                self.notification.show_notification("No hay tablas en esta base de datos", False)
        except Exception as e:
            print(f"Error al cargar tablas: {e}")
            self.notification.show_notification("Error al cargar las tablas", False)
            self.tabla_combo.setEnabled(False)
    
    def on_tabla_seleccionada(self, nombre_formateado):
        if not nombre_formateado:
            self.search_input.clear()
            self.tabla_title.setText("Tabla seleccionada: ninguna")
            self.table_widget.clear()
            return
            
        self.search_input.clear()
        self.tabla_title.setText(f"Tabla seleccionada: {nombre_formateado}")
        self.mostrar_datos_tabla(nombre_formateado)
    
    def mostrar_datos_tabla(self, nombre_tabla_formateado):
        encabezados, datos = self.gestor_conexion.obtener_datos_tabla(nombre_tabla_formateado)
        
        self.table_widget.clear()
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(0)
        
        if isinstance(datos, str):
            if datos == "empty":
                self.tabla_title.setText(f"Tabla seleccionada: {nombre_tabla_formateado} (vacía)")
        elif encabezados and datos:
            self.table_widget.setRowCount(len(datos))
            self.table_widget.setColumnCount(len(encabezados))
            self.table_widget.setHorizontalHeaderLabels(encabezados)
            
            for row_idx, fila in enumerate(datos):
                for col_idx, encabezado in enumerate(encabezados):
                    valor = str(fila.get(encabezado, ''))
                    item = QTableWidgetItem(valor)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.table_widget.setItem(row_idx, col_idx, item)
        
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    
    def agregar_base_datos(self):
        try:
            from agregar_base_datos import MySQLDBCreator
            
            dialog = MySQLDBCreator()
            icon_path = "RUTA/imagenes/big-data.png"
            dialog.setWindowIcon(QIcon(icon_path))
            dialog.exec_()
            
            self.cargar_bases_datos()
            
        except Exception as e:
            self.notification.show_notification(
                f"Error al abrir el gestor de bases de datos: {str(e)}", 
                False
            )
    
    def agregar_modificar_tabla(self):
        try:
            if not self.db_combo.currentText():
                self.notification.show_notification(
                    "Debe seleccionar una base de datos primero",
                    False
                )
                return

            from editortabla import MySQLCompleteEditor
            editor = MySQLCompleteEditor()
            editor.showMaximized()
            icon_path = "RUTA/imagenes/big-data.png"
            editor.setWindowIcon(QIcon(icon_path))
            editor.exec_()
            self.cargar_tablas()
            
        except ImportError as e:
            self.notification.show_notification(
                "Error: No se encontró el módulo editortabla.py", 
                False
            )
        except Exception as e:
            self.notification.show_notification(
                f"Error al abrir el editor de tablas: {str(e)}", 
                False
            )
    
    def mostrar_mensaje(self, titulo, mensaje):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(titulo)
        msg.setText(mensaje)
        msg.exec_()
    
    def closeEvent(self, event):
        self.gestor_conexion.cerrar_conexion()
        self.refresh_timer.stop()
        event.accept()
    
    def mostrar_dialogo_configuracion(self):
        dialog = ConfiguracionDialog(self.gestor_conexion.config, self)
        if dialog.exec_() == QDialog.Accepted:
            nueva_config = dialog.get_config()
            
            if dialog.tab_widget.currentIndex() == 0:  # Pestaña básica
                success = self.gestor_conexion.actualizar_configuracion(
                    host=nueva_config['host']
                )
            else:  # Pestaña avanzada
                success = self.gestor_conexion.actualizar_configuracion(
                    host=nueva_config['host'],
                    port=nueva_config['port'],
                    user=nueva_config['user'],
                    password=nueva_config['password'],
                    database=nueva_config['database']
                )
            
            if success:
                self.notification.show_notification(
                    f"Conexión actualizada exitosamente a {nueva_config['host']}", 
                    True
                )
                self.cargar_bases_datos()
            else:
                self.notification.show_notification(
                    f"Error al conectar con {nueva_config['host']}", 
                    False
                )

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(current_dir, "imagenes", "big-data.png")
    window.setWindowIcon(QIcon(icon_path))
    
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
