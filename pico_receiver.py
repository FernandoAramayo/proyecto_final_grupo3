from machine import Pin, PWM, I2C
from time import sleep_ms
import sys
import select
import ssd1306

green_leds = [Pin(2, Pin.OUT), Pin(3, Pin.OUT), Pin(4, Pin.OUT)]
red_leds = [Pin(5, Pin.OUT), Pin(6, Pin.OUT), Pin(7, Pin.OUT)]

buzzer = Pin(8, Pin.OUT)

servo = PWM(Pin(15))
servo.freq(50)

led = Pin("LED", Pin.OUT)

oled = None

try:
    i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=200000)
    devices = i2c.scan()
    print("I2C Scan:", devices)

    if 60 in devices:
        oled = ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)
        print("OLED_OK")
    else:
        print("OLED_NO_DETECTADA")

except OSError as e:
    oled = None
    print("OLED_ERROR:", e)

aciertos = 0
RECOMPENSA_CADA = 5
buffer_serial = ""


def mostrar_oled(linea1="", linea2="", linea3="", linea4=""):
    if oled is None:
        print("OLED:", linea1, linea2, linea3, linea4)
        return

    try:
        oled.fill(0)
        oled.text(linea1[:16], 0, 0)
        oled.text(linea2[:16], 0, 16)
        oled.text(linea3[:16], 0, 32)
        oled.text(linea4[:16], 0, 48)
        oled.show()

    except OSError as e:
        print("OLED_WRITE_ERROR:", e)


def apagar_todo():
    for l in green_leds:
        l.value(0)

    for l in red_leds:
        l.value(0)

    buzzer.value(0)
    led.value(0)


def beep(tiempo=200):
    buzzer.value(1)
    sleep_ms(tiempo)
    buzzer.value(0)


def servo_angle(angle):
    min_us = 500
    max_us = 2500
    us = min_us + (angle / 180) * (max_us - min_us)
    duty = int((us / 20000) * 65535)
    servo.duty_u16(duty)


def recompensa():
    print("RECOMPENSA")
    mostrar_oled("RECOMPENSA", "Entregando...", "Aciertos: " + str(aciertos))

    for l in green_leds:
        l.value(1)

    beep(150)

    servo_angle(90)
    sleep_ms(150)

    servo_angle(0)
    sleep_ms(500)

    for l in green_leds:
        l.value(0)

    print("RECOMPENSA_ENTREGADA")
    mostrar_oled("Premio listo", "Aciertos: " + str(aciertos), "Esperando...")


def correcta():
    global aciertos

    aciertos += 1

    print("OK")
    print("ACIERTOS:", aciertos)

    mostrar_oled("CORRECTO!", "Aciertos: " + str(aciertos), "Premio cada " + str(RECOMPENSA_CADA))

    for _ in range(2):
        for l in green_leds:
            l.value(1)
            sleep_ms(120)
            l.value(0)

    for l in green_leds:
        l.value(1)

    beep(100)
    sleep_ms(400)

    for l in green_leds:
        l.value(0)

    if aciertos % RECOMPENSA_CADA == 0:
        recompensa()
    else:
        mostrar_oled("Sistema listo", "Aciertos: " + str(aciertos), "Esperando cmd")


def incorrecta():
    print("ERROR")
    print("ACIERTOS:", aciertos)

    mostrar_oled("INCORRECTO", "Aciertos: " + str(aciertos), "Intenta otra vez")

    for _ in range(3):
        for l in red_leds:
            l.value(1)

        buzzer.value(1)
        sleep_ms(250)

        for l in red_leds:
            l.value(0)

        buzzer.value(0)
        sleep_ms(150)

    mostrar_oled("Sistema listo", "Aciertos: " + str(aciertos), "Esperando cmd")


def reset():
    global aciertos

    aciertos = 0
    apagar_todo()
    servo_angle(0)

    print("RESET")
    print("ACIERTOS:", aciertos)

    mostrar_oled("RESET", "Aciertos: 0", "Sistema listo")


def estado():
    print("ACIERTOS:", aciertos)
    mostrar_oled("ESTADO", "Aciertos: " + str(aciertos), "Premio cada " + str(RECOMPENSA_CADA))


def procesar(cmd):
    cmd = cmd.strip().upper()

    if cmd == "":
        return

    print("COMANDO:", cmd)

    if cmd in ["C", "CORRECTO", "OK", "1"]:
        correcta()

    elif cmd in ["I", "INCORRECTO", "ERROR", "0"]:
        incorrecta()

    elif cmd in ["R", "RECOMPENSA", "PREMIO"]:
        recompensa()

    elif cmd == "RESET":
        reset()

    elif cmd == "STOP":
        apagar_todo()
        print("STOP_OK")
        mostrar_oled("STOP", "Actuadores OFF", "Aciertos: " + str(aciertos))

    elif cmd in ["ESTADO", "COUNT", "CONTADOR"]:
        estado()

    else:
        print("COMANDO_INVALIDO")
        mostrar_oled("Comando invalido", cmd[:16])
        incorrecta()


apagar_todo()
servo_angle(0)

print("PICO_2_LISTA")
mostrar_oled("PICO 2 LISTA", "Aciertos: 0", "Esperando cmd")

for _ in range(3):
    led.value(1)
    sleep_ms(150)
    led.value(0)
    sleep_ms(150)

poll = select.poll()
poll.register(sys.stdin, select.POLLIN)

while True:
    if poll.poll(50):
        char = sys.stdin.read(1)

        if char == "\n" or char == "\r":
            if buffer_serial != "":
                procesar(buffer_serial)
                buffer_serial = ""
        else:
            buffer_serial += char

            if len(buffer_serial) > 40:
                buffer_serial = ""
