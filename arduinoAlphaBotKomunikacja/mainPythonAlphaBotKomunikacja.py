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
time.sleep(5)  # krótka pauza na reset Arduino

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
    return suma%256

def SprawdzenieAckOdArduino(arduino):
    #sprawdzenie czy Arduino wyslalo otrzymalo cala ramke
    start_time = time.time()
    while time.time() - start_time < TIMEOUT_RESPONSE:
        if arduino.in_waiting > 0:
            response = arduino.readline().decode().strip()
            if response:
                if response.startswith("{ACK"):
                    print("IN| Arduino, ACK:", response, " odsylam ACK2")
                    ACK_Odeslanie(arduino)
                    return "ACK"
                elif response.startswith("{NACK"):
                    print("IN| Arduino, NACK:", response)
                    return "NACK"
        time.sleep(0.05)
    print("!TIMEOUT - Brak {ACK,...} od ARDUINO")
    return "close"

def ACK_Odeslanie(arduino):
    #odeslanie drugiego ack do arduino zeby wykonalo polecenie
    ack_ramka = "{ACK2\n}"
    arduino.write(ack_ramka.encode())
    print("OUT| ACK2 do Arduino:", ack_ramka)

def PisanieRamki():
    print(" -------- Pisanie Ramki do wiadomosci:------")
    zadania = input()

    #dla V: walidacja podanej predkosci:
    if not zadania.isdigit():
        return None
    elif int(zadania) < 0 or int(zadania) > 255:
        return None
    else:
        return zadania
    #todo wszystkie opcje i suma kontrolna w ramce

def KonfiguracjaSprzetu():
    #przykladowa ramka: {KONFIG,R0,L1,<sumaKONTROLNA>,"\n"}
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

    ramka+= "SK"+str(SumaKontrolna(ramka))
    ramka+=",\n}"
    return ramka

def InputUzytkownika():
    # wysyłanie danych do Arduino    Podaj predkosc (0-255) do Arduino
    cmd = input("========================================\nWpisz \nh lub p dla pomocy,\nr dla pisania ramki, \nk dla konfiguracji sprzetu,\nq zeby zakonczyc:\n")

    if cmd == "q" or cmd == "quit" or cmd == "exit" or cmd == "Q":
        return "q"
    elif cmd == "h" or cmd == "H" or cmd == "help" or cmd == "p" or cmd == "P":
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

        print(f"OUT| Wyslanie ramki do arduino:     {cmd}")
        arduino.write(cmd.encode())

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
                    if arduinoResponse.startswith("{ARD"):
                        print("------- Arduino odpowiedz na ramke ---------")
                        print("IN| Arduino:" , arduinoResponse)
                        break
                time.sleep(0.05)
                if time.time() - start_time > TIMEOUT_RESPONSE:
                    print("!TIMEOUT - Brak odpowiedzi {ARD, ...} od Arduino.")


        print("\n =================== Kolejna komenda ===============")


except KeyboardInterrupt:
    print("Zakonczono program.")

finally:
    arduino.close()
    print("Zamknieto polaczenie.")


#todo komunikacja z uzytkownikiem
    #todo uzytkownik podaje co chce wyslac literami jedna obok drugiej np mrvb
    #todo przeslanie ramki z danymi w stylu
    """
    {
        M15,
        R-60,
        V100,
        SN, 
        BY, 
        IN, 
        KonfN,
        Num<numerWiadomosci>,
        "/n"
    }
    """

    """
    ustalenie czy po uruchomieniu silnik jedzie do przodu czy do tylu, ewentualna zmiana po stornie arduino w przypadku odbioru N
    {
        silnik1<Forward>Y/N, 
        silnik2<Forward>Y/N, 
        Num<numerWiadomosci>,
        "/n"
    }
    ciag dalszy numeracji wiadomosci
    """

#todo komenda help -> taka dokumentacja, ktora komenda robi co
#todo zebranie danych do ramki
#todo wysylanie ramki a nie suchej liczby