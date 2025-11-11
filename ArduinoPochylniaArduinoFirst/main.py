# pip install pyserial
# pip install keyboard
import serial
import serial.tools.list_ports
import time
import sys


# -------- funkcje laczace automatycznie z arduino --------
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

# -------- stale -----------
BAUDRATE = 9600
PONAWIANIE_LIMIT = 3
TIMEOUT_CONNECTION = 100

# ------- PORT I POLACZENIE ---------
PORT = WykrywaniePortu()
arduino = serial.Serial(PORT, BAUDRATE, timeout=1)
time.sleep(2) #pauza na reset arduino

PolacznieZArduino(arduino)

# ---------- FLAGI -----------
TRYB_Testowy = False
TRYB_Zaliczeniowy = False

# --------- metody komunikacyjne -------------
def InputUzytkownika():
    return "q"

# --------- petla main ----------
def main():
    global TRYB_Testowy, TRYB_Zaliczeniowy
    try:
        while True:
            cmd = InputUzytkownika()
            if cmd == 'q':
                break
            if cmd == "h":
                continue
            if cmd == "p":
                print("Ta ramka nie wprowadzi zmian, pomijam.")
                continue

            arduino.reset_input_buffer()
            arduino.reset_output_buffer()
            print(f"OUT| Wyslanie do arduino:     {cmd.replace("\n", "\\n")}")
            arduino.write(cmd.encode())
            arduino.flush()

            print("\n====================== Kolejna komenda ===================")



    except KeyboardInterrupt:
        print("Zakonczono program.")

    finally:
        arduino.close()
        print("Zamknieto polaczenie.")


# ---- wywolanie funkcji main ----
if __name__ == "__main__":
    main()

#todo
# - help
# - Zaimplementujcie co najmniej poniższe polecenia i odpowiedzi:
# 1. Ustawienie odległości od czujnika
# 2. Ustawienie Kp, Ki, Kd (float).
# 3. Ustawienie wartości zero serwomechanizmu.
# 4. Uruchomienie trybu testowego do strojenia.
# 5. Tryb zaliczeniowy: system zaczyna od pozycji lekko pochylonej w stronę czujnika, tak aby kulka zsunęła się do czujnika, min. 10 sekund lub dalsza część po komendzie;
# po wydaniu komendy regulator ma:
# ■ w ≤ 10 s ustawić kulkę na TARGET,
# ■ następnie przez 3 s logować błąd i obliczyć średnią z modułu błędu bezwzględnego,
# ■ wypisać wynik zaokrąglony do dwóch miejsc po przecinku i zakończyć sterowanie.