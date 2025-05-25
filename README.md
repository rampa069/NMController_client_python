# NM Controller (Python Version)

This is a Python implementation of the NM Controller application, designed to monitor and control NM mining devices through a serial connection.

## Features

- Serial port communication with NM devices
- Real-time monitoring of device status
- Temperature and fan speed control
- Mining start/stop control
- Configuration management
- Auto-start and auto-restart options

## Requirements

- Python 3.8 or higher
- PyQt6
- pyserial

## Installation

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python main.py
```

2. Select the appropriate serial port from the dropdown menu
3. Click "Connect" to establish connection with the device
4. Use the interface to monitor and control your NM device

## Configuration

The application can be configured through the Configuration window, accessible from the main interface. Settings include:

- Serial port baud rate
- Connection timeout
- Auto-start mining
- Auto-restart on error
- Temperature limits

## File Structure

- `main.py`: Main application window and entry point
- `config_window.py`: Configuration dialog implementation
- `nm_device.py`: NM device communication and control
- `requirements.txt`: Python package dependencies

## License

This project is licensed under the same terms as the original C# implementation. 