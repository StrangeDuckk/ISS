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

void WyslijACK(int SumaWynik = 0){
  Serial.println("{ACK,SK"+String(SumaWynik)+"}");
}

void KonfiguracjaRuchuSwapSilnik(bool prawy,bool lewy){
  bool zamieniono = false;
  if(lewy){
    int temp = PIN_LEFT_MOTOR_REVERSE;
    PIN_LEFT_MOTOR_REVERSE = PIN_LEFT_MOTOR_FORWARD;
    PIN_LEFT_MOTOR_FORWARD = temp;
    odpowiedzDoUzytkownika += "|odwrocono kierunek lewego silnika|";
    zamieniono = true;
  }
  if(prawy){
    int temp = PIN_RIGHT_MOTOR_REVERSE;
    PIN_RIGHT_MOTOR_REVERSE = PIN_RIGHT_MOTOR_FORWARD;
    PIN_RIGHT_MOTOR_FORWARD = temp;
    odpowiedzDoUzytkownika += "|odwrocono kierunek prawego silnika|";
    zamieniono = true;
  }
  if (zamieniono)
    ZapiszKonfiguracjeDoEEPROM();
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
  odpowiedzDoUzytkownika = "{DONE,";
  int speed = 0;
  String cmd = "";

  if (Serial.available()){
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
          WyslijACK(sumaKontrolnaZRamki);
        }
      }
      else{
        WyslijNACK();
      }
    }
    

    if(cmd.indexOf("KONFIG")>=0){
      //przykladowa ramka: {KONFIG,RN,LY,<NUMER>,"\n"}
      bool swapLewy =  false;
      bool swapPrawy = false;
      if(cmd.indexOf("L1")>=0)
        swapLewy = true;
      if(cmd.indexOf("R1")>=0)
        swapPrawy = true;

      if(swapPrawy || swapLewy)
        KonfiguracjaRuchuSwapSilnik(swapPrawy, swapLewy);
      else
        odpowiedzDoUzytkownika += "|Brak zmian w konfiguracji|,";

      odpowiedzDoUzytkownika += "}";
      Serial.println(odpowiedzDoUzytkownika);
      //todo ack cale
    }
    else{
      //todo ramka ruchowa i reszta ramek
      int pythonRamkaOdUzytkownika = Serial.parseInt();
      speed = pythonRamkaOdUzytkownika;
      M_RuchOZadanaOdleglosc(speed);
      Serial.println(odpowiedzDoUzytkownika);
    }
  }
  
  //odpowiedzDoUzytkownika+="}";
  //Serial.println(odpowiedzDoUzytkownika);
  odpowiedzDoUzytkownika = "{DONE,"; // reset zawartości

  left_encoder_count=0;
  right_encoder_count=0;
}

//todo S - nagle zatrzymanie dziala zawsze w przypadku wykrycia obiektu przed soba
//sterowanie robotem, symulowane lub gotowe
//parser ramek
//odpowiadanie ACK i kontrolowanie liczby kontrolnej, ewentualnie podeslanie ponowne wiadomosci nieodebranej
