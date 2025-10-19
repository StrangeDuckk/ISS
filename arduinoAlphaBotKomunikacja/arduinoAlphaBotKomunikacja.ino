// ------------- ustawienia bazowe --------------

#define PIN_LEFT_MOTOR_SPEED 5
int PIN_LEFT_MOTOR_FORWARD = A0;            
int PIN_LEFT_MOTOR_REVERSE = A1;
#define PIN_LEFT_ENCODER 2
   
#define PIN_RIGHT_MOTOR_SPEED 6
int PIN_RIGHT_MOTOR_FORWARD = A2;         
int PIN_RIGHT_MOTOR_REVERSE = A3;
#define PIN_RIGHT_ENCODER 3

#include <EEPROM.h>

struct KonfiguracjaSilnikow {
  int PIN_LEFT_MOTOR_FORWARD;
  int PIN_LEFT_MOTOR_REVERSE;
  int PIN_RIGHT_MOTOR_FORWARD;
  int PIN_RIGHT_MOTOR_REVERSE;
  bool initialized;
};
// ------------- flgi stanu ---------------
bool awaryjnyStop = false;
bool wykonanieRuchu = true;

// ------------------- ustawianie danych z EEPROM -------------------
#define EEPROM_ADRES_KONFIG 0

KonfiguracjaSilnikow config;

// Funkcje EEPROM
void ZapiszKonfiguracjeDoEEPROM() {
  config.PIN_LEFT_MOTOR_FORWARD = PIN_LEFT_MOTOR_FORWARD;
  config.PIN_LEFT_MOTOR_REVERSE = PIN_LEFT_MOTOR_REVERSE;
  config.PIN_RIGHT_MOTOR_FORWARD = PIN_RIGHT_MOTOR_FORWARD;
  config.PIN_RIGHT_MOTOR_REVERSE = PIN_RIGHT_MOTOR_REVERSE;
  config.initialized = true;
  EEPROM.put(EEPROM_ADRES_KONFIG, config);
  Serial.println("|Zapisano konfiguracje silnikow w EEPROM|}");
}

void WczytajKonfiguracjeZEEPROM() {
  EEPROM.get(EEPROM_ADRES_KONFIG, config);
  //if (config.initialized) {
    PIN_LEFT_MOTOR_FORWARD = config.PIN_LEFT_MOTOR_FORWARD;
    PIN_LEFT_MOTOR_REVERSE = config.PIN_LEFT_MOTOR_REVERSE;
    PIN_RIGHT_MOTOR_FORWARD = config.PIN_RIGHT_MOTOR_FORWARD;
    PIN_RIGHT_MOTOR_REVERSE = config.PIN_RIGHT_MOTOR_REVERSE;
    //Serial.println("{DONE,|Wczytano konfiguracje silnikow z EEPROM|}");
  //} else {
    //Serial.println("{DONE,|EEPROM pusty - uzyto domyslnych pinow|}");
  //}
}

// ======================================================================================

#define SERIAL_BAUD_RATE 9600

String odpowiedzDoUzytkownika= "{DONE,";

int left_encoder_count=0;
int right_encoder_count=0;
int left_full_rotation = 20;
int right_full_rotation = 20;
int speed = 100;

void left_encoder(){
  left_encoder_count++;  
}

void right_encoder(){
  right_encoder_count++;  
}

bool PoprawnaSumaKontrolna(String cmd, int sumaPodana){
  int suma = 0;
  for(int i = 0; i < cmd.length(); i++){
    char znak = cmd[i];
    if (znak >= '0' && znak <= '9'){
      suma+=(znak - '0');
    }
  }
  suma = suma%256;

  if(suma == sumaPodana)
    return true;
  else
    return false;
}

void WyslijNACK(){
  Serial.println("{NACK}");
}

void WyslijACK(){
  Serial.println("{ACK}");
}

void setup() {
  Serial.begin(SERIAL_BAUD_RATE);
  WczytajKonfiguracjeZEEPROM();
  Serial.println("Polaczenie z Arduino jest gotowe.");
  
  pinMode(PIN_LEFT_MOTOR_SPEED, OUTPUT);
  analogWrite(PIN_LEFT_MOTOR_SPEED, 0);
  pinMode(PIN_LEFT_MOTOR_FORWARD, OUTPUT);
  pinMode(PIN_LEFT_MOTOR_REVERSE, OUTPUT);

  pinMode(PIN_RIGHT_MOTOR_SPEED, OUTPUT);
  analogWrite(PIN_RIGHT_MOTOR_SPEED, 0);
  pinMode(PIN_RIGHT_MOTOR_FORWARD, OUTPUT);
  pinMode(PIN_RIGHT_MOTOR_REVERSE, OUTPUT);

  attachInterrupt(digitalPinToInterrupt(PIN_LEFT_ENCODER), left_encoder, RISING);
  attachInterrupt(digitalPinToInterrupt(PIN_RIGHT_ENCODER), right_encoder, RISING);
}



// ========================================== funkcje bota ==========================================
// --------------- konfiguracja ---------------
void KonfiguracjaRuchuSwapSilnik(bool prawy,bool lewy){
  bool zamieniono = false;
  if(lewy){
    int temp = PIN_LEFT_MOTOR_REVERSE;
    PIN_LEFT_MOTOR_REVERSE = PIN_LEFT_MOTOR_FORWARD;
    PIN_LEFT_MOTOR_FORWARD = temp;
    odpowiedzDoUzytkownika += "|odwrocono kierunek lewego silnika|,";
    zamieniono = true;
  }
  if(prawy){
    int temp = PIN_RIGHT_MOTOR_REVERSE;
    PIN_RIGHT_MOTOR_REVERSE = PIN_RIGHT_MOTOR_FORWARD;
    PIN_RIGHT_MOTOR_FORWARD = temp;
    odpowiedzDoUzytkownika += "|odwrocono kierunek prawego silnika|,";
    zamieniono = true;
  }
  if (zamieniono)
    ZapiszKonfiguracjeDoEEPROM();
}

void Konfiguracja_EnkoderPelnyObrot(int prawyPelnyObrot, int lewyPelnyObrot){
  if(prawyPelnyObrot != 0){
    right_full_rotation = prawyPelnyObrot;
    odpowiedzDoUzytkownika += "|nowy pelny obrot dla enkodera prawego ustawiony|,";
  }
  if(lewyPelnyObrot != 0){
    left_full_rotation = prawyPelnyObrot;
    odpowiedzDoUzytkownika += "|nowy pelny obrot dla enkodera lewego ustawiony|,";
  }
}

// ------------------- funkcje ruchu i danych -------------------

void Funkcja_M(int liczbaCM){
  // int impulsyNaCentymetrLewy = left_full_rotation/16; // do zmiany po zmierzeniu kol rzeczywiscie, 5cm przyjete. obwod: 5*PI = 16cm
  // int impulsyNaCentymetrPrawy = right_full_rotation/16;

  // int lewyTarget = liczbaCM*impulsyNaCentymetrLewy; //do tylu impulsow na lewym kole dazymy
  // int prawyTarget = liczbaCM*impulsyNaCentymetrPrawy;

  // //tymczasowe enkodery
  // int LeftEncoderCountTemp = 0;
  // int RightEncoderCountTemp = 0;

  // // ruszenie do przodu
  // digitalWrite(PIN_LEFT_MOTOR_FORWARD, HIGH);
  // digitalWrite(PIN_LEFT_MOTOR_REVERSE, LOW);
  // analogWrite(PIN_LEFT_MOTOR_SPEED, speed);

  // digitalWrite(PIN_RIGHT_MOTOR_FORWARD, LOW);
  // digitalWrite(PIN_RIGHT_MOTOR_REVERSE, HIGH);
  // analogWrite(PIN_RIGHT_MOTOR_SPEED, speed);

  // //jazda do konkretnego dystansu
  // while (LeftEncoderCountTemp < lewyTarget && RightEncoderCountTemp < prawyTarget){
  //   //korekta kierunku
  //   if (left_encoder_count > right_encoder_count) {
  //     analogWrite(PIN_LEFT_MOTOR_SPEED, speed - 5);
  //     analogWrite(PIN_RIGHT_MOTOR_SPEED, speed);
  //   } else if (right_encoder_count > left_encoder_count) {
  //     analogWrite(PIN_RIGHT_MOTOR_SPEED, speed - 5);
  //     analogWrite(PIN_LEFT_MOTOR_SPEED, speed);
  //   } else {
  //     analogWrite(PIN_LEFT_MOTOR_SPEED, speed);
  //     analogWrite(PIN_RIGHT_MOTOR_SPEED, speed);
  //   }
  // }

  // //zatrzymanie
  // if (left_encoder_count > right_encoder_count) {
  //     analogWrite(PIN_LEFT_MOTOR_SPEED, speed - 5);
  //     analogWrite(PIN_RIGHT_MOTOR_SPEED, speed);
  //   } else if (right_encoder_count > left_encoder_count) {
  //     analogWrite(PIN_RIGHT_MOTOR_SPEED, speed - 5);
  //     analogWrite(PIN_LEFT_MOTOR_SPEED, speed);
  //   } else {
  //     analogWrite(PIN_LEFT_MOTOR_SPEED, speed);
  //     analogWrite(PIN_RIGHT_MOTOR_SPEED, speed);
  //   }

  wykonanieRuchu = true;
  awaryjnyStop = false;

  digitalWrite(PIN_LEFT_MOTOR_FORWARD, HIGH);
  digitalWrite(PIN_LEFT_MOTOR_REVERSE, LOW);
  analogWrite(PIN_LEFT_MOTOR_SPEED, speed);

  digitalWrite(PIN_RIGHT_MOTOR_FORWARD, LOW);
  digitalWrite(PIN_RIGHT_MOTOR_REVERSE, HIGH);
  analogWrite(PIN_RIGHT_MOTOR_SPEED, speed);

  unsigned long start = millis();
  while(millis()-start < 1000)
  {
    if(awaryjnyStop){
      Funkcja_S(2);
      wykonanieRuchu = false;
      return;
    }
    delay(10);
  }

  Funkcja_S(0);
  odpowiedzDoUzytkownika += "M{Bot przejechal o " + String(liczbaCM) + " cm}, ";
  Funkcja_E();

  wykonanieRuchu = false;
}

void Funkcja_R(int kat){
  wykonanieRuchu = true;
  awaryjnyStop = false;

  digitalWrite(PIN_LEFT_MOTOR_FORWARD, HIGH);
  digitalWrite(PIN_LEFT_MOTOR_REVERSE, LOW);
  analogWrite(PIN_LEFT_MOTOR_SPEED, speed);

  digitalWrite(PIN_RIGHT_MOTOR_FORWARD, LOW);
  digitalWrite(PIN_RIGHT_MOTOR_REVERSE, HIGH);
  analogWrite(PIN_RIGHT_MOTOR_SPEED, speed);
  
  unsigned long start = millis();
  while(millis()-start < 500)
  {
    if(awaryjnyStop){
      Funkcja_S(2);
      wykonanieRuchu = false;
      return;
    }
    delay(10);
  }

  Funkcja_S(0);
  odpowiedzDoUzytkownika += "R{Bot obrocil sie o " + String(kat) + " stopni}, ";
  Funkcja_E();

  wykonanieRuchu = false;
}

void Funkcja_V(int predkosc){
  odpowiedzDoUzytkownika += "V{Predkosc bota zostala ustawiona na " + String(predkosc) + "}, ";
}

void Funkcja_T(int iloscSekund){
  delay(iloscSekund*1000);
  odpowiedzDoUzytkownika += "T{Uplynelo " + String(iloscSekund) + " sekund}, ";
}

void Funkcja_S(int czyAwaryjnie){
  digitalWrite(PIN_LEFT_MOTOR_FORWARD, LOW);
  digitalWrite(PIN_LEFT_MOTOR_REVERSE, LOW);
  analogWrite(PIN_LEFT_MOTOR_SPEED, 0);

  digitalWrite(PIN_RIGHT_MOTOR_FORWARD, LOW);
  digitalWrite(PIN_RIGHT_MOTOR_REVERSE, LOW);
  analogWrite(PIN_RIGHT_MOTOR_SPEED, 0);
  
  //0 to tylko zatrzymanie bez zadnych informacji
  if(czyAwaryjnie == 1)
    odpowiedzDoUzytkownika += "S{Bot zatrzymal sie}, ";
  else{  
    awaryjnyStop = true;
    odpowiedzDoUzytkownika = "{DONE, Awaryjne_Zatrzymanie}";
    Serial.println(odpowiedzDoUzytkownika);
  }
}

void Funkcja_B(){
  odpowiedzDoUzytkownika += "B{Odczyt z sonaru na koniec komend TODO}, ";
}

void Funkcja_I(){
  odpowiedzDoUzytkownika += "I{Odczyt z czujnika na koniec komend TODO}, ";
}

void Funkcja_E(){
  odpowiedzDoUzytkownika += "E{Odczyt z kol na koniec: [";
  odpowiedzDoUzytkownika += left_encoder_count;
  odpowiedzDoUzytkownika += " , ";
  odpowiedzDoUzytkownika += right_encoder_count;
  odpowiedzDoUzytkownika += "]}, ";
}

// ------------------ parsowanie ramki -------------------
void WykonajRamke(String ramka){
  //przykladowa ramka: {TASK, M10, R-90, V100, T5, S1, B1, I1, E1, SK19,\n}
  //przetwarzana ramka:  M10, R-90, V100, T5, S1, B1, I1, E1
  ramka.trim();

  int start = 0;
  int end = ramka.indexOf(",");
  
  while (end != -1){
    String komenda = ramka.substring(start, end);
    komenda.trim();

    if (komenda.startsWith("M")) Funkcja_M(komenda.substring(1).toInt());
    else if (komenda.startsWith("R")) Funkcja_R(komenda.substring(1).toInt());
    else if (komenda.startsWith("V")) Funkcja_V(komenda.substring(1).toInt());
    else if (komenda.startsWith("T")) Funkcja_T(komenda.substring(1).toInt());
    else if (komenda.startsWith("S")) {
      int wartosc = komenda.substring(1).toInt();
      if (wartosc == 2) { // STOP awaryjny
        awaryjnyStop = true;
        Funkcja_S(2);
        return; 
      } else {
        Funkcja_S(1);
      }
    }
    else if (komenda.startsWith("B")) Funkcja_B();
    else if (komenda.startsWith("I")) Funkcja_I();
    else if (komenda.startsWith("E")) Funkcja_E();

    start = end + 1;
    end = ramka.indexOf(",", start);
  }
}

//--------------------- M + V - ruch o zadana odleglosc -----------------------
void M_RuchOZadanaOdleglosc(int speed){
  //todo rozdzielic V i M
  
  delay(500);
  digitalWrite(PIN_LEFT_MOTOR_FORWARD, HIGH);
  digitalWrite(PIN_LEFT_MOTOR_REVERSE, LOW);
  analogWrite(PIN_LEFT_MOTOR_SPEED, speed);

  digitalWrite(PIN_RIGHT_MOTOR_FORWARD, LOW);
  digitalWrite(PIN_RIGHT_MOTOR_REVERSE, HIGH);
  analogWrite(PIN_RIGHT_MOTOR_SPEED, speed);
  delay(3000);

  digitalWrite(PIN_LEFT_MOTOR_FORWARD, LOW);
  digitalWrite(PIN_LEFT_MOTOR_REVERSE, LOW);
  analogWrite(PIN_LEFT_MOTOR_SPEED, 0);

  digitalWrite(PIN_RIGHT_MOTOR_FORWARD, LOW);
  digitalWrite(PIN_RIGHT_MOTOR_REVERSE, LOW);
  analogWrite(PIN_RIGHT_MOTOR_SPEED, 0);

  odpowiedzDoUzytkownika += "M {Wykonano ruch o ";
  odpowiedzDoUzytkownika += speed;
  odpowiedzDoUzytkownika += ", (odpowiedz kol: [";
  odpowiedzDoUzytkownika += left_encoder_count;
  odpowiedzDoUzytkownika += " ";
  odpowiedzDoUzytkownika += right_encoder_count;
  odpowiedzDoUzytkownika += "]}, ";
}

void loop() {
  int speed = 0;
  String cmd = "";

  if (Serial.available()){
    while(Serial.available() > 0) Serial.read(); // czyszczenie resztek bajtów
    cmd = Serial.readStringUntil('\n');

    //sciagniecie ramki i podzielenie jej do walidacji
    if (cmd.indexOf("ACK2") < 0){
      int pozycjaSK = cmd.indexOf("SK");
      if (pozycjaSK != -1){
        String czescGlowna = cmd.substring(0,pozycjaSK);
      
        String temp = cmd.substring(pozycjaSK+2, cmd.indexOf(',', pozycjaSK+2));
        int  sumaKontrolnaZRamki = temp.toInt();
        if (PoprawnaSumaKontrolna(czescGlowna, sumaKontrolnaZRamki) == false){
          WyslijNACK();
        }
        else{
          WyslijACK();
        }
      }
      else{
        WyslijNACK();
      }
    }
    

    if(cmd.indexOf("KONFIG")>=0){
      //przykladowa ramka: {KONFIG,RN,LY,<NUMER>,\n}
      // przykladowa ramka: '{KONFIG,R0,L1,PE100,LE150,SK8,\n}'
      bool swapLewy =  false;
      bool swapPrawy = false;
      int prawyEnkoderCount = 0;
      int lewyEnkoderCount = 0;
      if(cmd.indexOf("L1")>=0)
        swapLewy = true;
      if(cmd.indexOf("R1")>=0)
        swapPrawy = true;
      if(cmd.indexOf("PE0")<0){
        prawyEnkoderCount = cmd.substring(cmd.indexOf("PE")+2, cmd.indexOf(",", cmd.indexOf("PE")+2)).toInt();
      }
      if(cmd.indexOf("LE0")<0){
        lewyEnkoderCount = cmd.substring(cmd.indexOf("LE")+2, cmd.indexOf(",", cmd.indexOf("LE")+2)).toInt();
      }

      if(swapPrawy || swapLewy)
        KonfiguracjaRuchuSwapSilnik(swapPrawy, swapLewy);
      else
        odpowiedzDoUzytkownika += "|Brak zmian w konfiguracji|,";

      if(prawyEnkoderCount>0 || lewyEnkoderCount>0)
        Konfiguracja_EnkoderPelnyObrot(prawyEnkoderCount,lewyEnkoderCount);
      else
        odpowiedzDoUzytkownika += "|Brak zmian w konfiguracji enkoderow|,";

      odpowiedzDoUzytkownika += "}";
      Serial.println(odpowiedzDoUzytkownika);
    }
    else{
      int start = cmd.indexOf(",") + 1;  // po pierwszym przecinku
      int end = cmd.indexOf(", SK");      // przed SK
      String ramkaSurowa = "";
      if (start < end){
        // {TASK, R10, SK1,\n} -> jednoelementowa ramka
        ramkaSurowa = cmd.substring(start, end+2);
        ramkaSurowa.trim();
      }

      WykonajRamke(ramkaSurowa);
      odpowiedzDoUzytkownika.setCharAt( odpowiedzDoUzytkownika.lastIndexOf(",")  , '}');
      Serial.println(odpowiedzDoUzytkownika);
    }
  }
  
  odpowiedzDoUzytkownika = "{DONE,"; // reset zawartości
  awaryjnyStop = false;//reset flag
  wykonanieRuchu = false;//reset dla pewnosci

  left_encoder_count=0;
  right_encoder_count=0;
}

//todo S - nagle zatrzymanie dziala zawsze w przypadku wykrycia obiektu przed soba
//sterowanie robotem, symulowane lub gotowe