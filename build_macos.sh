#!/bin/bash

# Verificar si Pillow está instalado
if ! python3 -c "import PIL" &> /dev/null; then
    echo "Installing Pillow..."
    pip3 install Pillow
fi

# Convertir el icono de ICO a ICNS
echo "Converting icon to ICNS format..."
python3 -c "
from PIL import Image
import os

# Crear directorio temporal para los iconos
os.makedirs('icon.iconset', exist_ok=True)

# Abrir el icono ICO
img = Image.open('nm.ico')

# Generar diferentes tamaños de icono
sizes = [16, 32, 64, 128, 256, 512, 1024]
for size in sizes:
    resized = img.resize((size, size), Image.Resampling.LANCZOS)
    resized.save(f'icon.iconset/icon_{size}x{size}.png')
    if size <= 512:  # También necesitamos versiones @2x
        resized = img.resize((size*2, size*2), Image.Resampling.LANCZOS)
        resized.save(f'icon.iconset/icon_{size}x{size}@2x.png')

# Convertir el directorio de iconos a ICNS
os.system('iconutil -c icns icon.iconset')

# Limpiar el directorio temporal
os.system('rm -rf icon.iconset')
"

# Crear el ejecutable para macOS
pyinstaller --name="NMController" \
            --windowed \
            --icon=icon.icns \
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

# Asegurarse de que el icono esté en el directorio de recursos
cp nm.ico dist/NMController.app/Contents/Resources/

# Limpiar archivos temporales
rm -rf build *.spec icon.icns
mv dist/NMController.app release/

