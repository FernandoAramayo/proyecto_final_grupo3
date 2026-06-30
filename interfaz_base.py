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

def cargar_imagen_tk(ruta, ancho, alto):
    if not os.path.exists(ruta):
        return None
    img_cv = cv2.imread(ruta)
    if img_cv is not None:
        img_cv = cv2.resize(img_cv, (int(ancho), int(alto)))
        img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        return ImageTk.PhotoImage(image=img_pil)
    return None

class SistemaEducativoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema Educativo Inteligente")
        
        # 1. Obtenemos las dimensiones reales de la pantalla
        self.w = self.winfo_screenwidth()
        self.h = self.winfo_screenheight()
        
        # Factor de escala tomando 1920x1080 como resolución base de diseño
        self.escala = self.w / 1920.0
        
        self.geometry(f"{self.w}x{self.h}")
        self.configure(bg="#E8F4F8")
        
        try:
            self.state('zoomed')
        except tk.TclError:
            self.attributes('-zoomed', True)
            
        style = ttk.Style()
        style.theme_use("clam")
        
        # Estilos adaptables
        font_tree_head = int(28 * self.escala)
        font_tree_row = int(24 * self.escala)
        row_height = int(60 * self.escala)
        
        style.configure("Treeview.Heading", font=('Helvetica', max(12, font_tree_head), 'bold'), background="#45B7D1", foreground="white")
        style.configure("Treeview", font=('Helvetica', max(10, font_tree_row)), rowheight=row_height)
        
        gestor_datos.inicializar_csv()
        
        self.usuario_actual = ""
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
        
    def f_size(self, size):
        """Devuelve un tamaño de fuente proporcional a la pantalla"""
        return max(10, int(size * self.escala))

    def enviar_comando_pico(self, comando):
        if self.puerto_serial and self.puerto_serial.is_open:
            try:
                self.puerto_serial.write((comando + '\n').encode('utf-8'))
            except Exception:
                pass

    def mostrar_pantalla(self, page_name, modo=None):
        frame = self.frames[page_name]
        
        if page_name == "PantallaModo" and modo is not None:
            frame.iniciar_modo(modo)
        elif page_name == "PantallaStats":
            frame.actualizar_stats() 
            
        if page_name in ["PantallaHome", "PantallaInicio", "PantallaStats"]:
            if "PantallaModo" in self.frames:
                self.frames["PantallaModo"].detener_camara()
                
        frame.tkraise()

    def cerrar_sesion(self):
        self.enviar_comando_pico("U")
        if self.usuario_actual:
            total_intentos = self.respuestas_correctas + self.respuestas_incorrectas
            puntaje = (self.respuestas_correctas / total_intentos) if total_intentos > 0 else 0.0
            
            datos_sesion = {
                'nombre_usuario': self.usuario_actual,
                'respuestas_correctas': self.respuestas_correctas,
                'respuestas_incorrectas': self.respuestas_incorrectas,
                'puntaje': round(puntaje, 2),
                'nivel_modo1': self.progreso[1]['nivel'],
                'pregunta_modo1': self.progreso[1]['pregunta'],
                'nivel_modo2': self.progreso[2]['nivel'],
                'pregunta_modo2': self.progreso[2]['pregunta']
            }
            gestor_datos.guardar_sesion(datos_sesion)
            
            self.usuario_actual = ""
            self.respuestas_correctas = 0
            self.respuestas_incorrectas = 0
            self.imagenes_vistas.clear() 
            self.progreso = {1: {'nivel': 1, 'pregunta': 1}, 2: {'nivel': 1, 'pregunta': 1}}
            
        self.mostrar_pantalla("PantallaInicio")

class PantallaInicio(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#E8F4F8")
        self.controller = controller
        
        # Imágenes adaptables
        w_img = self.controller.w * 0.4
        h_img = self.controller.h * 0.35
        
        self.img_inicio = cargar_imagen_tk("assets/inicio.jpg", w_img, h_img)
        if self.img_inicio:
            tk.Label(self, image=self.img_inicio, bg="#E8F4F8").pack(pady=int(40 * self.controller.escala))
        else:
            tk.Label(self, text="[Falta assets/inicio.jpg]", bg="#FFD700", font=("Helvetica", self.controller.f_size(24)), width=40, height=5).pack(pady=40)
        
        tk.Label(self, text="¡Aprende Jugando!", font=("Helvetica", self.controller.f_size(64), "bold"), bg="#E8F4F8", fg="#333333").pack(pady=int(20*self.controller.escala))
        tk.Label(self, text="Ingresa tu nombre para empezar o eliminar:", font=("Helvetica", self.controller.f_size(32)), bg="#E8F4F8").pack(pady=int(20*self.controller.escala))
        
        self.entry_usuario = tk.Entry(self, font=("Helvetica", self.controller.f_size(40)), justify="center", width=20, bd=4, relief="groove")
        self.entry_usuario.pack(pady=int(30*self.controller.escala))
        self.entry_usuario.bind('<Return>', self.iniciar_sesion)
        
        frame_botones_inicio = tk.Frame(self, bg="#E8F4F8")
        frame_botones_inicio.pack(pady=int(40*self.controller.escala))
        
        pad_x = int(30 * self.controller.escala)
        pad_y = int(15 * self.controller.escala)
        tk.Button(frame_botones_inicio, text="ENTRAR", command=self.iniciar_sesion, font=("Helvetica", self.controller.f_size(28), "bold"), bg="#4CAF50", fg="white", padx=pad_x, pady=pad_y, cursor="hand2").grid(row=0, column=0, padx=20)
        tk.Button(frame_botones_inicio, text="ELIMINAR USUARIO", command=self.borrar_perfil, font=("Helvetica", self.controller.f_size(28), "bold"), bg="#F44336", fg="white", padx=pad_x, pady=pad_y, cursor="hand2").grid(row=0, column=1, padx=20)
        
    def iniciar_sesion(self, event=None):
        usuario = self.entry_usuario.get().strip()
        if usuario:
            self.controller.usuario_actual = usuario
            registro_previo = gestor_datos.cargar_datos_usuario(usuario)
            if registro_previo:
                self.controller.progreso[1]['nivel'] = registro_previo['nivel_modo1']
                self.controller.progreso[1]['pregunta'] = registro_previo['pregunta_modo1']
                self.controller.progreso[2]['nivel'] = registro_previo['nivel_modo2']
                self.controller.progreso[2]['pregunta'] = registro_previo['pregunta_modo2']
            self.entry_usuario.delete(0, tk.END)
            self.controller.mostrar_pantalla("PantallaHome")
        else:
            messagebox.showwarning("Falta nombre", "¡Por favor dime cómo te llamas!")

    def borrar_perfil(self):
        usuario = self.entry_usuario.get().strip()
        if not usuario: return
        confirmacion = messagebox.askyesno("Confirmar eliminación", f"¿Estás seguro de que deseas eliminar a '{usuario}'?")
        if confirmacion:
            if gestor_datos.eliminar_usuario(usuario):
                messagebox.showinfo("Éxito", f"El usuario '{usuario}' eliminado correctamente.")
                self.entry_usuario.delete(0, tk.END)
            else:
                messagebox.showerror("Error", f"No se encontró registro para '{usuario}'.")

class PantallaHome(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#E8F4F8")
        self.controller = controller
        
        top_frame = tk.Frame(self, bg="#E8F4F8")
        top_frame.pack(fill="x", pady=int(30 * self.controller.escala), padx=int(50 * self.controller.escala))
        
        pad_x = int(30 * self.controller.escala)
        pad_y = int(15 * self.controller.escala)
        tk.Button(top_frame, text="🚪 Cerrar Sesión", font=("Helvetica", self.controller.f_size(24), "bold"), bg="#757575", fg="white", bd=0, cursor="hand2", padx=pad_x, pady=pad_y, command=self.controller.cerrar_sesion).pack(side="right")
        
        tk.Label(self, text="Elige tu Aventura", font=("Helvetica", self.controller.f_size(72), "bold"), bg="#E8F4F8", fg="#2C3E50").pack(pady=int(50 * self.controller.escala))
        
        frame_botones = tk.Frame(self, bg="#E8F4F8")
        frame_botones.pack(expand=True)
        
        # Botones cuadrados adaptables
        tam_btn = int(self.controller.w * 0.22)
        
        self.img_modo1 = cargar_imagen_tk("assets/modo1.jpg", tam_btn, tam_btn)
        self.img_modo2 = cargar_imagen_tk("assets/modo2.jpg", tam_btn, tam_btn)
        self.img_stats = cargar_imagen_tk("assets/stats.jpg", tam_btn, tam_btn)
        
        pad_btn_x = int(40 * self.controller.escala)
        
        btn_modo1 = tk.Button(frame_botones, command=lambda: self.controller.mostrar_pantalla("PantallaModo", modo=1), cursor="hand2", bd=0, bg="#E8F4F8", activebackground="#E8F4F8")
        if self.img_modo1: btn_modo1.config(image=self.img_modo1)
        else: btn_modo1.config(text="Modo 1", width=15, height=5, bg="#FF6B6B", fg="white", font=("Helvetica", self.controller.f_size(24)))
        btn_modo1.grid(row=0, column=0, padx=pad_btn_x, pady=20)
        tk.Label(frame_botones, text="Modo 1: Pizarra", font=("Helvetica", self.controller.f_size(32), "bold"), bg="#E8F4F8").grid(row=1, column=0, pady=(0, 40))
        
        btn_modo2 = tk.Button(frame_botones, command=lambda: self.controller.mostrar_pantalla("PantallaModo", modo=2), cursor="hand2", bd=0, bg="#E8F4F8", activebackground="#E8F4F8")
        if self.img_modo2: btn_modo2.config(image=self.img_modo2)
        else: btn_modo2.config(text="Modo 2", width=15, height=5, bg="#4ECDC4", fg="white", font=("Helvetica", self.controller.f_size(24)))
        btn_modo2.grid(row=0, column=1, padx=pad_btn_x, pady=20)
        tk.Label(frame_botones, text="Modo 2: Conteo", font=("Helvetica", self.controller.f_size(32), "bold"), bg="#E8F4F8").grid(row=1, column=1, pady=(0, 40))
        
        btn_stats = tk.Button(frame_botones, command=lambda: self.controller.mostrar_pantalla("PantallaStats"), cursor="hand2", bd=0, bg="#E8F4F8", activebackground="#E8F4F8")
        if self.img_stats: btn_stats.config(image=self.img_stats)
        else: btn_stats.config(text="Stats", width=15, height=5, bg="#45B7D1", fg="white", font=("Helvetica", self.controller.f_size(24)))
        btn_stats.grid(row=0, column=2, padx=pad_btn_x, pady=20)
        tk.Label(frame_botones, text="Estadísticas", font=("Helvetica", self.controller.f_size(32), "bold"), bg="#E8F4F8").grid(row=1, column=2, pady=(0, 40))

class PantallaModo(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#ffffff")
        self.controller = controller
        self.modo_actual = None
        self.max_niveles = 5
        self.cap = None
        self.camara_loop = None
        self.imgtk_cam = None 
        self.imgtk_modo2 = None 
        self.respuesta_modo2 = 0 
        
        # Calculamos proporciones para la cámara (Ej: 60% del ancho total de la pantalla)
        self.ancho_camara = int(self.controller.w * 0.6)
        self.alto_camara = int(self.controller.h * 0.55)
        
        self.top_frame = tk.Frame(self, bg="#ffffff")
        self.top_frame.pack(fill="x", pady=int(15 * self.controller.escala), padx=int(40 * self.controller.escala))
        self.lbl_info = tk.Label(self.top_frame, text="", font=("Helvetica", self.controller.f_size(36), "bold"), bg="#ffffff", fg="#333")
        self.lbl_info.pack(side="left")
        
        pad_x = int(30 * self.controller.escala)
        pad_y = int(10 * self.controller.escala)
        tk.Button(self.top_frame, text="🏠 Return to Home", font=("Helvetica", self.controller.f_size(24), "bold"), bg="#FF5252", fg="white", bd=0, cursor="hand2", padx=pad_x, pady=pad_y, command=lambda: self.controller.mostrar_pantalla("PantallaHome")).pack(side="right")
        
        self.juego_frame = tk.Frame(self, bg="#ffffff")
        self.juego_frame.pack(expand=True, fill="both")
        
        self.lbl_pregunta = tk.Label(self.juego_frame, text="", font=("Helvetica", self.controller.f_size(32), "bold"), bg="#ffffff", fg="#2196F3")
        self.lbl_pregunta.pack(pady=(10, 0))
        
        self.lbl_ejercicio = tk.Label(self.juego_frame, text="", font=("Helvetica", self.controller.f_size(100), "bold"), bg="#ffffff", fg="#2C3E50", width=10, height=1)
        self.lbl_imagen_modo2 = tk.Label(self.juego_frame, bg="#ffffff")
        
        self.lbl_camara = tk.Label(self.juego_frame, bg="black", width=self.ancho_camara, height=self.alto_camara)
        self.lbl_camara.pack(pady=int(20 * self.controller.escala))
        
        self.btn_mandar = tk.Button(self.juego_frame, text="MANDAR RESPUESTA", font=("Helvetica", self.controller.f_size(32), "bold"), bg="#2196F3", fg="white", cursor="hand2", padx=pad_x, pady=pad_y, command=self.evaluar_respuesta)
        self.btn_mandar.pack(pady=int(20 * self.controller.escala))

    def iniciar_modo(self, modo):
        self.modo_actual = modo
        self.max_niveles = 5
        self.actualizar_ui_textos()
        self.detener_camara()
        
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.3)
        self.actualizar_camara()
        
    def cargar_imagen_ejercicio(self):
        nivel = self.controller.progreso[self.modo_actual]['nivel']
        carpeta = f"modo2_nivel{nivel}"
        
        if not os.path.exists(carpeta):
            self.lbl_imagen_modo2.configure(image="", text=f"Falta carpeta:\n{carpeta}", font=("Helvetica", self.controller.f_size(32)), width=30, height=5, bg="#F0F0F0")
            self.respuesta_modo2 = 0
            return

        archivos = [f for f in os.listdir(carpeta) if f.lower().endswith(('.jpg', '.png'))]
        archivos_disponibles = [f for f in archivos if f not in self.controller.imagenes_vistas]
        
        if not archivos_disponibles:
            self.lbl_imagen_modo2.configure(image="", text="¡Te quedaste sin imágenes nuevas!", font=("Helvetica", self.controller.f_size(32)), width=30, height=5, bg="#F0F0F0")
            self.respuesta_modo2 = 0
            return

        imagen_elegida = random.choice(archivos_disponibles)
        self.controller.imagenes_vistas.append(imagen_elegida)
        
        try:
            nombre_sin_ext = imagen_elegida.split('.')[0]
            partes = nombre_sin_ext.split('_') 
            categoria = partes[1]
            self.respuesta_modo2 = int(partes[2])
            self.lbl_pregunta.config(text=f"¿Cuántos {categoria} hay en la imagen?")
        except Exception as e:
            self.respuesta_modo2 = 0
            self.lbl_pregunta.config(text="¿Cuántos objetos ves?")

        ruta_completa = os.path.join(carpeta, imagen_elegida)
        img_cv = cv2.imread(ruta_completa)
        if img_cv is not None:
            img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB) 
            img_pil = Image.fromarray(img_rgb)
            
            ancho_caja = int(self.controller.w * 0.6)
            alto_caja = int(self.controller.h * 0.4)
            img_pil.thumbnail((ancho_caja, alto_caja), Image.Resampling.LANCZOS)
            
            fondo = Image.new('RGB', (ancho_caja, alto_caja), "#ffffff")
            x_offset = (ancho_caja - img_pil.width) // 2
            y_offset = (alto_caja - img_pil.height) // 2
            fondo.paste(img_pil, (x_offset, y_offset))
            
            self.imgtk_modo2 = ImageTk.PhotoImage(image=fondo)
            self.lbl_imagen_modo2.configure(image=self.imgtk_modo2, width=ancho_caja, height=alto_caja, text="")

    def actualizar_ui_textos(self):
        nivel = self.controller.progreso[self.modo_actual]['nivel']
        pregunta = self.controller.progreso[self.modo_actual]['pregunta']
        self.lbl_info.config(text=f"Modo {self.modo_actual} | Nivel {nivel}/{self.max_niveles} | Pregunta {pregunta}/3")
        
        pad_dinamico = int(20 * self.controller.escala)
        
        if self.modo_actual == 1:
            self.lbl_imagen_modo2.pack_forget() 
            self.lbl_ejercicio.pack(pady=pad_dinamico, before=self.lbl_camara) 
            self.lbl_pregunta.config(text="Resuelve la siguiente operación:")
            ejercicio = banco_ejercicios.obtener_ejercicio(nivel, pregunta)
            self.lbl_ejercicio.config(text=ejercicio["ecuacion"])
            
        elif self.modo_actual == 2:
            self.lbl_ejercicio.pack_forget() 
            self.lbl_imagen_modo2.pack(pady=pad_dinamico, before=self.lbl_camara) 
            self.cargar_imagen_ejercicio()

    def actualizar_camara(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.convertScaleAbs(frame, alpha=1.0, beta=-50) 
                
                # Aquí se ajusta dinámicamente al tamaño calculado de la cámara
                frame_recorte = cv2.resize(frame, (self.ancho_camara, self.alto_camara))
                img_rgb = cv2.cvtColor(frame_recorte, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(img_rgb)
                self.imgtk_cam = ImageTk.PhotoImage(image=img_pil)
                self.lbl_camara.configure(image=self.imgtk_cam)
            self.camara_loop = self.after(15, self.actualizar_camara)

    def detener_camara(self):
        if self.camara_loop:
            self.after_cancel(self.camara_loop)
            self.camara_loop = None
        if self.cap:
            self.cap.release()
            self.cap = None

    def evaluar_respuesta(self):
        if not self.cap or not self.cap.isOpened(): return
        
        ret, frame = self.cap.read()
        if not ret: return

        if self.modo_actual == 1:
            nivel = self.controller.progreso[self.modo_actual]['nivel']
            pregunta = self.controller.progreso[self.modo_actual]['pregunta']
            ejercicio = banco_ejercicios.obtener_ejercicio(nivel, pregunta)
            respuesta_esperada = int(ejercicio["respuesta"])
        else:
            respuesta_esperada = self.respuesta_modo2

        numero_detectado, confianza, estado = motor_vision.leer_pizarra(
            frame, 
            self.controller.interpreter, 
            self.controller.input_details, 
            self.controller.output_details
        )

        if estado == "NO_PIZARRA":
            messagebox.showinfo("Ups!", "No logro ver la pizarra completa. Asegúrate de mostrar las 4 esquinas a la cámara.")
            return
        elif estado == "NO_NUMEROS":
            messagebox.showinfo("¡Pizarra en blanco!", "Veo la pizarra perfectamente, pero no detecto números. Remarca bien tu respuesta.")
            return

        if numero_detectado == respuesta_esperada and confianza >= 60.0:
            self.controller.respuestas_correctas += 1
            self.controller.enviar_comando_pico("C")
            messagebox.showinfo("¡Correcto!", f"¡Excelente! Leí un {numero_detectado}.")
            self.avanzar_pregunta()
        elif numero_detectado == respuesta_esperada and confianza < 60.0:
            messagebox.showinfo("Casi...", f"Parece un {numero_detectado}, pero no estoy seguro. ¿Puedes remarcarlo y volver a mandar?")
        else:
            if confianza >= 60.0 and numero_detectado < 100:
                self.controller.respuestas_incorrectas += 1
                self.controller.enviar_comando_pico("I")
                messagebox.showerror("Aún no", f"Leí un {numero_detectado}. Esa no es la respuesta. ¡Sigue intentando!")
            else:
                messagebox.showinfo("Trazo dudoso", "Veo trazos confusos, ¿podrías borrar y escribir los números más claros?")

    def avanzar_pregunta(self):
        pregunta_actual = self.controller.progreso[self.modo_actual]['pregunta']
        if pregunta_actual < 3:
            self.controller.progreso[self.modo_actual]['pregunta'] += 1
            self.actualizar_ui_textos() 
        else:
            self.detener_camara()
            self.mostrar_popup_recompensa()

    def mostrar_popup_recompensa(self):
        popup = tk.Toplevel(self)
        popup.title("¡Nivel Terminado!")
        
        pw = int(self.controller.w * 0.4)
        ph = int(self.controller.h * 0.3)
        popup.geometry(f"{pw}x{ph}")
        popup.configure(bg="#FFF9C4")
        
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (pw // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (ph // 2)
        popup.geometry(f"+{x}+{y}")
        
        popup.transient(self.controller)
        popup.grab_set()
        
        tk.Label(popup, text="¡Bien Hecho!", font=("Helvetica", self.controller.f_size(50), "bold"), fg="#FF9800", bg="#FFF9C4").pack(pady=int(40 * self.controller.escala))
        
        nivel_actual = self.controller.progreso[self.modo_actual]['nivel']
        es_ultimo_nivel = (nivel_actual >= self.max_niveles)
        texto_btn = "Finalizar Modo" if es_ultimo_nivel else "Siguiente Nivel"
        
        pad_x = int(30 * self.controller.escala)
        pad_y = int(15 * self.controller.escala)
        tk.Button(popup, text=texto_btn, font=("Helvetica", self.controller.f_size(24), "bold"), bg="#4CAF50", fg="white", padx=pad_x, pady=pad_y, command=lambda: self.avanzar_nivel(popup, es_ultimo_nivel)).pack(pady=20)

    def avanzar_nivel(self, popup, es_ultimo_nivel):
        popup.destroy()
        if not es_ultimo_nivel:
            self.controller.progreso[self.modo_actual]['nivel'] += 1
            self.controller.progreso[self.modo_actual]['pregunta'] = 1
            self.actualizar_ui_textos()
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.3)
            self.actualizar_camara()
        else:
            self.controller.mostrar_pantalla("PantallaHome")

class PantallaStats(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#ffffff")
        self.controller = controller
        
        self.top_frame = tk.Frame(self, bg="#ffffff")
        self.top_frame.pack(fill="x", pady=int(40*self.controller.escala), padx=int(60*self.controller.escala))
        
        self.lbl_titulo = tk.Label(self.top_frame, text="Panel de Estadísticas", font=("Helvetica", self.controller.f_size(48), "bold"), bg="#ffffff", fg="#2C3E50")
        self.lbl_titulo.pack(side="left")
        
        pad_x = int(30 * self.controller.escala)
        pad_y = int(15 * self.controller.escala)
        tk.Button(self.top_frame, text="🏠 Return to Home", font=("Helvetica", self.controller.f_size(24), "bold"), bg="#FF5252", fg="white", bd=0, cursor="hand2", padx=pad_x, pady=pad_y, command=lambda: self.controller.mostrar_pantalla("PantallaHome")).pack(side="right")
        
        frame_tabla = tk.Frame(self, bg="#ffffff")
        frame_tabla.pack(fill="both", expand=True, padx=int(80*self.controller.escala), pady=int(40*self.controller.escala))
        
        columnas = ("fecha", "hora", "correctas", "incorrectas", "puntaje")
        self.tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=20)
        
        self.tree.heading("fecha", text="Fecha")
        self.tree.heading("hora", text="Hora")
        self.tree.heading("correctas", text="Aciertos")
        self.tree.heading("incorrectas", text="Fallos")
        self.tree.heading("puntaje", text="Rendimiento")
        
        col_width = int(self.controller.w * 0.15)
        for col in columnas:
            self.tree.column(col, width=col_width, anchor="center")
        
        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

    def actualizar_stats(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        usuario = self.controller.usuario_actual
        if usuario:
            self.lbl_titulo.config(text=f"Historial de Sesiones: {usuario}")
            
            total_actual = self.controller.respuestas_correctas + self.controller.respuestas_incorrectas
            pct_actual = (self.controller.respuestas_correctas / total_actual) if total_actual > 0 else 0.0
            puntaje_str_actual = f"{int(pct_actual * 100)}%"
            self.tree.insert('', tk.END, values=("(En curso)", "Ahora", self.controller.respuestas_correctas, self.controller.respuestas_incorrectas, puntaje_str_actual))
        else:
            self.lbl_titulo.config(text="Estadísticas Generales")
            
        ruta_csv = os.path.join("data", "sesiones.csv")
            
        try:
            with open(ruta_csv, mode='r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not usuario or row.get('nombre_usuario') == usuario:
                        fecha = row.get('fecha', '-')
                        hora = row.get('hora', '-')
                        aciertos = row.get('respuestas_correctas', '0')
                        fallos = row.get('respuestas_incorrectas', '0')
                        
                        try:
                            puntaje_raw = float(row.get('puntaje', 0))
                            puntaje_str = f"{int(puntaje_raw * 100)}%"
                        except ValueError:
                            puntaje_str = "0%"

                        self.tree.insert('', tk.END, values=(fecha, hora, aciertos, fallos, puntaje_str))
        except FileNotFoundError:
            pass
        except Exception:
            pass

if __name__ == "__main__":
    app = SistemaEducativoApp()
    app.mainloop()