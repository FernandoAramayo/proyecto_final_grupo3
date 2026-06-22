import os
import cv2
import numpy as np
import random

def generar_imagenes_prueba():
    carpetas = ['modo2_nivel1', 'modo2_nivel2']
    categorias = ['autos', 'semaforos', 'autobuses', 'bicicletas', 'letreros']
    
    for carpeta in carpetas:
        # 1. Crear el directorio si no existe
        os.makedirs(carpeta, exist_ok=True)
        print(f"\n--- Generando imágenes en: {carpeta} ---")
        
        # 2. Generar 20 imágenes por carpeta
        for i in range(1, 21):
            categoria_elegida = random.choice(categorias)
            respuesta = random.randint(1, 6) # El niño tendrá que contar entre 1 y 6 objetos
            
            # Formato mágico: ID_categoria_RESPUESTA.jpg
            nombre_archivo = f"{i}_{categoria_elegida}_{respuesta}.jpg"
            ruta = os.path.join(carpeta, nombre_archivo)
            
            # 3. Crear una imagen falsa (Fondo gris claro) de 400x300 píxeles
            img = np.ones((300, 400, 3), dtype=np.uint8) * 220 
            
            # 4. Ponerle un texto para saber qué simula ser
            texto = f"SIMULACION: {respuesta} {categoria_elegida.upper()}"
            # Centrar un poco el texto
            cv2.putText(img, texto, (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 50, 200), 2)
            cv2.putText(img, "(Reemplazar por foto real)", (80, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
            
            # 5. Guardar la imagen
            cv2.imwrite(ruta, img)
            print(f"Creado: {nombre_archivo}")

if __name__ == "__main__":
    generar_imagenes_prueba()
    print("\n¡Listo! Directorios y banco de imágenes generados con éxito.")