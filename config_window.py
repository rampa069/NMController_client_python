from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QLineEdit, QPushButton, QSpinBox, QCheckBox,
                            QGroupBox, QFormLayout, QMessageBox, QScrollArea,
                            QWidget)
from PySide6.QtCore import Qt
import json
import socket
import threading
import time

class ConfigWindow(QDialog):
    def __init__(self, device_ip=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Device Configuration")
        self.setMinimumSize(600, 400)  # Ajustar tamaño mínimo para mostrar todo el contenido
        self.device_ip = device_ip
        self.parent = parent
        self.setup_ui()
        
    def setup_ui(self):
        self.setModal(True)
        self.resize(410, 720)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create main widget and layout
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(10)
        
        # Create form groups
        self.create_device_info_group(layout)
        self.create_wifi_group(layout)
        self.create_primary_pool_group(layout)
        self.create_secondary_pool_group(layout)
        self.create_settings_group(layout)
        self.create_buttons(layout)
        
        # Set scroll area widget
        scroll.setWidget(main_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
        
        # Load default values first
        self.load_default_values()
        
        # Si tenemos la configuración almacenada, la usamos
        if self.device_ip and hasattr(self.parent, 'device_configs') and self.device_ip in self.parent.device_configs:
            self.load_config(self.parent.device_configs[self.device_ip])
        
    def create_device_info_group(self, parent_layout):
        group = QGroupBox("Device Information")
        form = QFormLayout()
        
        self.device_ip_label = QLabel(self.device_ip if self.device_ip else "0.0.0.0")
        form.addRow("Device IP:", self.device_ip_label)
        
        group.setLayout(form)
        parent_layout.addWidget(group)
        
    def create_wifi_group(self, parent_layout):
        group = QGroupBox("Device Wifi Configuration")
        form = QFormLayout()
        
        self.wifi_ssid = QLineEdit()
        self.wifi_ssid.setPlaceholderText("Enter WiFi SSID")
        form.addRow("SSID:", self.wifi_ssid)
        
        self.wifi_password = QLineEdit()
        self.wifi_password.setPlaceholderText("Enter WiFi Password")
        self.wifi_password.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Password:", self.wifi_password)
        
        group.setLayout(form)
        parent_layout.addWidget(group)
        
    def create_primary_pool_group(self, parent_layout):
        group = QGroupBox("Primary pool (used on bootup)")
        form = QFormLayout()
        
        self.primary_pool = QLineEdit()
        self.primary_pool.setPlaceholderText("stratum+tcp://pool.example.com:3333")
        form.addRow("Primary Pool URL:", self.primary_pool)
        
        self.primary_password = QLineEdit()
        self.primary_password.setPlaceholderText("x")
        form.addRow("Pool password:", self.primary_password)
        
        self.primary_address = QLineEdit()
        self.primary_address.setPlaceholderText("Your BTC address")
        form.addRow("BTC address:", self.primary_address)
        
        group.setLayout(form)
        parent_layout.addWidget(group)
        
    def create_secondary_pool_group(self, parent_layout):
        group = QGroupBox("Secondary pool (used when primary fails)")
        form = QFormLayout()
        
        self.secondary_pool = QLineEdit()
        self.secondary_pool.setPlaceholderText("stratum+tcp://pool.example.com:3333")
        form.addRow("Secondary Pool URL:", self.secondary_pool)
        
        self.secondary_password = QLineEdit()
        self.secondary_password.setPlaceholderText("x")
        form.addRow("Pool password:", self.secondary_password)
        
        self.secondary_address = QLineEdit()
        self.secondary_address.setPlaceholderText("Your BTC address")
        form.addRow("BTC address:", self.secondary_address)
        
        group.setLayout(form)
        parent_layout.addWidget(group)
        
    def create_settings_group(self, parent_layout):
        group = QGroupBox("Settings")
        form = QFormLayout()
        
        self.timezone = QSpinBox()
        self.timezone.setRange(-12, 12)
        self.timezone.setValue(8)
        form.addRow("Timezone:", self.timezone)
        
        self.ui_refresh = QSpinBox()
        self.ui_refresh.setRange(1, 60)
        self.ui_refresh.setValue(2)
        form.addRow("UI Refresh (s):", self.ui_refresh)
        
        self.screen_timeout = QSpinBox()
        self.screen_timeout.setRange(0, 3600)
        self.screen_timeout.setValue(60)
        form.addRow("Screen Timeout (s):", self.screen_timeout)
        
        self.brightness = QSpinBox()
        self.brightness.setRange(0, 100)
        self.brightness.setValue(100)
        form.addRow("Brightness (%):", self.brightness)
        
        self.save_uptime = QCheckBox("Save uptime, best diff, shares in nvs")
        self.save_uptime.setChecked(True)
        form.addRow("", self.save_uptime)
        
        self.led_enable = QCheckBox("Led enable")
        self.led_enable.setChecked(True)
        form.addRow("", self.led_enable)
        
        self.rotate_screen = QCheckBox("Rotate screen")
        form.addRow("", self.rotate_screen)
        
        self.btc_price = QCheckBox("BTC price update from market")
        form.addRow("", self.btc_price)
        
        self.auto_brightness = QCheckBox("Enable/disable auto brightness")
        self.auto_brightness.setChecked(True)
        form.addRow("", self.auto_brightness)
        
        group.setLayout(form)
        parent_layout.addWidget(group)
        
    def create_buttons(self, parent_layout):
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        parent_layout.addLayout(button_layout)
        
    def load_default_values(self):
        """Carga los valores por defecto."""
        self.wifi_ssid.setText("NMTech-2.4G")
        self.wifi_password.setText("NMMiner2048")
        self.primary_pool.setText("stratum+tcp://public-pool.io:21496")
        self.primary_password.setText("x")
        self.primary_address.setText("18dK8EfyepKuS74fs27iuDJWoGUT4rPto1")
        self.secondary_pool.setText("stratum+tcp://pool.tazmining.ch:33333")
        self.secondary_password.setText("x")
        self.secondary_address.setText("18dK8EfyepKuS74fs27iuDJWoGUT4rPto1")
        
    def read_current_config(self):
        """Lee la configuración actual del dispositivo."""
        try:
            # Crear socket UDP para recibir la configuración
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.0)
            
            # Enviar solicitud de configuración
            request = json.dumps({"command": "get_config"})
            sock.sendto(request.encode('utf-8'), (self.device_ip, 12347))
            
            # Esperar respuesta
            try:
                data, addr = sock.recvfrom(4096)
                config = json.loads(data.decode('utf-8'))
                
                # Mostrar la configuración recibida en el log
                if hasattr(self.parent, 'log'):
                    self.parent.log(f"Configuración recibida de {self.device_ip}:")
                    self.parent.log(f"WiFi SSID: {config.get('WiFiSSID', '')}")
                    self.parent.log(f"WiFi Password: {config.get('WiFiPWD', '')}")
                    self.parent.log(f"Primary Pool: {config.get('PrimaryPool', '')}")
                    self.parent.log(f"Primary Password: {config.get('PrimaryPassword', '')}")
                    self.parent.log(f"Primary Address: {config.get('PrimaryAddress', '')}")
                    self.parent.log(f"Secondary Pool: {config.get('SecondaryPool', '')}")
                    self.parent.log(f"Secondary Password: {config.get('SecondaryPassword', '')}")
                    self.parent.log(f"Secondary Address: {config.get('SecondaryAddress', '')}")
                    self.parent.log(f"Timezone: {config.get('Timezone', 8)}")
                    self.parent.log(f"UI Refresh: {config.get('UIRefresh', 2)}")
                    self.parent.log(f"Screen Timeout: {config.get('ScreenTimeout', 60)}")
                    self.parent.log(f"Brightness: {config.get('Brightness', 100)}")
                    self.parent.log(f"Save Uptime: {config.get('SaveUptime', True)}")
                    self.parent.log(f"Led Enable: {config.get('LedEnable', True)}")
                    self.parent.log(f"Rotate Screen: {config.get('RotateScreen', False)}")
                    self.parent.log(f"BTC Price: {config.get('BTCPrice', False)}")
                    self.parent.log(f"Auto Brightness: {config.get('AutoBrightness', True)}")
                    self.parent.log("----------------------------------------")
                
                # Actualizar campos con la configuración recibida
                self.wifi_ssid.setText(config.get("WiFiSSID", ""))
                self.wifi_password.setText(config.get("WiFiPWD", ""))
                self.primary_pool.setText(config.get("PrimaryPool", ""))
                self.primary_password.setText(config.get("PrimaryPassword", ""))
                self.primary_address.setText(config.get("PrimaryAddress", ""))
                self.secondary_pool.setText(config.get("SecondaryPool", ""))
                self.secondary_password.setText(config.get("SecondaryPassword", ""))
                self.secondary_address.setText(config.get("SecondaryAddress", ""))
                self.timezone.setValue(config.get("Timezone", 8))
                self.ui_refresh.setValue(config.get("UIRefresh", 2))
                self.screen_timeout.setValue(config.get("ScreenTimeout", 60))
                self.brightness.setValue(config.get("Brightness", 100))
                self.save_uptime.setChecked(config.get("SaveUptime", True))
                self.led_enable.setChecked(config.get("LedEnable", True))
                self.rotate_screen.setChecked(config.get("RotateScreen", False))
                self.btc_price.setChecked(config.get("BTCPrice", False))
                self.auto_brightness.setChecked(config.get("AutoBrightness", True))
                
            except socket.timeout:
                if hasattr(self.parent, 'log'):
                    self.parent.log(f"Timeout al leer la configuración de {self.device_ip}")
                QMessageBox.warning(self, "Warning", "Timeout reading device configuration. Using default values.")
            except json.JSONDecodeError:
                if hasattr(self.parent, 'log'):
                    self.parent.log(f"Error al decodificar la configuración de {self.device_ip}")
                QMessageBox.warning(self, "Warning", "Invalid configuration received. Using default values.")
                
        except Exception as e:
            if hasattr(self.parent, 'log'):
                self.parent.log(f"Error al leer la configuración de {self.device_ip}: {str(e)}")
            QMessageBox.warning(self, "Warning", f"Error reading configuration: {str(e)}. Using default values.")
        finally:
            sock.close()
        
    def get_config(self):
        """Obtiene la configuración actual."""
        return {
            "IP": self.device_ip if self.device_ip else "0.0.0.0",
            "WiFiSSID": self.wifi_ssid.text(),
            "WiFiPWD": self.wifi_password.text(),
            "PrimaryPool": self.primary_pool.text(),
            "PrimaryPassword": self.primary_password.text(),
            "PrimaryAddress": self.primary_address.text(),
            "SecondaryPool": self.secondary_pool.text(),
            "SecondaryPassword": self.secondary_password.text(),
            "SecondaryAddress": self.secondary_address.text(),
            "Timezone": self.timezone.value(),
            "UIRefresh": self.ui_refresh.value(),
            "ScreenTimeout": self.screen_timeout.value(),
            "Brightness": self.brightness.value(),
            "SaveUptime": self.save_uptime.isChecked(),
            "LedEnable": self.led_enable.isChecked(),
            "RotateScreen": self.rotate_screen.isChecked(),
            "BTCPrice": self.btc_price.isChecked(),
            "AutoBrightness": self.auto_brightness.isChecked()
        }
        
    def save_config(self):
        """Guarda la configuración y la envía al dispositivo."""
        config = self.get_config()
        
        # Validar campos requeridos
        if not config["WiFiSSID"] or not config["WiFiPWD"]:
            QMessageBox.warning(self, "Error", "WiFi Parameter (SSID or PWD) can't be empty.")
            return
            
        # Enviar configuración
        try:
            self.send_config(config)
            QMessageBox.information(self, "Success", "Configuration sent successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to send configuration: {str(e)}")
            
    def send_config(self, config):
        """Envía la configuración al dispositivo mediante UDP."""
        json_data = json.dumps(config)
        data = json_data.encode('utf-8')
        
        # Crear socket UDP
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.1)
        
        try:
            # Enviar 10 veces para asegurar la recepción
            for _ in range(10):
                if config["IP"] == "0.0.0.0":
                    # Broadcast a todos los dispositivos
                    sock.sendto(data, ('<broadcast>', 12347))
                else:
                    # Enviar a un dispositivo específico
                    sock.sendto(data, (config["IP"], 12347))
                time.sleep(0.1)
        finally:
            sock.close()

    def load_config(self, config):
        """Carga la configuración desde un diccionario."""
        self.wifi_ssid.setText(config.get("WiFiSSID", ""))
        self.wifi_password.setText(config.get("WiFiPWD", ""))
        self.primary_pool.setText(config.get("PrimaryPool", ""))
        self.primary_password.setText(config.get("PrimaryPassword", ""))
        self.primary_address.setText(config.get("PrimaryAddress", ""))
        self.secondary_pool.setText(config.get("SecondaryPool", ""))
        self.secondary_password.setText(config.get("SecondaryPassword", ""))
        self.secondary_address.setText(config.get("SecondaryAddress", ""))
        self.timezone.setValue(config.get("Timezone", 8))
        self.ui_refresh.setValue(config.get("UIRefresh", 2))
        self.screen_timeout.setValue(config.get("ScreenTimeout", 60))
        self.brightness.setValue(config.get("Brightness", 100))
        self.save_uptime.setChecked(config.get("SaveUptime", True))
        self.led_enable.setChecked(config.get("LedEnable", True))
        self.rotate_screen.setChecked(config.get("RotateScreen", False))
        self.btc_price.setChecked(config.get("BTCPrice", False))
        self.auto_brightness.setChecked(config.get("AutoBrightness", True))
        
        # Mostrar la configuración en el log
        if hasattr(self.parent, 'log'):
            self.parent.log(f"Configuración cargada para {self.device_ip}:")
            self.parent.log(f"WiFi SSID: {config.get('WiFiSSID', '')}")
            self.parent.log(f"WiFi Password: {config.get('WiFiPWD', '')}")
            self.parent.log(f"Primary Pool: {config.get('PrimaryPool', '')}")
            self.parent.log(f"Primary Password: {config.get('PrimaryPassword', '')}")
            self.parent.log(f"Primary Address: {config.get('PrimaryAddress', '')}")
            self.parent.log(f"Secondary Pool: {config.get('SecondaryPool', '')}")
            self.parent.log(f"Secondary Password: {config.get('SecondaryPassword', '')}")
            self.parent.log(f"Secondary Address: {config.get('SecondaryAddress', '')}")
            self.parent.log(f"Timezone: {config.get('Timezone', 8)}")
            self.parent.log(f"UI Refresh: {config.get('UIRefresh', 2)}")
            self.parent.log(f"Screen Timeout: {config.get('ScreenTimeout', 60)}")
            self.parent.log(f"Brightness: {config.get('Brightness', 100)}")
            self.parent.log(f"Save Uptime: {config.get('SaveUptime', True)}")
            self.parent.log(f"Led Enable: {config.get('LedEnable', True)}")
            self.parent.log(f"Rotate Screen: {config.get('RotateScreen', False)}")
            self.parent.log(f"BTC Price: {config.get('BTCPrice', False)}")
            self.parent.log(f"Auto Brightness: {config.get('AutoBrightness', True)}")
            self.parent.log("----------------------------------------") 