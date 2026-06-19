import tkinter as tk
from tkinter import messagebox
import cv2

class SistemaEducativoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema Educativo Inteligente")
        self.geometry("950x750")
        self.configure(bg="#E8F4F8")
        
        # Variables de sesión
        self.usuario_actual = ""
        self.nivel_actual = 1
        self.pregunta_actual = 1
        self.respuestas_correctas = 0
        
        # Contenedor principal
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

    def mostrar_pantalla(self, page_name, modo=None):
        frame = self.frames[page_name]
        
        if page_name == "PantallaModo" and modo is not None:
            frame.iniciar_modo(modo)
        elif page_name in ["PantallaHome", "PantallaInicio", "PantallaStats"]:
            if "PantallaModo" in self.frames:
                self.frames["PantallaModo"].detener_camara()
                
        frame.tkraise()

    def cerrar_sesion(self):
        self.usuario_actual = ""
        self.mostrar_pantalla("PantallaInicio")

class PantallaInicio(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#E8F4F8")
        self.controller = controller
        
        # Para usar una imagen real sin Pillow, usa:
        # self.img_deco = tk.PhotoImage(file="tu_imagen.png")
        # tk.Label(self, image=self.img_deco, bg="#E8F4F8").pack(pady=40)
        
        tk.Label(self, text="[Espacio para Imagen Decorativa .PNG]", bg="#FFD700", width=40, height=10).pack(pady=40)
        
        tk.Label(self, text="¡Aprende Jugando!", font=("Helvetica", 28, "bold"), bg="#E8F4F8", fg="#333333").pack(pady=10)
        tk.Label(self, text="Ingresa tu nombre para empezar:", font=("Helvetica", 14), bg="#E8F4F8").pack(pady=10)
        
        self.entry_usuario = tk.Entry(self, font=("Helvetica", 16), justify="center", width=20, bd=2, relief="groove")
        self.entry_usuario.pack(pady=10)
        self.entry_usuario.bind('<Return>', self.iniciar_sesion)
        
        tk.Button(self, text="ENTRAR", command=self.iniciar_sesion, font=("Helvetica", 14, "bold"), 
                  bg="#4CAF50", fg="white", padx=20, pady=5, cursor="hand2").pack(pady=20)
        
    def iniciar_sesion(self, event=None):
        usuario = self.entry_usuario.get().strip()
        if usuario:
            self.controller.usuario_actual = usuario
            self.entry_usuario.delete(0, tk.END)
            self.controller.mostrar_pantalla("PantallaHome")
        else:
            messagebox.showwarning("Falta nombre", "¡Por favor dime cómo te llamas!")

class PantallaHome(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#E8F4F8")
        self.controller = controller
        
        # --- EL BOTÓN CERRAR SESIÓN AHORA SOLO EXISTE AQUÍ ---
        top_frame = tk.Frame(self, bg="#E8F4F8")
        top_frame.pack(fill="x", pady=10, padx=20)
        
        tk.Button(top_frame, text="🚪 Cerrar Sesión", font=("Helvetica", 11, "bold"), bg="#757575", fg="white", bd=0,
                  cursor="hand2", padx=15, pady=5, command=self.controller.cerrar_sesion).pack(side="right")
        
        tk.Label(self, text="Elige tu Aventura", font=("Helvetica", 26, "bold"), bg="#E8F4F8", fg="#2C3E50").pack(pady=20)
        
        frame_botones = tk.Frame(self, bg="#E8F4F8")
        frame_botones.pack(expand=True)
        
        # Cuando tengas tus imágenes .PNG, cámbialas así:
        # self.img_btn1 = tk.PhotoImage(file="boton_modo1.png")
        # btn_modo1 = tk.Button(..., image=self.img_btn1, ...)
        
        btn_modo1 = tk.Button(frame_botones, text="[Imagen\nModo 1]", font=("Helvetica", 14), width=15, height=7, bg="#FF6B6B", fg="white",
                              command=lambda: self.controller.mostrar_pantalla("PantallaModo", modo=1))
        btn_modo1.grid(row=0, column=0, padx=30, pady=10)
        tk.Label(frame_botones, text="Modo 1: Pizarra", font=("Helvetica", 14, "bold"), bg="#E8F4F8").grid(row=1, column=0, pady=(0, 20))
        
        btn_modo2 = tk.Button(frame_botones, text="[Imagen\nModo 2]", font=("Helvetica", 14), width=15, height=7, bg="#4ECDC4", fg="white",
                              command=lambda: self.controller.mostrar_pantalla("PantallaModo", modo=2))
        btn_modo2.grid(row=0, column=1, padx=30, pady=10)
        tk.Label(frame_botones, text="Modo 2: Conteo", font=("Helvetica", 14, "bold"), bg="#E8F4F8").grid(row=1, column=1, pady=(0, 20))
        
        btn_stats = tk.Button(frame_botones, text="[Imagen\nEstadísticas]", font=("Helvetica", 14), width=15, height=7, bg="#45B7D1", fg="white",
                              command=lambda: self.controller.mostrar_pantalla("PantallaStats"))
        btn_stats.grid(row=0, column=2, padx=30, pady=10)
        tk.Label(frame_botones, text="Estadísticas", font=("Helvetica", 14, "bold"), bg="#E8F4F8").grid(row=1, column=2, pady=(0, 20))

class PantallaModo(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#ffffff")
        self.controller = controller
        self.modo_actual = None
        self.max_niveles = 5
        self.cap = None
        self.camara_loop = None
        self.imgtk = None # Referencia nativa para evitar que el recolector de basura borre el video
        
        # --- ZONA SUPERIOR (SOLO RETURN TO HOME) ---
        self.top_frame = tk.Frame(self, bg="#ffffff")
        self.top_frame.pack(fill="x", pady=10, padx=20)
        
        self.lbl_info = tk.Label(self.top_frame, text="", font=("Helvetica", 16, "bold"), bg="#ffffff", fg="#333")
        self.lbl_info.pack(side="left")
        
        tk.Button(self.top_frame, text="🏠 Return to Home", font=("Helvetica", 11, "bold"), bg="#FF5252", fg="white", bd=0,
                  cursor="hand2", padx=15, pady=4, command=lambda: self.controller.mostrar_pantalla("PantallaHome")).pack(side="right")
        
        # --- ZONA JUEGO ---
        self.juego_frame = tk.Frame(self, bg="#ffffff")
        self.juego_frame.pack(expand=True, fill="both")
        
        # Imagen del ejercicio (Placeholder nativo)
        self.lbl_ejercicio = tk.Label(self.juego_frame, text="[Imagen del Ejercicio .PNG]", bg="#F0F0F0", width=50, height=8)
        self.lbl_ejercicio.pack(pady=10)
        
        # Feed de la cámara web
        self.lbl_camara = tk.Label(self.juego_frame, bg="black", width=400, height=300)
        self.lbl_camara.pack(pady=10)
        
        self.btn_mandar = tk.Button(self.juego_frame, text="MANDAR RESPUESTA", font=("Helvetica", 14, "bold"), 
                                    bg="#2196F3", fg="white", cursor="hand2", padx=20, pady=5, command=self.evaluar_respuesta)
        self.btn_mandar.pack(pady=15)

    def iniciar_modo(self, modo):
        self.modo_actual = modo
        self.controller.nivel_actual = 1
        self.controller.pregunta_actual = 1
        self.controller.respuestas_correctas = 0
        self.max_niveles = 5 if modo == 1 else 2
        
        self.actualizar_ui_textos()
        self.detener_camara()
        self.cap = cv2.VideoCapture(0)
        self.actualizar_camara()
        
    def actualizar_ui_textos(self):
        txt = f"Modo {self.modo_actual} | Nivel {self.controller.nivel_actual}/{self.max_niveles} | Pregunta {self.controller.pregunta_actual}/3"
        self.lbl_info.config(text=txt)

    def actualizar_camara(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.resize(frame, (400, 300))
                # TRUCO SIN PILLOW: Codificamos el frame en memoria a formato PPM (compatible nativo con Tkinter)
                ret_encode, buffer = cv2.imencode('.ppm', frame)
                if ret_encode:
                    self.imgtk = tk.PhotoImage(data=buffer.tobytes())
                    self.lbl_camara.configure(image=self.imgtk)
                    
            self.camara_loop = self.after(15, self.actualizar_camara)

    def detener_camara(self):
        if self.camara_loop:
            self.after_cancel(self.camara_loop)
            self.camara_loop = None
        if self.cap:
            self.cap.release()
            self.cap = None

    def evaluar_respuesta(self):
        self.controller.respuestas_correctas += 1 # Simula acierto
        
        if self.controller.pregunta_actual < 3:
            self.controller.pregunta_actual += 1
            self.actualizar_ui_textos()
        else:
            self.detener_camara()
            self.mostrar_popup_recompensa()

    def mostrar_popup_recompensa(self):
        popup = tk.Toplevel(self)
        popup.title("¡Nivel Terminado!")
        popup.geometry("350x200")
        popup.configure(bg="#FFF9C4")
        
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 175
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 100
        popup.geometry(f"+{x}+{y}")
        
        popup.transient(self.controller)
        popup.grab_set()
        
        tk.Label(popup, text="¡Bien Hecho!", font=("Helvetica", 24, "bold"), fg="#FF9800", bg="#FFF9C4").pack(pady=20)
        tk.Label(popup, text=f"Aciertos: {self.controller.respuestas_correctas} de 3", 
                 font=("Helvetica", 14), bg="#FFF9C4").pack(pady=10)
        
        # Determinar si es el último nivel para cambiar el texto del botón y la acción
        es_ultimo_nivel = (self.controller.nivel_actual >= self.max_niveles)
        texto_btn = "Finalizar Modo" if es_ultimo_nivel else "Siguiente Nivel"
        
        btn_ok = tk.Button(popup, text=texto_btn, font=("Helvetica", 12, "bold"), bg="#4CAF50", fg="white",
                           command=lambda: self.avanzar_nivel(popup, es_ultimo_nivel))
        btn_ok.pack(pady=10)

    def avanzar_nivel(self, popup, es_ultimo_nivel):
        popup.destroy()
        
        if not es_ultimo_nivel:
            self.controller.nivel_actual += 1
            self.controller.pregunta_actual = 1
            self.controller.respuestas_correctas = 0
            self.actualizar_ui_textos()
            
            self.cap = cv2.VideoCapture(0)
            self.actualizar_camara()
        else:
            # RETORNO AUTOMÁTICO A HOME
            self.controller.mostrar_pantalla("PantallaHome")

class PantallaStats(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#ffffff")
        self.controller = controller
        
        # --- ZONA SUPERIOR (SOLO RETURN TO HOME) ---
        self.top_frame = tk.Frame(self, bg="#ffffff")
        self.top_frame.pack(fill="x", pady=10, padx=20)
        
        tk.Label(self.top_frame, text="Panel de Estadísticas", font=("Helvetica", 20, "bold"), bg="#ffffff", fg="#2C3E50").pack(side="left")
        
        tk.Button(self.top_frame, text="🏠 Return to Home", font=("Helvetica", 11, "bold"), bg="#FF5252", fg="white", bd=0,
                  cursor="hand2", padx=15, pady=4, command=lambda: self.controller.mostrar_pantalla("PantallaHome")).pack(side="right")
        
        # --- CONTENIDO ---
        tk.Label(self, text="[Imagen de Gráfica .PNG]", bg="#A3E4D7", width=60, height=20).pack(pady=40)
        
        tk.Label(self, text="* Aquí se desplegarán las métricas de aciertos y rendimiento.", 
                 font=("Helvetica", 11, "italic"), bg="#ffffff", fg="#666").pack()

if __name__ == "__main__":
    app = SistemaEducativoApp()
    app.mainloop()