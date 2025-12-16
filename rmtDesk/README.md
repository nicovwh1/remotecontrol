# rmtDesk - Control Remoto de Escritorio

## Descripción

rmtDesk es una aplicación de control remoto de escritorio desarrollada en Python que permite controlar un equipo de forma remota a través de una conexión de red. El sistema está compuesto por dos componentes principales: un cliente (ctrl) y un servidor (bectrl) que se comunican mediante sockets TCP.

## Características Principales

- 🖥️ **Transmisión de pantalla en tiempo real** con compresión inteligente
- 🖱️ **Control remoto de mouse** (movimiento, clics, rueda)
- ⌨️ **Control remoto de teclado** con soporte multiplataforma
- 🔄 **Transmisión diferencial** para optimizar el ancho de banda
- 🌐 **Soporte multiplataforma** (Windows, Linux/X11, macOS)
- 📱 **Interfaz gráfica intuitiva** desarrollada con tkinter
- 🔧 **Configuración automática de IP** con sistema de fallbacks inteligente
- 🌐 **Detección automática de IP local** excluyendo VPN y ZSCALER
- ⚙️ **Puerto por defecto optimizado** (3380) para mejor compatibilidad

## Arquitectura del Sistema

### Diagrama de Funcionamiento

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SISTEMA rmtDesk                                   │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────┐                    ┌─────────────────────────┐
│       CLIENTE           │                    │       SERVIDOR          │
│     (ctrl/main.pyw)     │                    │    (bectrl/main.py)     │
├─────────────────────────┤                    ├─────────────────────────┤
│                         │                    │                         │
│  ┌─────────────────┐    │                    │  ┌─────────────────┐    │
│  │   Interfaz GUI  │    │                    │  │ Captura Pantalla│    │
│  │   (tkinter)     │    │                    │  │  (ImageGrab)    │    │
│  └─────────────────┘    │                    │  └─────────────────┘    │
│           │              │                    │           │             │
│  ┌─────────────────┐    │                    │  ┌─────────────────┐    │
│  │ Procesamiento   │    │                    │  │   Compresión    │    │
│  │   de Imagen     │    │                    │  │   de Imagen     │    │
│  │   (OpenCV)      │    │                    │  │   (OpenCV)      │    │
│  └─────────────────┘    │                    │  └─────────────────┘    │
│           │              │                    │           │             │
│  ┌─────────────────┐    │                    │  ┌─────────────────┐    │
│  │ Visualización   │    │                    │  │ Transmisión     │    │
│  │   de Pantalla   │    │                    │  │  Diferencial    │    │
│  └─────────────────┘    │                    │  └─────────────────┘    │
│           │              │                    │           │             │
│  ┌─────────────────┐    │   Socket TCP/IP    │  ┌─────────────────┐    │
│  │ Envío Eventos   │◄───┼────────────────────┼──►│ Recepción       │    │
│  │ Mouse/Teclado   │    │     Puerto 3380     │  │ Eventos         │    │
│  └─────────────────┘    │                    │  └─────────────────┘    │
│                         │                    │           │             │
│                         │                    │  ┌─────────────────┐    │
│                         │                    │  │ Ejecución       │    │
│                         │                    │  │ Comandos        │    │
│                         │                    │  │ (pyautogui)     │    │
│                         │                    │  └─────────────────┘    │
└─────────────────────────┘                    └─────────────────────────┘
           │                                                 │
           │                                                 │
           └─────────────────────────────────────────────────┘
                        Red TCP/IP (Puerto 3380)
```

### Flujo de Datos

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FLUJO DE TRANSMISIÓN                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

SERVIDOR (bectrl)                           CLIENTE (ctrl)
     │                                           │
     ▼                                           │
┌─────────────┐                                 │
│ Captura     │                                 │
│ Pantalla    │                                 │
└─────────────┘                                 │
     │                                           │
     ▼                                           │
┌─────────────┐                                 │
│ Compresión  │                                 │
│ JPEG/PNG    │                                 │
└─────────────┘                                 │
     │                                           │
     ▼                                           │
┌─────────────┐                                 │
│ Cálculo     │                                 │
│ Diferencial │                                 │
└─────────────┘                                 │
     │                                           │
     ▼                                           │
┌─────────────┐    Transmisión TCP    ┌─────────────┐
│ Envío de    │ ────────────────────► │ Recepción   │
│ Datos       │                       │ de Imagen   │
└─────────────┘                       └─────────────┘
                                           │
                                           ▼
                                      ┌─────────────┐
                                      │ Decodifica- │
                                      │ ción        │
                                      └─────────────┘
                                           │
                                           ▼
                                      ┌─────────────┐
                                      │ Visualiza-  │
                                      │ ción GUI    │
                                      └─────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                         FLUJO DE CONTROL                                       │
└─────────────────────────────────────────────────────────────────────────────────┘

CLIENTE (ctrl)                              SERVIDOR (bectrl)
     │                                           │
     ▼                                           │
┌─────────────┐                                 │
│ Eventos     │                                 │
│ Mouse/Tecla │                                 │
└─────────────┘                                 │
     │                                           │
     ▼                                           │
┌─────────────┐                                 │
│ Codificación│                                 │
│ de Eventos  │                                 │
└─────────────┘                                 │
     │                                           │
     ▼                                           │
┌─────────────┐    Transmisión TCP    ┌─────────────┐
│ Envío de    │ ────────────────────► │ Recepción   │
│ Comandos    │                       │ de Comandos │
└─────────────┘                       └─────────────┘
                                           │
                                           ▼
                                      ┌─────────────┐
                                      │ Decodifica- │
                                      │ ción        │
                                      └─────────────┘
                                           │
                                           ▼
                                      ┌─────────────┐
                                      │ Ejecución   │
                                      │ (pyautogui) │
                                      └─────────────┘
```

## Configuración Automática de Red (v2.0)

### Sistema de Configuración Inteligente

#### Cliente - Configuración Automática de IP
El cliente implementa un sistema de fallbacks para obtener la IP del servidor:

1. **Prioridad 1**: Lee IP desde archivo `\ipwork.txt`
2. **Prioridad 2**: Si no existe el archivo, hace ping a `example.com`
3. **Prioridad 3**: Si la IP no es válida, usa IP por defecto `192.168.1.2`

```python
# Flujo de configuración automática
IP_FILE_PATH = "D:\\shared\\nico\\Desktop\\Netcool\\script\\ipwork.txt"
FALLBACK_HOSTNAME = "mail.nicodf.mooo.com"
DEFAULT_IP = "192.168.1.74"
DEFAULT_PORT = 3380
```

#### Servidor - Detección Automática de IP Local
El servidor detecta automáticamente su IP local real:

- ✅ **Excluye IPs de VPN** (OpenVPN, Cisco AnyConnect)
- ✅ **Excluye IPs de ZSCALER** y otros proxies
- ✅ **Prefiere rangos de red local** (192.168.x.x, 10.x.x.x, 172.x.x.x)
- ✅ **Detección inteligente** de la interfaz de red óptima

### Funciones de Configuración

#### Cliente
- `validar_ip()`: Valida formato de direcciones IP
- `leer_ip_desde_archivo()`: Lee IP desde archivo especificado
- `ping_y_obtener_ip()`: Resuelve hostname a IP
- `obtener_ip_configurada()`: Lógica principal con fallbacks

#### Servidor
- `obtener_interfaces_red()`: Obtiene interfaces disponibles
- `filtrar_ip_local()`: Filtra IPs locales válidas
- `detectar_ip_local()`: Detecta IP local óptima

## Componentes del Sistema

### Cliente (ctrl/main.pyw)
- **Interfaz gráfica**: Ventana principal con visualización de la pantalla remota
- **Gestión de eventos**: Captura eventos de mouse y teclado del usuario
- **Comunicación**: Envía comandos al servidor y recibe imágenes
- **Renderizado**: Muestra la pantalla remota en tiempo real
- **Configuración automática**: Sistema inteligente de detección de IP con fallbacks

### Servidor (bectrl/main.py)
- **Captura de pantalla**: Utiliza ImageGrab para capturar la pantalla
- **Procesamiento de imagen**: Compresión y optimización con OpenCV
- **Control de entrada**: Ejecuta comandos de mouse y teclado con pyautogui
- **Gestión de conexiones**: Maneja múltiples clientes simultáneamente
- **Detección de IP**: Identificación automática de IP local excluyendo VPN

### Módulo de Teclado (_keyboard.py)
- **Mapeo de teclas**: Soporte para Windows, X11 y macOS
- **Códigos de tecla**: Mapeo completo de teclas especiales y multimedia
- **Compatibilidad**: Detección automática de plataforma

## Instalación y Configuración

### Requisitos del Sistema
- Python 3.9 o superior
- Sistema operativo: Windows, Linux, macOS

### Dependencias
```bash
pip install -r requirements.txt
```

**Dependencias incluidas:**
- `opencv-python`: Procesamiento de imágenes
- `Pillow`: Manipulación de imágenes
- `pyautogui`: Automatización de GUI
- `mouse`: Control de mouse
- `numpy`: Operaciones numéricas

### Configuración

1. **Servidor (Equipo a controlar)**:
   ```bash
   cd bectrl
   python main.py
   ```

2. **Cliente (Equipo controlador)**:
   ```bash
   cd ctrl
   python main.pyw
   ```

3. **Configuración de red**:
   - Puerto por defecto: 3380 (actualizado en v2.0)
   - **Configuración automática**: El cliente detecta automáticamente la IP del servidor
   - **Fallbacks inteligentes**: Sistema de respaldo para configuración de IP
   - Asegurar que el firewall permita conexiones en el puerto 3380

## Protocolo de Comunicación

### Tipos de Mensaje

| Tipo | Código | Descripción |
|------|--------|-------------|
| Imagen completa | 1 | Transmisión de imagen completa |
| Imagen diferencial | 2 | Transmisión solo de cambios |
| Comando mouse | 3 | Eventos de mouse |
| Comando teclado | 4 | Eventos de teclado |

### Formato de Datos
```
[HEADER: 1 byte tipo][TAMAÑO: 4 bytes][DATOS: variable]
```

## Optimizaciones

### Transmisión de Imagen
- **Compresión JPEG**: Calidad ajustable para balance velocidad/calidad
- **Transmisión diferencial**: Solo envía píxeles que han cambiado
- **Compresión PNG**: Para imágenes con pocos cambios

### Rendimiento
- **Detección de cambios**: Algoritmo eficiente para detectar modificaciones
- **Buffer de imágenes**: Reutilización de buffers para reducir allocaciones
- **Compresión adaptativa**: Selección automática del mejor método

## Seguridad

⚠️ **Advertencia de Seguridad**: Esta aplicación no incluye cifrado ni autenticación. Se recomienda:
- Usar solo en redes confiables
- Implementar VPN para conexiones remotas
- Configurar firewall adecuadamente
- No usar en redes públicas

## Limitaciones

- No incluye cifrado de datos
- Sin autenticación de usuarios
- Rendimiento dependiente del ancho de banda
- Latencia variable según la red

## Desarrollo y Contribución

### Estructura del Proyecto
```
rmtDesk/
├── ctrl/                 # Cliente
│   └── main.pyw         # Aplicación principal del cliente
├── bectrl/              # Servidor
│   ├── main.py          # Aplicación principal del servidor
│   └── _keyboard.py     # Módulo de mapeo de teclado
├── requirements.txt     # Dependencias
├── LICENSE             # Licencia
└── README.md           # Este archivo
```

### Historial de Versiones

- **v2.0-final**: Configuración automática de IP y puerto optimizado (3380)
  - ✅ Cliente con sistema de fallbacks para IP
  - ✅ Servidor con detección automática de IP local
  - ✅ Exclusión de IPs de VPN y ZSCALER
  - ✅ Puerto por defecto cambiado a 3380
  - ✅ Sin dependencias externas agregadas
- **v1.3-corregido**: Correcciones finales de comentarios en chino
- **v1.2-final**: Documentación completa y correcciones
- **v1.1-traducido**: Traducción completa de comentarios del chino al español
- **v1.0-original**: Versión original con comentarios en chino

## Licencia

Este proyecto está bajo la licencia especificada en el archivo LICENSE.

## Soporte

Para reportar problemas o solicitar características:
1. Verificar la compatibilidad del sistema
2. Revisar la configuración de red
3. Consultar los logs de error
4. Verificar las dependencias instaladas

---

**Nota**: Esta documentación corresponde a la versión 2.0 del proyecto rmtDesk, que incluye:
- ✅ **Traducción completa** de comentarios del chino al español
- ✅ **Configuración automática de IP** con sistema de fallbacks inteligente
- ✅ **Detección automática de IP local** excluyendo VPN y ZSCALER
- ✅ **Puerto optimizado** (3380) para mejor compatibilidad
- ✅ **Compatibilidad total** con funcionalidad existente
- ✅ **Sin dependencias externas** agregadas
