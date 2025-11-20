#include <Wire.h>
#include <Servo.h>

unsigned long myTime;
Servo myservo;
float distance;
float kp = 2.5;//2.3    1.0     1.75  1.0    2.5
float ki = 0.04;//0.04  0.04    0.25  0.01    0.04
float kd = 2.0;//10.0   1.0     10    1.0     2.0
float integral = 0.0;
float derivative = 0.0;
float previousError = 0.0;
float distance_point = 26.0;
int servo_zero = 76;//          76    82
int t = 100; //                 10    100

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
    petla();

    sumaBlad += fabs(distance-distance_point); // sumowanie bezwzglednego bledu
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

String Odbior_komendy(String cmd){
  cmd.trim();
  String temp = "";
  
  if(cmd.startsWith("KP ")){
    kp = cmd.substring(3).toFloat();
    temp += "Ustawiono kp =";
    temp += String(kp);
    temp += "\n";
  }
  else if(cmd.startsWith("KI ")){
    ki = cmd.substring(3).toFloat();
    temp += "Ustawiono ki =";
    temp += String(ki);
    temp += "\n";
  }
  else if(cmd.startsWith("KD ")){
    kd = cmd.substring(3).toFloat();
    temp += "Ustawiono kd =";
    temp += String(kd);
    temp += "\n";
  }
  else if(cmd.startsWith("DIST ")){
    distance_point = cmd.substring(5).toFloat();
    temp += "Ustawiono distance_point =";
    temp += String(distance_point);
    temp += "\n";
  }
  else if(cmd.startsWith("ZERO ")){
    servo_zero = cmd.substring(5).toFloat();
    temp += "Ustawiono servo_zero =";
    temp += String(servo_zero);
    temp += "\n";
  }
  else if(cmd.startsWith("T ")){
    t = cmd.substring(2).toFloat();
    temp += "Ustawiono t =";
    temp += String(t);
    temp += "\n";
  }
  else{
    temp += "!Wyslano niezrozumiala funkcje";
    temp += "\n";
  }
  return temp;
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

    Serial.println(Odbior_komendy(cmd));
  }
}


void loop() {

  //odebranie danych z portu
  if(Serial.available() > 0){
    //sciagniecie z buffera
    String cmd = Serial.readStringUntil("\n");
    cmd.trim();

    //sprawdzenie ktora z komend przyszla
    if(cmd.startsWith("{RAM")){
      //{RAM, KP 10.0,\n}
      TRYB_Zaliczeniowy = false;
      TRYB_Testowy = false;

      Serial.println("ACK");

      cmd.remove(0,5); // "{RAM, "
      String doOdeslania = "";
      
      //rozbicie po przecinkach:
      int start = 0;
      while (true){
        int przecinek = cmd.indexOf(",", start);
        if( przecinek == -1)
          break;

        String sub = cmd.substring(start, przecinek);
        sub.trim();
        if(sub.length() > 0){
          doOdeslania+= Odbior_komendy(sub);
        }
        start = przecinek +1;
      }
      Serial.println(doOdeslania);

    }
    else if(cmd.startsWith("{ZAL") && cmd.indexOf("1")>0){
      //zmiana flag
      TRYB_Zaliczeniowy = true;
      TRYB_Testowy = false;

      // pochylenie maksymalne w strone czujnika
      myservo.write(servo_zero + 45); //todo do dostosowania

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

