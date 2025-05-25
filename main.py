import sys
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QPushButton, QComboBox,
                            QLineEdit, QMessageBox, QTableWidget, QTableWidgetItem,
                            QTabWidget, QGroupBox, QTextEdit, QMenu)
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
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NM Controller")
        self.setWindowIcon(QIcon("nm.ico"))
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
        layout.addWidget(self.log_window)
        
        # Create tab widget
        tab_widget = QTabWidget()
        tab_widget.setMaximumHeight(120)
        layout.addWidget(tab_widget)
        
        # Create Serial tab
        serial_tab = QWidget()
        serial_layout = QVBoxLayout(serial_tab)
        self.create_serial_controls(serial_layout)
        tab_widget.addTab(serial_tab, "Serial Connection")
        
        # Create Network tab
        network_tab = QWidget()
        network_layout = QVBoxLayout(network_tab)
        
        # Setup timer for updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_devices)
        
        # Create network controls after timer is initialized
        self.create_network_controls(network_layout)
        tab_widget.addTab(network_tab, "Network Connection")
        
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
        
        # Start listening for configuration updates
        self.start_config_listener()
        
        # Conectar señales a los métodos de UI
        self.update_list_signal.connect(self.update_device_list)
        self.update_table_signal.connect(self.update_device_table_all)
        
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
                            # Emit signals to update UI
                            self.update_list_signal.emit()
                            self.update_table_signal.emit()
                    except socket.timeout:
                        pass
                    try:
                        data, addr = status_sock.recvfrom(4096)
                        status = json.loads(data.decode('utf-8'))
                        ip = addr[0]
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
                        # Emit signal to update the table
                        self.update_table_signal.emit()
                    except socket.timeout:
                        pass
                except Exception as e:
                    self.log(f"Listener error: {str(e)}")
                    continue
            
        thread = threading.Thread(target=listen_for_updates, daemon=True)
        thread.start()
        
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
        self.log_window.append(message)
        
    def create_serial_controls(self, parent_layout):
        group = QGroupBox("Serial Connection")
        layout = QVBoxLayout()
        
        connection_layout = QHBoxLayout()
        self.port_combo = QComboBox()
        self.refresh_button = QPushButton("Refresh")
        self.connect_button = QPushButton("Connect")
        
        connection_layout.addWidget(QLabel("Port:"))
        connection_layout.addWidget(self.port_combo)
        connection_layout.addWidget(self.refresh_button)
        connection_layout.addWidget(self.connect_button)
        
        layout.addLayout(connection_layout)
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
        # Connect signals
        self.refresh_button.clicked.connect(self.refresh_ports)
        self.connect_button.clicked.connect(self.toggle_serial_connection)
        
        # Initialize
        self.refresh_ports()
        
    def create_network_controls(self, parent_layout):
        group = QGroupBox("Network Connection")
        layout = QVBoxLayout()
        
        connection_layout = QHBoxLayout()
        self.network_combo = QComboBox()
        self.network_connect_button = QPushButton("Connect")
        self.network_connect_button.setEnabled(False)  # Disable the button
        self.config_button = QPushButton("Configure All")
        
        connection_layout.addWidget(QLabel("Device:"))
        connection_layout.addWidget(self.network_combo)
        connection_layout.addWidget(self.network_connect_button)
        connection_layout.addWidget(self.config_button)
        
        layout.addLayout(connection_layout)
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
        # Connect signals
        self.config_button.clicked.connect(lambda: self.open_config_window())
        
        # Update device list when new data is received
        self.update_timer.timeout.connect(self.update_device_list)
        
    def refresh_ports(self):
        self.port_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo.addItems(ports)
        self.log(f"Serial ports found: {', '.join(ports) if ports else 'None'}")
        
    def update_device_list(self):
        """Actualiza la lista de dispositivos en el combo box."""
        current_text = self.network_combo.currentText()
        self.network_combo.clear()
        
        # Añadir todos los dispositivos conocidos
        for device in self.devices:
            self.network_combo.addItem(f"{device.device_id} ({device.ip})", device)
            
        # Restaurar la selección anterior si es posible
        if current_text:
            index = self.network_combo.findText(current_text)
            if index >= 0:
                self.network_combo.setCurrentIndex(index)
        
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
        
    def toggle_serial_connection(self):
        if not self.is_connected:
            try:
                port = self.port_combo.currentText()
                self.log(f"Connecting to serial port {port}...")
                self.serial_port = serial.Serial(port, 115200, timeout=1)
                self.is_connected = True
                self.connect_button.setText("Disconnect")
                self.update_timer.start(1000)  # Update every second
                self.log("Serial connection established.")
            except Exception as e:
                error_msg = f"Error connecting: {str(e)}"
                self.log(error_msg)
                QMessageBox.critical(self, "Error", error_msg)
        else:
            self.serial_port.close()
            self.serial_port = None
            self.is_connected = False
            self.connect_button.setText("Connect")
            self.update_timer.stop()
            self.log("Serial connection closed.")
            
    def update_devices(self):
        if not self.is_connected:
            return
            
        try:
            device = NMDevice(self.serial_port, self.network_device)
            status = device.get_status()
            
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