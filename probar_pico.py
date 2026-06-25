import serial
import time

PORT = "/dev/ttyACM0"
BAUDRATE = 115200

def enviar(ser, comando):
    ser.write((comando + "\n").encode())
    time.sleep(0.2)

    while ser.in_waiting > 0:
        respuesta = ser.readline().decode(errors="ignore").strip()
        if respuesta:
            print("Pico:", respuesta)


def main():
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=1)
        time.sleep(2)

        print("Conectado a la Pico 2")
        print()
        print("Comandos disponibles:")
        print("c      -> respuesta correcta")
        print("i      -> respuesta incorrecta")
        print("r      -> recompensa manual")
        print("reset  -> reiniciar contador")
        print("estado -> ver contador")
        print("stop   -> apagar LEDs y buzzer")
        print("q      -> salir")
        print()

        while True:
            cmd = input("Enviar: ").strip().lower()

            if cmd == "q":
                print("Saliendo...")
                break

            elif cmd == "c":
                enviar(ser, "C")

            elif cmd == "i":
                enviar(ser, "I")

            elif cmd == "r":
                enviar(ser, "R")

            elif cmd == "reset":
                enviar(ser, "RESET")

            elif cmd == "estado":
                enviar(ser, "ESTADO")

            elif cmd == "stop":
                enviar(ser, "STOP")

            else:
                print("Comando no valido")

        ser.close()

    except serial.SerialException as e:
        print("Error al conectar con la Pico:")
        print(e)
        print()
        print("Revisa:")
        print("- Que la Pico este conectada por USB")
        print("- Que el puerto sea /dev/ttyACM0")
        print("- Que Thonny este cerrado")
        print("- Que tengas permisos para usar el puerto serial")


if __name__ == "__main__":
    main()