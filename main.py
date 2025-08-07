#librerias necesarias
import os
import sys
import mysql.connector
from mysql.connector import Error
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QComboBox, QPushButton, 
                             QTextEdit, QMessageBox, QFrame, QTableWidget, 
                             QTableWidgetItem, QLineEdit, QHeaderView, QStatusBar, 
                             QInputDialog, QDialog, QStyle)
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
        
    # Configuración de la UI del widget de notificación    
    def setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("""
            background-color: #323232;
            color: white;
            border-radius: 4px;
            padding: 10px;
        """)
        # Layout del widget de notificación
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
        """Muestra la notificación con el mensaje y estilo apropiado"""
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
            'host': '192.168.1.72',# Cambia esto por tu host/dirección IP
            'port': 3306,
            'user': 'usuario0', #cambia esto por tu usuario
            'password': '@Holamundo0123' #cambia esto por tu contraseña
        }
        self.conexion = None #bjeto de conexión a la BD
        self.database = None #referencia a la base de datos
    
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
        """Obtiene solo las bases de datos de usuario, excluyendo las del sistema"""
        try:
            if not self.conexion or not self.conexion.is_connected():
                self.conexion = mysql.connector.connect(**self.config)
            
            # Lista de bases de datos del sistema que queremos excluir
            bases_sistema = {
                'information_schema', 
                'mysql', 
                'performance_schema', 
                'sys',
                'phpmyadmin'
            }
            #Crea un objeto cursor que permite ejecutar comandos SQL en la conexión establecida
            cursor = self.conexion.cursor() 
            cursor.execute("SHOW DATABASES")
            # Filtrar las bases de datos del sistema
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
        """Obtiene o crea una nueva conexión a MySQL"""
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
        """Obtiene las tablas de la base de datos actual"""
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
        """Cierra la conexión a MySQL si está abierta"""
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
                    # Usar el nombre de la base de datos actual
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
        """
        Busca el texto en todas las tablas de la base de datos.
        """
        resultados = {}
        try:
            conexion = self.obtener_conexion()
            if not conexion:
                return None
            
            cursor = conexion.cursor(dictionary=True)
            
            cursor.execute("SHOW TABLES")
            # Usar self.database en lugar de self.config['database']
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

#clase para manejo de hilos
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

# Clase para el diálogo de configuración de conexión
class ConfiguracionDialog(QDialog):
    """Diálogo para configurar la conexión a MySQL"""
    def __init__(self, config_actual, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Conexión")#titulo del diálogo
        self.setWindowIcon(QIcon("C:/Users/taver/OneDrive/Documentos/Development/AisaRevensData/imagenes/gestion-de-base-de-datos.png"))#icono del diálogo
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # Host
        host_layout = QHBoxLayout()
        host_label = QLabel("Host:")
        self.host_input = QLineEdit(config_actual['host'])
        host_layout.addWidget(host_label)
        host_layout.addWidget(self.host_input)
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_aceptar = QPushButton("Aceptar")
        btn_cancelar = QPushButton("Cancelar")
        btn_aceptar.clicked.connect(self.accept)
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_aceptar)
        btn_layout.addWidget(btn_cancelar)
        
        layout.addLayout(host_layout)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    # Método para obtener la configuración ingresada
    def get_config(self):
        return {'host': self.host_input.text()}

# Clase principal de la aplicación
class MainWindow(QMainWindow):
    """Ventana principal de la aplicación AISA Revens Data"""
    def __init__(self):
        super().__init__()
        self.gestor_conexion = GestorConexion()
        self.datos_actuales = None
        self.init_ui()
        self.verificar_conexion_inicial()
        self.setup_auto_refresh()
        self.showMaximized() #maximizar la ventana

    
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
                image: url("C:/Users/taver/OneDrive/Documentos/Development/AisaRevensData/imagenes/flecha.png");
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
        """)
        # Crear el widget central y establecer el layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Crear el layout principal
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Crear los frames y layouts para la cabecera
        header_frame = QFrame()
        header_frame.setFrameShape(QFrame.StyledPanel)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setSpacing(15)
        header_layout.setContentsMargins(10, 10, 10, 10)

        # Crear los widgets de la cabecera
        db_frame = QFrame()
        db_frame.setFrameShape(QFrame.StyledPanel)
        db_layout = QVBoxLayout(db_frame)
        db_layout.setSpacing(5)
        db_label = QLabel("Seleccione una base de datos")
        self.db_combo = QComboBox()
        self.db_combo.setFixedWidth(250)
        self.db_combo.setPlaceholderText("Seleccione base de datos...")  # Agregar placeholder
        self.db_combo.currentTextChanged.connect(self.on_database_selected)
        db_layout.addWidget(db_label)
        db_layout.addWidget(self.db_combo)

        # Agregar un item vacío al combo de bases de datos
        tabla_frame = QFrame()
        tabla_frame.setFrameShape(QFrame.StyledPanel)
        tabla_layout = QVBoxLayout(tabla_frame)
        tabla_layout.setSpacing(5)
        tabla_label = QLabel("Seleccione una tabla")
        self.tabla_combo = QComboBox()
        self.tabla_combo.setFixedWidth(250)
        self.tabla_combo.setPlaceholderText("Seleccione tabla...") # Agregar placeholder
        self.tabla_combo.setEnabled(False)  # Deshabilitar hasta que se seleccione BD
        self.tabla_combo.currentTextChanged.connect(self.on_tabla_seleccionada)
        tabla_layout.addWidget(tabla_label)
        tabla_layout.addWidget(self.tabla_combo)

        # Agregar un item vacío al combo de tablas
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

        # Agregar un item vacío al campo de búsqueda
        header_layout.addWidget(db_frame)
        header_layout.addWidget(tabla_frame)
        header_layout.addWidget(search_frame)
        header_layout.addStretch()

        # Crear el contenido principal
        content_frame = QFrame()
        content_frame.setFrameShape(QFrame.StyledPanel)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # Título de la tabla
        self.tabla_title = QLabel("Tabla seleccionada: ninguna")
        self.tabla_title.setFont(QFont("Arial", 12, QFont.Bold))
        self.tabla_title.setStyleSheet("color: #495057;")

        # Crear la tabla para mostrar los datos
        self.table_widget = QTableWidget()
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.verticalHeader().setVisible(False)

        # Establecer un estilo para la tabla
        content_layout.addWidget(self.tabla_title)
        content_layout.addWidget(self.table_widget)
        
        # Crear el frame para los botones
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setSpacing(15)
        
        # Botón para agregar base de datos
        self.btn_agregar_base = QPushButton("Agregar base de datos")
        self.btn_agregar_base.clicked.connect(self.agregar_base_datos)
        
        # Modificar la configuración inicial del botón
        self.btn_agregar_tabla = QPushButton("Agregar/modificar tabla")
        self.btn_agregar_tabla.clicked.connect(self.agregar_modificar_tabla)
        self.btn_agregar_tabla.setEnabled(True)  # Habilitamos el botón por defecto
        
        # Modificar el button_layout
        button_layout.addWidget(self.btn_agregar_base)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_agregar_tabla)
        
        # Crear el footer
        footer_label = QLabel("Ravens Developers © - Grupo AISA")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: #6c757d; font-size: 10px; margin-top: 10px;")
        
        # Organizar todo en el layout principal
        main_layout.addWidget(header_frame)
        main_layout.addWidget(content_frame, 1)
        main_layout.addWidget(button_frame)
        main_layout.addWidget(footer_label)
        
        central_widget.setLayout(main_layout)
        
        # Modificar la configuración de la barra de estado
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Crear el botón de configuración con icono de engrane
        self.btn_config_status = QPushButton()
        self.btn_config_status.setIcon(QIcon(QPixmap("C:/Users/taver/OneDrive/Documentos/Development/AisaRevensData/imagenes/gestion-de-base-de-datos.png")))
        self.btn_config_status.setFixedSize(24, 24)
        self.btn_config_status.setToolTip("Configurar conexión")  # Agregar tooltip
        self.btn_config_status.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                margin: 0 5px;  /* Agregar un poco de margen */
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 12px;
            }
        """)
        self.btn_config_status.clicked.connect(self.mostrar_dialogo_configuracion)
        
        # Crear widget permanente para el botón
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.addWidget(self.btn_config_status)
        
        # Agregar elementos a la barra de estado
        self.status_bar.addPermanentWidget(status_widget)  # Permanente a la derecha
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
        """Filtra los datos en toda la base de datos según el texto ingresado"""
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
        """Muestra los resultados de la búsqueda global en la tabla"""
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
        """Configura un temporizador para refrescar automáticamente los datos cada 30 segundos"""
         # Temporizador para refrescar automáticamente los datos
         # Cada 30 segundos
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.auto_refresh_data)
        self.refresh_timer.start(30000)
    
    def auto_refresh_data(self):
        """Refresca los datos automáticamente si hay una tabla seleccionada"""
        if self.tabla_combo.currentText() and self.tabla_combo.currentText() != "No hay tablas disponibles":
            current_table = self.tabla_combo.currentText()
            self.mostrar_datos_tabla(current_table)
    
    def verificar_conexion_inicial(self):
        """Verifica la conexión inicial a MySQL y muestra el diálogo de configuración si es necesario"""
        self.thread_conexion = ConexionThread(self.gestor_conexion)
        self.thread_conexion.conexion_result.connect(self.mostrar_resultado_conexion)
        self.thread_conexion.start()
    
    def mostrar_resultado_conexion(self, exito, mensaje):
        """Muestra el resultado de la verificación de conexión"""
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
            
            # Cargar las bases de datos disponibles
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
        """Muestra un mensaje de error en la tabla cuando no se puede conectar a MySQL"""
        self.table_widget.clear()
        self.table_widget.setRowCount(1)
        self.table_widget.setColumnCount(1)
        self.table_widget.setHorizontalHeaderLabels(["Error de Conexión"])
        item = QTableWidgetItem(mensaje)
        item.setTextAlignment(Qt.AlignCenter)
        self.table_widget.setItem(0, 0, item)
        self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    
    def cargar_bases_datos(self):
        """Carga las bases de datos disponibles en el combo box"""
        self.db_combo.clear()
        bases_datos = self.gestor_conexion.obtener_bases_datos()
        if bases_datos:
            self.db_combo.addItem("")  # Agregar item vacío
            self.db_combo.addItems(bases_datos)
        else:
            self.notification.show_notification("No se encontraron bases de datos", False)

    def on_database_selected(self, database):
        """Maneja la selección de una base de datos en el combo box"""
        if not database:  # Si no hay selección, limpiar y deshabilitar controles
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
        """Carga las tablas de la base de datos seleccionada en el combo box"""
        try:
            tablas = self.gestor_conexion.obtener_tablas()
            self.tabla_combo.clear()
            
            if tablas:
                self.tabla_combo.addItem("")  # Agregar item vacío
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
        """Maneja la selección de una tabla en el combo box"""
        if not nombre_formateado:  # Si no hay selección, limpiar vista
            self.search_input.clear()
            self.tabla_title.setText("Tabla seleccionada: ninguna")
            self.table_widget.clear()
            return
            
        self.search_input.clear()
        self.tabla_title.setText(f"Tabla seleccionada: {nombre_formateado}")
        self.mostrar_datos_tabla(nombre_formateado)
    
    def mostrar_datos_tabla(self, nombre_tabla_formateado):
        """Muestra los datos de la tabla seleccionada en el QTableWidget"""
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
        """Abre el diálogo para agregar o modificar bases de datos"""
        try:
            # Importar la clase MySQLDBCreator del módulo agregar_base_datos
            from agregar_base_datos import MySQLDBCreator
            
            # Crear y mostrar el diálogo de gestión de bases de datos
            dialog = MySQLDBCreator()

            #icono 
            icon_path = "C:/Users/taver/OneDrive/Documentos/Development/AisaRevensData/imagenes/big-data.png"
            dialog.setWindowIcon(QIcon(icon_path))#carga la imagen del icono

            dialog.exec_()
            
            # Recargar la lista de bases de datos después de cerrar el diálogo
            self.cargar_bases_datos()
            
        except Exception as e:
            self.notification.show_notification(
                f"Error al abrir el gestor de bases de datos: {str(e)}", 
                False
            )
    
    def agregar_modificar_tabla(self):
        """Abre el diálogo para agregar o modificar tablas"""
         # Importar la clase MySQLCompleteEditor del módulo editortabla
        try:
            # Verificar que haya una base de datos seleccionada
            if not self.db_combo.currentText():
                self.notification.show_notification(
                    "Debe seleccionar una base de datos primero",
                    False
                )
                return

            # Importar la clase MySQLCompleteEditor del módulo editortabla
            from editortabla import MySQLCompleteEditor

            # Crear y mostrar el diálogo del editor de tablas
            editor = MySQLCompleteEditor()
            editor.showMaximized()  # Asegurar que se muestre maximizado

            # Configurar el icono del editor
            icon_path = "C:/Users/taver/OneDrive/Documentos/Development/AisaRevensData/imagenes/big-data.png"
            editor.setWindowIcon(QIcon(icon_path))#carga la imagen del icono


            editor.exec_()

            # Recargar las tablas después de cerrar el diálogo
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
        """Muestra un mensaje de información en un cuadro de diálogo"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(titulo)
        msg.setText(mensaje)
        msg.exec_()
    
    def closeEvent(self, event):
        """Maneja el evento de cierre de la ventana principal"""
        self.gestor_conexion.cerrar_conexion()
        self.refresh_timer.stop()
        event.accept()
    
    def mostrar_dialogo_configuracion(self):
        """Muestra un diálogo personalizado para la configuración"""
        dialog = ConfiguracionDialog(self.gestor_conexion.config, self)
        if dialog.exec_() == QDialog.Accepted:
            nueva_config = dialog.get_config()
            if self.gestor_conexion.actualizar_configuracion(nueva_config['host']):
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
    """Función principal para iniciar la aplicación"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()

    # Configurar el icono de la aplicación
    current_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(current_dir, "imagenes", "big-data.png")
    window.setWindowIcon(QIcon(icon_path))
    
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()