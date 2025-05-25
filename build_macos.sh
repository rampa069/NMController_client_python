#!/bin/bash

# Crear el ejecutable para macOS
pyinstaller --name="NMController" \
            --windowed \
            --hidden-import=PySide6.QtXml \
            --hidden-import=PySide6.QtNetwork \
            --hidden-import=PySide6.QtCore \
            --hidden-import=PySide6.QtGui \
            --hidden-import=PySide6.QtWidgets \
            --hidden-import=serial \
            --hidden-import=serial.tools.list_ports \
            --clean \
            main.py



# Limpiar archivos temporales
rm -rf build *.spec
