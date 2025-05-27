#!/bin/bash

echo "Building NM Controller for Linux..."

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install it first."
    exit 1
fi

# Instalar dependencias
echo "Installing requirements..."
pip3 install -r requirements.txt
pip3 install pyinstaller
pip3 install --upgrade PySide6

# Crear el ejecutable
echo "Creating executable..."
pyinstaller --name="NMController" \
            --windowed \
            --icon=nm.ico \
            --add-data "nm.ico:." \
            --hidden-import=PySide6.QtXml \
            --hidden-import=PySide6.QtNetwork \
            --hidden-import=PySide6.QtCore \
            --hidden-import=PySide6.QtGui \
            --hidden-import=PySide6.QtWidgets \
            --hidden-import=serial \
            --hidden-import=serial.tools.list_ports \
            --clean \
            main.py

# Crear directorio de release si no existe
mkdir -p release

# Mover el ejecutable al directorio de release
mv dist/NMController release/

# Limpiar archivos temporales
rm -rf build dist *.spec

echo "Build complete! The executable is in the release folder." 