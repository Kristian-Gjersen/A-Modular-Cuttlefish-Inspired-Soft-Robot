#include <WiFi.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// WiFi
// ----
// Setup a costum hotspot and provide ssid and password
// Make sure that the laptop is connected to the same hotspot
const char* ssid = "WiFi-SSID";
const char* password = "WiFi-Password";

WiFiServer server(80);

// MOTOR PINS
// ----------
#define DIR2 7   // D0
#define PWM2 6   // D1
#define PWM1 5   // D2
#define DIR1 1   // D3

// PCA9685
// -------
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

// Servo settings
#define SERVOMIN  800
#define SERVOMAX  2200
#define SERVO_CHANNEL 12
#define SERVO_FREQ 240
#define SERVO_CENTER_ANGLE 50

int currentSpeed = 0;
const int maxSpeed = 150;
const int rampRate = 2;

int driveMode = 0;
int servoOffset = 0;

void setup() {
  Serial.begin(115200);

  // Motor pins
  pinMode(DIR1, OUTPUT);
  pinMode(PWM1, OUTPUT);
  pinMode(DIR2, OUTPUT);
  pinMode(PWM2, OUTPUT);

  stopMotors();

  // Setup I2C manually for ESP32
  Wire.begin(8, 9); // SDA=8, SCL=9

  pwm.begin();
  pwm.setPWMFreq(SERVO_FREQ);
  setSteeringOffset(0);

  delay(500);

  // WiFi
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.print("Connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  server.begin();
  Serial.println("SERVER STARTED");
}

void loop() {
  WiFiClient client = server.available();

  if (client) {
    Serial.println("CLIENT CONNECTED");

    while (client.connected()) {
      if (client.available()) {
        String cmd = client.readStringUntil('\n');
        cmd.trim();
        Serial.println("Received: " + cmd);

        handleCommand(cmd);
        updateOutputs();
      }
    }

    stopMotors();
    client.stop();
    Serial.println("CLIENT DISCONNECTED");
  }
}

void handleCommand(String cmd) {
  if (cmd.startsWith("DRIVE:")) {
    int firstComma = cmd.indexOf(',');
    int secondComma = cmd.indexOf(',', firstComma + 1);

    if (firstComma == -1 || secondComma == -1) {
      return;
    }

    int speedDelta = cmd.substring(6, firstComma).toInt();
    driveMode = cmd.substring(firstComma + 1, secondComma).toInt();
    servoOffset = cmd.substring(secondComma + 1).toInt();

    currentSpeed += speedDelta;
    currentSpeed = constrain(currentSpeed, 0, maxSpeed);

  } else if (cmd == "STOP") {
    currentSpeed = 0;
    driveMode = 0;
    servoOffset = 0;
    stopMotors();
    setSteeringOffset(0);
  }
}

void updateOutputs() {
  setSteeringOffset(servoOffset);
  driveMotorsByMode(driveMode);
  delay(rampRate);
}

// MOTOR FUNCTIONS
// ---------------

void driveMotorsByMode(int mode) {
  currentSpeed = map(currentSpeed, 0, 100, 0, 255);
  switch (mode) {
    case -1:
      // Soft left: motor 1 off, motor 2 forward.
      motor1Stop();
      motor2Forward(currentSpeed);
      break;

    case 1:
      // Soft right: motor 1 forward, motor 2 off.
      motor1Forward(currentSpeed);
      motor2Stop();
      break;

    case -2:
      // Differential left: motor 1 backward, motor 2 forward.
      motor1Backward(currentSpeed);
      motor2Forward(currentSpeed);
      break;

    case 2:
      // Differential right: motor 1 forward, motor 2 backward.
      motor1Forward(currentSpeed);
      motor2Backward(currentSpeed);
      break;

    case 0:
      // Normal forward drive.
      motor1Forward(currentSpeed);
      motor2Forward(currentSpeed);
      break;
  }
}

void motor1Forward(int speed) {
  digitalWrite(DIR1, LOW);
  analogWrite(PWM1, speed);
}

void motor1Backward(int speed) {
  digitalWrite(DIR1, HIGH);
  analogWrite(PWM1, speed);
}

void motor2Forward(int speed) {
  digitalWrite(DIR2, HIGH);
  analogWrite(PWM2, speed);
}

void motor2Backward(int speed) {
  digitalWrite(DIR2, LOW);
  analogWrite(PWM2, speed);
}

void motor1Stop() {
  analogWrite(PWM1, 0);
}

void motor2Stop() {
  analogWrite(PWM2, 0);
}

void stopMotors() {
  motor1Stop();
  motor2Stop();
}

// SERVO FUNCTION
// --------------

void setSteeringOffset(int offset) {
  int angle = constrain(SERVO_CENTER_ANGLE + offset, 0, 180);
  int pulse = map(angle, 0, 100, SERVOMIN, SERVOMAX);
  pwm.setPWM(SERVO_CHANNEL, 0, pulse);
}
