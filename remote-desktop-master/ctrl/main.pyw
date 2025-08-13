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
import argparse
import logging
from logging.handlers import TimedRotatingFileHandler
import os

# Configuración de argumentos de línea de comandos
parser = argparse.ArgumentParser(description='Cliente de Control Remoto')
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
    log_file = os.path.join(log_dir, 'remote_client.log')
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
logger.info(f"Cliente iniciado en modo {'DEBUG' if args.debug else 'NORMAL'}")

root = tkinter.Tk()
logger.debug("Ventana principal de tkinter creada")

# Ciclo de pantalla
IDLE = 0.05
logger.debug(f"Configurado IDLE: {IDLE}")

# Tamaño de escala
scale = 1

# Dimensiones originales de pantalla transmitida
fixw, fixh = 0, 0

# Bandera de escalado
wscale = False

# Lienzo de visualización de pantalla
showcan = None

# Tamaño del búfer de socket
bufsize = 10240

# Hilo
th = None

# socket
soc = None

# socks5

socks5 = None


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
    global soc, host_en
    logger.info("Configurando socket de conexión")

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
    logger.debug(f"Host obtenido: {host}")
    if host is None:
        logger.error("Configuración de host incorrecta: host es None")
        tkinter.messagebox.showinfo('Aviso', '¡Configuración de Host incorrecta!')
        return
    hs = host.split(":")
    if len(hs) != 2:
        logger.error(f"Configuración de host incorrecta: formato inválido {host}")
        tkinter.messagebox.showinfo('Aviso', '¡Configuración de Host incorrecta!')
        return
    if socks5 is not None:
        logger.info(f"Configurando conexión a través de proxy SOCKS5: {socks5}")
        ss = socks5.split(":")
        if len(ss) != 2:
            logger.error(f"Configuración de proxy incorrecta: formato inválido {socks5}")
            tkinter.messagebox.showinfo('Aviso', '¡Configuración de proxy incorrecta!')
            return
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            soc.connect((ss[0], int(ss[1])))
            logger.debug(f"Conectado al proxy SOCKS5: {ss[0]}:{ss[1]}")
        except Exception as e:
            logger.error(f"Error conectando al proxy SOCKS5: {e}")
            tkinter.messagebox.showinfo('Aviso', f'Error conectando al proxy: {e}')
            return
        soc.sendall(struct.pack(">BB", 5, 0))
        recv = soc.recv(2)
        if recv[1] != 0:
            logger.error(f"Respuesta de proxy incorrecta en handshake: {recv[1]}")
            tkinter.messagebox.showinfo('Aviso', '¡Respuesta de proxy incorrecta!')
            return
        if re.match(r'^\d+?\.\d+?\.\d+?\.\d+?:\d+$', host) is None:
            # acceso por nombre de dominio del host
            logger.debug(f"Configurando acceso por nombre de dominio: {hs[0]}")
            hand = byhost(hs[0], int(hs[1]))
            soc.sendall(hand)
        else:
            # acceso por IP del host
            logger.debug(f"Configurando acceso por IP: {hs[0]}")
            ip = [int(i) for i in hs[0].split(".")]
            port = int(hs[1])
            hand = byipv4(ip, port)
            soc.sendall(hand)
        # respuesta del proxy
        logger.debug("Esperando respuesta del proxy")
        rcv = b''
        while len(rcv) != 10:
            rcv += soc.recv(10-len(rcv))
        if rcv[1] != 0:
            logger.error(f"Error en respuesta del proxy, código: {rcv[1]}")
            tkinter.messagebox.showinfo('Aviso', '¡Respuesta de proxy incorrecta!')
            return
        logger.info("Conexión SOCKS5 configurada correctamente")
    else:
        logger.debug("Conexión directa sin proxy")
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            soc.connect((hs[0], int(hs[1])))
            logger.info(f"Conectado directamente a {hs[0]}:{hs[1]}")
        except Exception as e:
            logger.error(f"Error conectando directamente al host: {e}")
            tkinter.messagebox.showinfo('Aviso', f'Error conectando al host: {e}')
            return


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
    s5_lab = tkinter.Label(pr, text="Host Socks5:")
    s5_en = tkinter.Entry(pr, show=None, font=('Arial', 14), textvariable=s5v)
    s5_btn = tkinter.Button(pr, text="Aceptar", command=set_s5_addr)
    s5_lab.grid(row=0, column=0, padx=10, pady=10, ipadx=0, ipady=0)
    s5_en.grid(row=0, column=1, padx=10, pady=10, ipadx=40, ipady=0)
    s5_btn.grid(row=1, column=0, padx=10, pady=10, ipadx=30, ipady=0)
    s5v.set("127.0.0.1:88")


def ShowScreen():
    global showcan, root, soc, th, wscale
    logger.info("Iniciando visualización de pantalla remota")
    
    if showcan is None:
        logger.debug("Creando nueva ventana de visualización")
        wscale = True
        showcan = tkinter.Toplevel(root)
        showcan.title("Pantalla")
        showcan.protocol("WM_DELETE_WINDOW", lambda: showcan.destroy())
        
        logger.debug("Iniciando hilo de comunicación")
        th = threading.Thread(target=run)
        th.daemon = True
        th.start()
        logger.info("Visualización de pantalla iniciada correctamente")
    else:
        logger.info("Cerrando visualización de pantalla existente")
        soc.close()
        showcan.destroy()
        showcan = None
        logger.debug("Visualización cerrada correctamente")


val = tkinter.StringVar()
host_lab = tkinter.Label(root, text="Host:")
host_en = tkinter.Entry(root, show=None, font=('Arial', 16), textvariable=val)
sca_lab = tkinter.Label(root, text="Escala:")
sca = tkinter.Scale(root, from_=10, to=150, orient=tkinter.HORIZONTAL, length=100,
                    showvalue=100, resolution=0.2, tickinterval=50, command=SetScale)
proxy_btn = tkinter.Button(root, text="Proxy", command=ShowProxy)
show_btn = tkinter.Button(root, text="Mostrar", command=ShowScreen)

host_lab.grid(row=0, column=0, padx=10, pady=10, ipadx=0, ipady=0)
host_en.grid(row=0, column=1, padx=0, pady=0, ipadx=40, ipady=0)
sca_lab.grid(row=1, column=0, padx=10, pady=10, ipadx=0, ipady=0)
sca.grid(row=1, column=1, padx=0, pady=0, ipadx=100, ipady=0)
proxy_btn.grid(row=2, column=0, padx=0, pady=10, ipadx=30, ipady=0)
show_btn.grid(row=2, column=1, padx=0, pady=10, ipadx=30, ipady=0)
sca.set(97)

textfile = open(filename, 'r')

matches = []
reg = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
strip=""
if textfile.read() == '':
    strip="192.168.0.14"
    print("no se encontraron datos")
else:
    textfile.seek(0)
    print("Datos presentes en el archivo")
    for line in textfile:
        matches += reg.findall(line)
        print ("line:",line,"|len:",len(matches))
    textfile.close()

    print ("matches:",len(matches),matches[0])
    strip=matches[0]


val.set(strip+":3380")
last_send = time.time()





def BindEvents(canvas):
    global soc, scale
    '''
    Procesar eventos
    '''
    logger.debug("Configurando eventos de entrada del usuario")
    
    def EventDo(data):
        soc.sendall(data)
    # Botón izquierdo del ratón

    def LeftDown(e):
        logger.debug(f"Botón izquierdo presionado en ({int(e.x/scale)}, {int(e.y/scale)})")
        return EventDo(struct.pack('>BBHH', 1, 100, int(e.x/scale), int(e.y/scale)))

    def LeftUp(e):
        logger.debug(f"Botón izquierdo liberado en ({int(e.x/scale)}, {int(e.y/scale)})")
        return EventDo(struct.pack('>BBHH', 1, 117, int(e.x/scale), int(e.y/scale)))
    canvas.bind(sequence="<1>", func=LeftDown)
    canvas.bind(sequence="<ButtonRelease-1>", func=LeftUp)

    # Botón derecho del ratón
    def RightDown(e):
        logger.debug(f"Botón derecho presionado en ({int(e.x/scale)}, {int(e.y/scale)})")
        return EventDo(struct.pack('>BBHH', 3, 100, int(e.x/scale), int(e.y/scale)))

    def RightUp(e):
        logger.debug(f"Botón derecho liberado en ({int(e.x/scale)}, {int(e.y/scale)})")
        return EventDo(struct.pack('>BBHH', 3, 117, int(e.x/scale), int(e.y/scale)))
    canvas.bind(sequence="<3>", func=RightDown)
    canvas.bind(sequence="<ButtonRelease-3>", func=RightUp)

    # Rueda del ratón
    if PLAT == b'win' or PLAT == 'osx':
        # windows/mac (sistemas operativos)
        def Wheel(e):
            if e.delta < 0:
                logger.debug("Scroll hacia abajo enviado")
                return EventDo(struct.pack('>BBHH', 2, 0, int(e.x/scale), int(e.y/scale)))
            else:
                logger.debug("Scroll hacia arriba enviado")
                return EventDo(struct.pack('>BBHH', 2, 1, int(e.x/scale), int(e.y/scale)))
        canvas.bind(sequence="<MouseWheel>", func=Wheel)
    elif PLAT == b'x11':
        def WheelDown(e):
            logger.debug("Scroll hacia abajo enviado (Linux)")
            return EventDo(struct.pack('>BBHH', 2, 0, int(e.x/scale), int(e.y/scale)))
        def WheelUp(e):
            logger.debug("Scroll hacia arriba enviado (Linux)")
            return EventDo(struct.pack('>BBHH', 2, 1, int(e.x/scale), int(e.y/scale)))
        canvas.bind(sequence="<Button-4>", func=WheelUp)
        canvas.bind(sequence="<Button-5>", func=WheelDown)

    # Movimiento del ratón
    # Enviar una vez cada 100ms
    def Move(e):
        global last_send
        cu = time.time()
        if cu - last_send > IDLE:
            last_send = cu
            sx, sy = int(e.x/scale), int(e.y/scale)
            logger.debug(f"Movimiento del ratón enviado: ({sx}, {sy})")
            return EventDo(struct.pack('>BBHH', 4, 0, sx, sy))
    canvas.bind(sequence="<Motion>", func=Move)

    # Teclado
    def KeyDown(e):
        logger.debug(f"Tecla presionada: código {e.keycode}")
        return EventDo(struct.pack('>BBHH', e.keycode, 100, int(e.x/scale), int(e.y/scale)))

    def KeyUp(e):
        logger.debug(f"Tecla liberada: código {e.keycode}")
        return EventDo(struct.pack('>BBHH', e.keycode, 117, int(e.x/scale), int(e.y/scale)))
    canvas.bind(sequence="<KeyPress>", func=KeyDown)
    canvas.bind(sequence="<KeyRelease>", func=KeyUp)
    
    logger.info("Eventos de entrada configurados correctamente")


def run():
    global wscale, fixh, fixw, soc, showcan
    logger.info("Iniciando hilo de comunicación principal")
    
    SetSocket()
    if soc is None:
        logger.error("No se pudo configurar el socket, terminando hilo")
        return
    
    try:
        # Enviar información de plataforma
        logger.debug(f"Enviando información de plataforma: {PLAT}")
        soc.sendall(PLAT)
        
        # Recibir primera imagen
        logger.debug("Recibiendo primera imagen de pantalla")
        lenb = soc.recv(5)
        imtype, le = struct.unpack(">BI", lenb)
        logger.debug(f"Tipo de imagen: {imtype}, tamaño: {le} bytes")
        
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
        logger.info(f"Pantalla remota configurada: {w}x{h}")
        
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
        
        frame_count = 0
        while True:
            if wscale:
                h = int(fixh * scale)
                w = int(fixw * scale)
                cv.config(width=w, height=h)
                wscale = False
                logger.debug(f"Escala actualizada: {scale}, nuevo tamaño: {w}x{h}")
                
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
                    logger.debug(f"Frame completo recibido #{frame_count}")
                else:
                    # Transmisión diferencial
                    img = img ^ ims
                    logger.debug(f"Frame diferencial recibido #{frame_count}")
                    
                frame_count += 1
                imt = cv2.resize(img, (w, h))
                imsh = cv2.cvtColor(imt, cv2.COLOR_RGB2RGBA)
                imi = Image.fromarray(imsh)
                imgTK.paste(imi)
                
            except Exception as e:
                logger.error(f"Error en bucle de recepción: {e}")
                break
                
    except Exception as e:
        logger.error(f"Error en hilo de comunicación: {e}")
    finally:
        logger.info("Cerrando hilo de comunicación")
        if soc:
            soc.close()
        showcan = None


logger.info("Iniciando interfaz gráfica principal")
try:
    root.mainloop()
except Exception as e:
    logger.error(f"Error en interfaz gráfica: {e}")
finally:
    logger.info("Aplicación cliente terminada")
