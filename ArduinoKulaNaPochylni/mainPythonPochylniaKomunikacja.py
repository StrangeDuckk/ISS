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
log_filename = "log_mainPythonPochylniaKomunikacja.txt"
sys.stdout = Logger(log_filename)
sys.stderr = sys.stdout
print(f"Logowanie rozpoczete do pliku: {log_filename}")

# ------------------------- stałe ----------------------
PORT = WykrywaniePortu() #wyjsciowo bylo com4
BAUDRATE = 9600
PONAWIANIE_LIMIT = 3 #3 razy program probuje ponowic polaczenie
TIMEOUT_CONNECTION = 100
TIMEOUT_RESPONSE = 100

# -------------------- otwarcie portu ------------------
arduino = serial.Serial(PORT, BAUDRATE, timeout=1)
time.sleep(2)  # krótka pauza na reset Arduino

# ----------------- proba polaczenia z arduino --------------
PolacznieZArduino(arduino)

# ---------- uruchamianie kolejkowania i osobnego watku na nasluchiwanie awaryjnego stopu --------
emergency_stop_triggered = False
arduino_is_working = False

def ListenForStopKeyboardInterrupt(arduino):
    global emergency_stop_triggered
    while True:
        if keyboard.is_pressed('s') and not emergency_stop_triggered and arduino_is_working:
            emergency_stop_triggered = True
            print("! AWARYJNE ZATRZYMANIE !")
            try:
                ramka_stop = "{TASK, S2, SK1,\n}"
                arduino.write(ramka_stop.encode())
                arduino.flush()
                print("OUT| ! AWARYJNE ZATRZYMANIE !, wyslano: " + ramka_stop.replace("\n", "\\n"))
                print("(Nacisnij ENTER aby kontynuowac) $")
            except Exception as e:
                print("Blad wysylania STOP:",e)
            time.sleep(1)

stopListenerThread = threading.Thread(target=ListenForStopKeyboardInterrupt, args=(arduino,), daemon=True)
stopListenerThread.start()

# ===================================================================================================
# ----------------- funkcje -----------------

def SumaKontrolna(ramka):
    #suma kontrolna dla ramek to suma liczb z ramki %256 (zeby bylo na pewno na 8 bitach zapisane)
    suma = 0
    for digit in ramka:
        if digit.isnumeric():
            suma += int(digit)
    return str(suma%256)

def SprawdzenieAckOdArduino(arduino):
    #sprawdzenie czy Arduino wyslalo otrzymalo cala ramke
    for proba in range(1, PONAWIANIE_LIMIT):
        print(f"Oczekiwanie na ACK od Arduino, proba: {proba}/{PONAWIANIE_LIMIT}")

        start_time = time.time()
        while time.time() - start_time < TIMEOUT_RESPONSE:
            if arduino.in_waiting > 0:
                response = arduino.readline().decode().strip().replace("\n", "\\n")
                if response:
                    if response.startswith("{ACK"):
                        print("IN| Arduino, ACK:", response, " odsylam ACK2")
                        ACK_Odeslanie(arduino)
                        return "ACK"
                    elif response.startswith("{NACK"):
                        print("IN| Arduino, NACK:", response)
                        return "NACK"
            time.sleep(0.05)

        print(f"!TIMEOUT - Brak ACK od Arduino w probie: {proba}, pozostalo prob: {PONAWIANIE_LIMIT-proba}")

        if proba < PONAWIANIE_LIMIT:
            time.sleep(0.5)

    print(f"!TIMEOUT - Brak ACK od Arduino po {PONAWIANIE_LIMIT} probach")
    return "close"

def ACK_Odeslanie(arduino):
    #odeslanie drugiego ack do arduino zeby wykonalo polecenie
    ack_ramka = "{ACK2\n}"
    arduino.write(ack_ramka.encode())
    print("OUT| ACK2 do Arduino:", ack_ramka.replace("\n", "\\n"))

# ------------------------ funkcje robota --------------------------
#todo arduino caly czas zwraca odpis z czujnikow, komunikacje zakancza ramka {Done,..}

def FunkcjaPochylnia_Kp():
    #potegowanie bledu okolo 3.0
    cmd = ""
    while True:
        cmd = input("P| Podaj Kp - potege bledu (float, zakres: (0,10)) $")

        if cmd.__contains__("q"):
            return "q"

        try:
            val = float(cmd)  # próba konwersji na float
        except ValueError:
            print("!P| Podaj liczbę (float)")
            continue

        if 0 <= val <= 10:
            # zaokraglenie do dwoch miejsc po przecinku
            return f"P{val:.2f}, "
        else:
            print("!P| Podaj liczbę (float) z zakresu (0-10)")


def FunkcjaPochylnia_Ki():
    #zapis historyczny bledu okolo 0.5
    cmd = ""
    while True:
        cmd = input("I| Podaj Ki - potege bledu (float, zakres: (0,10)) $")

        if cmd.__contains__("q"):
            return "q"

        try:
            val = float(cmd)  # próba konwersji na float
        except ValueError:
            print("!I| Podaj liczbę (float)")
            continue

        if 0 <= val <= 10:
            # zaokraglenie do dwoch miejsc po przecinku
            return f"I{val:.2f}, "
        else:
            print("!I| Podaj liczbę (float) z zakresu (0-10)")


def FunkcjaPochylnia_Kd():
    # zapis historyczny bledu okolo 0.5
    cmd = ""
    while True:
        cmd = input("D| Podaj Kd - potege roznicy pomiedzy bledami, jak szybko ma sie 'poprawic' (float, zakres: (0,10)) $")

        if cmd.__contains__("q"):
            return "q"

        try:
            val = float(cmd)  # próba konwersji na float
        except ValueError:
            print("!D| Podaj liczbę (float)")
            continue

        if 0 <= val <= 10:
            # zaokraglenie do dwoch miejsc po przecinku
            return f"D{val:.2f}, "
        else:
            print("!D| Podaj liczbę (float) z zakresu (0-10)")

def FunkcjaPochylnia_B():
    #pobranie obecnej odleglosci z czujnika przeliczone na cm
    #todo przeliczenie na cm
    #todo zwrot jako cm i jako rzeczywista wartosc
    cmd = ""
    while cmd not in ("0","1"):
        cmd = input("B| Czy podac bierzacy odczyt z sonaru (jesli 0, komenda zostanie pomineta)? (1=Tak,0=Nie)? (1/0): $")
    if cmd == "1":
        return "B1, "
    else:
        return "N"

def FunkcjaPochylnia_A():
    #automatyczne pobieranie odleglosci z B i wstawianie jej jako output do C
    return "C"+str(17) #todo automatycznie pobieranie B instant i wysylanie w ramce C

def FunkcjaPochylnia_C():
#ustawienie zadanej odleglosci jako target
    while True:
        cmd = input(
            "C| Podaj docelowa odleglosc kulki od czujnika (uzyj funkcji B jednoczesnie trzymajac kulke w oczekiwanej pozycji koncowej) (10,30) $")

        if cmd.__contains__("q"):
            return "q"

        try:
            val = float(cmd)  # próba konwersji na float
        except ValueError:
            print("!C| Podaj liczbę (float)")
            continue

        if 10 <= val <= 30:
            # zaokraglenie do dwoch miejsc po przecinku
            return f"C{val:.2f}, "
        else:
            print("!C| Podaj liczbę (float) z zakresu (10-30)")

def FunkcjaPochylnia_E():
#ustawienie wartosci 0 dla serwo z ograniczeniem zakresow serwa
    while True:
        cmd = input(
            "E| Podaj pozycje 0 dla serwa (kat od 0 do 180*) $")

        if cmd.__contains__("q"):
            return "q"

        if not cmd.isdigit():
            print("!E| Podaj liczbe")
            continue
        if 0 <= int(cmd) <= 180:#todo jesli serwo 360 zmienic zakres
            return "E" + str(cmd) + ", "
        else:
            print("!E| Podaj liczbe calkowita z zakresu (0-180)")


def FunkcjaPochylnia_T():
#ustawienie zadanej odleglosci jako target
    while True:
        cmd = input(
            "T| Podaj czas ile milisekund ma trwac jedno przejscie petli (100,200) $")

        if cmd.__contains__("q"):
            return "q"

        if not cmd.isnumeric():
            print("!T| Podaj liczbe")
            continue
        if 100 <= int(cmd) <= 200:
            return "T" + str(cmd) + ", "
        else:
            print("!T| Podaj liczbe calkowita z zakresu (100-200)")


def PisanieRamki():
    # przykladowa ramka: {TASK, M10, R-15, 7, /n}
    print(" -------- Pisanie Ramki do wiadomosci:------")
    print("Dostepne funkcje robota: \n"
          "P - Kp -> potegowanie bledu (0,10)\n"
          "I - Ki -> ilosc zapisy historycznego bledu (0,10)\n"
          "D - Kd -> potegowanie roznicy pomiedzy ostatnim a obecnym bledem, jak szybko ma reagowac (0,10)\n"
          "E -> ustawienie punktu 0 dla servo (0-180)\n"
          "T -> dlugosc trwania jednego kroku petli w milisekundach (100 - 200)\n"
          "| B -> odczytanie bierzacej odleglosci z sonaru (1 - tak, 0 - pominiecie)\n"
          "| C -> ustawienie docelowej odleglosci pilki od sonaru, zalecane, uzyc najpierw B i przepisac wartosc (10,30)\n"
          "| Dla B i C uzytego razem, docelowa odleglosc bedzie ustawiona na odleglosc z sonaru\n"
          "Q - zakoncz pisanie ramki")
    zadania = input("Wpisz LITERY odpowiadajace funkcjom ktorych chcesz uzyc (np. RvTSi)\n$")
    ramka = "{TASK, "
    wykonywalnaRamka = False
    licznikKomend = 0
    czyBBylo = False
    if zadania == "q" or zadania == "Q" or zadania == "" or zadania == "\n":
        return "p"
    else:
        if zadania.__contains__("P") or zadania.__contains__("p"):
            cmd = FunkcjaPochylnia_Kp()
            if cmd.__contains__("q") and not wykonywalnaRamka:
                wykonywalnaRamka = False
            else:
                ramka += cmd
                wykonywalnaRamka = True
                licznikKomend+=1
        if zadania.__contains__("I") or zadania.__contains__("i"):
            cmd = FunkcjaPochylnia_Ki()
            if cmd.__contains__("q") and not wykonywalnaRamka:
                wykonywalnaRamka = False
            else:
                ramka += cmd
                wykonywalnaRamka = True
                licznikKomend+=1
        if zadania.__contains__("D") or zadania.__contains__("d"):
            cmd = FunkcjaPochylnia_Kd()
            if cmd.__contains__("q") and not wykonywalnaRamka:
                wykonywalnaRamka = False
            else:
                ramka += cmd
                wykonywalnaRamka = True
                licznikKomend+=1
        if zadania.__contains__("E") or zadania.__contains__("e"):
            cmd = FunkcjaPochylnia_E()
            if cmd.__contains__("q") and not wykonywalnaRamka:
                wykonywalnaRamka = False
            else:
                ramka += cmd
                wykonywalnaRamka = True
                licznikKomend+=1
        if zadania.__contains__("T") or zadania.__contains__("t"):
            cmd = FunkcjaPochylnia_T()
            if cmd.__contains__("q") and not wykonywalnaRamka:
                wykonywalnaRamka = False
            else:
                ramka += cmd
                wykonywalnaRamka = True
                licznikKomend+=1
        if zadania.__contains__("B") or zadania.__contains__("b"):
            cmd = FunkcjaPochylnia_B()
            if cmd == "N" and not wykonywalnaRamka:
                wykonywalnaRamka = False
            elif not cmd.__contains__("N"):
                ramka += cmd
                wykonywalnaRamka = True
                czyBBylo = True
            # N - jesli samo tylko BN to przejsc do kolejnego wpisywania ramki po wypisaniu komunikatu
        if zadania.__contains__("C") or zadania.__contains__("c"):
            #todo jesli uzyte B w tej samej ramce, ustawienie automatyczne
            cmd = FunkcjaPochylnia_C()
            if cmd.__contains__("q") and not wykonywalnaRamka:
                wykonywalnaRamka = False
            else:
                if not czyBBylo:
                    ramka += cmd
                    wykonywalnaRamka = True
                    licznikKomend+=1
                else:
                    FunkcjaPochylnia_A()


    if wykonywalnaRamka == False:
        return "p" #np ktos dal B0 tylko, takiej ramki nei oplaca sie wysylac

    ramka += "SK"+SumaKontrolna(ramka)+",\n}"
    return ramka

#TODO KONFIGURACJA JAKO TRYB ZALICZENIOWY
#todo funkcja -> uruchomienie trybu zaliczeniowego, bez zmian czujnikow komenda START
"""
Tryb zaliczeniowy: system zaczyna od pozycji lekko pochylonej w stronę czujnika, tak aby kulka zsunęła się do czujnika, min. 10 sekund lub dalsza część po komendzie;
po wydaniu komendy regulator ma:
■ w ≤ 10 s ustawić kulkę na TARGET,
■ następnie przez 3 s logować błąd i obliczyć średnią z modułu błędu bezwzględnego,
■ wypisać wynik zaokrąglony do dwóch miejsc po przecinku i zakończyć sterowanie.

Procedura oddania / test zaliczeniowy
1. Kalibracja (poza oceną).
2. Start: egzaminator wydaje START przy pochylni lekko przechylonej w stronę czujnika.
3. Faza 1 (≤ 10 s): kulka ma dotrzeć i ustalić się na TARGET.
4. Faza 2 (3 s): system liczy MAE:
○ MAE = średnia z |błąd próbkowania| co ten sam okres, co pętla PID.
5. Punkt zero (TARGET): ogłoszony indywidualnie dla konkretnego stanowiska (sprzętu). Jeżeli system nie osiągnie i nie utrzyma celu w 10 s (oczywiste rozbujanie/niestabilność), część „wynikowa” (10 pkt) = 0
"""
def PochylniaZaliczenie():
    #przykladowa ramka: {ZAL, SK0 ,"\n"}
    #todo suma MAE
    return "{ZAL, SK0, \n}"

def HelpWypisywanie():
    #todo napisac H od nowa
    print("====== Alpha bot, obsluga aplikacji komunikacyjnej =====")
    print("= tryb testowy jest domyslnym trybem =")
    print("Dostepne ramki: \n"
          "konfiguracyjna - konfiguracja sterowania robota, ustawienie pinow wejscia na silnikach i predkosci pelnego obrotu kola np:\n"
          " {KONFIG, R0, L1, PE200, LE0, SK3 ,'\\n'}\n"
          " KONFIG - typ ramki, \n"
          " R0/L1 - czy wymina kierunku silnika prawego/lewego (1-tak,0-nie),\n"
          " PE200/LE0 - ustawienie predkosci pelnego obrotu kola dla enkodera prawego/lewego (>0-tak, 0-bez zmian)\n"
          "aby prawidlowo ustawic predkosc enkoderow nalezy wyslac ramke z E, nastepnie przekrecic kazde kolo o pelny obrot\n"
          "nastepnie ponownie wyslac ramke E (tylko E) i potem ustawic w ramce konfiguracyjnej np PE20,LE19\n"
          "\nFunkcyjna - robot wykonuje zadany zestaw funkcji, np ruch o x cm albo odczyt z czujnikow\n"
          " {TASK, M10, R-90, V100, T5, S1, B1, I1, E1, SK20,'\\n'}"
          " TASK - typ ramki")
    print(" M - move - ruch o zadana odleglosc w cm (dodatnia - przod, ujemna - tyl)\n"
          " R - rotate - obrot o zadana liczbe stopni (dodatni - prawo, ujemny - lewo)\n"
          " | V - velocity - ustawienie predkosci liniowej bota (jedzie do momentu przeslania S - stop)\n"  # wyslane samo, bot ustawia predkosc
          " | T - czas w jakim ma odbywac sie V\n"  # wyslane samo po prostu odliczy czas 
          " (w przypadku wyslania \"V<liczba>T<liczbaSekund>S\" robot bedzie jechal przez T sekund predkoscia V a potem sie zatrzyma)\n"
          " S - stop - natychmiastowe zatrzymanie\n"  # jak samo to zatrzyma V, moze isc samo
          " B - bierzacy odczyt sonaru w cm\n"
          " I - bierzacy odczyt czujnika IR\n"
          " E - bierzacy odczyt z enkoderow kol IR\n"
          " Q - zakoncz pisanie ramki")
    print("SK<liczba> - suma kontrolna dla upewnienia sie dotarcia calej ramki, suma z cyfr ramki % 256")
    print("--------------------------\nRobot ma tez opcje awaryjnego zatrzymania, po wyslaniu ramki (podczas oczekiwania na ramke {DONE,..} robota, uzytkownik moze wpisac 's'\n"
          "nastepuje wtedy awaryjne zatrzymanie robota a Arduino odsyla specjalna ramke {DONE, Awaryjne_Zatrzymanie}\n"
          "po akcji awaryjnego zatrzymania nalezy nacisnac dowolny przycisk aby przejsc dalej (reset bufora)")

    return "h"

def InputUzytkownika():
    # wysyłanie danych do Arduino    Podaj predkosc (0-255) do Arduino
    cmd = ""
    while cmd not in ("q","Q","h","H","z","Z","r","R"):
        cmd = input("========================================\nWpisz \nh lub p dla pomocy,\nr dla pisania ramki, \nz dla trybu zaliczeniowego,\nq zeby zakonczyc:\n$")


    if cmd == "q" or cmd == "Q":
        return "q"
    elif cmd == "h" or cmd == "H":
        return HelpWypisywanie()
    elif cmd == "z" or cmd == "Z" or cmd == "start":
        return PochylniaZaliczenie()
    elif cmd == "r" or cmd == "R" or cmd == "ramka":
        return PisanieRamki()


#============================================================================================
# --------- petla glowna -------
try:
    while True:
        cmd = InputUzytkownika()
        ramka = ""
        if cmd == 'q':
            break
        if cmd == "h":
            continue
        if cmd == "p":
            print("Ta ramka nie wprowadzi zmian, pomijam.")
            continue

        arduino.reset_input_buffer()
        arduino.reset_output_buffer()
        print(f"OUT| Wyslanie ramki do arduino:     {cmd.replace("\n", "\\n")}")
        arduino.write(cmd.encode())
        arduino.flush()


        # --------------- 1. oczekiwanie na ACK -------------
        ack_status = SprawdzenieAckOdArduino(arduino)
        if ack_status == "close" or ack_status == "NACK":
            continue
        elif ack_status == "ACK":
            # ----------- 2. oczekiwanie na odpowiedz zwrotna od arduino ----------
            print("Oczekiwanie na wykonanie zadania przez Arduino...")
            start_time = time.time()
            arduino_is_working = True
            while True:
                if arduino.in_waiting > 0:
                    arduinoResponse = arduino.readline().decode().strip()
                    print(arduinoResponse)
                    if arduinoResponse.startswith("{DONE"):
                        print("------- Arduino odpowiedz na ramke ---------")
                        print("IN| Arduino:" , arduinoResponse.replace("\n", "\\n"))
                        arduino_is_working = False
                        if "Awaryjne_Zatrzymanie" in arduinoResponse:
                            input("Nacisnij ENTER znak zeby kontynuowac")
                        break
                time.sleep(0.05)
                if time.time() - start_time > TIMEOUT_RESPONSE:
                    arduino_is_working = False
                    print("!TIMEOUT - Brak odpowiedzi {DONE, ...} od Arduino.")
                    break


        print("\n =================== Kolejna komenda ===============")


except KeyboardInterrupt:
    print("Zakonczono program.")

finally:
    arduino.close()
    print("Zamknieto polaczenie.")

"""
przykladowa ramka funkcyjna:
{TASK, P4.00, I0.30, D8.30, C45, T100, B1, C17.00, SK29,\n}

przykladowa ramka konfiguracji sprzetu:
{KONFIG,R1,L0,SK1,\n}
"""


#todo dzialanie na float dla obliczania sumy kontrolnej
#todo obsluga funkcji w arduino i rozszyfrowanie ramki