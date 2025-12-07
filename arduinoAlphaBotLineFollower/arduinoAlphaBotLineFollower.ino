#include "TRSensors.h"
#define NUM_SENSORS 5
#define PIN_LEFT_MOTOR_SPEED 5
#define PIN_LEFT_MOTOR_FORWARD A0
#define PIN_LEFT_MOTOR_REVERSE A1
#define PIN_RIGHT_MOTOR_SPEED 6
#define PIN_RIGHT_MOTOR_FORWARD  A2
#define PIN_RIGHT_MOTOR_REVERSE A3
TRSensors trs =   TRSensors();
unsigned int sensorValues[NUM_SENSORS];


// PID
float Kp = 0.06;
float Ki = 0.0;
float Kd = 2.8;
long integral = 0;
int lastError = 0;
float derivative = 0;
// float D_filter = 0;
// float D_alpha = 0.2; // filtr dolnoprzepustowy D
int SPEED = 75;
int updateTime = 10; // ms
unsigned long lastPID = 0;


// Serial command buffer
#define CMD_BUF_SIZE 32
char cmdBuf[CMD_BUF_SIZE];
uint8_t cmdIndex = 0;
void setup() {
  Serial.begin(115200);
  pinMode(PIN_LEFT_MOTOR_SPEED, OUTPUT);
  analogWrite(PIN_LEFT_MOTOR_SPEED, 0);
  pinMode(PIN_LEFT_MOTOR_FORWARD, OUTPUT);
  pinMode(PIN_LEFT_MOTOR_REVERSE, OUTPUT);

  pinMode(PIN_RIGHT_MOTOR_SPEED, OUTPUT);
  analogWrite(PIN_RIGHT_MOTOR_SPEED, 0);
  pinMode(PIN_RIGHT_MOTOR_FORWARD, OUTPUT);
  pinMode(PIN_RIGHT_MOTOR_REVERSE, OUTPUT);

  Serial.println("Kalibruje TRSensors");
  for (int i = 0; i < 400; i++) 
    trs.calibrate();
  Serial.println("Kalibracja zakonczona");

  // Ustaw kierunki silników – PRAWDZIWY ruch do przodu
  digitalWrite(PIN_LEFT_MOTOR_FORWARD, LOW);
  digitalWrite(PIN_LEFT_MOTOR_REVERSE, HIGH);
  digitalWrite(PIN_RIGHT_MOTOR_FORWARD, HIGH);  // <- odwrócone dla prawego silnika
  digitalWrite(PIN_RIGHT_MOTOR_REVERSE, LOW);
  // Uruchom silniki na start
  // analogWrite(LEFT_MOTOR_PWM, SPEED);
  // analogWrite(RIGHT_MOTOR_PWM, SPEED);
}

void Move(int leftPWM, int rightPWM) {
  leftPWM = constrain(leftPWM, 0, 255);
  rightPWM = constrain(rightPWM, 0, 255);
  analogWrite(PIN_LEFT_MOTOR_SPEED, leftPWM);
  analogWrite(PIN_RIGHT_MOTOR_SPEED, rightPWM);
}

void updatePID() {
  unsigned int pos = trs.readLine(sensorValues); // 0-4000
  int proportional = (int)pos - 2000; // środek = 0
  // PID
  integral += proportional * updateTime;
  integral = constrain(integral, -2000,2000);
  // if (integral > 10000) 
  //   integral = 10000;
  // if (integral < -10000) integral = -10000;
  derivative = (proportional - lastError) / updateTime;
  // filtr dolnoprzepustowy D
  // D_filter = D_alpha * derivative + (1 - D_alpha) * D_filter;
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
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      cmdBuf[cmdIndex] = 0; // zakończenie stringa
      if (cmdIndex > 0) {
        handleCommand(cmdBuf);
      }
      cmdIndex = 0;
    } else if (cmdIndex < CMD_BUF_SIZE - 1) {
      cmdBuf[cmdIndex++] = c;
    }
  }
}

void handleCommand(char* cmd) {
  if (cmd[0] == 'P') { // start PID
    Serial.println("ACK | PID włączony");
  } else if (strncmp(cmd, "KP", 2) == 0) {
    Kp = atof(cmd + 3);
    Serial.print("ACK | Kp ustawione: "); Serial.println(Kp);
  } else if (strncmp(cmd, "KI", 2) == 0) {
    Ki = atof(cmd + 3);
    Serial.print("ACK | Ki ustawione: "); Serial.println(Ki);
  } else if (strncmp(cmd, "KD", 2) == 0) {
    Kd = atof(cmd + 3);
    Serial.print("ACK | Kd ustawione: "); Serial.println(Kd);
  } else {
    Serial.println("Nieznana komenda");
  }
}
void loop() {
  unsigned long t = millis();
  if (t - lastPID >= updateTime) {
    updatePID();
    lastPID = t;
  }
  processSerial(); // obsluga nieblokujaca seriala
}