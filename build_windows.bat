@echo off
echo Building NM Controller for Windows...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt
pip install pyinstaller altgraph tomlkit
pip install --upgrade PySide6

REM Create the executable
echo Creating executable...
pyinstaller --noconfirm "NM Controller.spec"

REM Create dist directory if it doesn't exist
if not exist "dist\NM Controller" mkdir "dist\NM Controller"

REM Copy additional DLLs
echo Copying additional DLLs...
xcopy /Y "C:\Windows\System32\bcrypt.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\VERSION.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\ncrypt.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\Secur32.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\imagehlp.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\IMM32.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\WTSAPI32.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\SHLWAPI.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\WINMM.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\COMDLG32.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\dwmapi.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\SETUPAPI.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\d3d9.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\d3d11.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\d3d12.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\DWrite.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\d2d1.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\UxTheme.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\IPHLPAPI.DLL" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\MPR.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\USERENV.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\NETAPI32.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\AUTHZ.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\DNSAPI.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\WINHTTP.dll" "dist\NM Controller\"
xcopy /Y "C:\Windows\System32\dxgi.dll" "dist\NM Controller\"

echo Build complete! The executable is in the dist folder.
pause 
