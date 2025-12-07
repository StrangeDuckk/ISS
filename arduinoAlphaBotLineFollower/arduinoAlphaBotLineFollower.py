import serial
import serial.tools.list_ports
import time
import sys
import threading
import keyboard
from Logger import Logger

# pip install pyserial
# pip install keyboard

# ------------------------ funkcje laczace -------------------
def WykrywaniePortu():
    porty = serial.tools.list_ports.comports()

    for port in porty:
        if "Arduino" in port.description:
            print("Arduino jest na porcie: ",port.device)
            return port.device

    return None

def PolacznieZArduino(arduino):
    connectedFlag = False
    ponawianieObecne = 0
    while ponawianieObecne < PONAWIANIE_LIMIT and not connectedFlag:
        try:
            # otwarcie portu:
            if not 'arduino' in locals() or arduino.closed:
                arduino = serial.Serial(PORT, BAUDRATE, timeout=1)
                time.sleep(2)

            start_time = time.time()
            while True:
                if arduino.in_waiting > 0:
                    response = arduino.readline().decode().strip()
                    if response:
                        print("Polaczone z Arduino!")
                        print("IN| Arduino:", response)
                        connectedFlag = True
                        break

                if time.time() - start_time > TIMEOUT_CONNECTION:
                    raise TimeoutError("Timeout oczekiwania na odpowiedz Arduino")
                time.sleep(0.05)

        except (serial.SerialException, TimeoutError) as e:
            print(f"Blad polaczenia: {e}")
            ponawianieObecne += 1
            print(f"Proba {ponawianieObecne} z {PONAWIANIE_LIMIT}")
            if 'arduino' in locals() or arduino.is_open:
                arduino.close()
            time.sleep(1)  # krotka pauza przed kolejna proba polaczenia

    if ponawianieObecne >= PONAWIANIE_LIMIT:
        print("Nie udalo sie nawiazac polaczenia z Arduino. Koncze dzialanie")
        sys.exit(1)


#-------------------------logowanie----------------------
log_filename = "log_PythonAplhaBotLineFollower.txt"
sys.stdout = Logger(log_filename)
sys.stderr = sys.stdout
print(f"Logowanie rozpoczete do pliku: {log_filename}")


# ------------------------- stałe ----------------------
PORT = WykrywaniePortu() #wyjsciowo bylo com4
BAUDRATE = 115200
PONAWIANIE_LIMIT = 3 #3 razy program probuje ponowic polaczenie
TIMEOUT_CONNECTION = 100
TIMEOUT_RESPONSE = 100

# ------------ FLAGI --------------
TRYB_JAZDY = False

# -------------------- otwarcie portu ------------------
arduino = serial.Serial(PORT, BAUDRATE, timeout=1)
time.sleep(2)  # krótka pauza na reset Arduino

# ----------------- proba polaczenia z arduino --------------
PolacznieZArduino(arduino)


def SumaKontrolna(ramka):
    #suma kontrolna dla ramek to suma liczb z ramki %256 (zeby bylo na pewno na 8 bitach zapisane)
    suma = 0
    for digit in ramka:
        if digit.isnumeric():
            suma += int(digit)
    return str(suma%256)

# --------- funkcja ACK ---------
def ACK_od_Arduino():
    global TRYB_JAZDY

    start_time = time.time()
    ack_received = False

    while time.time() - start_time < 5:  # 5 sekund
        if arduino.in_waiting > 0:
            response = arduino.readline().decode().strip()
            if response:
                print(f"IN| Arduino: {response}")
                if response.__contains__("ACK"):
                    ack_received = True
                    break
        time.sleep(0.05)

    if ack_received:
        if TRYB_JAZDY:
            print("Uruchomiono tryb jazdy")
            TRYB_JAZDY = False
        else:
            if arduino.in_waiting > 0:
                response = arduino.readline().decode().strip()
                if response:
                    print(f"IN | Arduino: {response}")

    else:
        print("Brak odpowiedzi ACK od Arduino")

def HelpWypisywanie():
    print("-------------------------Help-------------------------------\n"
          "todo\n"
          "S -> predkosc \n"
          "sl -> silnik lewy\n"
          "sp -> silnik prawyn\n"
          )#todo help

def PisanieRamki():
    #todo napisac od nowa, taka jak w zadaniu P1
    global TRYB_JAZDY
    TRYB_JAZDY = False

    print("-------- URUCHOMIONO PISANIE RAMKI ---------")
    print(f"RAM | komendy: S, T, KP, KI, KD, SP, SL | format: \"KP 1.0\" lub \"SL 1\" (Q -> zakoncz pisanie)")

    #todo do zmiany w locie piny na przod tyl

    cmdDoWyslania = ""
    while True:
        cmd = input("> ").strip().upper()
        if cmd == "Q":
            print("RAM | zakonczono prodecure pisania ramki")
            break

        elif any(cmd.startswith(command) for command in ["KP", "KI", "KD", "T", "S", "SL", "SP"]):
            # KI 3.2
            chars = cmd.split()
            if len(chars) == 2 and chars[1].replace('.', '', 1).isdigit():
                c = chars[0]
                v = chars[1]
                cmdToSend = f"{c} {v},"
                cmdDoWyslania += cmdToSend
            else:
                print(f"RAM | Niepoprawna komenda, komendy: S, T, KP, KI, KD, SP, SL | format: \"KP 1.0\" lub \"SL 1\"")

        else:
            print(f"RAM | komendy: S, T, KP, KI, KD, SP, SL | format: \"KP 1.0\" lub \"SL 1\"")
    cmdDoWyslania+="\n"
    arduino.write(cmdDoWyslania.encode())
    print(f"RAM | OUT: {cmdDoWyslania.replace('\n', '\\n}')}")

    ACK_od_Arduino()

    return "k"

def UruchomTrybJazdy():
    global TRYB_JAZDY
    TRYB_JAZDY = True

    arduino.write("START".encode())

    ACK_od_Arduino()

    return "k"

def InputUzytkownika():
    # wysyłanie danych do Arduino    Podaj predkosc (0-255) do Arduino
    global TRYB_JAZDY
    cmd = ""
    while cmd not in ("q", "Q", "h", "H", "p", "P", "r", "R"):
        cmd = input(
            "========================================\n"
            "Wpisz \n"
            "h lub p dla pomocy,\n"
            "p dla startu (default, po resecie po 5 s rozpoczecie kalibracji),\n"
            "r dla zmiany wartosci \n"
            "q zeby zakonczyc:\n$")

    if cmd == "q" or cmd == "Q":
        TRYB_JAZDY = False
        return "q"
    elif cmd == "h" or cmd == "H":
        return HelpWypisywanie()
    elif cmd == "p" or cmd == "P":
        TRYB_JAZDY = True
        return UruchomTrybJazdy()
    elif cmd == "r" or cmd == "R":
        return PisanieRamki()


# --------- petla main ----------
def main():

    global TRYB_JAZDY
    try:
        while True:
            cmd = InputUzytkownika()
            if cmd == 'q':
                break
            if cmd == "h" or cmd == "k":
                continue

            print("\n====================== Kolejna komenda ===================")


    except KeyboardInterrupt:
        print("Zakonczono program.")

    finally:
        arduino.close()
        print("Zamknieto polaczenie.")

# ---- wywolanie funkcji main ----
if __name__ == "__main__":
    main()