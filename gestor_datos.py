import csv
import os
from datetime import datetime

ARCHIVO_CSV = 'data/sesiones.csv'

def inicializar_csv():
    os.makedirs(os.path.dirname(ARCHIVO_CSV), exist_ok=True)
    if not os.path.exists(ARCHIVO_CSV):
        with open(ARCHIVO_CSV, mode='w', newline='', encoding='utf-8') as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow([
                'nombre_usuario', 'fecha', 'hora',
                'respuestas_correctas', 'respuestas_incorrectas', 'puntaje',
                'nivel_modo1', 'pregunta_modo1',
                'nivel_modo2', 'pregunta_modo2'
            ])
        print("Archivo CSV inicializado correctamente.")

def guardar_sesion(datos_sesion):
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

def cargar_datos_usuario(nombre_usuario):
    if not os.path.exists(ARCHIVO_CSV):
        return None
        
    ultimo_registro = None
    with open(ARCHIVO_CSV, mode='r', encoding='utf-8') as archivo:
        lector = csv.DictReader(archivo)
        for fila in lector:
            if fila['nombre_usuario'].lower() == nombre_usuario.lower():
                ultimo_registro = fila
                
    if ultimo_registro:
        return {
            'nivel_modo1': int(ultimo_registro['nivel_modo1']),
            'pregunta_modo1': int(ultimo_registro['pregunta_modo1']),
            'nivel_modo2': int(ultimo_registro['nivel_modo2']),
            'pregunta_modo2': int(ultimo_registro['pregunta_modo2'])
        }
    return None 

def eliminar_usuario(nombre_usuario):
    if not os.path.exists(ARCHIVO_CSV):
        return False
    
    filas_actualizadas = []
    usuario_encontrado = False
    campos = []

    with open(ARCHIVO_CSV, mode='r', encoding='utf-8') as archivo:
        lector = csv.DictReader(archivo)
        campos = lector.fieldnames
        for fila in lector:
            if fila['nombre_usuario'].lower() == nombre_usuario.lower():
                usuario_encontrado = True
            else:
                filas_actualizadas.append(fila)
                
    if usuario_encontrado:
        with open(ARCHIVO_CSV, mode='w', newline='', encoding='utf-8') as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=campos)
            escritor.writeheader()
            escritor.writerows(filas_actualizadas)
        print(f"Todos los registros de {nombre_usuario} fueron eliminados.")
        return True
        
    return False
