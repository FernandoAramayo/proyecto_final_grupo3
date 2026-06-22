import cv2
import numpy as np

def ordenar_puntos(puntos):
    puntos = puntos.reshape((4, 2))
    puntos_ordenados = np.zeros((4, 2), dtype="float32")
    suma = puntos.sum(axis=1)
    puntos_ordenados[0] = puntos[np.argmin(suma)]
    puntos_ordenados[2] = puntos[np.argmax(suma)]
    diferencia = np.diff(puntos, axis=1)
    puntos_ordenados[1] = puntos[np.argmin(diferencia)]
    puntos_ordenados[3] = puntos[np.argmax(diferencia)]
    return puntos_ordenados

cap = cv2.VideoCapture(0)

print("Presiona 'q' para salir")

while True:
    ret, frame = cap.read()
    if not ret: break

    gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gris, (5, 5), 0)
    bordes = cv2.Canny(blur, 50, 150)

    contornos, _ = cv2.findContours(bordes.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contornos = sorted(contornos, key=cv2.contourArea, reverse=True)[:5]
    contorno_pizarra = None

    for c in contornos:
        perimetro = cv2.arcLength(c, True)
        aproximacion = cv2.approxPolyDP(c, 0.02 * perimetro, True)
        if len(aproximacion) == 4:
            contorno_pizarra = aproximacion
            break

    if contorno_pizarra is not None:
        cv2.drawContours(frame, [contorno_pizarra], -1, (0, 255, 0), 2)

        puntos_origen = ordenar_puntos(contorno_pizarra)
        ancho, alto = 400, 300
        puntos_destino = np.array([[0, 0], [ancho - 1, 0], [ancho - 1, alto - 1], [0, alto - 1]], dtype="float32")
        matriz = cv2.getPerspectiveTransform(puntos_origen, puntos_destino)
        pizarra_plana = cv2.warpPerspective(frame, matriz, (ancho, alto))

        gris_pizarra = cv2.cvtColor(pizarra_plana, cv2.COLOR_BGR2GRAY)
        
        blur_pizarra = cv2.GaussianBlur(gris_pizarra, (5, 5), 0)

        binarizada = cv2.adaptiveThreshold(
            blur_pizarra, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 15
        )

        kernel_cierre = np.ones((5, 5), np.uint8)
        trazos_unidos = cv2.morphologyEx(binarizada, cv2.MORPH_CLOSE, kernel_cierre)

        kernel_dilatacion = np.ones((3, 3), np.uint8)
        dilatada = cv2.dilate(trazos_unidos, kernel_dilatacion, iterations=1)


        contornos_numeros, _ = cv2.findContours(dilatada, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for c in contornos_numeros:
            x, y, w, h = cv2.boundingRect(c)
            area_caja = w * h
            relacion_aspecto = float(w) / h

            if area_caja < 150:
                cv2.rectangle(pizarra_plana, (x, y), (x + w, y + h), (0, 255, 255), 1)
            else:
                if 0.15 <= relacion_aspecto <= 1.6:
                    cv2.rectangle(pizarra_plana, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    cv2.putText(pizarra_plana, "OK", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                else:
                    cv2.rectangle(pizarra_plana, (x, y), (x + w, y + h), (0, 0, 255), 1)

        cv2.imshow("1. Vista Final (Detecciones)", pizarra_plana)
        cv2.imshow("2. Vision de Maquina (Filtro Interno)", dilatada)

    cv2.imshow("0. Camara Base", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()