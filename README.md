# Control Remoto de Escritorio con Python

## Descripción

Este proyecto implementa un sistema de control remoto de escritorio desarrollado en Python que permite controlar una computadora de forma remota a través de la red. El sistema utiliza técnicas de compresión de imágenes y transmisión diferencial para optimizar el rendimiento.

## Estructura del Proyecto

- **`bectrl/`** - Código del extremo controlado (servidor)
- **`ctrl/`** - Código del extremo controlador (cliente)

## Características Principales

- ✅ **Transmisión de pantalla en tiempo real** con compresión JPEG
- ✅ **Control completo de mouse y teclado** remoto
- ✅ **Optimización de ancho de banda** mediante transmisión diferencial
- ✅ **Soporte multiplataforma** (Windows, Linux, macOS)
- ✅ **Soporte para proxy SOCKS5** para conexiones seguras
- ✅ **Interfaz gráfica intuitiva** con escalado de pantalla

## Instalación de Dependencias

```bash
pip install -r requirements.txt
```

### Dependencias Requeridas

- `numpy` - Procesamiento de arrays numéricos
- `Pillow` - Manipulación de imágenes
- `PyAutoGUI` - Control de mouse y teclado
- `opencv-python` - Procesamiento de imágenes y compresión
- `mouse` - Control avanzado del mouse

## Uso Rápido

### 1. Ejecutar el Servidor (Extremo Controlado)

```bash
cd bectrl
python main.py
```

El servidor mostrará la dirección IP y puerto de conexión.

### 2. Ejecutar el Cliente (Extremo Controlador)

```bash
cd ctrl
python main.pyw
```

Ingresa la dirección IP:puerto del servidor y haz clic en "Show".

## Diagrama de Flujo del Sistema

```
┌─────────────────┐         ┌─────────────────┐
│   CLIENTE       │         │    SERVIDOR     │
│   (ctrl/)       │         │   (bectrl/)     │
└─────────────────┘         └─────────────────┘
         │                           │
         │ 1. Conexión TCP           │
         ├──────────────────────────►│
         │                           │
         │ 2. Envío plataforma       │
         ├──────────────────────────►│
         │                           │
         │ 3. Captura pantalla       │
         │◄──────────────────────────┤
         │                           │
         │ 4. Eventos mouse/teclado  │
         ├──────────────────────────►│
         │                           │
         │ 5. Transmisión diferencial│
         │◄──────────────────────────┤
         │                           │
         │ 6. Actualización pantalla │
         │◄──────────────────────────┤
```

## Arquitectura Técnica

### Servidor (bectrl/main.py)

1. **Captura de Pantalla**: Utiliza `ImageGrab` para capturar la pantalla
2. **Compresión**: Aplica compresión JPEG con calidad configurable
3. **Transmisión Diferencial**: Envía solo los cambios entre frames
4. **Control de Eventos**: Procesa comandos de mouse y teclado remotos

### Cliente (ctrl/main.pyw)

1. **Interfaz Gráfica**: Ventana Tkinter para configuración y visualización
2. **Recepción de Imágenes**: Decodifica y muestra frames recibidos
3. **Captura de Eventos**: Envía eventos de mouse y teclado al servidor
4. **Escalado**: Permite ajustar el tamaño de visualización

## Configuración Avanzada

### Proxy SOCKS5

Para usar un proxy SOCKS5:
1. Haz clic en "Proxy" en la interfaz del cliente
2. Ingresa la dirección del proxy (ej: `127.0.0.1:1080`)
3. Conecta normalmente al servidor

### Parámetros de Rendimiento

- **IDLE**: Intervalo entre capturas (0.05s por defecto)
- **IMQUALITY**: Calidad JPEG (50 por defecto, rango 1-100)
- **SCROLL_NUM**: Sensibilidad del scroll del mouse (5 por defecto)

## Implementación en Rust

Para una versión más eficiente en Rust, consulta:
https://github.com/pysrc/diffscreen

## Videos Tutoriales (Chino)

- [Primera parte](https://www.bilibili.com/video/BV1Nk4y117f2/) - Introducción y configuración
- [Segunda parte](https://www.bilibili.com/video/BV1oz4y1o7fx/) - Implementación del servidor
- [Tercera parte](https://www.bilibili.com/video/BV1jA411J7Jj/) - Implementación del cliente
- [Cuarta parte](https://www.bilibili.com/video/BV1va4y1j7Q8/) - Optimizaciones
- [Quinta parte](https://www.bilibili.com/video/BV1e54y1y7eq/) - Características avanzadas

## Licencia

Ver archivo LICENSE para más detalles.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o envía un pull request.
