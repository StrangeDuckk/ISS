#include "TRSensors.h"
#define NUM_SENSORS 5
#define PIN_LEFT_MOTOR_SPEED 5
int PIN_LEFT_MOTOR_FORWARD = A0;
int PIN_LEFT_MOTOR_REVERSE = A1;
#define PIN_RIGHT_MOTOR_SPEED 6
int PIN_RIGHT_MOTOR_FORWARD = A2;
int PIN_RIGHT_MOTOR_REVERSE = A3;
TRSensors trs =   TRSensors();
unsigned int sensorValues[NUM_SENSORS];


// PID
float Kp = 0.06;
float Ki = 0.0;
float Kd = 2.8;
long integral = 0;
int lastError = 0;
float derivative = 0;
int SPEED = 75;
int updateTime = 10; // ms
unsigned long lastPID = 0;

bool czyJechac = false;
unsigned long czasOdUruchomienia = 0;
bool czyBylaAkcja = false;
bool czyLoopWypisalJednorazowo = false;
bool czyBylaKalibracja = false;


// Serial command buffer
#define CMD_BUF_SIZE 32
char cmdBuf[CMD_BUF_SIZE];
uint8_t cmdIndex = 0;

void Kalibracja(){
  Serial.println("Kalibruje TRSensors");
  for (int i = 0; i < 400; i++) 
    trs.calibrate();
  Serial.println("Kalibracja zakonczona");
}

void setup() {
  // unsigned long czasOdUruchomienia = millis();
  Serial.begin(115200);

  Serial.println("Arduino gotowe!");

  pinMode(PIN_LEFT_MOTOR_SPEED, OUTPUT);
  analogWrite(PIN_LEFT_MOTOR_SPEED, 0);
  pinMode(PIN_LEFT_MOTOR_FORWARD, OUTPUT);
  pinMode(PIN_LEFT_MOTOR_REVERSE, OUTPUT);

  pinMode(PIN_RIGHT_MOTOR_SPEED, OUTPUT);
  analogWrite(PIN_RIGHT_MOTOR_SPEED, 0);
  pinMode(PIN_RIGHT_MOTOR_FORWARD, OUTPUT);
  pinMode(PIN_RIGHT_MOTOR_REVERSE, OUTPUT);

  // Kalibracja();

  // Ustaw kierunki silników – PRAWDZIWY ruch do przodu
  digitalWrite(PIN_LEFT_MOTOR_FORWARD, LOW);
  digitalWrite(PIN_LEFT_MOTOR_REVERSE, HIGH);
  digitalWrite(PIN_RIGHT_MOTOR_FORWARD, HIGH);  // <- odwrócone dla prawego silnika
  digitalWrite(PIN_RIGHT_MOTOR_REVERSE, LOW);
}

void Move(int leftPWM, int rightPWM) {
  leftPWM = constrain(leftPWM, 0, 255);
  rightPWM = constrain(rightPWM, 0, 255);
  analogWrite(PIN_LEFT_MOTOR_SPEED, leftPWM);
  analogWrite(PIN_RIGHT_MOTOR_SPEED, rightPWM);
}

void Stop(){
  analogWrite(PIN_LEFT_MOTOR_SPEED, 0);
  analogWrite(PIN_RIGHT_MOTOR_SPEED, 0);

  digitalWrite(PIN_LEFT_MOTOR_FORWARD, LOW);
  digitalWrite(PIN_LEFT_MOTOR_REVERSE, LOW);
  digitalWrite(PIN_RIGHT_MOTOR_FORWARD, LOW);
  digitalWrite(PIN_RIGHT_MOTOR_REVERSE, LOW);

  czyJechac = false;
  czyBylaKalibracja = false;
}

void Start(){
  //todo zmienic
    // Ustaw kierunki silników – PRAWDZIWY ruch do przodu
  digitalWrite(PIN_LEFT_MOTOR_FORWARD, LOW);
  digitalWrite(PIN_LEFT_MOTOR_REVERSE, HIGH);
  digitalWrite(PIN_RIGHT_MOTOR_FORWARD, HIGH);  // <- odwrócone dla prawego silnika
  digitalWrite(PIN_RIGHT_MOTOR_REVERSE, LOW);
}

void updatePID() {
  unsigned int pos = trs.readLine(sensorValues); // 0-4000
  int proportional = (int)pos - 2000; // środek = 0
  // PID
  integral += proportional * updateTime;
  integral = constrain(integral, -2000,2000);
  derivative = (proportional - lastError) / updateTime;
  int u = (int)(Kp * proportional + Ki * integral + Kd * derivative);
  int leftPWM = SPEED - u;
  int rightPWM = SPEED + u;
  Move(leftPWM, rightPWM);
  lastError = proportional;
  // Debug
  Serial.print("Proportional: "); Serial.print(proportional);
  Serial.print(" | u: "); Serial.print(u);
  Serial.print(" | PWM_L: "); Serial.print(leftPWM);
  Serial.print(" PWM_R: "); Serial.println(rightPWM);
}

void processSerial() {
  //odebranie danych z portu
  if(Serial.available() > 0){
    //sciagniecie z buffera
    String cmd = Serial.readStringUntil("\n");
    Serial.print("ACK | ");

    if(cmd.startsWith("START")){
      Serial.print("rozpoczynam jazde");

      czasOdUruchomienia = millis();
      czyJechac = true;
      czyBylaKalibracja = false;
    }
    else if (cmd.startsWith("END")){
      Serial.println("Koncze jazde");
      Stop();
    }
    else{
      // rozbicie po przecinkach
      String output = "";
      int start = 0;
      while (true){
        int przecinek = cmd.indexOf(",", start);
        if(przecinek == -1)
          break;

        String sub = cmd.substring(start, przecinek);
        sub.trim();
        if(sub.length() > 0){
          output+= Odbior_komendy(sub);
        }
        start = przecinek +1;
      }

      Serial.println(output);
    }
  }
}

String Odbior_komendy(String cmd){
  String temp = "";
  cmd.trim();

  if(cmd.startsWith("KP ")){
    Kp = cmd.substring(3).toFloat();
    temp += "Ustawiono kp = ";
    temp += String(Kp);
    temp += " | ";
  }
  else if(cmd.startsWith("KI ")){
    Ki = cmd.substring(3).toFloat();
    temp += "Ustawiono ki = ";
    temp += String(Ki);
    temp += " | ";
  }
  else if(cmd.startsWith("KD ")){
    Kd = cmd.substring(3).toFloat();
    temp += "Ustawiono kd = ";
    temp += String(Kd);
    temp += " | ";
  }
  else if(cmd.startsWith("S ")){
    SPEED = cmd.substring(2).toFloat();
    temp += "Ustawiono SPEED = ";
    temp += String(SPEED);
    temp += " | ";
  }
  else if(cmd.startsWith("T ")){
    updateTime = cmd.substring(2).toFloat();
    temp += "Ustawiono updateTime = ";
    temp += String(updateTime);
    temp += " | ";
  }
  else if(cmd.startsWith("SP ")){
    int stare = PIN_LEFT_MOTOR_FORWARD;
    PIN_LEFT_MOTOR_FORWARD = PIN_LEFT_MOTOR_REVERSE;
    PIN_LEFT_MOTOR_REVERSE = stare;
    temp += "Odwrocono kierunek silnika prawego | ";
  }
  else if(cmd.startsWith("SL ")){
    int stare = PIN_RIGHT_MOTOR_FORWARD;
    PIN_RIGHT_MOTOR_FORWARD = PIN_RIGHT_MOTOR_REVERSE;
    PIN_RIGHT_MOTOR_REVERSE = stare;
    temp += "Odwrocono kierunek silnika lewego | ";
  }
  else{
    temp += "Nieobslugiwana komenda: ";
    temp += cmd;
    temp += " | ";
  }

  return temp;
}

void loop() {
  processSerial(); // obsluga nieblokujaca seriala
  unsigned long t = millis();
  // plan: po P, odczekac 10 s i rozpoczac kalibracje
  //nie usuwac -> jelsi nie bylo akcji przez 5 sekund (czyli np po resecie) alphabot ma zaczac jechac sam, jelis to nie bylo jeszce wypisane i zroione to robi kalibracje
  // if((!czyBylaAkcja && czasOdUruchomienia>=5000) && !czyLoopWypisalJednorazowo){
  //   czyJechac = true;
  //   Serial.println("Nie zarejestrowano akcji od 5 sekund, rozpoczynam kalibracje");
  //   if(!czyBylaKalibracja){
  //     Kalibracja();
  //     czyBylaKalibracja = true;
  //   }
  //   Kalibracja();
  //   czyLoopWypisalJednorazowo = true;
  // }
  if(czyJechac){
    if(!czyBylaKalibracja && czasOdUruchomienia > 0){
      if( t - czasOdUruchomienia >=10000){
        Kalibracja();
        czyBylaKalibracja = true;
        Start();
      }
    }
    if(czyBylaKalibracja){
      if (t - lastPID >= updateTime) {
        updatePID();
        lastPID = t;
        Serial.println("JADE");//do debugowania
      }
    }
  }
}