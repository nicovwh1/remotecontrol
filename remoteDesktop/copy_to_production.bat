@echo off
echo ========================================
echo COPIA A PRODUCCION - REMOTE DESKTOP
echo ========================================
echo Fecha: %date% %time%
echo.

REM Configuracion de directorios
set SOURCE_DIR=%~dp0
set DEST1=%%
set DEST2=%%

echo Directorio origen: %SOURCE_DIR%
echo Destino 1: %DEST1%
echo Destino 2: %DEST2%
echo.

REM Verificar que existen los directorios origen
if not exist "%SOURCE_DIR%ctrl" (
    echo ERROR: No se encuentra el directorio ctrl
    pause
    exit /b 1
)

if not exist "%SOURCE_DIR%bectrl" (
    echo ERROR: No se encuentra el directorio bectrl
    pause
    exit /b 1
)

echo ========================================
echo COPIANDO AL DESTINO 1
echo ========================================

REM Crear directorio destino 1 si no existe
if not exist "%DEST1%" (
    echo Creando directorio: %DEST1%
    mkdir "%DEST1%"
)

REM Copiar ctrl y bectrl al destino 1
echo Copiando ctrl\* a %DEST1%ctrl\
if not exist "%DEST1%ctrl" mkdir "%DEST1%ctrl"
xcopy "%SOURCE_DIR%ctrl\*" "%DEST1%ctrl\" /E /Y /I
if %errorlevel% neq 0 (
    echo ERROR: Fallo al copiar ctrl al destino 1
    pause
    exit /b 1
)

echo Copiando bectrl\* a %DEST1%bectrl\
if not exist "%DEST1%bectrl" mkdir "%DEST1%bectrl"
xcopy "%SOURCE_DIR%bectrl\*" "%DEST1%bectrl\" /E /Y /I
if %errorlevel% neq 0 (
    echo ERROR: Fallo al copiar bectrl al destino 1
    pause
    exit /b 1
)

echo ✓ Destino 1 completado

echo ========================================
echo COPIANDO AL DESTINO 2
echo ========================================

REM Crear directorio destino 2 si no existe
if not exist "%DEST2%" (
    echo Creando directorio: %DEST2%
    mkdir "%DEST2%"
)

REM Copiar ctrl y bectrl al destino 2
echo Copiando ctrl\* a %DEST2%ctrl\
if not exist "%DEST2%ctrl" mkdir "%DEST2%ctrl"
xcopy "%SOURCE_DIR%ctrl\*" "%DEST2%ctrl\" /E /Y /I
if %errorlevel% neq 0 (
    echo ERROR: Fallo al copiar ctrl al destino 2
    pause
    exit /b 1
)

echo Copiando bectrl\* a %DEST2%bectrl\
if not exist "%DEST2%bectrl" mkdir "%DEST2%bectrl"
xcopy "%SOURCE_DIR%bectrl\*" "%DEST2%bectrl\" /E /Y /I
if %errorlevel% neq 0 (
    echo ERROR: Fallo al copiar bectrl al destino 2
    pause
    exit /b 1
)

echo ✓ Destino 2 completado

echo ========================================
echo COPIA COMPLETADA EXITOSAMENTE
echo ========================================
echo Archivos copiados a:
echo - %DEST1%
echo - %DEST2%
echo.
echo Presiona cualquier tecla para salir...
 
