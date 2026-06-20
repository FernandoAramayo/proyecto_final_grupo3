import cv2
import numpy as np

def preparar_imagen_mnist(recorte):
    h, w = recorte.shape
    dif = abs(h - w)
    top, bottom, left, right = 0, 0, 0, 0
    if h > w:
        left = dif // 2
        right = dif - left
    elif w > h:
        top = dif // 2
        bottom = dif - top
        
    recorte_cuadrado = cv2.copyMakeBorder(recorte, top, bottom, left, right, cv2.BORDER_CONSTANT, value=0)
    margen = int(recorte_cuadrado.shape[0] * 0.15)
    recorte_con_margen = cv2.copyMakeBorder(recorte_cuadrado, margen, margen, margen, margen, cv2.BORDER_CONSTANT, value=0)
    redimensionada = cv2.resize(recorte_con_margen, (28, 28), interpolation=cv2.INTER_AREA)
    redimensionada = cv2.GaussianBlur(redimensionada, (3, 3), 0)
    normalizada = redimensionada.astype('float32') / 255.0
    return np.reshape(normalizada, (1, 28, 28, 1))

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

def leer_pizarra(frame, interpreter, input_details, output_details):
    """
    Procesa el fotograma, aísla la pizarra, encuentra múltiples números,
    los ordena de izquierda a derecha y devuelve la concatenación y confianza.
    Retorna: (numero_entero, confianza_promedio, estado_string)
    """
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

    if contorno_pizarra is None:
        return (None, 0.0, "NO_PIZARRA")

    # Aplanar pizarra
    puntos_origen = ordenar_puntos(contorno_pizarra)
    ancho, alto = 400, 300
    puntos_destino = np.array([[0, 0], [ancho - 1, 0], [ancho - 1, alto - 1], [0, alto - 1]], dtype="float32")
    matriz = cv2.getPerspectiveTransform(puntos_origen, puntos_destino)
    pizarra_plana = cv2.warpPerspective(frame, matriz, (ancho, alto))

    gris_pizarra = cv2.cvtColor(pizarra_plana, cv2.COLOR_BGR2GRAY)
    blur_pizarra = cv2.GaussianBlur(gris_pizarra, (5, 5), 0)
    binarizada = cv2.adaptiveThreshold(blur_pizarra, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 15)
    
    kernel_cierre = np.ones((5, 5), np.uint8)
    trazos_unidos = cv2.morphologyEx(binarizada, cv2.MORPH_CLOSE, kernel_cierre)
    kernel_dilatacion = np.ones((3, 3), np.uint8)
    dilatada = cv2.dilate(trazos_unidos, kernel_dilatacion, iterations=1)

    contornos_numeros, _ = cv2.findContours(dilatada, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    cajas_validas = []
    
    for c in contornos_numeros:
        x, y, w, h = cv2.boundingRect(c)
        area_caja = w * h
        relacion_aspecto = float(w) / h
        if area_caja > 150 and 0.15 <= relacion_aspecto <= 1.6:
            cajas_validas.append((x, y, w, h))

    if not cajas_validas:
        return (None, 0.0, "NO_NUMEROS")

    # ORDENAR DE IZQUIERDA A DERECHA (Para leer números de varias cifras correctamente)
    # Se ordena basándose en la coordenada 'x' de cada caja
    cajas_validas = sorted(cajas_validas, key=lambda b: b[0])
    
    numero_str = ""
    suma_confianza = 0.0

    for (x, y, w, h) in cajas_validas:
        roi_numero = trazos_unidos[y:y+h, x:x+w]
        input_data = preparar_imagen_mnist(roi_numero)
        
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        prediccion = interpreter.get_tensor(output_details[0]['index'])
        
        digito = np.argmax(prediccion[0])
        confianza_digito = np.max(prediccion[0]) * 100
        
        numero_str += str(digito)
        suma_confianza += confianza_digito
        
    confianza_promedio = suma_confianza / len(cajas_validas)
    
    return (int(numero_str), confianza_promedio, "EXITO")