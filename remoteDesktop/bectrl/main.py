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
import logging
import sys
import os
import argparse
from datetime import datetime

# ===== CONFIGURACIÓN DE ARGUMENTOS =====
def parse_arguments():
    parser = argparse.ArgumentParser(description='Servidor de Control Remoto - Fase 6')
    parser.add_argument('--debug', '-d', action='store_true', help='Activar modo debug')
    parser.add_argument('--verbose', '-v', action='store_true', help='Activar modo verbose')
    parser.add_argument('--port', '-p', type=int, default=3380, help='Puerto del servidor (default: 3380)')
    return parser.parse_args()

args = parse_arguments()
DEBUG_MODE = args.debug
VERBOSE_MODE = args.verbose
SERVER_PORT = args.port
LOG_LEVEL = logging.DEBUG if DEBUG_MODE else logging.INFO

# ===== FUNCIÓN PARA OBTENER IP LOCAL =====
def get_local_ip():
    """Obtiene la IP local real del sistema, sin importar VPN o Zscaler"""
    try:
        # Crear socket temporal para obtener IP local
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        temp_socket.connect(("8.8.8.8", 80))
        local_ip = temp_socket.getsockname()[0]
        temp_socket.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

# Configurar logging
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_filename = os.path.join(log_dir, f"server_{datetime.now().strftime('%Y%m%d')}.log")

# Configurar handlers según modo debug
handlers = [logging.FileHandler(log_filename, encoding='utf-8')]
if DEBUG_MODE:
    handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=handlers
)
logger = logging.getLogger(__name__)

# ===== CONFIGURACIÓN DEL SISTEMA =====
# Ciclo de pantalla
IDLE = 0.05

# Sensibilidad de rueda del mouse
SCROLL_NUM = 5

bufsize = 1024
local_ip = get_local_ip()
host = (local_ip, SERVER_PORT)
soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
soc.bind(host)
soc.listen(1)

logger.info(f"Servidor iniciado en modo {'DEBUG' if DEBUG_MODE else 'NORMAL'}")
logger.info(f"Host: {local_ip}, Puerto: {SERVER_PORT}")
logger.info(f"Archivo de log: {log_filename}")

# Solo mostrar información en modo debug
if DEBUG_MODE:
    print(f"Servidor de Control Remoto - Fase 6")
    print(f"Host: {local_ip}")
    print(f"Puerto: {SERVER_PORT}")
    print(f"Log: {log_filename}")
    print(f"Esperando conexiones...")
else:
    # Modo silencioso - solo logs
    pass

# Ratio de compresión 1-100, valores menores = mayor compresión, mayor pérdida de calidad
IMQUALITY = 50

lock = threading.Lock()

# ===== ESTADÍSTICAS DE DEBUG =====
stats = {
    'connections': 0,
    'frames_sent': 0,
    'commands_received': 0,
    'bytes_sent': 0,
    'start_time': time.time(),
    'last_frame_time': 0,
    'compression_ratio': 0
}

# if sys.platform == "win32":
#     from ._keyboard_win import keycodeMapping
# elif platform.system() == "Linux":
#     from ._keyboard_x11 import keycodeMapping
# elif sys.platform == "darwin":
#     from ._keyboard_osx import keycodeMapping


def ctrl(conn):
    '''
    Lee comandos de control y restaura operaciones en la máquina local
    '''
    global stats
    client_addr = conn.getpeername()
    logger.info(f"Iniciando control para cliente {client_addr}")
    
    keycodeMapping = {}
    
    def Op(key, op, ox, oy):
        stats['commands_received'] += 1
        
        if DEBUG_MODE:
            logger.debug(f"Comando recibido: key={key}, op={op}, x={ox}, y={oy}")
        
        try:
            if key == 4:
                # Movimiento del mouse
                mouse.move(ox, oy)
                if VERBOSE_MODE:
                    logger.debug(f"Mouse movido a ({ox}, {oy})")
            elif key == 1:
                if op == 100:
                    # Botón izquierdo presionado
                    ag.mouseDown(button=ag.LEFT)
                    logger.debug(f"Botón izquierdo presionado en ({ox}, {oy})")
                elif op == 117:
                    # Botón izquierdo liberado
                    ag.mouseUp(button=ag.LEFT)
                    logger.debug(f"Botón izquierdo liberado en ({ox}, {oy})")
            elif key == 2:
                # Evento de rueda del mouse
                if op == 0:
                    # Hacia arriba
                    ag.scroll(-SCROLL_NUM)
                    logger.debug(f"Scroll hacia arriba en ({ox}, {oy})")
                else:
                    # Hacia abajo
                    ag.scroll(SCROLL_NUM)
                    logger.debug(f"Scroll hacia abajo en ({ox}, {oy})")
            elif key == 3:
                # Botón derecho del mouse
                if op == 100:
                    # Botón derecho presionado
                    ag.mouseDown(button=ag.RIGHT)
                    logger.debug(f"Botón derecho presionado en ({ox}, {oy})")
                elif op == 117:
                    # Botón derecho liberado
                    ag.mouseUp(button=ag.RIGHT)
                    logger.debug(f"Botón derecho liberado en ({ox}, {oy})")
            else:
                k = keycodeMapping.get(key)
                if k is not None:
                    if op == 100:
                        ag.keyDown(k)
                        logger.debug(f"Tecla presionada: {k} (código: {key})")
                    elif op == 117:
                        ag.keyUp(k)
                        logger.debug(f"Tecla liberada: {k} (código: {key})")
                else:
                    logger.warning(f"Código de tecla desconocido: {key}")
        except Exception as e:
            logger.error(f"Error ejecutando comando: {e}")
            if DEBUG_MODE:
                import traceback
                logger.error(traceback.format_exc())
    try:
        plat = b''
        while True:
            plat += conn.recv(3-len(plat))
            if len(plat) == 3:
                break
        print("Plat:", plat.decode())
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
    except:
        return


# Imagen np después de compresión
img = None
# Imagen después de codificación
imbyt = None


def handle(conn):
    global img, imbyt, stats
    client_addr = conn.getpeername()
    logger.info(f"Iniciando transmisión de pantalla para cliente {client_addr}")
    
    frame_count = 0
    differential_frames = 0
    full_frames = 0
    
    lock.acquire()
    try:
        if imbyt is None:
            logger.debug("Capturando primera imagen")
            imorg = np.asarray(ImageGrab.grab())
            _, imbyt = cv2.imencode(
                ".jpg", imorg, [cv2.IMWRITE_JPEG_QUALITY, IMQUALITY])
            imnp = np.asarray(imbyt, np.uint8)
            img = cv2.imdecode(imnp, cv2.IMREAD_COLOR)
            logger.info(f"Primera imagen capturada: {len(imbyt)} bytes, resolución: {img.shape}")
    finally:
        lock.release()
    
    # Enviar primera imagen
    lenb = struct.pack(">BI", 1, len(imbyt))
    conn.sendall(lenb)
    conn.sendall(imbyt)
    stats['frames_sent'] += 1
    stats['bytes_sent'] += len(imbyt) + 5
    full_frames += 1
    
    logger.info(f"Primera imagen enviada: {len(imbyt)} bytes")
    
    while True:
        try:
            # fix for linux
            time.sleep(IDLE)
            frame_start_time = time.time()
            
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
                pass
            else:
                if VERBOSE_MODE:
                    logger.debug("Sin cambios en la imagen, omitiendo frame")
                continue
            
            imbyt = timbyt
            img = imgnew
            
            # Compresión sin pérdida
            _, imb = cv2.imencode(".png", imgs)
            l1 = len(imbyt)  # Tamaño de imagen original
            l2 = len(imb)  # Tamaño de imagen diferencial
            
            frame_count += 1
            stats['frames_sent'] += 1
            
            if l1 > l2:
                # Transmitir imagen diferencial
                lenb = struct.pack(">BI", 0, l2)
                conn.sendall(lenb)
                conn.sendall(imb)
                stats['bytes_sent'] += l2 + 5
                differential_frames += 1
                
                if DEBUG_MODE:
                    logger.debug(f"Frame diferencial #{frame_count}: {l2} bytes (ahorro: {l1-l2} bytes)")
            else:
                # Transmitir imagen codificada original
                lenb = struct.pack(">BI", 1, l1)
                conn.sendall(lenb)
                conn.sendall(imbyt)
                stats['bytes_sent'] += l1 + 5
                full_frames += 1
                
                if DEBUG_MODE:
                    logger.debug(f"Frame completo #{frame_count}: {l1} bytes")
            
            # Actualizar estadísticas
            stats['last_frame_time'] = time.time()
            if l1 > 0:
                stats['compression_ratio'] = (l2 / l1) * 100 if l1 > l2 else 100
            
            # Log periódico de estadísticas
            if frame_count % 100 == 0:
                fps = frame_count / (time.time() - stats['start_time'])
                logger.info(f"Estadísticas - Frames: {frame_count}, FPS: {fps:.1f}, "
                           f"Diferenciales: {differential_frames}, Completos: {full_frames}, "
                           f"Bytes enviados: {stats['bytes_sent']}")
                
        except Exception as e:
            logger.error(f"Error en transmisión de pantalla: {e}")
            if DEBUG_MODE:
                import traceback
                logger.error(traceback.format_exc())
            break


def print_stats():
    """Imprime estadísticas del servidor"""
    uptime = time.time() - stats['start_time']
    fps = stats['frames_sent'] / uptime if uptime > 0 else 0
    mb_sent = stats['bytes_sent'] / (1024 * 1024)
    
    logger.info("=== ESTADÍSTICAS DEL SERVIDOR ===")
    logger.info(f"Tiempo activo: {uptime:.1f}s")
    logger.info(f"Conexiones: {stats['connections']}")
    logger.info(f"Frames enviados: {stats['frames_sent']}")
    logger.info(f"Comandos recibidos: {stats['commands_received']}")
    logger.info(f"FPS promedio: {fps:.1f}")
    logger.info(f"Datos enviados: {mb_sent:.2f} MB")
    logger.info(f"Ratio de compresión: {stats['compression_ratio']:.1f}%")
    logger.info("=================================")

def handle_client(conn, addr):
    """Maneja una conexión de cliente"""
    global stats
    stats['connections'] += 1
    
    logger.info(f"Nueva conexión desde {addr} (Total: {stats['connections']})")
    
    try:
        # Iniciar hilos para manejo de pantalla y control
        screen_thread = threading.Thread(target=handle, args=(conn,), name=f"Screen-{addr[0]}")
        control_thread = threading.Thread(target=ctrl, args=(conn,), name=f"Control-{addr[0]}")
        
        screen_thread.daemon = True
        control_thread.daemon = True
        
        screen_thread.start()
        control_thread.start()
        
        logger.info(f"Hilos iniciados para cliente {addr}")
        
        # Esperar a que terminen los hilos
        screen_thread.join()
        control_thread.join()
        
    except Exception as e:
        logger.error(f"Error manejando cliente {addr}: {e}")
        if DEBUG_MODE:
            import traceback
            logger.error(traceback.format_exc())
    finally:
        try:
            conn.close()
            logger.info(f"Conexión cerrada para cliente {addr}")
        except:
            pass

logger.info("Servidor esperando conexiones...")
logger.info(f"Modo debug: {DEBUG_MODE}, Modo verbose: {VERBOSE_MODE}")

try:
    while True:
        try:
            conn, addr = soc.accept()
            logger.info(f"Conexión aceptada desde {addr}")
            
            # Crear hilo para manejar cliente
            client_thread = threading.Thread(
                target=handle_client, 
                args=(conn, addr),
                name=f"Client-{addr[0]}"
            )
            client_thread.daemon = True
            client_thread.start()
            
        except KeyboardInterrupt:
            logger.info("Interrupción de teclado recibida")
            break
        except Exception as e:
            logger.error(f"Error aceptando conexión: {e}")
            if DEBUG_MODE:
                import traceback
                logger.error(traceback.format_exc())
            time.sleep(1)  # Evitar bucle rápido en caso de error
            
except KeyboardInterrupt:
    logger.info("Cerrando servidor...")
finally:
    print_stats()
    try:
        soc.close()
        logger.info("Socket del servidor cerrado")
    except:
        pass
    logger.info("Servidor terminado")
