# -**- coding: utf-8 -**-
import sys

# --- VERIFICACIÓN DE VERSIÓN ---
if sys.version_info[0] < 3:
    print("Error: Necesitas Python 3.")
    exit()

import cv2
import numpy as np
import SeguimientoManos as sm
import time
import pyautogui
import os
import subprocess 
import tkinter as tk
from PIL import Image, ImageTk # REQUERIDO: pip install Pillow

# Configuración para máxima velocidad de respuesta
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

# --- CONFIGURACIÓN DE RUTAS DINÁMICAS ---
DIRECTORIO_PROYECTO = os.path.dirname(os.path.abspath(__file__))

# Archivos 3D
ARCHIVO_1 = os.path.join(DIRECTORIO_PROYECTO, "Meningo hidroencefalocele.mix")
ARCHIVO_2 = os.path.join(DIRECTORIO_PROYECTO, "Craneorraquisquisis.mix")
ARCHIVO_3 = os.path.join(DIRECTORIO_PROYECTO, "Holoprosencefalia alobar.mix")

# Imágenes correspondientes
IMG_1 = os.path.join(DIRECTORIO_PROYECTO, "feto1.png")
IMG_2 = os.path.join(DIRECTORIO_PROYECTO, "feto2.png")
IMG_3 = os.path.join(DIRECTORIO_PROYECTO, "feto3.png")

# ==============================================================================
# 1. AUTOSTART
# ==============================================================================
def configurar_autostart():
    try:
        ruta_script = os.path.abspath(__file__)
        ruta_startup = os.path.join(os.environ['APPDATA'], 
                                    r'Microsoft\Windows\Start Menu\Programs\Startup')
        archivo_bat = os.path.join(ruta_startup, "MediHand_Autostart.bat")
        
        if not os.path.exists(archivo_bat):
            with open(archivo_bat, "w") as f:
                f.write('@echo off\n')
                f.write('cd /d "{}"\n'.format(os.path.dirname(ruta_script)))
                f.write('start "" "{}" "{}"\n'.format(sys.executable, ruta_script))
    except: pass

configurar_autostart()

# ============= CLASE VENTANA DE ESTADO (HUD) COMPACTA =============
class VentanaEstado:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MediHand Status")
        self.root.attributes('-topmost', True) 
        self.root.attributes('-alpha', 0.95)

        # Ventana más compacta para evitar espacios en blanco
        self.ancho_ventana = 300
        self.alto_ventana = 390 

        ancho_p = self.root.winfo_screenwidth()
        self.root.geometry('{}x{}+{}+{}'.format(self.ancho_ventana, self.alto_ventana, ancho_p - self.ancho_ventana - 20, 50))
        self.root.configure(bg="#ffffff")
        
        White = "#ffffff"
        self.frame_principal = tk.Frame(self.root, bg=White, padx=10, pady=5)
        self.frame_principal.pack(fill='both', expand=True)

        tk.Label(self.frame_principal, text="CONTROL POR GESTOS", font=('Arial', 10, 'bold'), fg='#00aaaa', bg=White).pack(pady=(5, 0))
        tk.Frame(self.frame_principal, height=2, bg='#00aaaa').pack(fill='x', pady=5)

        self.label_estado = tk.Label(self.frame_principal, text="Estado: ACTIVO", font=('Arial', 9, 'bold'), fg='#00aa00', bg=White)
        self.label_estado.pack(anchor='w')

        self.label_modo = tk.Label(self.frame_principal, text="Modo: ESPERANDO", font=('Arial', 9), fg='#555555', bg=White)
        self.label_modo.pack(anchor='w')

        self.panel_imagen = tk.Label(self.frame_principal, bg=White)
        self.panel_imagen.pack(pady=5)

        self.label_evento = tk.Label(self.frame_principal, text="", font=('Arial', 8, 'italic'), fg='#0055ff', bg=White)
        self.label_evento.pack(anchor='w')

        self.activa = True
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar)

    def actualizar_imagen(self, ruta_img=None):
        if not self.activa: return
        if ruta_img and os.path.exists(ruta_img):
            img_pil = Image.open(ruta_img).resize((250, 250), Image.LANCZOS)
            self.img_tk = ImageTk.PhotoImage(img_pil)
            self.panel_imagen.config(image=self.img_tk)
        else: self.panel_imagen.config(image='')

    def actualizar_estado(self, pausado):
        if self.activa:
            txt, col = ("PAUSADO", "#ff4444") if pausado else ("ACTIVO", "#00aa00")
            self.label_estado.config(text="Estado: " + txt, fg=col)

    def actualizar_modo(self, modo, color='#555555'):
        if self.activa: self.label_modo.config(text="Modo: {}".format(modo), fg=color)

    def mostrar_evento(self, evento):
        if self.activa:
            self.label_evento.config(text=evento)
            self.root.after(1500, lambda: self.label_evento.config(text="") if self.activa else None)

    def cerrar(self):
        self.activa = False
        try: self.root.destroy()
        except: pass

    def actualizar(self):
        if self.activa:
            try: self.root.update_idletasks(); self.root.update()
            except: self.activa = False

# ============= FUNCIONES DE ARCHIVOS =============
def abrir_meshmixer(ruta_archivo):
    if not os.path.exists(ruta_archivo): return False
    try:
        os.startfile(ruta_archivo)
        time.sleep(6) 
        pyautogui.click(pyautogui.size()[0]//2, pyautogui.size()[1]//2)
        pyautogui.hotkey('alt', 'enter')
        return True
    except: return False

# ============= INICIO POR GESTO =============
def esperar_gesto_inicio(cap, detector):
    nombre_v = 'Instrucciones de Inicio - MediHand'
    img = cv2.imread(os.path.join(DIRECTORIO_PROYECTO, "GestoInicio.png"))
    ancho_p, alto_p = pyautogui.size()
    
    if img is not None:
        ancho_d = int(ancho_p * 0.5)
        img = cv2.resize(img, (ancho_d, int(img.shape[0] * (ancho_d/img.shape[1]))))
        cv2.namedWindow(nombre_v, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(nombre_v, cv2.WND_PROP_TOPMOST, 1)
        cv2.resizeWindow(nombre_v, img.shape[1], img.shape[0])
        cv2.moveWindow(nombre_v, (ancho_p // 2) - (img.shape[1] // 2), (alto_p // 2) - (img.shape[0] // 2))

    while True:
        ret, frame = cap.read()
        if not ret: break
        frame = detector.encontrarmanos(frame, dibujar=False)
        lista, _ = detector.encontrarposicion(frame, dibujar=False)
        if img is not None: cv2.imshow(nombre_v, img)
        if len(lista) != 0:
            if detector.dedosarriba() == [1, 0, 1, 1, 1]: 
                try: cv2.destroyWindow(nombre_v)
                except: pass
                return True
        if cv2.waitKey(1) == 27: return False
    return False

#======================== BUCLE PRINCIPAL ========================
def loop_principal(cap, detector):
    if not esperar_gesto_inicio(cap, detector): return "SALIR"

    nombre_portada = 'Museo de Embriologia - Seleccione un Feto'
    img_portada = cv2.imread(os.path.join(DIRECTORIO_PROYECTO, "PortadaEmbrio.png"))
    ancho_p, alto_p = pyautogui.size()

    if img_portada is not None:
        ancho_d = int(ancho_p * 0.6)
        img_portada = cv2.resize(img_portada, (ancho_d, int(img_portada.shape[0] * (ancho_d/img_portada.shape[1]))))
        cv2.namedWindow(nombre_portada, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(nombre_portada, cv2.WND_PROP_TOPMOST, 1)
        cv2.resizeWindow(nombre_portada, img_portada.shape[1], img_portada.shape[0])
        cv2.moveWindow(nombre_portada, (ancho_p // 2) - (img_portada.shape[1] // 2), (alto_p // 2) - (img_portada.shape[0] // 2))
        # Mostrar imagen inmediatamente para que no haya pantalla negra
        cv2.imshow(nombre_portada, img_portada)
        cv2.waitKey(1)

    ventana = VentanaEstado()
    pubix, pubiy = 0, 0
    izq_presionado, der_presionado = False, False
    sua = 4 
    # --- SEGURO DE TIEMPO INICIAL (3 segundos de cooldown al empezar) ---
    t_entrada = time.time()
    t_apertura = t_entrada + 3.0 
    
    sistema_pausado = False
    gesto_anterior = None
    frames_mismo_gesto = 0
    frames_reinicio = 0 
    scroll_anchor_y = None
    
    # Contadores para apertura segura
    frames_feto = 0
    ultimo_feto_detectado = None

    while True:
        if not ventana.activa: break
        ret, frame = cap.read()
        if not ret: break

        frame = detector.encontrarmanos(frame, dibujar=False)
        lista, _ = detector.encontrarposicion(frame, dibujar=False)
        modo_texto_actual = "ESPERANDO"
        ventana.actualizar_estado(sistema_pausado)

        if len(lista) != 0:
            x_i, y_i = lista[8][1:]
            dedos = detector.dedosarriba()

            # REINICIO / VOLVER AL MENÚ
            if dedos == [1, 1, 1, 1, 0]:
                frames_reinicio += 1
                if frames_reinicio > 40:
                    os.system("taskkill /F /IM meshmixer.exe /T >nul 2>&1")
                    ventana.cerrar()
                    try: cv2.destroyWindow(nombre_portada)
                    except: pass
                    return "REINICIAR"
                modo_texto_actual = "VOLVIENDO AL MENÚ..."
            else: frames_reinicio = 0

            # GESTIÓN DE PAUSA
            if tuple(dedos) == gesto_anterior: frames_mismo_gesto += 1
            else: frames_mismo_gesto = 0; gesto_anterior = tuple(dedos)
            if dedos == [0, 0, 0, 0, 0] and frames_mismo_gesto > 20:
                if time.time() - t_entrada > 2.0:
                    sistema_pausado = not sistema_pausado
                    frames_mismo_gesto = 0
                    ventana.mostrar_evento("PAUSADO" if sistema_pausado else "REANUDADO")

            if sistema_pausado:
                modo_texto_actual = "PAUSA"; ventana.actualizar_modo(modo_texto_actual, "#ff6600")
                ventana.actualizar(); cv2.imshow("Control por Gestos", frame)
                if cv2.waitKey(1) == 27: return "SALIR"
                continue

            # MOVIMIENTOS Y CLICS
            if dedos == [0, 1, 1, 1, 0]:
                modo_texto_actual = "SCROLL"
                if scroll_anchor_y is None: scroll_anchor_y = y_i
                delta = scroll_anchor_y - y_i
                if abs(delta) > 25: pyautogui.scroll(120 if delta > 0 else -120); scroll_anchor_y = y_i
            else:
                scroll_anchor_y = None
                if dedos == [0, 1, 1, 0, 0]:
                    pyautogui.click(); ventana.mostrar_evento("Click!"); time.sleep(0.3)
                if dedos[0] == 1 and dedos[1] == 1 and dedos[2] == 1 and dedos[3] == 0:
                    if not der_presionado: pyautogui.mouseDown(button='right'); der_presionado = True
                    modo_texto_actual = "ROTAR"
                else:
                    if der_presionado: pyautogui.mouseUp(button='right'); der_presionado = False
                dist_p, _, _ = detector.distancia(4, 8, frame, dibujar=False)
                if dist_p < 38:
                    if not izq_presionado: pyautogui.mouseDown(button='left'); izq_presionado = True
                    modo_texto_actual = "ARRASTRAR"
                else:
                    if izq_presionado: pyautogui.mouseUp(button='left'); izq_presionado = False
                if dedos[1] == 1:
                    x3 = np.interp(x_i, (80, 560), (0, ancho_p))
                    y3 = np.interp(y_i, (80, 400), (0, alto_p))
                    cubix = pubix + (x3 - pubix) / sua
                    cubiy = pubiy + (y3 - pubiy) / sua
                    pyautogui.moveTo(ancho_p - cubix, cubiy)
                    pubix, pubiy = cubix, cubiy
                    if modo_texto_actual == "ESPERANDO": modo_texto_actual = "MOVER"

            # --- GESTOS DE APERTURA CON CONFIRMACIÓN ---
            ahora = time.time()
            if ahora > t_apertura:
                gestos_fetos = [[0, 0, 1, 1, 1], [0, 0, 0, 1, 1], [0, 0, 0, 0, 1]]
                if dedos in gestos_fetos:
                    if dedos == ultimo_feto_detectado:
                        frames_feto += 1
                    else:
                        frames_feto = 0
                        ultimo_feto_detectado = dedos
                    
                    # Debe mantener el gesto 15 frames (~0.5 seg) para abrir
                    if frames_feto > 15:
                        try: cv2.destroyWindow(nombre_portada)
                        except: pass
                        
                        if dedos == [0, 0, 1, 1, 1]:
                            if abrir_meshmixer(ARCHIVO_1): 
                                t_apertura = ahora + 10.0; ventana.actualizar_imagen(IMG_1); ventana.mostrar_evento("Feto 1")
                        elif dedos == [0, 0, 0, 1, 1]:
                            if abrir_meshmixer(ARCHIVO_2): 
                                t_apertura = ahora + 10.0; ventana.actualizar_imagen(IMG_2); ventana.mostrar_evento("Feto 2")
                        elif dedos == [0, 0, 0, 0, 1]:
                            if abrir_meshmixer(ARCHIVO_3): 
                                t_apertura = ahora + 10.0; ventana.actualizar_imagen(IMG_3); ventana.mostrar_evento("Feto 3")
                        frames_feto = 0
                else:
                    frames_feto = 0
                    ultimo_feto_detectado = None

        if img_portada is not None:
            try: cv2.imshow(nombre_portada, img_portada)
            except: pass

        ventana.actualizar_modo(modo_texto_actual)
        ventana.actualizar()
        cv2.imshow("Control por Gestos", frame)
        if cv2.waitKey(1) == 27: return "SALIR"
    return "SALIR"

#======================== EJECUCIÓN FINAL ========================
cap = cv2.VideoCapture(0)
cap.set(3, 640); cap.set(4, 480)
detector = sm.detectormanos(maxManos=1)

while True:
    resultado = loop_principal(cap, detector)
    if resultado == "SALIR": break

cap.release()
cv2.destroyAllWindows()