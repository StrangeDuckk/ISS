#define PIN_LEFT_MOTOR_SPEED 5
int PIN_LEFT_MOTOR_FORWARD = A0;            
int PIN_LEFT_MOTOR_REVERSE = A1;
#define PIN_LEFT_ENCODER 2
   
#define PIN_RIGHT_MOTOR_SPEED 6
int PIN_RIGHT_MOTOR_FORWARD = A2;         
int PIN_RIGHT_MOTOR_REVERSE = A3;
#define PIN_RIGHT_ENCODER 3

#define SERIAL_BAUD_RATE 9600

int liczbaKontrolna = 0;
String odpowiedzDoUzytkownika= "{";

int left_encoder_count=0;
int right_encoder_count=0;

void left_encoder(){
  left_encoder_count++;  
}

void right_encoder(){
  right_encoder_count++;  
}

void KonfiguracjaRuchuSwapSilnik(bool prawy,bool lewy){
  if(lewy){
    int temp = PIN_LEFT_MOTOR_REVERSE;
    PIN_LEFT_MOTOR_REVERSE = PIN_LEFT_MOTOR_FORWARD;
    PIN_LEFT_MOTOR_FORWARD = temp;
    odpowiedzDoUzytkownika += "|odwrocono kierunek lewego silnika|";
  }
  if(prawy){
    int temp = PIN_RIGHT_MOTOR_REVERSE;
    PIN_RIGHT_MOTOR_REVERSE = PIN_RIGHT_MOTOR_FORWARD;
    PIN_RIGHT_MOTOR_FORWARD = temp;
    odpowiedzDoUzytkownika += "|odwrocono kierunek prawego silnika|";
  }
  //todo zapisanie konfiguracji po restarcie
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

void setup() {
  Serial.begin(SERIAL_BAUD_RATE);
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

  liczbaKontrolna = 0;
}



void loop() {
  odpowiedzDoUzytkownika = "{";
  int speed = 0;
  String cmd = "";

  // while(Serial.available()<=0){
  //   // WAIT
  // }
  if (Serial.available()){
    cmd = Serial.readStringUntil('}');

    if(cmd.indexOf("KONFIG")>=0){
      //przykladowa ramka: {KONFIG,RN,LY,<NUMER>,"\n"}
      bool swapLewy =  false;
      bool swapPrawy = false;
      if(cmd.indexOf("LY")>=0)
        swapLewy = true;
      if(cmd.indexOf("RY")>=0)
        swapPrawy = true;

      if(swapPrawy || swapLewy)
        KonfiguracjaRuchuSwapSilnik(swapPrawy, swapLewy);
      else
        odpowiedzDoUzytkownika += "|Brak zmian w konfiguracji|,";

      odpowiedzDoUzytkownika += liczbaKontrolna;

      odpowiedzDoUzytkownika += "}";
      Serial.println(odpowiedzDoUzytkownika);
      //todo ack cale
    }
    else{
      //todo ramka ruchowa i reszta ramek
      int pythonRamkaOdUzytkownika = Serial.parseInt();
      speed = pythonRamkaOdUzytkownika;
      M_RuchOZadanaOdleglosc(speed);
      Serial.println(speed);
    }
  }
  
  //odpowiedzDoUzytkownika+=liczbaKontolna;
  //odpowiedzDoUzytkownika+="}";
  //Serial.println(odpowiedzDoUzytkownika);
  odpowiedzDoUzytkownika = "{"; // reset zawartości
  liczbaKontrolna+=1;

  left_encoder_count=0;
  right_encoder_count=0;
}

//todo S - nagle zatrzymanie dziala zawsze w przypadku wykrycia obiektu przed soba
//sterowanie robotem, symulowane lub gotowe
//parser ramek
//odpowiadanie ACK i kontrolowanie liczby kontrolnej, ewentualnie podeslanie ponowne wiadomosci nieodebranej
