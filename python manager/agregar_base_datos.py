#librerias necesarias 
import os
import sys
import re
import mysql.connector
from mysql.connector import Error
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QGroupBox, QFormLayout, QSpinBox, QTextEdit,
    QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal 
from PyQt5.QtGui import QFont, QIcon, QColor

class DatabaseThread(QThread):
    """Clase base para operaciones con bases de datos"""
    resultado = pyqtSignal(bool, str, list)
    
    def __init__(self, config, operation, db_name=None):
        super().__init__()
        self.config = config
        self.operation = operation
        self.db_name = db_name

class CrearBaseDatosThread(DatabaseThread):
    """Thread para crear la base de datos"""
    def run(self):
        try:
            conexion = mysql.connector.connect(**self.config)
            cursor = conexion.cursor()
            cursor.execute(f"CREATE DATABASE `{self.db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.execute("SHOW DATABASES")
            bases = [db[0] for db in cursor.fetchall() if db[0] not in ['information_schema', 'mysql', 'performance_schema', 'sys']]
            cursor.close()
            conexion.close()
            self.resultado.emit(True, f"Base de datos '{self.db_name}' creada exitosamente", bases)
        except Error as e:
            self.resultado.emit(False, f"Error MySQL: {str(e)}", [])

class ListarBasesDatosThread(DatabaseThread):
    """Thread para listar bases de datos"""
    def run(self):
        try:
            conexion = mysql.connector.connect(**self.config)
            cursor = conexion.cursor()
            cursor.execute("SHOW DATABASES")
            bases = [db[0] for db in cursor.fetchall() if db[0] not in ['information_schema', 'mysql', 'performance_schema', 'sys']]
            cursor.close()
            conexion.close()
            
            self.resultado.emit(True, "Bases de datos listadas correctamente", bases)
        except Error as e:
            self.resultado.emit(False, f"Error al listar bases de datos: {str(e)}", [])

class EliminarBaseDatosThread(DatabaseThread):
    """Thread para eliminar una base de datos"""
    def run(self):
        try:
            conexion = mysql.connector.connect(**self.config)
            cursor = conexion.cursor()
            cursor.execute(f"DROP DATABASE `{self.db_name}`")
            
            # Obtener lista actualizada de bases de datos
            cursor.execute("SHOW DATABASES")
            bases = [db[0] for db in cursor.fetchall() if db[0] not in ['information_schema', 'mysql', 'performance_schema', 'sys']]
            
            cursor.close()
            conexion.close()
            
            self.resultado.emit(True, f"Base de datos '{self.db_name}' eliminada exitosamente", bases)
        except Error as e:
            self.resultado.emit(False, f"Error al eliminar base de datos: {str(e)}", [])

class MySQLDBCreator(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MySQL Database Manager")
        self.setFixedSize(680, 680)
        self.config_servidor = {}
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title = QLabel("MySQL Database Manager")
        title.setFont(QFont('Arial', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Configuración del Servidor
        server_group = QGroupBox("Configuración del Servidor MySQL")
        server_layout = QFormLayout()
        
        self.host = QLineEdit("localhost")
        self.port = QSpinBox()
        self.port.setRange(1, 65535)
        self.port.setValue(3306)
        self.user = QLineEdit("root")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        
        server_layout.addRow("Host/IP del servidor:", self.host)
        server_layout.addRow("Puerto:", self.port)
        server_layout.addRow("Usuario:", self.user)
        server_layout.addRow("Contraseña:", self.password)
        
        self.test_btn = QPushButton("Conectar al Servidor")
        self.test_btn.clicked.connect(self.conectar_servidor)
        server_layout.addRow(self.test_btn)
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # Crear Nueva Base de Datos
        create_group = QGroupBox("Crear Nueva Base de Datos")
        create_layout = QFormLayout()
        
        self.db_name = QLineEdit()
        self.db_name.setPlaceholderText("Nombre de la nueva base de datos")
        create_layout.addRow("Nombre:", self.db_name)
        
        self.create_btn = QPushButton("Crear Base de Datos")
        self.create_btn.clicked.connect(self.crear_bd)
        self.create_btn.setEnabled(False)
        create_layout.addRow(self.create_btn)
        
        create_group.setLayout(create_layout)
        layout.addWidget(create_group)
        
        # Gestión de Bases de Datos
        manage_group = QGroupBox("Gestión de Bases de Datos")
        manage_layout = QVBoxLayout()
        
        self.db_list = QListWidget()
        self.db_list.itemDoubleClicked.connect(self.mostrar_opciones_db)
        manage_layout.addWidget(self.db_list)
        
        self.refresh_btn = QPushButton("Actualizar Lista")
        self.refresh_btn.clicked.connect(self.actualizar_lista_bd)
        self.refresh_btn.setEnabled(False)
        manage_layout.addWidget(self.refresh_btn)
        
        manage_group.setLayout(manage_layout)
        layout.addWidget(manage_group)
        
        # Información del Servidor
        self.info = QTextEdit()
        self.info.setPlainText("Conecte al servidor para comenzar...")
        self.info.setReadOnly(True)
        layout.addWidget(self.info)
        
        self.setLayout(layout)
    
    def conectar_servidor(self):
        config = {
            'host': self.host.text(),
            'port': self.port.value(),
            'user': self.user.text(),
            'password': self.password.text()
        }
        
        self.test_btn.setEnabled(False)
        self.test_btn.setText("Conectando...")
        
        self.thread = ListarBasesDatosThread(config, 'list')
        self.thread.resultado.connect(self.conexion_resultado)
        self.thread.start()
    
    def conexion_resultado(self, success, message, databases):
        self.test_btn.setEnabled(True)
        self.test_btn.setText("Conectar al Servidor")
        
        if success:
            self.config_servidor = {
                'host': self.host.text(),
                'port': self.port.value(),
                'user': self.user.text(),
                'password': self.password.text()
            }
            self.info.setPlainText(f" {message}")
            self.lista_actualizada(True, "", databases)
            self.create_btn.setEnabled(True)
            self.refresh_btn.setEnabled(True)
        else:
            self.info.setPlainText(f" {message}")
            QMessageBox.critical(self, "Error", message)
    
    def actualizar_lista_bd(self):
        self.thread = ListarBasesDatosThread(self.config_servidor, 'list')
        self.thread.resultado.connect(self.lista_actualizada)
        self.thread.start()
    
    def lista_actualizada(self, success, message, databases):
        self.db_list.clear()
        if success:
            for db in databases:
                item = QListWidgetItem(db)
                item.setForeground(QColor(0, 0, 255))
                self.db_list.addItem(item)
        else:
            QMessageBox.critical(self, "Error", message)
    
    def mostrar_opciones_db(self, item):
        db_name = item.text()
        menu = QMessageBox()
        menu.setWindowTitle(f"Opciones para: {db_name}")
        menu.setText(f"¿Qué desea hacer con la base de datos '{db_name}'?")
        
        delete_btn = menu.addButton("Eliminar", QMessageBox.DestructiveRole)
        menu.addButton("Cancelar", QMessageBox.RejectRole)
        
        menu.exec_()
        
        if menu.clickedButton() == delete_btn:
            self.eliminar_bd(db_name)
    
    def eliminar_bd(self, db_name):
        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Está seguro de eliminar la base de datos '{db_name}'?\n¡Esta acción no se puede deshacer!",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.thread = EliminarBaseDatosThread(self.config_servidor, 'delete', db_name)
            self.thread.resultado.connect(self.eliminacion_resultado)
            self.thread.start()
    
    def eliminacion_resultado(self, success, message, databases):
        if success:
            QMessageBox.information(self, "Éxito", message)
            self.lista_actualizada(True, "", databases)
        else:
            QMessageBox.critical(self, "Error", message)
    
    def crear_bd(self):
        nombre = self.db_name.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Advertencia", "Ingrese un nombre para la base de datos")
            return
        
        if not re.match(r'^[a-zA-Z0-9_]+$', nombre):
            QMessageBox.warning(self, "Advertencia", "Nombre inválido. Solo use letras, números y _")
            return
        
        reply = QMessageBox.question(
            self, "Confirmar",
            f"¿Crear base de datos '{nombre}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.thread = CrearBaseDatosThread(self.config_servidor, 'create', nombre)
            self.thread.resultado.connect(self.creacion_resultado)
            self.thread.start()
    
    def creacion_resultado(self, success, message, databases):
        if success:
            QMessageBox.information(self, "Éxito", message)
            self.db_name.clear()
            self.lista_actualizada(True, "", databases)
        else:
            QMessageBox.critical(self, "Error", message)

def main():
    app = QApplication(sys.argv)
    window = MySQLDBCreator()
    window.show()
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(current_dir, "imagenes", "big-data.png")
    window.setWindowIcon(QIcon(icon_path))

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
