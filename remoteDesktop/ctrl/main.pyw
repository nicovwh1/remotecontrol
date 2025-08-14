import tkinter
import tkinter.messagebox
import struct
import socket
import numpy as np
from PIL import Image, ImageTk
import threading
import re
import cv2
import time
import sys
import platform
import logging
import os
import argparse
from datetime import datetime

# ===== CONFIGURACIÓN DE ARGUMENTOS =====
def parse_arguments():
    parser = argparse.ArgumentParser(description='Cliente de Control Remoto - Fase 6')
    parser.add_argument('--debug', '-d', action='store_true', help='Activar modo debug')
    parser.add_argument('--verbose', '-v', action='store_true', help='Activar modo verbose')
    parser.add_argument('--ip', type=str, help='IP del servidor')
    parser.add_argument('--port', '-p', type=int, default=3380, help='Puerto del servidor (default: 3380)')
    parser.add_argument('--scale', '-s', type=float, default=0.97, help='Escala de visualización (default: 0.97)')
    return parser.parse_args()

args = parse_arguments()
DEBUG_MODE = args.debug
VERBOSE_MODE = args.verbose
CLIENT_IP = args.ip
CLIENT_PORT = args.port
CLIENT_SCALE = args.scale
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

# ===== TABLA DE CONVERSIÓN DE KEYCODES - FASE 9 REDEFINIDA =====
# Convierte keycodes de tkinter a keycodes de Windows para sincronización correcta
TKINTER_TO_WINDOWS_KEYCODE = {
    # Números
    49: 0x31,  # '1'
    50: 0x32,  # '2'
    51: 0x33,  # '3'
    52: 0x34,  # '4'
    53: 0x35,  # '5'
    54: 0x36,  # '6'
    55: 0x37,  # '7'
    56: 0x38,  # '8'
    57: 0x39,  # '9'
    48: 0x30,  # '0'
    
    # Letras (tkinter usa mayúsculas, Windows también)
    65: 0x41,  # 'A'
    66: 0x42,  # 'B'
    67: 0x43,  # 'C'
    68: 0x44,  # 'D'
    69: 0x45,  # 'E'
    70: 0x46,  # 'F'
    71: 0x47,  # 'G'
    72: 0x48,  # 'H'
    73: 0x49,  # 'I'
    74: 0x4A,  # 'J'
    75: 0x4B,  # 'K'
    76: 0x4C,  # 'L'
    77: 0x4D,  # 'M'
    78: 0x4E,  # 'N'
    79: 0x4F,  # 'O'
    80: 0x50,  # 'P'
    81: 0x51,  # 'Q'
    82: 0x52,  # 'R'
    83: 0x53,  # 'S'
    84: 0x54,  # 'T'
    85: 0x55,  # 'U'
    86: 0x56,  # 'V'
    87: 0x57,  # 'W'
    88: 0x58,  # 'X'
    89: 0x59,  # 'Y'
    90: 0x5A,  # 'Z'
    
    # Caracteres especiales (usando keycodes base sin Shift)
    44: 0x2C,   # ',' (VK_OEM_COMMA)
    46: 0x2E,   # '.' (VK_OEM_PERIOD)
    59: 0x3B,   # ';' (VK_OEM_1 sin Shift)
    39: 0x27,   # "'" (VK_OEM_7 sin Shift)
    45: 0x2D,   # '-' (VK_OEM_MINUS)
    61: 0x3D,   # '=' (VK_OEM_PLUS sin Shift)
    91: 0x5B,   # '[' (VK_OEM_4 sin Shift)
    93: 0x5D,   # ']' (VK_OEM_6 sin Shift)
    92: 0x5C,   # '\\' (VK_OEM_5 sin Shift)
    47: 0x2F,   # '/' (VK_OEM_2 sin Shift)
    96: 0x60,   # '`' (VK_OEM_3 sin Shift)
    
    # Teclas especiales (ya coinciden, pero las incluimos para completitud)
    8: 0x08,    # Backspace
    9: 0x09,    # Tab
    13: 0x0D,   # Enter
    16: 0x10,   # Shift
    17: 0x11,   # Ctrl
    18: 0x12,   # Alt
    20: 0x14,   # Caps Lock
    27: 0x1B,   # Escape
    32: 0x20,   # Space
    33: 0x21,   # Page Up
    34: 0x22,   # Page Down
    35: 0x23,   # End
    36: 0x24,   # Home
    37: 0x25,   # Left Arrow
    38: 0x26,   # Up Arrow
    39: 0x27,   # Right Arrow
    40: 0x28,   # Down Arrow
    45: 0x2D,   # Insert
    46: 0x2E,   # Delete
}

def convert_tkinter_keycode(tkinter_keycode):
    """Convierte keycode de tkinter a keycode de Windows"""
    return TKINTER_TO_WINDOWS_KEYCODE.get(tkinter_keycode, tkinter_keycode)

# Configurar logging
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_filename = os.path.join(log_dir, f"client_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler(sys.stdout) if DEBUG_MODE else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===== INICIALIZACIÓN DE TKINTER =====
root = tkinter.Tk()
root.title(f"Cliente de Control Remoto - Fase 7 {'[DEBUG]' if DEBUG_MODE else ''}")

logger.info(f"Cliente iniciado en modo {'DEBUG' if DEBUG_MODE else 'NORMAL'}")
logger.info(f"Archivo de log: {log_filename}")
if DEBUG_MODE:
    print(f"Cliente de Control Remoto - Fase 7")
    print(f"Log: {log_filename}")
    print(f"Escala por defecto: {CLIENT_SCALE}")

# ===== CONFIGURACIÓN DEL SISTEMA =====
# Ciclo de pantalla
IDLE = 0.05

# Tamaño de escala
scale = 1

# Dimensiones originales de pantalla transmitida
fixw, fixh = 0, 0

# Bandera de escalado
wscale = False

# Lienzo de visualización de pantalla
showcan = None

# Tamaño de buffer de socket
bufsize = 10240

# Hilo
th = None

# socket
soc = None

# socks5
socks5 = None

# ===== ESTADÍSTICAS DE DEBUG =====
client_stats = {
    'frames_received': 0,
    'commands_sent': 0,
    'bytes_received': 0,
    'connection_time': 0,
    'last_frame_time': 0,
    'differential_frames': 0,
    'full_frames': 0
}

def print_client_stats():
    """Imprime estadísticas del cliente"""
    if client_stats['connection_time'] > 0:
        uptime = time.time() - client_stats['connection_time']
        fps = client_stats['frames_received'] / uptime if uptime > 0 else 0
        mbps = (client_stats['bytes_received'] * 8) / (1024 * 1024 * uptime) if uptime > 0 else 0
        
        logger.info("=== ESTADÍSTICAS DEL CLIENTE ===")
        logger.info(f"Tiempo conectado: {uptime:.1f}s")
        logger.info(f"Frames recibidos: {client_stats['frames_received']}")
        logger.info(f"  - Completos: {client_stats['full_frames']}")
        logger.info(f"  - Diferenciales: {client_stats['differential_frames']}")
        logger.info(f"Comandos enviados: {client_stats['commands_sent']}")
        logger.info(f"Datos recibidos: {client_stats['bytes_received'] / (1024*1024):.2f} MB")
        logger.info(f"FPS promedio: {fps:.2f}")
        logger.info(f"Velocidad: {mbps:.2f} Mbps")
        logger.info("=================================")


filename="D:\\shared\\nico\\Desktop\\Netcool\\script\\ipwork.txt"

# Plataforma
PLAT = b''
if sys.platform == "win32":
    PLAT = b'win'
elif sys.platform == "darwin":
    PLAT = b'osx'
elif platform.system() == "Linux":
    PLAT = b'x11'

# Inicializar socket


def SetSocket():
    global soc, host_en, client_stats, target_host
    
    logger.info("Iniciando configuración de socket")

    def byipv4(ip, port):
        return struct.pack(">BBBBBBBBH", 5, 1, 0, 1, ip[0], ip[1], ip[2], ip[3], port)

    def byhost(host, port):
        d = struct.pack(">BBBB", 5, 1, 0, 3)
        blen = len(host)
        d += struct.pack(">B", blen)
        d += host.encode()
        d += struct.pack(">H", port)
        return d
    
    # Obtener host desde CLI o GUI
    if CLIENT_IP:
        host = target_host
    else:
        if host_en is None:
            logger.error("Host no configurado")
            return False
        host = host_en.get()
        if host is None:
            logger.error("Host no configurado")
            if not DEBUG_MODE:  # Solo mostrar messagebox en modo debug
                tkinter.messagebox.showinfo('Error', 'Host设置错误！')
            return False
        
    hs = host.split(":")
    if len(hs) != 2:
        logger.error(f"Formato de host inválido: {host}")
        if not DEBUG_MODE and not CLIENT_IP:  # Solo mostrar messagebox en modo GUI debug
            tkinter.messagebox.showinfo('Error', 'Host设置错误！')
        return False
        
    logger.info(f"Conectando a {host}")
    
    try:
        if socks5 is not None:
            logger.info(f"Usando proxy SOCKS5: {socks5}")
            ss = socks5.split(":")
            if len(ss) != 2:
                logger.error(f"Formato de proxy inválido: {socks5}")
                tkinter.messagebox.showinfo('Error', '代理设置错误！')
                return
                
            soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            logger.debug(f"Conectando a proxy {ss[0]}:{ss[1]}")
            soc.connect((ss[0], int(ss[1])))
            
            soc.sendall(struct.pack(">BB", 5, 0))
            recv = soc.recv(2)
            if recv[1] != 0:
                logger.error(f"Error en respuesta del proxy: {recv[1]}")
                tkinter.messagebox.showinfo('Error', '代理回应错误！')
                return
                
            if re.match(r'^\d+?\.\d+?\.\d+?\.\d+?:\d+$', host) is None:
                # host 域名访问
                logger.debug(f"Conectando por dominio: {hs[0]}:{hs[1]}")
                hand = byhost(hs[0], int(hs[1]))
                soc.sendall(hand)
            else:
                # host ip访问
                logger.debug(f"Conectando por IP: {hs[0]}:{hs[1]}")
                ip = [int(i) for i in hs[0].split(".")]
                port = int(hs[1])
                hand = byipv4(ip, port)
                soc.sendall(hand)
            # Respuesta del proxy
            rcv = b''
            while len(rcv) != 10:
                rcv += soc.recv(10-len(rcv))
            if rcv[1] != 0:
                logger.error(f"Error en respuesta del proxy (segunda fase): {rcv[1]}")
                tkinter.messagebox.showinfo('Error', '代理回应错误！')
                return
            logger.info("Conexión SOCKS5 establecida exitosamente")
        else:
            logger.info("Conexión directa (sin proxy)")
            soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            soc.connect((hs[0], int(hs[1])))
            
        client_stats['connection_time'] = time.time()
        logger.info(f"Socket configurado exitosamente para {host}")
        return True
        
    except Exception as e:
        logger.error(f"Error al configurar socket: {str(e)}")
        if DEBUG_MODE:
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
        tkinter.messagebox.showinfo('Error', f'Error de conexión: {str(e)}')
        return False


def SetScale(x):
    global scale, wscale
    scale = float(x) / 100
    wscale = True


def ShowProxy():
    # Mostrar configuración de proxy
    global root

    def set_s5_addr():
        global socks5
        socks5 = s5_en.get()
        if socks5 == "":
            socks5 = None
        pr.destroy()
    pr = tkinter.Toplevel(root)
    s5v = tkinter.StringVar()
    s5_lab = tkinter.Label(pr, text="Socks5 Host:")
    s5_en = tkinter.Entry(pr, show=None, font=('Arial', 14), textvariable=s5v)
    s5_btn = tkinter.Button(pr, text="OK", command=set_s5_addr)
    s5_lab.grid(row=0, column=0, padx=10, pady=10, ipadx=0, ipady=0)
    s5_en.grid(row=0, column=1, padx=10, pady=10, ipadx=40, ipady=0)
    s5_btn.grid(row=1, column=0, padx=10, pady=10, ipadx=30, ipady=0)
    s5v.set("127.0.0.1:88")


def ShowScreen():
    global showcan, root, soc, th, wscale
    if showcan is None:
        wscale = True
        showcan = tkinter.Toplevel(root)
        th = threading.Thread(target=run)
        th.start()
    else:
        soc.close()
        showcan.destroy()


# Fase 7: Siempre crear GUI
if root is not None:
    val = tkinter.StringVar()
    host_lab = tkinter.Label(root, text="Host:")
    host_en = tkinter.Entry(root, show=None, font=('Arial', 16), textvariable=val)
    sca_lab = tkinter.Label(root, text="Scale:")
    sca = tkinter.Scale(root, from_=10, to=150, orient=tkinter.HORIZONTAL, length=100,
                        showvalue=100, resolution=0.2, tickinterval=50, command=SetScale)
    proxy_btn = tkinter.Button(root, text="Proxy", command=ShowProxy)
    show_btn = tkinter.Button(root, text="Show", command=ShowScreen)

    host_lab.grid(row=0, column=0, padx=10, pady=10, ipadx=0, ipady=0)
    host_en.grid(row=0, column=1, padx=0, pady=0, ipadx=40, ipady=0)
    sca_lab.grid(row=1, column=0, padx=10, pady=10, ipadx=0, ipady=0)
    sca.grid(row=1, column=1, padx=0, pady=0, ipadx=100, ipady=0)
    proxy_btn.grid(row=2, column=0, padx=0, pady=10, ipadx=30, ipady=0)
    show_btn.grid(row=2, column=1, padx=0, pady=10, ipadx=30, ipady=0)
    # Configurar escala desde parámetros CLI
    sca.set(int(CLIENT_SCALE * 100))
    
    # Fase 7: Autocompletar campos de la GUI
    if CLIENT_IP:
        # Usar parámetros CLI para autocompletar
        target_host = f"{CLIENT_IP}:{CLIENT_PORT}"
        val.set(target_host)
        logger.info(f"GUI autocompletada con parámetros CLI: {target_host}")
        if DEBUG_MODE:
            print(f"Campos autocompletados: IP={CLIENT_IP}, Puerto={CLIENT_PORT}, Escala={CLIENT_SCALE}")
    else:
        # Leer archivo de configuración o usar IP local para autocompletar
        try:
            textfile = open(filename, 'r')
            matches = []
            reg = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
            strip = ""
            if textfile.read() == '':
                strip = get_local_ip()  # Usar IP local automática
                if DEBUG_MODE:
                    print("No data found, using local IP")
            else:
                textfile.seek(0)
                if DEBUG_MODE:
                    print("Data present in file")
                for line in textfile:
                    matches += reg.findall(line)
                    if DEBUG_MODE:
                        print("line:", line, "|len:", len(matches))
                textfile.close()
                if matches:
                    strip = matches[0]
                    if DEBUG_MODE:
                        print("matches:", len(matches), matches[0])
                else:
                    strip = get_local_ip()  # Fallback a IP local
            
            target_host = f"{strip}:{CLIENT_PORT}"
            val.set(target_host)
        except Exception as e:
            logger.warning(f"Error leyendo archivo de configuración: {e}")
            strip = get_local_ip()
            target_host = f"{strip}:{CLIENT_PORT}"
            val.set(target_host)
else:
    # Fallback si no hay GUI (no debería ocurrir en Fase 7)
    target_host = f"{CLIENT_IP or get_local_ip()}:{CLIENT_PORT}"

# Configurar escala inicial
scale = CLIENT_SCALE
last_send = time.time()





def BindEvents(canvas):
    global soc, scale, client_stats
    '''
    Procesar eventos
    '''
    logger.debug("Configurando eventos de mouse y teclado")
    
    def EventDo(data):
        soc.sendall(data)
        client_stats['commands_sent'] += 1
    # Botón izquierdo del mouse

    def LeftDown(e):
        if VERBOSE_MODE:
            logger.debug(f"Mouse izquierdo presionado en ({int(e.x/scale)}, {int(e.y/scale)})")
        return EventDo(struct.pack('>BBHH', 1, 100, int(e.x/scale), int(e.y/scale)))

    def LeftUp(e):
        if VERBOSE_MODE:
            logger.debug(f"Mouse izquierdo liberado en ({int(e.x/scale)}, {int(e.y/scale)})")
        return EventDo(struct.pack('>BBHH', 1, 117, int(e.x/scale), int(e.y/scale)))
    canvas.bind(sequence="<1>", func=LeftDown)
    canvas.bind(sequence="<ButtonRelease-1>", func=LeftUp)

    # Botón derecho del mouse
    def RightDown(e):
        if VERBOSE_MODE:
            logger.debug(f"Mouse derecho presionado en ({int(e.x/scale)}, {int(e.y/scale)})")
        return EventDo(struct.pack('>BBHH', 3, 100, int(e.x/scale), int(e.y/scale)))

    def RightUp(e):
        if VERBOSE_MODE:
            logger.debug(f"Mouse derecho liberado en ({int(e.x/scale)}, {int(e.y/scale)})")
        return EventDo(struct.pack('>BBHH', 3, 117, int(e.x/scale), int(e.y/scale)))
    canvas.bind(sequence="<3>", func=RightDown)
    canvas.bind(sequence="<ButtonRelease-3>", func=RightUp)

    # Rueda del mouse
    if PLAT == b'win' or PLAT == 'osx':
        # windows/mac
        def Wheel(e):
            if VERBOSE_MODE:
                logger.debug(f"Rueda del mouse en ({int(e.x/scale)}, {int(e.y/scale)}), delta: {e.delta}")
            if e.delta < 0:
                return EventDo(struct.pack('>BBHH', 2, 0, int(e.x/scale), int(e.y/scale)))
            else:
                return EventDo(struct.pack('>BBHH', 2, 1, int(e.x/scale), int(e.y/scale)))
        canvas.bind(sequence="<MouseWheel>", func=Wheel)
    elif PLAT == b'x11':
        def WheelDown(e):
            if VERBOSE_MODE:
                logger.debug(f"Rueda del mouse hacia abajo en ({int(e.x/scale)}, {int(e.y/scale)})")
            return EventDo(struct.pack('>BBHH', 2, 0, int(e.x/scale), int(e.y/scale)))
        def WheelUp(e):
            if VERBOSE_MODE:
                logger.debug(f"Rueda del mouse hacia arriba en ({int(e.x/scale)}, {int(e.y/scale)})")
            return EventDo(struct.pack('>BBHH', 2, 1, int(e.x/scale), int(e.y/scale)))
        canvas.bind(sequence="<Button-4>", func=WheelUp)
        canvas.bind(sequence="<Button-5>", func=WheelDown)

    # Deslizamiento del mouse
    # Enviar una vez cada 100ms
    def Move(e):
        global last_send
        cu = time.time()
        if cu - last_send > IDLE:
            last_send = cu
            sx, sy = int(e.x/scale), int(e.y/scale)
            if VERBOSE_MODE:
                logger.debug(f"Movimiento del mouse a ({sx}, {sy})")
            return EventDo(struct.pack('>BBHH', 4, 0, sx, sy))
    canvas.bind(sequence="<Motion>", func=Move)

    # Teclado - FASE 9 REDEFINIDA: Conversión de keycodes
    def KeyDown(e):
        # Convertir keycode de tkinter a keycode de Windows
        windows_keycode = convert_tkinter_keycode(e.keycode)
        if VERBOSE_MODE:
            logger.debug(f"Tecla presionada: tkinter={e.keycode} -> windows={windows_keycode}")
        return EventDo(struct.pack('>BBHH', windows_keycode, 100, int(e.x/scale), int(e.y/scale)))

    def KeyUp(e):
        # Convertir keycode de tkinter a keycode de Windows
        windows_keycode = convert_tkinter_keycode(e.keycode)
        if VERBOSE_MODE:
            logger.debug(f"Tecla liberada: tkinter={e.keycode} -> windows={windows_keycode}")
        return EventDo(struct.pack('>BBHH', windows_keycode, 117, int(e.x/scale), int(e.y/scale)))
    canvas.bind(sequence="<KeyPress>", func=KeyDown)
    canvas.bind(sequence="<KeyRelease>", func=KeyUp)


def run():
    global wscale, fixh, fixw, soc, showcan, client_stats
    
    logger.info("Iniciando función de ejecución principal")
    
    if not SetSocket():
        logger.error("No se pudo establecer la conexión")
        return
        
    try:
        logger.info(f"Enviando información de plataforma: {PLAT}")
        soc.sendall(PLAT)
        
        # Recibir primer frame
        logger.debug("Recibiendo primer frame")
        lenb = soc.recv(5)
        imtype, le = struct.unpack(">BI", lenb)
        
        logger.debug(f"Tamaño del primer frame: {le} bytes, tipo: {imtype}")
        
        imb = b''
        while le > bufsize:
            t = soc.recv(bufsize)
            imb += t
            le -= len(t)
        while le > 0:
            t = soc.recv(le)
            imb += t
            le -= len(t)
            
        client_stats['bytes_received'] += len(imb)
        client_stats['frames_received'] += 1
        client_stats['full_frames'] += 1
        client_stats['last_frame_time'] = time.time()
        
        data = np.frombuffer(imb, dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        h, w, _ = img.shape
        fixh, fixw = h, w
        
        logger.info(f"Primer frame recibido: {w}x{h}, escala: {scale}")
        
        imsh = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA)
        imi = Image.fromarray(imsh)
        imgTK = ImageTk.PhotoImage(image=imi)
        cv = tkinter.Canvas(showcan, width=w, height=h, bg="white")
        cv.focus_set()
        BindEvents(cv)
        cv.pack()
        cv.create_image(0, 0, anchor=tkinter.NW, image=imgTK)
        h = int(h * scale)
        w = int(w * scale)
        
        frame_count = 1
        last_stats_time = time.time()
        
        while True:
            if wscale:
                h = int(fixh * scale)
                w = int(fixw * scale)
                cv.config(width=w, height=h)
                wscale = False
            try:
                lenb = soc.recv(5)
                imtype, le = struct.unpack(">BI", lenb)
                
                imb = b''
                while le > bufsize:
                    t = soc.recv(bufsize)
                    imb += t
                    le -= len(t)
                while le > 0:
                    t = soc.recv(le)
                    imb += t
                    le -= len(t)
                    
                client_stats['bytes_received'] += len(imb)
                client_stats['frames_received'] += 1
                client_stats['last_frame_time'] = time.time()
                
                data = np.frombuffer(imb, dtype=np.uint8)
                ims = cv2.imdecode(data, cv2.IMREAD_COLOR)
                
                if imtype == 1:
                    # Transmisión completa
                    client_stats['full_frames'] += 1
                    img = ims
                    if VERBOSE_MODE:
                        logger.debug(f"Frame completo recibido: {le} bytes")
                else:
                    # Transmisión diferencial
                    client_stats['differential_frames'] += 1
                    img = img ^ ims
                    if VERBOSE_MODE:
                        logger.debug("Frame diferencial recibido")
                        
                imt = cv2.resize(img, (w, h))
                imsh = cv2.cvtColor(imt, cv2.COLOR_RGB2RGBA)
                imi = Image.fromarray(imsh)
                imgTK.paste(imi)
                
                frame_count += 1
                
                # Mostrar estadísticas cada 30 segundos en modo debug
                if DEBUG_MODE and time.time() - last_stats_time > 30:
                    logger.info(f"Estadísticas - Frames: {client_stats['frames_received']}, Bytes: {client_stats['bytes_received']}, Comandos: {client_stats['commands_sent']}")
                    last_stats_time = time.time()
                    
            except Exception as e:
                logger.error(f"Error en bucle principal: {str(e)}")
                if DEBUG_MODE:
                    import traceback
                    logger.debug(f"Traceback: {traceback.format_exc()}")
                showcan = None
                ShowScreen()
                return
                
    except Exception as e:
        logger.error(f"Error en función run: {str(e)}")
        if DEBUG_MODE:
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
    finally:
        if soc:
            soc.close()
            logger.info("Conexión cerrada")


if __name__ == '__main__':
    # Mostrar información de argumentos de línea de comandos
    if DEBUG_MODE or VERBOSE_MODE:
        logger.info(f"Argumentos: {sys.argv}")
        logger.info(f"Modo DEBUG: {DEBUG_MODE}")
        logger.info(f"Modo VERBOSE: {VERBOSE_MODE}")
        logger.info(f"IP Cliente: {CLIENT_IP}")
        logger.info(f"Puerto: {CLIENT_PORT}")
        logger.info(f"Escala: {CLIENT_SCALE}")
    
    # Fase 7: Siempre mostrar GUI, usar parámetros CLI para autocompletar
    if CLIENT_IP:
        logger.info(f"Parámetros CLI detectados - Autocompletando GUI: {CLIENT_IP}:{CLIENT_PORT}")
        if DEBUG_MODE:
            print(f"Autocompletando GUI con: IP={CLIENT_IP}, Puerto={CLIENT_PORT}, Escala={CLIENT_SCALE}")
    
    # Siempre iniciar interfaz gráfica
    if DEBUG_MODE:
        print("Iniciando interfaz gráfica")
        # Botón de estadísticas en modo debug
        if root is not None:
            stats_btn = tkinter.Button(root, text="Estadísticas", command=print_client_stats)
            stats_btn.grid(row=3, column=0, padx=0, pady=10, ipadx=30, ipady=0)
            log_label = tkinter.Label(root, text=f"Log: {log_filename}", font=("Arial", 8))
            log_label.grid(row=3, column=1, padx=0, pady=10)
    
    logger.info("Interfaz gráfica inicializada")
    if root is not None:
        root.mainloop()
