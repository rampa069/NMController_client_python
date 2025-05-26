import json
import time
import socket
import threading
import subprocess
from dataclasses import dataclass
from typing import Optional, List, Dict

@dataclass
class DeviceStatus:
    device_id: str
    hash_rate: float
    temperature: float
    fan_speed: int
    is_mining: bool
    error: Optional[str] = None

@dataclass
class NetworkDevice:
    ip: str
    port: int
    device_id: str
    is_online: bool
    hash_rate: str = "0"
    share: str = "0/0"
    net_diff: str = "0"
    pool_diff: str = "0"
    last_diff: str = "0"
    best_diff: str = "0"
    valid: int = 0
    progress: float = 0.0
    temp: float = 0.0
    rssi: float = 0.0
    free_heap: float = 0.0
    uptime: str = "0"
    version: str = ""
    board_type: str = ""
    pool_in_use: str = ""
    update_time: str = ""

class NMDevice:
    DISCOVERY_PORT = 12345  # Puerto para descubrimiento de dispositivos (igual que el original)
    
    def __init__(self, serial_port=None, network_device: NetworkDevice = None):
        self.serial_port = serial_port
        self.network_device = network_device
        self.status = DeviceStatus(
            device_id="",
            hash_rate=0.0,
            temperature=0.0,
            fan_speed=0,
            is_mining=False
        )
        self._discovery_thread = None
        self._keep_listening = False
        self._discovered_devices = []
        
    @staticmethod
    def get_network_interfaces() -> List[str]:
        """Obtiene las interfaces de red disponibles."""
        interfaces = []
        try:
            # En macOS, usamos networksetup para obtener las interfaces
            result = subprocess.run(['networksetup', '-listallhardwareports'], 
                                 capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'Device:' in line:
                    device = line.split('Device:')[1].strip()
                    if device and device != 'lo0':  # Excluir loopback
                        interfaces.append(device)
        except Exception as e:
            print(f"Error getting network interfaces: {e}")
        return interfaces
        
    @staticmethod
    def get_interface_ip(interface: str) -> Optional[str]:
        """Obtiene la dirección IP de una interfaz específica."""
        try:
            # En macOS, usamos ifconfig para obtener la IP
            result = subprocess.run(['ifconfig', interface], 
                                 capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'inet ' in line:
                    return line.split('inet ')[1].split(' ')[0]
        except Exception as e:
            print(f"Error getting IP for interface {interface}: {e}")
        return None
        
    def _listen_for_devices(self):
        """Escucha continuamente mensajes de dispositivos."""
        listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            listen_sock.bind(('', self.DISCOVERY_PORT))
            print(f"Escuchando en puerto {self.DISCOVERY_PORT}")
            
            while self._keep_listening:
                try:
                    data, addr = listen_sock.recvfrom(1024)
                    print(f"Mensaje recibido de {addr}: {data}")
                    
                    try:
                        response_text = data.decode('utf-8')
                        print(f"Mensaje decodificado: {response_text}")
                        
                        try:
                            device_data = json.loads(response_text)
                            print(f"Datos del dispositivo: {device_data}")
                            
                            # Verificar si ya tenemos este dispositivo
                            device_exists = False
                            for device in self._discovered_devices:
                                if device.ip == addr[0]:
                                    # Actualizar datos del dispositivo existente
                                    device.hash_rate = device_data.get('HashRate', device.hash_rate)
                                    device.share = device_data.get('Share', device.share)
                                    device.net_diff = device_data.get('NetDiff', device.net_diff)
                                    device.pool_diff = device_data.get('PoolDiff', device.pool_diff)
                                    device.last_diff = device_data.get('LastDiff', device.last_diff)
                                    device.best_diff = device_data.get('BestDiff', device.best_diff)
                                    device.valid = device_data.get('Valid', device.valid)
                                    device.progress = device_data.get('Progress', device.progress)
                                    device.temp = device_data.get('Temp', device.temp)
                                    device.rssi = device_data.get('RSSI', device.rssi)
                                    device.free_heap = device_data.get('FreeHeap', device.free_heap)
                                    device.uptime = device_data.get('Uptime', device.uptime)
                                    device.version = device_data.get('Version', device.version)
                                    device.board_type = device_data.get('BoardType', device.board_type)
                                    device.pool_in_use = device_data.get('PoolInUse', device.pool_in_use)
                                    device.update_time = time.strftime("%Y-%m-%d %H:%M:%S")
                                    device.is_online = True
                                    device_exists = True
                                    print(f"Dispositivo actualizado: {addr[0]}")
                                    break
                            
                            if not device_exists:
                                new_device = NetworkDevice(
                                    ip=addr[0],
                                    port=addr[1],
                                    device_id=device_data.get('BoardType', ''),
                                    is_online=True,
                                    hash_rate=device_data.get('HashRate', '0'),
                                    share=device_data.get('Share', '0/0'),
                                    net_diff=device_data.get('NetDiff', '0'),
                                    pool_diff=device_data.get('PoolDiff', '0'),
                                    last_diff=device_data.get('LastDiff', '0'),
                                    best_diff=device_data.get('BestDiff', '0'),
                                    valid=device_data.get('Valid', 0),
                                    progress=device_data.get('Progress', 0.0),
                                    temp=device_data.get('Temp', 0.0),
                                    rssi=device_data.get('RSSI', 0.0),
                                    free_heap=device_data.get('FreeHeap', 0.0),
                                    uptime=device_data.get('Uptime', '0'),
                                    version=device_data.get('Version', ''),
                                    board_type=device_data.get('BoardType', ''),
                                    pool_in_use=device_data.get('PoolInUse', ''),
                                    update_time=time.strftime("%Y-%m-%d %H:%M:%S")
                                )
                                self._discovered_devices.append(new_device)
                                print(f"Nuevo dispositivo encontrado: {addr[0]}")
                                
                            # Imprimir estado actual de todos los dispositivos
                            print("\nEstado actual de los dispositivos:")
                            for device in self._discovered_devices:
                                print(f"\nDispositivo: {device.device_id} ({device.ip})")
                                print(f"  Hash Rate: {device.hash_rate}")
                                print(f"  Share: {device.share}")
                                print(f"  Net Diff: {device.net_diff}")
                                print(f"  Pool Diff: {device.pool_diff}")
                                print(f"  Last Diff: {device.last_diff}")
                                print(f"  Best Diff: {device.best_diff}")
                                print(f"  Valid: {device.valid}")
                                print(f"  Progress: {device.progress}")
                                print(f"  Temp: {device.temp}°C")
                                print(f"  RSSI: {device.rssi} dBm")
                                print(f"  Free Heap: {device.free_heap} KB")
                                print(f"  Uptime: {device.uptime}")
                                print(f"  Version: {device.version}")
                                print(f"  Board Type: {device.board_type}")
                                print(f"  Pool in Use: {device.pool_in_use}")
                                print(f"  Last Update: {device.update_time}")
                                
                        except json.JSONDecodeError as e:
                            print(f"Error decodificando JSON de {addr[0]}: {e}")
                    except UnicodeDecodeError as e:
                        print(f"Error decodificando mensaje de {addr[0]}: {e}")
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Error recibiendo mensaje: {e}")
                    
        except Exception as e:
            print(f"Error en el hilo de escucha: {e}")
        finally:
            listen_sock.close()
            
    @staticmethod
    def discover_network_devices() -> List[NetworkDevice]:
        """Busca dispositivos NM en la red local."""
        print("Iniciando búsqueda de dispositivos...")
        
        # Crear una instancia para manejar el descubrimiento
        discoverer = NMDevice()
        discoverer._keep_listening = True
        discoverer._discovery_thread = threading.Thread(target=discoverer._listen_for_devices)
        discoverer._discovery_thread.daemon = True
        discoverer._discovery_thread.start()
        
        # Esperar un tiempo para recibir respuestas
        time.sleep(5)  # Esperar 5 segundos por respuestas iniciales
        
        # Detener la escucha
        discoverer._keep_listening = False
        discoverer._discovery_thread.join(timeout=1)
        
        print(f"Búsqueda completada. Dispositivos encontrados: {len(discoverer._discovered_devices)}")
        for device in discoverer._discovered_devices:
            print(f"  - {device.device_id} ({device.ip})")
            
        return discoverer._discovered_devices
        
    def send_command(self, command: str) -> bool:
        try:
            if self.serial_port:
                print(f"Sending command to serial port: {command}")
                # Enviar el comando con el formato correcto para ESP32
                self.serial_port.write(f"{command}\r\n".encode())
                # Esperar un momento para asegurar que el comando se envía
                time.sleep(0.1)
                # Limpiar el buffer de entrada antes de leer la respuesta
                self.serial_port.reset_input_buffer()
            elif self.network_device:
                print(f"Sending command to network device: {command}")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect((self.network_device.ip, self.network_device.port))
                sock.send(f"{command}\n".encode())
                sock.close()
            return True
        except Exception as e:
            print(f"Error sending command: {e}")
            return False
            
    def read_response(self) -> Optional[str]:
        try:
            if self.serial_port:
                # Esperar un momento para que llegue la respuesta
                time.sleep(0.2)
                if self.serial_port.in_waiting:
                    response = self.serial_port.readline().decode().strip()
                    print(f"Raw response from serial port: {response}")
                    return response
                else:
                    print("No data available in serial port")
            elif self.network_device:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect((self.network_device.ip, self.network_device.port))
                response = sock.recv(1024).decode().strip()
                print(f"Raw response from network device: {response}")
                sock.close()
                return response
        except Exception as e:
            print(f"Error reading response: {e}")
        return None
        
    def configure_wifi(self, ssid: str, password: str, btc_address: str = None) -> bool:
        """Configura la conexión WiFi del dispositivo usando el protocolo JSON."""
        try:
            print(f"Configurando WiFi para SSID: {ssid}")
            # Crear el objeto JSON de configuración
            config = {
                "ssid": ssid,
                "password": password
            }
            if btc_address:
                config["btc"] = btc_address

            # Convertir a JSON y enviar
            json_config = json.dumps(config)
            if self.send_command(json_config):
                response = self.read_response()
                print(f"WiFi config response: {response}")
                if response and ("Save Wifi SSID" in response or "Save Wifi Password" in response):
                    return True
            return False
        except Exception as e:
            print(f"Error configuring WiFi: {e}")
            return False

    def get_wifi_status(self) -> Optional[Dict]:
        """Obtiene el estado de la configuración WiFi."""
        try:
            if self.send_command("status"):
                response = self.read_response()
                print(f"WiFi status response: {response}")
                if response:
                    if "WiFi configuration time left:" in response:
                        time_left = response.split("time left:")[1].strip().replace("s", "")
                        return {
                            "status": "configuring",
                            "time_left": int(time_left)
                        }
                    elif "Connected to" in response:
                        return {
                            "status": "connected",
                            "ssid": response.split("Connected to")[1].strip()
                        }
            return None
        except Exception as e:
            print(f"Error getting WiFi status: {e}")
            return None
        
    def get_config(self) -> Optional[Dict]:
        """Obtiene la configuración del dispositivo."""
        try:
            print("Sending get_config command...")
            # Intentar primero con el comando de estado
            if self.send_command("status"):
                response = self.read_response()
                print(f"Status response received: {response}")
                if response:
                    # Si estamos en modo de configuración WiFi
                    if "WiFi configuration time left:" in response:
                        time_left = response.split("time left:")[1].strip().replace("s", "")
                        return {
                            "wifi_config_time": int(time_left),
                            "status": "configuring"
                        }
                    # Si recibimos el MD5 del firmware
                    elif "NMMiner Firmware md5" in response:
                        md5 = response.split("[")[1].split("]")[0]
                        return {
                            "firmware_md5": md5,
                            "status": "initializing"
                        }
                    # Si está intentando conectarse
                    elif "Try to connect" in response:
                        return {
                            "status": "connecting",
                            "message": response
                        }
            
            # Intentar con el comando de configuración
            if self.send_command("config"):
                response = self.read_response()
                print(f"Config response received: {response}")
                if response:
                    return {
                        "status": "configuring",
                        "message": response
                    }
            
            return None
        except Exception as e:
            print(f"Error getting config: {e}")
            return None
        
    def get_status(self) -> DeviceStatus:
        print("Sending status command...")
        if self.send_command("status"):
            response = self.read_response()
            print(f"Status response received: {response}")
            if response:
                try:
                    # Si estamos en modo de configuración WiFi
                    if "WiFi configuration time left:" in response:
                        self.status = DeviceStatus(
                            device_id="NM Device (WiFi Config Mode)",
                            hash_rate=0.0,
                            temperature=0.0,
                            fan_speed=0,
                            is_mining=False
                        )
                    # Si está inicializando
                    elif "NMMiner Firmware md5" in response:
                        self.status = DeviceStatus(
                            device_id="NM Device (Initializing)",
                            hash_rate=0.0,
                            temperature=0.0,
                            fan_speed=0,
                            is_mining=False
                        )
                    # Si está intentando conectarse
                    elif "Try to connect" in response:
                        self.status = DeviceStatus(
                            device_id="NM Device (Connecting)",
                            hash_rate=0.0,
                            temperature=0.0,
                            fan_speed=0,
                            is_mining=False
                        )
                    else:
                        # Por ahora, devolvemos un estado básico
                        self.status = DeviceStatus(
                            device_id="NM Device",
                            hash_rate=0.0,
                            temperature=0.0,
                            fan_speed=0,
                            is_mining=False
                        )
                except Exception as e:
                    print(f"Error processing status: {e}")
                    self.status.error = str(e)
            else:
                print("No response received for status command")
                self.status.error = "No response"
        return self.status
        
    def start_mining(self) -> bool:
        return self.send_command("start")
        
    def stop_mining(self) -> bool:
        return self.send_command("stop")
        
    def set_fan_speed(self, speed: int) -> bool:
        if 0 <= speed <= 100:
            return self.send_command(f"fan {speed}")
        return False
        
    def reboot(self) -> bool:
        return self.send_command("reboot") 