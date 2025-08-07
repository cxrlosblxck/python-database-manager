import os
import sys
import logging
import mysql.connector
from mysql.connector import Error
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QGroupBox, QFormLayout, QSpinBox, QTextEdit,
    QListWidget, QListWidgetItem, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QWidget, QInputDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QColor

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('mysql_editor')

class DatabaseThread(QThread):
    """Clase base para operaciones con bases de datos"""
    resultado = pyqtSignal(bool, str, list)
    
    def __init__(self, config, operation, db_name=None, table_name=None, data=None):
        super().__init__()
        self.config = config
        self.operation = operation
        self.db_name = db_name
        self.table_name = table_name
        self.data = data
        self._is_running = True

    def stop(self):
        """Detener el hilo de manera segura"""
        self._is_running = False
        self.quit()
        self.wait(1000)

    def run(self):
        try:
            if not self._is_running:
                return
                
            # Implementación específica en las subclases
            pass
            
        except Exception as e:
            if self._is_running:
                self.resultado.emit(False, f"Error: {str(e)}", [])

class ConnectThread(DatabaseThread):
    """Thread para conectar y listar bases de datos"""
    def run(self):
        try:
            if not self._is_running:
                return
                
            conexion = mysql.connector.connect(**self.config)
            cursor = conexion.cursor()
            cursor.execute("SHOW DATABASES")
            bases = [db[0] for db in cursor.fetchall()]
            cursor.close()
            conexion.close()
            
            if self._is_running:
                self.resultado.emit(True, "Conexión exitosa", bases)
                
        except Error as e:
            if self._is_running:
                self.resultado.emit(False, f"Error de conexión: {str(e)}", [])

class ListTablesThread(DatabaseThread):
    """Thread para listar tablas de una base de datos"""
    def run(self):
        try:
            if not self._is_running:
                return
                
            config = self.config.copy()
            config['database'] = self.db_name
            conexion = mysql.connector.connect(**config)
            cursor = conexion.cursor()
            cursor.execute("SHOW TABLES")
            tablas = [table[0] for table in cursor.fetchall()]
            cursor.close()
            conexion.close()
            
            if self._is_running:
                self.resultado.emit(True, f"Tablas de '{self.db_name}' listadas", tablas)
                
        except Error as e:
            if self._is_running:
                self.resultado.emit(False, f"Error al listar tablas: {str(e)}", [])

class DescribeTableThread(DatabaseThread):
    """Thread para describir la estructura de una tabla"""
    def run(self):
        try:
            if not self._is_running:
                return
                
            config = self.config.copy()
            config['database'] = self.db_name
            conexion = mysql.connector.connect(**config)
            cursor = conexion.cursor()
            cursor.execute(f"DESCRIBE `{self.table_name}`")
            columnas = cursor.fetchall()
            cursor.close()
            conexion.close()
            
            if self._is_running:
                self.resultado.emit(True, f"Estructura de '{self.table_name}'", columnas)
                
        except Error as e:
            if self._is_running:
                self.resultado.emit(False, f"Error al describir tabla: {str(e)}", [])

class FetchDataThread(DatabaseThread):
    """Thread para obtener datos de una tabla"""
    def run(self):
        try:
            if not self._is_running:
                return
                
            config = self.config.copy()
            config['database'] = self.db_name
            conexion = mysql.connector.connect(**config)
            cursor = conexion.cursor(dictionary=True)
            cursor.execute(f"SELECT * FROM `{self.table_name}` LIMIT 500")
            datos = cursor.fetchall()
            cursor.close()
            conexion.close()
            
            if self._is_running:
                self.resultado.emit(True, f"Datos de '{self.table_name}'", datos)
                
        except Error as e:
            if self._is_running:
                self.resultado.emit(False, f"Error al obtener datos: {str(e)}", [])

class CreateTableThread(DatabaseThread):
    """Thread para crear una nueva tabla"""
    def run(self):
        try:
            if not self._is_running:
                return
                
            config = self.config.copy()
            config['database'] = self.db_name
            conexion = mysql.connector.connect(**config)
            cursor = conexion.cursor()
            
            cursor.execute(self.data['query'])
            conexion.commit()
            
            cursor.close()
            conexion.close()
            
            if self._is_running:
                self.resultado.emit(True, f"Tabla '{self.table_name}' creada exitosamente", [])
                
        except Error as e:
            if self._is_running:
                self.resultado.emit(False, f"Error al crear tabla: {str(e)}", [])

class MySQLCompleteEditor(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MySQL Complete Editor")
        self.showMaximized()
        
        # Configuración de conexión predefinida
        self.config_servidor = {
            'host': '192.168.1.72',
            'port': 3306,
            'user': 'usuario0',
            'password': '@Holamundo0123'
        }
        
        self.current_db = None
        self.current_table = None
        self.original_data = None
        self.primary_key = None
        self.table_structure = None
        self.active_threads = []
        
        # Inicializar atributos de UI
        self.data_table = None
        self.structure_table = None
        self.sql_editor = None
        self.sql_result = None
        self.execute_sql_btn = None
        self.delete_column_btn = None
        
        self.init_ui()
        self.conectar_servidor()

    def closeEvent(self, event):
        """Manejar el cierre de la aplicación"""
        for thread in self.active_threads:
            if thread.isRunning():
                thread.stop()
        event.accept()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título con botón de ayuda
        title_layout = QHBoxLayout()
        title = QLabel("MySQL Complete Editor")
        title.setFont(QFont('Arial', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        
        # Añadir status_label
        self.status_label = QLabel("No conectado")
        self.status_label.setStyleSheet("font-weight: bold; color: gray;")
        
        title_layout.addWidget(title)
        title_layout.addWidget(self.status_label)
        layout.addLayout(title_layout)
        
        # Selector de Base de Datos y Tabla
        db_table_group = QGroupBox("Selección de Base de Datos y Tabla")
        db_table_layout = QHBoxLayout()

        self.db_combo = QComboBox()
        self.db_combo.setPlaceholderText("Seleccione una base de datos")
        self.db_combo.currentIndexChanged.connect(self.db_seleccionada)

        self.table_combo = QComboBox()
        self.table_combo.setPlaceholderText("Seleccione una tabla")
        self.table_combo.currentIndexChanged.connect(self.tabla_seleccionada)

        self.refresh_btn = QPushButton("Actualizar")
        self.refresh_btn.clicked.connect(self.actualizar_listas)
        self.refresh_btn.setEnabled(False)

        db_table_layout.addWidget(QLabel("Base de datos:"))
        db_table_layout.addWidget(self.db_combo, 1)
        db_table_layout.addWidget(QLabel("Tabla:"))
        db_table_layout.addWidget(self.table_combo, 1)
        db_table_layout.addWidget(self.refresh_btn)

        db_table_group.setLayout(db_table_layout)
        layout.addWidget(db_table_group)
        
        # Pestañas para diferentes operaciones
        self.tabs = QTabWidget()
        
        # Pestaña de Datos (principal)
        self.data_tab = QWidget()
        self.init_data_tab()
        self.tabs.addTab(self.data_tab, "Datos")
        
        # Pestaña de Estructura (solo visualización)
        self.structure_tab = QWidget()
        self.init_structure_tab()
        self.tabs.addTab(self.structure_tab, "Estructura")
        
        # Pestaña de SQL
        self.sql_tab = QWidget()
        self.init_sql_tab()
        self.tabs.addTab(self.sql_tab, "SQL")
        
        layout.addWidget(self.tabs)
        
        self.setLayout(layout)
    
    def init_data_tab(self):
        layout = QVBoxLayout()
        
        self.data_table = QTableWidget()
        
        # Botones de acción
        btn_layout = QHBoxLayout()
        
        self.refresh_data_btn = QPushButton("Actualizar Datos")
        self.refresh_data_btn.clicked.connect(self.actualizar_datos)
        self.refresh_data_btn.setEnabled(False)
        
        self.save_data_btn = QPushButton("Guardar Cambios")
        self.save_data_btn.clicked.connect(self.guardar_datos)
        self.save_data_btn.setEnabled(False)
        self.save_data_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        
        self.add_row_btn = QPushButton("Añadir Fila")
        self.add_row_btn.clicked.connect(self.anadir_fila)
        self.add_row_btn.setEnabled(False)
        
        self.delete_row_btn = QPushButton("Eliminar Fila")
        self.delete_row_btn.clicked.connect(self.eliminar_fila)
        self.delete_row_btn.setEnabled(False)
        self.delete_row_btn.setStyleSheet("background-color: #f44336; color: white;")
        
        self.delete_column_btn = QPushButton("Eliminar Columna")
        self.delete_column_btn.clicked.connect(self.eliminar_columna)
        self.delete_column_btn.setEnabled(False)
        self.delete_column_btn.setStyleSheet("background-color: #FF5722; color: white;")
        
        btn_layout.addWidget(self.refresh_data_btn)
        btn_layout.addWidget(self.save_data_btn)
        btn_layout.addWidget(self.add_row_btn)
        btn_layout.addWidget(self.delete_row_btn)
        btn_layout.addWidget(self.delete_column_btn)
        
        layout.addWidget(self.data_table)
        layout.addLayout(btn_layout)
        
        self.data_tab.setLayout(layout)
    
    def init_structure_tab(self):
        layout = QVBoxLayout()
        
        self.structure_table = QTableWidget()
        self.structure_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.structure_table)
        
        self.structure_tab.setLayout(layout)
    
    def init_sql_tab(self):
        layout = QVBoxLayout()
        
        self.sql_editor = QTextEdit()
        self.sql_editor.setPlaceholderText("Escriba su consulta SQL aquí...")
        
        btn_layout = QHBoxLayout()
        
        self.execute_sql_btn = QPushButton("Ejecutar SQL")
        self.execute_sql_btn.clicked.connect(self.ejecutar_sql)
        self.execute_sql_btn.setEnabled(False)
        
        self.clear_sql_btn = QPushButton("Limpiar")
        self.clear_sql_btn.clicked.connect(self.limpiar_sql)
        
        btn_layout.addWidget(self.execute_sql_btn)
        btn_layout.addWidget(self.clear_sql_btn)
        
        self.sql_result = QTextEdit()
        self.sql_result.setReadOnly(True)
        
        layout.addWidget(self.sql_editor)
        layout.addLayout(btn_layout)
        layout.addWidget(self.sql_result)
        
        self.sql_tab.setLayout(layout)
    
    def conectar_servidor(self):
        self.status_label.setText("Conectando...")
        self.status_label.setStyleSheet("font-weight: bold; color: blue;")
        
        self.thread = ConnectThread(self.config_servidor, 'connect')
        self.thread.resultado.connect(self.conexion_resultado)
        self.active_threads.append(self.thread)
        self.thread.start()
    
    def conexion_resultado(self, success, message, databases):
        if success:
            bases_sistema = {'information_schema', 'mysql', 'performance_schema', 'sys', 'phpmyadmin'}
            bases_usuario = [bd for bd in databases if bd not in bases_sistema]
            
            self.db_combo.clear()
            self.db_combo.addItems(bases_usuario)
            self.refresh_btn.setEnabled(True)
            self.execute_sql_btn.setEnabled(True)
            
            self.status_label.setText("Conectado")
            self.status_label.setStyleSheet("font-weight: bold; color: green;")
        else:
            self.status_label.setText("Error de conexión")
            self.status_label.setStyleSheet("font-weight: bold; color: red;")
            QMessageBox.critical(self, "Error", message)
    
    def db_seleccionada(self, index):
        if index >= 0:
            self.current_db = self.db_combo.currentText()
            self.actualizar_tablas()
    
    def actualizar_tablas(self):
        if self.current_db:
            self.thread = ListTablesThread(
                self.config_servidor, 
                'list_tables', 
                self.current_db
            )
            self.thread.resultado.connect(self.tablas_listadas)
            self.active_threads.append(self.thread)
            self.thread.start()
    
    def tablas_listadas(self, success, message, tablas):
        if success:
            self.table_combo.clear()
            self.table_combo.addItems(tablas)
            self.current_table = None
            if self.data_table:
                self.data_table.clear()
            if self.structure_table:
                self.structure_table.clear()
            self.original_data = None
            
            # Deshabilitar botones hasta que se seleccione una tabla
            self.refresh_data_btn.setEnabled(False)
            self.save_data_btn.setEnabled(False)
            self.add_row_btn.setEnabled(False)
            self.delete_row_btn.setEnabled(False)
            self.delete_column_btn.setEnabled(False)
        else:
            QMessageBox.critical(self, "Error", message)
    
    def tabla_seleccionada(self, index):
        if index >= 0 and self.current_db:
            self.current_table = self.table_combo.currentText()
            
            # Habilitar botones principales
            self.refresh_data_btn.setEnabled(True)
            self.save_data_btn.setEnabled(True)
            self.add_row_btn.setEnabled(True)
            self.delete_row_btn.setEnabled(True)
            self.delete_column_btn.setEnabled(True)
            
            self.obtener_estructura_tabla()
            self.mostrar_datos_tabla()
        else:
            # Deshabilitar botones si no hay tabla seleccionada
            self.refresh_data_btn.setEnabled(False)
            self.save_data_btn.setEnabled(False)
            self.add_row_btn.setEnabled(False)
            self.delete_row_btn.setEnabled(False)
            self.delete_column_btn.setEnabled(False)
    
    def obtener_estructura_tabla(self):
        if not self.current_db or not self.current_table:
            return
        
        self.thread = DescribeTableThread(
            self.config_servidor,
            'describe_table',
            self.current_db,
            self.current_table
        )
        self.thread.resultado.connect(self.estructura_listada)
        self.active_threads.append(self.thread)
        self.thread.start()
    
    def estructura_listada(self, success, message, columnas):
        if success:
            self.table_structure = columnas
            self.mostrar_estructura_en_tabla()
            
            # Identificar la clave primaria
            self.primary_key = None
            for columna in columnas:
                if 'PRI' in columna[3]:  # El campo Key indica si es PK
                    self.primary_key = columna[0]
                    break
            
            # Verificar si es auto-incremental
            if self.primary_key:
                self.verificar_auto_increment()
        else:
            QMessageBox.critical(self, "Error", message)
    
    def verificar_auto_increment(self):
        """Verifica si la clave primaria es auto-incremental"""
        try:
            config = self.config_servidor.copy()
            config['database'] = self.current_db
            conexion = mysql.connector.connect(**config)
            cursor = conexion.cursor()
            
            cursor.execute(f"""
                SELECT EXTRA 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = '{self.current_db}'
                AND TABLE_NAME = '{self.current_table}'
                AND COLUMN_NAME = '{self.primary_key}'
            """)
            
            result = cursor.fetchone()
            if result and 'auto_increment' in result[0].lower():
                # Si es auto-incremental, hacer la columna de solo lectura
                for col in range(self.data_table.columnCount()):
                    if self.data_table.horizontalHeaderItem(col).text() == self.primary_key:
                        for row in range(self.data_table.rowCount()):
                            item = self.data_table.item(row, col)
                            if item:
                                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            
            cursor.close()
            conexion.close()
        except Error as e:
            logger.error(f"Error al verificar auto-increment: {str(e)}")
    
    def mostrar_estructura_en_tabla(self):
        if not self.table_structure:
            return
        
        self.structure_table.setRowCount(len(self.table_structure))
        self.structure_table.setColumnCount(6)
        self.structure_table.setHorizontalHeaderLabels([
            "Campo", "Tipo", "Nulo", "Clave", "Por defecto", "Extra"
        ])
        
        for i, columna in enumerate(self.table_structure):
            for j, valor in enumerate(columna):
                item = QTableWidgetItem(str(valor) if valor is not None else "NULL")
                self.structure_table.setItem(i, j, item)
        
        self.structure_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    
    def mostrar_datos_tabla(self):
        if self.current_db and self.current_table:
            self.thread = FetchDataThread(
                self.config_servidor,
                'fetch_data',
                self.current_db,
                self.current_table
            )
            self.thread.resultado.connect(self.datos_listados)
            self.active_threads.append(self.thread)
            self.thread.start()
    
    def datos_listados(self, success, message, datos):
        if success:
            if datos:
                self.original_data = datos.copy()
                columnas = list(datos[0].keys())
                
                self.data_table.setColumnCount(len(columnas))
                self.data_table.setHorizontalHeaderLabels(columnas)
                self.data_table.setRowCount(len(datos))
                
                for i, fila in enumerate(datos):
                    for j, col in enumerate(columnas):
                        item = QTableWidgetItem(str(fila[col]) if fila[col] is not None else "NULL")
                        self.data_table.setItem(i, j, item)
                
                # Configurar tabla para edición
                self.data_table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
                self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                
                # Si hay clave primaria auto-incremental, hacerla de solo lectura
                if self.primary_key:
                    self.verificar_auto_increment()
                
                # Habilitar botones de datos
                self.refresh_data_btn.setEnabled(True)
                self.save_data_btn.setEnabled(True)
                self.add_row_btn.setEnabled(True)
                self.delete_row_btn.setEnabled(True)
                self.delete_column_btn.setEnabled(True)
            else:
                # Tabla vacía - mostrar estructura
                if self.table_structure:
                    columnas = [col[0] for col in self.table_structure]
                    self.data_table.setColumnCount(len(columnas))
                    self.data_table.setHorizontalHeaderLabels(columnas)
                    self.data_table.setRowCount(0)
                    
                    # Permitir añadir nuevas filas
                    self.data_table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
                    self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                    
                    # Si hay clave primaria auto-incremental, hacerla de solo lectura
                    if self.primary_key:
                        self.verificar_auto_increment()
                    
                    # Habilitar botones de datos
                    self.refresh_data_btn.setEnabled(True)
                    self.save_data_btn.setEnabled(True)
                    self.add_row_btn.setEnabled(True)
                    self.delete_row_btn.setEnabled(True)
                    self.delete_column_btn.setEnabled(True)
                else:
                    QMessageBox.information(self, "Información", "La tabla está vacía y no se pudo obtener su estructura")
        else:
            QMessageBox.critical(self, "Error", message)
    
    def anadir_fila(self):
        if not self.table_structure:
            QMessageBox.warning(self, "Advertencia", "No se puede añadir filas sin conocer la estructura de la tabla")
            return
        
        row_position = self.data_table.rowCount()
        self.data_table.insertRow(row_position)
        
        # Rellenar con valores por defecto según la estructura
        for col in range(self.data_table.columnCount()):
            col_name = self.data_table.horizontalHeaderItem(col).text()
            col_info = next((c for c in self.table_structure if c[0] == col_name), None)
            
            if col_info:
                default_value = col_info[4]  # Valor por defecto
                if default_value and str(default_value).upper() != "NULL":
                    item = QTableWidgetItem(str(default_value))
                else:
                    item = QTableWidgetItem("")
                
                # Si es la clave primaria y es auto-incremental, dejarla vacía y no editable
                if col_name == self.primary_key:
                    item.setText("")  # Dejar vacío para auto-increment
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                
                self.data_table.setItem(row_position, col, item)
    
    def eliminar_fila(self):
        selected_row = self.data_table.currentRow()
        if selected_row >= 0:
            # Verificar si estamos eliminando una fila existente en la base de datos
            if self.original_data and selected_row < len(self.original_data) and self.primary_key:
                # Confirmar eliminación
                reply = QMessageBox.question(
                    self, 'Confirmar eliminación',
                    '¿Está seguro de eliminar esta fila de la base de datos?',
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
                
                # Obtener el valor de la clave primaria
                pk_value = None
                for col in range(self.data_table.columnCount()):
                    if self.data_table.horizontalHeaderItem(col).text() == self.primary_key:
                        pk_item = self.data_table.item(selected_row, col)
                        pk_value = pk_item.text() if pk_item else None
                        break
                
                if pk_value:
                    # Eliminar de la base de datos
                    query = f"DELETE FROM `{self.current_table}` WHERE `{self.primary_key}` = %s"
                    
                    try:
                        config = self.config_servidor.copy()
                        config['database'] = self.current_db
                        conexion = mysql.connector.connect(**config)
                        cursor = conexion.cursor()
                        
                        cursor.execute(query, (pk_value,))
                        conexion.commit()
                        
                        cursor.close()
                        conexion.close()
                        
                        # Actualizar los datos
                        self.mostrar_datos_tabla()
                        return
                    
                    except Error as e:
                        QMessageBox.critical(self, "Error", f"No se pudo eliminar la fila: {str(e)}")
                        return
            
            # Si no es una fila de la base de datos o no tiene clave primaria, solo eliminar de la vista
            self.data_table.removeRow(selected_row)
        else:
            QMessageBox.warning(self, "Advertencia", "Seleccione una fila para eliminar")
    
    def guardar_datos(self):
        if not self.current_db or not self.current_table:
            QMessageBox.warning(self, "Error", "No hay tabla seleccionada")
            return
        
        # Obtener información actualizada de la tabla
        self.primary_key = self.obtener_primary_key(self.current_db, self.current_table)
        
        if not self.primary_key:
            QMessageBox.critical(self, "Error", 
                f"No se pudo identificar la PRIMARY KEY de la tabla '{self.current_table}'\n"
                f"Por favor, asegúrese que la tabla tiene una clave primaria definida")
            return
        
        # Verificar si la PK es auto-incremental
        is_auto_increment = self.es_auto_increment(self.current_db, self.current_table, self.primary_key)
        
        # Preparar consultas
        updates = []
        inserts = []
        column_names = [self.data_table.horizontalHeaderItem(col).text() 
                       for col in range(self.data_table.columnCount())]
        
        # 1. Procesar actualizaciones
        if self.original_data:
            for row in range(min(self.data_table.rowCount(), len(self.original_data))):
                pk_value = self.obtener_valor_pk(row)
                if not pk_value:
                    continue
                
                set_clause = []
                params = []
                for col in range(self.data_table.columnCount()):
                    col_name = column_names[col]
                    if col_name == self.primary_key:
                        continue
                    
                    new_value = self.obtener_valor_celda(row, col)
                    original_value = self.original_data[row].get(col_name)
                    
                    if str(new_value) != str(original_value):
                        set_clause.append(f"`{col_name}` = %s")
                        params.append(new_value)
                
                if set_clause:
                    params.append(pk_value)
                    updates.append({
                        'query': f"UPDATE `{self.current_table}` SET {', '.join(set_clause)} WHERE `{self.primary_key}` = %s",
                        'params': params
                    })
        
        # 2. Procesar inserciones
        if self.data_table.rowCount() > len(self.original_data or []):
            insert_columns = [col for col in column_names 
                            if not (col == self.primary_key and is_auto_increment)]
            
            for row in range(len(self.original_data or []), self.data_table.rowCount()):
                values = []
                params = []
                has_values = False
                
                for col in range(self.data_table.columnCount()):
                    col_name = column_names[col]
                    if col_name == self.primary_key and is_auto_increment:
                        continue
                    
                    value = self.obtener_valor_celda(row, col)
                    if value is not None:
                        has_values = True
                    
                    values.append("%s")
                    params.append(value)
                
                if has_values:
                    inserts.append({
                        'query': f"INSERT INTO `{self.current_table}` ({', '.join([f'`{col}`' for col in insert_columns])}) VALUES ({', '.join(values)})",
                        'params': params,
                        'new_row_index': row  # Para actualizar la vista después
                    })
        
        # Ejecutar en transacción
        if updates or inserts:
            try:
                config = self.config_servidor.copy()
                config['database'] = self.current_db
                conexion = mysql.connector.connect(**config)
                cursor = conexion.cursor()
                
                # Ejecutar actualizaciones
                for update in updates:
                    cursor.execute(update['query'], update['params'])
                
                # Ejecutar inserciones y obtener los nuevos IDs
                new_ids = []
                for insert in inserts:
                    cursor.execute(insert['query'], insert['params'])
                    if is_auto_increment:
                        new_id = cursor.lastrowid
                        new_ids.append((insert['new_row_index'], new_id))
                
                conexion.commit()
                
                # Actualizar los IDs en la vista para filas nuevas
                if new_ids:
                    pk_col = column_names.index(self.primary_key)
                    for row_idx, new_id in new_ids:
                        item = QTableWidgetItem(str(new_id))
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Hacerlo de solo lectura
                        self.data_table.setItem(row_idx, pk_col, item)
                
                # Refrescar datos
                self.mostrar_datos_tabla()
                
                QMessageBox.information(self, "Éxito", 
                    f"Datos guardados correctamente\n"
                    f"Actualizaciones: {len(updates)}\n"
                    f"Inserciones: {len(inserts)}")
                
            except Error as e:
                if 'conexion' in locals() and conexion.is_connected():
                    conexion.rollback()
                
                error_msg = str(e)
                
                # Mensaje más amigable para duplicados
                if "1062" in error_msg and "Duplicate entry" in error_msg:
                    duplicate_value = error_msg.split("'")[1]
                    QMessageBox.critical(self, "Error de duplicado",
                        f"El valor '{duplicate_value}' ya existe en la tabla.\n"
                        f"Tabla: {self.current_table}\n"
                        f"Campo: {self.primary_key if 'PRIMARY' in error_msg else 'único'}\n"
                        f"Por favor, use un valor diferente.")
                else:
                    QMessageBox.critical(self, "Error", f"No se pudieron guardar los cambios: {error_msg}")
                
            finally:
                if 'conexion' in locals() and conexion.is_connected():
                    cursor.close()
                    conexion.close()
        else:
            QMessageBox.information(self, "Información", "No hay cambios para guardar")
    
    def obtener_primary_key(self, db_name, table_name):
        """Identifica automáticamente la PRIMARY KEY de una tabla"""
        try:
            config = self.config_servidor.copy()
            config['database'] = db_name
            conexion = mysql.connector.connect(**config)
            cursor = conexion.cursor()
            
            cursor.execute(f"""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = '{db_name}' 
                AND TABLE_NAME = '{table_name}'
                AND COLUMN_KEY = 'PRI'
            """)
            
            result = cursor.fetchone()
            cursor.close()
            conexion.close()
            
            return result[0] if result else None
            
        except Error as e:
            QMessageBox.critical(self, "Error", f"No se pudo obtener la clave primaria: {str(e)}")
            return None
    
    def es_auto_increment(self, db_name, table_name, column_name):
        """Determina si una columna es auto-incremental"""
        try:
            config = self.config_servidor.copy()
            config['database'] = db_name
            conexion = mysql.connector.connect(**config)
            cursor = conexion.cursor()
            
            cursor.execute(f"""
                SELECT EXTRA 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = '{db_name}'
                AND TABLE_NAME = '{table_name}'
                AND COLUMN_NAME = '{column_name}'
            """)
            
            result = cursor.fetchone()
            cursor.close()
            conexion.close()
            
            return result and 'auto_increment' in result[0].lower()
            
        except Error:
            return False
    
    def obtener_valor_celda(self, row, col):
        """Obtiene el valor de una celda manejando NULL correctamente"""
        item = self.data_table.item(row, col)
        if not item:
            return None
        
        text = item.text().strip()
        return None if text.upper() == "NULL" else text
    
    def obtener_valor_pk(self, row):
        """Obtiene el valor de la PK para una fila"""
        for col in range(self.data_table.columnCount()):
            if self.data_table.horizontalHeaderItem(col).text() == self.primary_key:
                return self.obtener_valor_celda(row, col)
        return None
    
    def actualizar_datos(self):
        self.mostrar_datos_tabla()
    
    def actualizar_listas(self):
        if self.current_db:
            self.actualizar_tablas()
            if self.current_table:
                self.mostrar_datos_tabla()
    
    def eliminar_columna(self):
        if not self.current_db or not self.current_table:
            return

        selected_column = self.data_table.currentColumn()
        if selected_column < 0:
            QMessageBox.warning(self, "Advertencia", "Seleccione una columna para eliminar")
            return

        column_name = self.data_table.horizontalHeaderItem(selected_column).text()
        
        # Verificar si es clave primaria
        if column_name == self.primary_key:
            QMessageBox.warning(self, "Error", "No se puede eliminar la columna de clave primaria")
            return

        # Confirmar eliminación
        reply = QMessageBox.question(
            self, 'Confirmar eliminación',
            f'¿Está seguro de eliminar la columna "{column_name}"?\nEsta acción no se puede deshacer.',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                config = self.config_servidor.copy()
                config['database'] = self.current_db
                conexion = mysql.connector.connect(**config)
                cursor = conexion.cursor()

                # Ejecutar ALTER TABLE para eliminar la columna
                query = f"ALTER TABLE `{self.current_table}` DROP COLUMN `{column_name}`"
                cursor.execute(query)
                conexion.commit()

                cursor.close()
                conexion.close()

                QMessageBox.information(self, "Éxito", f"Columna '{column_name}' eliminada correctamente")
                
                # Actualizar la vista
                self.obtener_estructura_tabla()
                self.mostrar_datos_tabla()

            except Error as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar la columna: {str(e)}")
    
    def ejecutar_sql(self):
        query = self.sql_editor.toPlainText().strip()
        if not query:
            QMessageBox.warning(self, "Error", "Ingrese una consulta SQL")
            return
        
        config = self.config_servidor.copy()
        if self.current_db:
            config['database'] = self.current_db
        
        try:
            conexion = mysql.connector.connect(**config)
            cursor = conexion.cursor(dictionary=True)
            
            # Para SELECT mostrar resultados, para otros mostrar mensaje
            if query.lower().startswith('select'):
                cursor.execute(query)
                resultados = cursor.fetchall()
                
                if resultados:
                    columnas = list(resultados[0].keys())
                    output = "\t".join(columnas) + "\n"
                    for fila in resultados:
                        output += "\t".join(str(fila[col]) for col in columnas) + "\n"
                    self.sql_result.setPlainText(output)
                else:
                    self.sql_result.setPlainText("La consulta no devolvió resultados")
            else:
                cursor.execute(query)
                conexion.commit()
                self.sql_result.setPlainText(f"Consulta ejecutada. Filas afectadas: {cursor.rowcount}")
            
            cursor.close()
            conexion.close()
            
            # Actualizar vistas si afectó la estructura
            if any(q in query.lower() for q in ['alter', 'create', 'drop']):
                self.actualizar_listas()
            elif any(q in query.lower() for q in ['insert', 'update', 'delete']):
                self.mostrar_datos_tabla()
        
        except Error as e:
            self.sql_result.setPlainText(f"Error SQL: {str(e)}")
    
    def limpiar_sql(self):
        self.sql_editor.clear()
        self.sql_result.clear()

def main():
    app = QApplication(sys.argv)
    window = MySQLCompleteEditor()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(current_dir, "imagenes", "big-data.png")
    window.setWindowIcon(QIcon(icon_path))
    
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()