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

float sumaBlad = 0.0;
int iloscPomiarow = 0;
unsigned long TimeZaliczeniowy;

//jesli serwo poruszaloby sie w trybie testowym a nie powinno:
// float ostatnieWychylenie = 0; 

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

  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.print(" Proportional: ");
  Serial.print(proportional);
  Serial.print(" Output: ");
  Serial.print(output);
  Serial.print(" | Kp: ");
  Serial.print(kp);
  Serial.print(", Ki: ");
  Serial.print(ki);
  Serial.print(", Kd: ");
  Serial.print(kd);
  Serial.print(", Distance_point: ");
  Serial.print(distance_point);
  Serial.print(", servo_zero: ");
  Serial.print(servo_zero);
  Serial.print(", t: ");
  Serial.println(t);
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
  TimeZaliczeniowy = millis();
}

void Tryb_Zaliczeniowy_funkcja(){
  unsigned long czas = millis() - TimeZaliczeniowy;

  // jesli "s" jeszcze nie wyslane to czekaj
  if(TimeZaliczeniowy == 0){
    return;
  }

  if(czas <= 10000){ //dzialanie pid przez 10 sekund
    petla();
  }
  else if (czas > 10000 && czas <= 13000){//zbieranie bledu do sredniej przez 3 s    
    // zapamiętaj ostatnią pozycję serwa i ją zablokuj
    // myservo.detach();

    float blad = distance - distance_point;
    sumaBlad += fabs(blad); // sumowanie bezwzglednego bledu
    iloscPomiarow++;
    Serial.print("iloscpomiarow: ");
    Serial.print(iloscPomiarow);
    Serial.print(" sumaBlad: ");
    Serial.println(sumaBlad);
  }
  else if (czas > 13000){// koniec testu
    float srednia = sumaBlad / iloscPomiarow;
    sumaBlad = round(srednia * 100.0) / 100.0; // dla zostawienia 2 miejsc po przecinku

    Serial.print("{DONE,");
    Serial.print(sumaBlad);
    Serial.print("}");

    //reset flag i zmiennych
    TRYB_Zaliczeniowy = false;
    TRYB_Testowy = false;
    TimeZaliczeniowy = 0;
    sumaBlad = 0;
    iloscPomiarow = 0;
    myservo.attach(9);
    return;
  }
}

void Odbior_komendy(String cmd){
  cmd.trim();
  
  if(cmd.startsWith("KP ")){
    kp = cmd.substring(3).toFloat();
    Serial.print("Ustawiono kp = ");
    Serial.println(kp);
  }
  else if(cmd.startsWith("KI ")){
    ki = cmd.substring(3).toFloat();
    Serial.print("Ustawiono ki = ");
    Serial.println(ki);
  }
  else if(cmd.startsWith("KD ")){
    kd = cmd.substring(3).toFloat();
    Serial.print("Ustawiono kd = ");
    Serial.println(kd);
  }
  else if(cmd.startsWith("DIST ")){
    distance_point = cmd.substring(5).toFloat();
    Serial.print("Ustawiono distance_point = ");
    Serial.println(distance_point);
  }
  else if(cmd.startsWith("ZERO ")){
    servo_zero = cmd.substring(5).toFloat();
    Serial.print("Ustawiono servo_zero = ");
    Serial.println(servo_zero);
  }
  else if(cmd.startsWith("T ")){
    t = cmd.substring(2).toFloat();
    Serial.print("Ustawiono t = ");
    Serial.println(t);
  }
  else{
    Serial.println("!Wyslano niezrozumiala funkcje");
  }
}

int Tryb_Testowy_funkcja(){
  petla();

  //Odbior komend od uzytkownika
  if(Serial.available()>0){
    String cmd = Serial.readStringUntil('\n');

    if(cmd.startsWith("Q") || cmd.startsWith("q")){
      TRYB_Zaliczeniowy = false;
      TRYB_Testowy = false;
      Serial.println("STOP");
      return 0;
    }

    Odbior_komendy(cmd);
  }
}

void loop() {

  //odebranie danych z portu
  if(Serial.available() > 0){
    //sciagniecie z buffera
    String cmd = Serial.readStringUntil("\n");
    cmd.trim();

    Serial.print("Flagi: TRYB_Zaliczeniowy ")
    Serial.print(TRYB_Zaliczeniowy)
    Serial.print(", TRYB_Testowy: ")
    Serial.print(TRYB_Testowy)
    Serial.print("ARDUINO: Otrzymano: ");
    Serial.println(cmd);

    //sprawdzenie ktora z komend przyszla
    if(cmd.startsWith("{ZAL") && cmd.indexOf("1")>0){
      //zmiana flag
      TRYB_Zaliczeniowy = true;
      TRYB_Testowy = false;

      // pochylenie maksymalne w strone czujnika
      myservo.write(servo_zero - 45); //todo do dostosowania

      Serial.println("ACK");
    }
    else if(TRYB_Zaliczeniowy && cmd == "s"){
      Serial.println("START"); //potwierdzenie startu
      TimeZaliczeniowy = millis();
    }
    else if(cmd.startsWith("{TEST") && cmd.indexOf("1")>0){
      //zmiana flag
      TRYB_Zaliczeniowy = false;
      TRYB_Testowy = true;
      Serial.println("ACK");
    }
    else if(TRYB_Testowy && cmd == "q"){
      Serial.println("Koniec trybu testowego"); //zakonczenie trybu testowego
      TRYB_Zaliczeniowy = false;
      TRYB_Testowy = false;
    }
  }

  // --- uruchomienie petli do obslugi pochylni ----
  if(TRYB_Zaliczeniowy){
    Tryb_Zaliczeniowy_funkcja();
  }
  else if (TRYB_Testowy){
    Tryb_Testowy_funkcja();
  }

}

