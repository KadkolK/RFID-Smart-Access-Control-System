#include <SPI.h>
#include <MFRC522.h>
#include <Servo.h>

#define SS_PIN 10
#define RST_PIN 9

MFRC522 mfrc522(SS_PIN, RST_PIN); //creates instance

#define BUZZER 8
#define SERVO_PIN 7

Servo myServo;

// YOUR UID
String allowedUID = "3A07203B";

void setup() {
  Serial.begin(9600);

  SPI.begin();
  mfrc522.PCD_Init();

  pinMode(BUZZER, OUTPUT);

  myServo.attach(SERVO_PIN);
  delay(500);
  myServo.write(0);

  Serial.println("SYSTEM_READY");
}

void loop() {

  if (!mfrc522.PICC_IsNewCardPresent()) return;
  if (!mfrc522.PICC_ReadCardSerial()) return;

  delay(50);

  // Build UID properly
  String uid = "";

  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(mfrc522.uid.uidByte[i], HEX);
  }

  uid.toUpperCase();
  uid.trim(); // IMPORTANT FIX

  Serial.print("UID:");
  Serial.println(uid);

  // buzzer
  digitalWrite(BUZZER, HIGH);
  delay(80);
  digitalWrite(BUZZER, LOW);

  // =========================
  // SAFE COMPARISON (FIX)
  // =========================
  if (uid.indexOf(allowedUID) >= 0) {

    Serial.println("GRANTED");

    myServo.write(90);
    delay(3000);
    myServo.write(0);

  } else {

    Serial.println("DENIED");

    digitalWrite(BUZZER, HIGH);
    delay(400);
    digitalWrite(BUZZER, LOW);
  }

  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
}
