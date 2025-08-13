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
# Importación de tkinter removida - servidor sin interfaz gráfica
import subprocess
import platform
import argparse
import logging
from logging.handlers import TimedRotatingFileHandler
import os

# Configuración de argumentos de línea de comandos
parser = argparse.ArgumentParser(description='Servidor de Control Remoto')
parser.add_argument('--debug', action='store_true', help='Activar modo debug con logging detallado')
args = parser.parse_args()

# Configuración del sistema de logging
def setup_logging(debug_mode=False):
    """Configura el sistema de logging con rotación diaria"""
    # Crear directorio de logs si no existe
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configurar el nivel de logging
    log_level = logging.DEBUG if debug_mode else logging.INFO
    
    # Crear el handler con rotación diaria
    log_file = os.path.join(log_dir, 'remote_server.log')
    handler = TimedRotatingFileHandler(
        log_file,
        when='midnight',
        interval=1,
        backupCount=30,  # Mantener 30 días de logs
        encoding='utf-8'
    )
    
    # Formato del log
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    # Configurar el logger principal
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(handler)
    
    # También mostrar en consola si está en modo debug
    if debug_mode:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

# Inicializar logging
logger = setup_logging(args.debug)
logger.info(f"Servidor iniciado en modo {'DEBUG' if args.debug else 'NORMAL'}")

# Ciclo de pantalla
IDLE = 0.05
logger.debug(f"Configurado IDLE: {IDLE}")

# Sensibilidad de la rueda del ratón
SCROLL_NUM = 5
logger.debug(f"Configurado SCROLL_NUM: {SCROLL_NUM}")

def get_local_ip():
    """
    Detecta la IP local real del equipo, incluso con VPN activa como Cisco o Zscaler
    """
    logger.debug("Iniciando detección de IP local")
    
    try:
        # Método 1: Conectar a un servidor externo para obtener la IP local usada
        logger.debug("Intentando método 1: conexión a servidor externo")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            logger.info(f"IP detectada por método 1: {local_ip}")
            return local_ip
    except Exception as e:
        logger.debug(f"Método 1 falló: {e}")
        try:
            # Método 2: Usar hostname si el método anterior falla
            logger.debug("Intentando método 2: hostname")
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            if local_ip.startswith("127."):
                # Si obtenemos localhost, intentar otro método
                logger.debug(f"IP localhost detectada ({local_ip}), intentando otro método")
                raise Exception("Localhost detected")
            logger.info(f"IP detectada por método 2: {local_ip}")
            return local_ip
        except Exception as e:
            logger.debug(f"Método 2 falló: {e}")
            try:
                # Método 3: Usar comando del sistema según la plataforma
                logger.debug(f"Intentando método 3: comando del sistema ({platform.system()})")
                if platform.system() == "Windows":
                    result = subprocess.run(['ipconfig'], capture_output=True, text=True)
                    lines = result.stdout.split('\n')
                    for i, line in enumerate(lines):
                        if 'IPv4' in line and 'Address' in line:
                            ip = line.split(':')[-1].strip()
                            if not ip.startswith('127.') and not ip.startswith('169.254.'):
                                logger.info(f"IP detectada por método 3 (Windows): {ip}")
                                return ip
                else:
                    # Para Linux/Mac
                    result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
                    ips = result.stdout.strip().split()
                    for ip in ips:
                        if not ip.startswith('127.') and not ip.startswith('169.254.'):
                            logger.info(f"IP detectada por método 3 (Linux/Mac): {ip}")
                            return ip
            except Exception as e:
                logger.debug(f"Método 3 falló: {e}")
                pass
            
            # Método 4: Fallback a IP por defecto
            fallback_ip = "192.168.1.14"
            logger.warning(f"Todos los métodos fallaron, usando IP por defecto: {fallback_ip}")
            return fallback_ip

bufsize = 1024
logger.debug(f"Configurado bufsize: {bufsize}")

port = 3380  # Puerto fijo como solicitado
logger.debug(f"Puerto configurado: {port}")

local_ip = get_local_ip()
host = (local_ip, port)
logger.info(f"Configurando servidor en {host}")

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
soc.bind(host)
soc.listen(1)
logger.info(f"Servidor escuchando en {local_ip}:{port}")

logger.info(f"Servidor configurado - Host: {local_ip}, Puerto: {port}")

# Relación de compresión 1-100, cuanto menor sea el valor, mayor será la compresión y mayor la pérdida de calidad de imagen
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
    Lee comandos de control y restaura las operaciones en la máquina local
    '''
    logger.info(f"Iniciando función de control para conexión {conn.getpeername()}")
    keycodeMapping = {}
    def Op(key, op, ox, oy):
        logger.debug(f"Comando recibido - key: {key}, op: {op}, ox: {ox}, oy: {oy}")
        if key == 4:
            # Movimiento del ratón
            logger.debug(f"Movimiento del ratón a ({ox}, {oy})")
            mouse.move(ox, oy)
        elif key == 1:
            if op == 100:
                # Botón izquierdo presionado
                logger.debug(f"Botón izquierdo presionado")
                ag.mouseDown(button=ag.LEFT)
            elif op == 117:
                # Botón izquierdo liberado
                logger.debug(f"Botón izquierdo liberado")
                ag.mouseUp(button=ag.LEFT)
        elif key == 2:
            # Evento de rueda del ratón
            if op == 0:
                # Hacia arriba
                logger.debug(f"Scroll hacia arriba")
                ag.scroll(-SCROLL_NUM)
            else:
                # Hacia abajo
                logger.debug(f"Scroll hacia abajo")
                ag.scroll(SCROLL_NUM)
        elif key == 3:
            # Botón derecho del ratón
            if op == 100:
                # Botón derecho presionado
                logger.debug(f"Botón derecho presionado")
                ag.mouseDown(button=ag.RIGHT)
            elif op == 117:
                # Botón derecho liberado
                logger.debug(f"Botón derecho liberado")
                ag.mouseUp(button=ag.RIGHT)
        else:
            k = keycodeMapping.get(key)
            if k is not None:
                if op == 100:
                    logger.debug(f"Tecla presionada: {k} (código: {key})")
                    ag.keyDown(k)
                elif op == 117:
                    logger.debug(f"Tecla liberada: {k} (código: {key})")
                    ag.keyUp(k)
            else:
                logger.warning(f"Código de tecla no reconocido: {key}")
    try:
        plat = b''
        while True:
            plat += conn.recv(3-len(plat))
            if len(plat) == 3:
                break
        logger.info(f"Plataforma del cliente: {plat.decode()}")
        keycodeMapping = getKeycodeMapping(plat)
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
        logger.error(f"Error en función de control: {e}")
        return
    
    logger.info(f"Función de control terminada para conexión {conn.getpeername()}")


# Imagen np después de compresión
img = None
# Imagen después de codificación
imbyt = None


def handle(conn):
    global img, imbyt
    logger.info(f"Iniciando función de manejo de pantalla para conexión {conn.getpeername()}")
    
    try:
        lock.acquire()
        if imbyt is None:
            logger.debug("Capturando primera imagen de pantalla")
            imorg = np.asarray(ImageGrab.grab())
            _, imbyt = cv2.imencode(
                ".jpg", imorg, [cv2.IMWRITE_JPEG_QUALITY, IMQUALITY])
            imnp = np.asarray(imbyt, np.uint8)
            img = cv2.imdecode(imnp, cv2.IMREAD_COLOR)
            logger.debug(f"Primera imagen capturada, tamaño: {len(imbyt)} bytes")
        lock.release()
        
        lenb = struct.pack(">BI", 1, len(imbyt))
        conn.sendall(lenb)
        conn.sendall(imbyt)
        logger.debug(f"Imagen inicial enviada al cliente")
        
        frame_count = 0
        while True:
            # corrección para linux
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
                # Calidad de imagen cambiada
                frame_count += 1
                if frame_count % 100 == 0:  # Log cada 100 frames para no saturar
                    logger.debug(f"Frame {frame_count}: cambios detectados en pantalla")
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
                if frame_count % 100 == 0:
                    logger.debug(f"Enviando imagen diferencial: {l2} bytes")
            else:
                # Transmitir imagen codificada original
                lenb = struct.pack(">BI", 1, l1)
                conn.sendall(lenb)
                conn.sendall(imbyt)
                if frame_count % 100 == 0:
                    logger.debug(f"Enviando imagen completa: {l1} bytes")
                    
    except Exception as e:
        logger.error(f"Error en función de manejo de pantalla: {e}")
    finally:
        logger.info(f"Función de manejo de pantalla terminada para conexión {conn.getpeername()}")


logger.info("Servidor listo para aceptar conexiones")
while True:
    try:
        conn, addr = soc.accept()
        logger.info(f"Nueva conexión aceptada desde {addr}")
        
        # Iniciar hilos para manejo de pantalla y control
        handle_thread = threading.Thread(target=handle, args=(conn,))
        ctrl_thread = threading.Thread(target=ctrl, args=(conn,))
        
        handle_thread.daemon = True
        ctrl_thread.daemon = True
        
        handle_thread.start()
        ctrl_thread.start()
        
        logger.info(f"Hilos iniciados para conexión {addr}")
        
    except Exception as e:
        logger.error(f"Error aceptando conexión: {e}")
        break

logger.info("Servidor detenido")
