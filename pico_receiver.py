from machine import Pin, PWM
from time import sleep_ms
import sys
import select

def set_up():
    
    green_leds = [Pin(2, Pin.OUT), Pin(3, Pin.OUT), Pin(4, Pin.OUT)]
    red_leds = [Pin(5, Pin.OUT), Pin(6, Pin.OUT), Pin(7, Pin.OUT)]

    buzzer = Pin(8, Pin.OUT)
    servo = PWM(Pin(15))
    servo.freq(50)

    led = Pin("LED", Pin.OUT)
        
    aciertos = 0
    RECOMPENSA_CADA = 5
    buffer_serial = ""


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

    for l in green_leds:
        l.value(1)

    beep(150)

    servo_angle(90)
    sleep_ms(800)

    servo_angle(0)
    sleep_ms(500)

    for l in green_leds:
        l.value(0)

    print("RECOMPENSA_ENTREGADA")


def correcta():
    global aciertos

    aciertos += 1

    print("OK")
    print("ACIERTOS:", aciertos)

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


def incorrecta():
    print("ERROR")
    print("ACIERTOS:", aciertos)

    for _ in range(3):
        for l in red_leds:
            l.value(1)

        buzzer.value(1)
        sleep_ms(250)

        for l in red_leds:
            l.value(0)

        buzzer.value(0)
        sleep_ms(150)


def reset():
    global aciertos

    aciertos = 0
    apagar_todo()
    servo_angle(0)

    print("RESET")
    print("ACIERTOS:", aciertos)


def estado():
    print("ACIERTOS:", aciertos)


def procesar(cmd):
    cmd = cmd.strip().upper()

    if cmd == "":
        return

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

    elif cmd in ["ESTADO", "COUNT", "CONTADOR"]:
        estado()

    else:
        print("COMANDO_INVALIDO")
        incorrecta()


apagar_todo()
servo_angle(0)

print("PICO_2_LISTA")

poll = select.poll()
poll.register(sys.stdin, select.POLLIN)

def main():
    set_up()
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
                
if __name__ = "__main__":
    main()
