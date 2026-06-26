BANCO_MODO_1 = {
    1: [ # Sumas y Restas Básicas
        {"ecuacion": "8 + 5 = ?", "respuesta": "13"},
        {"ecuacion": "15 - 7 = ?", "respuesta": "8"},
        {"ecuacion": "12 + 14 = ?", "respuesta": "26"}
    ],
    2: [ # Multiplicaciones
        {"ecuacion": "4 x 6 = ?", "respuesta": "24"},
        {"ecuacion": "7 x 8 = ?", "respuesta": "56"},
        {"ecuacion": "9 x 3 = ?", "respuesta": "27"}
    ],
    3: [ # Divisiones Exactas
        {"ecuacion": "20 ÷ 4 = ?", "respuesta": "5"},
        {"ecuacion": "36 ÷ 6 = ?", "respuesta": "6"},
        {"ecuacion": "45 ÷ 9 = ?", "respuesta": "5"}
    ],
    4: [ # Lógica: El Número Faltante
        {"ecuacion": "5 + ? = 12", "respuesta": "7"},
        {"ecuacion": "? - 4 = 6", "respuesta": "10"},
        {"ecuacion": "3 x ? = 15", "respuesta": "5"}
    ],
    5: [ # Operaciones Combinadas Simples
        {"ecuacion": "2 x 3 + 4 = ?", "respuesta": "10"},
        {"ecuacion": "10 - 2 x 4 = ?", "respuesta": "2"},
        {"ecuacion": "15 ÷ 3 + 2 = ?", "respuesta": "7"}
    ]
}

def obtener_ejercicio(nivel, pregunta_num):
    """
    Devuelve un diccionario con la 'ecuacion' y la 'respuesta'
    basado en el nivel (1-5) y el número de pregunta (1-3).
    """
    indice = pregunta_num - 1
    
    if nivel not in BANCO_MODO_1:
        return {"ecuacion": "FIN", "respuesta": ""}
    if indice < 0 or indice >= len(BANCO_MODO_1[nivel]):
        return {"ecuacion": "FIN", "respuesta": ""}
        
    return BANCO_MODO_1[nivel][indice]
