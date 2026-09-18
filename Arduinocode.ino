// ==========================================
// L298N Motor Driver Pins
// ==========================================

const int IN1 = 8;
const int IN2 = 7;
const int ENA = 9;   // PWM


void setup() {

  // Motor control pins
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENA, OUTPUT);

  // Serial communication with Python
  Serial.begin(9600);

  // Motor initially OFF
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  analogWrite(ENA, 0);
}


void loop() {

  if (Serial.available() > 0) {

    // Read PWM value from Python
    int pwm = Serial.parseInt();

    // Make sure PWM is between 0 and 255
    pwm = constrain(pwm, 0, 255);

    // Set motor direction
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);

    // Set motor speed
    analogWrite(ENA, pwm);
  }
}
