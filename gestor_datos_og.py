import os
import csv
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CARPETA_DATA = os.path.join(BASE_DIR, "data")
RUTA_SESIONES = os.path.join(CARPETA_DATA, "sesiones.csv")
RUTA_PROGRESO = os.path.join(CARPETA_DATA, "progreso_usuarios.csv")

CAMPOS_SESIONES = [
    "fecha",
    "hora",
    "nombre_usuario",
    "respuestas_correctas",
    "respuestas_incorrectas",
    "puntaje",
    "nivel_modo1",
    "pregunta_modo1",
    "nivel_modo2",
    "pregunta_modo2"
]

CAMPOS_PROGRESO = [
    "nombre_usuario",
    "nivel_modo1",
    "pregunta_modo1",
    "nivel_modo2",
    "pregunta_modo2",
    "fecha_ultima",
    "hora_ultima"
]


def inicializar_csv():
    os.makedirs(CARPETA_DATA, exist_ok=True)

    if not os.path.exists(RUTA_SESIONES) or os.path.getsize(RUTA_SESIONES) == 0:
        with open(RUTA_SESIONES, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CAMPOS_SESIONES)
            writer.writeheader()

    if not os.path.exists(RUTA_PROGRESO) or os.path.getsize(RUTA_PROGRESO) == 0:
        with open(RUTA_PROGRESO, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CAMPOS_PROGRESO)
            writer.writeheader()


def guardar_sesion(datos):
    inicializar_csv()

    ahora = datetime.now()

    fila = {
        "fecha": ahora.strftime("%Y-%m-%d"),
        "hora": ahora.strftime("%H:%M:%S"),
        "nombre_usuario": datos["nombre_usuario"],
        "respuestas_correctas": datos["respuestas_correctas"],
        "respuestas_incorrectas": datos["respuestas_incorrectas"],
        "puntaje": datos["puntaje"],
        "nivel_modo1": datos["nivel_modo1"],
        "pregunta_modo1": datos["pregunta_modo1"],
        "nivel_modo2": datos["nivel_modo2"],
        "pregunta_modo2": datos["pregunta_modo2"]
    }

    # IMPORTANTE: "a" agrega al final, no borra sesiones antiguas
    with open(RUTA_SESIONES, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS_SESIONES)
        writer.writerow(fila)

    guardar_progreso(datos)


def guardar_progreso(datos):
    inicializar_csv()

    ahora = datetime.now()
    usuario = datos["nombre_usuario"].strip().lower()

    filas = []

    with open(RUTA_PROGRESO, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        filas = list(reader)

    nueva_fila = {
        "nombre_usuario": datos["nombre_usuario"],
        "nivel_modo1": datos["nivel_modo1"],
        "pregunta_modo1": datos["pregunta_modo1"],
        "nivel_modo2": datos["nivel_modo2"],
        "pregunta_modo2": datos["pregunta_modo2"],
        "fecha_ultima": ahora.strftime("%Y-%m-%d"),
        "hora_ultima": ahora.strftime("%H:%M:%S")
    }

    encontrado = False

    for i, fila in enumerate(filas):
        if fila.get("nombre_usuario", "").strip().lower() == usuario:
            filas[i] = nueva_fila
            encontrado = True
            break

    if not encontrado:
        filas.append(nueva_fila)

    with open(RUTA_PROGRESO, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS_PROGRESO)
        writer.writeheader()
        writer.writerows(filas)


def cargar_datos_usuario(usuario):
    inicializar_csv()

    usuario_buscar = usuario.strip().lower()

    # Primero busca el progreso más reciente
    with open(RUTA_PROGRESO, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for fila in reader:
            if fila.get("nombre_usuario", "").strip().lower() == usuario_buscar:
                return {
                    "nivel_modo1": int(fila.get("nivel_modo1", 1)),
                    "pregunta_modo1": int(fila.get("pregunta_modo1", 1)),
                    "nivel_modo2": int(fila.get("nivel_modo2", 1)),
                    "pregunta_modo2": int(fila.get("pregunta_modo2", 1))
                }

    # Si no existe progreso, intenta cargar desde la última sesión guardada
    ultima = None

    with open(RUTA_SESIONES, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for fila in reader:
            if fila.get("nombre_usuario", "").strip().lower() == usuario_buscar:
                ultima = fila

    if ultima:
        return {
            "nivel_modo1": int(ultima.get("nivel_modo1", 1)),
            "pregunta_modo1": int(ultima.get("pregunta_modo1", 1)),
            "nivel_modo2": int(ultima.get("nivel_modo2", 1)),
            "pregunta_modo2": int(ultima.get("pregunta_modo2", 1))
        }

    return None


def eliminar_usuario(usuario):
    inicializar_csv()

    usuario_borrar = usuario.strip().lower()
    eliminado = False

    # Eliminar de sesiones
    with open(RUTA_SESIONES, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        sesiones = list(reader)

    nuevas_sesiones = [
        fila for fila in sesiones
        if fila.get("nombre_usuario", "").strip().lower() != usuario_borrar
    ]

    if len(nuevas_sesiones) != len(sesiones):
        eliminado = True

    with open(RUTA_SESIONES, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS_SESIONES)
        writer.writeheader()
        writer.writerows(nuevas_sesiones)

    # Eliminar de progreso
    with open(RUTA_PROGRESO, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        progresos = list(reader)

    nuevos_progresos = [
        fila for fila in progresos
        if fila.get("nombre_usuario", "").strip().lower() != usuario_borrar
    ]

    if len(nuevos_progresos) != len(progresos):
        eliminado = True

    with open(RUTA_PROGRESO, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS_PROGRESO)
        writer.writeheader()
        writer.writerows(nuevos_progresos)

    return eliminado

def obtener_sesiones_usuario(usuario):
    inicializar_csv()

    usuario_buscar = usuario.strip().lower()
    sesiones = []

    try:
        with open(RUTA_SESIONES, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            for fila in reader:
                nombre_csv = fila.get("nombre_usuario", "").strip().lower()

                if nombre_csv == usuario_buscar:
                    sesiones.append({
                        "fecha": fila.get("fecha", "-"),
                        "hora": fila.get("hora", "-"),
                        "respuestas_correctas": fila.get("respuestas_correctas", "0"),
                        "respuestas_incorrectas": fila.get("respuestas_incorrectas", "0"),
                        "puntaje": fila.get("puntaje", "0")
                    })

    except FileNotFoundError:
        return []

    return sesiones