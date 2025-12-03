#include "TRSensors.h"

#define PIN_LEFT_MOTOR_SPEED 5
int PIN_LEFT_MOTOR_FORWARD A1 //default A0
int PIN_LEFT_MOTOR_REVERSE A0 //default A1
#define PIN_LEFT_ENCODER 2
   
#define PIN_RIGHT_MOTOR_SPEED 6
int PIN_RIGHT_MOTOR_FORWARD A3 //default A2           
int PIN_RIGHT_MOTOR_REVERSE A2 //default A3
#define PIN_RIGHT_ENCODER 3

#define NUM_SENSORS 5
TRSensors trs =   TRSensors();
unsigned int sensorValues[NUM_SENSORS];
unsigned int last_proportional = 0;
long integral = 0;
unsigned long myTime;

int left_encoder_count=0;
int right_encoder_count=0;

void left_encoder(){
  left_encoder_count++;  
}

void right_encoder(){
  right_encoder_count++;  
}

void setup(){
  Serial.begin(115200);
  Serial.println("TRSensor example");
  
  for (int i = 0; i < 400; i++){                  // make the calibration take about 10 seconds
    trs.calibrate();                             // reads all sensors 10 times
  }
  Serial.println("calibrate done");
  
  // print the calibration minimum values measured when emitters were on
  for (int i = 0; i < NUM_SENSORS; i++){
    Serial.print(trs.calibratedMin[i]);
    Serial.print(' ');
  }
  Serial.println();
  
  // print the calibration maximum values measured when emitters were on
  for (int i = 0; i < NUM_SENSORS; i++){
    Serial.print(trs.calibratedMax[i]);
    Serial.print(' ');
  }
  Serial.println();
  delay(1000);
  myTime = millis();

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


void loop(){
  if((millis() - myTime) >= 100){
    unsigned int position = trs.readLine(sensorValues);
    int proportional = (int)position - 2000;
    myTime = millis();

    Serial.print(proportional);
    Serial.print(" | ");
    Serial.print(left_encoder_count);
    Serial.print(" : ");
    Serial.println(right_encoder_count);

    left_encoder_count=0;
    right_encoder_count=0;
    if(proportional < -100){
      digitalWrite(PIN_LEFT_MOTOR_FORWARD, HIGH);
      digitalWrite(PIN_LEFT_MOTOR_REVERSE, LOW);
      analogWrite(PIN_LEFT_MOTOR_SPEED, 100);

      digitalWrite(PIN_RIGHT_MOTOR_FORWARD, LOW);
      digitalWrite(PIN_RIGHT_MOTOR_REVERSE, HIGH);
      analogWrite(PIN_RIGHT_MOTOR_SPEED, 70);
    }else if(proportional > 100){
      digitalWrite(PIN_LEFT_MOTOR_FORWARD, HIGH);
      digitalWrite(PIN_LEFT_MOTOR_REVERSE, LOW);
      analogWrite(PIN_LEFT_MOTOR_SPEED, 70);

      digitalWrite(PIN_RIGHT_MOTOR_FORWARD, LOW);
      digitalWrite(PIN_RIGHT_MOTOR_REVERSE, HIGH);
      analogWrite(PIN_RIGHT_MOTOR_SPEED, 100);
    }else{
      digitalWrite(PIN_LEFT_MOTOR_FORWARD, HIGH);
      digitalWrite(PIN_LEFT_MOTOR_REVERSE, LOW);
      analogWrite(PIN_LEFT_MOTOR_SPEED, 90);

      digitalWrite(PIN_RIGHT_MOTOR_FORWARD, LOW);
      digitalWrite(PIN_RIGHT_MOTOR_REVERSE, HIGH);
      analogWrite(PIN_RIGHT_MOTOR_SPEED, 90);
    }
  }
}
