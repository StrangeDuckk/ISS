Dokumentacja techniczna
# System sterowania robota mobilnego AlphaBot (Arduino + Python)
# 1. Opis projektu

Projekt składa się z dwóch współpracujących modułów:

Oprogramowanie wbudowane (Arduino) – odpowiada za niskopoziomowe sterowanie silnikami, obsługę enkoderów, przetwarzanie ramek poleceń i komunikację przez port szeregowy.

Aplikacja komputerowa (Python) – umożliwia użytkownikowi interaktywne tworzenie i wysyłanie komend do robota, odbieranie odpowiedzi oraz wykonywanie konfiguracji sprzętowej.
Aplikacja uzywa m.in. bibliotek:
    
    pyserial
    keyboard
System umożliwia:

- ruch robota (przód, tył, obrót),

- sterowanie prędkością,

- pomiar czasu jazdy,

- zatrzymanie awaryjne z klawiatury,

- konfigurację kierunku silników i parametrów enkoderów,

- odczyty z czujników (sonar, IR).

# 2. Struktura projektu


    Projekt_AlphaBot
    ├── Arduino/    
    │   └── AlphaBot_Program.ino     # Kod sterujący mikrokontrolerem   
    ├── Python/     
    │   ├── main.py                  # Główna aplikacja komunikacyjna   
    │   ├── Logger.py                # Klasa logująca stdout do pliku   
    │   └── log_PythonAplhaBotKomunikacja.txt   
    └── README.md (dokumentacja)

# 3. Komunikacja między Arduino a Pythonem
### 3.1 Format ramek komunikacyjnych

Wszystkie wiadomości są przesyłane w formacie tekstowym (9600 bps).

### a) Ramka funkcyjna:     
{TASK, M10, R-90, V100, T5, S1, B1, I1, E1, SK19,\n}


    TASK – typ ramki

    M<liczbaCM> – ruch o liczbaCM cm, >0 do przodu, <0 do tylu

    R<liczbaStopni> – obrót o liczbeStopni, >0 obrot w prawo, <0 obrot w lewo

    V<predkoscLiniowa> – ustawienie prędkości 100

    T<liczbaSekund> – jazda przez 5 sekund

    S(0/1) – zatrzymanie

    B/I/E(0/1) – odczyty czujników

    SK<liczba> – suma kontrolna
    
    /n - znak konca ramki  

Przykladowo, wywolanie ramki: 
    
    {TASK, M10, V100, T2, I1, SK5,\n}
spowoduje odpowiedz od arduino w postaci: 

    {DONE,M{Bot przejechal o 10 cm}, E{Odczyt z kol na koniec: [0 , 0]}, V{Predkosc bota zostala ustawiona na 100}, TV{Robot poruszal sie przez 2 sekund predkoscia 100}, E{Odczyt z kol na koniec: [0 , 0]}, I{Odczyt z czujnika na koniec komend TODO}}
Log z wykonania tego polecenia (input od uzytkownika znajduje sie po znaku zachety "$"):
    
    Logowanie rozpoczete do pliku: log_PythonAplhaBotKomunikacja.txt
    Arduino jest na porcie:  COM14
    Polaczone z Arduino!
    IN| Arduino: Polaczenie z Arduino jest gotowe.
    ========================================
    Wpisz 
    h lub p dla pomocy,
    r dla pisania ramki, 
    k dla konfiguracji sprzetu,
    q zeby zakonczyc:
    $r
     -------- Pisanie Ramki do wiadomosci:------
    Dostepne funkcje robota: 
    M - move - ruch o zadana odleglosc w cm (dodatnia - przod, ujemna - tyl)
    R - rotate - obrot o zadana liczbe stopni (dodatni - prawo, ujemny - lewo)
    | V - velocity - ustawienie predkosci liniowej bota (jedzie do momentu przeslania S - stop)
    | T - czas w jakim ma odbywac sie V
    S - stop - natychmiastowe zatrzymanie
    (w przypadku wyslania "V<liczba>T<liczbaSekund>S" robot bedzie jechal przez T sekund predkoscia V a potem sie zatrzyma)
    B - biezacy odczyt sonaru w cm
    I - biezacy odczyt czujnika IR
    E - biezacy odczyt z enkoderow kol IR
    Q - zakoncz pisanie ramki
    Wpisz LITERY odpowiadajace funkcjom ktorych chcesz uzyc (np. RvTSi)
    $mtvi
    M| Podaj o jaka odleglosc (w cm) robot ma sie przesunac (dla >0 w przod, dla <0 w tyl): $10
    V| Podaj z jaka predkoscia robot ma jechac (>=0, <=256, tylko ustawienie predkosci): $100
    T| Podaj przez jaki czas robot ma jechac dana predkoscia a potem sie zatrzymac (0 -> pominiecie): $2
    I| Czy podac biezacy odczyt z czujnika (jesli 0, komenda zostanie pominieta)? (1=Tak,0=Nie)? (1/0): $1
    OUT| Wyslanie ramki do arduino:     {TASK, M10, V100, T2, I1, SK5,\n}
    Oczekiwanie na ACK od Arduino, proba: 1/3
    IN| Arduino, ACK: {ACK}  odsylam ACK2
    OUT| ACK2 do Arduino: {ACK2\n}
    Oczekiwanie na wykonanie zadania przez Arduino...
    ------- Arduino odpowiedz na ramke ---------
    IN| Arduino: {DONE,M{Bot przejechal o 10 cm}, E{Odczyt z kol na koniec: [0 , 0]}, V{Predkosc bota zostala ustawiona na 100}, TV{Robot poruszal sie przez 2 sekund predkoscia 100}, E{Odczyt z kol na koniec: [0 , 0]}, I{Odczyt z czujnika na koniec komend TODO}}
    
     =================== Kolejna komenda ===============
    ...

### b) Ramka konfiguracyjna:    
{KONFIG, R1, L0, PE200, LE180, SK12,\n}

    R1/L0 – odwrócenie kierunku silnika prawego/lewego

    PE/LE – liczba impulsów enkodera na jeden obrót koła

    SK – suma kontrolna

    /n - znak konca ramki  

Przykladowo wywolanie ramki:    

    {KONFIG, R1, L0, PE200, LE180, SK12,\n}     
spowoduje odpowiedz od arduino w postaci:   

    {DONE,|odwrocono kierunek prawego silnika|,|nowy pelny obrot dla enkodera prawego ustawiony|,|nowy pelny obrot dla enkodera lewego ustawiony|,}

Log z wykonania tego polecenia (input od uzytkownika znajduje sie po znaku zachety "$"):
    
    Logowanie rozpoczete do pliku: log_PythonAplhaBotKomunikacja.txt
    Arduino jest na porcie:  COM14
    Polaczone z Arduino!
    IN| Arduino: Polaczenie z Arduino jest gotowe.
    ========================================
    Wpisz 
    h lub p dla pomocy,
    r dla pisania ramki, 
    k dla konfiguracji sprzetu,
    q zeby zakonczyc:
    $k
     --------------- konfiguracja sprzetu --------------
    Czy odwrocic (forward/backward) silnik prawy (1=Tak,0=Nie)? (1/0) $1
    Czy odwrocic (forward/backward) silnik lewy? (1=Tak,0=Nie)? (1/0) $0
    Czy zmienic bazowa ilosc punktow dla jednego obrotu kola PRAWEGO? (1=Tak,0=Nie)? (1/0) $1
    PE| Podaj odczyt z enkodera dla prawego kola po jednym pelnym obrocie: $200
    Czy zmienic bazowa ilosc punktow dla jednego obrotu kola Lewego? (1=Tak,0=Nie)? (1/0) $1
    LE| Podaj odczyt z enkodera dla prawego kola po jednym pelnym obrocie: $180
    OUT| Wyslanie ramki do arduino:     {KONFIG,R1,L0,PE200,LE180,SK12,\n}
    Oczekiwanie na ACK od Arduino, proba: 1/3
    IN| Arduino, ACK: {ACK}  odsylam ACK2
    OUT| ACK2 do Arduino: {ACK2\n}
    Oczekiwanie na wykonanie zadania przez Arduino...
    ------- Arduino odpowiedz na ramke ---------
    IN| Arduino: {DONE,|odwrocono kierunek prawego silnika|,|nowy pelny obrot dla enkodera prawego ustawiony|,|nowy pelny obrot dla enkodera lewego ustawiony|,}
    
     =================== Kolejna komenda ===============
    ...

### 3.2 Protokół wymiany danych

- Python wysyła ramkę → Arduino odbiera.
- Arduino weryfikuje sumę kontrolną. (suma pojedyjczych cyfr z ramki podzielona modulo przez 256)
- Jeśli poprawna:
     - Arduino wysyła {ACK}.
     - Python odsyła {ACK2} → Arduino wykonuje komendy.
- Jeśli błędna:
  - Arduino wysyła {NACK} (Python powtarza transmisję, potrzebny ponowny input od uzytkownika).
- Po zakończeniu wykonania Arduino odsyła odpowiedz z wywolanych funkcji np.:
  - {DONE, M{...}, R{...}, E{[x,y]}, }


W przypadku zatrzymania awaryjnego:

- Arduino odsyla ramke: {DONE, Awaryjne_Zatrzymanie}
- Python potrzebuje aby uzytkownik wprowadzil dowolny znak aby kontynuowac prace z programem (dla wyczyszczenia bufora stdin)

# 4. Oprogramowanie Arduino
### 4.1 Kluczowe funkcje

Funkcje	ruchu:

    Funkcja_M(int cm)	Ruch o określoną odległość (cm)
    Funkcja_R(int kat)	Obrót o zadany kąt
    Funkcja_V(int speed)	Ustawienie prędkości silników
    Funkcja_T(int sekundy, bool czyTV)	Odczekanie okreslonego czasu lub jazda przez określony czas
    Funkcja_S(int tryb)	Zatrzymanie robota lub awaryjny stop

Funkcje stanu:
    
    Funkcja_B()     Odczyt z sonaru
    Funkcja_I()     Odczyt z czujnikow zblizeniowych
    Funkcja_E()     Odczyt z enkoderow kol

Funkcje konfiguracyjne:
    
    KonfiguracjaRuchuSwapSilnik(bool pr, bool le)	                    Zmiana kierunku obrotu silników
    Konfiguracja_EnkoderPelnyObrot(int prawy, int lewy)                 Zmiana bazowej ilosci punktow dla pelnego obrotu w kazdym z kol
    ZapiszKonfiguracjeDoEEPROM() / WczytajKonfiguracjeZEEPROM()	    Trwałe przechowywanie konfiguracji silników

Funkcja parsowania ramki funkcyjnej:
    
    WykonajRamke(String)	Parsowanie i wykonanie otrzymanej ramki

### 4.2 Flagi i stany

- awaryjnyStop – zatrzymanie natychmiastowe z komunikacji.

- wykonanieRuchu – flaga trwającego ruchu.

- left_encoder_count, right_encoder_count – liczniki impulsów enkoderów.

- speed – aktualna prędkość dla silnikow (0–255).

### 4.3 EEPROM

EEPROM przechowuje konfigurację pinów i kierunków obrotów.
Adres bazowy: EEPROM_ADRES_KONFIG = 0.

# 5. Aplikacja Python
### 5.1 Główne zadania

- automatyczne wykrywanie portu COM z Arduino,
- zestawienie połączenia (3 próby),
- budowanie ramek konfiguracyjnych i funkcyjnych,
- wysyłanie ramek oraz obsługa protokołu ACK/NACK/ACK2,
- obsługa awaryjnego zatrzymania (naciśnięcie klawisza s).

### 5.2 Najważniejsze funkcje

Funkcje laczace:

    WykrywaniePortu()	Wyszukanie portu, na którym działa Arduino
    PolacznieZArduino()	Próba połączenia i weryfikacja odpowiedzi

Funkcje kontrolujace polaczenie i zgodnosc: 

    SumaKontrolna(ramka)	        Obliczanie sumy kontrolnej % 256
    SprawdzenieAckOdArduino()	Oczekiwanie na potwierdzenie {ACK}

Funkcje umozliwiajace komunikacje z uzytkownikiem:

    PisanieRamki()	                        Interaktywne tworzenie ramki TASK
    KonfiguracjaSprzetu()	                Tworzenie ramki KONFIG
    ListenForStopKeyboardInterrupt()	Nadzór nad awaryjnym zatrzymaniem
    HelpWypisywanie()	                Wyświetlenie instrukcji obsługi

### 5.3 Logowanie

Logowanie obdlugiwane jest przez klase Logger, ktora zapisuje kazde wypisanie na konsole do pliku.

Cała komunikacja i błędy zapisywane są do pliku:

    log_PythonAplhaBotKomunikacja.txt

# 6. Obsługa programu
### 6.1 Uruchomienie

1. Podłącz Arduino przez USB oraz wybierz port na ktorym znajduje sie Arduino
2. Uruchom i wgraj program arduinoAlphaBotKomunikacja.ino
3. Uruchom python arduinoAlphaBotKomunikacja.py
4. Program automatycznie znajdzie port i nawiąże połączenie
5. Z dostepnego menu wybierz:
   

    r – wysyłanie ramki z zadaniem,
    k – konfiguracja silników/enkoderów,
    h – pomoc,
    q – zakończenie pracy.

Jesli zostala wybrana opcja r:
1. Podaj ktore z dostepnych funkcji chcesz aby robot wykonal
2. Podaj parametry do funkcji (kazda funkcja zapyta oddzielnie o parametr do siebie)
3. W trakcie wykonywania zadania przez Arduino mozesz uzyc "s" aby uruchomic Awaryjny stop (rozdzial 6.2 dokumentacji)
4. Czekaj na wynik z Arduino
5. Po otrzymaniu wyniku mozesz ponownie wyslac kolejne zadanie

Jesli zostala wybrana opcja k:
1. Dla parametrow ktore beda prosic o dane wpisz odpowiednie wartosci
    - w przypadku kiedy nie chcesz zmian -> 0
    - w przypadku zmian odpowiednio 1 (dla swap kierunku silnikow) lub wartosc (dla enkoderow)
2. Czekaj na wynik z Arduino

Jesli zostala wybrana opcja h - Python wypisze dostepne opcje i obsluge funkcji

Jesli zostala wybrana opcja q - program python zakonczy dzialanie

### 6.2 Awaryjny stop

W momencie naciśniecia „s” podczas pracy robota – python wysle do niego specjalna ramke:
    
    {TASK, S2, SK2, \n}
Ramka ta wywola Funkcja_S(int czyAwaryjnie) w trybie awaryjnym, czyli zatrzyma wszystkie procesy i odesle specjalna ramke:

    {DONE, Awaryjne_Zatrzymanie}
Funkcja awaryjnego stopu wymaga nastepnie wprowadzenia dowolnej liczby aby program mogl kontynuowac

Logi z przykladowego wykonania awaryjnego stopu (podczas trwania wykonania funkcji T w formie opoznienia):

    Logowanie rozpoczete do pliku: log_PythonAplhaBotKomunikacja.txt
    Arduino jest na porcie:  COM14
    Polaczone z Arduino!
    IN| Arduino: Polaczenie z Arduino jest gotowe.
    ========================================
    Wpisz 
    h lub p dla pomocy,
    r dla pisania ramki, 
    k dla konfiguracji sprzetu,
    q zeby zakonczyc:
    $r
     -------- Pisanie Ramki do wiadomosci:------
    Dostepne funkcje robota: 
    M - move - ruch o zadana odleglosc w cm (dodatnia - przod, ujemna - tyl)
    R - rotate - obrot o zadana liczbe stopni (dodatni - prawo, ujemny - lewo)
    | V - velocity - ustawienie predkosci liniowej bota (jedzie do momentu przeslania S - stop)
    | T - czas w jakim ma odbywac sie V
    S - stop - natychmiastowe zatrzymanie
    (w przypadku wyslania "V<liczba>T<liczbaSekund>S" robot bedzie jechal przez T sekund predkoscia V a potem sie zatrzyma)
    B - biezacy odczyt sonaru w cm
    I - biezacy odczyt czujnika IR
    E - biezacy odczyt z enkoderow kol IR
    Q - zakoncz pisanie ramki
    Wpisz LITERY odpowiadajace funkcjom ktorych chcesz uzyc (np. RvTSi)
    $vt
    V| Podaj z jaka predkoscia robot ma jechac (>=0, <=256, tylko ustawienie predkosci): $150
    T| Podaj przez jaki czas robot ma jechac dana predkoscia a potem sie zatrzymac (0 -> pominiecie): $3
    OUT| Wyslanie ramki do arduino:     {TASK, V150, T3, SK9,\n}
    Oczekiwanie na ACK od Arduino, proba: 1/3
    IN| Arduino, ACK: {ACK}  odsylam ACK2
    OUT| ACK2 do Arduino: {ACK2\n}
    Oczekiwanie na wykonanie zadania przez Arduino...
    s! AWARYJNE ZATRZYMANIE !
    OUT| ! AWARYJNE ZATRZYMANIE !, wyslano: {TASK, S2, SK1,\n}
    (Nacisnij dowolny przycisk aby kontynuowac) $
    ------- Arduino odpowiedz na ramke ---------
    IN| Arduino: {DONE, Awaryjne_Zatrzymanie}
    Nacisnij dowolny znak zeby kontynuowac
    
     =================== Kolejna komenda ===============

klikniecie 's' nastapilo w tym miejscu:     
Oczekiwanie na wykonanie zadania przez Arduino...   
<span style="color:limegreen">s</span>! AWARYJNE ZATRZYMANIE !  
...

# 7. Dodatkowe informacje techniczne 
Oryginalne przylacza pinow:

    Element	                Pin	    Opis

    Silnik lewy PWM	        D5	    Sterowanie prędkością
    Silnik lewy kierunek	A0/A1	    Kierunek FWD/REV
    Enkoder lewy	        D2	    Zliczanie impulsów
    Silnik prawy PWM	D6	    Sterowanie prędkością
    Silnik prawy kierunek	A2/A3	    Kierunek FWD/REV
    Enkoder prawy	        D3	    Zliczanie impulsów

Baud rate: 9600
Protokół: tekstowy, 
Zakończenie: \n

# 8. Autor kodu:
    Katarzyna Mikusek
    s30338, PJATK 
    Jezyk Polski, studia dzienne
    10.2025