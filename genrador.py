import os
import cv2
import numpy as np
import random

def generar_imagenes_prueba():
    carpetas = ['modo2_nivel1', 'modo2_nivel2']
    categorias = ['autos', 'semaforos', 'autobuses', 'bicicletas', 'letreros']
    
    for carpeta in carpetas:
        os.makedirs(carpeta, exist_ok=True)
        print(f"\n--- Generando imágenes en: {carpeta} ---")
        
        for i in range(1, 21):
            categoria_elegida = random.choice(categorias)
            respuesta = random.randint(1, 6) 
            
            nombre_archivo = f"{i}_{categoria_elegida}_{respuesta}.jpg"
            ruta = os.path.join(carpeta, nombre_archivo)
            
            img = np.ones((300, 400, 3), dtype=np.uint8) * 220 
            
            texto = f"SIMULACION: {respuesta} {categoria_elegida.upper()}"

            cv2.putText(img, texto, (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 50, 200), 2)
            cv2.putText(img, "(Reemplazar por foto real)", (80, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
            
            cv2.imwrite(ruta, img)
            print(f"Creado: {nombre_archivo}")

if __name__ == "__main__":
    generar_imagenes_prueba()
    print("\n¡Listo! Directorios y banco de imágenes generados con éxito.")
