import struct
import socket
from PIL import ImageGrab
import cv2
import numpy as np
import threading
import time
import pyautogui as ag
import mouse
from _keyboard import getKeycodeMapping
from random import randint 
from tkinter.messagebox import showinfo # To give alerts
import subprocess
import platform
import argparse
import logging
import os
import sys

# Variables globales para configuración
DEBUG_MODE = False
LOG_ENABLED = True
logger = None

# Ciclo de pantalla
IDLE = 0.05

# Sensibilidad de rueda del mouse
SCROLL_NUM = 5

# Configuración del servidor
bufsize = 1024
DEFAULT_PORT = 3380

def parse_arguments():
    """Analiza los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Servidor de escritorio remoto')
    parser.add_argument('--port', '-p', type=int, default=DEFAULT_PORT,
                       help=f'Puerto del servidor (por defecto: {DEFAULT_PORT})')
    parser.add_argument('--debug', '-d', action='store_true',
                       help='Activar modo debug')
    return parser.parse_args()

def setup_logging():
    """Configura el sistema de logging"""
    global logger
    
    # Obtener directorio un nivel arriba del script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    log_file = os.path.join(parent_dir, 'rmtDesk_server.log')
    
    # Configurar logger
    logger = logging.getLogger('rmtDesk_server')
    logger.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler (solo si está en modo debug)
    if DEBUG_MODE:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    logger.info("Sistema de logging inicializado")
    return log_file

def debug_print(message):
    """Imprime mensaje solo en modo debug"""
    if DEBUG_MODE:
        print(f"[DEBUG] {message}")
    if logger:
        logger.info(message)

# Funciones de detección automática de IP local
def obtener_interfaces_red():
    """Obtiene todas las interfaces de red disponibles usando métodos estándar"""
    interfaces = []
    try:
        # Método 1: Usar socket para obtener IP local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        interfaces.append(local_ip)
        
        # Método 2: Obtener hostname local
        hostname_ip = socket.gethostbyname(socket.gethostname())
        if hostname_ip not in interfaces:
            interfaces.append(hostname_ip)
            
    except Exception as e:
        print(f"Error obteniendo interfaces: {e}")
    
    return interfaces

def filtrar_ip_local(interfaces):
    """Filtra y selecciona la IP local principal excluyendo VPN y ZSCALER"""
    debug_print(f"Filtrando interfaces: {interfaces}")
    
    # Lista de patrones a excluir (VPN, Zscaler, etc.)
    patrones_excluir = [
        'zscaler', 'vpn', 'cisco', 'anyconnect', 'tunnel',
        'tap', 'tun', 'virtual', 'vmware', 'vbox'
    ]
    
    for ip in interfaces:
        # Excluir loopback
        if ip.startswith('127.'):
            debug_print(f"Excluyendo loopback: {ip}")
            continue
            
        # Verificar si la IP está en rangos de VPN conocidos
        ip_parts = ip.split('.')
        if len(ip_parts) == 4:
            # Rangos típicos de VPN corporativas
            if (ip.startswith('172.16.') or ip.startswith('172.17.') or 
                ip.startswith('172.18.') or ip.startswith('172.19.') or
                ip.startswith('10.0.') or ip.startswith('10.1.') or
                ip.startswith('10.2.') or ip.startswith('10.3.')):
                debug_print(f"Posible IP de VPN detectada: {ip}")
                continue
        
        # Preferir rangos de red local estándar
        if (ip.startswith('192.168.') or 
            (ip.startswith('10.') and not ip.startswith('10.0.') and not ip.startswith('10.1.')) or
            ip.startswith('172.20.') or ip.startswith('172.21.') or ip.startswith('172.22.')):
            debug_print(f"IP local válida encontrada: {ip}")
            return ip
    
    # Si no encuentra una IP local típica, usar la primera disponible
    fallback_ip = interfaces[0] if interfaces else '127.0.0.1'
    debug_print(f"Usando IP de fallback: {fallback_ip}")
    return fallback_ip

def detectar_ip_local():
    """Detecta automáticamente la IP local del servidor"""
    debug_print("Detectando IP local del servidor...")
    interfaces = obtener_interfaces_red()
    
    if not interfaces:
        debug_print("No se pudieron detectar interfaces de red, usando localhost")
        return '127.0.0.1'
    
    ip_local = filtrar_ip_local(interfaces)
    debug_print(f"IP local detectada: {ip_local}")
    debug_print(f"Interfaces disponibles: {interfaces}")
    
    return ip_local

# Analizar argumentos de línea de comandos
args = parse_arguments()
DEBUG_MODE = args.debug

# Configurar logging
log_file = setup_logging()

# Detectar IP local automáticamente
server_ip = detectar_ip_local()
port = args.port
host = (server_ip, port)

# Configurar socket del servidor
soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
soc.bind(host)
soc.listen(1)

debug_print(f"Servidor configurado en {server_ip}:{port}")
debug_print(f"Logs guardados en: {log_file}")

# Mostrar información solo en modo debug
if DEBUG_MODE:
    showinfo('Control Data', f'Host = {server_ip}\nPort = {port}\nServidor iniciado en modo DEBUG\nLogs: {log_file}')
    print(f"Servidor iniciado en {server_ip}:{port} (Modo DEBUG)")
else:
    debug_print(f"Servidor iniciado en {server_ip}:{port} (Modo silencioso)")

# Ratio de compresión 1-100, menor valor = mayor compresión y pérdida de calidad
IMQUALITY = 50

lock = threading.Lock()

# if sys.platform == "win32":
#     from ._keyboard_win import keycodeMapping
# elif platform.system() == "Linux":
#     from ._keyboard_x11 import keycodeMapping
# elif sys.platform == "darwin":
#     from ._keyboard_osx import keycodeMapping


def ctrl(conn):
    '''
    Leer comandos de control y restaurar operaciones en la máquina local
    '''
    keycodeMapping = {}
    def Op(key, op, ox, oy):
        debug_print(f"Operación: key={key}, op={op}, x={ox}, y={oy}")
        if key == 4:
            # Movimiento del mouse
            mouse.move(ox, oy)
        elif key == 1:
            if op == 100:
                # Presionar botón izquierdo
                ag.mouseDown(button=ag.LEFT)
                debug_print("Mouse: botón izquierdo presionado")
            elif op == 117:
                # Soltar botón izquierdo
                ag.mouseUp(button=ag.LEFT)
                debug_print("Mouse: botón izquierdo soltado")
        elif key == 2:
            # Evento de rueda
            if op == 0:
                # Hacia arriba
                ag.scroll(-SCROLL_NUM)
                debug_print("Mouse: scroll hacia arriba")
            else:
                # Hacia abajo
                ag.scroll(SCROLL_NUM)
                debug_print("Mouse: scroll hacia abajo")
        elif key == 3:
            # Botón derecho del mouse
            if op == 100:
                # Presionar botón derecho
                ag.mouseDown(button=ag.RIGHT)
                debug_print("Mouse: botón derecho presionado")
            elif op == 117:
                # Soltar botón derecho
                ag.mouseUp(button=ag.RIGHT)
                debug_print("Mouse: botón derecho soltado")
        else:
            k = keycodeMapping.get(key)
            if k is not None:
                if op == 100:
                    ag.keyDown(k)
                    debug_print(f"Teclado: tecla {k} presionada")
                elif op == 117:
                    ag.keyUp(k)
                    debug_print(f"Teclado: tecla {k} soltada")
    try:
        debug_print("Iniciando función de control")
        plat = b''
        while True:
            plat += conn.recv(3-len(plat))
            if len(plat) == 3:
                break
        platform_info = plat.decode()
        debug_print(f"Plataforma del cliente: {platform_info}")
        keycodeMapping = getKeycodeMapping(plat)
        debug_print("Mapeo de teclas configurado")
        base_len = 6
        while True:
            cmd = b''
            rest = base_len - 0
            while rest > 0:
                cmd += conn.recv(rest)
                rest -= len(cmd)
            key = cmd[0]
            op = cmd[1]
            x = struct.unpack('>H', cmd[2:4])[0]
            y = struct.unpack('>H', cmd[4:6])[0]
            Op(key, op, x, y)
    except Exception as e:
        debug_print(f"Error en función de control: {e}")
        if logger:
            logger.error(f"Error en función de control: {e}")
        return


# Imagen numpy comprimida
img = None
# Imagen codificada
imbyt = None


def handle(conn):
    global img, imbyt
    try:
        debug_print("Iniciando función de manejo de imágenes")
        lock.acquire()
        if imbyt is None:
            debug_print("Capturando imagen inicial")
            imorg = np.asarray(ImageGrab.grab())
            _, imbyt = cv2.imencode(
                ".jpg", imorg, [cv2.IMWRITE_JPEG_QUALITY, IMQUALITY])
            imnp = np.asarray(imbyt, np.uint8)
            img = cv2.imdecode(imnp, cv2.IMREAD_COLOR)
            debug_print(f"Imagen inicial capturada: {len(imbyt)} bytes")
        lock.release()
        
        # Enviar imagen inicial
        lenb = struct.pack(">BI", 1, len(imbyt))
        conn.sendall(lenb)
        conn.sendall(imbyt)
        debug_print("Imagen inicial enviada al cliente")
        
        frame_count = 0
        while True:
            # fix for linux
            time.sleep(IDLE)
            gb = ImageGrab.grab()
            imgnpn = np.asarray(gb)
            _, timbyt = cv2.imencode(
                ".jpg", imgnpn, [cv2.IMWRITE_JPEG_QUALITY, IMQUALITY])
            imnp = np.asarray(timbyt, np.uint8)
            imgnew = cv2.imdecode(imnp, cv2.IMREAD_COLOR)
            
            # Calcular diferencia de imagen
            imgs = imgnew ^ img
            if (imgs != 0).any():
                # Cambio detectado en la imagen
                frame_count += 1
                if frame_count % 100 == 0:  # Log cada 100 frames
                    debug_print(f"Frames procesados: {frame_count}")
            else:
                continue
                
            imbyt = timbyt
            img = imgnew
            
            # Compresión sin pérdida
            _, imb = cv2.imencode(".png", imgs)
            l1 = len(imbyt)  # Tamaño de imagen original
            l2 = len(imb)  # Tamaño de imagen diferencial
            
            if l1 > l2:
                # Transmitir imagen diferencial
                lenb = struct.pack(">BI", 0, l2)
                conn.sendall(lenb)
                conn.sendall(imb)
                debug_print(f"Enviada imagen diferencial: {l2} bytes")
            else:
                # Transmitir imagen original codificada
                lenb = struct.pack(">BI", 1, l1)
                conn.sendall(lenb)
                conn.sendall(imbyt)
                debug_print(f"Enviada imagen completa: {l1} bytes")
                
    except Exception as e:
        debug_print(f"Error en función de manejo de imágenes: {e}")
        if logger:
            logger.error(f"Error en función de manejo de imágenes: {e}")


debug_print("Servidor listo para aceptar conexiones")
while True:
    try:
        conn, addr = soc.accept()
        debug_print(f"Nueva conexión desde: {addr}")
        threading.Thread(target=handle, args=(conn,)).start()
        threading.Thread(target=ctrl, args=(conn,)).start()
        debug_print("Hilos de manejo iniciados para la conexión")
    except Exception as e:
        debug_print(f"Error aceptando conexión: {e}")
        if logger:
            logger.error(f"Error aceptando conexión: {e}")
