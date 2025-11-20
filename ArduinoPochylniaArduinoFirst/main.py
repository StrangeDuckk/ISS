# pip install pyserial
# pip install keyboard
import threading
from unittest import skipIf

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
wynikGlobal = 0.0

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


def Tryb_Zaliczeniowy_dzialanie(kom):
    global TRYB_Zaliczeniowy, TRYB_Testowy, wynikGlobal
    #Tryb zaliczeniowy: system zaczyna od pozycji lekko pochylonej w stronę czujnika,
    # tak aby kulka zsunęła się do czujnika, min. 10 sekund;
    # po wydaniu komendy regulator ma:
    # # ■ w ≤ 10 s ustawić kulkę na TARGET,
    # # ■ następnie przez 3 s logować błąd i obliczyć średnią z modułu błędu bezwzględnego,
    # # ■ wypisać wynik zaokrąglony do dwóch miejsc po przecinku i zakończyć sterowanie.

    #pochylenie pochylni w strone czujnika i oczekiwanei na komende do startu opdliczania
    print("ZAL | Pochylenie w strone czujnika, kiedy gotowe, nacisnij s")

    if kom is None:
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
                        wynik = float(wynikStr)*10
                    except Exception:
                        wynik = "!BLAD - niewlasciwa wartosc podczas konwersji"
                    break

    print(f"ZAL | zakonczono prodedure z wynikiem: {wynik} mm")
    TRYB_Zaliczeniowy = False
    TRYB_Testowy = False
    wynikGlobal = wynik

def Tryb_Zaliczeniowy_funkcja_wprowadzajaca(AutoKom = None):
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
    ACK_od_Arduino(AutoKom) #tutaj uruchomienie funkcji Tryb_Zaliczeniowy_dzialanie()

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

def PisanieRamki(GotowaRamka = None):
    global TRYB_Zaliczeniowy, TRYB_Testowy
    TRYB_Zaliczeniowy = False
    TRYB_Testowy = False

    if GotowaRamka is not None:
        print(f"OUT | {GotowaRamka}")
        arduino.reset_input_buffer()
        arduino.write(GotowaRamka.encode())
        arduino.flush()
        ACK_od_Arduino()
        return

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

def AutomatyczneWyszukiwanieWartosci():
    global TRYB_Zaliczeniowy, TRYB_Testowy, wynikGlobal
    TRYB_Zaliczeniowy = False
    TRYB_Testowy = False

    def testPID(kpPID,kiPID,kdPID):
        global wynikGlobal
        print(f"A| test pid | kp: {kpPID},ki: {kiPID},kd: {kdPID}")
        gotowaRamka = f"{{RAM, KP {kpPID}, KI {kiPID}, KD {kdPID}, DIST {DIST}, ZERO {ZERO}, T {T}}}\n"
        PisanieRamki(GotowaRamka=gotowaRamka)
        Tryb_Zaliczeniowy_funkcja_wprowadzajaca("s")#dla wprowadzenia s, bez czekania na input uzytkownika
        print(f"Wynik: {wynikGlobal}")
        return wynikGlobal

    def frange(start, stop, step):
        #tworzenie zakresu floatow po ktorych ma chodzic program
        count = int(round((stop - start) / step))+1
        return [start + i * step for i in range(count)]

    def przeszukaj(kp_range, ki_range, kd_range):
        wyniki = []
        for Kp in kp_range:
            for Ki in ki_range:
                for Kd in kd_range:
                    result = testPID(Kp,Ki,Kd)
                    if result is not None:
                        wyniki.append((result, Kp, Ki, Kd))
        wyniki.sort(key=lambda x: x[0])
        return wyniki

    # -------- stale ----------
    DIST = 25
    ZERO = 82
    T = 150

    # ------- manipulacyjne -------
    KP = 0.00
    Max_KP = 3.0
    KI = 0.00
    Max_KI = 0.5
    KD = 1.00
    Max_KD = 4.0

    print("=========== AUTOMATYCZNE STROJENIE =============\n")
    #wysylanie ramki bazowej do strojenia
    ramka = f"{{RAM, KP {KP},KI {KI},KD {KD},DIST {DIST}, ZERO {ZERO}, T {T},\n"
    PisanieRamki(GotowaRamka=ramka)

    # def wykonaj Zaliczenie jako -> Tryb_Zaliczeniowy_funkcja_wprowadzajaca("s")

    # Etap 1 --------------- GRUBE SKANOWANIE --------------------
    print("A | ----------- Grube Skanowanie -------------")
    # print(list(frange(0, 8, 0.5)))
    wyniki1 = przeszukaj(
        kd_range=frange(KD, Max_KD, 0.5),
        ki_range=frange(KI, Max_KI, 0.5),
        kp_range=frange(KP, Max_KP, 0.5),
    )

    top5_etap1 = wyniki1[:5]
    print("najlepsze z 1 etapu: ")
    for wynik in top5_etap1:
        print(wynik)

    # Etap 2 --------------- Dokladne skanowanie przy TOP 5 --------------------
    print("A | --------- Dokladne skanowanie przy TOP 5 -----------")
    wyniki2 = []

    for result, KP0, KI0, KD0 in top5_etap1:
        wyniki2 += przeszukaj(
            kp_range=frange(KP0 - 0.5, KP0 + 0.5, 0.1),
            ki_range=frange(KI0 - 0.1, KI0 + 0.1, 0.02),
            kd_range=frange(KD0 - 0.5, KD0 + 0.5, 0.1),
        )

    wyniki2.sort(key=lambda x: x[0])
    top_etap2 = wyniki2[0]
    print("A | najlepszy z 2 etapu:", top_etap2)

    # --------------- ETAP 3 – ultra precyzja ---------------

    print("A | === ETAP 3: Ultra precyzyjne skanowanie ===")
    result, KP0, KI0, KD0 = top_etap2

    wyniki3 = przeszukaj(
        kp_range=frange(KP0 - 0.1, KP0 + 0.1, 0.02),
        ki_range=frange(KI0 - 0.02, KI0 + 0.02, 0.005),
        kd_range=frange(KD0 - 0.1, KD0 + 0.1, 0.02),
    )

    wyniki3.sort(key=lambda x: x[0])
    best3 = wyniki3[0]

    # ----------------- KONIEC ---------------------

    print("A | ===== OSTATECZNY WYNIK =====")
    print(f"Najlepszy błąd: {best3[0]}")
    print(f"KP={best3[1]}, KI={best3[2]}, KD={best3[3]}")
    print("===== KONIEC STROJENIA =====\n")

    return best3


def InputUzytkownika():
    # wysyłanie danych do Arduino    Podaj predkosc (0-255) do Arduino
    cmd = ""
    while cmd not in ("q", "Q", "h", "H", "z", "Z", "t", "T", "r", "R", "a", "A"):
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
    elif cmd == "a" or cmd == "A":
        return AutomatyczneWyszukiwanieWartosci()

# --------- funkcja ACK ---------
def ACK_od_Arduino(AutoKom = None):
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
            Tryb_Zaliczeniowy_dzialanie(AutoKom)
        elif TRYB_Testowy:
            Tryb_Testowy_funkcja_dzialanie()
        else:
            if arduino.in_waiting > 0:
                response = arduino.readline().decode().strip()
                if response:
                    print(f"IN | Arduino: {response}")

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