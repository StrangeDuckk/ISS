import serial
import serial.tools.list_ports
import time
import sys

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
                        print("Arduino:", response)
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

# ------------------------- stałe ----------------------
PORT = WykrywaniePortu() #wyjsciowo bylo com4
BAUDRATE = 9600
PONAWIANIE_LIMIT = 3 #3 razy program probuje ponowic polaczenie
TIMEOUT_CONNECTION = 100
TIMEOUT_RESPONSE = 100
LiczbaKontrolna = 0

# -------------------- otwarcie portu ------------------
arduino = serial.Serial(PORT, BAUDRATE, timeout=1)
time.sleep(5)  # krótka pauza na reset Arduino

# ----------------- proba polaczenia z arduino --------------
PolacznieZArduino(arduino)

# ===================================================================================================
# ----------------- funkcje -----------------

def PisanieRamki():
    zadania = input(" ------------ Pisanie Ramki {}")

def InputUzytkownika():
    # wysyłanie danych do Arduino    Podaj predkosc (0-255) do Arduino
    cmd = input("========================================\nWpisz \nh lub p dla pomocy,\nr dla pisania ramki\nq zeby zakonczyc:\n")

    if cmd == "q" or cmd == "quit" or cmd == "exit" or cmd == "Q":
        return "q"
    elif cmd == "h" or cmd == "H" or cmd == "help" or cmd == "p" or cmd == "P":
        #todo napisac help
        print("HELP TODO DO NAPISANIA")
        return "h"
    elif cmd == "r" or cmd == "R" or cmd == "ramka":
        return PisanieRamki()

    # walidacja podanej predkosci:
    if not cmd.isdigit():
        return None
    elif int(cmd) < 0 or int(cmd) > 255:
        return None
    else:
        return cmd




#============================================================================================
# --------- petla glowna -------
try:
    while True:
        cmd = InputUzytkownika()
        if cmd == "q":
            break
        if cmd == "h":
            continue
        if cmd is None:
            print("Wpisz liczbe z zakresu 0-255!")
            continue

        arduino.write(cmd.encode())

        # odbiór odpowiedzi
        while True:
            arduinoResponse = arduino.readline().decode().strip()
            if arduinoResponse:
                print("------- Arduino odpowiedz na ramke ---------")
                print("Arduino:", arduinoResponse)
                break

except KeyboardInterrupt:
    print("Zakonczono program.")

finally:
    arduino.close()
    print("Zamknieto polaczenie.")

#todo zapis logowania do pliku txt, nadpisywanie za kazdym uruchomieniem programu

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
        "/n", //znacznik konca dla spelnienia wymagan
        <numerWiadomosci>
    }
    """
    #todo do konfiguracji sprzetu oddzielna ramka do wyslania
    #todo nuemrWiadomosci jako liczba kontrolna, kontrolowana od strony pythona i Arduino,np Arduino: 5, python ACK jako 5.1 i ack po stronie arduino dostaje jako 5.2

    #todo ramka konfiguracji
    """
    ustalenie czy po uruchomieniu silnik jedzie do przodu czy do tylu, ewentualna zmiana po stornie arduino w przypadku odbioru N
    {
        silnik1<Forward>Y/N, 
        silnik2<Forward>Y/N, 
        "/n", //znacznik konca dla spelnienia wymagan
        <numerWiadomosci>
    }
    ciag dalszy numeracji wiadomosci
    """

#todo komenda help -> taka dokumentacja, ktora komenda robi co
#todo zebranie danych do ramki
#todo wysylanie ramki a nie suchej liczby
#todo sprawdzanie czy cala ramka dotarla i wysylanie odpowiedzi czy dotarla (ack) + liczba kontrolna