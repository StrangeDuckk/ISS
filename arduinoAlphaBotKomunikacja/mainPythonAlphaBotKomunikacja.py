import serial
import serial.tools.list_ports
import time
import sys
from Logger import Logger

# pip install pyserial

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
log_filename = "log_PythonAplhaBotKomunikacja.txt"
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
def FunkcjaRobot_M():
    #"M- move - ruch o zadana odleglosc w cm (dodatnia - przod, ujemna - tyl)\n"
    # ruch o m cm, + w przod, - w tyl
    cmd = ""
    while not cmd.lstrip("-").isnumeric():
        cmd = input("M| Podaj o jaka odleglosc (w cm) robot ma sie przesunac (dla >0 w przod, dla <0 w tyl): ")
    return "M"+str(cmd)+", "

def FunkcjaRobot_R():
    #"R - rotate - obrot o zadana liczbe krokow (dodatni - prawo, ujemny - lewo)\n"
    # obrot o r w stopniach, + w przod, - w tyl
    cmd = ""
    while not cmd.lstrip("-").isnumeric():
        cmd = input("R| Podaj o jaki kat (w stopniach) robot ma sie przesunac (dla >0 w prawo, dla <0 w lewo): ")
    return "R"+str(cmd)+", "

def FunkcjaRobot_V():
    #"| V - velocity - ustawienie predkosci liniowej bota (jedzie do momentu przeslania S - stop)\n"
    #wyslane samo, robot jedzie caly czas, bez blokowania portu do wpisania
    cmd = "0"
    while True:
        cmd = input("V| Podaj z jaka predkoscia robot ma jechac (>=0, <=256, w przypadku podania predkosci bez czasu, robot bedzie jechal caly czas do wyslania S): ")

        if not cmd.isdigit():
            print("!V| Podaj liczbe calkowita")
            continue
        if 0< int(cmd) <=255:
            return "V"+str(cmd)+", "
        else:
            print("!V| Podaj liczbe z zakresu (0-256)")

def FunkcjaRobot_T():
    #"| T - czas w jakim ma odbywac sie V\n"  # wyslane samo po prostu odliczy czas
    #jesli T jest samo to puscic bo moze po prostu chciec opoznienie
    cmd = ""
    while True:
        cmd = input("T| Podaj przez jaki czas robot ma jechac dana predkoscia a potem sie zatrzymac (0 -> pominiecie): ")

        if not cmd.isdigit():
            print("!T| Podaj liczbe calkowita")
            continue
        if int(cmd) <= 0:
            print("!T| Podaj liczbe > 0")
            continue

        return "T"+str(cmd)+", "

def FunkcjaRobot_S():
    #"| S - stop - natychmiastowe zatrzymanie\n" #jak samo to zatrzyma V, moze isc samo
    #jesli wyslane samo to tez puscic
    cmd = ""
    while cmd not in ("0","1"):
        cmd = input("S| Czy robot ma sie zatrzymac (wykonac komende S, jesli 0, komenda pominieta)? (1=Tak,0=Nie)? (1/0): ")
    if cmd == "1":
        return "S1, "
    else:
        return "N"

def FunkcjaRobot_B():
    #"B - bierzacy odczyt sonaru w cm\n"
    cmd = ""
    while cmd not in ("0","1"):
        cmd = input("B| Czy podac bierzacy odczyt z sonaru (jesli 0, komenda zostanie pomineta)? (1=Tak,0=Nie)? (1/0): ")
    if cmd == "1":
        return "B1, "
    else:
        return "N"

def FunkcjaRobot_I():
    #"I - bierzacy odczyt czujnika IR\n"
    cmd = ""
    while cmd not in ("0","1"):
        cmd = input("I| Czy podac bierzacy odczyt z czujnika (jesli 0, komenda zostanie pominieta)? (1=Tak,0=Nie)? (1/0): ")
    if cmd == "1":
        return "I1, "
    else:
        return "N"

def FunkcjaRobot_E():
    #"I - bierzacy odczyt enkoderow w kolach\n"
    cmd = ""
    while cmd not in ("0","1"):
        cmd = input("E| Czy podac bierzacy odczyt z enkoderow kol (jesli 0, komenda zostanie pominieta)? (1=Tak,0=Nie)? (1/0): ")
    if cmd == "1":
        return "E1, "
    else:
        return "N"

def PisanieRamki():
    # przykladowa ramka: {TASK, M10, R-15, 7, /n}
    print(" -------- Pisanie Ramki do wiadomosci:------")
    print("Dostepne funkcje robota: \n"
          "M - move - ruch o zadana odleglosc w cm (dodatnia - przod, ujemna - tyl)\n"
          "R - rotate - obrot o zadana liczbe krokow (dodatni - prawo, ujemny - lewo)\n"
          "| V - velocity - ustawienie predkosci liniowej bota (jedzie do momentu przeslania S - stop)\n" #wyslane samo, robot jedzie caly czas 
          "| T - czas w jakim ma odbywac sie V\n" # wyslane samo po prostu odliczy czas 
          "| S - stop - natychmiastowe zatrzymanie\n" #jak samo to zatrzyma V, moze isc samo
          "(w przypadku wyslania \"V<liczba>T<liczbaSekund>S\" robot bedzie jechal przez T sekund predkoscia V a potem sie zatrzyma)\n"
          "B - bierzacy odczyt sonaru w cm\n"
          "I - bierzacy odczyt czujnika IR\n"
          "E - bierzacy odczyt z enkoderow kol IR\n"
          "Q - zakoncz pisanie ramki")
    zadania = input("Wpisz LITERY odpowiadajace funkcjom ktorych chcesz uzyc (np. RvTSi)\n")
    ramka = "{TASK, "
    wykonywalnaRamka = False
    licznikKomend = 0
    if zadania == "q" or zadania == "Q" or zadania == "" or zadania == "\n":
        return "p"
    else:
        if zadania.__contains__("M") or zadania.__contains__("m"):
            cmd = FunkcjaRobot_M()
            if cmd.__contains__("M0") and not wykonywalnaRamka:
                wykonywalnaRamka = False
            else:
                ramka += cmd
                wykonywalnaRamka = True
                licznikKomend+=1
        if zadania.__contains__("R") or zadania.__contains__("r"):
            cmd = FunkcjaRobot_R()
            if cmd.__contains__("R0") and not wykonywalnaRamka:
                wykonywalnaRamka = False
            else:
                ramka += cmd
                wykonywalnaRamka = True
                licznikKomend+=1
        if zadania.__contains__("V") or zadania.__contains__("v"):
            cmd = FunkcjaRobot_V()
            if cmd.__contains__("V0") and not wykonywalnaRamka:
                wykonywalnaRamka = False
            else:
                ramka += cmd
                wykonywalnaRamka = True
                licznikKomend+=1
        if zadania.__contains__("T") or zadania.__contains__("t"): #nie da sie wpisac 0
            wykonywalnaRamka = True
            ramka += FunkcjaRobot_T()#jesli samo w ramce to nie pomijac
            licznikKomend+=1
        if zadania.__contains__("S") or zadania.__contains__("s"):
            cmd = FunkcjaRobot_S()
            if cmd == "N" and not wykonywalnaRamka:
                wykonywalnaRamka = False
            elif not cmd.__contains__("N"):
                ramka += cmd
                wykonywalnaRamka = True
            #N - jesli N to nie wysylac i jesli samo tylko SN to przejsc do kolejnego wpisywania ramki po wypisaniu komunikatu
        if zadania.__contains__("B") or zadania.__contains__("b"):
            cmd = FunkcjaRobot_B()
            if cmd == "N" and not wykonywalnaRamka:
                wykonywalnaRamka = False
            elif not cmd.__contains__("N"):
                ramka += cmd
                wykonywalnaRamka = True
            #N - jesli samo tylko BN to przejsc do kolejnego wpisywania ramki po wypisaniu komunikatu
        if zadania.__contains__("I") or zadania.__contains__("i"):
            cmd = FunkcjaRobot_I()
            if cmd == "N" and not wykonywalnaRamka:
                wykonywalnaRamka = False
            elif not cmd.__contains__("N"):
                ramka += cmd
                wykonywalnaRamka = True
            #N - jesli samo tylko iN to przejsc do kolejnego wpisywania ramki po wypisaniu komunikatu
        if zadania.__contains__("E") or zadania.__contains__("e"):
            cmd = FunkcjaRobot_E()
            if cmd == "N" and not wykonywalnaRamka:
                wykonywalnaRamka = False
            elif not cmd.__contains__("N"):
                ramka += cmd
                wykonywalnaRamka = True
            #N - jesli samo tylko eN to przejsc do kolejnego wpisywania ramki po wypisaniu komunikatu

    if wykonywalnaRamka == False:
        return "p" #np ktos dal B0 tylko, takiej ramki nei oplaca sie wysylac

    ramka += "SK"+SumaKontrolna(ramka)+",\n}"
    return ramka
    #todo dodac ruch

def KonfiguracjaSprzetu():
    #przykladowa ramka: {KONFIG, R0, L1, PE200, LE0, SK3 ,"\n"}
    print(" --------------- konfiguracja sprzetu --------------")
    ramka = "{KONFIG,"
    cmd = ""
    while cmd not in("1", "0"):
        cmd = input("Czy odwrocic (forward/backward) silnik prawy (1=Tak,0=Nie)? (1/0)")

    if cmd == "1":
        ramka+="R1,"
    else:
        ramka+="R0,"

    cmd = ""
    while cmd not in("1", "0"):
        cmd = input("Czy odwrocic (forward/backward) silnik lewy? (1=Tak,0=Nie)? (1/0)")
    if cmd == "1":
        ramka+="L1,"
    else:
        ramka+="L0,"

    cmd = ""
    while cmd not in("1", "0"):
        cmd = input("Czy zmienic bazowa ilosc punktow dla jednego obrotu kola PRAWEGO? (1=Tak,0=Nie)? (1/0)")
    if cmd == "1":
        cmd = ""
        while True:
            cmd = input(
                "PE| Podaj odczyt z enkodera dla prawego kola po jednym pelnym obrocie: ")

            if not cmd.isdigit():
                print("!PE| Podaj liczbe calkowita")
                continue
            else:
                ramka += "PE"+str(cmd)+","
                break
    else:
        ramka+="PE0,"

    cmd = ""
    while cmd not in ("1", "0"):
        cmd = input("Czy zmienic bazowa ilosc punktow dla jednego obrotu kola Lewego? (1=Tak,0=Nie)? (1/0)")
    if cmd == "1":
        cmd = ""
        while True:
            cmd = input(
                "LE| Podaj odczyt z enkodera dla prawego kola po jednym pelnym obrocie: ")

            if not cmd.isdigit():
                print("!LE| Podaj liczbe calkowita")
                continue
            else:
                ramka += "LE" + str(cmd)+","
                break
    else:
        ramka += "LE0,"


    ramka+= "SK"+SumaKontrolna(ramka)
    ramka+=",\n}"
    return ramka

def InputUzytkownika():
    # wysyłanie danych do Arduino    Podaj predkosc (0-255) do Arduino
    cmd = ""
    while cmd not in ("q","Q","h","H","k","K","r","R"):
        cmd = input("========================================\nWpisz \nh lub p dla pomocy,\nr dla pisania ramki, \nk dla konfiguracji sprzetu,\nq zeby zakonczyc:\n")


    if cmd == "q" or cmd == "Q":
        return "q"
    elif cmd == "h" or cmd == "H":
        #todo napisac help
        print("HELP TODO DO NAPISANIA")
        return "h"
    elif cmd == "k" or cmd == "K" or cmd == "konf":
        return KonfiguracjaSprzetu()
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
            while True:
                if arduino.in_waiting > 0:
                    arduinoResponse = arduino.readline().decode().strip()
                    if arduinoResponse.startswith("{DONE"):
                        print("------- Arduino odpowiedz na ramke ---------")
                        print("IN| Arduino:" , arduinoResponse.replace("\n", "\\n"))
                        break
                time.sleep(0.05)
                if time.time() - start_time > TIMEOUT_RESPONSE:
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
    {TASK, M10, R-90, V100, T5, S1, B1, I1, SK19,\n}
    
    przykladowa ramka konfiguracji sprzetu:
    {KONFIG,R1,L0,SK1,\n}
    """

#todo dokumentacja
#todo s w kazdym momencie do wpisania