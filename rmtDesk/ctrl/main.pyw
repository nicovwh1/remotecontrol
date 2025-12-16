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
import os
import subprocess
import argparse
import logging

# Constantes ya definidas arriba

# Variables globales para configuración
DEBUG_MODE = False
LOG_ENABLED = True
logger = None

def parse_arguments():
    """Analiza los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Cliente de escritorio remoto')
    parser.add_argument('--ip', '-i', type=str, default=None,
                       help='IP del servidor')
    parser.add_argument('--port', '-p', type=int, default=DEFAULT_PORT,
                       help=f'Puerto del servidor (por defecto: {DEFAULT_PORT})')
    parser.add_argument('--scale', '-s', type=float, default=None,
                       help='Escala de visualización (por defecto: 97)')
    parser.add_argument('--debug', '-d', action='store_true',
                       help='Activar modo debug')
    return parser.parse_args()

def setup_logging():
    """Configura el sistema de logging"""
    global logger
    
    # Obtener directorio un nivel arriba del script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    log_file = os.path.join(parent_dir, 'rmtDesk_client.log')
    
    # Configurar logger
    logger = logging.getLogger('rmtDesk_client')
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

root = tkinter.Tk()

# Ciclo de pantalla
IDLE = 0.05

# Tamaño de escalado
scale = 1

# Dimensiones originales de transmisión
fixw, fixh = 0, 0

# Bandera de escalado
wscale = False

# Lienzo de visualización
showcan = None

# Tamaño del buffer del socket
bufsize = 10240

# Hilo de ejecución
th = None

# socket
soc = None

# socks5

socks5 = None


# Configuración de IP automática
IP_FILE_PATH = ""
FALLBACK_HOSTNAME = ""
DEFAULT_IP = "192.168.1.1"
DEFAULT_PORT = 3380

# Plataforma
PLAT = b''
if sys.platform == "win32":
    PLAT = b'win'
elif sys.platform == "darwin":
    PLAT = b'osx'
elif platform.system() == "Linux":
    PLAT = b'x11'

# Analizar argumentos de línea de comandos
args = parse_arguments()
DEBUG_MODE = args.debug
CONFIG_IP = args.ip
CONFIG_PORT = args.port
CONFIG_SCALE = args.scale

# Configurar logging
log_file = setup_logging()

# Inicializar socket


def SetSocket():
    global soc, host_en

    def byipv4(ip, port):
        return struct.pack(">BBBBBBBBH", 5, 1, 0, 1, ip[0], ip[1], ip[2], ip[3], port)

    def byhost(host, port):
        d = struct.pack(">BBBB", 5, 1, 0, 3)
        blen = len(host)
        d += struct.pack(">B", blen)
        d += host.encode()
        d += struct.pack(">H", port)
        return d
    host = host_en.get()
    if host is None:
        if DEBUG_MODE:
            tkinter.messagebox.showinfo('Aviso', 'Error en configuración de Host!')
        debug_print('Error en configuración de Host!')
        return
    hs = host.split(":")
    if len(hs) != 2:
        tkinter.messagebox.showinfo('Aviso', 'Error en configuración de Host!')
        return
    if socks5 is not None:
        ss = socks5.split(":")
        if len(ss) != 2:
            if DEBUG_MODE:
                tkinter.messagebox.showinfo('Aviso', 'Error en configuración de proxy!')
            debug_print('Error en configuración de proxy!')
            return
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soc.connect((ss[0], int(ss[1])))
        soc.sendall(struct.pack(">BB", 5, 0))
        recv = soc.recv(2)
        if recv[1] != 0:
            if DEBUG_MODE:
                tkinter.messagebox.showinfo('Aviso', 'Error en respuesta del proxy!')
            debug_print('Error en respuesta del proxy!')
            return
        if re.match(r'^\d+?\.\d+?\.\d+?\.\d+?:\d+$', host) is None:
            # Acceso por nombre de dominio
            hand = byhost(hs[0], int(hs[1]))
            soc.sendall(hand)
        else:
            # Acceso por dirección IP
            ip = [int(i) for i in hs[0].split(".")]
            port = int(hs[1])
            hand = byipv4(ip, port)
            soc.sendall(hand)
        # Respuesta del proxy
        rcv = b''
        while len(rcv) != 10:
            rcv += soc.recv(10-len(rcv))
        if rcv[1] != 0:
            if DEBUG_MODE:
                tkinter.messagebox.showinfo('Aviso', 'Error en respuesta del proxy!')
            debug_print('Error en respuesta del proxy!')
            return
    else:
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soc.connect((hs[0], int(hs[1])))


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
sca.set(CONFIG_SCALE if CONFIG_SCALE else 97)

# Funciones de configuración automática de IP
def validar_ip(ip_string):
    """Valida si una cadena es una dirección IP válida"""
    try:
        parts = ip_string.split('.')
        if len(parts) != 4:
            return False
        for part in parts:
            if not part.isdigit() or not 0 <= int(part) <= 255:
                return False
        return True
    except:
        return False

def leer_ip_desde_archivo(ruta_archivo):
    """Lee la IP desde el archivo especificado"""
    try:
        if os.path.exists(ruta_archivo):
            with open(ruta_archivo, 'r') as file:
                content = file.read().strip()
                if content:
                    # Buscar IP en el contenido del archivo
                    reg = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
                    matches = reg.findall(content)
                    if matches:
                        return matches[0]
        return None
    except Exception as e:
        debug_print(f"Error leyendo archivo IP: {e}")
        return None

def ping_y_obtener_ip(hostname):
    """Hace ping al hostname y obtiene su IP"""
    try:
        # Resolver hostname a IP
        ip = socket.gethostbyname(hostname)
        return ip
    except Exception as e:
        debug_print(f"Error resolviendo hostname {hostname}: {e}")
        return None

def obtener_ip_configurada():
    """Lógica principal de configuración de IP con fallbacks"""
    debug_print("Iniciando configuración automática de IP...")
    
    # Prioridad 1: IP desde argumentos de línea de comandos
    if CONFIG_IP:
        if validar_ip(CONFIG_IP):
            debug_print(f"IP obtenida desde argumentos: {CONFIG_IP}")
            return CONFIG_IP
        else:
            debug_print(f"IP inválida en argumentos: {CONFIG_IP}")
    
    # Prioridad 2: Leer IP desde archivo
    ip_archivo = leer_ip_desde_archivo(IP_FILE_PATH)
    if ip_archivo and validar_ip(ip_archivo):
        debug_print(f"IP leída desde archivo: {ip_archivo}")
        return ip_archivo
    elif ip_archivo:
        debug_print(f"IP del archivo no válida: {ip_archivo}")
    else:
        debug_print("No se pudo leer IP desde archivo")
    
    # Prioridad 3: Ping a hostname de fallback
    ip_ping = ping_y_obtener_ip(FALLBACK_HOSTNAME)
    if ip_ping and validar_ip(ip_ping):
        debug_print(f"IP obtenida por ping a {FALLBACK_HOSTNAME}: {ip_ping}")
        return ip_ping
    else:
        debug_print(f"No se pudo obtener IP por ping a {FALLBACK_HOSTNAME}")
    
    # Prioridad 4: IP por defecto
    debug_print(f"Usando IP por defecto: {DEFAULT_IP}")
    return DEFAULT_IP

# Configuración automática de IP
ip_configurada = obtener_ip_configurada()
puerto_configurado = CONFIG_PORT

# Usar la IP configurada automáticamente con el puerto por defecto
val.set(f"{ip_configurada}:{puerto_configurado}")
debug_print(f"Configuración final: {ip_configurada}:{puerto_configurado}")

# Mantener compatibilidad con código original (por si se necesita)
try:
    textfile = open(IP_FILE_PATH, 'r')
    textfile.close()
except:
    pass  # No es crítico si falla
last_send = time.time()





def BindEvents(canvas):
    global soc, scale
    '''
    Procesar eventos
    '''
    def EventDo(data):
        soc.sendall(data)
    # Botón izquierdo del mouse

    def LeftDown(e):
        return EventDo(struct.pack('>BBHH', 1, 100, int(e.x/scale), int(e.y/scale)))

    def LeftUp(e):
        return EventDo(struct.pack('>BBHH', 1, 117, int(e.x/scale), int(e.y/scale)))
    canvas.bind(sequence="<1>", func=LeftDown)
    canvas.bind(sequence="<ButtonRelease-1>", func=LeftUp)

    # Botón derecho del mouse
    def RightDown(e):
        return EventDo(struct.pack('>BBHH', 3, 100, int(e.x/scale), int(e.y/scale)))

    def RightUp(e):
        return EventDo(struct.pack('>BBHH', 3, 117, int(e.x/scale), int(e.y/scale)))
    canvas.bind(sequence="<3>", func=RightDown)
    canvas.bind(sequence="<ButtonRelease-3>", func=RightUp)

    # Rueda del mouse
    if PLAT == b'win' or PLAT == 'osx':
        # windows/mac
        def Wheel(e):
            if e.delta < 0:
                return EventDo(struct.pack('>BBHH', 2, 0, int(e.x/scale), int(e.y/scale)))
            else:
                return EventDo(struct.pack('>BBHH', 2, 1, int(e.x/scale), int(e.y/scale)))
        canvas.bind(sequence="<MouseWheel>", func=Wheel)
    elif PLAT == b'x11':
        def WheelDown(e):
            return EventDo(struct.pack('>BBHH', 2, 0, int(e.x/scale), int(e.y/scale)))
        def WheelUp(e):
            return EventDo(struct.pack('>BBHH', 2, 1, int(e.x/scale), int(e.y/scale)))
        canvas.bind(sequence="<Button-4>", func=WheelUp)
        canvas.bind(sequence="<Button-5>", func=WheelDown)

    # Movimiento del mouse
    # Enviar cada 100ms
    def Move(e):
        global last_send
        cu = time.time()
        if cu - last_send > IDLE:
            last_send = cu
            sx, sy = int(e.x/scale), int(e.y/scale)
            return EventDo(struct.pack('>BBHH', 4, 0, sx, sy))
    canvas.bind(sequence="<Motion>", func=Move)

    # Teclado
    def KeyDown(e):
        return EventDo(struct.pack('>BBHH', e.keycode, 100, int(e.x/scale), int(e.y/scale)))

    def KeyUp(e):
        return EventDo(struct.pack('>BBHH', e.keycode, 117, int(e.x/scale), int(e.y/scale)))
    canvas.bind(sequence="<KeyPress>", func=KeyDown)
    canvas.bind(sequence="<KeyRelease>", func=KeyUp)


def run():
    global wscale, fixh, fixw, soc, showcan
    try:
        debug_print("Iniciando conexión con el servidor...")
        SetSocket()
        debug_print("Socket configurado correctamente")
        
        # Enviar información de plataforma
        soc.sendall(PLAT)
        debug_print(f"Información de plataforma enviada: {PLAT}")
        
        lenb = soc.recv(5)
        imtype, le = struct.unpack(">BI", lenb)
        debug_print(f"Recibiendo imagen inicial: tipo={imtype}, tamaño={le}")
        
        imb = b''
        while le > bufsize:
            t = soc.recv(bufsize)
            imb += t
            le -= len(t)
        while le > 0:
            t = soc.recv(le)
            imb += t
            le -= len(t)
            
        data = np.frombuffer(imb, dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        h, w, _ = img.shape
        fixh, fixw = h, w
        debug_print(f"Imagen inicial recibida: {w}x{h}")
        
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
        debug_print(f"Canvas configurado con escala: {scale}")
        
        frame_count = 0
        while True:
            if wscale:
                h = int(fixh * scale)
                w = int(fixw * scale)
                cv.config(width=w, height=h)
                wscale = False
                debug_print(f"Escala actualizada: {scale}")
                
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
                    
                data = np.frombuffer(imb, dtype=np.uint8)
                ims = cv2.imdecode(data, cv2.IMREAD_COLOR)
                
                if imtype == 1:
                    # Transmisión completa
                    img = ims
                    if DEBUG_MODE and frame_count % 100 == 0:
                        debug_print(f"Frame completo recibido #{frame_count}")
                else:
                    # Transmisión diferencial
                    img = img ^ ims
                    if DEBUG_MODE and frame_count % 100 == 0:
                        debug_print(f"Frame diferencial recibido #{frame_count}")
                        
                imt = cv2.resize(img, (w, h))
                imsh = cv2.cvtColor(imt, cv2.COLOR_RGB2RGBA)
                imi = Image.fromarray(imsh)
                imgTK.paste(imi)
                frame_count += 1
                
            except Exception as e:
                debug_print(f"Error en recepción de frame: {e}")
                showcan = None
                ShowScreen()
                return
                
    except Exception as e:
        debug_print(f"Error en función run(): {e}")
        if DEBUG_MODE:
            tkinter.messagebox.showerror('Error', f'Error de conexión: {e}')
        showcan = None
        ShowScreen()
        return


root.mainloop()
