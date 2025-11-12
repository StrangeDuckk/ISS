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
def HelpWypisywanie():
    print("todo help wypisywanie")

def Tryb_Zaliczeniowy_dzialanie(cmd):
    global TRYB_Zaliczeniowy, TRYB_Testowy
    #Tryb zaliczeniowy: system zaczyna od pozycji lekko pochylonej w stronę czujnika,
    # tak aby kulka zsunęła się do czujnika, min. 10 sekund;
    # po wydaniu komendy regulator ma:
    # # ■ w ≤ 10 s ustawić kulkę na TARGET,
    # # ■ następnie przez 3 s logować błąd i obliczyć średnią z modułu błędu bezwzględnego,
    # # ■ wypisać wynik zaokrąglony do dwóch miejsc po przecinku i zakończyć sterowanie.

    #pochylenie pochylni w strone czujnika i oczekiwanei na komende do startu opdliczania
    print("ZAL | Pochylenie w strone czujnika, kiedy gotowe, nacisnij s")

    kom = ""
    while True:
        kom = input("ZAL | oczekiwanie na komende 's': ")
        if kom == "s" or kom == "S":
            break

    arduino.reset_input_buffer()
    print("OUT | Wysylanie do arduino: s")
    arduino.write(b"s\n")
    arduino.flush()

    print("ZAL | Start : 10 s stabilizacji, 3 s pomiaru bledu..")
    wynik = None
    start_time = time.time()

    while time.time() - start_time < 15: #maksymalnie 15 s na calosc dla unikniecia nieskonczonej petli
        if arduino.in_waiting > 0:
            response = arduino.readline().decode().strip()
            if response:
                print(f"IN | Arduino: {response}")

                #wykrycie konca testu
                if response.startswith("{DONE"):
                    try:
                        wynikStr = response.split(",")[1].replace("}", "")
                        wynik = float(wynikStr)
                    except Exception:
                        wynik = "!BLAD - niewlasciwa wartosc podczas konwersji"
                    break
        #todo zobaczyc time sleep ale nie powinno nic zwalniac programu

    #todo limit 10 s, potem nie ruszanie sie, 3 sekundy zbieranie bledu i obliczenie sredniej bezwzglednej
    #wypisac wynik zaokraglony do dwoch miejsc po przecinku i wyjsc z trybu zaliczeniowego

    print(f"ZAL | zakonczono prodedure z wynikiem: {wynik}")

def Tryb_Zaliczeniowy_funkcja_wprowadzajaca():
    global TRYB_Zaliczeniowy, TRYB_Testowy
    TRYB_Zaliczeniowy = True
    TRYB_Testowy = False


    print("-------- URUCHOMIONO TRYB ZALICZENIOWY ---------")
    print(f"trybzaliczeniowy: {TRYB_Zaliczeniowy}, trybtestowy: {TRYB_Testowy}")
    #wyslanie ramki do pochylni z informacja o wlaczeniu trybu zaliczeniowego: "{ZAL,1}"
    cmd = "{ZAL,1}"

    arduino.reset_input_buffer()
    arduino.reset_output_buffer()
    print(f"OUT| Wyslanie do arduino:     {cmd}")
    arduino.write(cmd.encode())
    arduino.flush()

    #oczekiwanie na ACK:
    ACK_od_Arduino(cmd) #tutaj uruchomienie funkcji Tryb_Zaliczeniowy_dzialanie()

    return "k"

def Tryb_Testowy_funkcja_dzialanie(cmd):
    # komunikacja z arduino do momentu nacisniecia q
    # todo mozliwosc ustawienia kp, ki, kd, distance_point, servo_zero, t rownoczesnie odbierajac wszystko

    print("TEST | zakonczono prodedure")
    pass

def Tryb_Testowy_funkcja_wprowadzajaca():
    global TRYB_Zaliczeniowy, TRYB_Testowy
    TRYB_Zaliczeniowy = False
    TRYB_Testowy = True

    print("-------- URUCHOMIONO TRYB TESTOWY ---------")
    print(f"trybzaliczeniowy: {TRYB_Zaliczeniowy}, trybtestowy: {TRYB_Testowy}")

    # wyslanie ramki do pochylni z informacja o wlaczeniu trybu zaliczeniowego: "{TEST,1}"
    cmd = "{TEST,1}"

    arduino.reset_input_buffer()
    arduino.reset_output_buffer()
    print(f"OUT| Wyslanie do arduino:     {cmd}")
    arduino.write(cmd.encode())
    arduino.flush()

    # oczekiwanie na ACK:
    ACK_od_Arduino(cmd) #tutaj uruchomienie funkcji Tryb_Testowy_funkcja_dzialanie

    return "k"


def InputUzytkownika():
    # wysyłanie danych do Arduino    Podaj predkosc (0-255) do Arduino
    cmd = ""
    while cmd not in ("q", "Q", "h", "H", "z", "Z", "t", "T"):
        cmd = input(
            "========================================\n"
            "Wpisz \n"
            "h lub p dla pomocy,\n"
            "z dla trybu zaliczeniowego,\n"
            "t dla trybu testowego, \n"
            "q zeby zakonczyc:\n$")

    if cmd == "q" or cmd == "Q":
        global TRYB_Testowy, TRYB_Zaliczeniowy
        TRYB_Testowy = False
        TRYB_Zaliczeniowy = False
        return "q"
    elif cmd == "h" or cmd == "H":
        return HelpWypisywanie()
    elif cmd == "z" or cmd == "Z" or cmd == "start":
        return Tryb_Zaliczeniowy_funkcja_wprowadzajaca()
    elif cmd == "t" or cmd == "T" or cmd == "ramka":
        return Tryb_Testowy_funkcja_wprowadzajaca()

# --------- funkcja ACK ---------
def ACK_od_Arduino(cmd):
    global TRYB_Zaliczeniowy, TRYB_Testowy

    start_time = time.time()
    ack_received = False

    while time.time() - start_time < 5:  # 5 sekund
        if arduino.in_waiting > 0:
            response = arduino.readline().decode().strip()
            if response:
                print(f"IN| Arduino: {response}")
                if response == "ACK":
                    ack_received = True
                    break
        time.sleep(0.05)

    if ack_received:
        if TRYB_Zaliczeniowy:
            Tryb_Zaliczeniowy_dzialanie(cmd)
        elif TRYB_Testowy:
            Tryb_Testowy_funkcja_dzialanie(cmd)
    else:
        print("Brak odpowiedzi ACK od Arduino")

# --------- petla main ----------
def main():
    global TRYB_Testowy, TRYB_Zaliczeniowy
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