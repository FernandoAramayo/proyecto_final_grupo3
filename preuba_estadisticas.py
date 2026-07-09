import tkinter as tk
from tkinter import messagebox, ttk
import cv2
import tensorflow as tf
import os
import random
import csv
import serial
import gestor_datos  
import banco_ejercicios
import motor_vision  
from PIL import Image, ImageTk
import datetime

FUENTE_PIXEL = "Terminal"

def font_pixel(tamano, negrita=True):
    tamano = max(8, int(tamano))
    if negrita:
        return (FUENTE_PIXEL, tamano, "bold")
    return (FUENTE_PIXEL, tamano)


def escala_ui(root):
    ancho = root.winfo_screenwidth()
    alto = root.winfo_screenheight()
    return max(0.50, min(0.85, min(ancho / 1920, alto / 1080)))


def font_adapt(root, tamano_base, negrita=True):
    return font_pixel(tamano_base * escala_ui(root), negrita)

def cargar_imagen_tk(ruta, max_ancho, max_alto):
    if not os.path.exists(ruta):
        return None

    img_cv = cv2.imread(ruta)
    if img_cv is None:
        return None

    h, w = img_cv.shape[:2]

    escala = min(max_ancho / w, max_alto / h)
    nuevo_ancho = int(w * escala)
    nuevo_alto = int(h * escala)

    img_cv = cv2.resize(img_cv, (nuevo_ancho, nuevo_alto))
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)

    return ImageTk.PhotoImage(image=img_pil)

class SistemaEducativoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema Educativo Inteligente")
        
        ancho_pantalla = self.winfo_screenwidth()
        alto_pantalla = self.winfo_screenheight()
        self.geometry(f"{ancho_pantalla}x{alto_pantalla}")
        self.configure(bg="#E8F4F8")
        
        try:
            self.state('zoomed')
        except tk.TclError:
            self.attributes('-zoomed', True)
            
        style = ttk.Style()
        style.theme_use("clam")
        s = escala_ui(self)

        style.configure(
            "Treeview.Heading",
            font=font_pixel(16 * s),
            background="#45B7D1",
            foreground="white"
        )

        style.configure(
            "Treeview",
            font=font_pixel(13 * s, False),
            rowheight=max(28, int(38 * s))
        )
        
        gestor_datos.inicializar_csv()
        self.protocol("WM_DELETE_WINDOW", self.cerrar_ventana)
        
        self.usuario_actual = ""
        self.fecha_sesion = "" # <-- NUEVO: Identificador de sesión
        self.hora_sesion = ""  # <-- NUEVO: Identificador de sesión
        self.respuestas_correctas = 0
        self.respuestas_incorrectas = 0
        self.imagenes_vistas = [] 
        
        self.progreso = {
            1: {'nivel': 1, 'pregunta': 1},
            2: {'nivel': 1, 'pregunta': 1}
        }
        
        self.interpreter = tf.lite.Interpreter(model_path="modelo_numeros3.tflite")
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        self.puerto_serial = None
        try:
            self.puerto_serial = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
            self.enviar_comando_pico("RESET")
        except serial.SerialException:
            pass
        
        self.container = tk.Frame(self, bg="#E8F4F8")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        self.frames = {}
        for F in (PantallaInicio, PantallaHome, PantallaModo, PantallaStats):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        self.mostrar_pantalla("PantallaInicio")

    def enviar_comando_pico(self, comando):
        if self.puerto_serial and self.puerto_serial.is_open:
            try:
                self.puerto_serial.write((comando + '\n').encode('utf-8'))
            except Exception:
                pass

    def construir_datos_sesion(self):
        total_intentos = self.respuestas_correctas + self.respuestas_incorrectas
        puntaje = (self.respuestas_correctas / total_intentos) if total_intentos > 0 else 0.0

        return {
            'nombre_usuario': self.usuario_actual,
            'respuestas_correctas': self.respuestas_correctas,
            'respuestas_incorrectas': self.respuestas_incorrectas,
            'puntaje': round(puntaje, 2),
            'nivel_modo1': self.progreso[1]['nivel'],
            'pregunta_modo1': self.progreso[1]['pregunta'],
            'nivel_modo2': self.progreso[2]['nivel'],
            'pregunta_modo2': self.progreso[2]['pregunta']
        }

    def guardar_progreso_actual(self):
        if self.usuario_actual:
            gestor_datos.guardar_progreso(self.construir_datos_sesion())

    def guardar_sesion_actual(self, nueva=False):
        """ NUEVA LÓGICA: Actualiza la fila en tiempo real sin duplicarla """
        if not self.usuario_actual:
            return

        datos = self.construir_datos_sesion()
        gestor_datos.guardar_progreso(datos)

        gestor_datos.inicializar_csv()
        ruta = gestor_datos.RUTA_SESIONES
        filas = []
        
        if os.path.exists(ruta):
            with open(ruta, "r", newline="", encoding="utf-8-sig") as f:
                filas = list(csv.DictReader(f))

        if nueva:
            # Crea la fila al iniciar sesión
            fila = {
                "fecha": self.fecha_sesion,
                "hora": self.hora_sesion,
                "nombre_usuario": datos["nombre_usuario"],
                "respuestas_correctas": datos["respuestas_correctas"],
                "respuestas_incorrectas": datos["respuestas_incorrectas"],
                "puntaje": datos["puntaje"],
                "nivel_modo1": datos["nivel_modo1"],
                "pregunta_modo1": datos["pregunta_modo1"],
                "nivel_modo2": datos["nivel_modo2"],
                "pregunta_modo2": datos["pregunta_modo2"]
            }
            filas.append(fila)
        else:
            # Busca y actualiza en tiempo real
            encontrado = False
            for i in range(len(filas)-1, -1, -1):
                nombre_csv = gestor_datos.normalizar_usuario(filas[i].get("nombre_usuario", ""))
                nombre_actual = gestor_datos.normalizar_usuario(self.usuario_actual)
                
                if nombre_csv == nombre_actual and filas[i].get("fecha") == self.fecha_sesion and filas[i].get("hora") == self.hora_sesion:
                    filas[i]["respuestas_correctas"] = datos["respuestas_correctas"]
                    filas[i]["respuestas_incorrectas"] = datos["respuestas_incorrectas"]
                    filas[i]["puntaje"] = datos["puntaje"]
                    filas[i]["nivel_modo1"] = datos["nivel_modo1"]
                    filas[i]["pregunta_modo1"] = datos["pregunta_modo1"]
                    filas[i]["nivel_modo2"] = datos["nivel_modo2"]
                    filas[i]["pregunta_modo2"] = datos["pregunta_modo2"]
                    encontrado = True
                    break
            
            if not encontrado:
                fila = {
                    "fecha": self.fecha_sesion, "hora": self.hora_sesion,
                    "nombre_usuario": datos["nombre_usuario"],
                    "respuestas_correctas": datos["respuestas_correctas"],
                    "respuestas_incorrectas": datos["respuestas_incorrectas"],
                    "puntaje": datos["puntaje"], "nivel_modo1": datos["nivel_modo1"],
                    "pregunta_modo1": datos["pregunta_modo1"], "nivel_modo2": datos["nivel_modo2"],
                    "pregunta_modo2": datos["pregunta_modo2"]
                }
                filas.append(fila)

        # Sobrescribe el CSV de sesiones limpiamente
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=gestor_datos.CAMPOS_SESIONES)
            writer.writeheader()
            writer.writerows(filas)

    def cerrar_ventana(self):
        if self.usuario_actual:
            self.guardar_sesion_actual()
        self.destroy()

    def mostrar_pantalla(self, page_name, modo=None):
        frame = self.frames[page_name]
        
        if page_name == "PantallaModo" and modo is not None:
            frame.iniciar_modo(modo)
        elif page_name == "PantallaStats":
            frame.redibujar_stats()
            
        if page_name in ["PantallaHome", "PantallaInicio", "PantallaStats"]:
            if "PantallaModo" in self.frames:
                self.frames["PantallaModo"].detener_camara()
                
        frame.tkraise()

    def cerrar_sesion(self):
        self.enviar_comando_pico("U")

        if self.usuario_actual:
            self.guardar_sesion_actual()

            self.usuario_actual = ""
            self.fecha_sesion = ""
            self.hora_sesion = ""
            self.respuestas_correctas = 0
            self.respuestas_incorrectas = 0
            self.imagenes_vistas.clear()
            self.progreso = {
                1: {'nivel': 1, 'pregunta': 1},
                2: {'nivel': 1, 'pregunta': 1}
            }

        self.mostrar_pantalla("PantallaInicio")

class PantallaInicio(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#F7D99A")
        self.controller = controller

        self.fondo_original = None
        self.fondo_tk = None
        self.entry_usuario = None

        self.canvas = tk.Canvas(
            self,
            bg="#F7D99A",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.cargar_assets()
        self.canvas.bind("<Configure>", self.redibujar_inicio)

    def fuente_pixel(self, tamano, negrita=True):
        tamano = max(8, int(tamano))
        if negrita:
            return ("Terminal", tamano, "bold")
        return ("Terminal", tamano)

    def cargar_assets(self):
        ruta_fondo = "assets/fondo_inicio.png"
        if os.path.exists(ruta_fondo):
            self.fondo_original = Image.open(ruta_fondo).convert("RGBA")
        else:
            self.fondo_original = None

    def redibujar_inicio(self, event=None):
        c = self.canvas
        c.delete("all")

        w = c.winfo_width()
        h = c.winfo_height()

        if w < 100 or h < 100:
            return

        if self.fondo_original:
            fondo_w, fondo_h = self.fondo_original.size
            escala = min(w / fondo_w, h / fondo_h)

            nuevo_w = int(fondo_w * escala)
            nuevo_h = int(fondo_h * escala)

            try:
                filtro = Image.Resampling.LANCZOS
            except AttributeError:
                filtro = Image.LANCZOS

            fondo_redimensionado = self.fondo_original.resize(
                (nuevo_w, nuevo_h),
                filtro
            )

            self.fondo_tk = ImageTk.PhotoImage(fondo_redimensionado)

            self.x_fondo = (w - nuevo_w) // 2
            self.y_fondo = (h - nuevo_h) // 2
            self.nuevo_w = nuevo_w
            self.nuevo_h = nuevo_h

            c.create_image(
                self.x_fondo,
                self.y_fondo,
                image=self.fondo_tk,
                anchor="nw"
            )
        else:
            self.x_fondo = 0
            self.y_fondo = 0
            self.nuevo_w = w
            self.nuevo_h = h

            c.create_rectangle(0, 0, w, h, fill="#F7D99A", outline="")
            c.create_text(
                w / 2,
                h / 2,
                text="Falta assets/fondo_inicio.png",
                font=self.fuente_pixel(28),
                fill="black"
            )

        escala_ui = min(self.nuevo_w / 1672, self.nuevo_h / 941)

        if self.entry_usuario is not None and self.entry_usuario.winfo_exists():
            self.entry_usuario.destroy()

        self.entry_usuario = tk.Entry(
            self.canvas,
            font=self.fuente_pixel(max(12, int(24 * escala_ui)), False),
            justify="center",
            bd=0,
            relief="flat",
            bg="#F8E7C2",
            fg="#151515",
            insertbackground="#151515"
        )
        self.entry_usuario.bind("<Return>", self.iniciar_sesion)

        self.canvas.create_window(
            self.x_fondo + self.nuevo_w * 0.51,
            self.y_fondo + self.nuevo_h * 0.55,
            window=self.entry_usuario,
            width=self.nuevo_w * 0.31,
            height=self.nuevo_h * 0.06
        )

        self.crear_boton_imagen(
            nombre="entrar",
            rel_x=0.30,
            rel_y=0.84,
            rel_w=0.20,
            rel_h=0.11,
            texto="ENTRAR",
            color_texto="white",
            comando=self.iniciar_sesion,
            escala=escala_ui
        )

        self.crear_boton_imagen(
            nombre="borrar",
            rel_x=0.70,
            rel_y=0.84,
            rel_w=0.24,
            rel_h=0.11,
            texto="BORRAR PERFIL",
            color_texto="white",
            comando=self.borrar_perfil,
            escala=escala_ui
        )

    def crear_boton_imagen(self, nombre, rel_x, rel_y, rel_w, rel_h, texto, color_texto, comando, escala):
        c = self.canvas

        x = self.x_fondo + self.nuevo_w * rel_x
        y = self.y_fondo + self.nuevo_h * rel_y
        bw = self.nuevo_w * rel_w
        bh = self.nuevo_h * rel_h

        x1 = x - bw / 2
        y1 = y - bh / 2
        x2 = x + bw / 2
        y2 = y + bh / 2

        tag = f"btn_{nombre}"

        c.create_rectangle(
            x1, y1, x2, y2,
            fill="",
            outline="",
            tags=(tag,)
        )

        c.create_text(
            x,
            y,
            text=texto,
            font=self.fuente_pixel(max(14, int(26 * escala))),
            fill=color_texto,
            tags=(tag,)
        )

        c.tag_bind(tag, "<Button-1>", lambda event: comando())
        c.tag_bind(tag, "<Enter>", lambda event: c.config(cursor="hand2"))
        c.tag_bind(tag, "<Leave>", lambda event: c.config(cursor=""))

    def iniciar_sesion(self, event=None):
        usuario = self.entry_usuario.get().strip()

        if usuario:
            self.controller.usuario_actual = usuario
            self.controller.respuestas_correctas = 0
            self.controller.respuestas_incorrectas = 0
            self.controller.imagenes_vistas.clear()
            
            # --- NUEVO: MARCAMOS EL INICIO EXACTO Y CREAMOS LA SESIÓN ---
            ahora = datetime.datetime.now()
            self.controller.fecha_sesion = ahora.strftime("%Y-%m-%d")
            self.controller.hora_sesion = ahora.strftime("%H:%M:%S")

            registro_previo = gestor_datos.cargar_datos_usuario(usuario)

            if registro_previo:
                self.controller.progreso[1]['nivel'] = registro_previo['nivel_modo1']
                self.controller.progreso[1]['pregunta'] = registro_previo['pregunta_modo1']
                self.controller.progreso[2]['nivel'] = registro_previo['nivel_modo2']
                self.controller.progreso[2]['pregunta'] = registro_previo['pregunta_modo2']
            else:
                self.controller.progreso = {
                    1: {'nivel': 1, 'pregunta': 1},
                    2: {'nivel': 1, 'pregunta': 1}
                }
                
            self.controller.guardar_sesion_actual(nueva=True) # Crea el registro en vivo

            self.entry_usuario.delete(0, tk.END)
            self.controller.mostrar_pantalla("PantallaHome")
        else:
            messagebox.showwarning("Falta nombre", "¡Por favor escribe tu nombre!")

    def borrar_perfil(self):
        usuario = self.entry_usuario.get().strip()

        if not usuario:
            messagebox.showwarning("Falta nombre", "Escribe el nombre del usuario que quieres eliminar.")
            return

        confirmacion = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Estás seguro de que deseas eliminar a '{usuario}'?"
        )

        if confirmacion:
            if gestor_datos.eliminar_usuario(usuario):
                messagebox.showinfo("Éxito", f"El usuario '{usuario}' fue eliminado correctamente.")
                self.entry_usuario.delete(0, tk.END)
            else:
                messagebox.showerror("Error", f"No se encontró registro para '{usuario}'.")

class PantallaHome(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#F7D99A")
        self.controller = controller

        self.fondo_original = None
        self.fondo_tk = None

        self.canvas = tk.Canvas(
            self,
            bg="#F7D99A",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.cargar_assets()
        self.canvas.bind("<Configure>", self.redibujar_home)

    def fuente_pixel(self, tamano, negrita=True):
        tamano = max(8, int(tamano))
        if negrita:
            return ("Terminal", tamano, "bold")
        return ("Terminal", tamano)

    def cargar_assets(self):
        ruta_fondo = "assets/fondo_mapa.png"

        if os.path.exists(ruta_fondo):
            self.fondo_original = Image.open(ruta_fondo).convert("RGBA")
        else:
            self.fondo_original = None

    def redibujar_home(self, event=None):
        c = self.canvas
        c.delete("all")

        w = c.winfo_width()
        h = c.winfo_height()

        if w < 100 or h < 100:
            return

        if self.fondo_original:
            fondo_w, fondo_h = self.fondo_original.size
            escala = min(w / fondo_w, h / fondo_h)

            nuevo_w = int(fondo_w * escala)
            nuevo_h = int(fondo_h * escala)

            try:
                filtro = Image.Resampling.LANCZOS
            except AttributeError:
                filtro = Image.LANCZOS

            fondo_redimensionado = self.fondo_original.resize(
                (nuevo_w, nuevo_h),
                filtro
            )

            self.fondo_tk = ImageTk.PhotoImage(fondo_redimensionado)
            self.x_fondo = (w - nuevo_w) // 2
            self.y_fondo = (h - nuevo_h) // 2
            self.nuevo_w = nuevo_w
            self.nuevo_h = nuevo_h

            c.create_image(
                self.x_fondo,
                self.y_fondo,
                image=self.fondo_tk,
                anchor="nw"
            )
        else:
            self.x_fondo = 0
            self.y_fondo = 0
            self.nuevo_w = w
            self.nuevo_h = h

            c.create_rectangle(0, 0, w, h, fill="#F7D99A", outline="")
            c.create_text(
                w / 2,
                h / 2,
                text="Falta assets/fondo_mapa.png",
                font=self.fuente_pixel(28),
                fill="black"
            )

        self.crear_boton_pixel(
            nombre="modo1",
            rel_x=0.34,
            rel_y=0.50,
            rel_w=0.095,
            rel_h=0.070,
            texto="MODO 1\nPIZARRA",
            color="#123333",
            borde="#071616",
            comando=lambda: self.controller.mostrar_pantalla("PantallaModo", modo=1),
            tipo="modo"
        )

        self.crear_boton_pixel(
            nombre="modo2",
            rel_x=0.61,
            rel_y=0.50,
            rel_w=0.095,
            rel_h=0.070,
            texto="MODO 2\nCONTEO",
            color="#123333",
            borde="#071616",
            comando=lambda: self.controller.mostrar_pantalla("PantallaModo", modo=2),
            tipo="modo"
        )

        self.crear_boton_pixel(
            nombre="stats",
            rel_x=0.76,
            rel_y=0.089,
            rel_w=0.13,
            rel_h=0.065,
            texto="ESTADISTICAS",
            color="#3FB7C9",
            borde="#1B5F6B",
            comando=lambda: self.controller.mostrar_pantalla("PantallaStats"),
            tipo="top"
        )

        self.crear_boton_pixel(
            nombre="salir",
            rel_x=0.90,
            rel_y=0.089,
            rel_w=0.13,
            rel_h=0.065,
            texto="SALIR",
            color="#7A5A3A",
            borde="#3C2614",
            comando=self.controller.cerrar_sesion,
            tipo="top"
        )

    def crear_boton_pixel(self, nombre, rel_x, rel_y, rel_w, rel_h, texto, color, borde, comando, tipo="modo"):
        c = self.canvas
        escala = min(self.nuevo_w / 1600, self.nuevo_h / 900)

        x = self.x_fondo + self.nuevo_w * rel_x
        y = self.y_fondo + self.nuevo_h * rel_y
        bw = self.nuevo_w * rel_w
        bh = self.nuevo_h * rel_h

        x1 = x - bw / 2
        y1 = y - bh / 2
        x2 = x + bw / 2
        y2 = y + bh / 2

        tag = f"btn_{nombre}"

        c.create_rectangle(
            x1 + 5 * escala,
            y1 + 5 * escala,
            x2 + 5 * escala,
            y2 + 5 * escala,
            fill="#2B1A0E",
            outline="",
            tags=(tag,)
        )

        c.create_rectangle(
            x1, y1, x2, y2,
            fill=borde,
            outline="#000000",
            width=max(2, int(3 * escala)),
            tags=(tag,)
        )

        c.create_rectangle(
            x1 + 4 * escala,
            y1 + 4 * escala,
            x2 - 4 * escala,
            y2 - 4 * escala,
            fill=color,
            outline="#D7C38A",
            width=max(1, int(2 * escala)),
            tags=(tag,)
        )

        c.create_line(
            x1 + 7 * escala,
            y1 + 7 * escala,
            x2 - 7 * escala,
            y1 + 7 * escala,
            fill="#FFFFFF",
            width=max(1, int(2 * escala)),
            tags=(tag,)
        )

        if tipo == "modo":
            tri_x = x1 + 22 * escala
            tri_y = y
            c.create_polygon(
                tri_x - 5 * escala, tri_y - 9 * escala,
                tri_x - 5 * escala, tri_y + 9 * escala,
                tri_x + 9 * escala, tri_y,
                fill="#A5E7FF", outline="white",
                width=max(1, int(1 * escala)),
                tags=(tag,)
            )
            text_x = x + 10 * escala
            font_size = max(10, int(17 * escala))
        else:
            c.create_polygon(x1 + 13 * escala, y, x1 + 20 * escala, y, x1 + 16 * escala, y + 7 * escala, fill="white", outline="", tags=(tag,))
            c.create_polygon(x1 + 25 * escala, y, x1 + 32 * escala, y, x1 + 28 * escala, y + 7 * escala, fill="white", outline="", tags=(tag,))
            text_x = x + 10 * escala
            font_size = max(9, int(17 * escala))

        c.create_text(
            text_x, y,
            text=texto,
            font=self.fuente_pixel(font_size),
            fill="white",
            justify="center",
            tags=(tag,)
        )

        c.tag_bind(tag, "<Button-1>", lambda event: comando())
        c.tag_bind(tag, "<Enter>", lambda event: c.config(cursor="hand2"))
        c.tag_bind(tag, "<Leave>", lambda event: c.config(cursor=""))

class PantallaModo(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#F7D99A")
        self.controller = controller
        self.modo_actual = None
        self.max_niveles = 5

        # Ajuste de orientación antes de analizar números.
        self.flip_analisis = -1

        self.cap = None
        self.camara_loop = None
        self.imgtk_cam = None
        self.imgtk_modo2 = None
        self.respuesta_modo2 = 0
        self.fondo_original = None
        self.fondo_tk = None

        self.x_fondo = 0
        self.y_fondo = 0
        self.nuevo_w = 1
        self.nuevo_h = 1

        self.cam_w = 900
        self.cam_h = 360
        self.modo2_w = 800
        self.modo2_h = 230

        self.canvas = tk.Canvas(self, bg="#F7D99A", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.cargar_assets()

        self.lbl_info = tk.Label(self.canvas, text="", font=font_pixel(18), bg="#F8E7C2", fg="#2C3E50")
        self.lbl_pregunta = tk.Label(self.canvas, text="", font=font_pixel(18), bg="#FCE9BD", fg="#2C3E50")
        self.lbl_ejercicio = tk.Label(self.canvas, text="", font=font_pixel(52), bg="#FFF2C8", fg="#2C3E50")
        self.lbl_imagen_modo2 = tk.Label(self.canvas, bg="#FFF2C8")
        self.lbl_camara = tk.Label(self.canvas, bg="black", bd=3, relief="solid")

        self.canvas.bind("<Configure>", self.redibujar_modo)

    def cargar_assets(self):
        ruta_fondo = "assets/fondo_modo.png"
        if os.path.exists(ruta_fondo):
            self.fondo_original = Image.open(ruta_fondo).convert("RGBA")
        else:
            self.fondo_original = None

    def redibujar_modo(self, event=None):
        c = self.canvas
        c.delete("all")

        w = c.winfo_width()
        h = c.winfo_height()

        if w < 100 or h < 100:
            return

        if self.fondo_original:
            fondo_w, fondo_h = self.fondo_original.size
            escala = min(w / fondo_w, h / fondo_h)

            nuevo_w = int(fondo_w * escala)
            nuevo_h = int(fondo_h * escala)

            try:
                filtro = Image.Resampling.LANCZOS
            except AttributeError:
                filtro = Image.LANCZOS

            fondo_redimensionado = self.fondo_original.resize((nuevo_w, nuevo_h), filtro)
            self.fondo_tk = ImageTk.PhotoImage(fondo_redimensionado)
            self.x_fondo = (w - nuevo_w) // 2
            self.y_fondo = (h - nuevo_h) // 2
            self.nuevo_w = nuevo_w
            self.nuevo_h = nuevo_h

            c.create_image(self.x_fondo, self.y_fondo, image=self.fondo_tk, anchor="nw")
        else:
            self.x_fondo = 0
            self.y_fondo = 0
            self.nuevo_w = w
            self.nuevo_h = h

            c.create_rectangle(0, 0, w, h, fill="#F7D99A", outline="")
            c.create_text(w / 2, h / 2, text="Falta assets/fondo_modo.png", font=font_pixel(28), fill="black")

        escala_ui = min(self.nuevo_w / 1672, self.nuevo_h / 941)

        self.cam_w = int(self.nuevo_w * 0.55)
        self.cam_h = int(self.nuevo_h * 0.28)
        self.modo2_w = int(self.nuevo_w * 0.46)
        self.modo2_h = int(self.nuevo_h * 0.21)

        self.lbl_info.config(font=font_pixel(19 * escala_ui))
        self.lbl_pregunta.config(font=font_pixel(18 * escala_ui))
        self.lbl_ejercicio.config(font=font_pixel(60 * escala_ui))

        c.create_text(
            self.x_fondo + self.nuevo_w * 0.32,
            self.y_fondo + self.nuevo_h * 0.105,
            text=self.lbl_info.cget("text"),
            font=font_pixel(20 * escala_ui),
            fill="#2C3E50"
        )

        self.crear_boton_canvas(
            nombre="home_modo",
            rel_x=0.895, rel_y=0.103, rel_w=0.105, rel_h=0.055,
            texto="HOME", color_texto="#7A4B2A",
            comando=lambda: self.controller.mostrar_pantalla("PantallaHome"),
            escala=escala_ui, tam_fuente=24
        )

        c.create_text(
            self.x_fondo + self.nuevo_w * 0.50,
            self.y_fondo + self.nuevo_h * 0.240,
            text=self.lbl_pregunta.cget("text"),
            font=font_pixel(20 * escala_ui),
            fill="#2C3E50",
            justify="center"
        )

        if self.modo_actual == 1:
            c.create_text(self.x_fondo + self.nuevo_w * 0.50, self.y_fondo + self.nuevo_h * 0.39, text=self.lbl_ejercicio.cget("text"), font=font_pixel(62 * escala_ui), fill="#2C3E50")
            c.create_window(self.x_fondo + self.nuevo_w * 0.50, self.y_fondo + self.nuevo_h * 0.61, window=self.lbl_camara, width=self.cam_w, height=self.cam_h)
        elif self.modo_actual == 2:
            c.create_window(self.x_fondo + self.nuevo_w * 0.50, self.y_fondo + self.nuevo_h * 0.40, window=self.lbl_imagen_modo2, width=self.modo2_w, height=self.modo2_h)
            c.create_window(self.x_fondo + self.nuevo_w * 0.50, self.y_fondo + self.nuevo_h * 0.66, window=self.lbl_camara, width=self.cam_w, height=self.cam_h)
        else:
            c.create_window(self.x_fondo + self.nuevo_w * 0.50, self.y_fondo + self.nuevo_h * 0.58, window=self.lbl_camara, width=self.cam_w, height=self.cam_h)
        
        self.crear_boton_canvas(
            nombre="mandar_respuesta",
            rel_x=0.50, rel_y=0.865, rel_w=0.22, rel_h=0.060,
            texto="MANDAR RESPUESTA", color_texto="#7A4B2A",
            comando=self.evaluar_respuesta,
            escala=escala_ui, tam_fuente=20
        )

    def crear_boton_canvas(self, nombre, rel_x, rel_y, rel_w, rel_h, texto, color_texto, comando, escala, tam_fuente=20):
        c = self.canvas
        x = self.x_fondo + self.nuevo_w * rel_x
        y = self.y_fondo + self.nuevo_h * rel_y
        bw = self.nuevo_w * rel_w
        bh = self.nuevo_h * rel_h

        x1 = x - bw / 2
        y1 = y - bh / 2
        x2 = x + bw / 2
        y2 = y + bh / 2

        tag = f"btn_{nombre}"
        c.create_rectangle(x1, y1, x2, y2, fill="", outline="", tags=(tag,))
        c.create_text(x, y, text=texto, font=font_pixel(max(10, int(tam_fuente * escala))), fill=color_texto, tags=(tag,))

        c.tag_bind(tag, "<Button-1>", lambda event: comando())
        c.tag_bind(tag, "<Enter>", lambda event: c.config(cursor="hand2"))
        c.tag_bind(tag, "<Leave>", lambda event: c.config(cursor=""))

    def iniciar_modo(self, modo):
        self.modo_actual = modo
        self.max_niveles = 5
        self.actualizar_ui_textos()
        self.redibujar_modo()
        self.detener_camara()

        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.3)
        self.actualizar_camara()

    def cargar_imagen_ejercicio(self):
        nivel = self.controller.progreso[self.modo_actual]['nivel']
        carpeta = f"modo2_nivel{nivel}"

        if not os.path.exists(carpeta):
            self.lbl_imagen_modo2.configure(image="", text=f"Falta carpeta:\n{carpeta}", font=font_adapt(self.controller, 18), width=50, height=5, bg="#FFF2C8", fg="#151515")
            self.respuesta_modo2 = 0
            return

        archivos = [f for f in os.listdir(carpeta) if f.lower().endswith(('.jpg', '.png'))]
        archivos_disponibles = [f for f in archivos if f not in self.controller.imagenes_vistas]

        if not archivos_disponibles:
            self.lbl_imagen_modo2.configure(image="", text="¡Te quedaste sin imágenes nuevas!", font=font_adapt(self.controller, 18), width=50, height=5, bg="#FFF2C8", fg="#151515")
            self.respuesta_modo2 = 0
            return

        imagen_elegida = random.choice(archivos_disponibles)
        self.controller.imagenes_vistas.append(imagen_elegida)

        try:
            nombre_sin_ext = imagen_elegida.split('.')[0]
            partes = text_sin_ext = nombre_sin_ext.split('_')
            categoria = partes[1]
            self.respuesta_modo2 = int(partes[2])
            self.lbl_pregunta.config(text=f"¿Cuántos {categoria} hay?")
        except Exception:
            self.respuesta_modo2 = 0
            self.lbl_pregunta.config(text="¿Cuántos objetos ves?")

        ruta_completa = os.path.join(carpeta, imagen_elegida)
        img_cv = cv2.imread(ruta_completa)

        if img_cv is not None:
            img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)

            ancho_caja, alto_caja = self.modo2_w, self.modo2_h
            img_pil.thumbnail((ancho_caja, alto_caja), Image.Resampling.LANCZOS)

            fondo = Image.new("RGB", (ancho_caja, alto_caja), "#FFF2C8")
            x_offset = (ancho_caja - img_pil.width) // 2
            y_offset = (alto_caja - img_pil.height) // 2
            fondo.paste(img_pil, (x_offset, y_offset))

            self.imgtk_modo2 = ImageTk.PhotoImage(image=fondo)
            self.lbl_imagen_modo2.configure(image=self.imgtk_modo2, text="", bg="#FFF2C8")

    def actualizar_ui_textos(self):
        nivel = self.controller.progreso[self.modo_actual]['nivel']
        pregunta = self.controller.progreso[self.modo_actual]['pregunta']

        self.lbl_info.config(text=f"Modo {self.modo_actual} | Nivel {nivel}/{self.max_niveles} | Pregunta {pregunta}/3")

        if self.modo_actual == 1:
            self.lbl_pregunta.config(text="Resuelve la siguiente operación:")
            ejercicio = banco_ejercicios.obtener_ejercicio(nivel, pregunta)
            self.lbl_ejercicio.config(text=ejercicio["ecuacion"])
        elif self.modo_actual == 2:
            self.cargar_imagen_ejercicio()

        self.redibujar_modo()

    def preparar_frame_analisis(self, frame):
        frame = cv2.convertScaleAbs(frame, alpha=1.0, beta=-50)

        if self.flip_analisis is not None:
            frame = cv2.flip(frame, self.flip_analisis)

        return frame

    def actualizar_camara(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()

            if ret:
                frame = self.preparar_frame_analisis(frame)

                try:
                    numero_detectado, confianza, estado, frame_debug = motor_vision.leer_pizarra(
                        frame,
                        self.controller.interpreter,
                        self.controller.input_details,
                        self.controller.output_details,
                        dibujar=True
                    )
                except Exception:
                    frame_debug = frame

                frame_recorte = cv2.resize(frame_debug, (self.cam_w, self.cam_h))
                img_rgb = cv2.cvtColor(frame_recorte, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(img_rgb)

                self.imgtk_cam = ImageTk.PhotoImage(image=img_pil)
                self.lbl_camara.configure(image=self.imgtk_cam)

            # 60 ms para no sobrecargar la Raspberry al ejecutar visión en vivo
            self.camara_loop = self.after(60, self.actualizar_camara)

    def detener_camara(self):
        if self.camara_loop:
            self.after_cancel(self.camara_loop)
            self.camara_loop = None
        if self.cap:
            self.cap.release()
            self.cap = None

    def evaluar_respuesta(self):
        if not self.cap or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        frame = self.preparar_frame_analisis(frame)

        if self.modo_actual == 1:
            nivel = self.controller.progreso[self.modo_actual]['nivel']
            pregunta = self.controller.progreso[self.modo_actual]['pregunta']
            ejercicio = banco_ejercicios.obtener_ejercicio(nivel, pregunta)
            respuesta_esperada = int(ejercicio["respuesta"])
        else:
            respuesta_esperada = self.respuesta_modo2

        numero_detectado, confianza, estado = motor_vision.leer_pizarra(
            frame, self.controller.interpreter, self.controller.input_details, self.controller.output_details
        )

        if estado == "NO_PIZARRA":
            messagebox.showinfo("Ups!", "No logro ver la pizarra completa. Asegúrate de mostrar las 4 esquinas a la cámara.")
            return
        elif estado == "NO_NUMEROS":
            messagebox.showinfo("¡Pizarra en blanco!", "Veo la pizarra perfectamente, pero no detecto números. Remarca bien tu respuesta.")
            return

        # --- AQUÍ INYECTAMOS EL GUARDADO EN TIEMPO REAL ---
        if numero_detectado == respuesta_esperada and confianza >= 60.0:
            self.controller.respuestas_correctas += 1
            self.controller.enviar_comando_pico("C")
            self.controller.guardar_sesion_actual() # <--- GUARDADO SEGURO
            messagebox.showinfo("¡Correcto!", f"¡Excelente! Leí un {numero_detectado}.")
            self.avanzar_pregunta()
        elif numero_detectado == respuesta_esperada and confianza < 60.0:
            messagebox.showinfo("Casi...", f"Parece un {numero_detectado}, pero no estoy seguro. ¿Puedes remarcarlo y volver a mandar?")
        else:
            if confianza >= 60.0 and numero_detectado < 100:
                self.controller.respuestas_incorrectas += 1
                self.controller.enviar_comando_pico("I")
                self.controller.guardar_sesion_actual() # <--- GUARDADO SEGURO
                messagebox.showerror("Aún no", f"Leí un {numero_detectado}. Esa no es la respuesta. ¡Sigue intentando!")
            else:
                messagebox.showinfo("Trazo dudoso", "Veo trazos confusos, ¿podrías borrar y escribir los números más claros?")

    def avanzar_pregunta(self):
        pregunta_actual = self.controller.progreso[self.modo_actual]['pregunta']

        if pregunta_actual < 3:
            self.controller.progreso[self.modo_actual]['pregunta'] += 1
            self.controller.guardar_progreso_actual()
            self.actualizar_ui_textos()
        else:
            self.controller.guardar_progreso_actual()
            self.detener_camara()
            self.mostrar_popup_recompensa()

    def mostrar_popup_recompensa(self):
        s = escala_ui(self.controller)
        popup = tk.Toplevel(self)
        popup.title("¡Nivel Terminado!")
        popup.geometry(f"{int(650 * s)}x{int(330 * s)}")
        popup.configure(bg="#FFF9C4")

        x = self.winfo_rootx() + (self.winfo_width() // 2) - int(325 * s)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - int(165 * s)
        popup.geometry(f"+{x}+{y}")

        popup.transient(self.controller)
        popup.grab_set()

        tk.Label(
            popup,
            text="¡Bien Hecho!",
            font=font_pixel(42 * s),
            fg="#FF9800",
            bg="#FFF9C4"
        ).pack(pady=max(25, int(45 * s)))

        nivel_actual = self.controller.progreso[self.modo_actual]['nivel']
        es_ultimo_nivel = nivel_actual >= self.max_niveles
        texto_btn = "Finalizar Modo" if es_ultimo_nivel else "Siguiente Nivel"

        tk.Button(
            popup,
            text=texto_btn,
            font=font_pixel(22 * s),
            bg="#4CAF50",
            fg="white",
            padx=max(20, int(35 * s)),
            pady=max(8, int(14 * s)),
            command=lambda: self.avanzar_nivel(popup, es_ultimo_nivel)
        ).pack(pady=max(10, int(18 * s)))

    def avanzar_nivel(self, popup, es_ultimo_nivel):
        popup.destroy()

        if not es_ultimo_nivel:
            self.controller.progreso[self.modo_actual]['nivel'] += 1
            self.controller.progreso[self.modo_actual]['pregunta'] = 1
            self.controller.guardar_progreso_actual()

            self.actualizar_ui_textos()
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.3)
            self.actualizar_camara()
        else:
            self.controller.guardar_progreso_actual()
            self.controller.mostrar_pantalla("PantallaHome")

class PantallaStats(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#F7D99A")
        self.controller = controller

        self.fondo_original = None
        self.fondo_tk = None
        self.tabla_frame = None
        self.tree = None

        self.canvas = tk.Canvas(self, bg="#F7D99A", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.cargar_assets()
        self.canvas.bind("<Configure>", self.redibujar_stats)

    def fuente_pixel(self, tamano, negrita=True):
        tamano = max(8, int(tamano))
        if negrita:
            return (FUENTE_PIXEL, tamano, "bold")
        return (FUENTE_PIXEL, tamano)

    def cargar_assets(self):
        ruta_fondo = "assets/fondo_stats.png"
        if os.path.exists(ruta_fondo):
            self.fondo_original = Image.open(ruta_fondo).convert("RGBA")
        else:
            self.fondo_original = None

    def redibujar_stats(self, event=None):
        c = self.canvas
        c.delete("all")

        if self.tabla_frame is not None and self.tabla_frame.winfo_exists():
            self.tabla_frame.destroy()

        w = c.winfo_width()
        h = c.winfo_height()

        if w < 100 or h < 100:
            return

        if self.fondo_original:
            fondo_w, fondo_h = self.fondo_original.size
            escala = min(w / fondo_w, h / fondo_h)

            nuevo_w = int(fondo_w * escala)
            nuevo_h = int(fondo_h * escala)

            try:
                filtro = Image.Resampling.LANCZOS
            except AttributeError:
                filtro = Image.LANCZOS

            fondo_redimensionado = self.fondo_original.resize((nuevo_w, nuevo_h), filtro)
            self.fondo_tk = ImageTk.PhotoImage(fondo_redimensionado)
            self.x_fondo = (w - nuevo_w) // 2
            self.y_fondo = (h - nuevo_h) // 2
            self.nuevo_w = nuevo_w
            self.nuevo_h = nuevo_h

            c.create_image(self.x_fondo, self.y_fondo, image=self.fondo_tk, anchor="nw")
        else:
            self.x_fondo = 0
            self.y_fondo = 0
            self.nuevo_w = w
            self.nuevo_h = h

            c.create_rectangle(0, 0, w, h, fill="#F7D99A", outline="")
            c.create_text(w / 2, h / 2, text="Falta assets/fondo_stats.png", font=self.fuente_pixel(28), fill="black")

        escala_ui = min(self.nuevo_w / 1672, self.nuevo_h / 941)
        usuario = self.controller.usuario_actual.strip()

        if usuario:
            texto_usuario = f"USUARIO: {usuario}"
        else:
            texto_usuario = "USUARIO: SIN SESION"

        c.create_text(
            self.x_fondo + self.nuevo_w * 0.55,
            self.y_fondo + self.nuevo_h * 0.105,
            text=texto_usuario,
            font=self.fuente_pixel(max(10, int(20 * escala_ui))),
            fill="#3A2A18",
            anchor="w"
        )
        self.crear_zona_home()
        self.crear_tabla(escala_ui)
        self.actualizar_stats()

    def crear_zona_home(self):
        c = self.canvas
        x = self.x_fondo + self.nuevo_w * 0.875
        y = self.y_fondo + self.nuevo_h * 0.095
        bw = self.nuevo_w * 0.15
        bh = self.nuevo_h * 0.075

        x1 = x - bw / 2
        y1 = y - bh / 2
        x2 = x + bw / 2
        y2 = y + bh / 2

        tag = "btn_home_stats"
        c.create_rectangle(x1, y1, x2, y2, fill="", outline="", tags=(tag,))
        c.tag_bind(tag, "<Button-1>", lambda event: self.controller.mostrar_pantalla("PantallaHome"))
        c.tag_bind(tag, "<Enter>", lambda event: c.config(cursor="hand2"))
        c.tag_bind(tag, "<Leave>", lambda event: c.config(cursor=""))

    def crear_tabla(self, escala_ui):
        tabla_x = self.x_fondo + self.nuevo_w * 0.50
        tabla_y = self.y_fondo + self.nuevo_h * 0.54
        tabla_w = self.nuevo_w * 0.83
        tabla_h = self.nuevo_h * 0.53

        self.tabla_frame = tk.Frame(self.canvas, bg="#FFF2C8", bd=0, highlightthickness=0)
        self.canvas.create_window(tabla_x, tabla_y, window=self.tabla_frame, width=tabla_w, height=tabla_h)

        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "StatsBody.Treeview",
            font=self.fuente_pixel(max(8, int(14 * escala_ui)), False),
            rowheight=max(22, int(34 * escala_ui)),
            background="#FFF2C8", fieldbackground="#FFF2C8", foreground="#151515",
            borderwidth=0, relief="flat"
        )

        style.map("StatsBody.Treeview", background=[("selected", "#F6C37A")], foreground=[("selected", "#151515")])

        columnas = ("fecha", "hora", "correctas", "incorrectas", "puntaje")
        self.tree = ttk.Treeview(self.tabla_frame, columns=columnas, show="headings", height=12, style="StatsBody.Treeview")

        self.tree.heading("fecha", text="FECHA")
        self.tree.heading("hora", text="HORA")
        self.tree.heading("correctas", text="CORRECTAS")
        self.tree.heading("incorrectas", text="INCORRECTAS")
        self.tree.heading("puntaje", text="PUNTAJE")

        self.tree.column("fecha", width=int(tabla_w * 0.18), anchor="center")
        self.tree.column("hora", width=int(tabla_w * 0.18), anchor="center")
        self.tree.column("correctas", width=int(tabla_w * 0.20), anchor="center")
        self.tree.column("incorrectas", width=int(tabla_w * 0.18), anchor="center")
        self.tree.column("puntaje", width=int(tabla_w * 0.20), anchor="center")

        scrollbar = ttk.Scrollbar(self.tabla_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def actualizar_stats(self):
        if self.tree is None:
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        usuario = self.controller.usuario_actual.strip()

        def formatear_puntaje(valor):
            try:
                texto = str(valor).strip()

                if texto.endswith("%"):
                    return texto

                numero = float(texto)

                if numero <= 1:
                    return f"{int(numero * 100)}%"
                else:
                    return f"{int(numero)}%"
            except Exception:
                return "0%"

        if usuario:
            total_actual = self.controller.respuestas_correctas + self.controller.respuestas_incorrectas
            pct_actual = (self.controller.respuestas_correctas / total_actual) if total_actual > 0 else 0.0
            puntaje_str_actual = f"{int(pct_actual * 100)}%"

            self.tree.insert(
                "",
                tk.END,
                values=(
                    "(En curso)",
                    "Ahora",
                    self.controller.respuestas_correctas,
                    self.controller.respuestas_incorrectas,
                    puntaje_str_actual
                )
            )

        try:
            print("Leyendo historial desde:", gestor_datos.RUTA_SESIONES)
            sesiones = gestor_datos.obtener_sesiones_usuario(usuario)
        except Exception as e:
            self.tree.insert(
                "",
                tk.END,
                values=("Error", "CSV", "-", "-", str(e)[:12])
            )
            return

        if not sesiones:
            self.tree.insert(
                "",
                tk.END,
                values=("Sin historial", "-", "0", "0", "0%")
            )
            return

        for sesion in reversed(sesiones):
            # --- NUEVO: No mostramos duplicada la sesión actual en el historial ---
            if sesion["fecha"] == self.controller.fecha_sesion and sesion["hora"] == self.controller.hora_sesion:
                continue

            self.tree.insert(
                "",
                tk.END,
                values=(
                    sesion["fecha"],
                    sesion["hora"],
                    sesion["respuestas_correctas"],
                    sesion["respuestas_incorrectas"],
                    formatear_puntaje(sesion["puntaje"])
                )
            )

if __name__ == "__main__":
    app = SistemaEducativoApp()
    app.mainloop()
