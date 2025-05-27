import sys
import json
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QPushButton, QComboBox,
                            QLineEdit, QMessageBox, QTableWidget, QTableWidgetItem,
                            QTabWidget, QGroupBox, QTextEdit, QMenu, QGridLayout)
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QIcon, QPixmap, QAction
import serial
import serial.tools.list_ports
from nm_device import NMDevice, NetworkDevice
import time
from config_window import ConfigWindow
import socket
import threading

class NMController(QMainWindow):
    update_list_signal = Signal()
    update_table_signal = Signal()
    log_signal = Signal(str)  # Nueva señal para el log
    config_received_signal = Signal(dict)  # Nueva señal para configuraciones
    status_received_signal = Signal(str, dict)  # Nueva señal para actualizaciones de estado
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NM Controller")
        
        # Set application icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nm.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Icon file not found at: {icon_path}")
            
        self.resize(1200, 800)
        
        # Initialize variables
        self.serial_port = None
        self.network_device = None
        self.is_connected = False
        self.devices = []
        self.device_configs = {}  # Diccionario para almacenar las configuraciones
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create log window first
        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        self.log_window.setMaximumHeight(100)
        self.log_window.setMinimumHeight(80)
        # Establecer un límite máximo de líneas para el log
        self.max_log_lines = 1000
        self.current_log_lines = 0
        layout.addWidget(self.log_window)
        
        # Create connection controls section
        connection_section = QWidget()
        connection_layout = QHBoxLayout(connection_section)
        
        # Create Serial Connection Group
        serial_group = QGroupBox("Serial Connection")
        serial_layout = QVBoxLayout()
        
        # Port and Baud controls
        port_baud_layout = QHBoxLayout()
        port_baud_layout.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        self.refresh_ports()
        port_baud_layout.addWidget(self.port_combo)
        
        port_baud_layout.addWidget(QLabel("Baud:"))
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(['115200', '230400', '460800', '921600'])
        self.baud_combo.setCurrentText('115200')
        port_baud_layout.addWidget(self.baud_combo)
        
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_serial_connection)
        port_baud_layout.addWidget(self.connect_button)
        
        serial_layout.addLayout(port_baud_layout)
        
        # WiFi Configuration
        wifi_group = QGroupBox("WiFi Configuration")
        wifi_layout = QGridLayout()
        wifi_layout.setSpacing(5)
        
        # SSID
        wifi_layout.addWidget(QLabel("SSID:"), 0, 0)
        self.ssid_input = QLineEdit()
        wifi_layout.addWidget(self.ssid_input, 0, 1)
        
        # Password
        wifi_layout.addWidget(QLabel("Password:"), 1, 0)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        wifi_layout.addWidget(self.password_input, 1, 1)
        
        # BTC
        wifi_layout.addWidget(QLabel("BTC:"), 2, 0)
        self.btc_input = QLineEdit()
        wifi_layout.addWidget(self.btc_input, 2, 1)
        
        # Configure button
        self.configure_wifi_button = QPushButton("Configure WiFi")
        self.configure_wifi_button.clicked.connect(self.configure_wifi)
        wifi_layout.addWidget(self.configure_wifi_button, 3, 0, 1, 2)
        
        wifi_group.setLayout(wifi_layout)
        serial_layout.addWidget(wifi_group)
        
        serial_group.setLayout(serial_layout)
        connection_layout.addWidget(serial_group)
        
        # Create Network Connection Group
        network_group = QGroupBox("Network Connection")
        network_layout = QVBoxLayout()
        
        # Create instruction label
        instruction_label = QLabel("To configure a device:\n"
                                 "1. Connect via Serial to configure WiFi\n"
                                 "2. Once connected to network, right-click\n"
                                 "   on the device in the list below\n"
                                 "3. Select 'Configure Device' or\n"
                                 "   'Open Web Monitor' from the menu")
        instruction_label.setWordWrap(True)
        instruction_label.setStyleSheet("QLabel { padding: 10px; font-size: 12pt; }")
        
        network_layout.addWidget(instruction_label)
        network_group.setLayout(network_layout)
        connection_layout.addWidget(network_group)
        
        # Add connection section to main layout
        layout.addWidget(connection_section)
        
        # Create device table
        self.device_table = QTableWidget()
        self.device_table.setColumnCount(17)
        self.device_table.setHorizontalHeaderLabels([
            "Device", "Hash Rate", "Share", "Net Diff", "Pool Diff",
            "Last Diff", "Best Diff", "Valid", "Progress", "Temp",
            "RSSI", "Free Heap", "Uptime", "Version", "Board Type",
            "Pool in Use", "Last Update"
        ])
        self.device_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.device_table.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.device_table)
        
        # Setup timer for updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_devices)
        
        # Start listening for configuration updates
        self.start_config_listener()
        
        # Connect signals
        self.update_list_signal.connect(self.update_device_list)
        self.update_table_signal.connect(self.update_device_table_all)
        
        # Initially disable WiFi configuration
        self.disable_wifi_config()
        
    def start_config_listener(self):
        """Starts a thread to listen for configuration and status updates."""
        def listen_for_updates():
            config_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            config_sock.bind(('0.0.0.0', 12346))
            config_sock.settimeout(0.1)
            status_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            status_sock.bind(('0.0.0.0', 12345))
            status_sock.settimeout(0.1)
            while True:
                try:
                    try:
                        data, addr = config_sock.recvfrom(4096)
                        config = json.loads(data.decode('utf-8'))
                        # Emitir señal en lugar de actualizar directamente
                        self.config_received_signal.emit(config)
                    except socket.timeout:
                        pass
                    try:
                        data, addr = status_sock.recvfrom(4096)
                        status = json.loads(data.decode('utf-8'))
                        ip = addr[0]
                        # Emitir señal en lugar de actualizar directamente
                        self.status_received_signal.emit(ip, status)
                    except socket.timeout:
                        pass
                except Exception as e:
                    self.log_signal.emit(f"Listener error: {str(e)}")
                    continue
            
        # Conectar las señales a los slots correspondientes
        self.log_signal.connect(self.log)
        self.config_received_signal.connect(self.handle_config_received)
        self.status_received_signal.connect(self.handle_status_received)
        
        thread = threading.Thread(target=listen_for_updates, daemon=True)
        thread.start()
        
    def handle_config_received(self, config):
        """Maneja la recepción de configuración en el hilo principal."""
        if 'IP' in config:
            self.device_configs[config['IP']] = config
            self.log(f"Configuration received from {config['IP']}")
            if not any(d.ip == config['IP'] for d in self.devices):
                device = NetworkDevice(
                    ip=config['IP'],
                    port=12345,
                    device_id=config.get('BoardType', config['IP']),
                    is_online=True,
                    hash_rate="",
                    share="",
                    net_diff="",
                    pool_diff="",
                    last_diff="",
                    best_diff="",
                    valid=0,
                    progress=0.0,
                    temp=0.0,
                    rssi=0,
                    free_heap=0.0,
                    uptime="",
                    version=config.get('Version', ''),
                    board_type=config.get('BoardType', ''),
                    pool_in_use=config.get('PoolInUse', ''),
                    update_time=""
                )
                self.devices.append(device)
            # Emitir señales para actualizar UI
            self.update_list_signal.emit()
            self.update_table_signal.emit()
            
    def handle_status_received(self, ip, status):
        """Maneja la recepción de estado en el hilo principal."""
        for device in self.devices:
            if device.ip == ip:
                device.hash_rate = status.get('HashRate', device.hash_rate)
                device.share = status.get('Share', device.share)
                device.net_diff = status.get('NetDiff', device.net_diff)
                device.pool_diff = status.get('PoolDiff', device.pool_diff)
                device.last_diff = status.get('LastDiff', device.last_diff)
                device.best_diff = status.get('BestDiff', device.best_diff)
                device.valid = status.get('Valid', device.valid)
                device.progress = status.get('Progress', device.progress)
                device.temp = status.get('Temp', device.temp)
                device.rssi = status.get('RSSI', device.rssi)
                device.free_heap = status.get('FreeHeap', device.free_heap)
                device.uptime = status.get('Uptime', device.uptime)
                device.version = status.get('Version', device.version)
                device.board_type = status.get('BoardType', device.board_type)
                device.pool_in_use = status.get('PoolInUse', device.pool_in_use)
                device.update_time = time.strftime("%Y-%m-%d %H:%M:%S")
                device.is_online = True
                break
        # Emitir señal para actualizar la tabla
        self.update_table_signal.emit()
        
    def show_context_menu(self, position):
        """Muestra el menú contextual al hacer clic derecho en la tabla."""
        menu = QMenu()
        
        # Obtener el dispositivo seleccionado
        row = self.device_table.rowAt(position.y())
        if row >= 0:
            device_id = self.device_table.item(row, 0).text()
            ip = device_id.split('(')[1].split(')')[0]
            
            # Añadir acciones al menú
            config_action = QAction("Configure Device", self)
            config_action.triggered.connect(lambda: self.open_config_window(ip))
            menu.addAction(config_action)
            
            web_monitor_action = QAction("Open Web Monitor", self)
            web_monitor_action.triggered.connect(lambda: self.open_web_monitor(ip))
            menu.addAction(web_monitor_action)
            
            menu.exec(self.device_table.viewport().mapToGlobal(position))
            
    def open_config_window(self, device_ip=None):
        """Abre la ventana de configuración."""
        if device_ip and device_ip in self.device_configs:
            # Si tenemos la configuración almacenada, la usamos
            config = self.device_configs[device_ip]
            config_window = ConfigWindow(device_ip, self)
            config_window.load_config(config)
            config_window.exec()
        else:
            # Si no tenemos la configuración, abrimos la ventana con valores por defecto
            config_window = ConfigWindow(device_ip, self)
            config_window.exec()
        
    def open_web_monitor(self, device_ip):
        """Abre el monitor web del dispositivo."""
        import webbrowser
        webbrowser.open(f"http://{device_ip}")
        
    def log(self, message: str):
        """Adds a message to the log (in English)."""
        # Incrementar el contador de líneas
        self.current_log_lines += 1
        
        # Si excedemos el límite, eliminar las líneas más antiguas
        if self.current_log_lines > self.max_log_lines:
            # Obtener el texto actual
            current_text = self.log_window.toPlainText()
            # Dividir en líneas
            lines = current_text.split('\n')
            # Mantener solo las últimas max_log_lines líneas
            lines = lines[-self.max_log_lines:]
            # Actualizar el texto
            self.log_window.setPlainText('\n'.join(lines))
            self.current_log_lines = self.max_log_lines
        
        # Agregar el nuevo mensaje
        self.log_window.append(message)
        
        # Scroll to the bottom
        self.log_window.verticalScrollBar().setValue(
            self.log_window.verticalScrollBar().maximum()
        )
        
    def disable_wifi_config(self):
        """Disable WiFi configuration controls."""
        self.ssid_input.setEnabled(False)
        self.password_input.setEnabled(False)
        self.btc_input.setEnabled(False)
        self.configure_wifi_button.setEnabled(False)
        
    def enable_wifi_config(self):
        """Enable WiFi configuration controls."""
        self.ssid_input.setEnabled(True)
        self.password_input.setEnabled(True)
        self.btc_input.setEnabled(True)
        self.configure_wifi_button.setEnabled(True)
        
    def configure_wifi(self):
        """Configure WiFi settings for the device."""
        if not self.serial_port:
            self.log("No serial connection available")
            return
            
        ssid = self.ssid_input.text().strip()
        password = self.password_input.text().strip()
        btc = self.btc_input.text().strip()
        
        if not ssid or not password:
            QMessageBox.warning(self, "Configuration Error", 
                              "SSID and Password are required")
            return
            
        try:
            # Crear el objeto JSON de configuración solo con campos que tienen datos
            config = {}
            if ssid:
                config["ssid"] = ssid
            if password:
                config["password"] = password
            if btc:
                config["btc"] = btc

            # Convertir a JSON y enviar
            json_config = json.dumps(config)
            self.log(f"Sending WiFi configuration: {json_config}")
            
            # Enviar la configuración
            self.serial_port.write(f"{json_config}\r\n".encode())
            self.serial_port.flush()  # Asegurar que se envíe
            
            # Esperar y leer la respuesta
            time.sleep(0.5)  # Dar tiempo para que el dispositivo procese
            response = ""
            while self.serial_port.in_waiting:
                line = self.serial_port.readline().decode().strip()
                # Eliminar códigos ANSI
                line = line.replace('\x1b[32m', '').replace('\x1b[0m', '')
                response += line + "\n"
                self.log(f"Device response: {line}")
            
            # Verificar la respuesta
            if "Save Wifi SSID" in response and "Save Wifi Password" in response:
                QMessageBox.information(self, "Success", 
                                      "WiFi configuration sent successfully.\n\n"
                                      "Please manually restart the device for the changes to take effect.")
            else:
                QMessageBox.warning(self, "Warning", 
                                  "Unexpected response from device. Please verify the configuration.")
                
        except Exception as e:
            self.log(f"Error configuring WiFi: {str(e)}")
            QMessageBox.critical(self, "Error", 
                               f"Error configuring WiFi: {str(e)}")
            
    def toggle_serial_connection(self):
        """Toggle serial connection."""
        if not self.is_connected:
            try:
                port = self.port_combo.currentText()
                baud_rate = int(self.baud_combo.currentText())
                
                self.serial_port = serial.Serial(port, baud_rate, timeout=1)
                self.is_connected = True
                self.connect_button.setText("Disconnect")
                self.log(f"Connected to {port} at {baud_rate} baud")
                
                # Enable WiFi configuration when connected via serial
                self.enable_wifi_config()
                
            except Exception as e:
                self.log(f"Error connecting to {port}: {str(e)}")
                QMessageBox.critical(self, "Connection Error", 
                                   f"Error connecting to {port}: {str(e)}")
                self.serial_port = None
                self.is_connected = False
                self.connect_button.setText("Connect")
                self.disable_wifi_config()
        else:
            try:
                if self.serial_port:
                    self.serial_port.close()
                self.serial_port = None
                self.is_connected = False
                self.connect_button.setText("Connect")
                self.log("Disconnected from serial port")
                self.disable_wifi_config()
            except Exception as e:
                self.log(f"Error disconnecting: {str(e)}")
                QMessageBox.critical(self, "Disconnection Error", 
                                   f"Error disconnecting: {str(e)}")
            
    def refresh_ports(self):
        self.port_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo.addItems(ports)
        self.log(f"Serial ports found: {', '.join(ports) if ports else 'None'}")
        
    def update_device_list(self):
        """Actualiza la lista de dispositivos en la tabla."""
        # Actualizar la tabla
        self.update_device_table_all()
        
    def format_uptime(self, uptime_str: str) -> str:
        """Formats the uptime string to remove duplicates and ensure proper spacing."""
        if not uptime_str:
            return "0d 00:00:00"
        # Remove any duplicate entries and extra spaces
        parts = uptime_str.split()
        if len(parts) >= 2:
            return f"{parts[0]} {parts[1]}"
        return uptime_str

    def update_device_table_all(self):
        """Actualiza la tabla con todos los dispositivos detectados."""
        # Asegurarse de que las actualizaciones de la UI se realizan en el hilo principal
        QApplication.instance().processEvents()
        self.device_table.setRowCount(len(self.devices))
        for row, device in enumerate(self.devices):
            self.device_table.setItem(row, 0, QTableWidgetItem(f"{device.device_id} ({device.ip})"))
            self.device_table.setItem(row, 1, QTableWidgetItem(device.hash_rate))
            self.device_table.setItem(row, 2, QTableWidgetItem(device.share))
            self.device_table.setItem(row, 3, QTableWidgetItem(device.net_diff))
            self.device_table.setItem(row, 4, QTableWidgetItem(device.pool_diff))
            self.device_table.setItem(row, 5, QTableWidgetItem(device.last_diff))
            self.device_table.setItem(row, 6, QTableWidgetItem(device.best_diff))
            self.device_table.setItem(row, 7, QTableWidgetItem(str(device.valid)))
            self.device_table.setItem(row, 8, QTableWidgetItem(f"{device.progress:.2f}"))
            self.device_table.setItem(row, 9, QTableWidgetItem(f"{device.temp:.1f}°C"))
            self.device_table.setItem(row, 10, QTableWidgetItem(f"{device.rssi} dBm"))
            self.device_table.setItem(row, 11, QTableWidgetItem(f"{device.free_heap:.1f} KB"))
            self.device_table.setItem(row, 12, QTableWidgetItem(self.format_uptime(device.uptime)))
            self.device_table.setItem(row, 13, QTableWidgetItem(device.version))
            self.device_table.setItem(row, 14, QTableWidgetItem(device.board_type))
            self.device_table.setItem(row, 15, QTableWidgetItem(device.pool_in_use))
            self.device_table.setItem(row, 16, QTableWidgetItem(device.update_time))
        self.device_table.resizeColumnsToContents()
        
    def update_devices(self):
        if not self.is_connected:
            return
            
        try:
            device = NMDevice(self.serial_port, self.network_device)
            self.log("Requesting device status...")
            status = device.get_status()
            self.log(f"Device status received: {status}")
            
            # Update table
            row = 0
            self.device_table.setRowCount(1)
            self.device_table.setItem(row, 0, QTableWidgetItem(status.device_id))
            self.device_table.setItem(row, 1, QTableWidgetItem(f"{status.hash_rate:.2f} MH/s"))
            self.device_table.setItem(row, 2, QTableWidgetItem("0/0"))  # share
            self.device_table.setItem(row, 3, QTableWidgetItem("0"))    # net_diff
            self.device_table.setItem(row, 4, QTableWidgetItem("0"))    # pool_diff
            self.device_table.setItem(row, 5, QTableWidgetItem("0"))    # last_diff
            self.device_table.setItem(row, 6, QTableWidgetItem("0"))    # best_diff
            self.device_table.setItem(row, 7, QTableWidgetItem("0"))    # valid
            self.device_table.setItem(row, 8, QTableWidgetItem("0.00")) # progress
            self.device_table.setItem(row, 9, QTableWidgetItem(f"{status.temperature:.1f}°C"))
            self.device_table.setItem(row, 10, QTableWidgetItem("0 dBm"))  # rssi
            self.device_table.setItem(row, 11, QTableWidgetItem("0.0 KB")) # free_heap
            self.device_table.setItem(row, 12, QTableWidgetItem("0"))      # uptime
            self.device_table.setItem(row, 13, QTableWidgetItem(""))       # version
            self.device_table.setItem(row, 14, QTableWidgetItem(""))       # board_type
            self.device_table.setItem(row, 15, QTableWidgetItem(""))       # pool_in_use
            self.device_table.setItem(row, 16, QTableWidgetItem(time.strftime("%Y-%m-%d %H:%M:%S")))
            
            # Intentar obtener la configuración si no la tenemos
            if not self.device_configs:
                self.log("No device configuration found, attempting to get it...")
                try:
                    config = device.get_config()
                    if config:
                        self.log(f"Configuration received: {config}")
                        if 'IP' in config:
                            self.device_configs[config['IP']] = config
                            self.log(f"Device configuration stored for IP: {config['IP']}")
                    else:
                        self.log("No configuration received from device")
                except Exception as e:
                    self.log(f"Error getting configuration: {str(e)}")
            
        except Exception as e:
            error_msg = f"Error reading data: {str(e)}"
            self.log(error_msg)
            QMessageBox.warning(self, "Error", error_msg)
            if self.serial_port:
                self.toggle_serial_connection()
            else:
                self.toggle_network_connection()

def main():
    app = QApplication(sys.argv)
    window = NMController()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 