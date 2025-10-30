// ------------ kod do sterowania pochylnia ------------------
// #include <Wire.h>  
// #include <Servo.h>  

 
  
// unsigned long myTime;  
// Servo myservo;  
// float distance;  
// float kp = 3.0; //potegowanie bledu 3.0 
// float ki = 0.5; //potegowanie bledu w czasie, zapis historyczny, jesli zwiekszamy, dluzej bedzie pamietal co sie dzielo wczesniej, jak cyfry wyskoczyly to dlugo czekal, male 0.5 
// float kd = 0.8; //poteguje roznice pomiedzy ostatnim a obecnym bledem, jak szybko ma zareagowac (przewiduje troche przyszlosc) kd jest 2x mniejsze lub wieksze niz kp (mniejsze wg macmaca) 0.8 
// float integral = 0.0;  
// float derivative = 0.0;  
// float previousError = 0.0;  
// float distance_point = 18.0;  
// int servo_zero = 0;  
// int t = 100;  

 
  
// float get_dist(int n){  
//   long sum=0;  
//   for(int i=0;i<n;i++){  
//     sum=sum+analogRead(A0);  
//   }    
//   float adc=sum/n;  
// //zbiera wartosc 100 razy i usrednienie  
  
//   float distance_cm = 17569.7 * pow(adc, -1.2062); //przeliczenie na cm  
//   return(distance_cm);  
// //sciaga odleglosc od czurnika  
// }  
  
// void PID(){  
// //to jest algorytm caly praktycznie,   
//   float proportional = distance-distance_point; //proporcjonalny, im wiekszy blad tym silnejsze dzialanie regulatora, tutaj jest szybkosc, troche ponad 1  
//   integral = integral+proportional*0.1; // calkujacy, 0,1 jest do normalizacji wartosci, integral jest globalne pamietane z poprzedniej iteracji  
//   derivative=(proportional-previousError)/0.1; //rozniczkujacy, roznica pomiedzy aktualnym bleden i poprzedniej iteracji, mowi w która strone powinnismy się krecic  
//   float output=kp*proportional+ki*integral+kd*derivative;  
// //kp ki kd to sa parametry do regulowania pida, tym manipulujemy  
  
// //distance point -> punkt docelowy  
  
// //wypisanie wartosci  
//   Serial.print(distance);  
//   Serial.print(" : ");  
//   Serial.print(proportional);//blad pomiedzy tym co ma a tym co powinno byc  
//   Serial.print(" : ");  
//   Serial.println(output); //wysjcie z pida, powinien być w zakresie –10/10  
//   previousError=proportional;  
//   myservo.write(servo_zero+output); //tu sterujemy serwem pochylnia  
// // servo_zero jest rownym poziomem, sprawdzic i ustawic to samodzielnie  
// }  

 
  
// void setup() {  
//   Serial.begin(9600);     
//   myservo.attach(9);  
//   myservo.write(95);  
//   pinMode(A0,INPUT);  
  
  
//   myTime = millis();//aktualny czas systemu  
// }  

 
  
 



// ------------- ustawienia bazowe --------------
#include <Wire.h>  
#include <Servo.h> 

unsigned long myTime;  
Servo myservo;  
float distance;  
float kp = 3.0; //potegowanie bledu 3.0 
float ki = 0.5; //potegowanie bledu w czasie, zapis historyczny, jesli zwiekszamy, dluzej bedzie pamietal co sie dzielo wczesniej, jak cyfry wyskoczyly to dlugo czekal, male 0.5 
float kd = 0.8; //poteguje roznice pomiedzy ostatnim a obecnym bledem, jak szybko ma zareagowac (przewiduje troche przyszlosc) kd jest 2x mniejsze lub wieksze niz kp (mniejsze wg macmaca) 0.8 
float integral = 0.0;  
float derivative = 0.0;  
float previousError = 0.0;  
float distance_point = 18.0;  
int servo_zero = 0;  
int t = 100;  


// #define PIN_LEFT_MOTOR_SPEED 5
// int PIN_LEFT_MOTOR_FORWARD = A0;            
// int PIN_LEFT_MOTOR_REVERSE = A1;
// #define PIN_LEFT_ENCODER 2
   
// #define PIN_RIGHT_MOTOR_SPEED 6
// int PIN_RIGHT_MOTOR_FORWARD = A2;         
// int PIN_RIGHT_MOTOR_REVERSE = A3;
// #define PIN_RIGHT_ENCODER 3

// #include <EEPROM.h>

// struct KonfiguracjaSilnikow {
//   int PIN_LEFT_MOTOR_FORWARD;
//   int PIN_LEFT_MOTOR_REVERSE;
//   int PIN_RIGHT_MOTOR_FORWARD;
//   int PIN_RIGHT_MOTOR_REVERSE;
//   bool initialized;
// };

// ------------- flgi stanu ---------------
bool awaryjnyStop = false;
bool wykonanieRuchu = true;
bool controlActive = false; // true gdy poruszanie dziala


// ======================================================================================

#define SERIAL_BAUD_RATE 9600

String odpowiedzDoUzytkownika= "{DONE,";

// int left_encoder_count=0;
// int right_encoder_count=0;
// int left_full_rotation = 20;
// int right_full_rotation = 20;
// int speed = 100;

// void left_encoder(){
//   left_encoder_count++;  
// }

// void right_encoder(){
//   right_encoder_count++;  
// }

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
  Serial.begin(9600);     
  myservo.attach(9);  
  myservo.write(95);  
  pinMode(A0,INPUT);  
  
  Serial.println("Polaczenie z Arduino jest gotowe.");
  
  myTime = millis();//aktualny czas systemu  
}  

// void setup() {
//   Serial.begin(SERIAL_BAUD_RATE);

//   Serial.println("Polaczenie z Arduino jest gotowe.");
  
//   pinMode(PIN_LEFT_MOTOR_SPEED, OUTPUT);
//   analogWrite(PIN_LEFT_MOTOR_SPEED, 0);
//   pinMode(PIN_LEFT_MOTOR_FORWARD, OUTPUT);
//   pinMode(PIN_LEFT_MOTOR_REVERSE, OUTPUT);

//   pinMode(PIN_RIGHT_MOTOR_SPEED, OUTPUT);
//   analogWrite(PIN_RIGHT_MOTOR_SPEED, 0);
//   pinMode(PIN_RIGHT_MOTOR_FORWARD, OUTPUT);
//   pinMode(PIN_RIGHT_MOTOR_REVERSE, OUTPUT);

//   attachInterrupt(digitalPinToInterrupt(PIN_LEFT_ENCODER), left_encoder, RISING);
//   attachInterrupt(digitalPinToInterrupt(PIN_RIGHT_ENCODER), right_encoder, RISING);
// }



// ========================================== funkcje pochylni ==========================================
// ---------------- funkcje z tresci -----------------
float get_dist(int n){  
  long sum=0;  
  for(int i=0;i<n;i++){  
    sum=sum+analogRead(A0);  
  }    
  float adc=sum/n;  
//zbiera wartosc 100 razy i usrednienie  

  float distance_cm = 17569.7 * pow(adc, -1.2062); //przeliczenie na cm  
  return(distance_cm);  
//sciaga odleglosc od czurnika  
}  

void PID(){  
//to jest algorytm caly praktycznie,   
  float proportional = distance-distance_point; //proporcjonalny, im wiekszy blad tym silnejsze dzialanie regulatora, tutaj jest szybkosc, troche ponad 1  
  integral = integral+proportional*0.1; // calkujacy, 0,1 jest do normalizacji wartosci, integral jest globalne pamietane z poprzedniej iteracji  
  derivative=(proportional-previousError)/0.1; //rozniczkujacy, roznica pomiedzy aktualnym bleden i poprzedniej iteracji, mowi w która strone powinnismy się krecic  
  float output=kp*proportional+ki*integral+kd*derivative;  
//kp ki kd to sa parametry do regulowania pida, tym manipulujemy  
  
//distance point -> punkt docelowy  
  
//wypisanie wartosci  
  Serial.print(distance);  
  Serial.print(" : ");  
  Serial.print(proportional);//blad pomiedzy tym co ma a tym co powinno byc  
  Serial.print(" : ");  
  Serial.println(output); //wysjcie z pida, powinien być w zakresie –10/10  
  previousError=proportional;  
  
  int servo_cmd = constrain(servo_zero + output, 0, 180);
  myservo.write(servo_cmd);

  //myservo.write(servo_zero+output); //tu sterujemy serwem pochylnia  
// servo_zero jest rownym poziomem, sprawdzic i ustawic to samodzielnie  
}  



// ------------------- funkcje ruchu i danych -------------------
void Funkcja_P(float noweKp){
  kp = noweKp;
  odpowiedzDoUzytkownika += "P{Kp pochylni zostala ustawiona na " + String(kp) + "}, ";
}

void Funkcja_I(float noweKi){
  ki = noweKi;
  odpowiedzDoUzytkownika += "I{Ki pochylni zostala ustawiona na " + String(ki) + "}, ";
}

void Funkcja_D(float noweKd){
  kd = noweKd;
  odpowiedzDoUzytkownika += "D{Kd pochylni zostala ustawiona na " + String(kd) + "}, ";
}

void Funkcja_E(int kat){
  servo_zero = kat;
  myservo.write(constrain(servo_zero, 0, 180));
  odpowiedzDoUzytkownika += "E{Ustawiono punkt servo_zero na " + String(servo_zero) + "}, ";
}

void Funkcja_S(int czyAwaryjnie){
  //todo rzeczywiste zatrzymanie robota
  
  // digitalWrite(PIN_LEFT_MOTOR_FORWARD, LOW);
  // digitalWrite(PIN_LEFT_MOTOR_REVERSE, LOW);
  // analogWrite(PIN_LEFT_MOTOR_SPEED, 0);

  // digitalWrite(PIN_RIGHT_MOTOR_FORWARD, LOW);
  // digitalWrite(PIN_RIGHT_MOTOR_REVERSE, LOW);
  // analogWrite(PIN_RIGHT_MOTOR_SPEED, 0);
  
  //0 to tylko zatrzymanie bez zadnych informacji
  if(czyAwaryjnie == 1)
    odpowiedzDoUzytkownika += "S{Bot zatrzymal sie}, ";
  else if(czyAwaryjnie == 2){  
    awaryjnyStop = true;
    odpowiedzDoUzytkownika = "{DONE, Awaryjne_Zatrzymanie}";
    Serial.println(odpowiedzDoUzytkownika);
  }
}

void Funkcja_T(int iloscMiliSekund) {
  t = iloscMiliSekund;
  odpowiedzDoUzytkownika += "T{Ustawiono predkosc naprawy na " + String(t) + "}, ";
}



void Funkcja_B(){
  odpowiedzDoUzytkownika += "B{Odczyt z sonaru " + String(get_dist(10)) + "}, ";
}

void Funkcja_I(){
  odpowiedzDoUzytkownika += "I{Odczyt z czujnika na koniec komend TODO}, ";
}



void Funkcja_C(float odl, bool czyBC){
  distance_point = odl;
  odpowiedzDoUzytkownika += "C{Ustawiono odleglosc celu na: " + String(distance_point) + "}, ";
}

// ------------------ parsowanie ramki -------------------
void WykonajRamke(String ramka){
  //przykladowa ramka: {TASK, P4.00, I0.30, D8.30, C45, T100, B1, C17.00, SK29,\n}
  //przetwarzana ramka:  P4.00, I0.30, D8.30, C45, T100, B1, C17.00
  ramka.trim();

  int start = 0;
  int end = ramka.indexOf(",");

  bool czyCB = false;

  if (ramka.indexOf("C")>=0 && ramka.indexOf("B")>=0){// todo c i b
    czyCB = true;
  }
  
  while (end != -1){
    String komenda = ramka.substring(start, end);
    komenda.trim();

    if (komenda.startsWith("P")) Funkcja_P(komenda.substring(1).toFloat()); //P4.00, 
    else if (komenda.startsWith("I")) Funkcja_I(komenda.substring(1).toFloat());//I0.30,
    else if (komenda.startsWith("D")) Funkcja_D(komenda.substring(1).toFloat());//D8.30, 
    else if (komenda.startsWith("E")) Funkcja_E(komenda.substring(1).toInt()); //E45, 
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
    else if (komenda.startsWith("T")) Funkcja_T(komenda.substring(1).toInt()); //T100,
    else if (komenda.startsWith("B")) Funkcja_B();// B1, 
    else if (komenda.startsWith("C")) Funkcja_C(komenda.substring(1).toFloat(), czyCB);//C17.00

    start = end + 1;
    end = ramka.indexOf(",", start);
  }
}

//--------------------- M + V - ruch o zadana odleglosc -----------------------
// void M_RuchOZadanaOdleglosc(int speed){
//   //todo rozdzielic V i M
  
//   delay(500);
//   digitalWrite(PIN_LEFT_MOTOR_FORWARD, HIGH);
//   digitalWrite(PIN_LEFT_MOTOR_REVERSE, LOW);
//   analogWrite(PIN_LEFT_MOTOR_SPEED, speed);

//   digitalWrite(PIN_RIGHT_MOTOR_FORWARD, LOW);
//   digitalWrite(PIN_RIGHT_MOTOR_REVERSE, HIGH);
//   analogWrite(PIN_RIGHT_MOTOR_SPEED, speed);
//   delay(3000);

//   digitalWrite(PIN_LEFT_MOTOR_FORWARD, LOW);
//   digitalWrite(PIN_LEFT_MOTOR_REVERSE, LOW);
//   analogWrite(PIN_LEFT_MOTOR_SPEED, 0);

//   digitalWrite(PIN_RIGHT_MOTOR_FORWARD, LOW);
//   digitalWrite(PIN_RIGHT_MOTOR_REVERSE, LOW);
//   analogWrite(PIN_RIGHT_MOTOR_SPEED, 0);

//   odpowiedzDoUzytkownika += "M {Wykonano ruch o ";
//   odpowiedzDoUzytkownika += speed;
//   odpowiedzDoUzytkownika += ", (odpowiedz kol: [";
//   odpowiedzDoUzytkownika += left_encoder_count;
//   odpowiedzDoUzytkownika += " ";
//   odpowiedzDoUzytkownika += right_encoder_count;
//   odpowiedzDoUzytkownika += "]}, ";
// }

// ------------------- loop -----------------------
void poruszanie() {  
//t to co ile mili sekund chce mieć kolejna iteracje 100, 150, 200  
  if (millis() > myTime+t){  
    distance = get_dist(100);   
    myTime = millis();  

    if (millis() % 500 < 20) {
    Serial.print("Dist: "); Serial.print(distance);
    Serial.print(" Target: "); Serial.print(distance_point);
    Serial.print(" Servo: "); Serial.println(servo_zero);
    }


    PID();  
  }  
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

      // if(swapPrawy || swapLewy)
      //   // KonfiguracjaRuchuSwapSilnik(swapPrawy, swapLewy);
      // else
      //   odpowiedzDoUzytkownika += "|Brak zmian w konfiguracji|,";

      // if(prawyEnkoderCount>0 || lewyEnkoderCount>0)
        // Konfiguracja_EnkoderPelnyObrot(prawyEnkoderCount,lewyEnkoderCount);
      // else
        // odpowiedzDoUzytkownika += "|Brak zmian w konfiguracji enkoderow|,";

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

      integral = 0;
      derivative = 0;
      previousError = 0;


      WykonajRamke(ramkaSurowa);
      poruszanie();
      odpowiedzDoUzytkownika.setCharAt( odpowiedzDoUzytkownika.lastIndexOf(",")  , '}');
      Serial.println(odpowiedzDoUzytkownika);
    }
  }
  
  odpowiedzDoUzytkownika = "{DONE,"; // reset zawartości
  awaryjnyStop = false;//reset flag
  wykonanieRuchu = false;//reset dla pewnosci

  integral = 0;
  derivative = 0;
  previousError = 0;


  // left_encoder_count=0;
  // right_encoder_count=0;
}