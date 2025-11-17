# pip install pyserial
# pip install keyboard
import threading
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
    print("-------------------------Help-------------------------------\n"
          "------------------pochylnia / balanser----------------------\n"
          "- T -> Tryb testowy:\n"
          "użytkownik wpisuje T (lub t) aby wejsc do trybu testowego, \n"
          "podczas dzialania trybu testowego moze stroic urzadzenie wpisujac komendy:\n"
          "KP -> edycja kp <float (0.0, 10.0)>, np. KP 2.5\n"
          "KI -> edycja ki <float (0.0, 10.0)>, np. KI 0.02\n"
          "KD -> edycja kd <float (0.0, 10.0)>, np. KD 10.0\n"
          "DIST -> docelowa odleglosc od czujnika <int>, np. DIST 25\n"
          "ZERO -> wartosc 0 dla serwo <int>, np. ZERO 52\n"
          "T -> edycja t <int (100,200)>, np. T 150\n"
          "-------------------------------------------------------------\n"
          "- Z -> Tryb zaliczeniowy:\n"
          "system zaczyna od pozycji lekko pochylonej w stronę czujnika\n"
          "tak aby kulka zsunęła się do czujnika, min. 10 sekundn\n"
          "po wydaniu komendy regulator ma:\n"
          "w ≤ 10 s ustawić kulkę na TARGET,\n"
          "następnie przez 3 s logować błąd i obliczyć średnią z modułu błędu bezwzględnego,\n"
          "wypisać wynik zaokrąglony do dwóch miejsc po przecinku i zakończyć sterowanie.\n"
          "-------------------------------------------------------------\n"
          "- R -> wyslanie ramki\n"
          "Ustawienie wartosci \"na sucho\" \n"
          "KP -> edycja kp <float (0.0, 10.0)>, np. KP 2.5\n"
          "KI -> edycja ki <float (0.0, 10.0)>, np. KI 0.02\n"
          "KD -> edycja kd <float (0.0, 10.0)>, np. KD 10.0\n"
          "DIST -> docelowa odleglosc od czujnika <int>, np. DIST 25\n"
          "ZERO -> wartosc 0 dla serwo <int>, np. ZERO 52\n"
          "T -> edycja t <int (100,200)>, np. T 150\n"
          "-------------------------------------------------------------\n"
          )


def Tryb_Zaliczeniowy_dzialanie():
    global TRYB_Zaliczeniowy, TRYB_Testowy
    #Tryb zaliczeniowy: system zaczyna od pozycji lekko pochylonej w stronę czujnika,
    # tak aby kulka zsunęła się do czujnika, min. 10 sekund;
    # po wydaniu komendy regulator ma:
    # # ■ w ≤ 10 s ustawić kulkę na TARGET,
    # # ■ następnie przez 3 s logować błąd i obliczyć średnią z modułu błędu bezwzględnego,
    # # ■ wypisać wynik zaokrąglony do dwóch miejsc po przecinku i zakończyć sterowanie.

    #pochylenie pochylni w strone czujnika i oczekiwanei na komende do startu opdliczania
    print("ZAL | Pochylenie w strone czujnika, kiedy gotowe, nacisnij s")

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

    print(f"ZAL | zakonczono prodedure z wynikiem: {wynik}")
    TRYB_Zaliczeniowy = False
    TRYB_Testowy = False

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
    ACK_od_Arduino() #tutaj uruchomienie funkcji Tryb_Zaliczeniowy_dzialanie()

    return "k"

def Tryb_Testowy_funkcja_dzialanie():
    # komunikacja z arduino do momentu nacisniecia q
    global TRYB_Testowy, TRYB_Zaliczeniowy

    print("TEST | Sterowanie aktywne, po pomoc wyjdz z trybu \"q\" i wpisz \"h\" dla pomocy")

    stopEvent = threading.Event()

    def nasluch():
        while not stopEvent.is_set():
            response = arduino.readline().decode().strip()
            if response:
                print(f"TEST | Arduino: {response}")

    nasluch_watek = threading.Thread(target=nasluch, daemon=True)
    nasluch_watek.start()

    try:
        while True:
            cmd = input("> ").strip().upper()
            if cmd == "Q":
                arduino.write(b"q\n")
                print("TEST | zakonczono prodecure")

                for i in range(3): #sciaganie ostatnich outputow od arduino, cos jeszcze wysylalo zanim dotarlo "q"
                    response = arduino.readline().decode().strip()
                    if response:
                        print(f"TEST | Arduino: {response}")
                break

            elif any(cmd.startswith(command) for command in ["KP" , "KI", "KD", "DIST", "ZERO", "T"]):
                #KI 3.2
                chars = cmd.split()
                if len(chars) == 2 and chars[1].replace('.', '', 1).isdigit():
                    c = chars[0]
                    v = chars[1]
                    cmdToSend = f"{c} {v}\n"
                    arduino.write(cmdToSend.encode())
                    print(f"TEST | OUT: {cmdToSend}")
                else:
                    print(f"TEST | Niepoprawna komenda")

            else:
                print(f"TEST | komendy: KP, KI, KD, DIST, ZERO, T. format: \"KP 1.0\"")

    except KeyboardInterrupt:
        print("TEST | Except Keyboard Interrupt")
    finally:
        stopEvent.set()
        nasluch_watek.join()


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
    ACK_od_Arduino() #tutaj uruchomienie funkcji Tryb_Testowy_funkcja_dzialanie

    return "k"

def PisanieRamki():
    global TRYB_Zaliczeniowy, TRYB_Testowy
    TRYB_Zaliczeniowy = False
    TRYB_Testowy = False
    print("-------- URUCHOMIONO PISANIE RAMKI ---------")
    print(f"RAM | komendy: KP, KI, KD, DIST, ZERO, T. format: \"KP 1.0\"")

    cmdDoWyslania = "{RAM, "
    while True:
        cmd = input("> ").strip().upper()
        if cmd == "Q":
            print("RAM | zakonczono prodecure pisania ramki")
            break

        elif any(cmd.startswith(command) for command in ["KP", "KI", "KD", "DIST", "ZERO", "T"]):
            # KI 3.2
            chars = cmd.split()
            if len(chars) == 2 and chars[1].replace('.', '', 1).isdigit():
                c = chars[0]
                v = chars[1]
                cmdToSend = f"{c} {v},"
                cmdDoWyslania += cmdToSend
            else:
                print(f"RAM | Niepoprawna komenda, komendy: KP, KI, KD, DIST, ZERO, T. format: \"KP 1.0\"")

        else:
            print(f"RAM | komendy: KP, KI, KD, DIST, ZERO, T. format: \"KP 1.0\"")
    cmdDoWyslania+="\n"
    arduino.write(cmdDoWyslania.encode())
    print(f"TEST | OUT: {cmdDoWyslania.replace('\n', '\\n}')}")

    ACK_od_Arduino()

    return "k"

def InputUzytkownika():
    # wysyłanie danych do Arduino    Podaj predkosc (0-255) do Arduino
    cmd = ""
    while cmd not in ("q", "Q", "h", "H", "z", "Z", "t", "T", "r", "R"):
        cmd = input(
            "========================================\n"
            "Wpisz \n"
            "h lub p dla pomocy,\n"
            "z dla trybu zaliczeniowego,\n"
            "t dla trybu testowego, \n"
            "r dla zmiany wartosci \n"
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
    elif cmd == "t" or cmd == "T":
        return Tryb_Testowy_funkcja_wprowadzajaca()
    elif cmd == "r" or cmd == "R":
        return PisanieRamki()

# --------- funkcja ACK ---------
def ACK_od_Arduino():
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
            Tryb_Zaliczeniowy_dzialanie()
        elif TRYB_Testowy:
            Tryb_Testowy_funkcja_dzialanie()
        else:
            if arduino.in_waiting > 0:
                response = arduino.readline().decode().strip()
                if response:
                    print(f"IN | Arduino: {response}")

                    # # wykrycie konca testu
                    # if response.startswith("{DONE"):
                    #     try:
                    #         wynikStr = response.split(",")[1].replace("}", "")
                    #         wynik = float(wynikStr)
                    #     except Exception:
                    #         wynik = "!BLAD - niewlasciwa wartosc podczas konwersji"
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