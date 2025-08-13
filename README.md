# Sistema de Control Remoto con Python (fork (https://github.com/pysrc/remote-desktop))

Un sistema completo de control remoto implementado en Python que permite controlar un equipo de forma remota a través de la red. El sistema consta de dos componentes principales: un servidor (extremo controlado) y un cliente (extremo controlador).

## 📋 Tabla de Contenidos

- [Descripción](#descripción)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Componentes](#componentes)
- [Requerimientos](#requerimientos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Modo Debug](#modo-debug)
- [Características](#características)
- [Recursos Adicionales](#recursos-adicionales)

## 📖 Descripción

Este sistema permite el control remoto de escritorio con las siguientes funcionalidades:
- Captura y transmisión de pantalla en tiempo real
- Control de mouse y teclado remotos
- Compresión de imágenes para optimizar el ancho de banda
- Soporte para proxy SOCKS5
- Sistema de logging con rotación automática
- Modo debug para diagnósticos detallados

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                    SISTEMA DE CONTROL REMOTO                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────┐                    ┌─────────────────────┐
│     SERVIDOR        │                    │      CLIENTE        │
│    (bectrl/)        │                    │     (ctrl/)         │
│                     │                    │                     │
│ ┌─────────────────┐ │                    │ ┌─────────────────┐ │
│ │   Captura de    │ │                    │ │   Interfaz      │ │
│ │   Pantalla      │ │                    │ │   Gráfica       │ │
│ │   (PIL/OpenCV)  │ │                    │ │   (Tkinter)     │ │
│ └─────────────────┘ │                    │ └─────────────────┘ │
│          │          │                    │          │          │
│          ▼          │                    │          ▼          │
│ ┌─────────────────┐ │                    │ ┌─────────────────┐ │
│ │   Compresión    │ │                    │ │   Visualización │ │
│ │   de Imagen     │ │                    │ │   de Pantalla   │ │
│ │   (JPEG)        │ │                    │ │   Remota        │ │
│ └─────────────────┘ │                    │ └─────────────────┘ │
│          │          │                    │          │          │
│          ▼          │                    │          ▼          │
│ ┌─────────────────┐ │    CONEXIÓN TCP    │ ┌─────────────────┐ │
│ │   Servidor      │ │◄──────────────────►│ │   Cliente       │ │
│ │   Socket        │ │    Puerto 3380     │ │   Socket        │ │
│ │   (Puerto 3380) │ │                    │ │                 │ │
│ └─────────────────┘ │                    │ └─────────────────┘ │
│          │          │                    │          │          │
│          ▼          │                    │          ▼          │
│ ┌─────────────────┐ │                    │ ┌─────────────────┐ │
│ │   Control de    │ │                    │ │   Eventos de    │ │
│ │   Mouse/Teclado │ │                    │ │   Usuario       │ │
│ │   (PyAutoGUI)   │ │                    │ │   (Mouse/Teclado)│ │
│ └─────────────────┘ │                    │ └─────────────────┘ │
│                     │                    │                     │
│ ┌─────────────────┐ │                    │ ┌─────────────────┐ │
│ │   Sistema de    │ │                    │ │   Sistema de    │ │
│ │   Logging       │ │                    │ │   Logging       │ │
│ │   (Rotación)    │ │                    │ │   (Rotación)    │ │
│ └─────────────────┘ │                    │ └─────────────────┘ │
└─────────────────────┘                    └─────────────────────┘
           │                                          │
           ▼                                          ▼
┌─────────────────────┐                    ┌─────────────────────┐
│  logs/              │                    │  logs/              │
│  remote_server.log  │                    │  remote_client.log  │
└─────────────────────┘                    └─────────────────────┘

                    ┌─────────────────────┐
                    │   PROXY SOCKS5      │
                    │   (Opcional)        │
                    │   novpn.cn          │
                    └─────────────────────┘
```

## 🧩 Componentes

### Servidor (bectrl/)
- **main.py**: Servidor principal sin interfaz gráfica
- **_keyboard.py**: Mapeo de códigos de teclado multiplataforma
- **Funcionalidades**:
  - Captura de pantalla automática
  - Procesamiento de comandos de control
  - Compresión de imágenes
  - Detección automática de IP
  - Sistema de logging

### Cliente (ctrl/)
- **main.pyw**: Cliente con interfaz gráfica
- **Funcionalidades**:
  - Interfaz de usuario intuitiva
  - Visualización de pantalla remota
  - Control de mouse y teclado
  - Soporte para proxy SOCKS5
  - Escalado de imagen

## 📦 Requerimientos

### Dependencias de Python
```
numpy>=1.21.0          # Procesamiento de arrays numéricos
Pillow>=8.3.0          # Manipulación de imágenes
PyAutoGUI>=0.9.53      # Automatización de GUI
opencv-python>=4.5.0   # Procesamiento de imágenes y video
mouse>=0.7.1           # Control de mouse
```

### Módulos Estándar Utilizados
- **socket**: Comunicación de red TCP
- **threading**: Manejo de hilos concurrentes
- **struct**: Empaquetado/desempaquetado de datos binarios
- **time**: Manejo de tiempo y delays
- **platform**: Detección de sistema operativo
- **argparse**: Procesamiento de argumentos de línea de comandos
- **logging**: Sistema de registro de eventos
- **tkinter**: Interfaz gráfica (solo cliente)
- **re**: Expresiones regulares
- **subprocess**: Ejecución de procesos del sistema
- **os**: Operaciones del sistema operativo

### Requerimientos del Sistema
- **Python 3.7+**
- **Windows/Linux/macOS**
- **Conexión de red TCP**
- **Permisos de captura de pantalla**
- **Permisos de control de mouse/teclado**

## 🚀 Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone <repository-url>
   cd remote-desktop-master
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verificar instalación**:
   ```bash
   python bectrl/main.py --help
   python ctrl/main.pyw --help
   ```

## 💻 Uso

### Servidor (Equipo a Controlar)
```bash
# Modo normal (sin ventanas gráficas)
python bectrl/main.py

# Modo debug (logging detallado)
python bectrl/main.py --debug
```

### Cliente (Equipo Controlador)
```bash
# Modo normal
python ctrl/main.pyw

# Modo debug
python ctrl/main.pyw --debug
```

### Script de Ayuda
Utiliza el script interactivo para facilitar el uso:
```bash
run_debug_example.bat
```

## 🐛 Modo Debug

El sistema incluye un modo debug completo con:
- **Logging detallado** de todas las operaciones
- **Rotación automática** de logs cada 24 horas
- **Retención** de 30 días de historial
- **Archivos separados** para servidor y cliente

### Archivos de Log
- `logs/remote_server.log` - Logs del servidor
- `logs/remote_client.log` - Logs del cliente

Para más información, consulta [DEBUG_README.md](DEBUG_README.md)

## ✨ Características

- 🖥️ **Control remoto completo**: Mouse, teclado y visualización
- 🔒 **Sin interfaz gráfica en servidor**: Ideal para servidores headless
- 🌐 **Soporte para proxy**: Compatible con SOCKS5
- 📊 **Compresión inteligente**: Optimización automática de ancho de banda
- 🔍 **Sistema de logging**: Diagnósticos detallados y rotación automática
- 🎯 **Multiplataforma**: Windows, Linux y macOS
- ⚡ **Alto rendimiento**: Transmisión eficiente de imágenes
- 🛠️ **Modo debug**: Herramientas avanzadas de diagnóstico

## 📚 Recursos Adicionales

### Implementación en Rust
Versión optimizada disponible en: https://github.com/pysrc/diffscreen

### Videos Explicativos
- [Primera Lección](https://www.bilibili.com/video/BV1Nk4y117f2/)
- [Segunda Lección](https://www.bilibili.com/video/BV1oz4y1o7fx/)
- [Tercera Lección](https://www.bilibili.com/video/BV1jA411J7Jj/)
- [Cuarta Lección](https://www.bilibili.com/video/BV1va4y1j7Q8/)
- [Quinta Lección](https://www.bilibili.com/video/BV1e54y1y7eq/)

### Proxy Recomendado
Se recomienda utilizar un proxy SOCKS5 de [novpn.cn](https://novpn.cn) para conexiones a través de internet.

---

**Nota**: Este sistema está diseñado para uso educativo y administrativo legítimo. Asegúrate de tener los permisos apropiados antes de usar en cualquier sistema.
