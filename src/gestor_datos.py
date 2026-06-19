import csv
import os
from datetime import datetime

ARCHIVO_CSV = 'data/sesiones.csv'

def inicializar_csv():
    """Crea el archivo CSV y los encabezados si no existe."""
    os.makedirs(os.path.dirname(ARCHIVO_CSV), exist_ok=True)
    
    if not os.path.exists(ARCHIVO_CSV):
        with open(ARCHIVO_CSV, mode='w', newline='', encoding='utf-8') as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow([
                'nombre_usuario', 
                'fecha', 
                'hora',
                'respuestas_correctas', 
                'respuestas_incorrectas', 
                'puntaje',
                'nivel_modo1', 
                'pregunta_modo1',
                'nivel_modo2', 
                'pregunta_modo2'
            ])
        print("Archivo CSV inicializado correctamente.")

def guardar_sesion(datos_sesion):
    """
    Guarda una nueva fila con los datos de la sesión.
    Recibe un diccionario con los datos.
    """
    with open(ARCHIVO_CSV, mode='a', newline='', encoding='utf-8') as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow([
            datos_sesion.get('nombre_usuario', 'Desconocido'),
            datos_sesion.get('fecha', datetime.now().strftime("%Y-%m-%d")),
            datos_sesion.get('hora', datetime.now().strftime("%H:%M:%S")),
            datos_sesion.get('respuestas_correctas', 0),
            datos_sesion.get('respuestas_incorrectas', 0),
            datos_sesion.get('puntaje', 0.0),
            datos_sesion.get('nivel_modo1', 1),
            datos_sesion.get('pregunta_modo1', 1),
            datos_sesion.get('nivel_modo2', 1),
            datos_sesion.get('pregunta_modo2', 1)
        ])
        print(f"Sesión de {datos_sesion.get('nombre_usuario')} guardada con éxito.")