import tkinter as tk
from tkinter import messagebox
import cv2
import gestor_datos  
import banco_ejercicios

class SistemaEducativoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema Educativo Inteligente")
        self.geometry("950x750")
        self.configure(bg="#E8F4F8")
        
        # Inicializar el archivo CSV al arrancar la aplicación
        gestor_datos.inicializar_csv()
        
        # Variables globales de la sesión activa
        self.usuario_actual = ""
        self.respuestas_correctas = 0
        self.respuestas_incorrectas = 0
        
        # Diccionario para controlar el progreso de ambos modos de manera independiente
        self.progreso = {
            1: {'nivel': 1, 'pregunta': 1},
            2: {'nivel': 1, 'pregunta': 1}
        }
        
        # Contenedor principal para el intercambio de pantallas
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
        if self.usuario_actual:
            total_intentos = self.respuestas_correctas + self.respuestas_incorrectas
            puntaje = (self.respuestas_correctas / total_intentos) if total_intentos > 0 else 0.0
            
            # Estructurar paquete de datos para persistencia en CSV
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
            
            # Limpiar el estado de la aplicación para el siguiente usuario
            self.usuario_actual = ""
            self.respuestas_correctas = 0
            self.respuestas_incorrectas = 0
            self.progreso = {
                1: {'nivel': 1, 'pregunta': 1},
                2: {'nivel': 1, 'pregunta': 1}
            }
            
        self.mostrar_pantalla("PantallaInicio")


class PantallaInicio(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#E8F4F8")
        self.controller = controller
        
        tk.Label(self, text="[Espacio para Imagen Decorativa .PNG]", bg="#FFD700", width=40, height=10).pack(pady=40)
        tk.Label(self, text="¡Aprende Jugando!", font=("Helvetica", 28, "bold"), bg="#E8F4F8", fg="#333333").pack(pady=10)
        tk.Label(self, text="Ingresa tu nombre para empezar o eliminar:", font=("Helvetica", 14), bg="#E8F4F8").pack(pady=10)
        
        self.entry_usuario = tk.Entry(self, font=("Helvetica", 16), justify="center", width=20, bd=2, relief="groove")
        self.entry_usuario.pack(pady=10)
        self.entry_usuario.bind('<Return>', self.iniciar_sesion)
        
        # Contenedor para alinear los botones horizontalmente
        frame_botones_inicio = tk.Frame(self, bg="#E8F4F8")
        frame_botones_inicio.pack(pady=20)
        
        tk.Button(frame_botones_inicio, text="ENTRAR", command=self.iniciar_sesion, font=("Helvetica", 14, "bold"), 
                  bg="#4CAF50", fg="white", padx=20, pady=5, cursor="hand2").grid(row=0, column=0, padx=10)
                  
        tk.Button(frame_botones_inicio, text="ELIMINAR USUARIO", command=self.borrar_perfil, font=("Helvetica", 14, "bold"), 
                  bg="#F44336", fg="white", padx=15, pady=5, cursor="hand2").grid(row=0, column=1, padx=10)
        
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
                print(f"Progreso recuperado para {usuario}.")
            else:
                print(f"Nuevo perfil creado para {usuario}.")

            self.entry_usuario.delete(0, tk.END)
            self.controller.mostrar_pantalla("PantallaHome")
        else:
            messagebox.showwarning("Falta nombre", "¡Por favor dime cómo te llamas!")

    def borrar_perfil(self):
        usuario = self.entry_usuario.get().strip()
        if not usuario:
            messagebox.showwarning("Falta nombre", "¡Escribe el nombre del usuario que deseas borrar en el recuadro!")
            return
            
        # Alerta de confirmación de seguridad
        confirmacion = messagebox.askyesno(
            "Confirmar eliminación", 
            f"¿Estás seguro de que deseas eliminar a '{usuario}'?\nEsta acción borrará todo su historial permanentemente."
        )
        
        if confirmacion:
            fue_eliminado = gestor_datos.eliminar_usuario(usuario)
            if fue_eliminado:
                messagebox.showinfo("Éxito", f"El usuario '{usuario}' e historial eliminados correctamente.")
                self.entry_usuario.delete(0, tk.END)
            else:
                messagebox.showerror("Error", f"No se encontró ningún registro para el usuario '{usuario}'.")


class PantallaHome(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#E8F4F8")
        self.controller = controller
        
        top_frame = tk.Frame(self, bg="#E8F4F8")
        top_frame.pack(fill="x", pady=10, padx=20)
        
        tk.Button(top_frame, text="🚪 Cerrar Sesión", font=("Helvetica", 11, "bold"), bg="#757575", fg="white", bd=0,
                  cursor="hand2", padx=15, pady=5, command=self.controller.cerrar_sesion).pack(side="right")
        
        tk.Label(self, text="Elige tu Aventura", font=("Helvetica", 26, "bold"), bg="#E8F4F8", fg="#2C3E50").pack(pady=20)
        
        frame_botones = tk.Frame(self, bg="#E8F4F8")
        frame_botones.pack(expand=True)
        
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
        self.imgtk = None 
        
        self.top_frame = tk.Frame(self, bg="#ffffff")
        self.top_frame.pack(fill="x", pady=10, padx=20)
        
        self.lbl_info = tk.Label(self.top_frame, text="", font=("Helvetica", 16, "bold"), bg="#ffffff", fg="#333")
        self.lbl_info.pack(side="left")
        
        tk.Button(self.top_frame, text="🏠 Return to Home", font=("Helvetica", 11, "bold"), bg="#FF5252", fg="white", bd=0,
                  cursor="hand2", padx=15, pady=4, command=lambda: self.controller.mostrar_pantalla("PantallaHome")).pack(side="right")
        
        self.juego_frame = tk.Frame(self, bg="#ffffff")
        self.juego_frame.pack(expand=True, fill="both")
        
        self.lbl_ejercicio = tk.Label(self.juego_frame, text="", font=("Helvetica", 48, "bold"), 
                                      bg="#ffffff", fg="#2C3E50", width=15, height=2)
        self.lbl_ejercicio.pack(pady=20)
        
        self.lbl_camara = tk.Label(self.juego_frame, bg="black", width=400, height=300)
        self.lbl_camara.pack(pady=10)
        
        self.btn_mandar = tk.Button(self.juego_frame, text="MANDAR RESPUESTA", font=("Helvetica", 14, "bold"), 
                                    bg="#2196F3", fg="white", cursor="hand2", padx=20, pady=5, command=self.evaluar_respuesta)
        self.btn_mandar.pack(pady=15)

    def iniciar_modo(self, modo):
        self.modo_actual = modo
        self.max_niveles = 5 if modo == 1 else 2
        
        self.actualizar_ui_textos()
        self.detener_camara()
        self.cap = cv2.VideoCapture(0)
        self.actualizar_camara()
        
    def actualizar_ui_textos(self):
        nivel = self.controller.progreso[self.modo_actual]['nivel']
        pregunta = self.controller.progreso[self.modo_actual]['pregunta']
        
        # Actualizar el texto superior
        txt = f"Modo {self.modo_actual} | Nivel {nivel}/{self.max_niveles} | Pregunta {pregunta}/3"
        self.lbl_info.config(text=txt)
        
        # Cargar el ejercicio correspondiente si estamos en el Modo 1
        if self.modo_actual == 1:
            ejercicio = banco_ejercicios.obtener_ejercicio(nivel, pregunta)
            self.lbl_ejercicio.config(text=ejercicio["ecuacion"])
        elif self.modo_actual == 2:
            # Aquí luego irá la lógica para cargar las imágenes del Modo 2
            self.lbl_ejercicio.config(text="[Imagen a contar]")

    def actualizar_camara(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.resize(frame, (400, 300))
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
        # Simulación de respuesta correcta transitoria
        self.controller.respuestas_correctas += 1 
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
        popup.geometry("350x200")
        popup.configure(bg="#FFF9C4")
        
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 175
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 100
        popup.geometry(f"+{x}+{y}")
        
        popup.transient(self.controller)
        popup.grab_set()
        
        tk.Label(popup, text="¡Bien Hecho!", font=("Helvetica", 24, "bold"), fg="#FF9800", bg="#FFF9C4").pack(pady=20)
        
        nivel_actual = self.controller.progreso[self.modo_actual]['nivel']
        es_ultimo_nivel = (nivel_actual >= self.max_niveles)
        texto_btn = "Finalizar Modo" if es_ultimo_nivel else "Siguiente Nivel"
        
        btn_ok = tk.Button(popup, text=texto_btn, font=("Helvetica", 12, "bold"), bg="#4CAF50", fg="white",
                           command=lambda: self.avanzar_nivel(popup, es_ultimo_nivel))
        btn_ok.pack(pady=10)

    def avanzar_nivel(self, popup, es_ultimo_nivel):
        popup.destroy()
        
        if not es_ultimo_nivel:
            self.controller.progreso[self.modo_actual]['nivel'] += 1
            self.controller.progreso[self.modo_actual]['pregunta'] = 1
            self.actualizar_ui_textos()
            
            self.cap = cv2.VideoCapture(0)
            self.actualizar_camara()
        else:
            self.controller.mostrar_pantalla("PantallaHome")


class PantallaStats(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#ffffff")
        self.controller = controller
        
        self.top_frame = tk.Frame(self, bg="#ffffff")
        self.top_frame.pack(fill="x", pady=10, padx=20)
        
        tk.Label(self.top_frame, text="Panel de Estadísticas", font=("Helvetica", 20, "bold"), bg="#ffffff", fg="#2C3E50").pack(side="left")
        
        tk.Button(self.top_frame, text="🏠 Return to Home", font=("Helvetica", 11, "bold"), bg="#FF5252", fg="white", bd=0,
                  cursor="hand2", padx=15, pady=4, command=lambda: self.controller.mostrar_pantalla("PantallaHome")).pack(side="right")
        
        tk.Label(self, text="[Imagen de Gráfica .PNG]", bg="#A3E4D7", width=60, height=20).pack(pady=40)
        tk.Label(self, text="* Aquí se desplegarán las métricas de aciertos y rendimiento.", 
                 font=("Helvetica", 11, "italic"), bg="#ffffff", fg="#666").pack()


# Bloque de arranque principal de la aplicación (debe estar al ras del archivo)
if __name__ == "__main__":
    app = SistemaEducativoApp()
    app.mainloop()