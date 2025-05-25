@echo off

REM Crear el ejecutable para Windows
pyinstaller --name="NMController" ^
            --windowed ^
            --hidden-import=PySide6.QtXml ^
            --hidden-import=PySide6.QtNetwork ^
            --hidden-import=PySide6.QtCore ^
            --hidden-import=PySide6.QtGui ^
            --hidden-import=PySide6.QtWidgets ^
            --hidden-import=serial ^
            --hidden-import=serial.tools.list_ports ^
            main.py

REM Crear carpeta exe si no existe
if not exist ..\exe\windows mkdir ..\exe\windows

REM Mover el ejecutable a la carpeta exe
move dist\NMController.exe ..\exe\windows\

REM Limpiar archivos temporales
rmdir /s /q build
rmdir /s /q dist
del /q *.spec 