#include <Wire.h>
#include <Servo.h>

unsigned long myTime;
Servo myservo;
float distance;
float kp = 2.0;
float ki = 0.20;
float kd = 4.0;
float integral = 0.0;
float derivative = 0.0;
float previousError = 0.0;
float distance_point = 25.0;
int servo_zero = 0;
int t = 150;

// -------------- flagi --------------
bool TRYB_Zaliczeniowy = false;
bool TRYB_Testowy = false;

// ------------- funkcje dane ------------
float get_dist(int n){
  long sum=0;
  for(int i=0;i<n;i++){
    sum=sum+analogRead(A0);
  }  
  float adc=sum/n;

  float distance_cm = 17569.7 * pow(adc, -1.2062);
  return(distance_cm);
}

void PID(){
  float proportional = distance-distance_point;
  integral = integral+proportional*0.1;
  derivative=(proportional-previousError)/0.1;
  float output=kp*proportional+ki*integral+kd*derivative;
  Serial.print(distance);
  Serial.print(" : ");
  Serial.print(proportional);
  Serial.print(" : ");
  Serial.println(output);
  previousError=proportional;
  myservo.write(servo_zero+output);
}

void petla() {
  if (millis() > myTime+t){
    distance = get_dist(100); 
    myTime = millis();
    PID();
  }
}

void setup() {
  Serial.begin(9600);   
  myservo.attach(9);
  myservo.write(95);
  pinMode(A0,INPUT);

  Serial.println("Arduino polaczone poprawnie!");

  myTime = millis();
}

void loop() {
  //odebranie danych z portu
  if(Serial.available() > 0){
    if(!TRYB_Zaliczeniowy && !TRYB_Testowy){
      //sciagniecie z buffera
      String cmd = Serial.readStringUntil("\n");
      cmd.trim();

      Serial.print("ARDUINO: Otrzymano: ");
      Serial.println(cmd);

      //sprawdzenie ktora z komend przyszla
      if(cmd.startsWith("{ZAL") && cmd.indexOf("1")>0){
        //zmiana flag
        TRYB_Zaliczeniowy = true;
        TRYB_Testowy = false;
        Serial.println("ACK");
      }
      else if(cmd.startsWith("{TEST") && cmd.indexOf("1")>0){
        //zmiana flag
        TRYB_Zaliczeniowy = false;
        TRYB_Testowy = true;
        Serial.println("ACK");
      }
    }
  }


  // --- uruchomienie petli do obslugi pochylni ----
  if(TRYB_Zaliczeniowy){
    petla();
  }
  else if (TRYB_Testowy){
    petla();
  }
}

